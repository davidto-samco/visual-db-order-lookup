# Quickstart Guide: Engineering Module Implementation

**Feature**: 003-engineering-work-order-hierarchy
**Date**: 2025-01-14
**Estimated Effort**: 5-7 days

## Overview

This guide provides step-by-step instructions for implementing the Engineering module for work order hierarchy viewing. Follow the phases sequentially.

## Prerequisites

- Existing visual-db-order-lookup application with Sales and Inventory modules
- Python 3.11+ environment
- PyQt6 installed
- Access to Visual SQL Server database (WLAN)
- Read permissions on WORK_ORDER, OPERATION, REQUIREMENT, PART, LABOR_TICKET, INVENTORY_TRANS, WIP_BALANCE tables

## Implementation Phases

### Phase 1: Database Layer (Day 1)

**Goal**: Create data models and query functions

**1.1 Add Data Models**

File: `visual_order_lookup/database/models.py`

```python
# Add at end of file after existing Part, WhereUsed, PurchaseHistory models

@dataclass
class WorkOrder:
    """Work order header from WORK_ORDER table."""
    base_id: str
    lot_id: str
    sub_id: str
    part_id: str
    part_description: Optional[str]
    order_qty: Decimal
    type: str  # M or W
    status: str
    start_date: Optional[date]
    complete_date: Optional[date]
    created_date: datetime

    def formatted_id(self) -> str:
        if self.sub_id:
            return f"{self.base_id}-{self.sub_id}/{self.lot_id}"
        return f"{self.base_id}/{self.lot_id}"

    def formatted_status(self) -> str:
        if self.status == "Closed":
            return "[C]"
        return f"[{self.status[0]}]"

    def formatted_qty(self) -> str:
        return f"{self.order_qty:.4f}"

@dataclass
class Operation:
    """Manufacturing operation from OPERATION table."""
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str
    sequence: int
    operation_id: str
    description: str
    department_id: Optional[str]
    setup_hrs: Decimal
    run_hrs: Decimal
    status: Optional[str]

    def formatted_sequence(self) -> str:
        return f"[{self.sequence}]"

    def formatted_description(self) -> str:
        return f"{self.formatted_sequence()} - {self.description}"

    def formatted_hours(self) -> str:
        return f"Setup: {self.setup_hrs:.2f} Hrs, Run: {self.run_hrs:.2f} Hrs/unit"

# Add remaining models: Requirement, LaborTicket, InventoryTransaction, WIPBalance
# (See data-model.md for complete definitions)
```

**1.2 Create Query Module**

File: `visual_order_lookup/database/work_order_queries.py`

```python
"""SQL query definitions for work order operations in Visual database."""

import logging
from typing import List
from decimal import Decimal
import pyodbc
from visual_order_lookup.database.models import WorkOrder, Operation, Requirement, LaborTicket, InventoryTransaction, WIPBalance

logger = logging.getLogger(__name__)

def search_work_orders(cursor: pyodbc.Cursor, base_id_pattern: str, limit: int = 1000) -> List[WorkOrder]:
    """Search for work orders by BASE_ID pattern."""
    if not base_id_pattern or not base_id_pattern.strip():
        raise ValueError("BASE_ID pattern cannot be empty")

    query = """
        SELECT TOP (?)
               wo.BASE_ID, wo.LOT_ID, wo.SUB_ID, wo.PART_ID,
               p.DESCRIPTION AS part_description,
               wo.TYPE, wo.STATUS, wo.START_DATE, wo.COMPLETE_DATE,
               wo.ORDER_QTY, wo.CREATE_DATE
        FROM WORK_ORDER wo WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
        WHERE wo.BASE_ID LIKE ?
        ORDER BY wo.CREATE_DATE DESC
    """

    try:
        cursor.execute(query, (limit, base_id_pattern.strip().upper() + '%'))
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append(WorkOrder(
                base_id=row.BASE_ID.strip() if row.BASE_ID else "",
                lot_id=row.LOT_ID.strip() if row.LOT_ID else "",
                sub_id=row.SUB_ID.strip() if row.SUB_ID else "",
                part_id=row.PART_ID.strip() if row.PART_ID else "",
                part_description=row.part_description.strip() if row.part_description else None,
                order_qty=Decimal(str(row.ORDER_QTY)) if row.ORDER_QTY else Decimal("0"),
                type=row.TYPE.strip() if row.TYPE else "",
                status=row.STATUS.strip() if row.STATUS else "",
                start_date=row.START_DATE,
                complete_date=row.COMPLETE_DATE,
                created_date=row.CREATE_DATE
            ))

        logger.info(f"Retrieved {len(records)} work orders for pattern {base_id_pattern}")
        return records

    except pyodbc.Error as e:
        logger.error(f"Database error searching work orders: {e}")
        raise Exception(f"Failed to search work orders: {str(e)}")

# Add remaining query functions: get_operations, get_requirements, etc.
# (See contracts/work_order_queries.sql for SQL)
```

**Testing**: Run unit tests for models and queries
```bash
pytest tests/unit/test_work_order_models.py
pytest tests/unit/test_work_order_queries.py
```

### Phase 2: Service Layer (Day 2)

**Goal**: Create WorkOrderService business logic

File: `visual_order_lookup/services/work_order_service.py`

```python
"""Business logic for work order operations."""

import logging
from typing import List, Optional
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database import work_order_queries
from visual_order_lookup.database.models import WorkOrder, Operation, Requirement, LaborTicket, InventoryTransaction, WIPBalance

logger = logging.getLogger(__name__)

class WorkOrderService:
    """Service for work order hierarchy data retrieval."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection

    def search_work_orders(self, base_id_pattern: str, limit: int = 1000) -> List[WorkOrder]:
        """Search for work orders by BASE_ID pattern."""
        if not base_id_pattern or not base_id_pattern.strip():
            raise ValueError("BASE_ID pattern cannot be empty")

        base_id_pattern = base_id_pattern.strip().upper()
        logger.info(f"Searching work orders: {base_id_pattern}")

        try:
            cursor = self.db_connection.get_cursor()
            records = work_order_queries.search_work_orders(cursor, base_id_pattern, limit)
            cursor.close()
            return records
        except Exception as e:
            logger.error(f"Error searching work orders: {e}")
            raise

    def get_operations(self, base_id: str, lot_id: str, sub_id: str) -> List[Operation]:
        """Get all operations for a work order (lazy load)."""
        # Implementation...

    # Add remaining service methods
```

**Testing**: Run unit tests for service
```bash
pytest tests/unit/test_work_order_service.py
```

### Phase 3: UI - Custom Tree Widget (Day 3)

**Goal**: Create reusable tree widget for hierarchical display

File: `visual_order_lookup/ui/work_order_tree.py`

```python
"""Custom tree widget for work order hierarchy display."""

import logging
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from visual_order_lookup.services.work_order_service import WorkOrderService
from visual_order_lookup.database.models import WorkOrder

logger = logging.getLogger(__name__)

class WorkOrderTreeWidget(QTreeWidget):
    """Custom tree widget with lazy loading for work order hierarchy."""

    # Signals
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, service: WorkOrderService):
        super().__init__()
        self.service = service
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Configure tree widget appearance."""
        self.setColumnCount(3)
        self.setHeaderLabels(["Description", "Quantity", "Details"])
        self.setAlternatingRowColors(True)
        self.setAnimated(True)  # Smooth expand/collapse

    def connect_signals(self):
        """Connect tree signals for lazy loading."""
        self.itemExpanded.connect(self.on_item_expanded)

    def load_work_order(self, work_order: WorkOrder):
        """Load work order as root node."""
        self.clear()

        # Create header node
        header = QTreeWidgetItem(self)
        header.setText(0, f"{work_order.formatted_status()} {work_order.formatted_id()} - {work_order.part_description or work_order.part_id}")
        header.setText(1, work_order.formatted_qty())
        header.setText(2, f"Status: {work_order.status}")

        # Store work order data
        header.setData(0, Qt.ItemDataRole.UserRole, {
            'type': 'HEADER',
            'base_id': work_order.base_id,
            'lot_id': work_order.lot_id,
            'sub_id': work_order.sub_id,
            'entity': work_order
        })

        # Add placeholder children for lazy loading
        self.add_placeholder_children(header, work_order)

    def add_placeholder_children(self, header: QTreeWidgetItem, work_order: WorkOrder):
        """Add placeholder nodes for lazy loading."""
        # Operations node
        operations_node = QTreeWidgetItem(header)
        operations_node.setText(0, "Operations")
        operations_node.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        operations_node.setData(0, Qt.ItemDataRole.UserRole, {
            'type': 'OPERATIONS_PLACEHOLDER',
            'base_id': work_order.base_id,
            'lot_id': work_order.lot_id,
            'sub_id': work_order.sub_id
        })

        # Labor, Materials, WIP nodes...

    def on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - lazy load children."""
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data:
            return

        # Check if already loaded
        if item.childCount() > 0 and not node_data.get('type', '').endswith('_PLACEHOLDER'):
            return  # Already loaded

        # Load based on node type
        node_type = node_data['type']
        if node_type == 'OPERATIONS_PLACEHOLDER':
            self.load_operations(item, node_data)
        elif node_type == 'OPERATION':
            self.load_requirements(item, node_data)
        # Handle other node types...

    def load_operations(self, parent_item: QTreeWidgetItem, node_data: dict):
        """Load operations for work order."""
        try:
            self.loading_started.emit()
            operations = self.service.get_operations(
                node_data['base_id'],
                node_data['lot_id'],
                node_data['sub_id']
            )

            # Clear placeholder
            parent_item.takeChildren()

            # Add operation nodes
            for op in operations:
                op_item = QTreeWidgetItem(parent_item)
                op_item.setText(0, op.formatted_description())
                op_item.setText(2, op.formatted_hours())
                op_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
                op_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'OPERATION',
                    'base_id': node_data['base_id'],
                    'lot_id': node_data['lot_id'],
                    'sub_id': node_data['sub_id'],
                    'operation_seq': op.sequence,
                    'entity': op
                })

            self.loading_finished.emit()

        except Exception as e:
            logger.error(f"Error loading operations: {e}")
            self.error_occurred.emit(f"Failed to load operations: {str(e)}")
            self.loading_finished.emit()
```

**Testing**: Run integration tests for tree widget
```bash
pytest tests/integration/test_engineering_module.py
```

### Phase 4: UI - Engineering Module (Day 4)

**Goal**: Create main Engineering module interface

File: `visual_order_lookup/ui/engineering_module.py`

```python
"""Engineering module for work order hierarchy viewing."""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from visual_order_lookup.services.work_order_service import WorkOrderService
from visual_order_lookup.ui.work_order_tree import WorkOrderTreeWidget

logger = logging.getLogger(__name__)

class EngineeringModule(QWidget):
    """Engineering module - work order hierarchy viewer."""

    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.service = WorkOrderService(db_connection)
        self.setup_ui()

    def setup_ui(self):
        """Set up the engineering module UI."""
        layout = QVBoxLayout(self)

        # Search panel
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Work Order BASE_ID:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter BASE_ID (e.g., 8113)")
        self.search_input.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Work order list
        self.work_order_list = QListWidget()
        self.work_order_list.itemClicked.connect(self.on_work_order_selected)
        layout.addWidget(self.work_order_list)

        # Tree view
        self.tree = WorkOrderTreeWidget(self.service)
        self.tree.loading_started.connect(self.on_loading_started)
        self.tree.loading_finished.connect(self.on_loading_finished)
        self.tree.error_occurred.connect(self.on_error)
        layout.addWidget(self.tree)

        # Export button
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.on_export)
        layout.addWidget(self.export_btn)

    def on_search(self):
        """Handle search button click."""
        base_id = self.search_input.text().strip()
        if not base_id:
            QMessageBox.warning(self, "Search Error", "Please enter a BASE_ID to search.")
            return

        try:
            results = self.service.search_work_orders(base_id)
            self.work_order_list.clear()

            for wo in results:
                item = QListWidgetItem(f"{wo.formatted_id()} - {wo.part_description or wo.part_id}")
                item.setData(Qt.ItemDataRole.UserRole, wo)
                self.work_order_list.addItem(item)

            if not results:
                QMessageBox.information(self, "No Results", f"No work orders found matching '{base_id}'.")

        except Exception as e:
            logger.error(f"Search error: {e}")
            QMessageBox.critical(self, "Search Error", f"Failed to search work orders:\n{str(e)}")

    def on_work_order_selected(self, item: QListWidgetItem):
        """Handle work order selection from list."""
        work_order = item.data(Qt.ItemDataRole.UserRole)
        self.tree.load_work_order(work_order)

    def on_loading_started(self):
        """Handle loading started."""
        # Show loading indicator

    def on_loading_finished(self):
        """Handle loading finished."""
        # Hide loading indicator

    def on_error(self, error_message: str):
        """Handle error from tree widget."""
        QMessageBox.critical(self, "Error", error_message)

    def on_export(self):
        """Handle export to CSV."""
        # Implement CSV export logic
```

**Testing**: Manual UI testing with test work orders

### Phase 5: Integration (Day 5)

**Goal**: Integrate Engineering module into main application

**5.1 Update Main Window**

File: `visual_order_lookup/ui/main_window.py`

```python
# In __init__ method, after Sales and Inventory modules:

# Engineering module
self.engineering_module = EngineeringModule(self.db_connection)
self.tab_widget.addTab(self.engineering_module, "Engineering")
```

**5.2 Update Left Sidebar (if applicable)**

Add Engineering module icon/button to sidebar navigation.

**Testing**: Full integration testing
```bash
# Run application
python visual_order_lookup/main.py

# Test workflow:
# 1. Click Engineering tab
# 2. Search for "8113"
# 3. Select work order
# 4. Expand operations
# 5. Expand operation to see requirements
# 6. Test lazy loading performance
```

### Phase 6: Polish & Performance (Day 6-7)

**Goal**: Optimize and add finishing touches

**6.1 Performance Optimization**
- Verify lazy loading works smoothly
- Test with large work orders (1000+ nodes)
- Profile query times

**6.2 CSV Export**
- Implement hierarchical CSV export
- Test export with large trees

**6.3 Keyboard Navigation**
- Test arrow keys, space, enter
- Ensure accessibility

**6.4 Visual Polish**
- Add icons for node types (optional)
- Verify styling matches Sales/Inventory
- Test expand all / collapse all buttons

## Testing Checklist

- [ ] Unit tests pass for models
- [ ] Unit tests pass for queries
- [ ] Unit tests pass for service
- [ ] Integration tests pass for tree widget
- [ ] Integration tests pass for module
- [ ] Manual testing: Search work orders
- [ ] Manual testing: Lazy loading operations
- [ ] Manual testing: Lazy loading requirements
- [ ] Manual testing: Keyboard navigation
- [ ] Manual testing: CSV export
- [ ] Performance testing: 500-node tree <2s
- [ ] Performance testing: Expand/collapse <100ms

## Common Issues & Solutions

### Issue: Tree doesn't expand
**Solution**: Check `setChildIndicatorPolicy(ShowIndicator)` is set

### Issue: Slow lazy loading
**Solution**: Verify queries use indexes, check NOLOCK hint

### Issue: Memory growth
**Solution**: Verify children cached in tree items, not reloaded

### Issue: CSV export incomplete
**Solution**: Ensure recursive traversal includes all expanded nodes

## Next Steps

After implementation complete:
1. Run `/speckit.tasks` to generate task breakdown
2. Begin implementation following this quickstart
3. Create feature branch: `git checkout -b 003-engineering-module`
4. Commit incrementally after each phase
5. Test thoroughly before merging to main

## Resources

- [PyQt6 QTreeWidget Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTreeWidget.html)
- [SQL Server NOLOCK Documentation](https://docs.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-table)
- Project constitution: `.specify/memory/constitution.md`
- Feature spec: `specs/main/spec.md`
- Data model: `specs/main/data-model.md`
- API contracts: `specs/main/contracts/`
