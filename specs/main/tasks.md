# Implementation Tasks: Engineering Module - Work Order Hierarchy Viewer

**Feature**: 003-engineering-work-order-hierarchy
**Date**: 2025-01-14
**Estimated Duration**: 5-7 days

---

## Phase 1: Setup & Foundation

### Project Structure

- [X] [T001] [P] Create visual_order_lookup/database/models/ subdirectory for work order models → `visual_order_lookup/database/models/`
- [X] [T002] [P] Create visual_order_lookup/database/queries/ subdirectory for query modules → `visual_order_lookup/database/queries/`
- [X] [T003] [P] Create visual_order_lookup/services/ directory for service layer → `visual_order_lookup/services/`
- [X] [T004] [P] Create visual_order_lookup/ui/engineering/ directory for Engineering UI components → `visual_order_lookup/ui/engineering/`

### Dependencies

- [X] [T005] Verify PyQt6 >= 6.4.0 installed (QTreeWidget support) → `requirements.txt`
- [X] [T006] Verify pyodbc installed for SQL Server connectivity → `requirements.txt`
- [X] [T007] [P] Add typing-extensions if needed for Python 3.11 dataclass features → `requirements.txt`

---

## Phase 2: Database Layer

### Data Models

- [X] [T008] Create WorkOrder dataclass with composite PK (base_id, lot_id, sub_id), part info, dates, and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T009] Create Operation dataclass with FK to WorkOrder, sequence, operation_id, description, hours, and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T010] Create Requirement dataclass with FK to WorkOrder+Operation, part_id, quantities, SUBORD_WO_SUB_ID field, and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T011] Create LaborTicket dataclass with FK to WorkOrder, employee_id, labor_date, hours, rates, and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T012] Create InventoryTransaction dataclass with FK to WorkOrder, part_id, trans_type, quantity, location, and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T013] Create WIPBalance dataclass with FK to WorkOrder, cost breakdown (material, labor, burden), and formatting methods → `visual_order_lookup/database/models/work_order.py`
- [X] [T014] [P] Create __init__.py to export all work order models → `visual_order_lookup/database/models/__init__.py`

### Query Functions (WITH NOLOCK, Parameterized)

- [X] [T015] [US1] Implement search_work_orders(cursor, base_id_pattern, limit=1000) with TOP 1000, LIKE pattern, JOIN PART, ORDER BY CREATE_DATE DESC → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T016] [US2] Implement get_work_order_header(cursor, base_id, lot_id, sub_id) with aggregate counts for operations, labor, materials → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T017] [US3] Implement get_operations(cursor, base_id, lot_id, sub_id) with requirement_count subquery, ORDER BY SEQUENCE → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T018] [US3] Implement get_requirements(cursor, base_id, lot_id, sub_id, operation_seq) with PART join, SUBORD_WO_SUB_ID retrieval → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T019] [US3] Implement get_labor_tickets(cursor, base_id, lot_id, sub_id) with calculated total_hrs and total_cost, ORDER BY LABOR_DATE DESC → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T020] [US3] Implement get_inventory_transactions(cursor, base_id, lot_id, sub_id) with PART join, WHERE WORKORDER_BASE_ID IS NOT NULL, ORDER BY TRANS_DATE DESC → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T021] [US3] Implement get_wip_balance(cursor, base_id, lot_id, sub_id) returning single record or None → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T022] [US3] Implement get_work_order_hierarchy(cursor, base_id, lot_id, sub_id) using recursive CTE to traverse SUBORD_WO_SUB_ID parent-child relationships → `visual_order_lookup/database/queries/work_order_queries.py`
- [X] [T024] [P] Add error handling wrapper for all query functions with 5-second timeout, DatabaseError wrapping → `visual_order_lookup/database/queries/work_order_queries.py`

### Service Layer

- [X] [T025] Create WorkOrderService class with __init__(db_connection) → `visual_order_lookup/services/work_order_service.py`
- [X] [T026] [US1] Implement WorkOrderService.search_work_orders(base_id_pattern, limit=1000) returning List[WorkOrder] → `visual_order_lookup/services/work_order_service.py`
- [X] [T027] [US2] Implement WorkOrderService.get_work_order_header(base_id, lot_id, sub_id) returning WorkOrder with counts → `visual_order_lookup/services/work_order_service.py`
- [X] [T028] [US3] Implement WorkOrderService.get_operations(base_id, lot_id, sub_id) returning List[Operation] → `visual_order_lookup/services/work_order_service.py`
- [X] [T029] [US3] Implement WorkOrderService.get_requirements(base_id, lot_id, sub_id, operation_seq) returning List[Requirement] → `visual_order_lookup/services/work_order_service.py`
- [X] [T030] [US3] Implement WorkOrderService.get_labor_tickets(base_id, lot_id, sub_id) returning List[LaborTicket] → `visual_order_lookup/services/work_order_service.py`
- [X] [T031] [US3] Implement WorkOrderService.get_inventory_transactions(base_id, lot_id, sub_id) returning List[InventoryTransaction] → `visual_order_lookup/services/work_order_service.py`
- [X] [T032] [US3] Implement WorkOrderService.get_wip_balance(base_id, lot_id, sub_id) returning Optional[WIPBalance] → `visual_order_lookup/services/work_order_service.py`
- [X] [T033] [US3] Implement WorkOrderService.get_work_order_hierarchy(base_id, lot_id, sub_id) returning hierarchical structure using recursive query → `visual_order_lookup/services/work_order_service.py`
- [X] [T034] [P] Add logging for all service method calls with parameters (no sensitive data) and input validation (strip whitespace, uppercase, composite key validation) to all service methods → `visual_order_lookup/services/work_order_service.py`

---

## Phase 3: UI Components - User Stories

### US1: Search Work Orders by BASE_ID (FR-1)

- [X] [T035] [US1] Create EngineeringModule QWidget with vertical layout → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T036] [US1] Add search panel with QLineEdit for BASE_ID input, Search button, uppercase auto-conversion → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T037] [US1] Connect Search button to search_work_orders service call with loading indicator → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T038] [US1] Add Enter key binding to trigger search from BASE_ID input field → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T039] [US1] Add error handling for invalid BASE_ID patterns (empty, too long) with user-friendly messages → `visual_order_lookup/ui/engineering/engineering_module.py`

### US2: Display Work Order List (FR-2)

- [X] [T040] [US2] Create QTableWidget for search results with columns: BASE_ID, Date Created, Status, Part Description → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T041] [US2] Implement populate_work_order_list(results) to display List[WorkOrder] in table → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T042] [US2] Add row selection handling to load selected work order into tree view → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T043] [US2] Format date as MM/DD/YYYY, status with [C] prefix, quantity as decimal → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T044] [US2] Add "No results found" message when search returns empty list → `visual_order_lookup/ui/engineering/engineering_module.py`

### US3: Hierarchical Tree Display with Lazy Loading (FR-3)

- [X] [T045] [US3] Create WorkOrderTreeWidget extending QTreeWidget with custom node types → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T046] [US3] Define TreeNodeData dataclass with node_type, base_id, lot_id, sub_id, operation_seq, part_id, children_loaded flag → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T047] [US3] Implement load_work_order_header(base_id, lot_id, sub_id) to create root node with formatted ID, status, part, quantity → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T048] [US3] Add 6 placeholder child nodes: Operations, Labor, Materials, WIP, Sub Work Orders (if SUBORD_WO_SUB_ID found) with [+] indicators → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T049] [US3] Connect itemExpanded signal to on_item_expanded(item) handler for lazy loading → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T050] [US3] Implement on_item_expanded for "Operations" node: check children_loaded flag, call get_operations, create Operation nodes with [sequence] prefix → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T051] [US3] Implement on_item_expanded for Operation node: check children_loaded flag, call get_requirements, create Requirement nodes with part_id - description - qty → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T052] [US3] Implement on_item_expanded for Requirement node with SUBORD_WO_SUB_ID: recursively load child work order hierarchy → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T053] [US3] Implement on_item_expanded for "Labor" node: call get_labor_tickets, create LaborTicket nodes with [LABOR] employee - date - hours → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T054] [US3] Implement on_item_expanded for "Materials" node: call get_inventory_transactions, create InventoryTransaction nodes with [MATERIAL] part - type - qty - date → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T055] [US3] Implement on_item_expanded for "WIP" node: call get_wip_balance, create WIPBalance child nodes for material/labor/burden costs → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T056] [US3] Implement on_item_expanded for "Sub Work Orders" node: call get_work_order_hierarchy, use SubWorkOrderNode (T053A) to recursively create child work order nodes with depth limit → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T057] [US3] Add setChildIndicatorPolicy(ShowIndicator) to nodes with potential children to force [+] icon → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T058] [US3] Store TreeNodeData in item.setData(0, Qt.UserRole, node_data) for all node types → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T059] [US3] Set children_loaded=True flag after first expansion to enable caching → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T060] [US3] Add loading spinner or "Loading..." text during lazy load queries → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T061] [US3] Add error handling for failed lazy load queries with user-friendly error nodes → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T053A] [US3] Create SubWorkOrderNode type for REQUIREMENT nodes with SUBORD_WO_* fields populated: Display child work order BASE_ID/LOT_ID/SUB_ID, add recursion depth tracking (max 10 levels), implement circular reference detection → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`

### US4: Keyboard Navigation (FR-4)

- [X] [T062] [US4] Implement keyPressEvent override in WorkOrderTreeWidget → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T063] [US4] Handle Up/Down arrow keys for node selection navigation → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T064] [US4] Handle Left arrow key to collapse expanded node or move to parent → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T065] [US4] Handle Right arrow key to expand collapsed node or move to first child → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T066] [US4] Handle Space key to toggle expand/collapse on selected node → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`

### US5: Expand/Collapse All (FR-5)

- [X] [T067] [US5] Add "Expand All" button to EngineeringModule toolbar → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T068] [US5] Add "Collapse All" button to EngineeringModule toolbar → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T069] [US5] Implement expand_all() to recursively expand all nodes, triggering lazy loads → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T070] [US5] Implement collapse_all() to collapse all nodes except root header → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T071] [US5] Add progress indicator for Expand All operation (may take 2+ seconds for large trees) → `visual_order_lookup/ui/engineering/engineering_module.py`

### US6: CSV Export (FR-6)

- [X] [T072] [US6] Add "Export to CSV" button to EngineeringModule toolbar → `visual_order_lookup/ui/engineering/engineering_module.py`
- [X] [T073] [US6] Create export_tree_to_csv() method with QFileDialog for save location → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T074] [US6] Generate default filename: workorder_{base_id}_{lot_id}_{YYYYMMDD}.csv → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T075] [US6] Implement recursive tree traversal to collect all visible nodes with level tracking → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T076] [US6] Create CSV with columns: Level, Type, ID, Description, Quantity, Details → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T077] [US6] Add indentation in first column (Level) to show hierarchy visually → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T078] [US6] Format dates, quantities, costs consistently with tree display → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [X] [T079] [US6] Add error handling for file write failures with user notification → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`

---

## Phase 4: Integration

### Main Application Integration

- [X] [T080] Import EngineeringModule in main_window.py → `visual_order_lookup/ui/main_window.py`
- [X] [T081] Add "Engineering" tab to QTabWidget after Sales and Inventory tabs → `visual_order_lookup/ui/main_window.py`
- [X] [T082] Pass db_connection to EngineeringModule constructor → `visual_order_lookup/ui/main_window.py`
- [X] [T083] Add EngineeringModule to tab widget with icon (optional) → `visual_order_lookup/ui/main_window.py`
- [X] [T084] [P] Update main application window title to include "Engineering Lookup - Read Only" when Engineering tab active → `visual_order_lookup/ui/main_window.py`

### Configuration & Documentation

- [ ] [T085] [P] Add engineering module configuration section to .env.example (if needed) → `.env.example`
- [ ] [T086] [P] Update README.md with Engineering module description and usage → `README.md`
- [ ] [T087] [P] Add docstrings to all WorkOrderService methods with parameter descriptions and return types → `visual_order_lookup/services/work_order_service.py`
- [ ] [T088] [P] Add docstrings to all query functions with SQL query descriptions → `visual_order_lookup/database/queries/work_order_queries.py`

---

## Phase 5: Testing & Quality

### Unit Tests

- [ ] [T089] [P] Create test_work_order_models.py with tests for all dataclass formatting methods → `tests/database/models/test_work_order_models.py`
- [ ] [T090] [P] Create test_work_order_queries.py with mocked cursor tests for all 8 query functions → `tests/database/queries/test_work_order_queries.py`
- [ ] [T091] [P] Create test_work_order_service.py with mocked database tests for all service methods → `tests/services/test_work_order_service.py`
- [ ] [T092] [P] Add test for SUBORD_WO_SUB_ID recursive hierarchy query with multi-level work orders → `tests/database/queries/test_work_order_queries.py`

### Integration Tests

- [ ] [T093] Create test_engineering_module_integration.py with real database connection (requires test Visual DB) → `tests/integration/test_engineering_module_integration.py`
- [ ] [T094] Test search_work_orders with BASE_ID pattern "8113" returns expected results → `tests/integration/test_engineering_module_integration.py`
- [ ] [T095] Test get_work_order_header with composite key returns valid WorkOrder with counts → `tests/integration/test_engineering_module_integration.py`
- [ ] [T096] Test lazy loading: expand Operations node loads Operation records → `tests/integration/test_engineering_module_integration.py`
- [ ] [T097] Test lazy loading: expand Operation node loads Requirement records → `tests/integration/test_engineering_module_integration.py`
- [ ] [T098] Test recursive hierarchy query returns all child work orders via SUBORD_WO_SUB_ID → `tests/integration/test_engineering_module_integration.py`

### Acceptance Tests (from spec.md)

- [ ] [T099] [AT1] Test search by BASE_ID "8113" returns list with work order 8113/26 → Acceptance Test 1
- [ ] [T100] [AT2] Test select work order 8113/26 displays tree with Operations, Labor, Materials, WIP nodes → Acceptance Test 2
- [ ] [T101] [AT3] Test expand Operations node lazy loads 10-50 operation records within 300ms → Acceptance Test 3
- [ ] [T102] [AT4] Test expand Requirement with SUBORD_WO_SUB_ID recursively loads child work order → Acceptance Test 4 (new)
- [ ] [T103] [AT5] Test arrow key navigation (Up/Down/Left/Right) and Space to expand/collapse → Acceptance Test 5
- [ ] [T104] [AT6] Test Expand All button expands all nodes, Collapse All collapses all → Acceptance Test 6
- [ ] [T105] [AT7] Test CSV export generates file with hierarchy indentation and correct filename → Acceptance Test 7
- [ ] [T106] [AT8] Test performance: tree with 500 nodes renders within 2 seconds, collapse <100ms → Acceptance Test 8

---

## Phase 6: Polish & Performance

### Performance Optimization

- [ ] [T107] Profile query performance with EXPLAIN PLAN for all 8 queries, ensure indexes on FK columns → `visual_order_lookup/database/queries/work_order_queries.py`
- [ ] [T108] Optimize recursive hierarchy query with max recursion depth 10 (matching T053A) and circular reference detection on SUBORD_WO_SUB_ID → `visual_order_lookup/database/queries/work_order_queries.py`
- [ ] [T109] Add query result caching for get_work_order_header (header data doesn't change) → `visual_order_lookup/services/work_order_service.py`
- [ ] [T110] Implement virtual scrolling optimization for trees with 1000+ nodes (Qt provides automatically, verify) → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T111] Add pagination for search results if >1000 work orders match BASE_ID pattern → `visual_order_lookup/ui/engineering/engineering_module.py`

### Error Handling & Validation

- [ ] [T112] Add comprehensive error handling for database connection failures with retry logic → `visual_order_lookup/services/work_order_service.py`
- [ ] [T113] Add validation for empty BASE_ID, LOT_ID, SUB_ID with user-friendly error messages → `visual_order_lookup/services/work_order_service.py`
- [ ] [T114] Add handling for NotFoundError when work order doesn't exist → `visual_order_lookup/ui/engineering/engineering_module.py`
- [ ] [T115] Add timeout handling (5 seconds) for all database queries → `visual_order_lookup/database/queries/work_order_queries.py`
- [ ] [T116] Log all errors with context (work order ID, operation) to application log file → `visual_order_lookup/services/work_order_service.py`

### UI Polish

- [ ] [T117] [P] Add visual indicators (icons) for node types: folder icon for Operations, person icon for Labor, box icon for Materials → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T118] [P] Add tooltips to tree nodes showing full details (hover to see complete part description) → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T119] [P] Style selected nodes with black bar background matching VISUAL Enterprise screenshots → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T120] [P] Add status bar message showing current work order and node count → `visual_order_lookup/ui/engineering/engineering_module.py`
- [ ] [T121] [P] Add "Clear" button to reset search and tree view → `visual_order_lookup/ui/engineering/engineering_module.py`

### Documentation

- [ ] [T122] [P] Create user guide section in README.md for Engineering module with screenshots → `README.md`
- [ ] [T123] [P] Document SUBORD_WO_SUB_ID hierarchy feature with example SQL queries → `docs/engineering_module.md`
- [ ] [T124] [P] Add inline code comments for complex lazy loading logic → `visual_order_lookup/ui/engineering/work_order_tree_widget.py`
- [ ] [T125] [P] Create CHANGELOG.md entry for Feature 003 with release notes → `CHANGELOG.md`

---

## Task Summary

- **Total Tasks**: 126 (removed 4 binary note tasks: T023A, T023B, T033A, T033B; added 1 task: T053A)
- **Parallelizable Tasks**: 31 (marked with [P])
- **User Story Tasks**: 95 (marked with [US1] through [US6])
- **Acceptance Test Tasks**: 8 (marked with [AT1] through [AT8])
- **Estimated Duration**: 5-7 days (dependent on team size and testing complexity)

## Critical Path

1. **Database Layer** (T008-T034): Foundation for all features - 2 days
2. **Tree Widget Core** (T045-T061): Lazy loading implementation - 2 days
3. **User Stories** (T035-T079): Sequential by priority - 2 days
4. **Integration & Testing** (T080-T106): Final validation - 1-2 days

## Dependencies

- **T035-T044** (US1-US2) depend on **T024-T034** (Service Layer)
- **T045-T061** (US3 Tree) depend on **T024-T034** (Service Layer)
- **T080-T084** (Integration) depend on **T035** (EngineeringModule created)
- **T099-T106** (Acceptance Tests) depend on all previous phases

## Notes

- SUBORD_WO_SUB_ID discovery adds recursive hierarchy feature to FR-3 with max depth 10 levels
- Lazy loading critical for performance (Constitution requirement: <15s total)
- All queries MUST use WITH (NOLOCK) for read-only access (Constitution Principle III)
- Binary note tables (WORKORDER_BINARY, REQUIREMENT_BINARY) deferred to future enhancement
- Tree node caching prevents re-querying on collapse/re-expand
- CSV export follows existing pattern from part_detail_view.py
