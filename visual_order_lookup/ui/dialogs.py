"""Dialog widgets for loading indicators and error messages."""

import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QMessageBox,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt


logger = logging.getLogger(__name__)


class LoadingDialog(QDialog):
    """Modal dialog showing loading progress."""

    def __init__(self, message: str = "Loading...", parent=None):
        """
        Initialize loading dialog.

        Args:
            message: Message to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Please Wait")
        self.setModal(True)
        self.setFixedWidth(400)
        self.setup_ui(message)

    def setup_ui(self, message: str):
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Message label
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Progress bar (indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

    def set_message(self, message: str):
        """
        Update loading message.

        Args:
            message: New message to display
        """
        self.label.setText(message)


class ErrorHandler:
    """Static methods for displaying error dialogs."""

    @staticmethod
    def show_connection_error(parent=None, retry_callback=None):
        """
        Show database connection error dialog.

        Args:
            parent: Parent widget
            retry_callback: Optional callback function to call on retry

        Returns:
            True if user wants to retry, False otherwise
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Connection Error")
        msg.setText("Unable to connect to Visual database")
        msg.setInformativeText(
            "Please check:\n"
            "• WLAN network connection\n"
            "• Database server is accessible (10.10.10.142:1433)\n"
            "• Database credentials in .env file are correct"
        )

        if retry_callback:
            retry_button = msg.addButton("Retry", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            return msg.clickedButton() == retry_button
        else:
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return False

    @staticmethod
    def show_timeout_error(parent=None):
        """
        Show query timeout error dialog.

        Args:
            parent: Parent widget
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Query Timeout")
        msg.setText("Database query timed out")
        msg.setInformativeText(
            "The query took longer than 30 seconds to complete.\n\n"
            "This may be due to:\n"
            "• Slow network connection\n"
            "• Heavy database server load\n"
            "• Large result set\n\n"
            "Please try again or narrow your search criteria."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    @staticmethod
    def show_not_found(item_type: str, item_value: str, parent=None):
        """
        Show item not found dialog.

        Args:
            item_type: Type of item (e.g., "Order", "Customer")
            item_value: Value that was searched for
            parent: Parent widget
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(f"{item_type} Not Found")
        msg.setText(f"No {item_type.lower()} found")
        msg.setInformativeText(f"Could not find {item_type.lower()}: {item_value}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    @staticmethod
    def show_validation_error(message: str, parent=None):
        """
        Show validation error dialog.

        Args:
            message: Error message to display
            parent: Parent widget
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Validation Error")
        msg.setText("Invalid input")
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    @staticmethod
    def show_general_error(error_message: str, parent=None):
        """
        Show general error dialog.

        Args:
            error_message: Error message to display
            parent: Parent widget
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred")
        msg.setInformativeText(error_message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    @staticmethod
    def show_info(title: str, message: str, parent=None):
        """
        Show informational dialog.

        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
