"""Main application entry point."""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from visual_order_lookup.ui.main_window import MainWindow
from visual_order_lookup.ui.dialogs import ErrorHandler


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
