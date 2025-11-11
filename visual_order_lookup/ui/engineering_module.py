"""Engineering Module for BOM hierarchy display."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QMenu
)
from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction

from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.bom_service import BOMService
from visual_order_lookup.services.order_service import DatabaseWorker
from visual_order_lookup.ui.job_search_panel import JobSearchPanel
from visual_order_lookup.ui.bom_tree_view import BOMTreeView
from visual_order_lookup.ui.dialogs import LoadingDialog, ErrorHandler


logger = logging.getLogger(__name__)


class EngineeringModuleWidget(QWidget):
    """Engineering module widget (Manufacturing Window).

    Provides job search with hierarchical BOM tree using lazy loading.
    """

    # Signal for cross-module navigation
    switch_to_inventory = pyqtSignal(str)  # part_number

    def __init__(self, db_connection: DatabaseConnection, parent=None):
        """Initialize engineering module.

        Args:
            db_connection: Database connection instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize services
        self.db_connection = db_connection
        self.bom_service = BOMService(db_connection)

        # Worker thread for async operations
        self.worker_thread = None
        self.worker = None

        # Loading dialog
        self.loading_dialog = None

        # Current job number
        self.current_job_number = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search panel
        self.search_panel = JobSearchPanel()
        layout.addWidget(self.search_panel)

        # Job header label
        self.job_header_label = QLabel("")
        self.job_header_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(self.job_header_label)

        # Filter panel
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by part number or description...")
        self.filter_input.setMaximumWidth(300)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_input)

        clear_filter_btn = QPushButton("Clear Filter")
        clear_filter_btn.clicked.connect(self._on_clear_filter)
        clear_filter_btn.setMaximumWidth(100)
        filter_layout.addWidget(clear_filter_btn)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(self._on_expand_all)
        self.expand_all_btn.setMaximumWidth(100)
        self.expand_all_btn.setEnabled(False)
        btn_layout.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(self._on_collapse_all)
        self.collapse_all_btn.setMaximumWidth(100)
        self.collapse_all_btn.setEnabled(False)
        btn_layout.addWidget(self.collapse_all_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # BOM tree view
        self.bom_tree = BOMTreeView()
        self.bom_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bom_tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.bom_tree)

    def _setup_connections(self):
        """Set up signal connections."""
        self.search_panel.search_requested.connect(self._on_search_job)
        self.bom_tree.load_children.connect(self._on_load_children)

    def cleanup_worker_thread(self):
        """Called when thread finishes to clean up references."""
        self.worker_thread = None
        self.worker = None

    def _on_search_job(self, job_number: str):
        """Handle job search request.

        Args:
            job_number: Job number to search for
        """
        logger.info(f"Searching for job: {job_number}")
        self.current_job_number = job_number

        # Clear existing tree
        self.bom_tree.clear_tree()
        self.job_header_label.clear()
        self.expand_all_btn.setEnabled(False)
        self.collapse_all_btn.setEnabled(False)

        # Show loading dialog
        self.loading_dialog = LoadingDialog(f"Loading job {job_number}...", self)
        self.loading_dialog.show()

        # Load job info and assemblies
        self.worker_thread = QThread()
        self.worker = DatabaseWorker(
            self.bom_service, "get_bom_assemblies", job_number=job_number
        )

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_assemblies_loaded)
        self.worker.error.connect(self._on_search_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def _on_assemblies_loaded(self, assemblies):
        """Handle successful assembly load.

        Args:
            assemblies: List of BOMNode assemblies
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if assemblies and len(assemblies) > 0:
            logger.info(f"Loaded {len(assemblies)} assemblies")

            # Load job info for header
            self._load_job_info()

            # Add assemblies to tree
            for assembly in assemblies:
                self.bom_tree.add_assembly(assembly)

            # Enable buttons
            self.expand_all_btn.setEnabled(True)
            self.collapse_all_btn.setEnabled(True)

        else:
            ErrorHandler.show_not_found("Job", self.current_job_number, self)
            self.bom_tree.clear_tree()

    def _on_search_error(self, error_message: str):
        """Handle job search error.

        Args:
            error_message: Error message from worker
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if "connection" in error_message.lower():
            ErrorHandler.show_connection_error(self)
        elif "timeout" in error_message.lower():
            ErrorHandler.show_timeout_error(self)
        else:
            ErrorHandler.show_general_error(error_message, self)

        logger.error(f"Error searching for job: {error_message}")

    def _load_job_info(self):
        """Load job information for header display."""
        if not self.current_job_number:
            return

        self.worker_thread = QThread()
        self.worker = DatabaseWorker(
            self.bom_service, "get_job_info", job_number=self.current_job_number
        )

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_job_info_loaded)
        self.worker.error.connect(lambda e: logger.error(f"Error loading job info: {e}"))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def _on_job_info_loaded(self, job):
        """Handle successful job info load.

        Args:
            job: Job object or None
        """
        if job:
            self.job_header_label.setText(job.formatted_header())

    def _on_load_children(self, job_number: str, lot_id: str):
        """Handle lazy loading of assembly children.

        Args:
            job_number: Job number
            lot_id: Assembly lot ID to expand
        """
        logger.debug(f"Loading children for {job_number}/{lot_id}")

        # Find the parent item in tree
        parent_item = self._find_item_by_lot_id(lot_id)
        if not parent_item:
            logger.warning(f"Could not find parent item for lot {lot_id}")
            return

        # Load parts asynchronously
        self.worker_thread = QThread()
        self.worker = DatabaseWorker(
            self.bom_service, "get_assembly_parts",
            job_number=job_number, lot_id=lot_id
        )

        # Store parent_item for callback
        self.worker.parent_item = parent_item

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_parts_loaded)
        self.worker.error.connect(lambda e: logger.error(f"Error loading parts: {e}"))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def _on_parts_loaded(self, parts):
        """Handle successful parts load.

        Args:
            parts: List of BOMNode parts
        """
        if hasattr(self.worker, 'parent_item'):
            parent_item = self.worker.parent_item
            self.bom_tree.add_parts_to_assembly(parent_item, parts)
            logger.debug(f"Added {len(parts)} parts to assembly")

    def _find_item_by_lot_id(self, lot_id: str):
        """Find tree item by lot ID.

        Args:
            lot_id: Lot ID to search for

        Returns:
            QTreeWidgetItem or None
        """
        for item, node in self.bom_tree.node_data.items():
            if node.lot_id == lot_id:
                return item
        return None

    def _on_expand_all(self):
        """Handle Expand All button."""
        if not self.current_job_number:
            return

        # Count total nodes
        assembly_count = self.bom_tree.topLevelItemCount()

        # Warn if large job
        if assembly_count > 30:
            reply = QMessageBox.question(
                self,
                "Large Job Warning",
                f"This job has {assembly_count} assemblies which may contain many parts.\n"
                "Loading the full hierarchy may take 5-10 seconds.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Show loading dialog
        self.loading_dialog = LoadingDialog("Loading full BOM hierarchy...", self)
        self.loading_dialog.show()

        # Load full hierarchy
        self.worker_thread = QThread()
        self.worker = DatabaseWorker(
            self.bom_service, "get_bom_hierarchy", job_number=self.current_job_number
        )

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_hierarchy_loaded)
        self.worker.error.connect(self._on_hierarchy_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker_thread)

        self.worker_thread.start()

    def _on_hierarchy_loaded(self, nodes):
        """Handle full hierarchy load.

        Args:
            nodes: List of all BOMNode objects
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        # Rebuild tree with full hierarchy
        self.bom_tree.clear_tree()

        # Group nodes by parent
        assemblies = [n for n in nodes if n.depth == 0]
        for assembly in assemblies:
            item = self.bom_tree.add_assembly(assembly)
            self._add_children_recursive(item, nodes, assembly.lot_id)

        # Expand all
        self.bom_tree.expand_all_items()

        logger.info(f"Loaded full hierarchy: {len(nodes)} nodes")

    def _add_children_recursive(self, parent_item, all_nodes, parent_lot_id):
        """Recursively add children to tree item.

        Args:
            parent_item: Parent QTreeWidgetItem
            all_nodes: All BOMNode objects
            parent_lot_id: Parent's LOT_ID
        """
        children = [n for n in all_nodes if n.base_lot_id == parent_lot_id]
        if children:
            self.bom_tree.add_parts_to_assembly(parent_item, children)

            # Recursively add grandchildren
            for i, child in enumerate(children):
                child_item = parent_item.child(i)
                if child.is_assembly:
                    self._add_children_recursive(child_item, all_nodes, child.lot_id)

    def _on_hierarchy_error(self, error_message: str):
        """Handle hierarchy load error.

        Args:
            error_message: Error message
        """
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        ErrorHandler.show_general_error(f"Failed to load full hierarchy:\n{error_message}", self)

    def _on_collapse_all(self):
        """Handle Collapse All button."""
        self.bom_tree.collapse_all_items()

    def _on_filter_changed(self, text: str):
        """Handle filter text change.

        Args:
            text: Filter text
        """
        self.bom_tree.filter_by_text(text)

    def _on_clear_filter(self):
        """Handle Clear Filter button."""
        self.filter_input.clear()
        self.bom_tree.clear_filter()

    def _on_context_menu(self, position):
        """Handle context menu request.

        Args:
            position: Mouse position
        """
        # Get selected node
        selected_node = self.bom_tree.get_selected_node()
        if not selected_node:
            return

        # Create context menu
        menu = QMenu(self)

        # Copy Part Number action
        copy_action = QAction("Copy Part Number", self)
        copy_action.triggered.connect(lambda: self._copy_part_number(selected_node.part_id))
        menu.addAction(copy_action)

        # Show Part Details action (switch to Inventory module)
        details_action = QAction("Show Part Details", self)
        details_action.triggered.connect(lambda: self.switch_to_inventory.emit(selected_node.part_id))
        menu.addAction(details_action)

        # Show menu
        menu.exec(self.bom_tree.viewport().mapToGlobal(position))

    def _copy_part_number(self, part_number: str):
        """Copy part number to clipboard.

        Args:
            part_number: Part number to copy
        """
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(part_number)

        logger.info(f"Copied part number to clipboard: {part_number}")
