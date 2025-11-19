"""SQL query definitions for part/inventory operations in Visual database."""

import logging
from typing import List
from decimal import Decimal
import pyodbc
from visual_order_lookup.database.models import WhereUsed


logger = logging.getLogger(__name__)


def get_part_bom_usage(cursor: pyodbc.Cursor, part_number: str) -> List[WhereUsed]:
    """Retrieve BOM structure records for a part.

    Queries the REQUIREMENT table (BOM detail) joined with WORK_ORDER table
    (BOM master) to find all places where a part is used in work orders/assemblies.

    Args:
        cursor: Database cursor
        part_number: Part ID to search for

    Returns:
        List of WhereUsed objects (BOM records), ordered by work order and sequence.
        Returns empty list [] if part has no BOM usage.

    Raises:
        ValueError: If part_number is empty
        Exception: If database query fails
    """
    if not part_number or not part_number.strip():
        raise ValueError("Part number cannot be empty")

    query = """
        SELECT
            wo.PART_ID AS manufactured_part_id,
            p.DESCRIPTION AS manufactured_part_description,
            wo.BASE_ID AS work_order_master,
            wo.SUB_ID AS work_order_sub_id,
            wo.LOT_ID AS work_order_lot_id,
            wo.TYPE AS work_order_type,
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
        LEFT JOIN PART p WITH (NOLOCK)
            ON wo.PART_ID = p.ID
        WHERE r.PART_ID = ?
        ORDER BY wo.BASE_ID, r.OPERATION_SEQ_NO
    """

    try:
        cursor.execute(query, (part_number.strip(),))
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append(WhereUsed(
                part_number=part_number,
                manufactured_part_id=row.manufactured_part_id.strip() if row.manufactured_part_id else None,
                manufactured_part_description=row.manufactured_part_description.strip() if row.manufactured_part_description else None,
                work_order_master=row.work_order_master.strip() if row.work_order_master else "",
                work_order_sub_id=row.work_order_sub_id.strip() if row.work_order_sub_id else "",
                work_order_lot_id=row.work_order_lot_id.strip() if row.work_order_lot_id else "",
                work_order_type=row.work_order_type.strip() if row.work_order_type else None,
                seq_no=row.seq_no if row.seq_no is not None else 0,
                piece_no=row.piece_no if row.piece_no is not None else 0,
                qty_per=Decimal(str(row.qty_per)) if row.qty_per is not None else Decimal("0"),
                fixed_qty=Decimal(str(row.fixed_qty)) if row.fixed_qty is not None else Decimal("0"),
                scrap_percent=Decimal(str(row.scrap_percent)) if row.scrap_percent is not None else Decimal("0"),
            ))

        logger.info(f"Retrieved {len(records)} BOM records for part {part_number}")
        return records

    except pyodbc.Error as e:
        logger.error(f"Database error retrieving BOM for part {part_number}: {e}")
        raise Exception(f"Failed to retrieve BOM data: {str(e)}")
