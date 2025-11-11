"""BOM tree view with lazy loading for Engineering module."""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from typing import List, Optional

from visual_order_lookup.database.models import BOMNode


class BOMTreeView(QTreeWidget):
    """Tree widget for displaying BOM hierarchy with lazy loading."""

    load_children = pyqtSignal(str, str)  # job_number, lot_id

    def __init__(self, parent=None):
        """Initialize BOM tree view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

        # Store BOMNode data in tree items for lazy loading
        self.node_data = {}  # item -> BOMNode mapping

    def _setup_ui(self):
        """Set up user interface."""
        # Configure columns
        self.setColumnCount(4)
        self.setHeaderLabels(["Lot ID", "Sub ID", "Part Number", "Description"])

        # Column widths
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Styling
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)

    def _setup_connections(self):
        """Set up signal connections."""
        self.itemExpanded.connect(self._on_item_expanded)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion for lazy loading.

        Args:
            item: The tree item that was expanded
        """
        # Check if this item has a BOMNode associated with it
        if item not in self.node_data:
            return

        node = self.node_data[item]

        # If already loaded or not an assembly, do nothing
        if node.is_loaded or not node.is_assembly:
            return

        # Emit signal to load children
        self.load_children.emit(node.job_number, node.lot_id)

    def add_assembly(self, node: BOMNode) -> QTreeWidgetItem:
        """Add top-level assembly to tree.

        Args:
            node: BOMNode representing assembly

        Returns:
            The created tree item
        """
        item = QTreeWidgetItem(self)
        self._populate_item(item, node)

        # If it's an assembly, add dummy child for expand arrow
        if node.is_assembly and not node.is_loaded:
            dummy = QTreeWidgetItem(item)
            dummy.setText(0, "Loading...")

        return item

    def add_parts_to_assembly(
        self, parent_item: QTreeWidgetItem, parts: List[BOMNode]
    ):
        """Add parts as children of an assembly item.

        Args:
            parent_item: Parent tree item (assembly)
            parts: List of BOMNode parts to add
        """
        # Remove dummy child if present
        if parent_item.childCount() > 0:
            dummy = parent_item.child(0)
            if dummy.text(0) == "Loading...":
                parent_item.removeChild(dummy)

        # Add real parts
        for part in parts:
            item = QTreeWidgetItem(parent_item)
            self._populate_item(item, part)

            # If this part is also an assembly, add dummy child
            if part.is_assembly and not part.is_loaded:
                dummy = QTreeWidgetItem(item)
                dummy.setText(0, "Loading...")

        # Mark parent node as loaded
        if parent_item in self.node_data:
            self.node_data[parent_item].is_loaded = True

    def _populate_item(self, item: QTreeWidgetItem, node: BOMNode):
        """Populate tree item with BOMNode data.

        Args:
            item: Tree item to populate
            node: BOMNode data
        """
        item.setText(0, node.lot_id)
        item.setText(1, node.sub_id)
        item.setText(2, node.part_id)
        item.setText(3, node.part_description or "N/A")

        # Store node data
        self.node_data[item] = node

        # Apply color based on node type
        color = self._get_color_for_node(node)
        for col in range(4):
            item.setForeground(col, color)

    def _get_color_for_node(self, node: BOMNode) -> QColor:
        """Get color for node based on type.

        Args:
            node: BOMNode

        Returns:
            QColor for the row
        """
        color_name = node.display_color
        if color_name == "blue":
            return QColor(0, 0, 200)  # Blue for assemblies
        elif color_name == "red":
            return QColor(200, 0, 0)  # Red for purchased
        else:
            return QColor(0, 0, 0)  # Black for manufactured

    def expand_all_items(self):
        """Expand all tree items."""
        self.expandAll()

    def collapse_all_items(self):
        """Collapse all tree items."""
        self.collapseAll()

    def clear_tree(self):
        """Clear tree and node data."""
        self.clear()
        self.node_data.clear()

    def get_all_part_numbers(self) -> List[str]:
        """Get all part numbers in the tree.

        Returns:
            List of unique part numbers
        """
        part_numbers = set()
        for node in self.node_data.values():
            part_numbers.add(node.part_id)
        return sorted(list(part_numbers))

    def filter_by_text(self, search_text: str):
        """Filter tree items by search text.

        Highlights matching rows and hides non-matching ones.

        Args:
            search_text: Text to search for (part number or description)
        """
        if not search_text:
            # Show all items
            self._set_all_visible(True)
            return

        search_text = search_text.lower()

        # Iterate through all items
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            part_number = item.text(2).lower()
            description = item.text(3).lower()

            # Check if this item matches
            matches = search_text in part_number or search_text in description

            # Show/hide based on match
            item.setHidden(not matches)

            iterator += 1

    def clear_filter(self):
        """Clear filter and show all items."""
        self._set_all_visible(True)

    def _set_all_visible(self, visible: bool):
        """Set visibility for all items.

        Args:
            visible: True to show, False to hide
        """
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item.setHidden(not visible)
            iterator += 1

    def get_selected_node(self) -> Optional[BOMNode]:
        """Get BOMNode for currently selected item.

        Returns:
            BOMNode or None if no selection
        """
        selected = self.selectedItems()
        if selected:
            return self.node_data.get(selected[0])
        return None
