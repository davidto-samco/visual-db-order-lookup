"""Database models for Visual Order Lookup application.

This module exports all dataclass models for Parts, Sales Orders, BOMs, and Work Orders.
"""

# Import existing models (Sales, Inventory, BOM)
from visual_order_lookup.database.models.core import (
    OrderSummary,
    Customer,
    OrderLineItem,
    OrderHeader,
    DateRangeFilter,
    Part,
    WhereUsed,
    PurchaseHistory,
    Job,
    BOMNode,
)

# Import work order models (Engineering Module)
from visual_order_lookup.database.models.work_order import (
    WorkOrder,
    Operation,
    Requirement,
    LaborTicket,
    InventoryTransaction,
    WIPBalance,
)

__all__ = [
    # Existing models (Sales, Inventory, BOM)
    'OrderSummary',
    'Customer',
    'OrderLineItem',
    'OrderHeader',
    'DateRangeFilter',
    'Part',
    'WhereUsed',
    'PurchaseHistory',
    'Job',
    'BOMNode',
    # Work Order models (Engineering Module)
    'WorkOrder',
    'Operation',
    'Requirement',
    'LaborTicket',
    'InventoryTransaction',
    'WIPBalance',
]
