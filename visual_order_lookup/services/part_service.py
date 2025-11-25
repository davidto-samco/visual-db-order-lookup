"""Part service for Inventory module.

Provides part lookup, where-used analysis, and purchase history queries.
"""

import logging
from typing import List, Optional
from decimal import Decimal
from datetime import date

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database.models import Part, WhereUsed, PurchaseHistory
from visual_order_lookup.database import part_queries


logger = logging.getLogger(__name__)


class PartService:
    """Service for part-related database operations.

    Provides read-only access to part master data, usage history, and
    purchase history from the Visual database.
    """

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize part service with database connection.

        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection

    def search_by_part_number(self, part_number: str) -> Optional[Part]:
        """Search for a part by exact part number match.

        Args:
            part_number: Exact part number to search for (case-insensitive)

        Returns:
            Part object if found, None if not found

        Raises:
            Exception: If database error occurs
        """
        # Validate and normalize input
        if not part_number or not part_number.strip():
            raise ValueError("Part number cannot be empty")

        part_number = part_number.strip().upper()

        if len(part_number) > 30:
            raise ValueError("Part number cannot exceed 30 characters")

        logger.info(f"Searching for part: {part_number}")

        # SQL query from contract
        query = """
            SELECT p.ID, p.DESCRIPTION, p.STOCK_UM, p.UNIT_MATERIAL_COST,
                   p.UNIT_LABOR_COST, p.UNIT_BURDEN_COST, p.UNIT_PRICE,
                   p.MATERIAL_CODE, p.QTY_ON_HAND, p.QTY_AVAILABLE_ISS,
                   p.QTY_ON_ORDER, p.QTY_IN_DEMAND, p.DRAWING_ID, p.DRAWING_REV_NO,
                   p.PREF_VENDOR_ID, p.PURCHASED, p.FABRICATED, p.STOCKED,
                   p.WEIGHT, p.WEIGHT_UM, v.NAME AS vendor_name
            FROM PART p WITH (NOLOCK)
            LEFT JOIN VENDOR v WITH (NOLOCK) ON p.PREF_VENDOR_ID = v.ID
            WHERE p.ID = ?
        """

        try:
            with self.db_connection.get_cursor() as cursor:
                cursor.execute(query, (part_number,))
                row = cursor.fetchone()

                if not row:
                    logger.info(f"Part not found: {part_number}")
                    return None

                # Map row to Part object
                part = Part(
                    part_id=row.ID,
                    part_number=row.ID,  # Part number is same as ID
                    description=row.DESCRIPTION or "",
                    extended_description=None,  # TODO: Load from PART_BINARY if needed
                    unit_of_measure=row.STOCK_UM or "",
                    unit_material_cost=Decimal(row.UNIT_MATERIAL_COST) if row.UNIT_MATERIAL_COST else None,
                    unit_labor_cost=Decimal(row.UNIT_LABOR_COST) if row.UNIT_LABOR_COST else None,
                    unit_burden_cost=Decimal(row.UNIT_BURDEN_COST) if row.UNIT_BURDEN_COST else None,
                    unit_price=Decimal(row.UNIT_PRICE) if row.UNIT_PRICE else None,
                    material_code=row.MATERIAL_CODE,
                    qty_on_hand=Decimal(row.QTY_ON_HAND) if row.QTY_ON_HAND else None,
                    qty_available=Decimal(row.QTY_AVAILABLE_ISS) if row.QTY_AVAILABLE_ISS else None,
                    qty_on_order=Decimal(row.QTY_ON_ORDER) if row.QTY_ON_ORDER else None,
                    qty_in_demand=Decimal(row.QTY_IN_DEMAND) if row.QTY_IN_DEMAND else None,
                    drawing_id=row.DRAWING_ID,
                    drawing_revision=row.DRAWING_REV_NO,
                    vendor_id=row.PREF_VENDOR_ID,
                    vendor_name=row.vendor_name,
                    is_purchased=(row.PURCHASED == 'Y'),
                    is_fabricated=(row.FABRICATED == 'Y'),
                    is_stocked=(row.STOCKED == 'Y'),
                    weight=Decimal(row.WEIGHT) if row.WEIGHT else None,
                    weight_um=row.WEIGHT_UM,
                )

                logger.info(f"Found part: {part.part_number} - {part.description}")
                return part

        except Exception as e:
            logger.error(f"Error searching for part {part_number}: {e}")
            raise

    def get_where_used(self, part_number: str) -> List[WhereUsed]:
        """Retrieve BOM where-used records for a specific part.

        Shows where the part is used in work orders/assemblies based on BOM structure.
        Replaces previous inventory transaction history with REQUIREMENT table data.

        Args:
            part_number: Part number to query BOM usage for

        Returns:
            List of WhereUsed records ordered by work_order_master and seq_no.
            Empty list if no BOM usage records found.

        Raises:
            Exception: If database error occurs
        """
        # Validate and normalize input
        if not part_number or not part_number.strip():
            raise ValueError("Part number cannot be empty")

        part_number = part_number.strip().upper()

        if len(part_number) > 30:
            raise ValueError("Part number cannot exceed 30 characters")

        logger.info(f"Fetching BOM where-used for part: {part_number}")

        try:
            cursor = self.db_connection.get_cursor()
            records = part_queries.get_part_bom_usage(cursor, part_number)
            cursor.close()

            logger.info(f"Found {len(records)} BOM where-used records for part {part_number}")
            return records

        except Exception as e:
            logger.error(f"Error fetching BOM where-used for part {part_number}: {e}")
            raise

    def get_purchase_history(self, part_number: str, limit: int = 100) -> List[PurchaseHistory]:
        """Retrieve purchase order history for a specific part.

        Shows all PO lines where this part was ordered with vendor info, quantities, and prices.

        Args:
            part_number: Part number to query purchase history for
            limit: Maximum number of purchase records to return (1-1000, default 100)

        Returns:
            List of PurchaseHistory records ordered by order_date descending.
            Empty list if no purchase history found.

        Raises:
            Exception: If database error occurs
        """
        # Validate and normalize input
        if not part_number or not part_number.strip():
            raise ValueError("Part number cannot be empty")

        part_number = part_number.strip().upper()

        if len(part_number) > 30:
            raise ValueError("Part number cannot exceed 30 characters")

        if not 1 <= limit <= 1000:
            raise ValueError("Limit must be between 1 and 1000")

        logger.info(f"Fetching purchase history for part: {part_number} (limit: {limit})")

        # SQL query from contract with additional fields from purchase history enhancement
        query = f"""
            SELECT TOP ({limit})
                   pol.PART_ID, po.ID AS po_number, pol.LINE_NO,
                   po.ORDER_DATE, v.NAME AS vendor_name, v.ID AS vendor_id,
                   pol.VENDOR_PART_ID, pol.USER_ORDER_QTY AS quantity,
                   pol.UNIT_PRICE, pol.TOTAL_AMT_ORDERED AS line_total,
                   pol.DESIRED_RECV_DATE, pol.LAST_RECEIVED_DATE,
                   po.CURRENCY_ID AS currency,
                   pol.TRADE_DISC_PERCENT AS disc_percent,
                   p.WHSALE_UNIT_COST AS standard_unit_cost
            FROM PURC_ORDER_LINE pol WITH (NOLOCK)
            INNER JOIN PURCHASE_ORDER po WITH (NOLOCK) ON pol.PURC_ORDER_ID = po.ID
            INNER JOIN VENDOR v WITH (NOLOCK) ON po.VENDOR_ID = v.ID
            LEFT JOIN PART p WITH (NOLOCK) ON pol.PART_ID = p.ID
            WHERE pol.PART_ID = ?
            ORDER BY po.ORDER_DATE DESC
        """

        try:
            with self.db_connection.get_cursor() as cursor:
                cursor.execute(query, (part_number,))
                rows = cursor.fetchall()

                purchase_records = []
                for row in rows:
                    purchase = PurchaseHistory(
                        part_number=row.PART_ID,
                        po_number=row.po_number,
                        line_number=row.LINE_NO,
                        order_date=row.ORDER_DATE,
                        vendor_name=row.vendor_name or "",
                        vendor_id=row.vendor_id or "",
                        vendor_part_id=row.VENDOR_PART_ID,
                        quantity=Decimal(row.quantity) if row.quantity else Decimal('0'),
                        unit_price=Decimal(row.UNIT_PRICE) if row.UNIT_PRICE else Decimal('0'),
                        line_total=Decimal(row.line_total) if row.line_total else Decimal('0'),
                        desired_receive_date=row.DESIRED_RECV_DATE,
                        last_received_date=row.LAST_RECEIVED_DATE,
                        # Enhanced fields from database
                        currency=row.currency,
                        native_currency=None,  # Not available in Visual database
                        native_unit_price=None,  # Not available in Visual database
                        disc_percent=Decimal(str(row.disc_percent)) if row.disc_percent is not None else None,
                        fixed_disc=None,  # Not available in Visual database
                        standard_unit_cost=Decimal(str(row.standard_unit_cost)) if row.standard_unit_cost is not None else None,
                    )
                    purchase_records.append(purchase)

                logger.info(f"Found {len(purchase_records)} purchase history records for part {part_number}")
                return purchase_records

        except Exception as e:
            logger.error(f"Error fetching purchase history for part {part_number}: {e}")
            raise
