"""Work Order Tree Widget with Lazy Loading.

Custom QTreeWidget implementation for hierarchical work order display.
Supports lazy loading of operations, requirements, labor, materials, and WIP data.
"""

import logging
import csv
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt

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
                    # Detailed view: Show operations → requirements
                    self._load_operations(item, node_data)
                else:
                    # Simplified view: Show only sub-work-orders (original behavior)
                    self._load_all_requirements(item, node_data)
            elif node_data.node_type == "SUB_WORK_ORDER":
                # Load sub-work-order children (recursive)
                if self.detailed_view:
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
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No requirements found")
            no_data_item.setDisabled(True)
            return

        # Display ONLY sub-work-orders (items with SUBORD_WO_SUB_ID)
        # The legacy Manufacturing Window only shows the work order hierarchy, not regular parts
        sub_work_orders = [req for req in requirements if req.has_child_work_order()]

        if not sub_work_orders:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "(No sub-work-orders)")
            no_data_item.setDisabled(True)
            return

        for req in sub_work_orders:
            req_item = QTreeWidgetItem(item)
            req_item.setText(0, req.formatted_display())
            req_item.setText(1, req.formatted_qty())
            req_item.setText(2, req.formatted_dates())

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
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No operations found")
            no_data_item.setDisabled(True)
            return

        logger.info(f"  Creating {len(operations)} operation nodes...")

        for op in operations:
            op_item = QTreeWidgetItem(item)
            op_item.setText(0, op.formatted_display())
            logger.debug(f"  - Operation {op.sequence}: {op.description[:40] if op.description else op.operation_id}")

            # Column 1: Leave empty in both views (or show minimal info in simplified)
            op_item.setText(1, "")

            # Column 2: Details (varies by view mode)
            if self.detailed_view:
                # Detailed view: Show status and hours information matching screenshot
                op_item.setText(2, op.formatted_details())
                logger.debug(f"DETAILED VIEW: Operation {op.sequence} - hours: {op.formatted_details()}")
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
        """Load requirements for operation.

        T051: Load requirements with part_id - description - qty format
        T052: Recursive load for SUBORD_WO_SUB_ID
        """
        requirements = self.service.get_requirements(
            node_data.base_id,
            node_data.lot_id,
            node_data.sub_id,
            node_data.operation_seq
        )

        if not requirements:
            no_data_item = QTreeWidgetItem(item)
            no_data_item.setText(0, "No requirements found")
            no_data_item.setDisabled(True)
            return

        # Count before filtering
        total_count = len(requirements)
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"{'DETAILED' if self.detailed_view else 'SIMPLIFIED'} VIEW: Loaded {total_count} requirements for operation {node_data.operation_seq}")
        logger.info(f"Detailed view flag: {self.detailed_view}")
        logger.info(f"{'='*80}")

        shown_count = 0
        filtered_count = 0
        for req in requirements:
            # FILTERING LOGIC: Simplified view only shows M-prefix parts and sub-work-orders
            if not self.detailed_view:
                # Simplified view: Filter out purchased parts (R, F, P, etc.)
                # Only show:
                # 1. Sub-work-orders (has SUBORD_WO_SUB_ID)
                # 2. Manufactured parts (part_id starts with 'M')
                if not req.has_child_work_order():
                    # Not a sub-work-order, check if it's a manufactured part
                    if not req.part_id or not req.part_id.startswith('M'):
                        # Skip purchased/other parts in simplified view
                        filtered_count += 1
                        logger.info(f"  ❌ SIMPLIFIED: Filtered out {req.part_id} ({req.part_description[:30] if req.part_description else 'No desc'})")
                        continue
                    else:
                        logger.info(f"  ✓ SIMPLIFIED: Showing M-part {req.part_id}")
                else:
                    logger.info(f"  ✓ SIMPLIFIED: Showing sub-WO {req.subord_wo_sub_id}")
            else:
                # Detailed view - show everything
                part_display = req.part_id if req.part_id else f"SUB-WO-{req.subord_wo_sub_id}"
                has_child = "with child WO" if req.has_child_work_order() else "regular part"
                logger.info(f"  ✓ DETAILED: Showing {part_display} ({has_child})")

            shown_count += 1
            req_item = QTreeWidgetItem(item)
            req_item.setText(0, req.formatted_display())

            # Column 1: Quantity (always shown)
            req_item.setText(1, req.formatted_qty())

            # Column 2: Details (varies by view mode)
            if self.detailed_view:
                # Detailed view: Show full details matching screenshot
                if req.has_child_work_order():
                    # Sub-work-order: Show date range
                    req_item.setText(2, req.formatted_dates())
                    logger.debug(f"DETAILED VIEW: Req (sub-WO) - dates: {req.formatted_dates()}")
                else:
                    # Regular part: Show status and quantity details
                    req_item.setText(2, req.formatted_details())
                    logger.debug(f"DETAILED VIEW: Req (part {req.part_id}) - details: {req.formatted_details()}")
            else:
                # Simplified view: Show simplified details for M-parts and sub-WOs
                if req.has_child_work_order():
                    # Sub-work-order: Show dates even in simplified
                    req_item.setText(2, req.formatted_dates())
                else:
                    # M-parts: Show type
                    req_item.setText(2, f"Type: {req.part_type or 'Mfg'}")
                logger.debug(f"SIMPLIFIED VIEW: Showing part {req.part_id}")

            # T052: Check for child work order via SUBORD_WO_SUB_ID
            if req.has_child_work_order():
                if self.detailed_view:
                    # Detailed view: ALWAYS expandable to show operations
                    req_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

                    # Store data for loading sub-work-order's operations directly
                    req_node_data = TreeNodeData(
                        node_type="SUB_WORK_ORDER",
                        base_id=node_data.base_id,
                        lot_id=node_data.lot_id,
                        sub_id=req.subord_wo_sub_id,  # Child work order SUB_ID
                        part_id=req.part_id,
                        children_loaded=False
                    )
                    req_item.setData(0, Qt.ItemDataRole.UserRole, req_node_data)
                    logger.debug(f"  → Sub-WO {req.subord_wo_sub_id} is expandable (detailed view)")
                else:
                    # Simplified view: Only expandable if it has children (other sub-work-orders)
                    # Check if this sub-work-order has child sub-work-orders
                    try:
                        child_requirements = self.service.get_requirements_by_sub_id(
                            node_data.base_id,
                            node_data.lot_id,
                            req.subord_wo_sub_id
                        )
                        has_children = any(child_req.has_child_work_order() for child_req in child_requirements)

                        if has_children:
                            # Has child sub-work-orders - make it expandable
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
                            logger.debug(f"  → Sub-WO {req.subord_wo_sub_id} is expandable (has {len([r for r in child_requirements if r.has_child_work_order()])} child sub-WOs)")
                        else:
                            # No children - it's a leaf node in simplified view
                            logger.debug(f"  → Sub-WO {req.subord_wo_sub_id} is leaf node (no child sub-WOs)")
                    except Exception as e:
                        # If query fails, make it expandable to allow user to try
                        logger.warning(f"Could not check children for sub-WO {req.subord_wo_sub_id}: {e}")
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

        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"{'DETAILED' if self.detailed_view else 'SIMPLIFIED'} VIEW SUMMARY:")
        logger.info(f"  Total requirements: {total_count}")
        logger.info(f"  Shown: {shown_count}")
        logger.info(f"  Filtered out: {filtered_count}")
        logger.info(f"{'='*80}")
        logger.info(f"")

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
