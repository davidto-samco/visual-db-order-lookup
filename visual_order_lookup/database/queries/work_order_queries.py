"""Work Order query functions for Engineering Module.

This module provides database query functions for work order hierarchy data:
- search_work_orders: Search by BASE_ID pattern
- get_work_order_header: Load header with aggregate counts
- get_operations: Load operations for work order (lazy)
- get_requirements: Load requirements for operation (lazy)
- get_operation_children: Load flattened requirements + child operations (lazy, flattened mode)
- get_labor_tickets: Load labor transactions (lazy)
- get_inventory_transactions: Load material transactions (lazy)
- get_wip_balance: Load WIP costs (lazy)
- get_work_order_hierarchy: Recursive query for child work orders via SUBORD_WO_SUB_ID

All queries use WITH (NOLOCK) for read-only access and parameterized queries.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import pyodbc

from visual_order_lookup.database.models.work_order import (
    WorkOrder,
    Operation,
    Requirement,
    LaborTicket,
    InventoryTransaction,
    WIPBalance,
)

logger = logging.getLogger(__name__)


def search_work_orders(cursor: pyodbc.Cursor, base_id_pattern: str, limit: int = 1000) -> List[WorkOrder]:
    """Search for work orders matching BASE_ID pattern.

    Args:
        cursor: Database cursor
        base_id_pattern: BASE_ID search pattern (supports wildcards, e.g., '8113%')
        limit: Maximum results to return (default 1000)

    Returns:
        List of WorkOrder objects ordered by CREATE_DATE DESC

    Raises:
        ValueError: If base_id_pattern is empty or invalid
        pyodbc.Error: If database query fails
    """
    if not base_id_pattern or not base_id_pattern.strip():
        raise ValueError("base_id_pattern cannot be empty")

    base_id_pattern = base_id_pattern.strip().upper()

    # Add wildcard if not present
    if '%' not in base_id_pattern:
        base_id_pattern = f"{base_id_pattern}%"

    query = """
        SELECT TOP (?)
               wo.BASE_ID,
               wo.LOT_ID,
               wo.SUB_ID,
               wo.PART_ID,
               p.DESCRIPTION AS part_description,
               wo.TYPE,
               wo.STATUS,
               wo.SCHED_START_DATE,
               wo.CLOSE_DATE,
               wo.DESIRED_QTY,
               wo.CREATE_DATE
        FROM WORK_ORDER wo WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
        WHERE wo.BASE_ID LIKE ?
          AND wo.SUB_ID = '0'
        ORDER BY wo.CREATE_DATE DESC
    """

    logger.debug(f"Searching work orders: pattern={base_id_pattern}, limit={limit}")

    cursor.execute(query, (limit, base_id_pattern))
    rows = cursor.fetchall()

    work_orders = []
    for row in rows:
        wo = WorkOrder(
            base_id=row.BASE_ID.strip() if row.BASE_ID else '',
            lot_id=row.LOT_ID.strip() if row.LOT_ID else '',
            sub_id=row.SUB_ID.strip() if row.SUB_ID else '',
            part_id=row.PART_ID.strip() if row.PART_ID else '',
            part_description=row.part_description.strip() if row.part_description else None,
            order_qty=Decimal(str(row.DESIRED_QTY)) if row.DESIRED_QTY is not None else Decimal('0'),
            type=row.TYPE.strip() if row.TYPE else 'M',
            status=row.STATUS.strip() if row.STATUS else 'Unknown',
            start_date=row.SCHED_START_DATE if isinstance(row.SCHED_START_DATE, date) else None,
            complete_date=row.CLOSE_DATE if isinstance(row.CLOSE_DATE, date) else None,
            create_date=row.CREATE_DATE if isinstance(row.CREATE_DATE, datetime) else None,
        )
        work_orders.append(wo)

    logger.info(f"Found {len(work_orders)} work orders matching '{base_id_pattern}'")
    return work_orders


def get_work_order_header(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> Optional[WorkOrder]:
    """Get complete work order header with aggregate counts.

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID (empty string '' for main work order)

    Returns:
        WorkOrder object with aggregate counts, or None if not found

    Raises:
        ValueError: If base_id, lot_id, or sub_id is None
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("base_id, lot_id, and sub_id cannot be None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT wo.BASE_ID,
               wo.LOT_ID,
               wo.SUB_ID,
               wo.PART_ID,
               p.DESCRIPTION AS part_description,
               p.STOCK_UM,
               wo.TYPE AS work_order_type,
               wo.STATUS,
               wo.SCHED_START_DATE,
               wo.CLOSE_DATE,
               wo.DESIRED_QTY,
               wo.CREATE_DATE,
               wo.DESIRED_WANT_DATE,
               wo.SCHED_FINISH_DATE,
               wo.DESIRED_RLS_DATE,
               -- Cast bits column from WORKORDER_BINARY to get notes
               -- Convert image -> varbinary -> varchar (two-step conversion required for image type)
               CAST(CAST(wb.bits AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes,
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
        LEFT JOIN WORKORDER_BINARY wb WITH (NOLOCK)
            ON wo.BASE_ID = wb.WORKORDER_BASE_ID
            AND wo.LOT_ID = wb.WORKORDER_LOT_ID
            AND wo.SUB_ID = wb.WORKORDER_SUB_ID
        WHERE wo.BASE_ID = ?
          AND wo.LOT_ID = ?
          AND wo.SUB_ID = ?
    """

    logger.debug(f"Loading work order header: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id))
    row = cursor.fetchone()

    if not row:
        logger.warning(f"Work order not found: {base_id}/{lot_id}/{sub_id}")
        return None

    wo = WorkOrder(
        base_id=row.BASE_ID.strip() if row.BASE_ID else '',
        lot_id=row.LOT_ID.strip() if row.LOT_ID else '',
        sub_id=row.SUB_ID.strip() if row.SUB_ID else '',
        part_id=row.PART_ID.strip() if row.PART_ID else '',
        part_description=row.part_description.strip() if row.part_description else None,
        order_qty=Decimal(str(row.DESIRED_QTY)) if row.DESIRED_QTY is not None else Decimal('0'),
        type=row.work_order_type.strip() if row.work_order_type else 'M',
        status=row.STATUS.strip() if row.STATUS else 'Unknown',
        start_date=row.SCHED_START_DATE if isinstance(row.SCHED_START_DATE, (date, datetime)) else None,
        complete_date=row.CLOSE_DATE if isinstance(row.CLOSE_DATE, (date, datetime)) else None,
        create_date=row.CREATE_DATE if isinstance(row.CREATE_DATE, datetime) else None,
        desired_want_date=row.DESIRED_WANT_DATE if isinstance(row.DESIRED_WANT_DATE, (date, datetime)) else None,
        sched_finish_date=row.SCHED_FINISH_DATE if isinstance(row.SCHED_FINISH_DATE, (date, datetime)) else None,
        desired_rls_date=row.DESIRED_RLS_DATE if isinstance(row.DESIRED_RLS_DATE, (date, datetime)) else None,
        notes=row.notes.strip() if row.notes else None,
        operation_count=row.operation_count or 0,
        labor_ticket_count=row.labor_ticket_count or 0,
        inventory_trans_count=row.inventory_trans_count or 0,
    )

    logger.info(f"Loaded work order: {wo.formatted_id()} with {wo.operation_count} operations")
    return wo


def get_operations(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> List[Operation]:
    """Get all operations for a work order (lazy load).

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID

    Returns:
        List of Operation objects ordered by SEQUENCE

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key (base_id, lot_id, sub_id) cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT op.SEQUENCE_NO,
               op.OPERATION_TYPE,
               op.RESOURCE_ID,
               op.SETUP_HRS,
               op.RUN,
               op.RUN_TYPE,
               op.STATUS,
               op.CALC_START_QTY,
               op.CLOSE_DATE,
               CAST(CAST(ob.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes,
               -- Requirement count for this operation
               (SELECT COUNT(*) FROM REQUIREMENT WITH (NOLOCK)
                WHERE WORKORDER_BASE_ID = ?
                  AND WORKORDER_LOT_ID = ?
                  AND WORKORDER_SUB_ID = ?
                  AND OPERATION_SEQ_NO = op.SEQUENCE_NO) AS requirement_count
        FROM OPERATION op WITH (NOLOCK)
        LEFT JOIN OPERATION_BINARY ob WITH (NOLOCK)
            ON op.WORKORDER_BASE_ID = ob.WORKORDER_BASE_ID
            AND op.WORKORDER_LOT_ID = ob.WORKORDER_LOT_ID
            AND op.WORKORDER_SUB_ID = ob.WORKORDER_SUB_ID
            AND op.SEQUENCE_NO = ob.SEQUENCE_NO
        WHERE op.WORKORDER_BASE_ID = ?
          AND op.WORKORDER_LOT_ID = ?
          AND op.WORKORDER_SUB_ID = ?
        ORDER BY op.SEQUENCE_NO
    """

    logger.debug(f"Loading operations for: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id, base_id, lot_id, sub_id))
    rows = cursor.fetchall()

    operations = []
    for row in rows:
        op = Operation(
            workorder_base_id=base_id,
            workorder_lot_id=lot_id,
            workorder_sub_id=sub_id,
            sequence=row.SEQUENCE_NO,
            operation_type=row.OPERATION_TYPE.strip() if row.OPERATION_TYPE else '',
            operation_id=row.RESOURCE_ID.strip() if row.RESOURCE_ID else '',
            description=row.OPERATION_TYPE.strip() if row.OPERATION_TYPE else '',  # Use OPERATION_TYPE as description
            department_id=None,  # DEPARTMENT_ID doesn't exist in OPERATION table
            setup_hrs=Decimal(str(row.SETUP_HRS)) if row.SETUP_HRS is not None else Decimal('0'),
            run_hrs=Decimal(str(row.RUN)) if row.RUN is not None else Decimal('0'),
            run_type=row.RUN_TYPE.strip() if row.RUN_TYPE else 'HRS/PC',
            status=row.STATUS.strip() if row.STATUS else None,
            calc_start_qty=Decimal(str(row.CALC_START_QTY)) if row.CALC_START_QTY is not None else Decimal('0'),
            close_date=row.CLOSE_DATE if isinstance(row.CLOSE_DATE, (date, datetime)) else None,
            notes=row.notes.strip() if row.notes else None,
            requirement_count=row.requirement_count or 0,
        )
        operations.append(op)

    logger.info(f"Loaded {len(operations)} operations")
    return operations


def get_requirements(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str, operation_seq: int) -> List[Requirement]:
    """Get material requirements for a specific operation (lazy load).

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID
        operation_seq: Operation sequence number

    Returns:
        List of Requirement objects

    Raises:
        ValueError: If parameters are invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT r.PART_ID,
               p.DESCRIPTION AS part_description,
               p.STOCK_UM,
               r.QTY_PER,
               r.FIXED_QTY,
               r.SCRAP_PERCENT,
               r.PIECE_NO,
               r.OPERATION_SEQ_NO,
               r.SUBORD_WO_SUB_ID,
               wo.STATUS AS subord_wo_status,
               wo.DESIRED_QTY AS subord_wo_qty,
               wo.SCHED_START_DATE AS subord_wo_start_date,
               wo.SCHED_FINISH_DATE AS subord_wo_finish_date,
               CAST(CAST(rb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
        FROM REQUIREMENT r WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
        LEFT JOIN WORK_ORDER wo WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = wo.BASE_ID
            AND r.WORKORDER_LOT_ID = wo.LOT_ID
            AND r.SUBORD_WO_SUB_ID = wo.SUB_ID
        LEFT JOIN REQUIREMENT_BINARY rb WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = rb.WORKORDER_BASE_ID
            AND r.WORKORDER_LOT_ID = rb.WORKORDER_LOT_ID
            AND r.WORKORDER_SUB_ID = rb.WORKORDER_SUB_ID
            AND r.OPERATION_SEQ_NO = rb.OPERATION_SEQ_NO
            AND r.PIECE_NO = rb.PIECE_NO
        WHERE r.WORKORDER_BASE_ID = ?
          AND r.WORKORDER_LOT_ID = ?
          AND r.WORKORDER_SUB_ID = ?
          AND r.OPERATION_SEQ_NO = ?
        ORDER BY r.OPERATION_SEQ_NO, r.PART_ID
    """

    logger.debug(f"Loading requirements for operation {operation_seq}")

    cursor.execute(query, (base_id, lot_id, sub_id, operation_seq))
    rows = cursor.fetchall()

    requirements = []
    logger.info(f"")
    logger.info(f"DATABASE QUERY RESULTS for operation {operation_seq}:")
    logger.info(f"  Found {len(rows)} rows from database")

    for row in rows:
        part_display = row.PART_ID.strip() if row.PART_ID else 'NO_PART_ID'
        has_sub_wo = 'YES' if row.SUBORD_WO_SUB_ID else 'NO'
        logger.info(f"  - Part: {part_display}, Has SubWO: {has_sub_wo}, SubWO_SUB_ID: {row.SUBORD_WO_SUB_ID}")

        req = Requirement(
            workorder_base_id=base_id,
            workorder_lot_id=lot_id,
            workorder_sub_id=sub_id,
            operation_seq_no=row.OPERATION_SEQ_NO,
            part_id=row.PART_ID.strip() if row.PART_ID else '',
            part_description=row.part_description.strip() if row.part_description else None,
            part_type=None,  # TYPE column doesn't exist in PART table
            unit_of_measure=row.STOCK_UM.strip() if row.STOCK_UM else None,
            qty_per=Decimal(str(row.QTY_PER)) if row.QTY_PER is not None else Decimal('0'),
            fixed_qty=Decimal(str(row.FIXED_QTY)) if row.FIXED_QTY is not None else Decimal('0'),
            scrap_percent=Decimal(str(row.SCRAP_PERCENT)) if row.SCRAP_PERCENT is not None else Decimal('0'),
            piece_no=row.PIECE_NO if row.PIECE_NO else None,
            subord_wo_sub_id=row.SUBORD_WO_SUB_ID.strip() if row.SUBORD_WO_SUB_ID else None,
            subord_wo_status=row.subord_wo_status.strip() if row.subord_wo_status else None,
            subord_wo_qty=Decimal(str(row.subord_wo_qty)) if row.subord_wo_qty is not None else Decimal('0'),
            subord_wo_start_date=row.subord_wo_start_date if isinstance(row.subord_wo_start_date, (date, datetime)) else None,
            subord_wo_finish_date=row.subord_wo_finish_date if isinstance(row.subord_wo_finish_date, (date, datetime)) else None,
            notes=row.notes.strip() if row.notes else None,
        )
        requirements.append(req)

    logger.info(f"Loaded {len(requirements)} requirements")
    logger.info(f"")
    return requirements


def get_operation_children(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str, operation_seq: int) -> List[dict]:
    """Get flattened children for an operation (requirements AND child work order operations as siblings).

    This solves the hierarchy issue where child work order operations appeared nested under
    the requirement instead of as siblings. Returns a mixed list of requirements and child operations.

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID
        operation_seq: Operation sequence number

    Returns:
        List of dictionaries with 'item_type' = 'REQUIREMENT' or 'CHILD_OPERATION'

    Raises:
        ValueError: If parameters are invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        -- Requirements for this operation
        SELECT
            'REQUIREMENT' AS item_type,
            r.PART_ID AS item_id,
            COALESCE(p.DESCRIPTION, CAST(CAST(rb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX))) AS item_description,
            r.PIECE_NO AS sort_order_1,
            0 AS sort_order_2,
            r.QTY_PER,
            r.FIXED_QTY,
            r.SCRAP_PERCENT,
            r.CALC_QTY,
            r.STATUS AS req_status,
            r.ISSUED_QTY,
            r.REQUIRED_DATE,
            r.CLOSE_DATE AS req_close_date,
            r.OPERATION_SEQ_NO,
            r.SUBORD_WO_SUB_ID,
            wo.STATUS AS subord_wo_status,
            wo.DESIRED_QTY AS subord_wo_qty,
            wo.SCHED_START_DATE AS subord_wo_start_date,
            wo.SCHED_FINISH_DATE AS subord_wo_finish_date,
            NULL AS operation_type,
            NULL AS resource_id,
            NULL AS setup_hrs,
            NULL AS run,
            NULL AS run_type,
            NULL AS CALC_START_QTY,
            NULL AS operation_status,
            NULL AS operation_close_date,
            p.STOCK_UM,
            CAST(CAST(rb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
        FROM REQUIREMENT r WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
        LEFT JOIN WORK_ORDER wo WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = wo.BASE_ID
            AND r.WORKORDER_LOT_ID = wo.LOT_ID
            AND r.SUBORD_WO_SUB_ID = wo.SUB_ID
        LEFT JOIN REQUIREMENT_BINARY rb WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = rb.WORKORDER_BASE_ID
            AND r.WORKORDER_LOT_ID = rb.WORKORDER_LOT_ID
            AND r.WORKORDER_SUB_ID = rb.WORKORDER_SUB_ID
            AND r.OPERATION_SEQ_NO = rb.OPERATION_SEQ_NO
            AND r.PIECE_NO = rb.PIECE_NO
        WHERE r.WORKORDER_BASE_ID = ?
          AND r.WORKORDER_LOT_ID = ?
          AND r.WORKORDER_SUB_ID = ?
          AND r.OPERATION_SEQ_NO = ?

        UNION ALL

        -- Child work order operations (appear at same level as their parent requirement)
        SELECT
            'CHILD_OPERATION' AS item_type,
            CAST(op.SEQUENCE_NO AS VARCHAR) + ' ' + ISNULL(op.RESOURCE_ID, '') AS item_id,
            op.OPERATION_TYPE AS item_description,
            r.PIECE_NO AS sort_order_1,
            op.SEQUENCE_NO AS sort_order_2,
            NULL AS QTY_PER,
            NULL AS FIXED_QTY,
            NULL AS SCRAP_PERCENT,
            NULL AS CALC_QTY,
            NULL AS req_status,
            NULL AS ISSUED_QTY,
            NULL AS REQUIRED_DATE,
            NULL AS req_close_date,
            NULL AS OPERATION_SEQ_NO,
            r.SUBORD_WO_SUB_ID,
            NULL AS subord_wo_status,
            NULL AS subord_wo_qty,
            NULL AS subord_wo_start_date,
            NULL AS subord_wo_finish_date,
            op.OPERATION_TYPE,
            op.RESOURCE_ID,
            op.SETUP_HRS,
            op.RUN,
            op.RUN_TYPE,
            op.CALC_START_QTY,
            op.STATUS AS operation_status,
            op.CLOSE_DATE AS operation_close_date,
            NULL AS STOCK_UM,
            CAST(CAST(ob.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
        FROM REQUIREMENT r WITH (NOLOCK)
        INNER JOIN OPERATION op WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = op.WORKORDER_BASE_ID
            AND r.WORKORDER_LOT_ID = op.WORKORDER_LOT_ID
            AND r.SUBORD_WO_SUB_ID = op.WORKORDER_SUB_ID
        LEFT JOIN OPERATION_BINARY ob WITH (NOLOCK)
            ON op.WORKORDER_BASE_ID = ob.WORKORDER_BASE_ID
            AND op.WORKORDER_LOT_ID = ob.WORKORDER_LOT_ID
            AND op.WORKORDER_SUB_ID = ob.WORKORDER_SUB_ID
            AND op.SEQUENCE_NO = ob.SEQUENCE_NO
        WHERE r.WORKORDER_BASE_ID = ?
          AND r.WORKORDER_LOT_ID = ?
          AND r.WORKORDER_SUB_ID = ?
          AND r.OPERATION_SEQ_NO = ?
          AND r.SUBORD_WO_SUB_ID IS NOT NULL

        ORDER BY sort_order_1, sort_order_2
    """

    logger.debug(f"Loading flattened operation children for operation {operation_seq}")

    cursor.execute(query, (base_id, lot_id, sub_id, operation_seq,
                           base_id, lot_id, sub_id, operation_seq))
    rows = cursor.fetchall()

    results = []
    logger.info(f"")
    logger.info(f"FLATTENED QUERY RESULTS for operation {operation_seq}:")
    logger.info(f"  Found {len(rows)} items from database")

    for row in rows:
        item_type = row.item_type
        item_display = row.item_id.strip() if row.item_id else 'NO_ID'
        logger.info(f"  - Type: {item_type}, ID: {item_display}")

        results.append({
            'item_type': item_type,
            'item_id': row.item_id.strip() if row.item_id else '',
            'item_description': row.item_description.strip() if row.item_description else '',
            'piece_no': row.sort_order_1 if row.sort_order_1 else None,
            'qty_per': Decimal(str(row.QTY_PER)) if row.QTY_PER is not None else Decimal('0'),
            'fixed_qty': Decimal(str(row.FIXED_QTY)) if row.FIXED_QTY is not None else Decimal('0'),
            'scrap_percent': Decimal(str(row.SCRAP_PERCENT)) if row.SCRAP_PERCENT is not None else Decimal('0'),
            'calc_qty': Decimal(str(row.CALC_QTY)) if row.CALC_QTY is not None else Decimal('0'),
            'req_status': row.req_status.strip() if row.req_status else None,
            'issued_qty': Decimal(str(row.ISSUED_QTY)) if row.ISSUED_QTY is not None else Decimal('0'),
            'required_date': row.REQUIRED_DATE if isinstance(row.REQUIRED_DATE, (date, datetime)) else None,
            'req_close_date': row.req_close_date if isinstance(row.req_close_date, (date, datetime)) else None,
            'operation_seq_no': row.OPERATION_SEQ_NO,
            'subord_wo_sub_id': row.SUBORD_WO_SUB_ID.strip() if row.SUBORD_WO_SUB_ID else None,
            'subord_wo_status': row.subord_wo_status.strip() if row.subord_wo_status else None,
            'subord_wo_qty': Decimal(str(row.subord_wo_qty)) if row.subord_wo_qty is not None else Decimal('0'),
            'subord_wo_start_date': row.subord_wo_start_date if isinstance(row.subord_wo_start_date, (date, datetime)) else None,
            'subord_wo_finish_date': row.subord_wo_finish_date if isinstance(row.subord_wo_finish_date, (date, datetime)) else None,
            'operation_type': row.operation_type.strip() if row.operation_type else None,
            'resource_id': row.resource_id.strip() if row.resource_id else None,
            'setup_hrs': Decimal(str(row.setup_hrs)) if row.setup_hrs is not None else Decimal('0'),
            'run_hrs': Decimal(str(row.run)) if row.run is not None else Decimal('0'),
            'run_type': row.run_type.strip() if row.run_type else 'HRS/PC',
            'calc_start_qty': Decimal(str(row.CALC_START_QTY)) if row.CALC_START_QTY is not None else Decimal('0'),
            'operation_status': row.operation_status.strip() if row.operation_status else None,
            'operation_close_date': row.operation_close_date if isinstance(row.operation_close_date, (date, datetime)) else None,
            'unit_of_measure': row.STOCK_UM.strip() if row.STOCK_UM else None,
            'notes': row.notes.strip() if row.notes else None,
        })

    logger.info(f"Loaded {len(results)} flattened children (requirements + child operations)")
    logger.info(f"")
    return results


def get_requirements_by_sub_id(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> List[Requirement]:
    """Get all requirements for a work order by WORKORDER_SUB_ID (for tree building).

    This queries requirements where WORKORDER_SUB_ID matches the given sub_id,
    which determines the tree hierarchy:
    - sub_id='0': Top-level requirements under main work order
    - sub_id='346': Requirements under sub-work-order 8113-346/26

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID (determines which level of the tree)

    Returns:
        List of Requirement objects (both parts and sub-work-orders)

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT r.PART_ID,
               p.DESCRIPTION AS part_description,
               p.STOCK_UM,
               r.QTY_PER,
               r.FIXED_QTY,
               r.SCRAP_PERCENT,
               r.PIECE_NO,
               r.OPERATION_SEQ_NO,
               r.SUBORD_WO_SUB_ID,
               wo.STATUS AS subord_wo_status,
               wo.DESIRED_QTY AS subord_wo_qty,
               wo.SCHED_START_DATE AS subord_wo_start_date,
               wo.SCHED_FINISH_DATE AS subord_wo_finish_date,
               CAST(CAST(rb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
        FROM REQUIREMENT r WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
        LEFT JOIN WORK_ORDER wo WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = wo.BASE_ID
            AND r.WORKORDER_LOT_ID = wo.LOT_ID
            AND r.SUBORD_WO_SUB_ID = wo.SUB_ID
        LEFT JOIN REQUIREMENT_BINARY rb WITH (NOLOCK)
            ON r.WORKORDER_BASE_ID = rb.WORKORDER_BASE_ID
            AND r.WORKORDER_LOT_ID = rb.WORKORDER_LOT_ID
            AND r.WORKORDER_SUB_ID = rb.WORKORDER_SUB_ID
            AND r.OPERATION_SEQ_NO = rb.OPERATION_SEQ_NO
            AND r.PIECE_NO = rb.PIECE_NO
        WHERE r.WORKORDER_BASE_ID = ?
          AND r.WORKORDER_LOT_ID = ?
          AND r.WORKORDER_SUB_ID = ?
        ORDER BY r.OPERATION_SEQ_NO, r.PIECE_NO, r.PART_ID
    """

    logger.debug(f"Loading requirements by SUB_ID: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id))
    rows = cursor.fetchall()

    requirements = []
    for row in rows:
        req = Requirement(
            workorder_base_id=base_id,
            workorder_lot_id=lot_id,
            workorder_sub_id=sub_id,
            operation_seq_no=row.OPERATION_SEQ_NO,
            part_id=row.PART_ID.strip() if row.PART_ID else '',
            part_description=row.part_description.strip() if row.part_description else None,
            part_type=None,  # TYPE column doesn't exist in PART table
            unit_of_measure=row.STOCK_UM.strip() if row.STOCK_UM else None,
            qty_per=Decimal(str(row.QTY_PER)) if row.QTY_PER is not None else Decimal('0'),
            fixed_qty=Decimal(str(row.FIXED_QTY)) if row.FIXED_QTY is not None else Decimal('0'),
            scrap_percent=Decimal(str(row.SCRAP_PERCENT)) if row.SCRAP_PERCENT is not None else Decimal('0'),
            piece_no=row.PIECE_NO if row.PIECE_NO else None,
            subord_wo_sub_id=row.SUBORD_WO_SUB_ID.strip() if row.SUBORD_WO_SUB_ID else None,
            subord_wo_status=row.subord_wo_status.strip() if row.subord_wo_status else None,
            subord_wo_qty=Decimal(str(row.subord_wo_qty)) if row.subord_wo_qty is not None else Decimal('0'),
            subord_wo_start_date=row.subord_wo_start_date if isinstance(row.subord_wo_start_date, (date, datetime)) else None,
            subord_wo_finish_date=row.subord_wo_finish_date if isinstance(row.subord_wo_finish_date, (date, datetime)) else None,
            notes=row.notes.strip() if row.notes else None,
        )
        requirements.append(req)

    logger.info(f"Loaded {len(requirements)} requirements for SUB_ID={sub_id}")
    return requirements


def get_labor_tickets(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> List[LaborTicket]:
    """Get all labor transactions for a work order (lazy load).

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID

    Returns:
        List of LaborTicket objects ordered by LABOR_DATE DESC

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT EMPLOYEE_ID,
               OPERATION_SEQ_NO,
               TRANSACTION_DATE,
               HOURS_WORKED,
               HOURLY_COST,
               (HOURS_WORKED * HOURLY_COST) AS total_cost,
               DESCRIPTION
        FROM LABOR_TICKET WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = ?
          AND WORKORDER_LOT_ID = ?
          AND WORKORDER_SUB_ID = ?
        ORDER BY TRANSACTION_DATE DESC
    """

    logger.debug(f"Loading labor tickets for: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id))
    rows = cursor.fetchall()

    labor_tickets = []
    for row in rows:
        ticket = LaborTicket(
            workorder_base_id=base_id,
            workorder_lot_id=lot_id,
            workorder_sub_id=sub_id,
            employee_id=row.EMPLOYEE_ID.strip() if row.EMPLOYEE_ID else '',
            operation_seq=row.OPERATION_SEQ_NO if row.OPERATION_SEQ_NO else None,
            labor_date=row.TRANSACTION_DATE if isinstance(row.TRANSACTION_DATE, (date, datetime)) else None,
            setup_hrs=Decimal('0'),  # SETUP_HRS doesn't exist in LABOR_TICKET table
            run_hrs=Decimal('0'),  # RUN_HRS doesn't exist in LABOR_TICKET table
            total_hrs=Decimal(str(row.HOURS_WORKED)) if row.HOURS_WORKED is not None else Decimal('0'),
            labor_rate=Decimal(str(row.HOURLY_COST)) if row.HOURLY_COST is not None else Decimal('0'),
            total_cost=Decimal(str(row.total_cost)) if row.total_cost is not None else Decimal('0'),
        )
        labor_tickets.append(ticket)

    logger.info(f"Loaded {len(labor_tickets)} labor tickets")
    return labor_tickets


def get_inventory_transactions(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> List[InventoryTransaction]:
    """Get all material transactions for a work order (lazy load).

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID

    Returns:
        List of InventoryTransaction objects ordered by TRANS_DATE DESC

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT it.PART_ID,
               p.DESCRIPTION AS part_description,
               it.TYPE,
               it.QTY,
               it.TRANSACTION_DATE,
               it.LOCATION_ID
        FROM INVENTORY_TRANS it WITH (NOLOCK)
        LEFT JOIN PART p WITH (NOLOCK) ON it.PART_ID = p.ID
        WHERE it.WORKORDER_BASE_ID = ?
          AND it.WORKORDER_LOT_ID = ?
          AND it.WORKORDER_SUB_ID = ?
          AND it.WORKORDER_BASE_ID IS NOT NULL
        ORDER BY it.TRANSACTION_DATE DESC
    """

    logger.debug(f"Loading inventory transactions for: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id))
    rows = cursor.fetchall()

    transactions = []
    for row in rows:
        trans = InventoryTransaction(
            workorder_base_id=base_id,
            workorder_lot_id=lot_id,
            workorder_sub_id=sub_id,
            part_id=row.PART_ID.strip() if row.PART_ID else '',
            part_description=row.part_description.strip() if row.part_description else None,
            trans_type=row.TYPE.strip() if row.TYPE else '',
            quantity=Decimal(str(row.QTY)) if row.QTY is not None else Decimal('0'),
            trans_date=row.TRANSACTION_DATE if isinstance(row.TRANSACTION_DATE, datetime) else None,
            location_id=row.LOCATION_ID.strip() if row.LOCATION_ID else None,
            lot_serial_no=None,  # LOT_SERIAL_NO column doesn't exist in INVENTORY_TRANS
        )
        transactions.append(trans)

    logger.info(f"Loaded {len(transactions)} inventory transactions")
    return transactions


def get_wip_balance(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str) -> Optional[WIPBalance]:
    """Get WIP cost accumulation for a work order (lazy load).

    Args:
        cursor: Database cursor
        base_id: Work order BASE_ID
        lot_id: Work order LOT_ID
        sub_id: Work order SUB_ID

    Returns:
        WIPBalance object or None if not found

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    query = """
        SELECT MATERIAL_AMOUNT,
               LABOR_AMOUNT,
               BURDEN_AMOUNT,
               (MATERIAL_AMOUNT + LABOR_AMOUNT + BURDEN_AMOUNT) AS total_cost,
               POSTING_DATE
        FROM WIP_BALANCE WITH (NOLOCK)
        WHERE WORKORDER_BASE_ID = ?
          AND WORKORDER_LOT_ID = ?
          AND WORKORDER_SUB_ID = ?
    """

    logger.debug(f"Loading WIP balance for: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id))
    row = cursor.fetchone()

    if not row:
        logger.info(f"No WIP balance found for: {base_id}/{lot_id}/{sub_id}")
        return None

    wip = WIPBalance(
        workorder_base_id=base_id,
        workorder_lot_id=lot_id,
        workorder_sub_id=sub_id,
        material_cost=Decimal(str(row.MATERIAL_AMOUNT)) if row.MATERIAL_AMOUNT is not None else Decimal('0'),
        labor_cost=Decimal(str(row.LABOR_AMOUNT)) if row.LABOR_AMOUNT is not None else Decimal('0'),
        burden_cost=Decimal(str(row.BURDEN_AMOUNT)) if row.BURDEN_AMOUNT is not None else Decimal('0'),
        total_cost=Decimal(str(row.total_cost)) if row.total_cost is not None else Decimal('0'),
        last_updated=row.POSTING_DATE if isinstance(row.POSTING_DATE, datetime) else None,
    )

    logger.info(f"Loaded WIP balance: {wip.formatted_total()}")
    return wip


def get_work_order_hierarchy(cursor: pyodbc.Cursor, base_id: str, lot_id: str, sub_id: str, max_depth: int = 10) -> List[WorkOrder]:
    """Get hierarchical work order tree using recursive CTE for SUBORD_WO_SUB_ID relationships.

    This query traverses parent-child work order relationships where a requirement's
    SUBORD_WO_SUB_ID points to a child work order that fulfills that requirement.

    Args:
        cursor: Database cursor
        base_id: Root work order BASE_ID
        lot_id: Root work order LOT_ID
        sub_id: Root work order SUB_ID
        max_depth: Maximum recursion depth (default 10, prevents infinite loops)

    Returns:
        List of WorkOrder objects in hierarchical order (parent before children)

    Raises:
        ValueError: If composite key is invalid
        pyodbc.Error: If database query fails
    """
    if base_id is None or lot_id is None or sub_id is None:
        raise ValueError("Composite key cannot contain None")

    base_id = base_id.strip().upper()
    lot_id = lot_id.strip().upper()
    sub_id = sub_id.strip().upper()

    # Recursive CTE to traverse work order hierarchy via SUBORD_WO_SUB_ID
    query = """
        WITH WorkOrderHierarchy AS (
            -- Anchor: Start with main work order
            SELECT wo.BASE_ID,
                   wo.LOT_ID,
                   wo.SUB_ID,
                   wo.PART_ID,
                   p.DESCRIPTION AS part_description,
                   wo.TYPE,
                   wo.STATUS,
                   wo.ORDER_QTY,
                   wo.CREATE_DATE,
                   0 AS depth,
                   CAST(wo.BASE_ID + '/' + wo.LOT_ID + '/' + wo.SUB_ID AS VARCHAR(500)) AS path
            FROM WORK_ORDER wo WITH (NOLOCK)
            LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
            WHERE wo.BASE_ID = ?
              AND wo.LOT_ID = ?
              AND wo.SUB_ID = ?

            UNION ALL

            -- Recursive: Find child work orders through SUBORD_WO_SUB_ID
            SELECT wo.BASE_ID,
                   wo.LOT_ID,
                   wo.SUB_ID,
                   wo.PART_ID,
                   p.DESCRIPTION AS part_description,
                   wo.TYPE,
                   wo.STATUS,
                   wo.ORDER_QTY,
                   wo.CREATE_DATE,
                   woh.depth + 1,
                   CAST(woh.path + ' -> ' + wo.BASE_ID + '/' + wo.LOT_ID + '/' + wo.SUB_ID AS VARCHAR(500))
            FROM WORK_ORDER wo WITH (NOLOCK)
            LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
            INNER JOIN REQUIREMENT req WITH (NOLOCK)
                ON req.SUBORD_WO_SUB_ID = wo.SUB_ID
                   AND req.WORKORDER_BASE_ID = wo.BASE_ID
                   AND req.WORKORDER_LOT_ID = wo.LOT_ID
            INNER JOIN WorkOrderHierarchy woh
                ON req.WORKORDER_BASE_ID = woh.BASE_ID
                   AND req.WORKORDER_LOT_ID = woh.LOT_ID
                   AND req.WORKORDER_SUB_ID = woh.SUB_ID
            WHERE woh.depth < ?
              AND woh.path NOT LIKE '%' + wo.BASE_ID + '/' + wo.LOT_ID + '/' + wo.SUB_ID + '%'  -- Prevent circular refs
        )
        SELECT BASE_ID, LOT_ID, SUB_ID, PART_ID, part_description, TYPE, STATUS, ORDER_QTY, CREATE_DATE, depth, path
        FROM WorkOrderHierarchy
        ORDER BY path
    """

    logger.debug(f"Loading work order hierarchy from: {base_id}/{lot_id}/{sub_id}")

    cursor.execute(query, (base_id, lot_id, sub_id, max_depth))
    rows = cursor.fetchall()

    work_orders = []
    for row in rows:
        wo = WorkOrder(
            base_id=row.BASE_ID.strip() if row.BASE_ID else '',
            lot_id=row.LOT_ID.strip() if row.LOT_ID else '',
            sub_id=row.SUB_ID.strip() if row.SUB_ID else '',
            part_id=row.PART_ID.strip() if row.PART_ID else '',
            part_description=row.part_description.strip() if row.part_description else None,
            order_qty=Decimal(str(row.ORDER_QTY)) if row.ORDER_QTY is not None else Decimal('0'),
            type=row.TYPE.strip() if row.TYPE else 'M',
            status=row.STATUS.strip() if row.STATUS else 'Unknown',
            create_date=row.CREATE_DATE if isinstance(row.CREATE_DATE, datetime) else None,
        )
        work_orders.append(wo)

    logger.info(f"Loaded {len(work_orders)} work orders in hierarchy (max depth: {max_depth})")
    return work_orders
