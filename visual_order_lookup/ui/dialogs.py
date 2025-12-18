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
    QLineEdit,
    QFormLayout,
    QCheckBox,
    QGroupBox,
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


class LoginDialog(QDialog):
    """Modal dialog for database login credentials."""

    def __init__(self, parent=None):
        """
        Initialize login dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Database Login")
        self.setModal(True)
        self.setFixedWidth(450)
        self.credentials = None
        self.remember_credentials = False
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header label
        header = QLabel("Connect to Visual Database")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Info label
        info = QLabel("Enter your database credentials to continue.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        # Form group
        form_group = QGroupBox("Database Connection")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Server input
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("e.g., 10.10.10.142,1433")
        self.server_input.setText("10.10.10.142,1433")
        form_layout.addRow("Server:", self.server_input)

        # Database input
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("e.g., SAMCO")
        self.database_input.setText("SAMCO")
        form_layout.addRow("Database:", self.database_input)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Database username")
        form_layout.addRow("Username:", self.username_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Database password")
        form_layout.addRow("Password:", self.password_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Remember credentials checkbox
        self.remember_checkbox = QCheckBox("Remember credentials (stored securely)")
        layout.addWidget(self.remember_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.login_button = QPushButton("Connect")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #106ebe; }"
        )
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)

        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        """Handle login button click."""
        server = self.server_input.text().strip()
        database = self.database_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validate inputs
        if not all([server, database, username, password]):
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please fill in all fields to continue."
            )
            return

        # Store credentials
        self.credentials = {
            'server': server,
            'database': database,
            'username': username,
            'password': password
        }
        self.remember_credentials = self.remember_checkbox.isChecked()

        # Accept dialog
        self.accept()

    def get_credentials(self):
        """
        Get entered credentials.

        Returns:
            dict: Dictionary containing server, database, username, password
            or None if dialog was cancelled
        """
        return self.credentials

    def get_remember_choice(self):
        """
        Get whether user wants to remember credentials.

        Returns:
            bool: True if credentials should be remembered
        """
        return self.remember_credentials


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
