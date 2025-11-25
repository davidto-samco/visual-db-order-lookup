# Implementation Plan: Inventory Module Where-Used Enhancement

**Branch**: `002-inventory-where-used-enhancement` | **Date**: 2025-11-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-inventory-where-used-enhancement/spec.md`

## Summary

Enhance the Inventory module's "Where Used" tab to display BOM (Bill of Materials) structure information from the BOM_DET table instead of inventory transaction history. The feature replaces the current transaction view (Date, Order/WO, Customer, Quantity, Warehouse, Location) with BOM structure columns (Work Order/Master, Seq #, Piece #, Quantity Per, Fixed Qty, Scrap %) while maintaining the existing pagination, export, and UI patterns.

**Technical Approach**: Update the WhereUsed data model to include BOM fields, create a new database query joining BOM_DET and BOM_MASTER tables, and modify the part_detail_view.py table display to show the new columns with appropriate formatting. Maintain read-only database access per constitution.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyQt6 (GUI framework), pyodbc (SQL Server connectivity), python-dotenv (configuration)
**Storage**: SQL Server Visual database (read-only access via WLAN)
**Testing**: pytest
**Target Platform**: Windows 10/11 desktop
**Project Type**: Single project (desktop application)
**Performance Goals**:
- BOM query: <5 seconds for 10,000 records
- Pagination rendering: <1 second for 50 records
- CSV export: <10 seconds for 10,000 records

**Constraints**:
- Read-only database access (Constitutional requirement)
- No database schema modifications
- Total response time <15 seconds per operation
- Memory footprint <100MB

**Scale/Scope**:
- 1 module enhancement (Inventory module)
- 1 tab modification (Where Used tab)
- 3 database tables queried (BOM_DET, BOM_MASTER, CUSTOMER_ORDER)
- 6 display columns
- Support for 10,000+ BOM records per part

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle III: Read-Only Database Access
**Status**: ✓ PASS
- All queries use SELECT statements only
- BOM_DET and BOM_MASTER tables accessed read-only
- No INSERT, UPDATE, DELETE, or DDL operations
- Parameterized queries prevent SQL injection

### Principle II: Reliable Database Connection
**Status**: ✓ PASS
- Uses existing DatabaseConnection infrastructure
- All queries use WITH (NOLOCK) hint
- Error handling via existing ErrorHandler framework
- Timeout limits enforced (5s for BOM query)

### Principle VI: Minimal UI with Error Visibility
**Status**: ✓ PASS
- Maintains existing tab structure (no new UI paradigms)
- Reuses existing pagination controls
- Existing export functionality pattern maintained
- Error states display actionable messages

### Performance Standards: Response Times
**Status**: ✓ PASS
- BOM query max 5 seconds (well under 15s total limit)
- Pagination rendering <1 second
- Export <10 seconds
- Total user wait time <15 seconds

### Legacy System Context: Replacement Scope
**Status**: ✓ PASS
- Feature enhances existing Customer Order Lookup functionality
- BOM structure viewing is directly related to order/part analysis
- Does NOT enter Manufacturing Window territory (no BOM editing, explosion, or hierarchical tree)
- Read-only BOM viewing supports part lookup use case

### Quality Requirements: Testing Gates
**Status**: ✓ PASS
- Database query testing with BOM_DET/BOM_MASTER tables required
- Edge case testing: empty BOM, NULL values, missing CUST_ORDER_ID
- Performance testing with 5,000+ record sets
- CSV export validation

**No violations detected. Feature fully complies with constitution.**

## Project Structure

### Documentation (this feature)

```text
specs/002-inventory-where-used-enhancement/
├── plan.md              # This file
├── research.md          # Phase 0: Database schema investigation
├── data-model.md        # Phase 1: WhereUsed model definition
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/           # Phase 1: Database query contracts
│   └── bom_query.sql    # BOM_DET query specification
└── tasks.md             # Phase 2: Implementation tasks (via /speckit.tasks)
```

### Source Code (repository root)

```text
visual_order_lookup/
├── database/
│   ├── models.py               # UPDATE: WhereUsed model with BOM fields
│   └── part_queries.py         # UPDATE: Add get_part_bom_usage() query
├── services/
│   └── part_service.py         # UPDATE: Add get_bom_where_used() method
├── ui/
│   └── part_detail_view.py     # UPDATE: Where Used tab columns and formatting
└── tests/
    ├── database/
    │   └── test_part_queries.py # NEW: BOM query tests
    └── ui/
        └── test_part_detail_view.py # UPDATE: Where Used display tests
```

**Structure Decision**: This is a single-project desktop application using the existing PyQt6 structure. The feature enhances the visual_order_lookup/ui/part_detail_view.py component and adds database query logic to visual_order_lookup/database/part_queries.py. No new top-level modules required - all changes integrate into existing Inventory module architecture.

## Complexity Tracking

> **No complexity violations** - Feature fully complies with constitution requirements.

---

## Phase 0: Research Tasks

**Objective**: Resolve all NEEDS CLARIFICATION items from Technical Context through database schema investigation and BOM table analysis.

### Research Questions to Answer

1. **BOM_DET Schema Validation**
   - Confirm exact column names: SEQ_NO, PIECE_NO, QTY_PER, FIXED_QTY, SCRAP_PERCENT
   - Determine data types for each column
   - Check for NULL handling requirements
   - Identify primary and foreign keys

2. **BOM_MASTER Schema Validation**
   - Confirm BASE_ID and CUST_ORDER_ID columns exist
   - Determine join relationship to BOM_DET (via MASTER_ID)
   - Check if CUST_ORDER_ID can be NULL

3. **Query Performance Baseline**
   - Test BOM_DET query with parts having 100, 1000, 5000, 10000 records
   - Measure query execution time
   - Identify if indexes exist on PART_ID

4. **Data Format Discovery**
   - Determine if PIECE_NO is integer or varchar
   - Check decimal precision for QTY_PER, FIXED_QTY, SCRAP_PERCENT
   - Identify typical value ranges for each field

5. **Edge Case Investigation**
   - Parts with no BOM usage (0 records in BOM_DET)
   - BOMs with NULL CUST_ORDER_ID
   - NULL values in SEQ_NO, PIECE_NO, QTY_PER, FIXED_QTY, SCRAP_PERCENT
   - Multiple BOMs using same part (verify ORDER BY clause)

**Output**: `research.md` with database schema details, query performance metrics, and data format specifications.

## Phase 1: Design & Contracts

**Objective**: Generate data model, database query contracts, and developer quickstart.

### Data Model (data-model.md)

**WhereUsed Model Update**:
- Add fields: `work_order_master`, `seq_no`, `piece_no`, `qty_per`, `fixed_qty`, `scrap_percent`
- Remove fields: `transaction_date`, `warehouse_id`, `location_id`
- Add property: `formatted_work_order()` - returns "CUST_ORDER (BASE_ID)" or BASE_ID
- Add property: `formatted_scrap_percent()` - returns "5.00%" format

**Relationships**:
- WhereUsed represents one row from BOM_DET + BOM_MASTER join
- Links to Part via `part_number` field
- Optional link to CustomerOrder via `cust_order_id` (when not NULL)

### API Contracts (contracts/)

**Database Query Contract** (`contracts/bom_query.sql`):
```sql
-- Query: get_part_bom_usage
-- Purpose: Retrieve BOM structure records for a given part
-- Performance: Must complete <5s for 10,000 records
-- Tables: BOM_DET (primary), BOM_MASTER (join), CUSTOMER_ORDER (optional display)

SELECT
    bm.BASE_ID,
    bm.CUST_ORDER_ID,
    bd.SEQ_NO,
    bd.PIECE_NO,
    bd.QTY_PER,
    bd.FIXED_QTY,
    bd.SCRAP_PERCENT
FROM BOM_DET bd WITH (NOLOCK)
INNER JOIN BOM_MASTER bm WITH (NOLOCK) ON bd.MASTER_ID = bm.ID
WHERE bd.PART_ID = ?
ORDER BY bm.BASE_ID, bd.SEQ_NO
```

**Parameters**:
- `part_number` (str): Part ID to search for

**Returns**: List of WhereUsed objects

**Error Handling**:
- pyodbc.Error → log and raise Exception with user-friendly message
- Empty result set → return empty list (not None)
- NULL value handling → map to None in model, display as "N/A"

### Quickstart (quickstart.md)

Developer setup:
1. Environment: Windows 10/11, Python 3.11+, WLAN database access
2. Dependencies: PyQt6, pyodbc, pytest
3. Database: Visual SQL Server connection via .env file
4. Testing: pytest with mock database for BOM queries

Run tests: `pytest visual_order_lookup/tests/database/test_part_queries.py -v`

**Output**: `data-model.md`, `contracts/bom_query.sql`, `quickstart.md`

## Phase 2: Implementation Planning

**Note**: This phase is handled by `/speckit.tasks` command (not part of `/speckit.plan`).

Implementation will include:
1. Update WhereUsed model in `visual_order_lookup/database/models.py`
2. Add `get_part_bom_usage()` query to `visual_order_lookup/database/part_queries.py`
3. Update `PartService.get_bom_where_used()` in `visual_order_lookup/services/part_service.py`
4. Modify Where Used tab display in `visual_order_lookup/ui/part_detail_view.py`:
   - Update table columns
   - Update formatting logic
   - Update CSV export headers and data
5. Add tests for BOM query and display

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| BOM_DET column names differ from spec | High | Medium | Phase 0 database schema investigation |
| Query performance <5s with 10k records | High | Low | Add indexes if needed (DBA approval), pagination limits display |
| PIECE_NO data type mismatch | Medium | Medium | Phase 0 research validates data types |
| NULL handling in BOM fields | Low | High | Design NULL→"N/A" display mapping in Phase 1 |

## Success Metrics

- [ ] Constitution check passes (no violations)
- [ ] Database schema research complete (Phase 0)
- [ ] Data model documented (Phase 1)
- [ ] Query contract defined (Phase 1)
- [ ] Performance requirements met (<5s query, <1s pagination, <10s export)
- [ ] All Open Questions from spec.md resolved

---

**Next Steps**: Execute Phase 0 research to investigate BOM_DET and BOM_MASTER table schemas in Visual database.
