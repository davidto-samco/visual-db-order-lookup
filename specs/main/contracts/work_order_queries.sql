-- Work Order Query Specifications for Engineering Module
-- Feature: 003-engineering-work-order-hierarchy
-- Date: 2025-01-14

-- ============================================================================
-- QUERY 1: Search Work Orders by BASE_ID
-- ============================================================================
-- Purpose: Search for work orders matching BASE_ID pattern
-- Used by: Engineering module search
-- Performance: <5 seconds for up to 1000 results
-- Returns: List of work orders with basic info

SELECT TOP 1000
       wo.BASE_ID,
       wo.LOT_ID,
       wo.SUB_ID,
       wo.PART_ID,
       p.DESCRIPTION AS part_description,
       wo.TYPE,
       wo.STATUS,
       wo.START_DATE,
       wo.COMPLETE_DATE,
       wo.ORDER_QTY,
       wo.CREATE_DATE
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID LIKE @base_id_pattern  -- Parameter: e.g., '8113%' for partial match
ORDER BY wo.CREATE_DATE DESC;

-- Example usage:
-- @base_id_pattern = '8113%'  -- Returns all work orders starting with 8113
-- @base_id_pattern = '%/26'   -- Returns all work orders with LOT_ID = 26


-- ============================================================================
-- QUERY 2: Get Work Order Header
-- ============================================================================
-- Purpose: Load complete work order header information
-- Used by: When user selects work order from list
-- Performance: <100ms (single record lookup)
-- Returns: Single work order with all details

SELECT wo.BASE_ID,
       wo.LOT_ID,
       wo.SUB_ID,
       wo.PART_ID,
       p.DESCRIPTION AS part_description,
       p.TYPE AS part_type,
       p.UNIT_OF_MEASURE,
       wo.TYPE AS work_order_type,
       wo.STATUS,
       wo.START_DATE,
       wo.COMPLETE_DATE,
       wo.ORDER_QTY,
       wo.CREATE_DATE,
       -- Aggregate counts for tree structure
       (SELECT COUNT(*) FROM OPERATION WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = wo.BASE_ID
          AND WORKORDER_LOT_ID = wo.LOT_ID
          AND WORKORDER_SUB_ID = wo.SUB_ID) AS operation_count,
       (SELECT COUNT(*) FROM LABOR_TICKET WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = wo.BASE_ID
          AND WORKORDER_LOT_ID = wo.LOT_ID
          AND WORKORDER_SUB_ID = wo.SUB_ID) AS labor_ticket_count,
       (SELECT COUNT(*) FROM INVENTORY_TRANS WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = wo.BASE_ID
          AND WORKORDER_LOT_ID = wo.LOT_ID
          AND WORKORDER_SUB_ID = wo.SUB_ID) AS inventory_trans_count
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = @base_id
  AND wo.LOT_ID = @lot_id
  AND wo.SUB_ID = @sub_id;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = ''


-- ============================================================================
-- QUERY 3: Get Operations for Work Order (Lazy Load Level 2)
-- ============================================================================
-- Purpose: Load all operations (routing steps) for a work order
-- Used by: When user expands "Operations" node in tree
-- Performance: <200ms (10-50 operations typical)
-- Returns: List of operations ordered by sequence

SELECT SEQUENCE,
       OPERATION_ID,
       DESCRIPTION,
       DEPARTMENT_ID,
       SETUP_HRS,
       RUN_HRS,
       STATUS,
       -- Requirement count for this operation
       (SELECT COUNT(*) FROM REQUIREMENT WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = @base_id
          AND WORKORDER_LOT_ID = @lot_id
          AND WORKORDER_SUB_ID = @sub_id
          AND OPERATION_SEQ_NO = op.SEQUENCE) AS requirement_count
FROM OPERATION op WITH (NOLOCK)
WHERE WORKORDER_BASE_ID = @base_id
  AND WORKORDER_LOT_ID = @lot_id
  AND WORKORDER_SUB_ID = @sub_id
ORDER BY SEQUENCE;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = ''


-- ============================================================================
-- QUERY 4: Get Requirements for Operation (Lazy Load Level 3)
-- ============================================================================
-- Purpose: Load material requirements for a specific operation
-- Used by: When user expands an Operation node
-- Performance: <100ms (5-20 requirements per operation typical)
-- Returns: List of parts required for operation

SELECT r.PART_ID,
       p.DESCRIPTION AS part_description,
       p.TYPE AS part_type,
       p.UNIT_OF_MEASURE,
       r.QTY_PER,
       r.FIXED_QTY,
       r.SCRAP_PERCENT,
       r.PIECE_NO,
       r.OPERATION_SEQ_NO
FROM REQUIREMENT r WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
WHERE r.WORKORDER_BASE_ID = @base_id
  AND r.WORKORDER_LOT_ID = @lot_id
  AND r.WORKORDER_SUB_ID = @sub_id
  AND r.OPERATION_SEQ_NO = @operation_seq
ORDER BY r.PART_ID;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = '', @operation_seq = 10


-- ============================================================================
-- QUERY 5: Get Part Details (Lazy Load Level 4)
-- ============================================================================
-- Purpose: Load detailed part information for a requirement
-- Used by: When user expands a Requirement node (optional - may use cached Part data)
-- Performance: <50ms (single record lookup)
-- Returns: Complete part master information

SELECT ID AS part_id,
       DESCRIPTION,
       TYPE,
       UNIT_OF_MEASURE,
       UNIT_MATERIAL_COST,
       UNIT_LABOR_COST,
       UNIT_BURDEN_COST,
       WHSALE_UNIT_COST,
       STATUS
FROM PART WITH (NOLOCK)
WHERE ID = @part_id;

-- Example usage:
-- @part_id = 'M28803'


-- ============================================================================
-- QUERY 6: Get Labor Tickets for Work Order (Lazy Load)
-- ============================================================================
-- Purpose: Load all labor transactions for a work order
-- Used by: When user expands "Labor" node in tree
-- Performance: <200ms (50-200 tickets typical)
-- Returns: List of labor tickets ordered by date descending

SELECT EMPLOYEE_ID,
       OPERATION_SEQ,
       LABOR_DATE,
       SETUP_HRS,
       RUN_HRS,
       (SETUP_HRS + RUN_HRS) AS total_hrs,
       LABOR_RATE,
       ((SETUP_HRS + RUN_HRS) * LABOR_RATE) AS total_cost
FROM LABOR_TICKET WITH (NOLOCK)
WHERE WORKORDER_BASE_ID = @base_id
  AND WORKORDER_LOT_ID = @lot_id
  AND WORKORDER_SUB_ID = @sub_id
ORDER BY LABOR_DATE DESC;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = ''


-- ============================================================================
-- QUERY 7: Get Inventory Transactions for Work Order (Lazy Load)
-- ============================================================================
-- Purpose: Load all material transactions (issues, returns, scrap) for a work order
-- Used by: When user expands "Materials" node in tree
-- Performance: <200ms (20-100 transactions typical)
-- Returns: List of material transactions ordered by date descending

SELECT it.PART_ID,
       p.DESCRIPTION AS part_description,
       it.TRANS_TYPE,
       it.QUANTITY,
       it.TRANS_DATE,
       it.LOCATION_ID,
       it.LOT_SERIAL_NO
FROM INVENTORY_TRANS it WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON it.PART_ID = p.ID
WHERE it.WORKORDER_BASE_ID = @base_id
  AND it.WORKORDER_LOT_ID = @lot_id
  AND it.WORKORDER_SUB_ID = @sub_id
  AND it.WORKORDER_BASE_ID IS NOT NULL  -- Only WO-related transactions
ORDER BY it.TRANS_DATE DESC;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = ''


-- ============================================================================
-- QUERY 8: Get WIP Balance for Work Order (Lazy Load)
-- ============================================================================
-- Purpose: Load cost accumulation for a work order
-- Used by: When user expands "WIP" node in tree
-- Performance: <50ms (single record lookup)
-- Returns: Single WIP balance record

SELECT MATERIAL_COST,
       LABOR_COST,
       BURDEN_COST,
       (MATERIAL_COST + LABOR_COST + BURDEN_COST) AS total_cost,
       LAST_UPDATED
FROM WIP_BALANCE WITH (NOLOCK)
WHERE WORKORDER_BASE_ID = @base_id
  AND WORKORDER_LOT_ID = @lot_id
  AND WORKORDER_SUB_ID = @sub_id;

-- Example usage:
-- @base_id = '8113', @lot_id = '26', @sub_id = ''


-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. All queries use WITH (NOLOCK) for read-only access (Constitutional requirement)
-- 2. Parameterized queries prevent SQL injection
-- 3. Lazy loading pattern: queries 3-8 only execute when user expands nodes
-- 4. Performance targets met through indexed lookups on composite FK (BASE_ID, LOT_ID, SUB_ID)
-- 5. Aggregate counts (e.g., requirement_count) used to show [+] indicator before expansion
-- 6. TOP 1000 on search prevents excessive result sets
