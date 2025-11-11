# Implementation Tasks: Three-Module Expansion

**Feature**: 001-visual-order-lookup
**Branch**: `001-visual-order-lookup`
**Date**: 2025-11-07
**Status**: Phase 1 Complete - Ready for Implementation

**Context**: Expand single-module Sales application to three-module system (Sales, Inventory, Engineering) with left-hand navigation panel.

**Organization**: Tasks organized by implementation phase following plan.md milestones. Tasks marked [P] can run in parallel within their phase.

---

## Phase 1: Project Setup (Priority: P0)

**Goal**: Ensure development environment and dependencies are configured

**Independent Test**: Run `pytest` and verify all existing tests pass

### Implementation

- [X] T001 [P] [SETUP] Verify Python 3.11+ installed and create virtual environment if needed
  - Run `python --version` to verify 3.11+
  - Create venv: `python -m venv venv`
  - Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)

- [X] T002 [P] [SETUP] Install/verify dependencies in requirements.txt and requirements-dev.txt
  - Install: `pip install -r requirements.txt -r requirements-dev.txt`
  - Verify PyQt6, pyodbc, python-dotenv, Jinja2, pytest, ruff installed
  - Run `pytest` to verify existing Sales module tests pass

---

## Phase 2: Navigation Infrastructure (Priority: P1)

**Goal**: Implement left-hand navigation panel and module container framework

**Dependencies**: Phase 1 complete

**Independent Test**: Start app and verify navigation panel appears with 3 module options, clicking switches views

### Implementation

- [X] T003 [NAV] Create NavigationPanel class in visual_order_lookup/ui/navigation_panel.py
  - Subclass QListWidget
  - 200px fixed width (setFixedWidth)
  - Add 3 items: "Sales", "Inventory", "Engineering"
  - Apply stylesheet from module_architecture.md (selected item styling)
  - **Depends on**: None

- [X] T004 [NAV] Create placeholder module widgets in visual_order_lookup/ui/
  - Create inventory_module.py with InventoryModuleWidget(QWidget)
  - Create engineering_module.py with EngineeringModuleWidget(QWidget)
  - Each should display "Module Name - Coming Soon" centered label
  - **Depends on**: None

- [X] T005 [NAV] Refactor MainWindow to integrate navigation in visual_order_lookup/ui/main_window.py
  - Wrap existing Sales UI in sales_module_widget (extract from main_window)
  - Create QHBoxLayout: NavigationPanel (left) + QStackedWidget (right)
  - Add sales_module_widget, inventory_module_widget, engineering_module_widget to stack
  - Connect navigation.currentRowChanged to stack.setCurrentIndex
  - **Depends on**: T003, T004

- [X] T006 [P] [NAV] Add module switching keyboard shortcuts in visual_order_lookup/ui/main_window.py
  - Ctrl+1: Switch to Sales
  - Ctrl+2: Switch to Inventory
  - Ctrl+3: Switch to Engineering
  - **Depends on**: T005

- [X] T007 [P] [NAV] Update visual_legacy.qss stylesheet in visual_order_lookup/resources/styles/
  - Add NavigationPanel styling (item selected, hover, background)
  - Add module container styling
  - Verify colors match existing Sales module theme
  - **Depends on**: T003

- [X] T008 [NAV] Write unit tests for NavigationPanel in tests/unit/test_navigation_panel.py
  - Test 3 items created
  - Test currentRowChanged signal
  - Test keyboard navigation
  - **Depends on**: T003

- [X] T009 [NAV] Write integration test for module switching in tests/integration/test_module_switching.py
  - Test all 3 modules accessible
  - Test state preservation when switching between modules
  - Test Sales module still functional after refactor
  - **Depends on**: T005

---

## Phase 3: Inventory Module (Priority: P1)

**Goal**: Implement part lookup with where-used and purchase history views

**Dependencies**: Phase 2 complete

**Independent Test**: Search for part "F0195", verify part info + where-used + purchase history tabs display

### Data Model & Service Layer

- [X] T010 [P] [INV] Add Part dataclass to visual_order_lookup/database/models.py
  - Copy from data-model.md (part_id, part_number, description, extended_description, unit_of_measure, costs, quantities, vendor_id, flags)
  - Add __post_init__ validation for required fields
  - **Depends on**: None

- [X] T011 [P] [INV] Add WhereUsed dataclass to visual_order_lookup/database/models.py
  - Copy from data-model.md (part_number, cust_order_id, work_order, transaction_date, quantity, customer_name)
  - **Depends on**: None

- [X] T012 [P] [INV] Add PurchaseHistory dataclass to visual_order_lookup/database/models.py
  - Copy from data-model.md (part_number, po_number, order_date, vendor_name, quantity, unit_price, line_total)
  - **Depends on**: None

- [X] T013 [INV] Create PartService class in visual_order_lookup/services/part_service.py
  - Implement search_by_part_number(part_number: str) -> Part | None
  - SQL: SELECT * FROM PART WHERE PART_ID = ? (exact match, <5ms)
  - Handle no results gracefully (return None)
  - Add 30s timeout
  - **Depends on**: T010

- [X] T014 [INV] Add get_where_used method to PartService in visual_order_lookup/services/part_service.py
  - Implement get_where_used(part_number: str) -> List[WhereUsed]
  - SQL joins: INVENTORY_TRANS → CUSTOMER_ORDER → CUSTOMER
  - Include work_order if WORK_ORDER field is not null
  - Order by transaction_date DESC
  - Limit 1000 results, add 30s timeout
  - **Depends on**: T011, T013

- [X] T015 [INV] Add get_purchase_history method to PartService in visual_order_lookup/services/part_service.py
  - Implement get_purchase_history(part_number: str, limit: int = 100) -> List[PurchaseHistory]
  - SQL joins: PURC_ORDER_LINE → PURC_ORDER → VENDOR
  - Order by order_date DESC
  - Add 30s timeout
  - **Depends on**: T012, T013

### UI Components

- [X] T016 [INV] Create PartSearchPanel in visual_order_lookup/ui/part_search_panel.py
  - QLineEdit for part number input
  - QPushButton "Search"
  - Connect Enter key to search
  - Emit search_requested(part_number: str) signal
  - **Depends on**: None

- [X] T017 [INV] Create PartDetailView with tabs in visual_order_lookup/ui/part_detail_view.py
  - QTabWidget with 3 tabs: "Part Info", "Where Used", "Purchase History"
  - Part Info: Display part_template.html in QTextBrowser
  - Where Used: QTableWidget with columns from WhereUsed dataclass
  - Purchase History: QTableWidget with columns from PurchaseHistory dataclass
  - Add loading indicators for each tab
  - **Depends on**: None

- [X] T018 [INV] Implement InventoryModuleWidget in visual_order_lookup/ui/inventory_module.py
  - Replace placeholder with QVBoxLayout: PartSearchPanel (top) + PartDetailView (bottom)
  - Connect search_requested signal to PartService.search_by_part_number
  - Use DatabaseWorker pattern (QThread) for async queries
  - Handle errors with dialogs.py error dialog
  - Update PartDetailView on successful part lookup
  - **Depends on**: T013, T014, T015, T016, T017

- [X] T019 [P] [INV] Add export functionality to PartDetailView in visual_order_lookup/ui/part_detail_view.py
  - Add "Export" button to each tab
  - Export Part Info as HTML (using part_template.html)
  - Export Where Used as CSV
  - Export Purchase History as CSV
  - **Depends on**: T017

- [X] T020 [INV] Write tests for Inventory module in tests/integration/test_inventory_module.py
  - Test part search for F0195, PF004, PP001
  - Test where-used query returns results
  - Test purchase history query returns results
  - Test error handling for non-existent parts
  - **Depends on**: T018

---

## Phase 4: Engineering Module (Priority: P2)

**Goal**: Implement job search with BOM hierarchy tree display using lazy loading

**Dependencies**: Phase 3 complete

**Independent Test**: Search for job "8113", verify BOM tree loads assemblies collapsed, expand assembly to load parts

### Data Model & Service Layer

- [X] T021 [P] [ENG] Add BOMNode dataclass to visual_order_lookup/database/models.py
  - Copy from data-model.md (job_number, lot_id, sub_id, base_lot_id, part_id, node_type, flags, depth, is_loaded)
  - Add method to calculate color: blue (assembly), black (manufactured), red (purchased)
  - **Depends on**: None

- [X] T022 [P] [ENG] Add Job dataclass to visual_order_lookup/database/models.py
  - Copy from data-model.md (job_number, customer_id, customer_name, assembly_count)
  - **Depends on**: None

- [X] T023 [ENG] Create BOMService class in visual_order_lookup/services/bom_service.py
  - Implement get_bom_assemblies(job_number: str) -> List[BOMNode]
  - SQL: SELECT from WORK_ORDER WHERE BASE_ID = job_number AND LOT_ID = '00' (top-level assemblies)
  - Each BOMNode has is_loaded = False (lazy loading flag)
  - Add 30s timeout
  - **Depends on**: T021

- [X] T024 [ENG] Add get_assembly_parts method to BOMService in visual_order_lookup/services/bom_service.py
  - Implement get_assembly_parts(job_number: str, lot_id: str) -> List[BOMNode]
  - SQL: SELECT from WORK_ORDER WHERE BASE_ID = job_number AND BASE_LOT_ID = lot_id
  - Join with PART to get part details (FABRICATED, PURCHASED flags)
  - Calculate node_type and color for each part
  - Set is_loaded = True for assemblies, False for unexpanded assemblies
  - Add 30s timeout, <300ms target
  - **Depends on**: T023

- [X] T025 [ENG] Add get_bom_hierarchy method to BOMService in visual_order_lookup/services/bom_service.py
  - Implement get_bom_hierarchy(job_number: str) -> List[BOMNode] (full hierarchy, for export)
  - Recursive SQL query or iterative loading
  - Use for "Expand All" and export features
  - Add 30s timeout, warn if >10s
  - **Depends on**: T024

### UI Components

- [X] T026 [ENG] Create JobSearchPanel in visual_order_lookup/ui/job_search_panel.py
  - QLineEdit for job number input
  - QPushButton "Search"
  - Connect Enter key to search
  - Emit search_requested(job_number: str) signal
  - **Depends on**: None

- [X] T027 [ENG] Create BOMTreeView in visual_order_lookup/ui/bom_tree_view.py
  - Subclass QTreeWidget
  - Columns: Lot ID, Sub ID, Part Number, Description
  - Color-code rows by node_type (blue/white, black, red)
  - Connect itemExpanded signal to lazy load handler
  - Add loading indicator for expanded items
  - **Depends on**: None

- [X] T028 [ENG] Implement lazy loading in BOMTreeView in visual_order_lookup/ui/bom_tree_view.py
  - On itemExpanded, check if BOMNode.is_loaded == False
  - If not loaded, emit load_children(job_number, lot_id) signal
  - Parent widget handles signal → calls BOMService.get_assembly_parts → updates tree
  - Show loading spinner during fetch
  - **Depends on**: T024, T027

- [X] T029 [ENG] Implement EngineeringModuleWidget in visual_order_lookup/ui/engineering_module.py
  - Replace placeholder with QVBoxLayout: JobSearchPanel (top) + BOMTreeView (bottom)
  - Connect search_requested signal to BOMService.get_bom_assemblies
  - Use DatabaseWorker pattern (QThread) for async queries
  - Handle load_children signal for lazy loading
  - Handle errors with dialogs.py error dialog
  - Display job header (job_number, customer_name, assembly_count)
  - **Depends on**: T023, T024, T026, T028

- [X] T030 [P] [ENG] Add BOM tree actions to EngineeringModuleWidget in visual_order_lookup/ui/engineering_module.py
  - "Expand All" button (loads full hierarchy, warn if >700 WOs)
  - "Collapse All" button
  - "Export" button (generates bom_template.html, saves as PDF)
  - Right-click context menu: "Copy Part Number", "Show Part Details" (opens Inventory module)
  - **Depends on**: T025, T029

- [X] T031 [P] [ENG] Add BOM search/filter to EngineeringModuleWidget in visual_order_lookup/ui/engineering_module.py
  - QLineEdit for filtering by part number or description
  - Filter tree items in real-time (highlight matching rows)
  - "Clear Filter" button
  - **Depends on**: T029

- [X] T032 [ENG] Write unit tests for BOMService in tests/unit/test_bom_service.py
  - Test get_bom_assemblies for job 8113 (should return ~20-30 assemblies)
  - Test get_assembly_parts for specific assembly (should return parts)
  - Test color calculation (blue, black, red)
  - Test lazy loading flag (is_loaded)
  - **Depends on**: T023, T024

- [X] T033 [ENG] Write integration tests for Engineering module in tests/integration/test_engineering_module.py
  - Test job search for 8113 (large), 8059 (small)
  - Test lazy loading (expand assembly, verify parts loaded)
  - Test "Expand All" functionality
  - Test export to PDF
  - Test performance: <500ms initial load, <300ms per expand
  - **Depends on**: T029

---

## Phase 5: Polish & Documentation (Priority: P3)

**Goal**: Final integration, performance optimization, user documentation

**Dependencies**: Phase 4 complete

**Independent Test**: Run full application, test all 3 modules, verify performance targets met

### Integration & Performance

- [X] T034 [POL] Add cross-module navigation in visual_order_lookup/ui/
  - From Where Used table (Inventory), double-click order → switch to Sales, load order
  - From BOM tree (Engineering), right-click part → switch to Inventory, load part
  - Implement via signals: module_switch_requested(module: str, context: dict)
  - **Depends on**: T018, T029

- [X] T035 [P] [POL] Optimize database queries for performance in visual_order_lookup/database/queries.py
  - Review all SQL queries, ensure indexes exist on key columns
  - Add query result caching for repeated searches (LRU cache, 100 entries)
  - Log slow queries (>5s) to help identify bottlenecks
  - **Depends on**: T015, T025

- [X] T036 [P] [POL] Add application-wide loading indicators in visual_order_lookup/ui/main_window.py
  - Status bar with progress indicator
  - Display current operation (e.g., "Loading BOM hierarchy...")
  - Show query time after completion
  - **Depends on**: T005

### Documentation & Testing

- [X] T037 [P] [POL] Update README.md with installation and usage instructions
  - Add screenshots of all 3 modules
  - Document test data (parts F0195, PF004, PP001; jobs 8113, 8059)
  - Document keyboard shortcuts (Ctrl+1/2/3)
  - Add troubleshooting section (database connection, slow queries)
  - **Depends on**: None

- [X] T038 [P] [POL] Create user guide from quickstart.md in docs/user_guide.md
  - Convert quickstart.md to standalone user guide
  - Add table of contents
  - Add "Getting Started" section with .env setup
  - Add FAQ section
  - **Depends on**: None

- [X] T039 [POL] Run full test suite and fix any integration issues in tests/
  - Run `pytest tests/` and verify all tests pass
  - Run `ruff check .` and fix any linting issues
  - Test on fresh installation (clean venv)
  - Verify performance targets: <10s queries, <15s total operations, <100MB memory
  - **Depends on**: T020, T033

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Phase 1 (Setup)**: No dependencies, start immediately
2. **Phase 2 (Navigation)**: Requires Phase 1 complete
3. **Phase 3 (Inventory)**: Requires Phase 2 complete
4. **Phase 4 (Engineering)**: Requires Phase 3 complete (or can run in parallel if independent)
5. **Phase 5 (Polish)**: Requires Phase 4 complete

### Parallel Opportunities (15 tasks, 38%)

**Within Phase 1**: T001, T002 (both independent)

**Within Phase 2**: T003, T004 (independent), then T006, T007 (after T005)

**Within Phase 3**: T010, T011, T012 (data models), T016, T017 (UI components), T019 (after T017)

**Within Phase 4**: T021, T022 (data models), T026, T027 (UI components), T030, T031 (after T029), T032 (after T023/T024)

**Within Phase 5**: T035, T036, T037, T038 (all independent)

### Critical Path (must be sequential)

Phase 2: T005 (refactor MainWindow) → T009 (integration test)
Phase 3: T013 (PartService) → T014/T015 (service methods) → T018 (InventoryModuleWidget) → T020 (tests)
Phase 4: T023 (BOMService) → T024 (get_assembly_parts) → T028 (lazy loading) → T029 (EngineeringModuleWidget) → T033 (tests)
Phase 5: T039 (final testing) must be last

---

## Implementation Strategy

### Recommended Execution Order

1. **Week 1**: Phase 1 + Phase 2 (Navigation framework) → 9 tasks
2. **Week 2**: Phase 3 (Inventory module) → 11 tasks
3. **Week 3**: Phase 4 (Engineering module) → 13 tasks
4. **Week 4**: Phase 5 (Polish & documentation) → 6 tasks

### Testing Strategy

- Run unit tests after each service implementation (T008, T020, T032)
- Run integration tests after each module complete (T009, T020, T033)
- Run full test suite at end (T039)
- Manual testing with test data throughout (F0195, PF004, PP001, Job 8113, Job 8059)

---

## Test Data Reference

### Inventory Module (Phase 3)

- **F0195**: Part with 995 purchase orders (good for testing pagination/performance)
- **PF004**: Finished part (assembly)
- **PP001**: Purchased part

### Engineering Module (Phase 4)

- **Job 8113**: Large job with 702 work orders (tests lazy loading performance)
- **Job 8059**: Small job with 33 work orders (tests basic functionality)

### Sales Module (existing)

- **Order 4049**: THE TRANE COMPANY (tests existing functionality still works)

---

## Performance Targets

- **Database Queries**: <10s per query, 30s timeout
- **Total Operations**: <15s (query + UI rendering)
- **Memory Usage**: <100MB
- **Module Switching**: <500ms
- **BOM Lazy Load**: <300ms per assembly expand
- **Initial BOM Load**: <1s for assemblies-only (collapsed)

---

## Success Criteria

- ✅ All 39 tasks completed
- ✅ All tests pass (`pytest tests/`)
- ✅ No linting errors (`ruff check .`)
- ✅ All 3 modules functional (Sales, Inventory, Engineering)
- ✅ Navigation panel working with keyboard shortcuts
- ✅ Performance targets met (<10s queries, <15s operations, <100MB memory)
- ✅ Test data validated (F0195, PF004, PP001, Job 8113, Job 8059)
- ✅ Documentation complete (README.md, user_guide.md)
- ✅ Sales module still works after refactoring (no regressions)

---

## Technical Notes

### QStackedWidget State Preservation

The QStackedWidget automatically preserves widget state when switching between modules. No manual save/restore needed - each module widget maintains its own state (search history, scroll position, expanded tree nodes).

### Lazy Loading Pattern

Engineering module BOM tree uses lazy loading to handle large jobs (700+ work orders):
1. Initial load: Get assemblies only (LOT_ID = '00') → <1s
2. User expands assembly: itemExpanded signal → load parts for that assembly → <300ms
3. "Expand All": Load full hierarchy → warn if >700 WOs, may take 5-10s

### DatabaseWorker Pattern

All database queries use QThread workers for async execution:
```python
worker = DatabaseWorker(query_function, *args)
thread = QThread()
worker.moveToThread(thread)
worker.finished.connect(on_success)
worker.error.connect(on_error)
thread.started.connect(worker.run)
thread.start()
```

This prevents UI freezing during long queries.

### Constitution Compliance

- ✅ Read-only database access (all queries are SELECT-only)
- ✅ No cloud dependencies (local SQL Server via WLAN)
- ✅ No write operations to database
- ✅ Error handling for all database operations
- ✅ 30s query timeout to prevent hanging

---

**Estimated Total Time**: 28-40 hours (1-1.5 hours per task average)
**Estimated Calendar Time**: 4 weeks (assuming 10 hours/week)
