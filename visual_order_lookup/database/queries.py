"""SQL query definitions for Visual database access."""

import pyodbc
import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional
from visual_order_lookup.database.models import (
    OrderSummary,
    OrderHeader,
    OrderLineItem,
    Customer,
)


logger = logging.getLogger(__name__)


def get_recent_orders(cursor: pyodbc.Cursor, limit: int = 100) -> List[OrderSummary]:
    """
    Retrieve most recent orders sorted by date descending.

    Args:
        cursor: Database cursor
        limit: Maximum number of orders to return (default: 100)

    Returns:
        List of OrderSummary objects

    Raises:
        pyodbc.Error: If query fails
    """
    query = """
        SELECT TOP (?)
            co.ID AS job_number,
            c.NAME AS customer_name,
            co.ORDER_DATE AS order_date,
            co.TOTAL_AMT_ORDERED AS total_amount,
            co.CUSTOMER_PO_REF AS customer_po
        FROM CUSTOMER_ORDER co WITH (NOLOCK)
        INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
        ORDER BY co.ORDER_DATE DESC
    """

    try:
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append(
                OrderSummary(
                    job_number=row.job_number.strip() if row.job_number else "",
                    customer_name=row.customer_name.strip() if row.customer_name else "",
                    order_date=row.order_date.date() if hasattr(row.order_date, 'date') else row.order_date,
                    total_amount=Decimal(str(row.total_amount)) if row.total_amount else Decimal("0.00"),
                    customer_po=row.customer_po.strip() if row.customer_po else None,
                )
            )

        logger.info(f"Retrieved {len(orders)} recent orders")
        return orders

    except pyodbc.Error as e:
        logger.error(f"Error retrieving recent orders: {e}")
        raise


def filter_orders_by_date_range(
    cursor: pyodbc.Cursor,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 1000,
) -> List[OrderSummary]:
    """
    Filter orders by date range.

    Args:
        cursor: Database cursor
        start_date: Start date for filter (inclusive)
        end_date: End date for filter (inclusive)
        limit: Maximum number of orders to return (default: 1000)

    Returns:
        List of OrderSummary objects

    Raises:
        pyodbc.Error: If query fails
    """
    query = """
        SELECT TOP (?)
            co.ID AS job_number,
            c.NAME AS customer_name,
            co.ORDER_DATE AS order_date,
            co.TOTAL_AMT_ORDERED AS total_amount,
            co.CUSTOMER_PO_REF AS customer_po
        FROM CUSTOMER_ORDER co WITH (NOLOCK)
        INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
        WHERE 1=1
    """

    params = [limit]

    if start_date:
        query += " AND co.ORDER_DATE >= ?"
        params.append(start_date)

    if end_date:
        query += " AND co.ORDER_DATE <= ?"
        params.append(end_date)

    query += " ORDER BY co.ORDER_DATE DESC"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append(
                OrderSummary(
                    job_number=row.job_number.strip() if row.job_number else "",
                    customer_name=row.customer_name.strip() if row.customer_name else "",
                    order_date=row.order_date.date() if hasattr(row.order_date, 'date') else row.order_date,
                    total_amount=Decimal(str(row.total_amount)) if row.total_amount else Decimal("0.00"),
                    customer_po=row.customer_po.strip() if row.customer_po else None,
                )
            )

        logger.info(f"Retrieved {len(orders)} orders in date range")
        return orders

    except pyodbc.Error as e:
        logger.error(f"Error filtering orders by date range: {e}")
        raise


def search_by_job_number(cursor: pyodbc.Cursor, job_number: str) -> Optional[OrderHeader]:
    """
    Search for order by exact job number match.

    Args:
        cursor: Database cursor
        job_number: Job number to search for

    Returns:
        OrderHeader object with customer and line items, or None if not found

    Raises:
        pyodbc.Error: If query fails
    """
    query = """
        SELECT
            co.ID AS order_id,
            co.ORDER_DATE AS order_date,
            co.CUSTOMER_PO_REF AS customer_po_ref,
            co.CONTACT_FIRST_NAME AS contact_first_name,
            co.CONTACT_LAST_NAME AS contact_last_name,
            co.CONTACT_PHONE AS contact_phone,
            co.CONTACT_FAX AS contact_fax,
            co.PROMISE_DATE AS promise_date,
            co.TOTAL_AMT_ORDERED AS total_amount,
            co.CURRENCY_ID AS currency_id,
            co.TERMS_DESCRIPTION AS terms_description,
            co.SALESREP_ID AS sales_rep_id,
            sr.NAME AS sales_rep_name,
            co.DESIRED_SHIP_DATE AS desired_ship_date,
            qo.QUOTE_ID AS quote_id,
            c.ID AS customer_id,
            c.NAME AS customer_name,
            c.ADDR_1 AS address_1,
            c.ADDR_2 AS address_2,
            c.CITY AS city,
            c.STATE AS state,
            c.ZIPCODE AS zip_code,
            c.COUNTRY AS country,
            c.BILL_TO_NAME AS bill_to_name,
            c.BILL_TO_ADDR_1 AS bill_to_address_1,
            c.BILL_TO_ADDR_2 AS bill_to_address_2,
            c.BILL_TO_ADDR_3 AS bill_to_address_3,
            c.BILL_TO_CITY AS bill_to_city,
            c.BILL_TO_STATE AS bill_to_state,
            c.BILL_TO_ZIPCODE AS bill_to_zip_code,
            c.BILL_TO_COUNTRY AS bill_to_country
        FROM CUSTOMER_ORDER co WITH (NOLOCK)
        INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
        LEFT JOIN QUOTE_ORDER qo WITH (NOLOCK) ON co.ID = qo.CUST_ORDER_ID
        LEFT JOIN SALES_REP sr WITH (NOLOCK) ON co.SALESREP_ID = sr.ID
        WHERE co.ID = ?
    """

    try:
        cursor.execute(query, (job_number,))
        row = cursor.fetchone()

        if not row:
            logger.info(f"No order found for job number: {job_number}")
            return None

        # Create customer object
        customer = Customer(
            customer_id=row.customer_id.strip() if row.customer_id else "",
            name=row.customer_name.strip() if row.customer_name else "",
            address_1=row.address_1.strip() if row.address_1 else None,
            address_2=row.address_2.strip() if row.address_2 else None,
            city=row.city.strip() if row.city else None,
            state=row.state.strip() if row.state else None,
            zip_code=row.zip_code.strip() if row.zip_code else None,
            country=row.country.strip() if row.country else None,
            bill_to_name=row.bill_to_name.strip() if row.bill_to_name else None,
            bill_to_address_1=row.bill_to_address_1.strip() if row.bill_to_address_1 else None,
            bill_to_address_2=row.bill_to_address_2.strip() if row.bill_to_address_2 else None,
            bill_to_address_3=row.bill_to_address_3.strip() if row.bill_to_address_3 else None,
            bill_to_city=row.bill_to_city.strip() if row.bill_to_city else None,
            bill_to_state=row.bill_to_state.strip() if row.bill_to_state else None,
            bill_to_zip_code=row.bill_to_zip_code.strip() if row.bill_to_zip_code else None,
            bill_to_country=row.bill_to_country.strip() if row.bill_to_country else None,
        )

        # Get project description from CUST_ORDER_BINARY
        project_description = None
        try:
            cursor.execute("""
                SELECT BITS
                FROM CUST_ORDER_BINARY WITH (NOLOCK)
                WHERE CUST_ORDER_ID = ?
                AND RTRIM(TYPE) = 'D'
            """, (job_number,))
            binary_row = cursor.fetchone()
            if binary_row and binary_row.BITS:
                try:
                    project_description = binary_row.BITS.decode('utf-8', errors='ignore').strip()
                except:
                    pass
        except:
            pass  # If query fails, just leave project_description as None

        # Create order header
        order = OrderHeader(
            order_id=row.order_id.strip() if row.order_id else "",
            order_date=row.order_date.date() if hasattr(row.order_date, 'date') else row.order_date,
            customer_po_ref=row.customer_po_ref.strip() if row.customer_po_ref else None,
            contact_first_name=row.contact_first_name.strip() if row.contact_first_name else None,
            contact_last_name=row.contact_last_name.strip() if row.contact_last_name else None,
            contact_phone=row.contact_phone.strip() if row.contact_phone else None,
            contact_fax=row.contact_fax.strip() if row.contact_fax else None,
            promise_date=row.promise_date.date() if row.promise_date and hasattr(row.promise_date, 'date') else (row.promise_date if row.promise_date else None),
            total_amount=Decimal(str(row.total_amount)) if row.total_amount else Decimal("0.00"),
            currency_id=row.currency_id.strip() if row.currency_id else "USD",
            terms_description=row.terms_description.strip() if row.terms_description else None,
            customer=customer,
            # New fields for SAMCO template
            quote_id=row.quote_id.strip() if row.quote_id else None,
            revision_number=None,  # Not available in database
            revision_date=None,  # Not available in database
            sales_rep=row.sales_rep_name.strip() if row.sales_rep_name else (row.sales_rep_id.strip() if row.sales_rep_id else None),
            desired_ship_date=row.desired_ship_date.date() if row.desired_ship_date and hasattr(row.desired_ship_date, 'date') else (row.desired_ship_date if row.desired_ship_date else None),
            factory_acceptance_date_estimated=row.desired_ship_date.date() if row.desired_ship_date and hasattr(row.desired_ship_date, 'date') else (row.desired_ship_date if row.desired_ship_date else None),
            factory_acceptance_date_firmed=None,  # Not in database schema
            project_description=project_description,
        )

        # Get line items
        order.line_items = get_order_line_items(cursor, job_number)

        logger.info(f"Retrieved order {job_number} with {len(order.line_items)} line items")
        return order

    except pyodbc.Error as e:
        logger.error(f"Error searching by job number {job_number}: {e}")
        raise


def get_order_line_items(cursor: pyodbc.Cursor, order_id: str) -> List[OrderLineItem]:
    """
    Retrieve line items for a specific order.

    Args:
        cursor: Database cursor
        order_id: Order ID to get line items for

    Returns:
        List of OrderLineItem objects

    Raises:
        pyodbc.Error: If query fails
    """
    # Get LINE_NO to LOT_ID mapping from INVENTORY_TRANS table
    # INVENTORY_TRANS tracks inventory transactions and links WORK_ORDER to CUST_ORDER_LINE
    # Filter by CUST_ORDER_ID to exclude LOT_IDs from order revisions (e.g., "4049 R3")
    # WORK_ORDER.BASE_ID contains only the numeric part (e.g., "4049")
    # INVENTORY_TRANS.CUST_ORDER_ID contains the full order ID with revision (e.g., "4049 R3")
    lot_id_mapping = {}
    try:
        # Extract base number from order ID for WORK_ORDER.BASE_ID
        # Handles: "4049 R3" -> "4049", "4126-R2" -> "4126", "4397R1" -> "4397"
        import re

        if ' ' in order_id:
            # Space-separated revision (e.g., "4049 R3")
            base_number = order_id.split()[0]
        elif '-' in order_id:
            # Dash-separated revision (e.g., "4126-R2")
            base_number = order_id.split('-')[0]
        else:
            # Try attached revision like "4397R1"
            match = re.match(r'^(.+\d)R\d+$', order_id)
            if match:
                base_number = match.group(1)
            else:
                # No revision found - use as-is
                base_number = order_id

        lot_query = """
            SELECT DISTINCT
                wo.LOT_ID,
                it.CUST_ORDER_LINE_NO AS LINE_NO
            FROM WORK_ORDER wo WITH (NOLOCK)
            INNER JOIN INVENTORY_TRANS it WITH (NOLOCK)
                ON wo.BASE_ID = it.WORKORDER_BASE_ID
                AND wo.LOT_ID = it.WORKORDER_LOT_ID
            WHERE wo.BASE_ID = ?
                AND it.CUST_ORDER_ID = ?
                AND wo.LOT_ID NOT LIKE '%W'
                AND it.CUST_ORDER_LINE_NO IS NOT NULL
            ORDER BY it.CUST_ORDER_LINE_NO, wo.LOT_ID
        """
        cursor.execute(lot_query, (base_number, order_id))
        for row in cursor.fetchall():
            line_no = row.LINE_NO
            lot_id = row.LOT_ID.strip() if row.LOT_ID else None
            if lot_id and line_no not in lot_id_mapping:
                # Take first LOT_ID for each LINE_NO (in case of multiple)
                lot_id_mapping[line_no] = lot_id
    except Exception as e:
        logger.warning(f"Could not fetch LOT_ID mapping from INVENTORY_TRANS: {e}")
        # Continue with empty mapping - will use fallback

    try:
        # Get order line items
        query = """
            SELECT
                LINE_NO AS line_number,
                CUST_ORDER_ID AS order_id,
                PART_ID AS part_id,
                ORDER_QTY AS quantity,
                UNIT_PRICE AS unit_price,
                TOTAL_AMT_ORDERED AS line_total,
                MISC_REFERENCE AS description,
                PROMISE_DATE AS promise_date
            FROM CUST_ORDER_LINE WITH (NOLOCK)
            WHERE CUST_ORDER_ID = ?
            ORDER BY LINE_NO
        """

        cursor.execute(query, (order_id,))
        rows = cursor.fetchall()

        # Check if order has a parent/header line (UNIT_PRICE = 0)
        has_parent_line = any(Decimal(str(row.unit_price)) == Decimal("0.00") for row in rows if row.unit_price is not None)

        # Get binary text data for all lines
        # Note: TYPE column may have trailing spaces, so use LIKE or RTRIM
        binary_query = """
            SELECT
                CUST_ORDER_LINE_NO AS line_number,
                BITS AS binary_data
            FROM CUST_LINE_BINARY WITH (NOLOCK)
            WHERE CUST_ORDER_ID = ?
            AND RTRIM(TYPE) = 'D'
            ORDER BY CUST_ORDER_LINE_NO
        """

        cursor.execute(binary_query, (order_id,))
        binary_rows = cursor.fetchall()

        # Create a map of line_number -> binary_text
        binary_text_map = {}
        for binary_row in binary_rows:
            if binary_row.binary_data:
                try:
                    text = binary_row.binary_data.decode('utf-8', errors='ignore').strip()
                    binary_text_map[binary_row.line_number] = text
                except:
                    pass

        line_items = []
        for row in rows:
            line_number = int(row.line_number) if row.line_number else 0

            # Get binary text for this line if available
            binary_text = binary_text_map.get(line_number) if line_number else None

            # Use LOT_ID from INVENTORY_TRANS mapping if available, otherwise let fallback generate from line_number
            base_id = None
            if line_number in lot_id_mapping:
                base_id = f"{order_id}/{lot_id_mapping[line_number]}"

            line_items.append(
                OrderLineItem(
                    line_number=line_number,
                    order_id=row.order_id.strip() if row.order_id else "",
                    base_id=base_id,  # Use INVENTORY_TRANS mapping or let fallback generate {ORDER_ID}/{LINE_NO:02d}
                    part_id=row.part_id.strip() if row.part_id else None,
                    quantity=Decimal(str(row.quantity)) if row.quantity else Decimal("0.0000"),
                    unit_price=Decimal(str(row.unit_price)) if row.unit_price else Decimal("0.00"),
                    line_total=Decimal(str(row.line_total)) if row.line_total else Decimal("0.00"),
                    description=row.description.strip() if row.description else None,
                    promise_date=row.promise_date.date() if row.promise_date and hasattr(row.promise_date, 'date') else (row.promise_date if row.promise_date else None),
                    binary_text=binary_text,
                    has_parent_line=has_parent_line,
                )
            )

        return line_items

    except pyodbc.Error as e:
        logger.error(f"Error retrieving line items for order {order_id}: {e}")
        raise


def search_by_customer_name(
    cursor: pyodbc.Cursor, customer_name: str, limit: int = 5000
) -> List[OrderSummary]:
    """
    Search for orders by partial customer name match (case-insensitive).

    Args:
        cursor: Database cursor
        customer_name: Customer name or partial name to search for
        limit: Maximum number of orders to return (default: 5000)

    Returns:
        List of OrderSummary objects

    Raises:
        pyodbc.Error: If query fails
    """
    query = """
        SELECT TOP (?)
            co.ID AS job_number,
            c.NAME AS customer_name,
            co.ORDER_DATE AS order_date,
            co.TOTAL_AMT_ORDERED AS total_amount,
            co.CUSTOMER_PO_REF AS customer_po
        FROM CUSTOMER_ORDER co WITH (NOLOCK)
        INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
        WHERE c.NAME LIKE ?
        ORDER BY co.ORDER_DATE DESC
    """

    # Add wildcards for partial matching
    search_pattern = f"%{customer_name}%"

    try:
        cursor.execute(query, (limit, search_pattern))
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append(
                OrderSummary(
                    job_number=row.job_number.strip() if row.job_number else "",
                    customer_name=row.customer_name.strip() if row.customer_name else "",
                    order_date=row.order_date.date() if hasattr(row.order_date, 'date') else row.order_date,
                    total_amount=Decimal(str(row.total_amount)) if row.total_amount else Decimal("0.00"),
                    customer_po=row.customer_po.strip() if row.customer_po else None,
                )
            )

        logger.info(f"Retrieved {len(orders)} orders for customer name: {customer_name}")
        return orders

    except pyodbc.Error as e:
        logger.error(f"Error searching by customer name '{customer_name}': {e}")
        raise


def search_by_customer_name_and_date(
    cursor: pyodbc.Cursor,
    customer_name: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 5000
) -> List[OrderSummary]:
    """
    Search for orders by customer name with optional date range filter.

    Args:
        cursor: Database cursor
        customer_name: Customer name or partial name to search for
        start_date: Start date for filter (inclusive)
        end_date: End date for filter (inclusive)
        limit: Maximum number of orders to return (default: 5000)

    Returns:
        List of OrderSummary objects

    Raises:
        pyodbc.Error: If query fails
    """
    query = """
        SELECT TOP (?)
            co.ID AS job_number,
            c.NAME AS customer_name,
            co.ORDER_DATE AS order_date,
            co.TOTAL_AMT_ORDERED AS total_amount,
            co.CUSTOMER_PO_REF AS customer_po
        FROM CUSTOMER_ORDER co WITH (NOLOCK)
        INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
        WHERE c.NAME LIKE ?
    """

    params = [limit, f"%{customer_name}%"]

    if start_date:
        query += " AND co.ORDER_DATE >= ?"
        params.append(start_date)

    if end_date:
        query += " AND co.ORDER_DATE <= ?"
        params.append(end_date)

    query += " ORDER BY co.ORDER_DATE DESC"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            orders.append(
                OrderSummary(
                    job_number=row.job_number.strip() if row.job_number else "",
                    customer_name=row.customer_name.strip() if row.customer_name else "",
                    order_date=row.order_date.date() if hasattr(row.order_date, 'date') else row.order_date,
                    total_amount=Decimal(str(row.total_amount)) if row.total_amount else Decimal("0.00"),
                    customer_po=row.customer_po.strip() if row.customer_po else None,
                )
            )

        logger.info(f"Retrieved {len(orders)} orders for customer '{customer_name}' with date filter")
        return orders

    except pyodbc.Error as e:
        logger.error(f"Error searching by customer name and date: {e}")
        raise
