"""Inventory Module for part lookups and where-used analysis.

Provides part search with where-used and purchase history views.
"""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QThread

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.part_service import PartService
from visual_order_lookup.services.order_service import DatabaseWorker
from visual_order_lookup.ui.part_search_panel import PartSearchPanel
from visual_order_lookup.ui.part_detail_view import PartDetailView
from visual_order_lookup.ui.dialogs import LoadingDialog, ErrorHandler


logger = logging.getLogger(__name__)


class InventoryModuleWidget(QWidget):
    """Inventory module widget (Part Maintenance).

    Provides part search with three-tab detail view:
    - Part Info (master data)
    - Where Used (usage history)
    - Purchase History (PO history)
    """

    def __init__(self, db_connection: DatabaseConnection, parent=None):
        """Initialize inventory module with UI components.

        Args:
            db_connection: Database connection instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize services
        self.db_connection = db_connection
        self.part_service = PartService(db_connection)

        # Worker threads for async operations (separate for each operation)
        self.search_thread = None
        self.search_worker = None
        self.where_used_thread = None
        self.where_used_worker = None
        self.purchase_history_thread = None
        self.purchase_history_worker = None

        # Loading dialog
        self.loading_dialog = None

        # Current part number
        self.current_part_number = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search panel
        self.search_panel = PartSearchPanel()
        layout.addWidget(self.search_panel)

        # Detail view
        self.detail_view = PartDetailView()
        layout.addWidget(self.detail_view)

    def _setup_connections(self):
        """Set up signal/slot connections."""
        self.search_panel.search_requested.connect(self._on_search_part)

    def _cleanup_search_thread(self):
        """Called when search thread finishes."""
        self.search_thread = None
        self.search_worker = None

    def _cleanup_where_used_thread(self):
        """Called when where-used thread finishes."""
        self.where_used_thread = None
        self.where_used_worker = None

    def _cleanup_purchase_history_thread(self):
        """Called when purchase history thread finishes."""
        self.purchase_history_thread = None
        self.purchase_history_worker = None

    def _on_search_part(self, part_number: str):
        """Handle part search request.

        Args:
            part_number: Part number to search for
        """
        logger.info(f"Searching for part: {part_number}")
        self.current_part_number = part_number

        # Clean up any existing search thread
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()

        # Show loading dialog
        self.loading_dialog = LoadingDialog(f"Searching for part {part_number}...", self)
        self.loading_dialog.show()

        # Search for part in background thread
        self.search_thread = QThread()
        self.search_worker = DatabaseWorker(
            self.part_service, "search_by_part_number", part_number=part_number
        )

        self.search_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.finished.connect(self._on_part_found)
        self.search_worker.error.connect(self._on_search_error)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.error.connect(self.search_thread.quit)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        self.search_thread.finished.connect(self._cleanup_search_thread)

        self.search_thread.start()

    def _on_part_found(self, part):
        """Handle successful part search.

        Args:
            part: Part object or None
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if part:
            logger.info(f"Part found: {part.part_number}")
            # Display part info
            self.detail_view.display_part_info(part)

            # Load where-used data
            self._load_where_used(part.part_number)
        else:
            ErrorHandler.show_not_found("Part", self.current_part_number, self)
            self.detail_view.clear()

    def _on_search_error(self, error_message: str):
        """Handle part search error.

        Args:
            error_message: Error message from worker
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if "connection" in error_message.lower():
            ErrorHandler.show_connection_error(self)
        elif "timeout" in error_message.lower():
            ErrorHandler.show_timeout_error(self)
        else:
            ErrorHandler.show_general_error(error_message, self)

        logger.error(f"Error searching for part: {error_message}")

    def _load_where_used(self, part_number: str):
        """Load where-used data for part.

        Args:
            part_number: Part number to load where-used for
        """
        logger.info(f"Loading where-used for part: {part_number}")

        # Clean up any existing where-used thread
        if self.where_used_thread and self.where_used_thread.isRunning():
            self.where_used_thread.quit()
            self.where_used_thread.wait()

        self.where_used_thread = QThread()
        self.where_used_worker = DatabaseWorker(
            self.part_service, "get_where_used", part_number=part_number
        )

        self.where_used_worker.moveToThread(self.where_used_thread)
        self.where_used_thread.started.connect(self.where_used_worker.run)
        self.where_used_worker.finished.connect(self._on_where_used_loaded)
        self.where_used_worker.error.connect(self._on_where_used_error)
        self.where_used_worker.finished.connect(self.where_used_thread.quit)
        self.where_used_worker.error.connect(self.where_used_thread.quit)
        self.where_used_thread.finished.connect(self.where_used_thread.deleteLater)
        self.where_used_thread.finished.connect(self._cleanup_where_used_thread)

        self.where_used_thread.start()

    def _on_where_used_loaded(self, records):
        """Handle successful where-used load.

        Args:
            records: List of WhereUsed records
        """
        logger.info(f"Loaded {len(records)} where-used records")
        self.detail_view.display_where_used(records)

        # Load purchase history
        if self.current_part_number:
            self._load_purchase_history(self.current_part_number)

    def _on_where_used_error(self, error_message: str):
        """Handle where-used load error.

        Args:
            error_message: Error message
        """
        logger.error(f"Error loading where-used: {error_message}")
        # Still try to load purchase history
        if self.current_part_number:
            self._load_purchase_history(self.current_part_number)

    def _load_purchase_history(self, part_number: str):
        """Load purchase history for part.

        Args:
            part_number: Part number to load purchase history for
        """
        logger.info(f"Loading purchase history for part: {part_number}")

        # Clean up any existing purchase history thread
        if self.purchase_history_thread and self.purchase_history_thread.isRunning():
            self.purchase_history_thread.quit()
            self.purchase_history_thread.wait()

        self.purchase_history_thread = QThread()
        self.purchase_history_worker = DatabaseWorker(
            self.part_service, "get_purchase_history", part_number=part_number, limit=100
        )

        self.purchase_history_worker.moveToThread(self.purchase_history_thread)
        self.purchase_history_thread.started.connect(self.purchase_history_worker.run)
        self.purchase_history_worker.finished.connect(self._on_purchase_history_loaded)
        self.purchase_history_worker.error.connect(self._on_purchase_history_error)
        self.purchase_history_worker.finished.connect(self.purchase_history_thread.quit)
        self.purchase_history_worker.error.connect(self.purchase_history_thread.quit)
        self.purchase_history_thread.finished.connect(self.purchase_history_thread.deleteLater)
        self.purchase_history_thread.finished.connect(self._cleanup_purchase_history_thread)

        self.purchase_history_thread.start()

    def _on_purchase_history_loaded(self, records):
        """Handle successful purchase history load.

        Args:
            records: List of PurchaseHistory records
        """
        logger.info(f"Loaded {len(records)} purchase history records")
        self.detail_view.display_purchase_history(records)

    def _on_purchase_history_error(self, error_message: str):
        """Handle purchase history load error.

        Args:
            error_message: Error message
        """
        logger.error(f"Error loading purchase history: {error_message}")
