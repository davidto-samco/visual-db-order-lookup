"""Database query modules for Visual Order Lookup application.

This package contains query functions organized by entity type.
"""

# Import existing queries (Sales, Orders)
from visual_order_lookup.database.queries.core import (
    get_recent_orders,
    filter_orders_by_date_range,
    search_by_job_number,
    get_order_line_items,
    search_by_customer_name,
    search_by_customer_name_and_date,
)

# Import work order queries (Engineering)
from visual_order_lookup.database.queries.work_order_queries import (
    search_work_orders,
    get_work_order_header,
    get_operations,
    get_requirements,
    get_labor_tickets,
    get_inventory_transactions,
    get_wip_balance,
    get_work_order_hierarchy,
)

__all__ = [
    # Existing queries (Sales, Orders)
    'get_recent_orders',
    'filter_orders_by_date_range',
    'search_by_job_number',
    'get_order_line_items',
    'search_by_customer_name',
    'search_by_customer_name_and_date',
    # Work Order queries (Engineering)
    'search_work_orders',
    'get_work_order_header',
    'get_operations',
    'get_requirements',
    'get_labor_tickets',
    'get_inventory_transactions',
    'get_wip_balance',
    'get_work_order_hierarchy',
]
