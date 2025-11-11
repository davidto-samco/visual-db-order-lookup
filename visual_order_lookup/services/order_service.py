"""Business logic for order retrieval and search operations."""

import logging
from typing import List, Optional
from datetime import date
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import pyodbc

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database import queries
from visual_order_lookup.database.models import (
    OrderSummary,
    OrderHeader,
    DateRangeFilter,
)


logger = logging.getLogger(__name__)


class OrderService:
    """Service for order retrieval and search operations."""

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize order service.

        Args:
            connection: Database connection manager
        """
        self.connection = connection

    def load_recent_orders(self, limit: int = 100) -> List[OrderSummary]:
        """
        Load most recent orders.

        Args:
            limit: Maximum number of orders to return

        Returns:
            List of OrderSummary objects

        Raises:
            Exception: If database operation fails
        """
        try:
            cursor = self.connection.get_cursor()
            orders = queries.get_recent_orders(cursor, limit)
            cursor.close()
            return orders

        except pyodbc.Error as e:
            logger.error(f"Database error loading recent orders: {e}")
            raise Exception(f"Failed to load recent orders: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error loading recent orders: {e}")
            raise

    def filter_by_date_range(self, date_filter: DateRangeFilter) -> List[OrderSummary]:
        """
        Filter orders by date range.

        Args:
            date_filter: Date range filter with start and/or end date

        Returns:
            List of OrderSummary objects

        Raises:
            ValueError: If date range is invalid
            Exception: If database operation fails
        """
        if not date_filter.validate():
            raise ValueError("Invalid date range: start date must be before or equal to end date")

        try:
            cursor = self.connection.get_cursor()
            orders = queries.filter_orders_by_date_range(
                cursor, date_filter.start_date, date_filter.end_date
            )
            cursor.close()
            return orders

        except pyodbc.Error as e:
            logger.error(f"Database error filtering orders by date range: {e}")
            raise Exception(f"Failed to filter orders: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error filtering orders: {e}")
            raise

    def get_order_by_job_number(self, job_number: str) -> Optional[OrderHeader]:
        """
        Get complete order details by job number.

        Args:
            job_number: Job number to search for

        Returns:
            OrderHeader object with customer and line items, or None if not found

        Raises:
            Exception: If database operation fails
        """
        if not job_number or not job_number.strip():
            raise ValueError("Job number cannot be empty")

        try:
            cursor = self.connection.get_cursor()
            order = queries.search_by_job_number(cursor, job_number.strip())
            cursor.close()
            return order

        except pyodbc.Error as e:
            logger.error(f"Database error searching for job number {job_number}: {e}")
            raise Exception(f"Failed to search for order: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error searching for job number: {e}")
            raise

    def search_by_customer_name(
        self,
        customer_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[OrderSummary]:
        """
        Search orders by partial customer name with optional date range.

        Args:
            customer_name: Customer name or partial name to search for
            start_date: Optional start date for filter
            end_date: Optional end date for filter

        Returns:
            List of OrderSummary objects

        Raises:
            ValueError: If customer name is empty
            Exception: If database operation fails
        """
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name cannot be empty")

        try:
            cursor = self.connection.get_cursor()

            # Use combined search if date filter is provided
            if start_date or end_date:
                orders = queries.search_by_customer_name_and_date(
                    cursor, customer_name.strip(), start_date, end_date
                )
            else:
                orders = queries.search_by_customer_name(cursor, customer_name.strip())

            cursor.close()
            return orders

        except pyodbc.Error as e:
            logger.error(f"Database error searching for customer '{customer_name}': {e}")
            raise Exception(f"Failed to search for customer: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error searching for customer: {e}")
            raise


class DatabaseWorker(QObject):
    """Worker thread for asynchronous database operations."""

    # Signals
    finished = pyqtSignal(object)  # Emits results on success
    error = pyqtSignal(str)  # Emits error message on failure

    def __init__(self, service: OrderService, operation: str, **kwargs):
        """
        Initialize database worker.

        Args:
            service: OrderService instance
            operation: Operation name (e.g., 'load_recent_orders', 'filter_by_date_range')
            **kwargs: Arguments to pass to the operation
        """
        super().__init__()
        self.service = service
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        """Execute database operation in background thread."""
        try:
            # Get the operation method
            method = getattr(self.service, self.operation)

            # Execute operation
            result = method(**self.kwargs)

            # Emit success signal
            self.finished.emit(result)

        except Exception as e:
            # Emit error signal
            error_msg = str(e)
            logger.error(f"Worker error in {self.operation}: {error_msg}")
            self.error.emit(error_msg)
