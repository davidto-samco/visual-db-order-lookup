# Feature Specification: Inventory Module Where-Used Enhancement

**Feature ID**: 002-inventory-where-used-enhancement
**Created**: 2025-11-12
**Status**: Planning
**Owner**: Spare Parts Department

## Overview

Enhance the Inventory module's "Where Used" tab to display BOM (Bill of Materials) structure information instead of inventory transaction data. The where-used view should show work order/master references, sequence numbers, piece numbers, quantity per, fixed quantity, and scrap percentage from the BOM_DET table.

### Context

The current where-used implementation shows inventory transaction history (INVENTORY_TRANS table) with columns: Date, Order/WO, Customer, Quantity, Warehouse, Location. This provides transaction-level data but doesn't show the underlying BOM structure that defines how parts are used in assemblies and manufacturing processes.

The Spare Parts department needs to see BOM structure information to understand:
- Which assemblies (work orders/masters) use this part
- The hierarchical position in the BOM (sequence number)
- Physical positioning (piece number)
- Material requirements (quantity per, fixed quantity)
- Manufacturing considerations (scrap percentage)

This information is critical for:
- Answering customer questions about part usage in specific assemblies
- Understanding material requirements for quotes and orders
- Identifying which customer orders used a part in their BOM structure
- Troubleshooting manufacturing issues related to part placement

### Relationship to Legacy System

In VISUAL Enterprise, the Manufacturing Window module provides BOM browsing with these exact fields. This feature brings that specific BOM structure viewing capability into the order lookup application's Inventory module, maintaining read-only access to the Visual database.

## Requirements

### Functional Requirements

**FR-1: BOM Structure Display**
- Where-used tab MUST display BOM detail records from REQUIREMENT table (BOM structure data)
- Columns displayed (in order):
  1. Work Order/Master - The parent assembly/work order ID
  2. Seq # - Sequence number in BOM (REQUIREMENT.OPERATION_SEQ_NO)
  3. Piece # - Piece number identifier (REQUIREMENT.PIECE_NO)
  4. Quantity Per - Quantity of this part per parent assembly (REQUIREMENT.QTY_PER)
  5. Fixed Qty - Fixed quantity regardless of parent qty (REQUIREMENT.FIXED_QTY)
  6. Scrap % - Scrap percentage for manufacturing (REQUIREMENT.SCRAP_PERCENT)

**FR-2: Work Order/Master Resolution**
- Work Order/Master column MUST show the BASE_ID from WORK_ORDER table
- Display format: BASE_ID as-is (e.g., "7961", "10002", "Q10-0202")

**Note**: Original spec proposed customer order linkage via CUST_ORDER_ID field. Phase 0 research found the WBS_CUST_ORDER_ID field in WORK_ORDER table exists but appears unused/empty in production data. Customer order linkage feature removed from scope pending further investigation. See research.md Section 2 for details.

**FR-3: Data Formatting**
- Seq # and Piece #: Integer display, right-aligned
- Quantity Per: Decimal with 4 decimal places (e.g., "1.2500"), right-aligned
- Fixed Qty: Decimal with 4 decimal places, right-aligned
- Scrap %: Percentage with 2 decimal places (e.g., "5.00%"), right-aligned
- Default zero values display as "0.00" or "0.00%" as appropriate

**FR-4: Pagination**
- Maintain existing pagination controls (First, Previous, Next, Last)
- Maintain existing page size: 50 records per page
- Update page label format: "Page {current} of {total} ({total_records} total records)"

**FR-5: Export Functionality**
- Export button MUST export ALL where-used records to CSV
- CSV headers: "Work Order/Master", "Seq #", "Piece #", "Quantity Per", "Fixed Qty", "Scrap %"
- CSV values: formatted as displayed (including % symbol for scrap)
- File naming: `where_used_{part_number}.csv`

**FR-6: Empty State Handling**
- If part has no BOM usage (no BOM_DET records), display message: "No BOM usage found for this part"
- Pagination controls disabled when no records
- Export button disabled when no records

### Non-Functional Requirements

**NFR-1: Performance**
- BOM query MUST complete within 5 seconds for parts with up to 10,000 BOM records
- Pagination rendering MUST complete within 1 second for 50 records
- Export MUST complete within 10 seconds for up to 10,000 records

**NFR-2: Database Access**
- Read-only access to Visual database (Constitutional requirement)
- Query tables: REQUIREMENT, WORK_ORDER (see Database Schema Reference for details)
- Use parameterized queries to prevent SQL injection
- Use WITH (NOLOCK) hint for all queries

**NFR-3: UI Consistency**
- Match existing where-used tab layout and styling
- Maintain existing pagination control behavior
- Follow existing export dialog patterns
- Use same alternating row colors and selection behavior

## Database Schema Reference

> **⚠️ IMPORTANT**: This section shows the original specification assumptions. Phase 0 research discovered the Visual database uses **REQUIREMENT** and **WORK_ORDER** tables instead. See [research.md](./research.md) for actual schema validation and [data-model.md](./data-model.md) for implemented model.

### Original Assumptions (Revised by Research)

**Assumed Tables**: BOM_DET, BOM_MASTER
**Actual Tables**: REQUIREMENT, WORK_ORDER

**Assumed Columns** vs **Actual Columns**:
- `BOM_DET.SEQ_NO` → `REQUIREMENT.OPERATION_SEQ_NO` (smallint)
- `BOM_DET.PIECE_NO` → `REQUIREMENT.PIECE_NO` (smallint)
- `BOM_DET.QTY_PER` → `REQUIREMENT.QTY_PER` (decimal 15,8)
- `BOM_DET.FIXED_QTY` → `REQUIREMENT.FIXED_QTY` (decimal 14,4)
- `BOM_DET.SCRAP_PERCENT` → `REQUIREMENT.SCRAP_PERCENT` (decimal 5,2)
- `BOM_MASTER.BASE_ID` → `WORK_ORDER.BASE_ID` (varchar 30)

**Join Pattern**: REQUIREMENT joins to WORK_ORDER via composite key (BASE_ID + LOT_ID + SUB_ID), not single MASTER_ID.

### Actual Query Pattern (From Research)

```sql
SELECT
    wo.BASE_ID AS work_order_master,
    r.OPERATION_SEQ_NO AS seq_no,
    r.PIECE_NO AS piece_no,
    r.QTY_PER AS qty_per,
    r.FIXED_QTY AS fixed_qty,
    r.SCRAP_PERCENT AS scrap_percent
FROM REQUIREMENT r WITH (NOLOCK)
INNER JOIN WORK_ORDER wo WITH (NOLOCK)
    ON r.WORKORDER_BASE_ID = wo.BASE_ID
   AND r.WORKORDER_LOT_ID = wo.LOT_ID
   AND r.WORKORDER_SUB_ID = wo.SUB_ID
WHERE r.PART_ID = ?
ORDER BY wo.BASE_ID, r.OPERATION_SEQ_NO
```

**Performance**: Query tested at 0.404s for 6,253 records (see research.md for details).

## Implementation Scope

### In Scope
- Update WhereUsed model to include new BOM fields
- Create new database query for BOM_DET data
- Update part_detail_view.py to display new columns
- Update CSV export with new column headers and data
- Update pagination labels and controls

### Out of Scope
- Hierarchical BOM tree view (flat list only)
- Editing BOM structure (read-only per Constitution)
- BOM explosion or rollup calculations
- Historical BOM versions or revisions
- Integration with work order scheduling
- Real-time inventory allocation

## Success Criteria

1. Where-used tab displays BOM structure columns (Work Order/Master, Seq #, Piece #, Quantity Per, Fixed Qty, Scrap %)
   - **Note**: Implementation expanded baseline 6 columns to 8 columns by adding manufactured part information (Manufactured PART ID + MFG PART DESCRIPTION from WORK_ORDER + PART tables). This enhancement improves usability by showing which assembly uses the part.
2. Data correctly retrieved from REQUIREMENT and WORK_ORDER tables (via composite key join)
3. Pagination works with 50 records per page
4. Export functionality generates CSV with all BOM records
5. Performance meets NFR-1 targets (5s query, 1s pagination, 10s export)
6. No database write operations (Constitutional compliance)
7. UI matches existing Inventory module styling and behavior

## Acceptance Tests

### Test 1: BOM Data Display
- Given: Part "12345" exists and is used in 3 BOMs
- When: User searches for part and views Where Used tab
- Then:
  - Table displays 3 rows with BOM structure data
  - All 6 columns populated with correct values
  - Work Order/Master shows BASE_ID or "CUST_ORDER_ID (BASE_ID)" format
  - Numeric values formatted per FR-3

### Test 2: Pagination
- Given: Part has 150 BOM records
- When: User navigates to Where Used tab
- Then:
  - Page 1 displays 50 records
  - Page label shows "Page 1 of 3 (150 total records)"
  - Next/Last buttons enabled, Previous/First disabled
  - User can navigate through all 3 pages

### Test 3: CSV Export
- Given: Part has 150 BOM records across 3 pages
- When: User clicks "Export All as CSV"
- Then:
  - CSV file contains header row + 150 data rows
  - All columns match display format
  - File named correctly: `where_used_{part_number}.csv`

### Test 4: Empty State
- Given: Part has no BOM usage
- When: User views Where Used tab
- Then:
  - Table empty with message "No BOM usage found for this part"
  - Pagination controls disabled
  - Export button disabled

### Test 5: Performance
- Given: Part has 5,000 BOM records
- When: User loads Where Used tab
- Then: Query completes within 5 seconds
- When: User exports to CSV
- Then: Export completes within 10 seconds

## Dependencies

- Existing Inventory module implementation
- Visual database BOM_DET and BOM_MASTER tables
- PyQt6 table widget functionality
- CSV export infrastructure

## Risks & Mitigation

**Risk**: BOM_DET table may have different column names or structure than documented
- **Mitigation**: Database schema investigation during Phase 0 research

**Risk**: Performance degradation with large BOM structures (10,000+ records)
- **Mitigation**: Pagination limits display to 50 records; export may need streaming for very large datasets

**Risk**: CUST_ORDER_ID linkage may not exist for all BOMs
- **Mitigation**: Graceful fallback to BASE_ID only when CUST_ORDER_ID is NULL

## Open Questions

~~All questions resolved by Phase 0 research (see research.md for details).~~

### Resolved Questions

**Q1: What is the exact column name for Piece # in BOM_DET?**
✅ **Answer**: `REQUIREMENT.PIECE_NO` (table is REQUIREMENT, not BOM_DET)

**Q2: Are SEQ_NO and PIECE_NO both integers, or is PIECE_NO a string?**
✅ **Answer**: Both are `smallint` (2-byte integers, NOT NULL, range -32768 to 32767)

**Q3: Should scrap % display show "N/A" or "0.00%" when NULL?**
✅ **Answer**: Display "0.00%" - All BOM fields have NOT NULL constraints with default value 0. No NULL handling needed.

**Q4: Do we need to filter BOM records by active/inactive status?**
✅ **Answer**: No filtering needed. REQUIREMENT table represents all BOM records; STATUS field exists but not relevant for where-used display.

**Q5: Should we show BOM records for all revision levels or only current?**
✅ **Answer**: All records displayed. No revision filtering required - BASE_ID uniquely identifies work orders regardless of revision.

### Remaining Open Items

None - feature fully specified.

## Notes

- This replaces transaction history view with BOM structure view
- Previous INVENTORY_TRANS query will be replaced, not deprecated
- Feature aligns with Constitution Principle III (read-only) and Principle VI (minimal UI)
- No cloud services or internet connectivity required beyond WLAN database access
