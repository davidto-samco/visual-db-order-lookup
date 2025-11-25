-- ============================================================================
-- Database Query Contract: get_part_bom_usage
-- ============================================================================
-- Feature: 002-inventory-where-used-enhancement
-- Purpose: Retrieve BOM structure records showing where a part is used
-- Date: 2025-11-12
-- Status: Phase 1 Design
-- ============================================================================

-- QUERY METADATA
-- ============================================================================
-- Query Name: get_part_bom_usage
-- Returns: List[WhereUsed] - BOM usage records for a part
-- Performance Target: <5 seconds for 10,000 records
-- Measured Performance: 0.404 seconds for 6,253 records (F0195)
-- Tables: REQUIREMENT (primary), WORK_ORDER (join)
-- Index: X_REQUIREMENT_1 on PART_ID (non-clustered)
-- ============================================================================

-- QUERY DEFINITION
-- ============================================================================
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
WHERE r.PART_ID = ?  -- Parameterized: part_number (str)
ORDER BY wo.BASE_ID, r.OPERATION_SEQ_NO;

-- ============================================================================
-- PARAMETERS
-- ============================================================================
-- @param part_number (str): Part ID to search for (e.g., "F0195")
--   - Type: varchar
--   - Required: Yes
--   - Validation: Non-empty string
--   - Example: "F0195", "R0236", "12345"
--
-- ============================================================================

-- ============================================================================
-- RETURN COLUMNS
-- ============================================================================
-- work_order_master: varchar - Work order/assembly BASE_ID
--   - Source: WORK_ORDER.BASE_ID
--   - Nullable: No
--   - Example: "7961", "Q10-0202", "4049 R3"
--   - Display: As-is (no formatting)
--
-- seq_no: smallint - Sequence number in BOM structure
--   - Source: REQUIREMENT.OPERATION_SEQ_NO
--   - Nullable: No (default: 0)
--   - Range: -32768 to 32767
--   - Example: 10, 20, 0
--   - Display: Integer string, right-aligned
--
-- piece_no: smallint - Piece number identifier
--   - Source: REQUIREMENT.PIECE_NO
--   - Nullable: No (default: 0)
--   - Range: -32768 to 32767
--   - Example: 1, 2, 0
--   - Display: Integer string, right-aligned
--
-- qty_per: decimal(15,8) - Quantity of part per parent assembly
--   - Source: REQUIREMENT.QTY_PER
--   - Nullable: No (default: 0.00000000)
--   - Precision: 15 total digits, 8 decimal places
--   - Example: 1.25000000, 0.50000000
--   - Display: 4 decimal places ("1.2500"), right-aligned
--
-- fixed_qty: decimal(14,4) - Fixed quantity regardless of parent qty
--   - Source: REQUIREMENT.FIXED_QTY
--   - Nullable: No (default: 0.0000)
--   - Precision: 14 total digits, 4 decimal places
--   - Example: 5.0000, 10.5000
--   - Display: 4 decimal places ("5.0000"), right-aligned
--
-- scrap_percent: decimal(5,2) - Scrap percentage for manufacturing
--   - Source: REQUIREMENT.SCRAP_PERCENT
--   - Nullable: No (default: 0.00)
--   - Precision: 5 total digits, 2 decimal places
--   - Range: Typically 0-100
--   - Example: 5.00, 10.50, 0.00
--   - Display: 2 decimal places + "%" symbol ("5.00%"), right-aligned
--
-- ============================================================================

-- ============================================================================
-- RESULT SET CHARACTERISTICS
-- ============================================================================
-- Ordering: Sorted by work_order_master (BASE_ID), then seq_no (OPERATION_SEQ_NO)
-- Cardinality: 0 to 10,000+ records per part
-- Empty Result: Returns 0 rows if part has no BOM usage (valid condition)
-- Duplicates: No duplicates (composite key ensures uniqueness per work order+seq)
--
-- Example Row Counts (from research):
--   F0195: 6,253 records
--   F0209: 5,004 records
--   R0236: 3,487 records
--   Typical part: 0-100 records
-- ============================================================================

-- ============================================================================
-- JOIN EXPLANATION
-- ============================================================================
-- The JOIN between REQUIREMENT and WORK_ORDER uses a 3-column composite key:
--   - WORKORDER_BASE_ID (primary work order identifier)
--   - WORKORDER_LOT_ID (lot/batch identifier)
--   - WORKORDER_SUB_ID (sub-assembly identifier)
--
-- This composite key is necessary because WORK_ORDER uses all three columns
-- as its primary key. A single BASE_ID is not sufficient for unique identification.
--
-- Performance Impact: Composite key join is optimized with indexes
-- ============================================================================

-- ============================================================================
-- PERFORMANCE CHARACTERISTICS
-- ============================================================================
-- Query Execution Plan:
--   1. Index Seek on REQUIREMENT using X_REQUIREMENT_1 (PART_ID)
--   2. Nested Loop Join to WORK_ORDER on composite key
--   3. Sort by BASE_ID, OPERATION_SEQ_NO
--
-- Measured Performance (Production Database):
--   - F0195 (6,253 records): 0.404 seconds
--   - Estimated 10,000 records: <1 second
--
-- Performance Optimizations:
--   - WITH (NOLOCK) hint prevents lock contention
--   - PART_ID has non-clustered index (X_REQUIREMENT_1)
--   - Composite key join uses clustered index on WORK_ORDER
--   - ORDER BY uses columns from index for optimal sorting
--
-- Performance Requirements:
--   - Target: <5 seconds for 10,000 records ✓ PASS
--   - Measured: 0.404s for 6,253 records (only 8% of target)
-- ============================================================================

-- ============================================================================
-- ERROR HANDLING
-- ============================================================================
-- Database Errors:
--   - pyodbc.Error → Catch and re-raise as user-friendly Exception
--   - Connection timeout → Display "Database connection timed out" message
--   - Invalid PART_ID → Returns empty result set (not an error)
--
-- NULL Handling:
--   - All columns have NOT NULL constraints with defaults
--   - No NULL values exist in result set
--   - No special NULL handling required
--
-- Edge Cases:
--   - Empty result (part not used): Return [] (empty list)
--   - Zero values: Valid data, display as "0.0000" or "0.00%"
--   - Large result set (10,000+): Query optimized, pagination in UI
-- ============================================================================

-- ============================================================================
-- PYTHON IMPLEMENTATION CONTRACT
-- ============================================================================

-- Function Signature:
-- def get_part_bom_usage(cursor: pyodbc.Cursor, part_number: str) -> List[WhereUsed]:
--
-- Parameters:
--   cursor: Active database cursor with connection to Visual database
--   part_number: Part ID to search for (e.g., "F0195")
--
-- Returns:
--   List[WhereUsed]: List of BOM usage records, empty list if none found
--
-- Raises:
--   Exception: Database query failed (user-friendly error message)
--   ValueError: Invalid part_number (empty or None)
--
-- Example Usage:
--   cursor = connection.get_cursor()
--   records = get_part_bom_usage(cursor, "F0195")
--   # Returns: [WhereUsed(...), WhereUsed(...), ...] (6,253 records)
--
--   cursor = connection.get_cursor()
--   records = get_part_bom_usage(cursor, "NONEXISTENT")
--   # Returns: [] (empty list, not None)
--
-- ============================================================================

-- ============================================================================
-- TESTING RECOMMENDATIONS
-- ============================================================================

-- Unit Tests:
--   1. test_bom_query_valid_part()
--      - Given: Part "F0195" exists with 6,253 BOM records
--      - When: Query executed
--      - Then: Returns 6,253 WhereUsed objects
--
--   2. test_bom_query_empty_result()
--      - Given: Part "NONEXISTENT" has no BOM usage
--      - When: Query executed
--      - Then: Returns empty list []
--
--   3. test_bom_query_ordering()
--      - Given: Part with multiple work orders
--      - When: Query executed
--      - Then: Results sorted by BASE_ID, then OPERATION_SEQ_NO
--
--   4. test_bom_query_data_types()
--      - Given: Any valid part
--      - When: Query executed
--      - Then: All fields have correct Python types (str, int, Decimal)
--
-- Integration Tests:
--   1. test_query_performance_large_dataset()
--      - Given: Part "F0195" with 6,253 records
--      - When: Query executed
--      - Then: Completes in <5 seconds
--
--   2. test_query_with_parameterized_input()
--      - Given: Part number with special characters
--      - When: Query executed with parameterized query
--      - Then: SQL injection prevented, safe execution
--
-- Test Data:
--   - High volume: F0195 (6,253 records), F0209 (5,004 records)
--   - Medium volume: R0236 (3,487 records)
--   - Low volume: Any part with 0-100 records
--   - No usage: Create test part not used in any BOM
--
-- ============================================================================

-- ============================================================================
-- SAMPLE OUTPUT
-- ============================================================================

-- Input: part_number = "F0195"
-- Output (first 3 rows):
--
-- work_order_master | seq_no | piece_no | qty_per      | fixed_qty | scrap_percent
-- ------------------|--------|----------|--------------|-----------|---------------
-- 7961              | 10     | 1        | 1.25000000   | 0.0000    | 5.00
-- 7961              | 20     | 2        | 2.50000000   | 0.0000    | 0.00
-- 8563              | 0      | 0        | 0.00000000   | 5.0000    | 10.00
--
-- (6,250 more rows...)
--
-- ============================================================================

-- ============================================================================
-- DEPENDENCIES
-- ============================================================================
-- Tables:
--   - REQUIREMENT (primary) - BOM detail records
--   - WORK_ORDER (join) - Work order/assembly master records
--
-- Indexes:
--   - REQUIREMENT.X_REQUIREMENT_1 (PART_ID) - Non-clustered index for fast lookup
--   - WORK_ORDER: Clustered index on (BASE_ID, LOT_ID, SUB_ID)
--
-- Constraints:
--   - REQUIREMENT.PART_ID: NOT NULL
--   - WORK_ORDER.BASE_ID: NOT NULL (part of primary key)
--   - All numeric fields: NOT NULL with defaults
--
-- ============================================================================

-- ============================================================================
-- CONSTITUTIONAL COMPLIANCE
-- ============================================================================
-- Principle III: Read-Only Database Access
--   - Query uses SELECT only (no INSERT, UPDATE, DELETE, DDL) ✓
--   - WITH (NOLOCK) hint prevents write locks ✓
--   - Parameterized query prevents SQL injection ✓
--
-- Principle II: Reliable Database Connection
--   - Error handling for connection failures ✓
--   - Timeout enforcement (<5s performance target) ✓
--   - Clear error messages for users ✓
--
-- Performance Standards: Response Times
--   - Query target: <5 seconds ✓
--   - Measured: 0.404 seconds (8% of target) ✓
--   - Total operation: <15 seconds with UI rendering ✓
--
-- ============================================================================

-- ============================================================================
-- VERSION HISTORY
-- ============================================================================
-- v1.0 - 2025-11-12
--   - Initial contract based on Phase 0 research
--   - Tables: REQUIREMENT + WORK_ORDER (not BOM_DET + BOM_MASTER)
--   - Columns: OPERATION_SEQ_NO (not SEQ_NO)
--   - Performance: Validated with 6,253 record test (0.404s)
--
-- ============================================================================
-- END OF CONTRACT
-- ============================================================================
