"""Part detail view with tabbed interface for Inventory module."""

import csv
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextBrowser,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
from typing import List, Optional

from visual_order_lookup.database.models import Part, WhereUsed, PurchaseHistory


class PartDetailView(QWidget):
    """Tabbed view for part information display.

    Three tabs:
    1. Part Info - Master data in formatted HTML
    2. Where Used - Table of usage transactions
    3. Purchase History - Table of purchase orders
    """

    def __init__(self, parent=None):
        """Initialize part detail view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_part: Optional[Part] = None
        self.where_used_records: List[WhereUsed] = []
        self.purchase_history_records: List[PurchaseHistory] = []

        # Pagination state for where-used
        self.where_used_page = 0
        self.where_used_page_size = 50

        # Pagination state for purchase history
        self.purchase_history_page = 0
        self.purchase_history_page_size = 50

        self._setup_ui()

    def _setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab 1: Part Info (HTML display) with export button
        part_info_widget = QWidget()
        part_info_layout = QVBoxLayout(part_info_widget)
        part_info_layout.setContentsMargins(0, 0, 0, 0)

        self.part_info_browser = QTextBrowser()
        part_info_layout.addWidget(self.part_info_browser)

        # Export button for Part Info
        part_info_export_btn = QPushButton("Export as HTML")
        part_info_export_btn.clicked.connect(self._export_part_info)
        part_info_export_btn.setMaximumWidth(150)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(part_info_export_btn)
        part_info_layout.addLayout(btn_layout)

        self.tab_widget.addTab(part_info_widget, "Part Info")

        # Tab 2: Where Used (Table) with export button and pagination
        where_used_widget = QWidget()
        where_used_layout = QVBoxLayout(where_used_widget)
        where_used_layout.setContentsMargins(0, 0, 0, 0)

        self.where_used_table = QTableWidget()
        self.where_used_table.setColumnCount(6)
        self.where_used_table.setHorizontalHeaderLabels([
            "Date", "Order/WO", "Customer", "Quantity", "Warehouse", "Location"
        ])
        self.where_used_table.horizontalHeader().setStretchLastSection(True)
        self.where_used_table.setAlternatingRowColors(True)
        self.where_used_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.where_used_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        where_used_layout.addWidget(self.where_used_table)

        # Pagination controls for Where Used
        wu_pagination_layout = QHBoxLayout()

        self.where_used_page_label = QLabel("Page 0 of 0 (0 records)")
        wu_pagination_layout.addWidget(self.where_used_page_label)

        wu_pagination_layout.addStretch()

        self.where_used_first_btn = QPushButton("First")
        self.where_used_first_btn.clicked.connect(lambda: self._go_to_where_used_page(0))
        self.where_used_first_btn.setMaximumWidth(70)
        wu_pagination_layout.addWidget(self.where_used_first_btn)

        self.where_used_prev_btn = QPushButton("Previous")
        self.where_used_prev_btn.clicked.connect(self._previous_where_used_page)
        self.where_used_prev_btn.setMaximumWidth(80)
        wu_pagination_layout.addWidget(self.where_used_prev_btn)

        self.where_used_next_btn = QPushButton("Next")
        self.where_used_next_btn.clicked.connect(self._next_where_used_page)
        self.where_used_next_btn.setMaximumWidth(70)
        wu_pagination_layout.addWidget(self.where_used_next_btn)

        self.where_used_last_btn = QPushButton("Last")
        self.where_used_last_btn.clicked.connect(lambda: self._go_to_where_used_page(-1))
        self.where_used_last_btn.setMaximumWidth(70)
        wu_pagination_layout.addWidget(self.where_used_last_btn)

        wu_pagination_layout.addSpacing(20)

        # Export button for Where Used
        where_used_export_btn = QPushButton("Export All as CSV")
        where_used_export_btn.clicked.connect(self._export_where_used)
        where_used_export_btn.setMaximumWidth(150)
        wu_pagination_layout.addWidget(where_used_export_btn)

        where_used_layout.addLayout(wu_pagination_layout)

        self.tab_widget.addTab(where_used_widget, "Where Used")

        # Tab 3: Purchase History (Table) with export button and pagination
        purchase_history_widget = QWidget()
        purchase_history_layout = QVBoxLayout(purchase_history_widget)
        purchase_history_layout.setContentsMargins(0, 0, 0, 0)

        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(7)
        self.purchase_history_table.setHorizontalHeaderLabels([
            "PO Date", "PO Number", "Vendor", "Qty", "Unit Price", "Total", "Last Received"
        ])
        self.purchase_history_table.horizontalHeader().setStretchLastSection(True)
        self.purchase_history_table.setAlternatingRowColors(True)
        self.purchase_history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.purchase_history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        purchase_history_layout.addWidget(self.purchase_history_table)

        # Pagination controls for Purchase History
        ph_pagination_layout = QHBoxLayout()

        self.purchase_history_page_label = QLabel("Page 0 of 0 (0 records)")
        ph_pagination_layout.addWidget(self.purchase_history_page_label)

        ph_pagination_layout.addStretch()

        self.purchase_history_first_btn = QPushButton("First")
        self.purchase_history_first_btn.clicked.connect(lambda: self._go_to_purchase_history_page(0))
        self.purchase_history_first_btn.setMaximumWidth(70)
        ph_pagination_layout.addWidget(self.purchase_history_first_btn)

        self.purchase_history_prev_btn = QPushButton("Previous")
        self.purchase_history_prev_btn.clicked.connect(self._previous_purchase_history_page)
        self.purchase_history_prev_btn.setMaximumWidth(80)
        ph_pagination_layout.addWidget(self.purchase_history_prev_btn)

        self.purchase_history_next_btn = QPushButton("Next")
        self.purchase_history_next_btn.clicked.connect(self._next_purchase_history_page)
        self.purchase_history_next_btn.setMaximumWidth(70)
        ph_pagination_layout.addWidget(self.purchase_history_next_btn)

        self.purchase_history_last_btn = QPushButton("Last")
        self.purchase_history_last_btn.clicked.connect(lambda: self._go_to_purchase_history_page(-1))
        self.purchase_history_last_btn.setMaximumWidth(70)
        ph_pagination_layout.addWidget(self.purchase_history_last_btn)

        ph_pagination_layout.addSpacing(20)

        # Export button for Purchase History
        purchase_history_export_btn = QPushButton("Export All as CSV")
        purchase_history_export_btn.clicked.connect(self._export_purchase_history)
        purchase_history_export_btn.setMaximumWidth(150)
        ph_pagination_layout.addWidget(purchase_history_export_btn)

        purchase_history_layout.addLayout(ph_pagination_layout)

        self.tab_widget.addTab(purchase_history_widget, "Purchase History")

    def display_part_info(self, part: Part):
        """Display part master data in Part Info tab.

        Args:
            part: Part object to display
        """
        self.current_part = part

        # Generate HTML for part info
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 10px; }}
                h2 {{ color: #0d47a1; margin-bottom: 5px; }}
                .section {{ margin-bottom: 20px; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #000; }}
                table {{ border-collapse: collapse; width: 100%; }}
                td {{ padding: 5px; }}
                .header-row {{ background-color: #f0f0f0; }}
            </style>
        </head>
        <body>
            <h2>{part.part_number} - {part.description}</h2>

            <div class="section">
                <h3>General Information</h3>
                <table>
                    <tr><td class="label">Part Type:</td><td class="value">{part.part_type}</td></tr>
                    <tr><td class="label">Unit of Measure:</td><td class="value">{part.unit_of_measure}</td></tr>
                    <tr><td class="label">Material Code:</td><td class="value">{part.material_code or 'N/A'}</td></tr>
                    <tr><td class="label">Drawing ID:</td><td class="value">{part.drawing_id or 'N/A'}</td></tr>
                    <tr><td class="label">Drawing Rev:</td><td class="value">{part.drawing_revision or 'N/A'}</td></tr>
                    <tr><td class="label">Weight:</td><td class="value">{part.weight or 'N/A'} {part.weight_um or ''}</td></tr>
                </table>
            </div>

            <div class="section">
                <h3>Cost & Pricing</h3>
                <table>
                    <tr><td class="label">Material Cost:</td><td class="value">${part.unit_material_cost or 0:,.2f}</td></tr>
                    <tr><td class="label">Labor Cost:</td><td class="value">${part.unit_labor_cost or 0:,.2f}</td></tr>
                    <tr><td class="label">Burden Cost:</td><td class="value">${part.unit_burden_cost or 0:,.2f}</td></tr>
                    <tr class="header-row"><td class="label">Total Cost:</td><td class="value">{part.formatted_total_cost()}</td></tr>
                    <tr><td class="label">Unit Price:</td><td class="value">{part.formatted_unit_price()}</td></tr>
                </table>
            </div>

            <div class="section">
                <h3>Inventory Status</h3>
                <table>
                    <tr><td class="label">On Hand:</td><td class="value">{part.qty_on_hand or 0:,.2f}</td></tr>
                    <tr><td class="label">Available:</td><td class="value">{part.qty_available or 0:,.2f}</td></tr>
                    <tr><td class="label">On Order:</td><td class="value">{part.qty_on_order or 0:,.2f}</td></tr>
                    <tr><td class="label">In Demand:</td><td class="value">{part.qty_in_demand or 0:,.2f}</td></tr>
                </table>
            </div>

            <div class="section">
                <h3>Vendor Information</h3>
                <table>
                    <tr><td class="label">Preferred Vendor:</td><td class="value">{part.vendor_name or 'N/A'}</td></tr>
                    <tr><td class="label">Vendor ID:</td><td class="value">{part.vendor_id or 'N/A'}</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

        self.part_info_browser.setHtml(html)

    def display_where_used(self, records: List[WhereUsed]):
        """Display where-used records in table with pagination.

        Args:
            records: List of WhereUsed records
        """
        try:
            # Store records
            self.where_used_records = records if records else []
            self.where_used_page = 0  # Reset to first page

            # Refresh to show first page
            self._refresh_where_used_page()

        except Exception as e:
            import logging
            logging.error(f"Error displaying where-used records: {e}")
            # Clear table on error
            self.where_used_table.setRowCount(0)
            self.where_used_page_label.setText("Error loading data")

    def _refresh_where_used_page(self):
        """Refresh the where-used table to show current page."""
        try:
            # Safety check
            if not self.where_used_records:
                self.where_used_table.setRowCount(0)
                self.where_used_page_label.setText("Page 0 of 0 (0 records)")
                self.where_used_first_btn.setEnabled(False)
                self.where_used_prev_btn.setEnabled(False)
                self.where_used_next_btn.setEnabled(False)
                self.where_used_last_btn.setEnabled(False)
                return

            total_records = len(self.where_used_records)
            total_pages = max(1, (total_records + self.where_used_page_size - 1) // self.where_used_page_size)

            # Ensure page is within bounds
            if self.where_used_page >= total_pages:
                self.where_used_page = max(0, total_pages - 1)

            # Calculate start and end indices for current page
            start_idx = self.where_used_page * self.where_used_page_size
            end_idx = min(start_idx + self.where_used_page_size, total_records)
            page_records = self.where_used_records[start_idx:end_idx]

            # Update page label
            self.where_used_page_label.setText(
                f"Page {self.where_used_page + 1} of {total_pages} ({total_records} total records)"
            )

            # Enable/disable navigation buttons
            self.where_used_first_btn.setEnabled(self.where_used_page > 0)
            self.where_used_prev_btn.setEnabled(self.where_used_page > 0)
            self.where_used_next_btn.setEnabled(self.where_used_page < total_pages - 1)
            self.where_used_last_btn.setEnabled(self.where_used_page < total_pages - 1)

            # Clear existing rows first
            self.where_used_table.setRowCount(0)

            # Disable updates during bulk operations for better performance
            self.where_used_table.setUpdatesEnabled(False)
            self.where_used_table.setSortingEnabled(False)

            try:
                # Set row count for new page
                self.where_used_table.setRowCount(len(page_records))

                # Populate rows
                for row, record in enumerate(page_records):
                    try:
                        # Date
                        date_item = QTableWidgetItem(record.formatted_date() if hasattr(record, 'formatted_date') else str(record.transaction_date))
                        self.where_used_table.setItem(row, 0, date_item)

                        # Order/WO reference
                        ref_item = QTableWidgetItem(str(record.order_reference or ""))
                        self.where_used_table.setItem(row, 1, ref_item)

                        # Customer
                        cust_item = QTableWidgetItem(str(record.customer_name or "N/A"))
                        self.where_used_table.setItem(row, 2, cust_item)

                        # Quantity
                        qty_text = record.formatted_quantity() if hasattr(record, 'formatted_quantity') else str(record.quantity)
                        qty_item = QTableWidgetItem(qty_text)
                        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self.where_used_table.setItem(row, 3, qty_item)

                        # Warehouse
                        wh_item = QTableWidgetItem(str(record.warehouse_id or "N/A"))
                        self.where_used_table.setItem(row, 4, wh_item)

                        # Location
                        loc_item = QTableWidgetItem(str(record.location_id or "N/A"))
                        self.where_used_table.setItem(row, 5, loc_item)

                    except Exception as e:
                        import logging
                        logging.error(f"Error adding row {row}: {e}")
                        continue

                # Resize columns to content
                self.where_used_table.resizeColumnsToContents()

            finally:
                # Re-enable updates
                self.where_used_table.setUpdatesEnabled(True)
                self.where_used_table.setSortingEnabled(False)

        except Exception as e:
            import logging
            logging.error(f"Error refreshing where-used page: {e}")
            import traceback
            traceback.print_exc()
            self.where_used_table.setRowCount(0)
            self.where_used_page_label.setText(f"Error: {str(e)}")

    def _next_where_used_page(self):
        """Navigate to next page of where-used records."""
        total_pages = max(1, (len(self.where_used_records) + self.where_used_page_size - 1) // self.where_used_page_size)
        if self.where_used_page < total_pages - 1:
            self.where_used_page += 1
            self._refresh_where_used_page()

    def _previous_where_used_page(self):
        """Navigate to previous page of where-used records."""
        if self.where_used_page > 0:
            self.where_used_page -= 1
            self._refresh_where_used_page()

    def _go_to_where_used_page(self, page: int):
        """Navigate to specific page of where-used records.

        Args:
            page: Page number (0-indexed), or -1 for last page
        """
        total_pages = max(1, (len(self.where_used_records) + self.where_used_page_size - 1) // self.where_used_page_size)

        if page == -1:
            self.where_used_page = total_pages - 1
        else:
            self.where_used_page = max(0, min(page, total_pages - 1))

        self._refresh_where_used_page()

    def display_purchase_history(self, records: List[PurchaseHistory]):
        """Display purchase history records in table with pagination.

        Args:
            records: List of PurchaseHistory records
        """
        self.purchase_history_records = records
        self.purchase_history_page = 0  # Reset to first page
        self._refresh_purchase_history_page()

    def _refresh_purchase_history_page(self):
        """Refresh the purchase history table to show current page."""
        total_records = len(self.purchase_history_records)
        total_pages = max(1, (total_records + self.purchase_history_page_size - 1) // self.purchase_history_page_size)

        # Ensure page is within bounds
        if self.purchase_history_page >= total_pages:
            self.purchase_history_page = max(0, total_pages - 1)

        # Calculate start and end indices for current page
        start_idx = self.purchase_history_page * self.purchase_history_page_size
        end_idx = min(start_idx + self.purchase_history_page_size, total_records)
        page_records = self.purchase_history_records[start_idx:end_idx]

        # Update page label
        self.purchase_history_page_label.setText(
            f"Page {self.purchase_history_page + 1} of {total_pages} ({total_records} total records)"
        )

        # Enable/disable navigation buttons
        self.purchase_history_first_btn.setEnabled(self.purchase_history_page > 0)
        self.purchase_history_prev_btn.setEnabled(self.purchase_history_page > 0)
        self.purchase_history_next_btn.setEnabled(self.purchase_history_page < total_pages - 1)
        self.purchase_history_last_btn.setEnabled(self.purchase_history_page < total_pages - 1)

        # Disable updates during bulk operations for better performance
        self.purchase_history_table.setUpdatesEnabled(False)

        try:
            self.purchase_history_table.setRowCount(len(page_records))

            for row, record in enumerate(page_records):
                # PO Date
                self.purchase_history_table.setItem(row, 0, QTableWidgetItem(record.formatted_order_date()))

                # PO Number
                self.purchase_history_table.setItem(row, 1, QTableWidgetItem(record.po_number))

                # Vendor
                self.purchase_history_table.setItem(row, 2, QTableWidgetItem(record.vendor_name))

                # Quantity
                qty_item = QTableWidgetItem(record.formatted_quantity())
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.purchase_history_table.setItem(row, 3, qty_item)

                # Unit Price
                price_item = QTableWidgetItem(record.formatted_unit_price())
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.purchase_history_table.setItem(row, 4, price_item)

                # Total
                total_item = QTableWidgetItem(record.formatted_line_total())
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.purchase_history_table.setItem(row, 5, total_item)

                # Last Received
                self.purchase_history_table.setItem(row, 6, QTableWidgetItem(record.formatted_received_date()))

            # Resize columns to content
            self.purchase_history_table.resizeColumnsToContents()

        finally:
            # Re-enable updates
            self.purchase_history_table.setUpdatesEnabled(True)

    def _next_purchase_history_page(self):
        """Navigate to next page of purchase history records."""
        total_pages = max(1, (len(self.purchase_history_records) + self.purchase_history_page_size - 1) // self.purchase_history_page_size)
        if self.purchase_history_page < total_pages - 1:
            self.purchase_history_page += 1
            self._refresh_purchase_history_page()

    def _previous_purchase_history_page(self):
        """Navigate to previous page of purchase history records."""
        if self.purchase_history_page > 0:
            self.purchase_history_page -= 1
            self._refresh_purchase_history_page()

    def _go_to_purchase_history_page(self, page: int):
        """Navigate to specific page of purchase history records.

        Args:
            page: Page number (0-indexed), or -1 for last page
        """
        total_pages = max(1, (len(self.purchase_history_records) + self.purchase_history_page_size - 1) // self.purchase_history_page_size)

        if page == -1:
            self.purchase_history_page = total_pages - 1
        else:
            self.purchase_history_page = max(0, min(page, total_pages - 1))

        self._refresh_purchase_history_page()

    def _export_part_info(self):
        """Export Part Info tab as HTML file."""
        if not self.current_part:
            QMessageBox.warning(self, "No Data", "No part information to export.")
            return

        # Prompt for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Part Info",
            f"part_info_{self.current_part.part_number}.html",
            "HTML Files (*.html)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Get current HTML from browser
            html_content = self.part_info_browser.toHtml()

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Part information exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export part information:\n{str(e)}"
            )

    def _export_where_used(self):
        """Export Where Used tab as CSV file."""
        if not self.where_used_records:
            QMessageBox.warning(self, "No Data", "No where-used records to export.")
            return

        # Prompt for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Where Used",
            f"where_used_{self.current_part.part_number if self.current_part else 'unknown'}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    "Date", "Order/WO", "Customer", "Quantity", "Warehouse", "Location"
                ])

                # Write data rows
                for record in self.where_used_records:
                    writer.writerow([
                        record.formatted_date(),
                        record.order_reference,
                        record.customer_name or "N/A",
                        record.formatted_quantity(),
                        record.warehouse_id or "N/A",
                        record.location_id or "N/A"
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Where-used records exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export where-used records:\n{str(e)}"
            )

    def _export_purchase_history(self):
        """Export Purchase History tab as CSV file."""
        if not self.purchase_history_records:
            QMessageBox.warning(self, "No Data", "No purchase history records to export.")
            return

        # Prompt for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Purchase History",
            f"purchase_history_{self.current_part.part_number if self.current_part else 'unknown'}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    "PO Date", "PO Number", "Vendor", "Qty", "Unit Price", "Total", "Last Received"
                ])

                # Write data rows
                for record in self.purchase_history_records:
                    writer.writerow([
                        record.formatted_order_date(),
                        record.po_number,
                        record.vendor_name,
                        record.formatted_quantity(),
                        record.formatted_unit_price(),
                        record.formatted_line_total(),
                        record.formatted_received_date()
                    ])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Purchase history exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export purchase history:\n{str(e)}"
            )

    def clear(self):
        """Clear all displays and reset pagination."""
        self.part_info_browser.clear()
        self.where_used_table.setRowCount(0)
        self.purchase_history_table.setRowCount(0)
        self.current_part = None
        self.where_used_records = []
        self.purchase_history_records = []

        # Reset pagination state
        self.where_used_page = 0
        self.purchase_history_page = 0

        # Update pagination labels
        self.where_used_page_label.setText("Page 0 of 0 (0 records)")
        self.purchase_history_page_label.setText("Page 0 of 0 (0 records)")

        # Disable pagination buttons
        self.where_used_first_btn.setEnabled(False)
        self.where_used_prev_btn.setEnabled(False)
        self.where_used_next_btn.setEnabled(False)
        self.where_used_last_btn.setEnabled(False)
        self.purchase_history_first_btn.setEnabled(False)
        self.purchase_history_prev_btn.setEnabled(False)
        self.purchase_history_next_btn.setEnabled(False)
        self.purchase_history_last_btn.setEnabled(False)
