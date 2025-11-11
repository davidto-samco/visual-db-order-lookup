"""Order list view widget using Qt model/view architecture."""

import logging
from typing import List
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtWidgets import QWidget, QTableView, QVBoxLayout, QHeaderView

from visual_order_lookup.database.models import OrderSummary


logger = logging.getLogger(__name__)


class OrderTableModel(QAbstractTableModel):
    """Table model for displaying order summaries."""

    def __init__(self, orders: List[OrderSummary] = None):
        """
        Initialize order table model.

        Args:
            orders: List of OrderSummary objects to display
        """
        super().__init__()
        self.orders = orders or []
        self.headers = ["Job #", "Customer Name", "PO Number", "Date"]

    def rowCount(self, parent=QModelIndex()) -> int:
        """Get number of rows."""
        return len(self.orders)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Get number of columns."""
        return len(self.headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """Get data for cell."""
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            order = self.orders[index.row()]
            column = index.column()

            if column == 0:  # Job Number
                return order.job_number
            elif column == 1:  # Customer Name
                return order.customer_name
            elif column == 2:  # PO Number
                return order.customer_po or "-"
            elif column == 3:  # Order Date
                return order.formatted_date()

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        """Get header data."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.headers[section]
            else:
                return str(section + 1)
        return None

    def setOrders(self, orders: List[OrderSummary]):
        """
        Update orders and refresh view.

        Args:
            orders: New list of OrderSummary objects
        """
        self.beginResetModel()
        self.orders = orders
        self.endResetModel()

    def getOrder(self, row: int) -> OrderSummary:
        """
        Get order at specific row.

        Args:
            row: Row index

        Returns:
            OrderSummary object at row
        """
        if 0 <= row < len(self.orders):
            return self.orders[row]
        return None


class OrderListView(QWidget):
    """Widget for displaying list of orders in table view."""

    # Signal emitted when order is selected
    order_selected = pyqtSignal(str)  # Emits job_number

    def __init__(self, parent=None):
        """Initialize order list view."""
        super().__init__(parent)
        self.model = OrderTableModel()
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create table view
        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        # Configure table appearance
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)

        # Configure column widths
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Job Number
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Customer Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # PO Number
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Date

        # Connect selection signal
        self.table_view.selectionModel().currentRowChanged.connect(self.on_row_selected)

        layout.addWidget(self.table_view)

    def on_row_selected(self, current: QModelIndex, previous: QModelIndex):
        """
        Handle row selection.

        Args:
            current: Currently selected index
            previous: Previously selected index
        """
        if current.isValid():
            order = self.model.getOrder(current.row())
            if order:
                logger.info(f"Order selected: {order.job_number}")
                self.order_selected.emit(order.job_number)

    def set_orders(self, orders: List[OrderSummary]):
        """
        Update displayed orders.

        Args:
            orders: List of OrderSummary objects to display
        """
        self.model.setOrders(orders)
        logger.info(f"Displaying {len(orders)} orders")

    def clear(self):
        """Clear all orders from view."""
        self.model.setOrders([])
