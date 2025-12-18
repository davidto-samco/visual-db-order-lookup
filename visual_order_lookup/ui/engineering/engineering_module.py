"""Engineering Module for Work Order Hierarchy Viewer.

This module provides:
- Search work orders by BASE_ID
- Display work order list results
- Show hierarchical tree view of selected work order
- Export work order data to CSV
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSplitter,
    QMessageBox, QToolBar, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.work_order_service import WorkOrderService, WorkOrderServiceError
from visual_order_lookup.ui.engineering.work_order_tree_widget import WorkOrderTreeWidget

logger = logging.getLogger(__name__)


class EngineeringModule(QWidget):
    """Engineering module widget for work order hierarchy viewing.

    Provides BASE_ID search with result list and hierarchical tree display.
    Read-only access to work order data from Visual database.
    """

    def __init__(self, db_connection: DatabaseConnection, parent=None):
        """Initialize Engineering module.

        Args:
            db_connection: Database connection instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize service
        self.db_connection = db_connection
        self.service = WorkOrderService(db_connection)

        # Current state
        self.current_work_orders = []

        self._setup_ui()
        self._connect_signals()

        logger.info("Engineering module initialized")

    def _setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Search panel (T036)
        search_layout = QHBoxLayout()

        search_label = QLabel("BASE_ID:")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter BASE_ID (e.g., 8113)")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_text_changed)  # Uppercase conversion
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(self.search_button)

        search_layout.addStretch()

        layout.addLayout(search_layout)

        # Create splitter for results table and tree view
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results table (T040)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Work Order ID",
            "Date Created",
            "Status",
            "Part Description"
        ])
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setMinimumHeight(150)

        splitter.addWidget(self.results_table)

        # Tree view panel
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar for tree actions (T067, T068, T072)
        toolbar = QToolBar()

        self.expand_all_action = QAction("Expand All", self)
        self.expand_all_action.triggered.connect(self._on_expand_all)
        toolbar.addAction(self.expand_all_action)

        self.collapse_all_action = QAction("Collapse All", self)
        self.collapse_all_action.triggered.connect(self._on_collapse_all)
        toolbar.addAction(self.collapse_all_action)

        toolbar.addSeparator()

        self.export_csv_action = QAction("Export to CSV", self)
        self.export_csv_action.triggered.connect(self._on_export_csv)
        toolbar.addAction(self.export_csv_action)

        toolbar.addSeparator()

        self.toggle_view_action = QAction("Detailed View", self)
        self.toggle_view_action.setCheckable(True)
        self.toggle_view_action.setChecked(False)  # Start in simplified view
        self.toggle_view_action.triggered.connect(self._on_toggle_view)
        toolbar.addAction(self.toggle_view_action)

        tree_layout.addWidget(toolbar)

        # Stacked widget to hold both tree views (T045)
        # This allows us to keep both trees in memory and swap between them
        # without losing expansion state, scroll position, etc.
        self.tree_stack = QStackedWidget()

        # Simplified view tree (index 0)
        self.simplified_tree = WorkOrderTreeWidget(self.service)
        self.simplified_tree.set_detailed_view(False)
        self.tree_stack.addWidget(self.simplified_tree)

        # Detailed view tree (index 1)
        self.detailed_tree = WorkOrderTreeWidget(self.service)
        self.detailed_tree.set_detailed_view(True)
        self.tree_stack.addWidget(self.detailed_tree)

        # Start with simplified view visible
        self.tree_stack.setCurrentIndex(0)

        tree_layout.addWidget(self.tree_stack)

        splitter.addWidget(tree_container)

        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Table
        splitter.setStretchFactor(1, 2)  # Tree

        layout.addWidget(splitter)

        logger.debug("Engineering module UI setup complete")

    @property
    def current_tree(self) -> WorkOrderTreeWidget:
        """Get the currently active tree widget based on view mode.

        Returns:
            The active tree widget (simplified or detailed)
        """
        return self.tree_stack.currentWidget()

    def _connect_signals(self):
        """Connect widget signals."""
        # T038: Enter key binding for search
        self.search_input.returnPressed.connect(self._on_search_clicked)

        # T042: Row selection handling
        self.results_table.itemSelectionChanged.connect(self._on_row_selected)

    def _on_search_text_changed(self, text: str):
        """Handle search text change - convert to uppercase.

        T036: Uppercase auto-conversion
        """
        # Convert to uppercase automatically
        cursor_pos = self.search_input.cursorPosition()
        self.search_input.blockSignals(True)
        self.search_input.setText(text.upper())
        self.search_input.setCursorPosition(cursor_pos)
        self.search_input.blockSignals(False)

    def _on_search_clicked(self):
        """Handle search button click.

        T037: Search work orders with loading indicator
        T039: Error handling for invalid patterns
        """
        base_id_pattern = self.search_input.text().strip()

        # Validation (T039)
        if not base_id_pattern:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a BASE_ID to search."
            )
            return

        if len(base_id_pattern) > 30:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "BASE_ID cannot exceed 30 characters."
            )
            return

        logger.info(f"Searching for work orders: {base_id_pattern}")

        # Disable search during query
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")

        try:
            # Search work orders (T037)
            results = self.service.search_work_orders(base_id_pattern, limit=1000)

            # Populate results table (T041)
            self._populate_results_table(results)

            logger.info(f"Found {len(results)} work orders")

        except WorkOrderServiceError as e:
            logger.error(f"Search error: {e}")
            QMessageBox.critical(
                self,
                "Search Error",
                f"Failed to search work orders:\n{str(e)}"
            )
        finally:
            # Re-enable search
            self.search_button.setEnabled(True)
            self.search_button.setText("Search")

    def _populate_results_table(self, results: list):
        """Populate results table with work order list.

        T041: Implement populate_work_order_list
        T043: Format date, status, quantity
        T044: Show "No results found" message
        """
        self.current_work_orders = results
        self.results_table.setRowCount(0)

        if not results:
            # T044: No results found
            QMessageBox.information(
                self,
                "No Results",
                "No work orders found matching that BASE_ID."
            )
            return

        self.results_table.setRowCount(len(results))

        for row, wo in enumerate(results):
            # Column 0: Work Order ID (T043)
            id_item = QTableWidgetItem(wo.formatted_id())
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 0, id_item)

            # Column 1: Date Created (T043: MM/DD/YYYY format)
            date_str = wo.create_date.strftime("%m/%d/%Y") if wo.create_date else ""
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 1, date_item)

            # Column 2: Status (T043: [C] prefix format)
            status_item = QTableWidgetItem(wo.formatted_status())
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 2, status_item)

            # Column 3: Part Description
            desc_item = QTableWidgetItem(wo.part_description or wo.part_id or "")
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 3, desc_item)

        # Auto-resize columns
        self.results_table.resizeColumnsToContents()

    def _on_row_selected(self):
        """Handle row selection - load selected work order into tree.

        T042: Row selection handling
        """
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self.current_work_orders):
            work_order = self.current_work_orders[row]
            logger.info(f"Loading work order: {work_order.formatted_id()}")

            try:
                # Load full work order with counts
                full_wo = self.service.get_work_order_header(
                    work_order.base_id,
                    work_order.lot_id,
                    work_order.sub_id
                )

                # Load into BOTH tree widgets (T047)
                # This allows seamless toggling between views without reloading
                self.simplified_tree.load_work_order(full_wo)
                self.detailed_tree.load_work_order(full_wo)

            except WorkOrderServiceError as e:
                logger.error(f"Error loading work order: {e}")
                QMessageBox.critical(
                    self,
                    "Load Error",
                    f"Failed to load work order details:\n{str(e)}"
                )

    def _on_expand_all(self):
        """Handle Expand All button click.

        T069: Implement expand_all()
        T071: Progress indicator for large trees
        """
        logger.debug("Expanding all tree nodes")

        # T071: Show progress for large operations
        self.expand_all_action.setEnabled(False)
        self.expand_all_action.setText("Expanding...")

        try:
            self.current_tree.expand_all()
        finally:
            self.expand_all_action.setEnabled(True)
            self.expand_all_action.setText("Expand All")

    def _on_collapse_all(self):
        """Handle Collapse All button click.

        T070: Implement collapse_all()
        """
        logger.debug("Collapsing all tree nodes")
        self.current_tree.collapse_all()

    def _on_export_csv(self):
        """Handle Export to CSV button click.

        T073: Create export_tree_to_csv()
        """
        logger.debug("Exporting tree to CSV")

        try:
            self.current_tree.export_to_csv()
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export to CSV:\n{str(e)}"
            )

    def _on_toggle_view(self, checked: bool):
        """Handle view toggle button click.

        Args:
            checked: True for detailed view, False for simplified view
        """
        view_mode = "DETAILED" if checked else "SIMPLIFIED"
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"🔄 TOGGLING TO {view_mode} VIEW")
        logger.info(f"{'='*60}")
        logger.info(f"")

        # Update button text
        if checked:
            self.toggle_view_action.setText("Simplified View")
        else:
            self.toggle_view_action.setText("Detailed View")

        # Simply swap the visible tree widget (preserves expansion state)
        if checked:
            self.tree_stack.setCurrentIndex(1)  # Detailed view
            logger.info("Switched to detailed view tree (expansion state preserved)")
        else:
            self.tree_stack.setCurrentIndex(0)  # Simplified view
            logger.info("Switched to simplified view tree (expansion state preserved)")
