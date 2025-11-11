"""Job search panel for Engineering module."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal


class JobSearchPanel(QWidget):
    """Search panel for job number lookups."""

    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize job search panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up user interface."""
        layout = QHBoxLayout(self)

        # Label
        label = QLabel("Job Number:")
        layout.addWidget(label)

        # Input field
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("Enter job number (e.g., 8113)")
        self.job_input.setMaximumWidth(200)
        self.job_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.job_input)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search)
        self.search_button.setMaximumWidth(100)
        layout.addWidget(self.search_button)

        # Spacer to push everything left
        layout.addStretch()

    def _on_search(self):
        """Handle search button click or Enter key."""
        job_number = self.job_input.text().strip()
        if job_number:
            self.search_requested.emit(job_number)

    def clear(self):
        """Clear search input."""
        self.job_input.clear()
