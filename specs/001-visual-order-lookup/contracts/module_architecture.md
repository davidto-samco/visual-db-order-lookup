# Module Architecture
# Visual Database Multi-Module Application
# Date: 2025-11-07

## Overview

This document defines the architectural design for the three-module Visual database application. The architecture supports **Sales (Customer Order Entry)**, **Inventory (Part Maintenance)**, and **Engineering (Manufacturing Window)** modules with shared infrastructure and independent UI components.

**Key Principles**:
- Left navigation panel for module selection
- Single shared database connection across all modules
- State preservation when switching modules
- Async database operations via worker threads
- Minimal UI with focused functionality per module

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MainWindow                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    QHBoxLayout (main_layout)              │  │
│  │  ┌──────────────┬──────────────────────────────────────┐  │  │
│  │  │              │                                      │  │  │
│  │  │ Navigation   │       Module Container               │  │  │
│  │  │   Panel      │       (QStackedWidget)               │  │  │
│  │  │              │                                      │  │  │
│  │  │ ┌──────────┐ │  ┌────────────────────────────────┐  │  │  │
│  │  │ │ Sales    │ │  │     Sales Module               │  │  │  │
│  │  │ │ (Active) │ │  │  ┌──────────────────────────┐  │  │  │  │
│  │  │ └──────────┘ │  │  │ DateRangePanel           │  │  │  │  │
│  │  │ ┌──────────┐ │  │  │ SearchPanel              │  │  │  │  │
│  │  │ │Inventory │ │  │  │ QSplitter                │  │  │  │  │
│  │  │ │          │ │  │  │  ├─ OrderListView        │  │  │  │  │
│  │  │ └──────────┘ │  │  │  └─ OrderDetailView      │  │  │  │  │
│  │  │ ┌──────────┐ │  │  └──────────────────────────┘  │  │  │  │
│  │  │ │Engineer  │ │  └────────────────────────────────┘  │  │  │
│  │  │ │   -ing   │ │                                      │  │  │
│  │  │ └──────────┘ │  ┌────────────────────────────────┐  │  │  │
│  │  │              │  │   Inventory Module (hidden)    │  │  │  │
│  │  │ 200px        │  └────────────────────────────────┘  │  │  │
│  │  │ Fixed Width  │  ┌────────────────────────────────┐  │  │  │
│  │  │              │  │  Engineering Module (hidden)   │  │  │  │
│  │  └──────────────┴──└────────────────────────────────┘  │  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Navigation Panel

**Class**: `NavigationPanel` (QWidget)

**Purpose**: Left-hand vertical panel with three module selection buttons

**Specifications**:
- **Width**: 200px (fixed, non-resizable)
- **Height**: Expands to fill window height
- **Implementation**: QListWidget with custom items

**QListWidget Configuration**:
```python
self.nav_list = QListWidget()
self.nav_list.setFixedWidth(200)
self.nav_list.setIconSize(QSize(32, 32))
self.nav_list.setSpacing(5)

# Add three module items
self.nav_list.addItem(QListWidgetItem(QIcon(":/icons/sales.svg"), "Sales"))
self.nav_list.addItem(QListWidgetItem(QIcon(":/icons/inventory.svg"), "Inventory"))
self.nav_list.addItem(QListWidgetItem(QIcon(":/icons/engineering.svg"), "Engineering"))

# Set default selection
self.nav_list.setCurrentRow(0)  # Sales selected by default
```

**Visual Indication of Active Module**:

Three visual cues indicate the active module:
1. **Background color change** (darker blue)
2. **Left border accent** (4px bright blue)
3. **Text color change** (white text on dark background)

**QSS Stylesheet**:
```css
/* Navigation Panel */
QListWidget {
    background-color: #f5f5f5;
    border: none;
    outline: none;
    font-size: 14px;
    font-weight: 500;
}

QListWidget::item {
    padding: 15px 10px;
    border-left: 4px solid transparent;
    color: #333;
    background-color: transparent;
}

QListWidget::item:selected {
    background-color: #0d47a1;      /* Dark blue for active */
    border-left: 4px solid #2196f3; /* Bright blue accent */
    color: white;
}

QListWidget::item:hover {
    background-color: #e0e0e0;      /* Light gray on hover */
}

QListWidget::item:selected:hover {
    background-color: #1565c0;      /* Slightly lighter blue when hovering selected */
}
```

**Module Switching Signal**:
```python
# Connect navigation selection to module switching
self.nav_list.currentRowChanged.connect(self.module_stack.setCurrentIndex)
```

**Icon Specifications**:
- **Size**: 32x32px
- **Format**: SVG (scalable) or PNG with @2x for HiDPI
- **Suggested icons** (Material Icons):
  - Sales: `receipt`, `shopping_cart`, `attach_money`
  - Inventory: `inventory_2`, `warehouse`, `category`
  - Engineering: `engineering`, `build`, `settings`

---

### 2. Module Container (QStackedWidget)

**Class**: QStackedWidget

**Purpose**: Container for module widgets; shows one module at a time

**Specifications**:
- **Index 0**: Sales Module (SalesModule widget)
- **Index 1**: Inventory Module (InventoryModule widget)
- **Index 2**: Engineering Module (EngineeringModule widget)

**State Preservation**:
- All three module widgets loaded on application startup
- Widgets remain in memory when hidden (not destroyed)
- Switching modules via `setCurrentIndex()` preserves:
  - Table/tree widget contents (rows/nodes)
  - Scroll positions
  - Selection states
  - Input field values
  - Expanded/collapsed states (tree widgets)
  - Child widget visibility

**Example State Preservation Scenario**:
```
1. User loads 100 orders in Sales module, scrolls to row 50, selects order #4049
2. User switches to Inventory module (Sales widget hidden, Inventory widget shown)
3. User searches for part F0195, views where-used results
4. User switches back to Sales module
   → Still shows 100 orders, scrolled to row 50, order #4049 selected
   → NO re-query, NO state loss
```

**Memory Impact**:
- Three modules loaded: ~5-15 MB total (acceptable for desktop application)
- Alternative (lazy loading): Only load module on first access (adds complexity, minimal memory benefit)

**Recommendation**: Load all three modules upfront for simplicity and instant switching.

---

### 3. Module Widgets

Each module is a self-contained QWidget with its own UI components and service layer.

#### Sales Module (SalesModule)

**Class**: `SalesModule` (QWidget)

**Components** (existing, wrapped in module container):
- **DateRangePanel**: Date filter controls
- **SearchPanel**: Job number and customer name search
- **OrderListView**: QTableView displaying OrderSummary results
- **OrderDetailView**: QSplitter with order acknowledgement display

**Service**: OrderService (existing)

**State**:
- Current order list (100 orders by default)
- Selected order
- Date range filter values
- Search query text
- Scroll position and selection

#### Inventory Module (InventoryModule)

**Class**: `InventoryModule` (QWidget)

**Components** (new):
- **PartSearchPanel**: Part number search input
- **PartDetailView**: Tabbed interface with three tabs:
  - **Part Info Tab**: Part master data (description, costs, quantities, vendor)
  - **Where Used Tab**: QTableView showing WhereUsed results
  - **Purchase History Tab**: QTableView showing PurchaseHistory results

**Layout**:
```
InventoryModule (QWidget)
├── QVBoxLayout
    ├── PartSearchPanel (QWidget)
    │   ├── QLabel: "Part Number:"
    │   ├── QLineEdit: part_number_input
    │   └── QPushButton: "Search"
    │
    └── PartDetailView (QTabWidget)
        ├── Tab 0: Part Info (QWidget with QTextBrowser for HTML template)
        ├── Tab 1: Where Used (QTableView)
        └── Tab 2: Purchase History (QTableView)
```

**Service**: PartService (new)

**State**:
- Current part number search
- Part info data
- Where-used results (table rows)
- Purchase history results (table rows)
- Active tab selection

#### Engineering Module (EngineeringModule)

**Class**: `EngineeringModule` (QWidget)

**Components** (new):
- **JobSearchPanel**: Job number search input with lazy loading toggle
- **BOMTreeView**: QTreeWidget displaying hierarchical BOM structure

**Layout**:
```
EngineeringModule (QWidget)
├── QVBoxLayout
    ├── JobSearchPanel (QWidget)
    │   ├── QLabel: "Job Number:"
    │   ├── QLineEdit: job_number_input
    │   ├── QPushButton: "Load BOM"
    │   └── QCheckBox: "Use lazy loading (for large jobs)"
    │
    └── BOMTreeView (QTreeWidget)
        ├── Column 0: Base/Lot ID (e.g., "8113/26")
        ├── Column 1: Description
        ├── Column 2: Drawing Number
        ├── Column 3: Quantity
        └── Column 4: Material
```

**Tree Structure**:
```
Job 8113
├── Assembly 01 (LOT_ID=01)
│   ├── Part M1234 - Manufactured part (black)
│   └── Part P5678 - Purchased part (red)
├── Assembly 26 (LOT_ID=26) - Roll former (blue)
│   ├── Part M0001 (black)
│   ├── Part P0002 (red)
│   └── ... (330+ parts total)
└── Assembly 41 (LOT_ID=41) - Hydraulics (blue)
    └── ...
```

**Color Coding**:
- **Blue text**: Assemblies (node_type='A')
- **Black text**: Manufactured parts (node_type='M')
- **Red text**: Purchased parts (node_type='P')
- **Gray text**: Other (node_type='O')

**Lazy Loading**:
- If checkbox enabled: Load only assemblies (get_bom_assemblies), expand on demand
- If checkbox disabled: Load full hierarchy (get_bom_hierarchy)

**Service**: BOMService (new)

**State**:
- Current job number
- BOM tree structure (all nodes)
- Expanded/collapsed state of tree nodes
- Selected tree item
- Lazy loading enabled/disabled

---

## Service Layer Architecture

All three modules share database infrastructure but have independent service classes.

```
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ OrderService   │  │  PartService   │  │  BOMService  │  │
│  │  (existing)    │  │    (new)       │  │    (new)     │  │
│  ├────────────────┤  ├────────────────┤  ├──────────────┤  │
│  │ - search_by_   │  │ - search_by_   │  │ - get_bom_   │  │
│  │   job_number   │  │   part_number  │  │   hierarchy  │  │
│  │ - search_by_   │  │ - get_where_   │  │ - get_bom_   │  │
│  │   customer     │  │   used         │  │   assemblies │  │
│  │ - filter_by_   │  │ - get_purchase │  │ - get_asm_   │  │
│  │   date_range   │  │   _history     │  │   parts      │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│           │                  │                   │          │
│           └──────────────────┴───────────────────┘          │
│                              │                              │
│                 ┌────────────▼────────────┐                 │
│                 │  DatabaseConnection     │                 │
│                 │  (shared instance)      │                 │
│                 ├─────────────────────────┤                 │
│                 │ - execute_query()       │                 │
│                 │ - execute_async()       │                 │
│                 │ - timeout: 30s          │                 │
│                 │ - read_only: True       │                 │
│                 └─────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

**Shared DatabaseConnection**:
- Single instance created on application startup
- Passed to all three service classes
- Manages connection pooling and error handling
- Enforces 30-second query timeout
- Ensures read-only access (constitution compliance)

**Service Method Pattern**:

All service methods follow the same pattern:

```python
class PartService:
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def search_by_part_number(self, part_number: str) -> Part | None:
        """
        Searches for part by part number.

        Args:
            part_number: Part number to search for

        Returns:
            Part object if found, None if not found

        Raises:
            ConnectionError: Database connection failed
            TimeoutError: Query exceeded 30s timeout
        """
        # 1. Validate input
        if not part_number or len(part_number) > 30:
            raise ValueError("Invalid part number")

        # 2. Normalize input
        part_number = part_number.strip().upper()

        # 3. Execute query (synchronous, called from worker thread)
        result = self.db.execute_query(PART_LOOKUP_QUERY, part_number)

        # 4. Transform to entity
        if result:
            return Part(**result[0])
        return None
```

---

## Thread Management

All database operations run in background threads to prevent UI freezing.

**DatabaseWorker Pattern** (existing, reused for all modules):

```python
class DatabaseWorker(QThread):
    """
    Worker thread for async database operations.
    Emits signals with results or errors.
    """
    result_ready = pyqtSignal(object)  # Success signal
    error_occurred = pyqtSignal(str)   # Error signal

    def __init__(self, service_method, *args, **kwargs):
        super().__init__()
        self.service_method = service_method
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.service_method(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except ConnectionError as e:
            self.error_occurred.emit(f"Connection error: {e}")
        except TimeoutError as e:
            self.error_occurred.emit(f"Query timeout: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {e}")
```

**Usage Example** (Inventory Module):

```python
class InventoryModule(QWidget):
    def search_part(self):
        # Show loading indicator
        self.loading_dialog.show("Searching for part...")

        # Create worker thread
        part_number = self.part_input.text()
        self.worker = DatabaseWorker(
            self.part_service.search_by_part_number,
            part_number
        )

        # Connect signals
        self.worker.result_ready.connect(self.on_part_found)
        self.worker.error_occurred.connect(self.on_error)

        # Start thread
        self.worker.start()

    def on_part_found(self, part: Part):
        self.loading_dialog.hide()
        if part:
            self.display_part_info(part)
        else:
            QMessageBox.information(self, "Not Found",
                                    f"Part '{self.part_input.text()}' not found")

    def on_error(self, error_message: str):
        self.loading_dialog.hide()
        QMessageBox.critical(self, "Error", error_message)
```

**Thread Cleanup on Module Switch**:

Worker threads remain active during module switching (signals delivered to hidden widgets). Cleanup occurs only on application exit.

```python
class MainWindow(QMainWindow):
    def closeEvent(self, event):
        """Call cleanup on all modules before exit"""
        self.sales_module.cleanup()
        self.inventory_module.cleanup()
        self.engineering_module.cleanup()
        event.accept()

class InventoryModule(QWidget):
    def cleanup(self):
        """Stop running worker threads"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)  # Wait max 3 seconds
            self.worker.deleteLater()
```

---

## Navigation Flow

**User Action**: Click "Inventory" in navigation panel

**System Response**:

1. **QListWidget** emits `currentRowChanged(1)` signal
2. **Signal connected to** `QStackedWidget.setCurrentIndex(1)`
3. **QStackedWidget** hides current widget (Sales), shows Inventory widget
4. **Sales widget** remains in memory with all state preserved
5. **Inventory widget** becomes visible (if first time, shows empty state; if returning, shows previous search results)

**Performance**: <10ms (instant visual transition)

**State Preservation**: Automatic (no code required)

---

## Error Handling

All modules share the same error handling patterns:

**Connection Errors**:
- Display: "Could not connect to Visual database. Please check network connection."
- Action: Allow retry

**Timeout Errors**:
- Display: "Query timed out after 30 seconds. Please try again or narrow your search."
- Action: Allow retry or suggest different query

**No Results**:
- Display: "No results found for [search term]."
- Action: Clear search, allow new query

**Invalid Input**:
- Display: "Invalid [field name]. [Validation rule]."
- Action: Highlight input field, show validation message

---

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Module switching | <100ms | Time from click to UI update |
| Part search (exact) | <5ms | Database query execution |
| Where-used query | <200ms | Database query execution |
| BOM assemblies load | <100ms | Database query execution |
| BOM full hierarchy (small) | <500ms | 30-100 work orders |
| BOM full hierarchy (large) | <10s | 700+ work orders |
| UI rendering (tree) | <500ms | 700 nodes to QTreeWidget |

**Monitoring**: Log all database query times; alert if exceeding targets.

---

## Testing Strategy

**Unit Tests**:
- Test each service method independently with mock database
- Verify input validation
- Verify error handling

**Integration Tests**:
- Test module UI with live database (test data)
- Verify state preservation when switching modules
- Verify worker thread cleanup

**Performance Tests**:
- Measure query execution times for 100 random parts
- Measure BOM load times for large jobs (8113, 8059)
- Measure memory footprint with all modules active

---

## Summary

This architecture provides:

- **Simple navigation**: 200px left panel with three clear module buttons
- **State preservation**: All modules remain in memory; switching preserves all state
- **Shared infrastructure**: Single database connection, error handling, threading pattern
- **Module independence**: Each module self-contained with dedicated service layer
- **Performance**: Background threads prevent UI freezing, lazy loading for large datasets
- **Constitution compliance**: Read-only database access, local-first execution

**Total Components**:
- 1 NavigationPanel
- 1 QStackedWidget
- 3 Module widgets (Sales, Inventory, Engineering)
- 3 Service classes (OrderService, PartService, BOMService)
- 1 DatabaseConnection (shared)
- 1 DatabaseWorker pattern (shared)

**Lines of Code Estimate**:
- NavigationPanel: ~50 lines
- Module architecture: ~100 lines (MainWindow modifications)
- InventoryModule: ~300 lines
- EngineeringModule: ~400 lines (tree complexity)
- PartService: ~200 lines
- BOMService: ~250 lines
- **Total new code**: ~1,300 lines (excludes existing Sales module)
