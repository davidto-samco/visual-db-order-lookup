# Implementation Tasks: Inventory Module Where-Used Enhancement

**Feature**: 002-inventory-where-used-enhancement
**Branch**: `002-inventory-where-used-enhancement`
**Date**: 2025-11-12
**Generated**: From `/speckit.tasks` command

## Overview

This task list implements the BOM (Bill of Materials) where-used display feature for the Inventory module. The feature replaces the current inventory transaction view with BOM structure information from the REQUIREMENT and WORK_ORDER tables.

**Key Discovery**: Visual database uses REQUIREMENT (not BOM_DET) and WORK_ORDER (not BOM_MASTER) tables.

## Task Summary

- **Total Tasks**: 19
- **Phase 1 (Setup)**: 2 tasks
- **Phase 2 (Data Layer)**: 5 tasks
- **Phase 3 (Service Layer)**: 2 tasks
- **Phase 4 (UI Layer)**: 8 tasks
- **Phase 5 (Integration & Testing)**: 2 tasks
- **Parallelizable Tasks**: 12 tasks (63%)

## Success Criteria

**Feature Complete When**:
1. ✓ WhereUsed model updated with BOM fields
2. ✓ Database query retrieves from REQUIREMENT + WORK_ORDER tables
3. ✓ Where Used tab displays 6 columns with correct formatting
4. ✓ Pagination works with 50 records per page
5. ✓ CSV export generates all BOM records with new format
6. ✓ Performance meets targets (query <5s, pagination <1s, export <10s)
7. ✓ Manual testing with parts F0195, F0209, R0236 passes

## Phase 1: Setup & Environment Validation

**Objective**: Verify development environment and database access before code changes.

### Tasks

- [ ] T001 Verify database connection to Visual SQL Server via .env configuration
- [ ] T002 [P] Run test query to confirm REQUIREMENT and WORK_ORDER tables exist and are accessible

**Completion Criteria**: Database queries execute successfully without errors.

**Dependencies**: None (blocking phase for all others)

---

## Phase 2: Data Layer - Model & Query Implementation

**Objective**: Update WhereUsed model and implement BOM database query.

### Model Update Tasks

- [ ] T003 [P] Update WhereUsed dataclass in `visual_order_lookup/database/models.py`:
  - Replace fields: `transaction_date`, `warehouse_id`, `location_id`, `customer_name`, `cust_order_id`, `cust_order_line_no`, `work_order`
  - Add fields: `work_order_master` (str), `seq_no` (int), `piece_no` (int), `qty_per` (Decimal), `fixed_qty` (Decimal), `scrap_percent` (Decimal)
  - Keep field: `part_number` (str)

- [ ] T004 [P] Add formatting methods to WhereUsed model in `visual_order_lookup/database/models.py`:
  - `formatted_work_order()` → returns `work_order_master` as-is
  - `formatted_seq_no()` → returns `str(seq_no)`
  - `formatted_piece_no()` → returns `str(piece_no)`
  - `formatted_qty_per()` → returns `f"{qty_per:.4f}"`
  - `formatted_fixed_qty()` → returns `f"{fixed_qty:.4f}"`
  - `formatted_scrap_percent()` → returns `f"{scrap_percent:.2f}%"`

### Query Implementation Tasks

- [ ] T005 Create new file `visual_order_lookup/database/part_queries.py` (if doesn't exist) or update existing

- [ ] T006 Implement `get_part_bom_usage()` function in `visual_order_lookup/database/part_queries.py`:
  - Query REQUIREMENT table joined with WORK_ORDER table
  - Use composite key join: WORKORDER_BASE_ID + WORKORDER_LOT_ID + WORKORDER_SUB_ID
  - SELECT columns: wo.BASE_ID, r.OPERATION_SEQ_NO, r.PIECE_NO, r.QTY_PER, r.FIXED_QTY, r.SCRAP_PERCENT
  - WHERE clause: r.PART_ID = ? (parameterized)
  - ORDER BY: wo.BASE_ID, r.OPERATION_SEQ_NO
  - Use WITH (NOLOCK) hint on both tables
  - Return List[WhereUsed]

- [ ] T007 Add error handling to `get_part_bom_usage()` in `visual_order_lookup/database/part_queries.py`:
  - Validate `part_number` parameter (non-empty)
  - Catch pyodbc.Error and raise user-friendly Exception
  - Log query execution with record count
  - Return empty list [] for parts with no BOM usage (not None)

**Completion Criteria**:
- WhereUsed model has 7 fields total (6 BOM + 1 part_number)
- All 6 formatting methods return correctly formatted strings
- Query executes without errors and returns WhereUsed objects
- Empty result returns [] not None

**Independent Test**:
```python
# Test model
record = WhereUsed(
    part_number="F0195",
    work_order_master="7961",
    seq_no=10,
    piece_no=1,
    qty_per=Decimal("1.2500"),
    fixed_qty=Decimal("5.0000"),
    scrap_percent=Decimal("5.00")
)
assert record.formatted_qty_per() == "1.2500"
assert record.formatted_scrap_percent() == "5.00%"

# Test query
cursor = connection.get_cursor()
results = get_part_bom_usage(cursor, "F0195")
assert len(results) == 6253  # Known test data
assert all(isinstance(r, WhereUsed) for r in results)
```

**Dependencies**: Phase 1 complete

**Parallel Opportunities**: T003 and T004 can be done in parallel; T006 and T007 are sequential

---

## Phase 3: Service Layer - Business Logic Update

**Objective**: Update PartService to use new BOM query.

### Tasks

- [ ] T008 [P] Update `get_bom_where_used()` method in `visual_order_lookup/services/part_service.py`:
  - Replace old query with call to `part_queries.get_part_bom_usage()`
  - Pass `part_number` parameter
  - Return List[WhereUsed] from query
  - Maintain existing error handling pattern

- [ ] T009 [P] Remove old inventory transaction query logic from `visual_order_lookup/services/part_service.py`:
  - Delete references to INVENTORY_TRANS table
  - Remove old WhereUsed field mappings
  - Clean up unused imports

**Completion Criteria**:
- PartService.get_bom_where_used() returns BOM data (not transaction data)
- Method signature unchanged: `get_bom_where_used(part_number: str) -> List[WhereUsed]`
- No references to old INVENTORY_TRANS query remain

**Independent Test**:
```python
service = PartService(db_connection)
records = service.get_bom_where_used("F0195")
assert len(records) == 6253
assert records[0].seq_no is not None  # BOM field exists
assert not hasattr(records[0], 'transaction_date')  # Old field gone
```

**Dependencies**: Phase 2 complete

**Parallel Opportunities**: T008 and T009 can be done in parallel

---

## Phase 4: UI Layer - Where Used Tab Update

**Objective**: Update Where Used tab display, formatting, and export functionality.

### Table Display Tasks

- [ ] T010 Update table column headers in `visual_order_lookup/ui/part_detail_view.py` (`_setup_ui()` method, around line 82):
  - Change from: ["Date", "Order/WO", "Customer", "Quantity", "Warehouse", "Location"]
  - Change to: ["Work Order/Master", "Seq #", "Piece #", "Quantity Per", "Fixed Qty", "Scrap %"]
  - Keep column count: 6 columns

- [ ] T011 Update table cell population in `visual_order_lookup/ui/part_detail_view.py` (`_refresh_where_used_page()` method, around line 328):
  - Column 0: `record.formatted_work_order()` (left-aligned)
  - Column 1: `record.formatted_seq_no()` (right-aligned)
  - Column 2: `record.formatted_piece_no()` (right-aligned)
  - Column 3: `record.formatted_qty_per()` (right-aligned)
  - Column 4: `record.formatted_fixed_qty()` (right-aligned)
  - Column 5: `record.formatted_scrap_percent()` (right-aligned)

- [ ] T012 Set text alignment for numeric columns in `visual_order_lookup/ui/part_detail_view.py` (`_refresh_where_used_page()` method):
  - Columns 1-5: Apply `Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter`
  - Column 0: Default left alignment

- [ ] T013 [P] Update empty state message in `visual_order_lookup/ui/part_detail_view.py` (`_refresh_where_used_page()` method):
  - Change message from transaction-related to: "No BOM usage found for this part"
  - Display when `len(self.where_used_records) == 0`

### CSV Export Tasks

- [ ] T014 [P] Update CSV export headers in `visual_order_lookup/ui/part_detail_view.py` (`_export_where_used()` method, around line 568):
  - Change from: ["Date", "Order/WO", "Customer", "Quantity", "Warehouse", "Location"]
  - Change to: ["Work Order/Master", "Seq #", "Piece #", "Quantity Per", "Fixed Qty", "Scrap %"]

- [ ] T015 [P] Update CSV export data rows in `visual_order_lookup/ui/part_detail_view.py` (`_export_where_used()` method, around line 573):
  - Row format: [formatted_work_order(), formatted_seq_no(), formatted_piece_no(), formatted_qty_per(), formatted_fixed_qty(), formatted_scrap_percent()]
  - Remove old field references (transaction_date, customer_name, warehouse_id, location_id)

### Pagination Tasks

- [ ] T016 [P] Verify pagination logic in `visual_order_lookup/ui/part_detail_view.py`:
  - Confirm page size remains 50 records
  - Verify page label format: "Page {page+1} of {total_pages} ({total_records} total records)"
  - Test navigation buttons (First, Previous, Next, Last)
  - No code changes needed if existing pagination works

### Integration Tasks

- [ ] T017 Update inventory module worker thread in `visual_order_lookup/ui/inventory_module.py`:
  - Verify `_on_search_part()` calls PartService.get_bom_where_used()
  - Ensure worker signal passes List[WhereUsed] to display_where_used()
  - No changes needed if existing flow is correct (likely just works)

**Completion Criteria**:
- Where Used tab displays 6 columns with new headers
- All numeric columns (1-5) are right-aligned
- CSV export has 6 columns with new headers
- CSV data matches table display format
- Empty state shows BOM-specific message
- Pagination controls work with new data

**Independent Test**:
```python
# Manual UI test steps:
1. Run application: python visual_order_lookup/main.py
2. Navigate to Inventory module
3. Search for part "F0195"
4. Click "Where Used" tab
5. Verify table shows 6 columns: Work Order/Master, Seq #, Piece #, Quantity Per, Fixed Qty, Scrap %
6. Verify numeric columns are right-aligned
7. Verify pagination shows "Page 1 of 126 (6253 total records)"
8. Click "Next" button → verify page 2 displays
9. Click "Export All as CSV"
10. Open CSV → verify headers and data format match table display
```

**Dependencies**: Phase 3 complete

**Parallel Opportunities**: T010-T012 are sequential (same method); T013-T016 can be done in parallel; T017 is independent

---

## Phase 5: Integration Testing & Performance Validation

**Objective**: Validate end-to-end functionality and performance targets.

### Tasks

- [ ] T018 Manual integration testing with test parts:
  - Test F0195 (6,253 records): Verify query <5s, pagination works, all 126 pages display correctly
  - Test F0209 (5,004 records): Verify export <10s, CSV contains all records with correct format
  - Test R0236 (3,487 records): Verify medium volume performance, pagination navigation
  - Test part with 0 BOM records: Verify empty state message displays, controls disabled

- [ ] T019 Performance validation and optimization:
  - Measure query time for F0195 (target: <5 seconds, expected: ~0.4s based on research)
  - Measure pagination rendering (target: <1 second)
  - Measure CSV export for F0209 (target: <10 seconds)
  - Document actual performance metrics
  - If performance issues found, investigate index usage and query plan

**Completion Criteria**:
- All manual tests pass for F0195, F0209, R0236
- Empty state handling works correctly
- Performance meets all targets (query <5s, pagination <1s, export <10s)
- No errors or exceptions during testing

**Independent Test**:
```bash
# Performance test script
python -c "
import time
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database import part_queries
from visual_order_lookup.utils.config import get_config

config = get_config()
conn = DatabaseConnection(config.connection_string)
cursor = conn.get_cursor()

start = time.time()
records = part_queries.get_part_bom_usage(cursor, 'F0195')
elapsed = time.time() - start

print(f'Query time: {elapsed:.3f}s for {len(records)} records')
assert elapsed < 5.0, f'Query too slow: {elapsed}s'
assert len(records) == 6253, f'Expected 6253 records, got {len(records)}'
print('Performance test PASSED')
"
```

**Dependencies**: Phase 4 complete

---

## Task Dependencies

```text
Phase 1 (Setup)
  └─> T001, T002
       └─> Phase 2 (Data Layer)
            └─> T003, T004 [parallel]
            └─> T005 → T006 → T007
                 └─> Phase 3 (Service Layer)
                      └─> T008, T009 [parallel]
                           └─> Phase 4 (UI Layer)
                                └─> T010 → T011 → T012
                                └─> T013, T014, T015, T016 [parallel]
                                └─> T017
                                     └─> Phase 5 (Integration)
                                          └─> T018 → T019
```

**Critical Path**: T001 → T002 → T005 → T006 → T007 → T008 → T010 → T011 → T012 → T018 → T019

**Parallel Execution Opportunities**:
- Phase 2: T003 + T004 can run in parallel
- Phase 3: T008 + T009 can run in parallel
- Phase 4: T013 + T014 + T015 + T016 can run in parallel

---

## Implementation Strategy

### MVP Approach

**Minimum Viable Product** (First working increment):
1. Complete Phase 1 + Phase 2 (Model + Query)
2. Complete Phase 3 (Service Layer)
3. Complete T010 + T011 + T012 only (basic table display)
4. Manual test with F0195

**Why this MVP**: Demonstrates core BOM data retrieval and display without export/polish features.

### Incremental Delivery

**Iteration 1** (MVP - 9 tasks):
- T001, T002, T003, T004, T005, T006, T007, T008, T010, T011, T012

**Iteration 2** (CSV Export - 3 tasks):
- T014, T015, T016

**Iteration 3** (Polish & Testing - 4 tasks):
- T009, T013, T017, T018, T019

### Recommended Execution Order

For a single developer (sequential):
1. T001, T002 (setup/validation)
2. T003, T004 (model - can be one commit)
3. T005, T006, T007 (query implementation)
4. T008 (service update)
5. T010, T011, T012 (basic UI)
6. **CHECKPOINT**: Manual test with F0195
7. T014, T015 (CSV export)
8. T013, T016, T017 (remaining UI)
9. T009 (cleanup)
10. T018, T019 (final testing)

For parallel work (2+ developers):
- Developer A: T001-T007 (data layer)
- Developer B: T008-T009 (service layer) **after** T007 complete
- Developer A: T010-T012 (core UI) **after** T008 complete
- Developer B: T013-T017 (export/polish) **in parallel with** T010-T012
- Both: T018, T019 (integration testing)

---

## Testing Notes

**Test Data** (from research.md):
- **F0195**: 6,253 BOM records (126 pages) - performance testing
- **F0209**: 5,004 BOM records (101 pages) - export testing
- **R0236**: 3,487 BOM records (70 pages) - medium volume testing

**Performance Targets**:
- Query execution: <5 seconds (measured: 0.404s for F0195)
- Pagination rendering: <1 second
- CSV export: <10 seconds

**Edge Cases to Test**:
- Part with 0 BOM records (empty state)
- Part with exactly 50 records (1 page)
- Part with 51 records (pagination boundary)
- Part with 10,000+ records (max performance test)

**No Automated Tests Required**: Feature spec does not request unit tests or automated testing. All testing is manual validation per acceptance criteria.

---

## File Change Summary

| File | Change Type | Lines Changed (est.) |
|------|-------------|---------------------|
| `visual_order_lookup/database/models.py` | UPDATE | ~80 (replace WhereUsed model) |
| `visual_order_lookup/database/part_queries.py` | NEW/UPDATE | ~60 (new query function) |
| `visual_order_lookup/services/part_service.py` | UPDATE | ~20 (method update + cleanup) |
| `visual_order_lookup/ui/part_detail_view.py` | UPDATE | ~50 (table + export updates) |
| `visual_order_lookup/ui/inventory_module.py` | VERIFY | 0 (likely no changes needed) |

**Total Estimated Changes**: ~210 lines across 5 files

---

## Risk Mitigation

| Risk | Mitigation Task |
|------|----------------|
| Database table names wrong | T001, T002 validate actual schema |
| Query performance slow | T019 measures and validates <5s target |
| UI alignment issues | T012 explicitly sets right-alignment |
| Export format mismatch | T015 uses same formatting methods as display |
| Empty state not handled | T013 adds explicit empty message |

---

## Completion Checklist

**Feature is complete when**:
- [ ] All 19 tasks marked complete
- [ ] Manual testing with F0195, F0209, R0236 passes (T018)
- [ ] Performance validation passes all targets (T019)
- [ ] Where Used tab displays 6 BOM columns (T010-T012)
- [ ] CSV export works with new format (T014-T015)
- [ ] Empty state displays correct message (T013)
- [ ] Code review approved
- [ ] Pull request merged to main branch

---

**Generated**: 2025-11-12 via `/speckit.tasks` command
**Ready for Implementation**: All tasks are executable with clear file paths and acceptance criteria
