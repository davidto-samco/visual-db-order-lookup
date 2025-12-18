"""Work Order Tree Widget with Lazy Loading.

Custom QTreeWidget implementation for hierarchical work order display.
Supports lazy loading of operations, requirements, labor, materials, and WIP data.
"""

import logging
import csv
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from decimal import Decimal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont

from visual_order_lookup.services.work_order_service import WorkOrderService, WorkOrderServiceError
from visual_order_lookup.database.models.work_order import WorkOrder

logger = logging.getLogger(__name__)


@dataclass
class TreeNodeData:
    """Data stored in tree node for lazy loading.

    T046: Define TreeNodeData dataclass
    """
    node_type: str  # HEADER, OPERATIONS_CONTAINER, OPERATION, REQUIREMENT, etc.
    base_id: str
    lot_id: str
    sub_id: str
    operation_seq: Optional[int] = None
    part_id: Optional[str] = None
    children_loaded: bool = False  # T059: Caching flag


class WorkOrderTreeWidget(QTreeWidget):
    """Custom tree widget for work order hierarchy display with lazy loading.

    T045: Create WorkOrderTreeWidget extending QTreeWidget
    """

    def __init__(self, service: WorkOrderService, parent=None):
        """Initialize tree widget.

        Args:
            service: WorkOrderService instance for data loading
            parent: Parent widget
        """
        super().__init__(parent)

        self.service = service
        self.current_work_order: Optional[WorkOrder] = None
        self.detailed_view = False  # Toggle between simplified and detailed view

        self._setup_ui()
        self._connect_signals()

        logger.debug("WorkOrderTreeWidget initialized")

    def set_detailed_view(self, detailed: bool):
        """Set the view mode.

        Args:
            detailed: True for detailed view, False for simplified view
        """
        self.detailed_view = detailed
        logger.debug(f"View mode changed to: {'detailed' if detailed else 'simplified'}")

    def _setup_ui(self):
        """Configure tree widget appearance."""
        self.setColumnCount(3)
        self.setHeaderLabels(["Description", "Quantity", "Details"])
        self.setAlternatingRowColors(True)
        self.setAnimated(True)  # Smooth expand/collapse animations

        # Column widths
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 300)

    def _connect_signals(self):
        """Connect tree signals for lazy loading.

        T049: Connect itemExpanded signal
        """
        self.itemExpanded.connect(self._on_item_expanded)

    def load_work_order(self, work_order: WorkOrder):
        """Load work order as root node with placeholder children.

        T047: Implement load_work_order_header
        T048: Add 6 placeholder child nodes
        """
        view_mode = "DETAILED" if self.detailed_view else "SIMPLIFIED"
        logger.info(f"📋 Loading work order in {view_mode} view mode")
        self.clear()
        self.current_work_order = work_order

        # T047: Create root node with formatted ID, status, part (WITHOUT '-' separator)
        # For root level, remove '-' from description column
        status_prefix = work_order.formatted_status()
        wo_id = work_order.formatted_id()
        desc = work_order.part_description or work_order.part_id
        header = QTreeWidgetItem(self)
        header.setText(0, f"{status_prefix} {wo_id} {desc}")

        # Set bold font for root header
        bold_font = QFont()
        bold_font.setBold(True)
        header.setFont(0, bold_font)
        header.setFont(1, bold_font)
        header.setFont(2, bold_font)

        # Column 1: Quantity followed by notes from WORKORDER_BINARY.bits
        # Format: "1.0000 - NOTES_TEXT"
        qty_text = work_order.formatted_qty()
        notes_text = work_order.notes if work_order.notes else ""
        if notes_text:
            header.setText(1, f"{qty_text} - {notes_text}")
        else:
            header.setText(1, qty_text)

        # Column 2: Details - Show dates in both simplified and detailed view
        # Format: -77, 8/15/2011(10/31/2011) - 1/13/2011(10/16/2011)
        logger.debug(f"Setting dates for work order root")
        header.setText(2, work_order.formatted_dates())

        # Store metadata (T058) - Set up for lazy loading requirements directly
        header.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

        node_data = TreeNodeData(
            node_type="WORK_ORDER_ROOT",
            base_id=work_order.base_id,
            lot_id=work_order.lot_id,
            sub_id=work_order.sub_id,
            children_loaded=False  # Will lazy load on expansion
        )
        header.setData(0, Qt.ItemDataRole.UserRole, node_data)

        # Expand header by default to trigger lazy load
        header.setExpanded(True)

        logger.info(f"Loaded work order: {work_order.formatted_id()}")

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - lazy load children.

        T050-T056: Lazy loading for each node type
        T059: Set children_loaded flag
        T060: Loading indicator
        T061: Error handling
        """
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or not isinstance(node_data, TreeNodeData):
            return

        # Check if already loaded (T059)
        if node_data.children_loaded:
            return

        logger.debug(f"Lazy loading: {node_data.node_type}")

        # T060: Show loading indicator
        loading_item = QTreeWidgetItem(item)
        loading_item.setText(0, "Loading...")
        self.expandItem(loading_item)

        try:
            # Load based on node type
            if node_data.node_type == "WORK_ORDER_ROOT":
                # Different behavior for simplified vs detailed view
                if self.detailed_view:
                    # Detailed view: Load operations only (sub-work-orders will be nested under operations)
                    self._load_operations(item, node_data)
                else:
                    # Simplified view: Show only sub-work-orders (original behavior)
                    self._load_all_requirements(item, node_data)
            elif node_data.node_type == "SUB_WORK_ORDER":
                # Load sub-work-order children (recursive)
                if self.detailed_view:
                    # Detailed view: Load operations only (sub-work-orders nested under operations)
                    self._load_operations(item, node_data)
                else:
                    self._load_all_requirements(item, node_data)
            elif node_data.node_type == "OPERATION":
                # Load requirements for this operation
                self._load_requirements(item, node_data)

            # Mark as loaded (T059)
            node_data.children_loaded = True

        except WorkOrderServiceError as e:
            # T061: Error handling with user-friendly error nodes
            logger.error(f"Lazy load error: {e}")
            error_item = QTreeWidgetItem(item)
            error_item.setText(0, f"Error: {str(e)}")
            error_item.setDisabled(True)
        finally:
            # Remove loading indicator
            item.removeChild(loading_item)

    def _load_all_requirements(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load all requirements for work order by WORKORDER_SUB_ID.

        Matches legacy Manufacturing Window structure:
        - Queries requirements WHERE WORKORDER_SUB_ID = node_data.sub_id
        - For main WO (8113/26), loads requirements with WORKORDER_SUB_ID='0'
        - For sub-WO (8113-346/26), loads requirements with WORKORDER_SUB_ID='346'
        """
        # Load requirements by SUB_ID (determines tree hierarchy)
        requirements = self.service.get_requirements_by_sub_id(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not requirements:
            # No requirements found - remove the expand indicator
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return

        # Display ONLY sub-work-orders (items with SUBORD_WO_SUB_ID)
        # The legacy Manufacturing Window only shows the work order hierarchy, not regular parts
        sub_work_orders = [req for req in requirements if req.has_child_work_order()]

        if not sub_work_orders:
            # No sub-work-orders found - remove the expand indicator
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return

        for req in sub_work_orders:
            req_item = QTreeWidgetItem(item)
            req_item.setText(0, req.formatted_display())
            req_item.setText(1, req.formatted_qty())
            req_item.setText(2, req.formatted_dates())

            # Set bold font
            bold_font = QFont()
            bold_font.setBold(True)
            req_item.setFont(0, bold_font)
            req_item.setFont(1, bold_font)
            req_item.setFont(2, bold_font)

            # Color sub-work-orders BLACK (default - no color change needed)

            # Store data for potential loading of sub-work-order's children
            req_node_data = TreeNodeData(
                node_type="SUB_WORK_ORDER",
                base_id=node_data.base_id,
                lot_id=node_data.lot_id,
                sub_id=req.subord_wo_sub_id,  # IMPORTANT: Use SUBORD_WO_SUB_ID as the new sub_id
                children_loaded=False
            )
            req_item.setData(0, Qt.ItemDataRole.UserRole, req_node_data)

            # Performance optimization: Only show expand indicator if this sub-work-order
            # might have children. We'll check this by querying if it has any requirements
            # with SUBORD_WO_SUB_ID (i.e., child sub-work-orders)
            # For now, show indicator for all - user can expand if interested
            # The lazy loading will handle it efficiently
            try:
                child_requirements = self.service.get_requirements_by_sub_id(
                    node_data.base_id,
                    node_data.lot_id,
                    req.subord_wo_sub_id
                )
                # Only show expand indicator if there are child sub-work-orders
                has_children = any(child_req.has_child_work_order() for child_req in child_requirements)
                if has_children:
                    req_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            except Exception as e:
                # If query fails, show indicator anyway to allow user to try expanding
                logger.warning(f"Could not check children for {req.subord_wo_sub_id}: {e}")
                req_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

        logger.debug(f"Loaded {len(sub_work_orders)} sub-work-orders for SUB_ID={node_data.sub_id}")

    def _load_wo_level_requirements(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load work-order-level sub-work-order requirements.

        In detailed view, ALL sub-work-orders should appear at the work order level
        as siblings to operations, regardless of their OPERATION_SEQ_NO.
        """
        logger.info(f"📦 Loading work-order-level sub-work-order requirements")

        # Load ALL requirements for this work order
        all_requirements = self.service.get_requirements_by_sub_id(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        # Filter to only sub-work-orders
        requirements = [req for req in all_requirements if req.has_child_work_order()]

        if not requirements:
            logger.debug("No sub-work-order requirements found")
            return

        logger.info(f"  Creating {len(requirements)} sub-work-order nodes at work order level...")

        for req in requirements:
            req_item = QTreeWidgetItem(item)
            req_item.setText(0, req.formatted_display())
            req_item.setText(1, req.formatted_qty())

            # Column 2: Show dates for sub-work-orders
            if req.has_child_work_order():
                req_item.setText(2, req.formatted_dates())
            else:
                req_item.setText(2, req.formatted_details())

            # If it's a sub-work-order, make it expandable
            if req.has_child_work_order():
                req_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

                req_node_data = TreeNodeData(
                    node_type="SUB_WORK_ORDER",
                    base_id=node_data.base_id,
                    lot_id=node_data.lot_id,
                    sub_id=req.subord_wo_sub_id,
                    part_id=req.part_id,
                    children_loaded=False
                )
                req_item.setData(0, Qt.ItemDataRole.UserRole, req_node_data)

        logger.info(f"✅ Loaded {len(requirements)} sub-work-orders at work order level")

    def _load_operations(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load operations for work order.

        T050: Load operations with [sequence] prefix
        """
        logger.info(f"⚙️  Loading operations in {'DETAILED' if self.detailed_view else 'SIMPLIFIED'} view mode")
        operations = self.service.get_operations(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not operations:
            # No operations found - remove the expand indicator
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return

        logger.info(f"  Creating {len(operations)} operation nodes...")

        for op in operations:
            op_item = QTreeWidgetItem(item)

            # Column 0: Operation display with notes appended
            display_text = op.formatted_display()
            if op.notes:
                display_text = f"{display_text} {op.notes}"
            op_item.setText(0, display_text)

            # Set bold font
            bold_font = QFont()
            bold_font.setBold(True)
            op_item.setFont(0, bold_font)
            op_item.setFont(1, bold_font)
            op_item.setFont(2, bold_font)

            # Color operations GREEN (all columns)
            green_brush = QBrush(QColor(0, 128, 0))
            op_item.setForeground(0, green_brush)
            op_item.setForeground(1, green_brush)
            op_item.setForeground(2, green_brush)

            logger.debug(f"  - Operation {op.sequence}: {op.description[:40] if op.description else op.operation_id}")

            # Column 1: Show status and completion date if applicable
            # Format: "[C], Completed M/d/yyyy" if close_date is set, else "[C]"
            if op.close_date is not None:
                # Operation is completed - show completion date
                date_str = f"{op.close_date.month}/{op.close_date.day}/{op.close_date.year}"
                if op.status:
                    status_text = f"[{op.status[0].upper()}], Completed {date_str}"
                else:
                    status_text = f"Completed {date_str}"
            else:
                # Operation is open/in-progress - just show status
                if op.status:
                    status_text = f"[{op.status[0].upper()}]"
                else:
                    status_text = ""

            op_item.setText(1, status_text)

            # Column 2: Details (varies by view mode)
            if self.detailed_view:
                # Detailed view: Show setup/run hours and quantity matching 6671-full.png
                # Format: "S/U 0.00 Hrs, 0.00 HRS/PC, Qty 5.0000"
                # Uses CALC_START_QTY from OPERATION table
                op_item.setText(2, op.formatted_details())
                logger.debug(f"DETAILED VIEW: Operation {op.sequence} - {op.formatted_details()}")
            else:
                # Simplified view: Show requirement count (M-parts + sub-WOs only)
                # Count will be lower since we filter in simplified view
                op_item.setText(2, f"{op.requirement_count} items")
                logger.debug(f"SIMPLIFIED VIEW: Operation {op.sequence} - {op.requirement_count} items (filtered)")

            # T057: Show indicator if operation has requirements
            op_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

            # Store operation data for lazy loading requirements (T051)
            op_node_data = TreeNodeData(
                node_type="OPERATION",
                base_id=node_data.base_id,
                lot_id=node_data.lot_id,
                sub_id=node_data.sub_id,
                operation_seq=op.sequence
            )
            op_item.setData(0, Qt.ItemDataRole.UserRole, op_node_data)

        logger.info(f"✅ Loaded {len(operations)} operation nodes successfully")

    def _load_requirements(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load requirements for operation using flattened hierarchy.

        This uses get_operation_children() which returns BOTH requirements AND child work order
        operations as siblings, solving the hierarchy issue where child operations appeared nested.

        Example for operation 10:
            10 100 [MECH. ENG.]
              ├─ [C] 6671-1/28 - 40072 - 5" BARRELL STRAIGHTENER  (REQUIREMENT)
              └─ 10 500 [MECH. ASSEMBLY]  (CHILD_OPERATION from sub-WO 6671-1/28)

        T051: Load requirements with part_id - description - qty format
        T052: Recursive load for SUBORD_WO_SUB_ID
        """
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"Loading operation {node_data.operation_seq} children (flattened hierarchy)")
        logger.info(f"{'='*80}")

        children = self.service.get_operation_children(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id,
            node_data.operation_seq
        )

        if not children:
            # No children found - remove the expand indicator
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            return

        logger.info(f"  Found {len(children)} items in flattened query")

        shown_count = 0
        filtered_count = 0

        for child in children:
            item_type = child['item_type']

            if item_type == 'REQUIREMENT':
                # FILTERING LOGIC: Simplified view only shows M-prefix parts and sub-work-orders
                if not self.detailed_view:
                    # Simplified view: Filter out purchased parts (R, F, P, etc.)
                    if not child['subord_wo_sub_id']:
                        # Not a sub-work-order, check if it's a manufactured part
                        part_id = child['item_id']
                        if not part_id or not part_id.startswith('M'):
                            # Skip purchased/other parts in simplified view
                            filtered_count += 1
                            logger.info(f"  ❌ SIMPLIFIED: Filtered out {part_id}")
                            continue

                # Create requirement node
                req_item = QTreeWidgetItem(item)

                # Build display text
                part_id = child['item_id']
                description = child['item_description']

                # Sub-work-orders vs regular parts
                if child['subord_wo_sub_id']:
                    # Sub-work-order: [C] 6671-1/28 - 40072 - 5" BARRELL STRAIGHTENER (no PIECE_NO)
                    sub_wo_id = f"{node_data.base_id}-{child['subord_wo_sub_id']}/{node_data.lot_id}"
                    status_prefix = f"[{child['subord_wo_status'][0].upper()}]" if child['subord_wo_status'] else "[?]"

                    # Only show part info if PART_ID exists and is not empty
                    if part_id is not None and (isinstance(part_id, str) and part_id.strip()):
                        if description:
                            display_text = f"{status_prefix} {sub_wo_id} - {part_id} - {description}"
                        else:
                            display_text = f"{status_prefix} {sub_wo_id} - {part_id}"
                    else:
                        # No part ID - just show work order ID
                        display_text = f"{status_prefix} {sub_wo_id}"
                else:
                    # Regular part: 10 F0646 - SPRING PIN 1/4 X 1 1/8 (with PIECE_NO)
                    piece_no = child.get('piece_no')

                    # Handle NULL part_id - use description only or show piece_no
                    # Check if part_id is None or empty string
                    if part_id is None or (isinstance(part_id, str) and not part_id.strip()):
                        # Part ID is NULL or empty - show piece_no and/or description
                        # Format: "{piece_no} {description}" or just description if no piece_no
                        if piece_no is not None and description and description.strip():
                            display_text = f"{piece_no} {description}"
                        elif description and description.strip():
                            display_text = description
                        elif piece_no is not None:
                            display_text = str(piece_no)
                        else:
                            display_text = "(No Part ID)"
                    else:
                        # Normal case with part_id
                        # Format: "{piece_no} {part_id} - {description}"
                        if piece_no is not None:
                            display_text = f"{piece_no} {part_id} - {description}" if (description and description.strip()) else f"{piece_no} {part_id}"
                        else:
                            display_text = f"{part_id} - {description}" if (description and description.strip()) else part_id

                req_item.setText(0, display_text)

                # Set bold font
                bold_font = QFont()
                bold_font.setBold(True)
                req_item.setFont(0, bold_font)
                req_item.setFont(1, bold_font)
                req_item.setFont(2, bold_font)

                # Color coding for requirements (all columns)
                if child['subord_wo_sub_id']:
                    # Sub-work-order: BLACK (default)
                    pass
                else:
                    # Regular requirement (not a sub-work-order): RED
                    # Color ALL regular requirements red, regardless of part_id prefix
                    red_brush = QBrush(QColor(255, 0, 0))
                    req_item.setForeground(0, red_brush)
                    req_item.setForeground(1, red_brush)
                    req_item.setForeground(2, red_brush)

                # Column 1 (second column)
                if self.detailed_view:
                    if child['subord_wo_sub_id']:
                        # Sub-work-orders: Show quantity like "5.0000 -"
                        req_item.setText(1, f"{child['calc_qty']:.4f} -")
                    else:
                        # Regular parts: Show status and issue info based on req_close_date
                        req_status = child.get('req_status')
                        calc_qty = child.get('calc_qty', 0)
                        req_close_date = child.get('req_close_date')

                        # Use req_close_date to determine if requirement has been issued
                        # req_close_date IS NOT NULL means material was issued and requirement was closed
                        if req_close_date is not None:
                            # If closed: [STATUS] Issued M/d/yyyy, CALC_QTY Qty Reqd
                            # Format as M/d/yyyy (without leading zeros)
                            date_str = f"{req_close_date.month}/{req_close_date.day}/{req_close_date.year}"
                            if req_status:
                                details = f"[{req_status}] Issued {date_str}, {calc_qty:.4f} Qty Reqd"
                            else:
                                details = f"Issued {date_str}, {calc_qty:.4f} Qty Reqd"
                        else:
                            # If not closed: [STATUS], CALC_QTY Qty Reqd
                            if req_status:
                                details = f"[{req_status}], {calc_qty:.4f} Qty Reqd"
                            else:
                                details = f"{calc_qty:.4f} Qty Reqd"

                        req_item.setText(1, details)
                else:
                    # Simplified view: Just show calc_qty
                    req_item.setText(1, str(child['calc_qty']))

                # Column 2 (third column): Different format for sub-work-orders vs regular requirements
                if self.detailed_view:
                    if child['subord_wo_sub_id']:
                        # Sub-work-orders: Show dates
                        start_date = child['subord_wo_start_date'].strftime("%m/%d/%Y") if child['subord_wo_start_date'] else ""
                        finish_date = child['subord_wo_finish_date'].strftime("%m/%d/%Y") if child['subord_wo_finish_date'] else ""
                        req_item.setText(2, f"[{start_date}] - [{finish_date}]")
                    else:
                        # Regular requirements: Show QTY_PER per + SCRAP_PERCENT% + FIXED_QTY
                        qty_per = child.get('qty_per', 0)
                        scrap_percent = child.get('scrap_percent', 0)
                        fixed_qty = child.get('fixed_qty', 0)
                        req_item.setText(2, f"{qty_per:.4f} per + {scrap_percent:.2f}% + {fixed_qty:.4f}")

                shown_count += 1
                logger.info(f"  ✓ Added REQUIREMENT: {display_text}")

            elif item_type == 'CHILD_OPERATION':
                # Create child operation node
                op_item = QTreeWidgetItem(item)

                # Column 0: Format "10 500 [MECH. ASSEMBLY]" with notes appended
                seq_and_resource = child['item_id']  # e.g., "10 500"
                op_type = child['operation_type']

                # Only show brackets if operation_type exists
                if op_type and op_type.strip():
                    display_text = f"{seq_and_resource} [{op_type}]"
                else:
                    # No operation type - just show sequence and resource
                    display_text = seq_and_resource

                # Append notes if available
                operation_notes = child.get('notes')
                if operation_notes:
                    display_text = f"{display_text} {operation_notes}"

                op_item.setText(0, display_text)

                # Set bold font
                bold_font = QFont()
                bold_font.setBold(True)
                op_item.setFont(0, bold_font)
                op_item.setFont(1, bold_font)
                op_item.setFont(2, bold_font)

                # Color child operations GREEN (all columns)
                green_brush = QBrush(QColor(0, 128, 0))
                op_item.setForeground(0, green_brush)
                op_item.setForeground(1, green_brush)
                op_item.setForeground(2, green_brush)

                # Column 1: Show status and completion date for child operations
                # Format: "[C], Completed M/d/yyyy" if operation_close_date is set, else "[C]"
                operation_close_date = child.get('operation_close_date')
                operation_status = child.get('operation_status')

                if operation_close_date is not None:
                    # Operation is completed - show completion date
                    date_str = f"{operation_close_date.month}/{operation_close_date.day}/{operation_close_date.year}"
                    if operation_status:
                        status_text = f"[{operation_status}], Completed {date_str}"
                    else:
                        status_text = f"Completed {date_str}"
                else:
                    # Operation is open/in-progress - just show status
                    if operation_status:
                        status_text = f"[{operation_status}]"
                    else:
                        status_text = ""

                op_item.setText(1, status_text)

                # Column 2: Show hours in detailed view matching 6671-full.png
                # Format: "S/U 0.00 Hrs, 0.00 HRS/PC, Qty 5.0000" or "S/U 0.00 Hrs, 20.00 MIN/PC, Qty 5.0000"
                # Uses CALC_START_QTY from OPERATION table
                # RUN_HRS is already stored in the unit specified by RUN_TYPE (no conversion needed)
                if self.detailed_view:
                    setup_hrs = child['setup_hrs'] if child['setup_hrs'] else Decimal('0')
                    run_hrs = child['run_hrs'] if child['run_hrs'] else Decimal('0')
                    run_type = child['run_type'] if child['run_type'] else 'HRS/PC'
                    calc_start_qty = child['calc_start_qty'] if child['calc_start_qty'] else Decimal('0')

                    # RUN_HRS is already in the correct unit - no conversion needed
                    # If RUN_TYPE is MIN/PC, RUN_HRS already contains minutes
                    # If RUN_TYPE is HRS/PC, RUN_HRS already contains hours
                    details_text = f"S/U {setup_hrs:.2f} Hrs, {run_hrs:.2f} {run_type}, Qty {calc_start_qty:.4f}"
                    op_item.setText(2, details_text)

                # IMPORTANT: Make child operations expandable to show their own requirements
                # Extract sequence number from item_id (e.g., "10 500" -> 10)
                seq_parts = seq_and_resource.strip().split()
                if seq_parts:
                    try:
                        operation_seq = int(seq_parts[0])

                        # Set up for lazy loading this operation's requirements
                        op_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

                        op_node_data = TreeNodeData(
                            node_type="OPERATION",
                            base_id=node_data.base_id,
                            lot_id=node_data.lot_id,
                            sub_id=child['subord_wo_sub_id'],  # Use child work order's SUB_ID
                            operation_seq=operation_seq
                        )
                        op_item.setData(0, Qt.ItemDataRole.UserRole, op_node_data)

                        shown_count += 1
                        logger.info(f"  ✓ Added CHILD_OPERATION: {display_text} (expandable for sub-WO {child['subord_wo_sub_id']})")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"  ⚠ Could not parse sequence from '{seq_and_resource}': {e}")
                        shown_count += 1
                        logger.info(f"  ✓ Added CHILD_OPERATION: {display_text} (non-expandable)")
                else:
                    shown_count += 1
                    logger.info(f"  ✓ Added CHILD_OPERATION: {display_text} (non-expandable)")

        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"{'DETAILED' if self.detailed_view else 'SIMPLIFIED'} VIEW SUMMARY:")
        logger.info(f"  Total items: {len(children)}")
        logger.info(f"  Shown: {shown_count}")
        logger.info(f"  Filtered out: {filtered_count}")
        logger.info(f"{'='*80}")
        logger.info(f"")

        # If no items were shown after filtering, remove expand indicator
        if shown_count == 0:
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)

    def _load_sub_work_order(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load sub-work-order when requirement is expanded.

        Creates a child work order node and sets it up for lazy loading operations.
        """
        logger.info(f"📦 Loading sub-work-order: {node_data.base_id}-{node_data.sub_id}/{node_data.lot_id}")

        # Load the sub-work-order header
        sub_wo = self.service.get_work_order_header(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not sub_wo:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "Sub-work-order not found")
            no_data_item.setDisabled(True)
            return

        # Create sub-work-order node
        sub_wo_item = QTreeWidgetItem(item)
        sub_wo_item.setText(0, f"{sub_wo.formatted_status()} {sub_wo.formatted_id()} {sub_wo.part_description or sub_wo.part_id}")
        sub_wo_item.setText(1, sub_wo.formatted_qty())
        if self.detailed_view:
            sub_wo_item.setText(2, sub_wo.formatted_dates())
        else:
            sub_wo_item.setText(2, f"{sub_wo.operation_count} ops")

        # Set up for lazy loading operations
        sub_wo_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

        sub_wo_node_data = TreeNodeData(
            node_type="SUB_WORK_ORDER",
            base_id=node_data.base_id,
            lot_id=node_data.lot_id,
            sub_id=node_data.sub_id,
            children_loaded=False
        )
        sub_wo_item.setData(0, Qt.ItemDataRole.UserRole, sub_wo_node_data)

    def _load_labor_tickets(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load labor transactions for work order.

        T053: Load labor tickets with [LABOR] employee - date - hours format
        """
        labor_tickets = self.service.get_labor_tickets(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not labor_tickets:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No labor tickets found")
            no_data_item.setDisabled(True)
            return

        for ticket in labor_tickets:
            labor_item = QTreeWidgetItem(item)
            labor_item.setText(0, ticket.formatted_display())
            labor_item.setText(1, ticket.formatted_hours())
            labor_item.setText(2, ticket.formatted_cost())

        logger.debug(f"Loaded {len(labor_tickets)} labor tickets")

    def _load_inventory_transactions(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load material transactions for work order.

        T054: Load inventory transactions with [MATERIAL] part - type - qty - date format
        """
        transactions = self.service.get_inventory_transactions(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not transactions:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No inventory transactions found")
            no_data_item.setDisabled(True)
            return

        for trans in transactions:
            trans_item = QTreeWidgetItem(item)
            trans_item.setText(0, trans.formatted_display())
            trans_item.setText(1, trans.formatted_qty())
            trans_item.setText(2, trans.formatted_date())

        logger.debug(f"Loaded {len(transactions)} inventory transactions")

    def _load_wip_balance(self, item: QTreeWidgetItem, node_data: TreeNodeData):
        """Load WIP cost accumulation for work order.

        T055: Load WIP balance with child nodes for material/labor/burden costs
        """
        wip_balance = self.service.get_wip_balance(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id
        )

        if not wip_balance:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No WIP balance found")
            no_data_item.setDisabled(True)
            return

        # Material cost node
        material_item = QTreeWidgetItem(item)
        material_item.setText(0, "[WIP] Material Cost")
        material_item.setText(1, wip_balance.formatted_material_cost())

        # Labor cost node
        labor_item = QTreeWidgetItem(item)
        labor_item.setText(0, "[WIP] Labor Cost")
        labor_item.setText(1, wip_balance.formatted_labor_cost())

        # Burden cost node
        burden_item = QTreeWidgetItem(item)
        burden_item.setText(0, "[WIP] Burden Cost")
        burden_item.setText(1, wip_balance.formatted_burden_cost())

        # Total node
        total_item = QTreeWidgetItem(item)
        total_item.setText(0, "[WIP] Total Cost")
        total_item.setText(1, wip_balance.formatted_total())

        logger.debug(f"Loaded WIP balance: {wip_balance.formatted_total()}")

    def expand_all(self):
        """Recursively expand all tree nodes.

        T069: Implement expand_all() with lazy loading trigger
        """
        self.expandAll()
        logger.debug("Expanded all tree nodes")

    def collapse_all(self):
        """Collapse all tree nodes except root.

        T070: Implement collapse_all()
        """
        self.collapseAll()

        # Re-expand root header
        if self.topLevelItemCount() > 0:
            root = self.topLevelItem(0)
            root.setExpanded(True)

        logger.debug("Collapsed all tree nodes")

    def export_to_csv(self):
        """Export tree data to CSV file.

        T073-T079: CSV export functionality
        """
        if not self.current_work_order:
            QMessageBox.warning(
                self,
                "No Data",
                "No work order loaded to export."
            )
            return

        # T074: Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d")
        default_filename = f"workorder_{self.current_work_order.base_id}_{self.current_work_order.lot_id}_{timestamp}.csv"

        # T073: File dialog for save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            default_filename,
            "CSV Files (*.csv)"
        )

        if not filename:
            return  # User cancelled

        try:
            self._write_csv(filename)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Work order exported to:\n{filename}"
            )
            logger.info(f"Exported tree to CSV: {filename}")

        except Exception as e:
            # T079: Error handling
            logger.error(f"CSV export error: {e}")
            raise

    def _write_csv(self, filename: str):
        """Write tree data to CSV file.

        T075: Recursive tree traversal
        T076: CSV columns
        T077: Indentation for hierarchy
        T078: Format dates, quantities, costs
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # T076: CSV header
            writer.writerow(["Level", "Type", "ID", "Description", "Quantity", "Details"])

            # T075: Recursive traversal
            if self.topLevelItemCount() > 0:
                root = self.topLevelItem(0)
                self._write_tree_node(writer, root, level=0)

    def _write_tree_node(self, writer, item: QTreeWidgetItem, level: int):
        """Recursively write tree node and children to CSV.

        T077: Add indentation in Level column
        """
        # T077: Indentation
        indent = "  " * level

        # Get node data
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        node_type = node_data.node_type if node_data and isinstance(node_data, TreeNodeData) else "UNKNOWN"

        # Extract columns
        description = item.text(0)
        quantity = item.text(1)
        details = item.text(2)

        # Determine ID
        if node_data and isinstance(node_data, TreeNodeData):
            node_id = f"{node_data.base_id}/{node_data.lot_id}/{node_data.sub_id}"
        else:
            node_id = ""

        # Write row
        writer.writerow([
            indent + str(level),
            node_type,
            node_id,
            description,
            quantity,
            details
        ])

        # Recursively write children
        for i in range(item.childCount()):
            child = item.child(i)
            self._write_tree_node(writer, child, level + 1)

    def keyPressEvent(self, event):
        """Handle keyboard navigation.

        T062-T066: Keyboard shortcuts
        """
        key = event.key()
        current = self.currentItem()

        if not current:
            super().keyPressEvent(event)
            return

        # T065: Right arrow - expand or move to first child
        if key == Qt.Key.Key_Right:
            if not current.isExpanded() and current.childCount() > 0:
                current.setExpanded(True)
            elif current.childCount() > 0:
                self.setCurrentItem(current.child(0))
            event.accept()

        # T064: Left arrow - collapse or move to parent
        elif key == Qt.Key.Key_Left:
            if current.isExpanded():
                current.setExpanded(False)
            else:
                parent = current.parent()
                if parent:
                    self.setCurrentItem(parent)
            event.accept()

        # T066: Space - toggle expand/collapse
        elif key == Qt.Key.Key_Space:
            if current.childCount() > 0:
                current.setExpanded(not current.isExpanded())
            event.accept()

        # T063: Up/Down arrows - default Qt behavior
        else:
            super().keyPressEvent(event)
