"""Main application entry point."""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from visual_order_lookup.ui.main_window import MainWindow
from visual_order_lookup.ui.dialogs import ErrorHandler, LoginDialog
from visual_order_lookup.utils.config import Config, set_config, has_env_file
from visual_order_lookup.utils.credential_store import CredentialStore


logger = logging.getLogger(__name__)


def load_stylesheet(app: QApplication) -> None:
    """Load and apply Visual legacy stylesheet."""
    try:
        # Get stylesheet path
        stylesheet_path = Path(__file__).parent / "resources" / "styles" / "visual_legacy.qss"

        if stylesheet_path.exists():
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                app.setStyleSheet(stylesheet)
                logger.info("Visual legacy stylesheet applied successfully")
        else:
            logger.warning(f"Stylesheet not found: {stylesheet_path}")
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {e}")
        # Continue without stylesheet


def get_database_credentials(app: QApplication) -> Config:
    """
    Get database credentials from .env file, saved credentials, or login dialog.

    Args:
        app: QApplication instance

    Returns:
        Config instance with database credentials

    Raises:
        SystemExit: If user cancels login dialog
    """
    # First, check if .env file exists
    if has_env_file():
        logger.info("Loading configuration from .env file")
        return Config()

    # No .env file - try to load saved credentials
    saved_creds = CredentialStore.load_credentials()
    if saved_creds:
        logger.info("Loading saved credentials from Windows Credential Manager")
        try:
            config = Config(manual_credentials=saved_creds)
            return config
        except Exception as e:
            logger.warning(f"Failed to use saved credentials: {e}")
            # Fall through to login dialog

    # No .env file and no saved credentials - show login dialog
    while True:
        logger.info("Showing login dialog")
        login_dialog = LoginDialog()

        if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
            # User cancelled login
            logger.info("User cancelled login")
            sys.exit(0)

        credentials = login_dialog.get_credentials()
        if not credentials:
            continue

        # Try to create config with these credentials
        try:
            config = Config(manual_credentials=credentials)

            # If user wants to remember credentials, save them
            if login_dialog.get_remember_choice():
                if CredentialStore.is_available():
                    success = CredentialStore.save_credentials(
                        credentials['server'],
                        credentials['database'],
                        credentials['username'],
                        credentials['password']
                    )
                    if success:
                        logger.info("Credentials saved to Windows Credential Manager")
                    else:
                        logger.warning("Failed to save credentials")
                else:
                    QMessageBox.warning(
                        None,
                        "Cannot Save Credentials",
                        "Credential storage is not available on this system.\n\n"
                        "Install the 'keyring' package to enable this feature."
                    )

            return config

        except Exception as e:
            logger.error(f"Failed to create config with manual credentials: {e}")
            QMessageBox.critical(
                None,
                "Configuration Error",
                f"Failed to configure database connection:\n\n{str(e)}"
            )
            # Loop back to login dialog


def main():
    """Main application entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Visual Order Lookup")
    app.setOrganizationName("Spare Parts Department")

    # Load Visual legacy stylesheet
    load_stylesheet(app)

    try:
        # Get database credentials (from .env, saved credentials, or login dialog)
        config = get_database_credentials(app)
        set_config(config)

        # Create and show main window
        window = MainWindow()
        window.show()

        # Start event loop
        sys.exit(app.exec())

    except FileNotFoundError as e:
        # Configuration file not found
        ErrorHandler.show_general_error(
            "Configuration file not found.\n\n"
            "Please create a .env file based on .env.example\n"
            "in the same directory as the application."
        )
        sys.exit(1)

    except Exception as e:
        # Unexpected error
        logger.exception("Fatal error starting application")
        ErrorHandler.show_general_error(
            f"Failed to start application:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
