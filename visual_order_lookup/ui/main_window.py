"""Main application window."""

import logging
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QLabel,
    QStackedWidget,
)
from PyQt6.QtCore import QThread, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.order_service import OrderService, DatabaseWorker
from visual_order_lookup.ui.navigation_panel import NavigationPanel
from visual_order_lookup.ui.sales_module import SalesModuleWidget
from visual_order_lookup.ui.inventory_module import InventoryModuleWidget
from visual_order_lookup.ui.engineering import EngineeringModule
from visual_order_lookup.ui.dialogs import LoadingDialog, ErrorHandler
from visual_order_lookup.utils.config import get_config
from visual_order_lookup.database.models import DateRangeFilter


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        # Load configuration
        try:
            self.config = get_config()
            self.config.setup_logging()
        except Exception as e:
            ErrorHandler.show_general_error(f"Configuration error: {e}")
            raise

        # Initialize database connection and service
        try:
            self.db_connection = DatabaseConnection(self.config.connection_string)
            self.order_service = OrderService(self.db_connection)
        except Exception as e:
            ErrorHandler.show_connection_error()
            raise

        # Worker thread for async operations
        self.worker_thread = None
        self.worker = None

        # Loading dialog
        self.loading_dialog = None

        # Search state tracking
        self.current_customer_search = None  # Active customer name search
        self.current_date_filter = None  # Active date range filter

        self.setup_ui()
        self.setup_connections()

        # Load recent orders on startup
        self.load_recent_orders()

    def setup_ui(self):
        """Set up user interface."""
        self.setWindowTitle(self.config.app_name)
        self.setMinimumSize(1200, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout (navigation + modules)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation panel (left side)
        self.navigation_panel = NavigationPanel()
        main_layout.addWidget(self.navigation_panel)

        # Module container (right side) - QStackedWidget for module switching
        self.module_stack = QStackedWidget()

        # Create Sales module widget (wrap existing Sales UI)
        self.sales_module = SalesModuleWidget()
        self.module_stack.addWidget(self.sales_module)  # Index 0

        # Create Inventory module widget (full functionality)
        self.inventory_module = InventoryModuleWidget(self.db_connection)
        self.module_stack.addWidget(self.inventory_module)  # Index 1

        # T080-T083: Create Engineering module widget (Work Order hierarchy viewer)
        self.engineering_module = EngineeringModule(self.db_connection)
        self.module_stack.addWidget(self.engineering_module)  # Index 2

        main_layout.addWidget(self.module_stack)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addPermanentWidget(self.status_label)

        # Setup keyboard shortcuts for module switching
        self._setup_shortcuts()

    def setup_connections(self):
        """Set up signal/slot connections."""
        # Navigation panel -> module stack switching
        self.navigation_panel.currentRowChanged.connect(self.module_stack.setCurrentIndex)

        # T084: Update window title when module changes
        self.navigation_panel.currentRowChanged.connect(self._on_module_changed)

        # Sales module signals
        self.sales_module.order_selected.connect(self.on_order_selected)
        self.sales_module.date_filter_requested.connect(self.on_date_filter)
        self.sales_module.clear_filters_requested.connect(self.on_clear_filters)
        self.sales_module.search_requested.connect(self.on_search)
        self.sales_module.search_cleared.connect(self.on_search_cleared)

        # Cross-module navigation (currently no signals from Engineering module)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts for module switching."""
        # Ctrl+1: Switch to Sales
        shortcut_sales = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_sales.activated.connect(lambda: self.navigation_panel.set_module_index(0))

        # Ctrl+2: Switch to Inventory
        shortcut_inventory = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_inventory.activated.connect(lambda: self.navigation_panel.set_module_index(1))

        # Ctrl+3: Switch to Engineering
        shortcut_engineering = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut_engineering.activated.connect(lambda: self.navigation_panel.set_module_index(2))

    def _on_module_changed(self, index: int):
        """Handle module change to update window title.

        T084: Update window title for Engineering module
        """
        module_names = {
            0: "Sales",
            1: "Inventory",
            2: "Engineering - Work Order Lookup - Read Only"
        }

        base_title = self.config.app_name
        if index in module_names:
            self.setWindowTitle(f"{base_title} - {module_names[index]}")
        else:
            self.setWindowTitle(base_title)

    def cleanup_worker_thread(self):
        """Called when thread finishes to clean up references."""
        self.worker_thread = None
        self.worker = None

    def on_order_selected(self, job_number: str):
        """
        Handle order selection.

        Args:
            job_number: Selected order's job number
        """
        logger.info(f"Order selected: {job_number}")
        self.status_label.setText(f"Loading order {job_number}...")

        # Load order details asynchronously
        self.worker_thread = QThread()
        self.worker = DatabaseWorker(
            self.order_service, "get_order_by_job_number", job_number=job_number
        )

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_order_details_loaded)
        self.worker.error.connect(self.on_order_details_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def on_order_details_loaded(self, order):
        """Handle successful order details loading."""
        if order:
            self.sales_module.order_detail.display_order(order)
            self.status_label.setText(f"Order {order.order_id} loaded")
        else:
            ErrorHandler.show_not_found("Order", "selected job number", self)
            self.status_label.setText("Order not found")

    def on_order_details_error(self, error_message: str):
        """Handle order details loading error."""
        ErrorHandler.show_general_error(error_message, self)
        self.status_label.setText("Error loading order details")

    def on_date_filter(self, date_filter: DateRangeFilter):
        """Handle date range filter."""
        if not date_filter.validate():
            ErrorHandler.show_validation_error(
                "Start date must be before or equal to end date", self
            )
            return

        # Store date filter state
        self.current_date_filter = date_filter

        logger.info(f"Filtering orders by date range")
        self.status_label.setText("Filtering orders...")

        self.loading_dialog = LoadingDialog("Filtering orders...", self)
        self.loading_dialog.show()

        # If there's an active customer search, combine with date filter
        if self.current_customer_search:
            logger.info(f"Combining date filter with customer search: {self.current_customer_search}")
            self.worker_thread = QThread()
            self.worker = DatabaseWorker(
                self.order_service,
                "search_by_customer_name",
                customer_name=self.current_customer_search,
                start_date=date_filter.start_date,
                end_date=date_filter.end_date
            )
        else:
            # No active customer search, just filter by date
            self.worker_thread = QThread()
            self.worker = DatabaseWorker(
                self.order_service, "filter_by_date_range", date_filter=date_filter
            )

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_orders_loaded)
        self.worker.error.connect(self.on_load_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def on_clear_filters(self):
        """Handle clear filters."""
        # Clear search state
        self.current_customer_search = None
        self.current_date_filter = None

        # Clear search input UI
        self.sales_module.toolbar.clear_search()

        # Load recent orders
        self.load_recent_orders()

    def on_search(self, search_type: str, search_value: str):
        """Handle search."""
        logger.info(f"Searching by {search_type}: {search_value}")
        self.status_label.setText(f"Searching...")

        self.loading_dialog = LoadingDialog(f"Searching for {search_value}...", self)
        self.loading_dialog.show()

        if search_type == "Job Number":
            # Job number search - clear search state and show order details directly
            self.current_customer_search = None
            # Keep date filter if active

            self.worker_thread = QThread()
            self.worker = DatabaseWorker(
                self.order_service, "get_order_by_job_number", job_number=search_value
            )

            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_job_number_search_result)
            self.worker.error.connect(self.on_load_error)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.error.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(self.cleanup_worker_thread)

            self.worker_thread.start()

        else:  # Customer Name
            # Store customer search state
            self.current_customer_search = search_value

            # Use date filter if active
            start_date = self.current_date_filter.start_date if self.current_date_filter else None
            end_date = self.current_date_filter.end_date if self.current_date_filter else None

            if start_date or end_date:
                logger.info(f"Combining customer search with date filter")

            self.worker_thread = QThread()
            self.worker = DatabaseWorker(
                self.order_service,
                "search_by_customer_name",
                customer_name=search_value,
                start_date=start_date,
                end_date=end_date
            )

            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_orders_loaded)
            self.worker.error.connect(self.on_load_error)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.error.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(self.cleanup_worker_thread)

            self.worker_thread.start()

    def on_search_cleared(self):
        """Handle search input being cleared.

        When user clears the search input (e.g., customer name), revert to date filter
        results if a date filter is active, otherwise load recent orders.
        """
        logger.info("Search input cleared")

        # Clear customer search state
        self.current_customer_search = None

        # If there's an active date filter, reapply it
        if self.current_date_filter:
            logger.info("Reapplying date filter after search cleared")
            self.status_label.setText("Applying date filter...")

            self.loading_dialog = LoadingDialog("Filtering orders...", self)
            self.loading_dialog.show()

            self.worker_thread = QThread()
            self.worker = DatabaseWorker(
                self.order_service,
                "filter_by_date_range",
                date_filter=self.current_date_filter
            )

            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_orders_loaded)
            self.worker.error.connect(self.on_load_error)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.error.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(self.cleanup_worker_thread)

            self.worker_thread.start()
        else:
            # No date filter active, load recent orders
            logger.info("No date filter active, loading recent orders")
            self.load_recent_orders()

    def on_job_number_search_result(self, order):
        """Handle job number search result."""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if order:
            # Clear order list and show order details
            self.sales_module.order_list.clear()
            self.sales_module.order_detail.display_order(order)
            self.status_label.setText(f"Order {order.order_id} found")
        else:
            ErrorHandler.show_not_found("Order", self.sales_module.toolbar.search_input.text(), self)
            self.status_label.setText("Order not found")

    def load_recent_orders(self):
        """Load recent orders asynchronously."""
        # Clear search state when loading recent orders
        self.current_customer_search = None
        self.current_date_filter = None

        logger.info("Loading recent orders...")
        self.status_label.setText("Loading recent orders...")

        # Show loading dialog
        self.loading_dialog = LoadingDialog("Loading recent orders...", self)
        self.loading_dialog.show()

        # Create worker thread (increased limit from 100 to 500)
        self.worker_thread = QThread()
        self.worker = DatabaseWorker(self.order_service, "load_recent_orders", limit=500)

        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_orders_loaded)
        self.worker.error.connect(self.on_load_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        # Start thread
        self.worker_thread.start()

    def on_orders_loaded(self, orders):
        """
        Handle successful order loading.

        Args:
            orders: List of OrderSummary objects
        """
        # Close loading dialog
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        # Update UI
        self.sales_module.order_list.set_orders(orders)
        self.status_label.setText(f"Loaded {len(orders)} orders")

        logger.info(f"Successfully loaded {len(orders)} orders")

    def on_load_error(self, error_message: str):
        """
        Handle order loading error.

        Args:
            error_message: Error message from worker
        """
        # Close loading dialog
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        # Show error dialog
        if "connection" in error_message.lower() or "connect" in error_message.lower():
            retry = ErrorHandler.show_connection_error(self, retry_callback=True)
            if retry:
                self.load_recent_orders()
        elif "timeout" in error_message.lower():
            ErrorHandler.show_timeout_error(self)
        else:
            ErrorHandler.show_general_error(error_message, self)

        self.status_label.setText("Error loading orders")
        logger.error(f"Error loading orders: {error_message}")

    def on_switch_to_inventory(self, part_number: str):
        """Handle request to switch to Inventory module and load part.

        Args:
            part_number: Part number to load in Inventory module
        """
        logger.info(f"Switching to Inventory module for part: {part_number}")

        # Switch to Inventory module (index 1)
        self.navigation_panel.set_module_index(1)
        self.module_stack.setCurrentIndex(1)

        # Trigger part search in Inventory module
        self.inventory_module.search_panel.part_input.setText(part_number)
        self.inventory_module._on_search_part(part_number)

        self.status_label.setText(f"Loading part {part_number} in Inventory module")

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Clean up database connection
        if self.db_connection:
            self.db_connection.close()

        # Disconnect signals and clean up worker thread
        try:
            if self.worker_thread is not None:
                # Disconnect all signals to prevent issues during shutdown
                try:
                    self.worker_thread.started.disconnect()
                except (TypeError, RuntimeError):
                    pass  # Already disconnected or thread deleted

                if self.worker is not None:
                    try:
                        self.worker.finished.disconnect()
                        self.worker.error.disconnect()
                    except (TypeError, RuntimeError):
                        pass  # Already disconnected or worker deleted

                # Now safely quit the thread if still running
                try:
                    if self.worker_thread.isRunning():
                        self.worker_thread.quit()
                        self.worker_thread.wait(2000)  # Wait up to 2 seconds
                except RuntimeError:
                    # Thread already deleted
                    logger.debug("Worker thread already deleted during close")
        except Exception as e:
            # Catch any unexpected exceptions during cleanup
            logger.error(f"Error during thread cleanup: {e}")
        finally:
            self.worker_thread = None
            self.worker = None

        event.accept()
