"""Search panel widget with date filtering and search controls."""

import logging
from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QLineEdit,
    QComboBox,
    QGroupBox,
    QFrame,
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt

from visual_order_lookup.database.models import DateRangeFilter


logger = logging.getLogger(__name__)


class DateRangePanel(QWidget):
    """Widget for date range filtering."""

    # Signals
    filter_clicked = pyqtSignal(DateRangeFilter)  # Emits date filter
    clear_clicked = pyqtSignal()  # Emits when clear button clicked

    def __init__(self, parent=None):
        """Initialize date range panel."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QHBoxLayout(self)

        # Start date
        layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.start_date_edit.setMinimumDate(QDate(1985, 1, 1))
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        self.start_date_edit.setSpecialValueText(" ")  # Show blank when cleared
        self.start_date_edit.clear()
        layout.addWidget(self.start_date_edit)

        # End date
        layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.end_date_edit.setMinimumDate(QDate(1985, 1, 1))
        self.end_date_edit.setMaximumDate(QDate.currentDate())
        self.end_date_edit.setSpecialValueText(" ")  # Show blank when cleared
        self.end_date_edit.clear()
        layout.addWidget(self.end_date_edit)

        # Filter button
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.on_filter_clicked)
        layout.addWidget(self.filter_button)

        # Clear button
        self.clear_button = QPushButton("Clear Filters")
        self.clear_button.clicked.connect(self.on_clear_clicked)
        layout.addWidget(self.clear_button)

        layout.addStretch()

    def on_filter_clicked(self):
        """Handle filter button click."""
        # Get dates (None if not set)
        start_date = None
        if not self.start_date_edit.text().strip() == "":
            qdate = self.start_date_edit.date()
            start_date = date(qdate.year(), qdate.month(), qdate.day())

        end_date = None
        if not self.end_date_edit.text().strip() == "":
            qdate = self.end_date_edit.date()
            end_date = date(qdate.year(), qdate.month(), qdate.day())

        # Create filter
        date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)

        # Emit signal
        self.filter_clicked.emit(date_filter)

    def on_clear_clicked(self):
        """Handle clear button click."""
        self.start_date_edit.clear()
        self.end_date_edit.clear()
        self.clear_clicked.emit()


class SearchPanel(QWidget):
    """Widget for search controls with job number and customer name search."""

    # Signals
    search_clicked = pyqtSignal(str, str)  # Emits (search_type, search_value)

    def __init__(self, parent=None):
        """Initialize search panel."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QHBoxLayout(self)

        # Search type selector
        layout.addWidget(QLabel("Search by:"))
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Job Number", "Customer Name"])
        self.search_type_combo.currentTextChanged.connect(self.on_search_type_changed)
        layout.addWidget(self.search_type_combo)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter job number...")
        self.search_input.returnPressed.connect(self.on_search_clicked)
        layout.addWidget(self.search_input)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search_clicked)
        layout.addWidget(self.search_button)

        layout.addStretch()

    def on_search_type_changed(self, search_type: str):
        """
        Handle search type change.

        Args:
            search_type: New search type
        """
        if search_type == "Job Number":
            self.search_input.setPlaceholderText("Enter job number...")
        else:
            self.search_input.setPlaceholderText("Enter customer name...")

    def on_search_clicked(self):
        """Handle search button click."""
        search_value = self.search_input.text().strip()
        if not search_value:
            return

        search_type = self.search_type_combo.currentText()
        self.search_clicked.emit(search_type, search_value)

    def clear(self):
        """Clear search input."""
        self.search_input.clear()


class CombinedFilterSearchToolbar(QWidget):
    """Combined widget for date filtering and search controls in a single compact toolbar."""

    # Signals
    filter_clicked = pyqtSignal(DateRangeFilter)  # Emits date filter
    clear_clicked = pyqtSignal()  # Emits when clear button clicked
    search_clicked = pyqtSignal(str, str)  # Emits (search_type, search_value)

    def __init__(self, parent=None):
        """Initialize combined filter and search toolbar."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Date filter section
        layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.start_date_edit.setMinimumDate(QDate(1985, 1, 1))
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        self.start_date_edit.setSpecialValueText(" ")
        self.start_date_edit.clear()
        layout.addWidget(self.start_date_edit)

        layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.end_date_edit.setMinimumDate(QDate(1985, 1, 1))
        self.end_date_edit.setMaximumDate(QDate.currentDate())
        self.end_date_edit.setSpecialValueText(" ")
        self.end_date_edit.clear()
        layout.addWidget(self.end_date_edit)

        # Filter buttons
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.on_filter_clicked)
        layout.addWidget(self.filter_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.on_clear_clicked)
        layout.addWidget(self.clear_button)

        # Visual divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setLineWidth(1)
        layout.addWidget(divider)

        # Search section
        layout.addWidget(QLabel("Search:"))
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Job Number", "Customer Name"])
        self.search_type_combo.currentTextChanged.connect(self.on_search_type_changed)
        layout.addWidget(self.search_type_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter job number...")
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self.on_search_clicked)
        layout.addWidget(self.search_input, 1)  # Stretch factor 1

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search_clicked)
        layout.addWidget(self.search_button)

        layout.addStretch()

    def on_filter_clicked(self):
        """Handle filter button click."""
        # Get dates (None if not set)
        start_date = None
        if not self.start_date_edit.text().strip() == "":
            qdate = self.start_date_edit.date()
            start_date = date(qdate.year(), qdate.month(), qdate.day())

        end_date = None
        if not self.end_date_edit.text().strip() == "":
            qdate = self.end_date_edit.date()
            end_date = date(qdate.year(), qdate.month(), qdate.day())

        # Create filter
        date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)

        # Emit signal
        self.filter_clicked.emit(date_filter)

    def on_clear_clicked(self):
        """Handle clear button click."""
        self.start_date_edit.clear()
        self.end_date_edit.clear()
        self.clear_clicked.emit()

    def on_search_type_changed(self, search_type: str):
        """
        Handle search type change.

        Args:
            search_type: New search type
        """
        if search_type == "Job Number":
            self.search_input.setPlaceholderText("Enter job number...")
        else:
            self.search_input.setPlaceholderText("Enter customer name...")

    def on_search_clicked(self):
        """Handle search button click."""
        search_value = self.search_input.text().strip()
        if not search_value:
            return

        search_type = self.search_type_combo.currentText()
        self.search_clicked.emit(search_type, search_value)

    def clear_search(self):
        """Clear search input."""
        self.search_input.clear()
