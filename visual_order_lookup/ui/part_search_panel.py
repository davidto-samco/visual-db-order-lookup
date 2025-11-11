"""Part search panel for Inventory module."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class PartSearchPanel(QWidget):
    """Search panel for part number lookups.

    Provides a simple search interface with part number input and search button.
    """

    # Signal emitted when search is requested
    search_requested = pyqtSignal(str)  # part_number

    def __init__(self, parent=None):
        """Initialize part search panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Label
        label = QLabel("Part Number:")
        layout.addWidget(label)

        # Part number input
        self.part_input = QLineEdit()
        self.part_input.setPlaceholderText("Enter part number (e.g., F0195)")
        self.part_input.setMaxLength(30)
        self.part_input.setMinimumWidth(200)
        layout.addWidget(self.part_input)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setMinimumWidth(100)
        layout.addWidget(self.search_button)

        # Add stretch to push controls to the left
        layout.addStretch()

        # Connect signals
        self.search_button.clicked.connect(self._on_search)
        self.part_input.returnPressed.connect(self._on_search)

    def _on_search(self):
        """Handle search button click or Enter key."""
        part_number = self.part_input.text().strip()
        if part_number:
            self.search_requested.emit(part_number)

    def clear(self):
        """Clear search input."""
        self.part_input.clear()
        self.part_input.setFocus()

    def set_part_number(self, part_number: str):
        """Set part number in search input.

        Args:
            part_number: Part number to set
        """
        self.part_input.setText(part_number)
