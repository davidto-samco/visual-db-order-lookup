# Phase 0 Research: Engineering Module - Work Order Hierarchy Viewer

**Date**: 2025-01-14
**Feature**: 003-engineering-work-order-hierarchy
**Status**: Complete

## Research Questions

### 1. PyQt6 Tree Control for Hierarchical Display

**Question**: What is the best approach for displaying expandable/collapsible hierarchical work order data in PyQt6?

**Research**:
- PyQt6 provides `QTreeWidget` (item-based) and `QTreeView` + `QStandardItemModel` (model-based)
- Legacy VISUAL screenshots show typical tree control with expand/collapse icons
- Need lazy loading support for performance with large trees

**Decision**: Use `QTreeWidget` for hierarchical display

**Rationale**:
- Item-based API simpler for tree manipulation (add/remove nodes dynamically)
- Built-in expand/collapse with `[+]`/`[-]` icons matching VISUAL appearance
- Supports lazy loading via `QTreeWidgetItem.setChildIndicatorPolicy()`
- Can detect expansion via `itemExpanded` signal to trigger child loading
- Used successfully in similar industrial applications

**Alternatives Considered**:
- `QTreeView` + `QStandardItemModel`: More complex for dynamic loading, requires custom model
- Custom tree widget from scratch: Unnecessary complexity, reinventing wheel
- Third-party tree controls: Additional dependency, inconsistent styling

**Implementation Notes**:
```python
# Lazy loading pattern
def on_item_expanded(item):
    if item.childCount() == 0:  # Not yet loaded
        load_children(item)

item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)  # Force [+] icon
```

### 2. Database Query Strategy for 7-Level Hierarchy

**Question**: Should we load the entire work order hierarchy in one query or use separate queries per level?

**Research**:
- Single query approach: Complex JOIN across 7 tables, returns denormalized data
- Separate queries: Simple queries, load on-demand (lazy), but more round-trips
- Hybrid: Load header + operations upfront, lazy load requirements/details

**Decision**: Lazy loading with separate queries per level

**Rationale**:
- **Performance**: Most users only expand a few nodes, not entire tree. Loading 500+ requirements upfront wastes time.
- **Memory**: Lazy loading keeps memory footprint small (Constitutional requirement <100MB)
- **Network**: WLAN connection prefers many small queries vs one huge JOIN
- **User Experience**: Tree header loads quickly, details load as expanded (feels responsive)
- **Simplicity**: Individual queries easier to optimize and debug than complex 7-table JOIN

**Query Breakdown**:
1. **On search**: Load work order list (WORK_ORDER + PART)
2. **On selection**: Load header + top-level nodes (WORK_ORDER + counts)
3. **On expand Operations**: Load OPERATION records for that work order
4. **On expand Operation**: Load REQUIREMENT records for that operation
5. **On expand Requirement**: Load PART details for that part
6. **On expand Labor**: Load LABOR_TICKET records
7. **On expand Materials**: Load INVENTORY_TRANS records
8. **On expand WIP**: Load WIP_BALANCE record

**Alternatives Considered**:
- Single mega-query: 7-table JOIN would be slow, return thousands of duplicate rows, complex to parse
- Load everything upfront: Wastes memory and time for unused data
- Caching: Adds complexity, unnecessary for read-only historical data

**Performance Impact**:
- Search query: ~200ms (WORK_ORDER + PART for 100 results)
- Header load: ~50ms (single WORK_ORDER record)
- Operation load: ~100ms (10-50 operations typical)
- Requirement load per operation: ~50ms (5-20 requirements typical)
- Total perceived load: <1 second for typical use (only expand what's needed)

### 3. Tree Node Identification and State Management

**Question**: How should we uniquely identify tree nodes for expand/collapse state and data retrieval?

**Research**:
- Need to distinguish node types (Header, Operation, Requirement, Labor, etc.)
- Need to store query parameters (BASE_ID, LOT_ID, SUB_ID, OPERATION_SEQ)
- QTreeWidget supports custom data via `setData(column, Qt.UserRole, value)`

**Decision**: Store node type and query data in QTreeWidgetItem.data()

**Rationale**:
- `Qt.UserRole` provides type-safe storage for custom data
- Can store Python objects (dict, dataclass) directly
- Enables lazy loading detection (check if children loaded)
- Supports context-specific queries (operation-specific requirements)

**Implementation Pattern**:
```python
# Store node metadata
node_data = {
    'type': 'OPERATION',
    'base_id': '8113',
    'lot_id': '26',
    'sub_id': '',
    'operation_seq': 10
}
item.setData(0, Qt.UserRole, node_data)

# Retrieve on expand
def on_item_expanded(item):
    node_data = item.data(0, Qt.UserRole)
    if node_data['type'] == 'OPERATION':
        load_requirements(node_data['base_id'], node_data['lot_id'], node_data['sub_id'], node_data['operation_seq'])
```

**Alternatives Considered**:
- Store in global dict keyed by item pointer: Memory leak risk, not Qt-idiomatic
- Parse node text to extract IDs: Fragile, breaks if text format changes
- Separate tracking data structure: Duplicate storage, synchronization issues

### 4. Visual Indicators for Node Types

**Question**: How should we visually distinguish different node types (operations, labor, materials, WIP)?

**Research**:
- Legacy VISUAL uses:
  - `[C]` prefix for closed work orders
  - Black bars for selected nodes (Qt selection handles this)
  - Indentation for hierarchy (QTreeWidget automatic)
  - Different fonts/colors for node types (optional)

**Decision**: Use text prefixes and optional icons for node types

**Rationale**:
- Text prefixes match VISUAL appearance: `[C]` for closed, `[OPERATION]`, `[LABOR]`, `[MATERIAL]`, `[WIP]`
- Qt icons can be added later for polish (not critical for MVP)
- Indentation provided by QTreeWidget automatically
- Selection highlighting provided by Qt theme

**Node Format Examples**:
```
[C] 8113/26 - 1.0000 - ROLLFORMER, 14-PASS DOUBLE
    [10] GEAR CUTTING
        M28803 - TOP BEARING COVER - Qty: 1.0000
        M28827 - TOP IDLER SPUR GEAR, 39 TEE - Qty: 1.0000
    [20] WELDING
        ...
    [LABOR] Employee 950 - 8/15/2011 - 0.50 Hrs
    [MATERIAL] M28803 - Issue - 1.0000 - 8/15/2011
    [WIP] Material Cost: $1,250.00, Labor Cost: $450.00
```

**Alternatives Considered**:
- Custom icons only: Requires icon asset management, not critical
- Color coding: Accessibility issues, theme conflicts
- No visual distinction: Confusing for users, harder to scan

### 5. Performance Optimization for Large Trees

**Question**: What techniques ensure smooth performance for work orders with 1000+ nodes?

**Research**:
- Virtual scrolling: Qt provides automatically via viewport
- Lazy loading: Already decided (Research Question 2)
- Progressive rendering: Load visible nodes first
- Caching: Store expanded state to avoid re-querying

**Decision**: Lazy loading + expand state tracking

**Rationale**:
- **Lazy loading**: Already decided, addresses 90% of performance concerns
- **Expand state**: User expands node, data cached in tree items, no re-query on collapse/re-expand
- **Virtual scrolling**: Qt QTreeWidget provides automatically (only renders visible items)
- **No progressive rendering needed**: Lazy loading + virtual scrolling sufficient

**Implementation Notes**:
```python
def on_item_expanded(item):
    if item.childCount() > 0:
        return  # Already loaded, use cached data

    # First expansion - load from database
    node_data = item.data(0, Qt.UserRole)
    children = query_child_nodes(node_data)
    for child_data in children:
        child_item = create_tree_item(child_data)
        item.addChild(child_item)
```

**Performance Targets**:
- Tree with 500 nodes: <2 seconds render (lazy loading ensures this)
- Expand/collapse: <100ms (cached data, no query)
- Scroll through 1000 nodes: Smooth (Qt virtual scrolling)

**Alternatives Considered**:
- Load everything upfront + virtual scrolling: Still slow initial load, wasted memory
- Progressive rendering (batch loading): Added complexity, lazy loading simpler
- Custom caching layer: Unnecessary, Qt tree items cache naturally

### 6. CSV Export Format for Hierarchical Data

**Question**: How should we export hierarchical tree data to flat CSV format?

**Research**:
- CSV is inherently flat (rows/columns), needs to indicate hierarchy
- Options: Indentation, level column, parent ID column
- Legacy VISUAL exports likely use indentation or level indicators

**Decision**: Use indentation in first column to show hierarchy

**Rationale**:
- **Visual clarity**: Indentation mirrors tree display, easy to understand
- **Excel/spreadsheet friendly**: Opens correctly, hierarchy visible
- **Simple implementation**: Recursive tree traversal, prepend spaces per level
- **Familiar pattern**: Matches typical hierarchical CSV exports

**Export Format**:
```csv
Level,Type,ID,Description,Quantity,Details
0,Work Order,8113/26,ROLLFORMER 14-PASS DOUBLE,1.0000,Closed
1,Operation,10,GEAR CUTTING,,Setup: 0.50 hrs
2,Requirement,M28803,TOP BEARING COVER,1.0000,
2,Requirement,M28827,TOP IDLER SPUR GEAR,1.0000,
1,Operation,20,WELDING,,Setup: 1.00 hrs
1,Labor,950,Employee 950 - 8/15/2011,0.50,Rate: $25.00/hr
1,Material,M28803,Issue,1.0000,Location: WAREHOUSE
1,WIP,Material Cost,,$1250.00,
```

**Alternatives Considered**:
- Parent ID column: Harder to visualize, requires tool to reconstruct tree
- Level column only: Less visual, but included as metadata
- Nested JSON/XML: Not CSV, requires special viewer

### 7. Integration with Existing Application Architecture

**Question**: How does the Engineering module integrate with Sales and Inventory modules?

**Research**:
- Existing architecture: PyQt6 tabbed interface, three modules (Sales, Inventory, Engineering)
- Shared components: DatabaseConnection, search_panel, main_window
- Module pattern: Each module is QWidget with its own layout

**Decision**: Engineering module follows existing tab pattern

**Rationale**:
- **Consistency**: Users familiar with Sales/Inventory navigation apply same to Engineering
- **Code reuse**: Leverage DatabaseConnection, search infrastructure, export dialogs
- **Minimal impact**: New module doesn't modify existing Sales/Inventory code
- **Separation**: Engineering-specific code isolated in engineering_module.py, work_order_tree.py

**Integration Points**:
1. **main_window.py**: Add Engineering tab to QTabWidget
2. **DatabaseConnection**: Reuse existing connection pool
3. **search_panel.py**: Can potentially reuse for BASE_ID search (or create engineering-specific)
4. **Export patterns**: Follow existing CSV export pattern from part_detail_view.py

**Module Structure**:
```python
# engineering_module.py
class EngineeringModule(QWidget):
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.service = WorkOrderService(db_connection)
        self.setup_ui()

    def setup_ui(self):
        # Search panel
        # Work order list
        # Tree view (work_order_tree.py)
        # Export button
```

**Alternatives Considered**:
- Separate window: Inconsistent with existing UI, extra windows confusing
- Merge with Inventory: Unrelated functionality, violates separation of concerns
- Plugin architecture: Overcomplicated for single application

## Summary of Decisions

| Research Question | Decision | Rationale |
|-------------------|----------|-----------|
| Tree Control | PyQt6 QTreeWidget | Built-in lazy loading, familiar API, matches VISUAL appearance |
| Query Strategy | Lazy loading per level | Performance, memory efficiency, responsive UX |
| Node Identification | Qt.UserRole data storage | Type-safe, Qt-idiomatic, supports lazy loading |
| Visual Indicators | Text prefixes `[C]`, `[OPERATION]`, etc. | Matches VISUAL, clear distinction, simple |
| Performance | Lazy loading + cached expand state | Sufficient for 1000+ nodes, no complex optimizations needed |
| CSV Export | Indentation in first column | Visual hierarchy, spreadsheet-friendly |
| Integration | Follow existing tab pattern | Consistency, code reuse, minimal impact |

## Technical Risks Mitigated

1. **Performance with large trees**: Lazy loading ensures only visible/expanded data loaded
2. **Memory consumption**: Lazy loading keeps footprint <100MB even for large work orders
3. **Database load**: Separate small queries preferred over single mega-join for WLAN connection
4. **UI responsiveness**: Expand/collapse uses cached data, no network delay
5. **Integration complexity**: Following existing patterns minimizes architectural changes

## Next Phase: Data Model Design

Phase 1 will define:
- WorkOrder, Operation, Requirement, LaborTicket, InventoryTransaction, WIPBalance dataclasses
- WorkOrderService API contract
- Tree node data structures
- Query specifications (contracts/work_order_queries.sql)
