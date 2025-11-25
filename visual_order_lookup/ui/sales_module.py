"""Sales Module for customer order lookup.

Provides order search, filtering, and acknowledgement display.
"""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal

from visual_order_lookup.database.models import DateRangeFilter
from visual_order_lookup.ui.order_list_view import OrderListView
from visual_order_lookup.ui.order_detail_view import OrderDetailView
from visual_order_lookup.ui.search_panel import CombinedFilterSearchToolbar


logger = logging.getLogger(__name__)


class SalesModuleWidget(QWidget):
    """Sales module widget (Customer Order Entry).

    Encapsulates the existing sales functionality as a reusable module widget.
    """

    # Signals for parent to handle (MainWindow will connect these to service calls)
    order_selected = pyqtSignal(str)  # job_number
    date_filter_requested = pyqtSignal(DateRangeFilter)
    clear_filters_requested = pyqtSignal()
    search_requested = pyqtSignal(str, str)  # search_type, search_value
    search_cleared = pyqtSignal()  # Emitted when search input is cleared

    def __init__(self, parent=None):
        """Initialize sales module with UI components.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Combined filter and search toolbar
        self.toolbar = CombinedFilterSearchToolbar()
        layout.addWidget(self.toolbar)

        # Horizontal splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Order list view (left side - wider for better space usage)
        self.order_list = OrderListView()
        self.order_list.setMinimumWidth(350)
        splitter.addWidget(self.order_list)

        # Order detail view (right side)
        self.order_detail = OrderDetailView()
        self.order_detail.setMinimumWidth(600)
        splitter.addWidget(self.order_detail)

        # Set splitter sizes to ~40% list, 60% details (better space usage)
        splitter.setSizes([400, 600])
        splitter.setStretchFactor(0, 3)  # List gets more space
        splitter.setStretchFactor(1, 4)  # Details still gets most space

        layout.addWidget(splitter)

        # Setup connections
        self._setup_connections()

    def _setup_connections(self):
        """Set up internal signal/slot connections."""
        # Forward signals to parent
        self.order_list.order_selected.connect(self.order_selected.emit)
        self.toolbar.filter_clicked.connect(self.date_filter_requested.emit)
        self.toolbar.clear_clicked.connect(self.clear_filters_requested.emit)
        self.toolbar.search_clicked.connect(self.search_requested.emit)
        self.toolbar.search_cleared.connect(self.search_cleared.emit)
