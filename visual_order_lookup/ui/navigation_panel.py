"""Navigation Panel for multi-module application.

Provides left-hand navigation with three module options: Sales, Inventory, Engineering.
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import QSize


class NavigationPanel(QListWidget):
    """Left navigation panel for module selection.

    Fixed width (200px) vertical list with three module options.
    Visual indication of active module via selected item styling.
    """

    def __init__(self, parent=None):
        """Initialize navigation panel with three module items.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Configure list widget
        self.setFixedWidth(200)
        self.setIconSize(QSize(32, 32))
        self.setSpacing(5)

        # Add three module items
        # TODO: Add icons when available (sales.svg, inventory.svg, engineering.svg)
        sales_item = QListWidgetItem("Sales")
        inventory_item = QListWidgetItem("Inventory")
        engineering_item = QListWidgetItem("Engineering")

        self.addItem(sales_item)
        self.addItem(inventory_item)
        self.addItem(engineering_item)

        # Set default selection (Sales module)
        self.setCurrentRow(0)

        # Configure selection behavior
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

    def get_current_module_index(self) -> int:
        """Get index of currently selected module.

        Returns:
            int: Index (0=Sales, 1=Inventory, 2=Engineering)
        """
        return self.currentRow()

    def set_module_index(self, index: int):
        """Set the currently selected module by index.

        Args:
            index: Module index (0=Sales, 1=Inventory, 2=Engineering)
        """
        if 0 <= index < self.count():
            self.setCurrentRow(index)
