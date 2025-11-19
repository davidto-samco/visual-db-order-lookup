"""Work Order Service for Engineering Module.

This service provides business logic for work order hierarchical data retrieval.
Acts as a facade over database query functions with validation, error handling, and logging.
"""

import logging
from typing import List, Optional
import pyodbc

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database.queries import work_order_queries
from visual_order_lookup.database.models.work_order import (
    WorkOrder,
    Operation,
    Requirement,
    LaborTicket,
    InventoryTransaction,
    WIPBalance,
)

logger = logging.getLogger(__name__)


class WorkOrderServiceError(Exception):
    """Base exception for work order service errors."""
    pass


class WorkOrderNotFoundError(WorkOrderServiceError):
    """Raised when work order is not found."""
    pass


class WorkOrderService:
    """Service for retrieving work order hierarchical data from Visual database.

    Provides methods for:
    - Searching work orders by BASE_ID pattern
    - Loading work order headers with aggregate counts
    - Lazy loading operations, requirements, labor, materials, WIP
    - Traversing work order hierarchies via SUBORD_WO_SUB_ID
    """

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize service with database connection.

        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
        logger.info("WorkOrderService initialized")

    def search_work_orders(self, base_id_pattern: str, limit: int = 1000) -> List[WorkOrder]:
        """Search for work orders by BASE_ID pattern.

        Args:
            base_id_pattern: BASE_ID search pattern (supports wildcards, e.g., '8113')
            limit: Maximum results to return (default 1000, max 1000)

        Returns:
            List of matching WorkOrder objects, ordered by CREATE_DATE DESC

        Raises:
            ValueError: If base_id_pattern is empty, too long, or limit is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if not base_id_pattern or not base_id_pattern.strip():
            raise ValueError("base_id_pattern cannot be empty")

        base_id_pattern = base_id_pattern.strip().upper()

        if len(base_id_pattern) > 30:
            raise ValueError("base_id_pattern cannot exceed 30 characters")

        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        logger.info(f"Searching work orders: pattern='{base_id_pattern}', limit={limit}")

        try:
            cursor = self.db_connection.get_cursor()
            work_orders = work_order_queries.search_work_orders(cursor, base_id_pattern, limit)
            cursor.close()
            logger.info(f"Search returned {len(work_orders)} work orders")
            return work_orders

        except pyodbc.Error as e:
            error_msg = f"Database error searching work orders: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_work_order_header(self, base_id: str, lot_id: str, sub_id: str) -> WorkOrder:
        """Get complete work order header with aggregate counts.

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID (empty string '' for main)

        Returns:
            WorkOrder object with operation_count, labor_ticket_count, inventory_trans_count

        Raises:
            ValueError: If composite key contains empty/invalid fields
            WorkOrderNotFoundError: If work order not found
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("base_id, lot_id, and sub_id cannot be None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        if not base_id or not lot_id:
            raise ValueError("base_id and lot_id cannot be empty")

        logger.info(f"Loading work order header: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            work_order = work_order_queries.get_work_order_header(cursor, base_id, lot_id, sub_id)
            cursor.close()

            if not work_order:
                raise WorkOrderNotFoundError(f"Work order not found: {base_id}/{lot_id}/{sub_id}")

            logger.info(f"Loaded work order: {work_order.formatted_id()}")
            return work_order

        except pyodbc.Error as e:
            error_msg = f"Database error loading work order header: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_operations(self, base_id: str, lot_id: str, sub_id: str) -> List[Operation]:
        """Get all operations for a work order (lazy load).

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID

        Returns:
            List of Operation objects ordered by SEQUENCE

        Raises:
            ValueError: If composite key is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading operations for: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            operations = work_order_queries.get_operations(cursor, base_id, lot_id, sub_id)
            cursor.close()
            logger.debug(f"Loaded {len(operations)} operations")
            return operations

        except pyodbc.Error as e:
            error_msg = f"Database error loading operations: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_requirements(self, base_id: str, lot_id: str, sub_id: str, operation_seq: int) -> List[Requirement]:
        """Get material requirements for a specific operation (lazy load).

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID
            operation_seq: Operation sequence number

        Returns:
            List of Requirement objects

        Raises:
            ValueError: If parameters are invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        if not isinstance(operation_seq, int) or operation_seq < 0:
            raise ValueError("operation_seq must be a non-negative integer")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading requirements for operation {operation_seq}")

        try:
            cursor = self.db_connection.get_cursor()
            requirements = work_order_queries.get_requirements(cursor, base_id, lot_id, sub_id, operation_seq)
            cursor.close()
            logger.debug(f"Loaded {len(requirements)} requirements")
            return requirements

        except pyodbc.Error as e:
            error_msg = f"Database error loading requirements: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_requirements_by_sub_id(self, base_id: str, lot_id: str, sub_id: str) -> List[Requirement]:
        """Get all requirements for a work order by WORKORDER_SUB_ID (for tree building).

        This retrieves requirements WHERE WORKORDER_SUB_ID = sub_id, which determines
        the tree hierarchy. Used for building the tree structure.

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID (determines tree level)

        Returns:
            List of Requirement objects (both parts and sub-work-orders)

        Raises:
            ValueError: If parameters are invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading requirements by SUB_ID: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            requirements = work_order_queries.get_requirements_by_sub_id(cursor, base_id, lot_id, sub_id)
            cursor.close()
            logger.debug(f"Loaded {len(requirements)} requirements for SUB_ID={sub_id}")
            return requirements

        except pyodbc.Error as e:
            error_msg = f"Database error loading requirements by SUB_ID: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_labor_tickets(self, base_id: str, lot_id: str, sub_id: str) -> List[LaborTicket]:
        """Get all labor transactions for a work order (lazy load).

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID

        Returns:
            List of LaborTicket objects ordered by LABOR_DATE DESC

        Raises:
            ValueError: If composite key is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading labor tickets for: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            labor_tickets = work_order_queries.get_labor_tickets(cursor, base_id, lot_id, sub_id)
            cursor.close()
            logger.debug(f"Loaded {len(labor_tickets)} labor tickets")
            return labor_tickets

        except pyodbc.Error as e:
            error_msg = f"Database error loading labor tickets: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_inventory_transactions(self, base_id: str, lot_id: str, sub_id: str) -> List[InventoryTransaction]:
        """Get all material transactions for a work order (lazy load).

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID

        Returns:
            List of InventoryTransaction objects ordered by TRANS_DATE DESC

        Raises:
            ValueError: If composite key is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading inventory transactions for: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            transactions = work_order_queries.get_inventory_transactions(cursor, base_id, lot_id, sub_id)
            cursor.close()
            logger.debug(f"Loaded {len(transactions)} inventory transactions")
            return transactions

        except pyodbc.Error as e:
            error_msg = f"Database error loading inventory transactions: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_wip_balance(self, base_id: str, lot_id: str, sub_id: str) -> Optional[WIPBalance]:
        """Get WIP cost accumulation for a work order (lazy load).

        Args:
            base_id: Work order BASE_ID
            lot_id: Work order LOT_ID
            sub_id: Work order SUB_ID

        Returns:
            WIPBalance object or None if not found

        Raises:
            ValueError: If composite key is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.debug(f"Loading WIP balance for: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            wip_balance = work_order_queries.get_wip_balance(cursor, base_id, lot_id, sub_id)
            cursor.close()

            if wip_balance:
                logger.debug(f"Loaded WIP balance: {wip_balance.formatted_total()}")
            else:
                logger.debug("No WIP balance found")

            return wip_balance

        except pyodbc.Error as e:
            error_msg = f"Database error loading WIP balance: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e

    def get_work_order_hierarchy(self, base_id: str, lot_id: str, sub_id: str, max_depth: int = 10) -> List[WorkOrder]:
        """Get hierarchical work order tree via SUBORD_WO_SUB_ID relationships.

        Uses recursive CTE to traverse parent-child work order links where a requirement's
        SUBORD_WO_SUB_ID points to a child work order fulfilling that requirement.

        Args:
            base_id: Root work order BASE_ID
            lot_id: Root work order LOT_ID
            sub_id: Root work order SUB_ID
            max_depth: Maximum recursion depth (default 10, prevents infinite loops)

        Returns:
            List of WorkOrder objects in hierarchical order (parent before children)

        Raises:
            ValueError: If composite key is invalid or max_depth is invalid
            WorkOrderServiceError: If database query fails
        """
        # Validation
        if base_id is None or lot_id is None or sub_id is None:
            raise ValueError("Composite key cannot contain None")

        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 50:
            raise ValueError("max_depth must be between 1 and 50")

        base_id = base_id.strip().upper()
        lot_id = lot_id.strip().upper()
        sub_id = sub_id.strip().upper()

        logger.info(f"Loading work order hierarchy from: {base_id}/{lot_id}/{sub_id}")

        try:
            cursor = self.db_connection.get_cursor()
            work_orders = work_order_queries.get_work_order_hierarchy(cursor, base_id, lot_id, sub_id, max_depth)
            cursor.close()
            logger.info(f"Loaded hierarchy with {len(work_orders)} work orders")
            return work_orders

        except pyodbc.Error as e:
            error_msg = f"Database error loading work order hierarchy: {str(e)}"
            logger.error(error_msg)
            raise WorkOrderServiceError(error_msg) from e
