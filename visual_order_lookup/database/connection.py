"""Database connection management for SQL Server."""

import pyodbc
import logging
from typing import Optional
import time


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages single persistent connection to Visual SQL Server database."""

    def __init__(self, connection_string: str):
        """
        Initialize database connection manager.

        Args:
            connection_string: ODBC connection string for SQL Server
        """
        self._connection_string = connection_string
        self._connection: Optional[pyodbc.Connection] = None
        self._max_retries = 3
        self._retry_delay = 2  # seconds

    def connect(self) -> pyodbc.Connection:
        """
        Establish database connection with retry logic.

        Returns:
            Active database connection

        Raises:
            pyodbc.Error: If connection fails after retries
        """
        if self._connection is not None and self._is_connection_alive():
            return self._connection

        last_error = None
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Attempting database connection (attempt {attempt + 1}/{self._max_retries})")

                self._connection = pyodbc.connect(
                    self._connection_string,
                    timeout=10,  # Connection timeout in seconds
                    autocommit=True,  # Read-only operations don't need transactions
                )

                # Set query timeout at connection level
                self._connection.timeout = 30  # Query timeout in seconds

                logger.info("Database connection established successfully")
                return self._connection

            except pyodbc.Error as e:
                last_error = e
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")

                if attempt < self._max_retries - 1:
                    logger.info(f"Retrying in {self._retry_delay} seconds...")
                    time.sleep(self._retry_delay)

        # All retries failed
        logger.error(f"Failed to connect after {self._max_retries} attempts")
        raise last_error

    def close(self) -> None:
        """Close database connection if open."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def _is_connection_alive(self) -> bool:
        """
        Check if current connection is still alive.

        Returns:
            True if connection is active, False otherwise
        """
        if self._connection is None:
            return False

        try:
            # Execute simple query to test connection
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            return False

    def get_cursor(self) -> pyodbc.Cursor:
        """
        Get a new cursor from active connection.

        Returns:
            Database cursor

        Raises:
            pyodbc.Error: If connection is not established
        """
        if self._connection is None or not self._is_connection_alive():
            self.connect()

        return self._connection.cursor()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False  # Don't suppress exceptions
