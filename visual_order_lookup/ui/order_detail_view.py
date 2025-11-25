"""Order detail view widget for displaying complete order acknowledgements."""

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTextBrowser,
    QLabel,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtGui import QPageSize, QPageLayout, QTextDocument

from visual_order_lookup.database.models import OrderHeader
from visual_order_lookup.services.report_service import ReportService


logger = logging.getLogger(__name__)


class OrderDetailView(QWidget):
    """Widget for displaying order acknowledgement details."""

    def __init__(self, parent=None):
        """Initialize order detail view."""
        super().__init__(parent)
        self.current_order = None
        self.report_service = ReportService()
        self.setup_ui()

    def setup_ui(self):
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Header with action buttons
        header_layout = QHBoxLayout()

        # Order header label
        self.header_label = QLabel("Order Details")
        self.header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(self.header_label)

        header_layout.addStretch()

        # Print Preview button
        self.print_preview_button = QPushButton("Print Preview")
        self.print_preview_button.clicked.connect(self.show_print_preview)
        self.print_preview_button.setEnabled(False)
        header_layout.addWidget(self.print_preview_button)

        # Print button
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_order)
        self.print_button.setEnabled(False)
        header_layout.addWidget(self.print_button)

        # Save as PDF button
        self.pdf_button = QPushButton("Save as PDF")
        self.pdf_button.clicked.connect(self.save_as_pdf)
        self.pdf_button.setEnabled(False)
        header_layout.addWidget(self.pdf_button)

        layout.addLayout(header_layout)

        # Main content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Order header section (top section with customer info, dates, etc.)
        header_group = QGroupBox("Order Information")
        header_grid = QGridLayout()
        header_grid.setHorizontalSpacing(20)
        header_grid.setVerticalSpacing(8)

        # Row 0: Order Date, Job Number, Customer PO
        header_grid.addWidget(QLabel("Order Date:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.order_date_value = QLabel("-")
        header_grid.addWidget(self.order_date_value, 0, 1)

        header_grid.addWidget(QLabel("Job Number:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        self.job_number_value = QLabel("-")
        self.job_number_value.setStyleSheet("font-weight: bold;")
        header_grid.addWidget(self.job_number_value, 0, 3)

        header_grid.addWidget(QLabel("Customer PO:"), 0, 4, Qt.AlignmentFlag.AlignRight)
        self.customer_po_value = QLabel("-")
        header_grid.addWidget(self.customer_po_value, 0, 5)

        # Row 1: Customer, Status, FOB
        header_grid.addWidget(QLabel("Customer:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.customer_value = QLabel("-")
        header_grid.addWidget(self.customer_value, 1, 1, 1, 2)

        header_grid.addWidget(QLabel("Status:"), 1, 3, Qt.AlignmentFlag.AlignRight)
        self.status_value = QLabel("-")
        header_grid.addWidget(self.status_value, 1, 4)

        header_grid.addWidget(QLabel("FOB:"), 1, 5, Qt.AlignmentFlag.AlignRight)
        self.fob_value = QLabel("-")
        header_grid.addWidget(self.fob_value, 1, 6)

        # Row 2: Contact, Ship Via, Currency
        header_grid.addWidget(QLabel("Contact:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.contact_value = QLabel("-")
        header_grid.addWidget(self.contact_value, 2, 1, 1, 2)

        header_grid.addWidget(QLabel("Ship Via:"), 2, 3, Qt.AlignmentFlag.AlignRight)
        self.ship_via_value = QLabel("-")
        header_grid.addWidget(self.ship_via_value, 2, 4)

        header_grid.addWidget(QLabel("Currency:"), 2, 5, Qt.AlignmentFlag.AlignRight)
        self.currency_value = QLabel("-")
        header_grid.addWidget(self.currency_value, 2, 6)

        # Row 3: Desired Ship Date, Carrier
        header_grid.addWidget(QLabel("Desired Ship Date:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.desired_ship_date_value = QLabel("-")
        header_grid.addWidget(self.desired_ship_date_value, 3, 1)

        header_grid.addWidget(QLabel("Carrier:"), 3, 3, Qt.AlignmentFlag.AlignRight)
        self.carrier_value = QLabel("-")
        header_grid.addWidget(self.carrier_value, 3, 4)

        header_group.setLayout(header_grid)
        self.content_layout.addWidget(header_group)

        # Line items section (middle section with table)
        line_items_group = QGroupBox("Line Items")
        line_items_layout = QVBoxLayout()

        self.line_items_table = QTableWidget()
        self.line_items_table.setColumnCount(9)
        self.line_items_table.setHorizontalHeaderLabels([
            "Line", "Quantity", "Base/Lot ID", "Split ID",
            "Part ID", "Description", "Unit Price", "Extension", "Shipped"
        ])

        # Configure table
        self.line_items_table.setAlternatingRowColors(True)
        self.line_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.line_items_table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.line_items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Line
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Base/Lot
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Split
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Part ID
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Description
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Unit Price
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Extension
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Shipped

        line_items_layout.addWidget(self.line_items_table)
        line_items_group.setLayout(line_items_layout)
        self.content_layout.addWidget(line_items_group)

        # Totals section (bottom section)
        totals_frame = QFrame()
        totals_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.addStretch()

        # Grand Total
        totals_layout.addWidget(QLabel("Grand Total:"))
        self.grand_total_value = QLabel("$0.00")
        self.grand_total_value.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_layout.addWidget(self.grand_total_value)

        totals_layout.addSpacing(20)

        # Tax
        totals_layout.addWidget(QLabel("Tax:"))
        self.tax_value = QLabel("$0.00")
        totals_layout.addWidget(self.tax_value)

        totals_layout.addSpacing(20)

        # Freight
        totals_layout.addWidget(QLabel("Freight:"))
        self.freight_value = QLabel("$0.00")
        totals_layout.addWidget(self.freight_value)

        totals_layout.addSpacing(20)

        # Total
        totals_layout.addWidget(QLabel("Total:"))
        self.total_value = QLabel("$0.00")
        self.total_value.setStyleSheet("font-weight: bold; font-size: 12pt; color: #0066cc;")
        totals_layout.addWidget(self.total_value)

        self.content_layout.addWidget(totals_frame)

        layout.addWidget(self.content_widget)

        # Initially show placeholder
        self.show_placeholder()

    def show_placeholder(self):
        """Show placeholder message."""
        # Hide content and show placeholder in header label
        self.content_widget.setVisible(False)
        self.header_label.setText("Order Details - Select an order from the list")
        self.print_preview_button.setEnabled(False)
        self.print_button.setEnabled(False)
        self.pdf_button.setEnabled(False)

    def display_order(self, order: OrderHeader):
        """
        Display order acknowledgement.

        Args:
            order: OrderHeader object with complete order information
        """
        self.current_order = order
        self.header_label.setText(f"Order Acknowledgement - Job #{order.order_id}")

        try:
            # Show content widget
            self.content_widget.setVisible(True)

            # Populate order header fields
            self.order_date_value.setText(order.formatted_date())
            self.job_number_value.setText(str(order.order_id))
            self.customer_po_value.setText(order.customer_po_ref or "-")

            customer_name = order.customer.name if order.customer else "N/A"
            self.customer_value.setText(customer_name)

            # Note: status, fob, ship_via, carrier_id not in current OrderHeader model
            # These would need to be added to the database queries
            self.status_value.setText("-")  # Not available yet
            self.fob_value.setText("-")  # Not available yet
            self.contact_value.setText(order.contact_name or "-")
            self.ship_via_value.setText("-")  # Not available yet
            self.currency_value.setText(order.currency_id or "USD")
            self.desired_ship_date_value.setText(
                order.desired_ship_date.strftime("%m/%d/%Y") if order.desired_ship_date else "-"
            )
            self.carrier_value.setText("-")  # Not available yet

            # Populate line items table
            self.line_items_table.setRowCount(len(order.line_items))
            for row, item in enumerate(order.line_items):
                # Line number
                self.line_items_table.setItem(row, 0, QTableWidgetItem(str(item.line_number)))

                # Quantity
                self.line_items_table.setItem(row, 1, QTableWidgetItem(item.formatted_quantity()))

                # Base/Lot ID
                self.line_items_table.setItem(row, 2, QTableWidgetItem(item.base_lot_id or "-"))

                # Split ID (not in current model)
                self.line_items_table.setItem(row, 3, QTableWidgetItem("-"))

                # Part ID
                self.line_items_table.setItem(row, 4, QTableWidgetItem(item.part_id or "-"))

                # Description
                self.line_items_table.setItem(row, 5, QTableWidgetItem(item.description or "-"))

                # Unit Price
                self.line_items_table.setItem(row, 6, QTableWidgetItem(item.formatted_unit_price()))

                # Extension (Line Total)
                self.line_items_table.setItem(row, 7, QTableWidgetItem(item.formatted_line_total()))

                # Shipped Quantity (not in current model)
                self.line_items_table.setItem(row, 8, QTableWidgetItem("-"))

            # Populate totals
            self.grand_total_value.setText(order.formatted_total_amount())
            self.tax_value.setText(order.formatted_tax() if hasattr(order, 'formatted_tax') else "$0.00")
            self.freight_value.setText(order.formatted_freight() if hasattr(order, 'formatted_freight') else "$0.00")
            self.total_value.setText(order.formatted_total_amount())

            logger.info(f"Displaying order {order.order_id} with {len(order.line_items)} line items")

            # Enable print/export buttons
            self.print_preview_button.setEnabled(True)
            self.print_button.setEnabled(True)
            self.pdf_button.setEnabled(True)

        except Exception as e:
            logger.error(f"Error displaying order {order.order_id}: {e}")
            # Show error in header
            self.header_label.setText(f"Error displaying order {order.order_id}")
            self.content_widget.setVisible(False)

    def clear(self):
        """Clear order details."""
        self.current_order = None
        self.header_label.setText("Order Details")
        self.show_placeholder()

    def show_print_preview(self):
        """Show print preview dialog before printing."""
        if not self.current_order:
            return

        try:
            # Create printer with Letter page size
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            # Create print preview dialog
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_dialog.setWindowTitle(f"Print Preview - Order {self.current_order.order_id}")

            # Connect paint request signal to rendering function
            preview_dialog.paintRequested.connect(lambda p: self._print_to_device(p))

            # Show dialog (modal)
            preview_dialog.exec()

            logger.info(f"Print preview shown for order {self.current_order.order_id}")

        except Exception as e:
            logger.error(f"Error showing print preview: {e}")
            from visual_order_lookup.ui.dialogs import ErrorHandler
            ErrorHandler.show_general_error(f"Failed to show print preview: {str(e)}", self)

    def print_order(self):
        """Print order acknowledgement directly to default printer."""
        if not self.current_order:
            return

        try:
            # Create printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            # Show print dialog
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Print the document
                self._print_to_device(printer)
                logger.info(f"Printed order {self.current_order.order_id}")

        except Exception as e:
            logger.error(f"Error printing order: {e}")
            from visual_order_lookup.ui.dialogs import ErrorHandler
            ErrorHandler.show_general_error(f"Failed to print order: {str(e)}", self)

    def save_as_pdf(self):
        """Save order acknowledgement as PDF."""
        if not self.current_order:
            return

        try:
            # Suggest filename
            default_filename = f"Order_{self.current_order.order_id}.pdf"

            # Show save dialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Order as PDF",
                default_filename,
                "PDF Files (*.pdf);;All Files (*)"
            )

            if filename:
                # Ensure .pdf extension
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'

                # Create printer for PDF
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(filename)
                printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

                # Print to PDF
                self._print_to_device(printer)

                logger.info(f"Saved order {self.current_order.order_id} as PDF: {filename}")

                # Show success message
                from visual_order_lookup.ui.dialogs import ErrorHandler
                ErrorHandler.show_info(
                    "PDF Saved",
                    f"Order acknowledgement saved to:\n{filename}",
                    self
                )

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            from visual_order_lookup.ui.dialogs import ErrorHandler
            ErrorHandler.show_general_error(f"Failed to save PDF: {str(e)}", self)

    def _print_to_device(self, printer):
        """Generate HTML and print to device (printer or PDF).

        Args:
            printer: QPrinter device to print to
        """
        try:
            # Generate HTML report using ReportService
            html = self.report_service.generate_order_acknowledgement(self.current_order)

            # Create text document and set HTML
            document = QTextDocument()
            document.setHtml(html)

            # Print to device
            document.print(printer)

        except Exception as e:
            logger.error(f"Error printing to device: {e}")
            # Fallback: generate simple HTML from current data
            html = self._generate_print_html()
            document = QTextDocument()
            document.setHtml(html)
            document.print(printer)

    def _generate_print_html(self) -> str:
        """Generate simple HTML for printing from current order data.

        Returns:
            HTML string for printing
        """
        order = self.current_order
        customer_name = order.customer.name if order.customer else "N/A"

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th {{ background-color: #f0f0f0; padding: 8px; text-align: left; border: 1px solid #ddd; }}
                td {{ padding: 8px; border: 1px solid #ddd; }}
                .header-table td {{ border: none; }}
                .totals {{ text-align: right; font-weight: bold; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h2>Order Acknowledgement - Job #{order.order_id}</h2>

            <table class='header-table'>
                <tr><td><b>Order Date:</b></td><td>{order.formatted_date()}</td></tr>
                <tr><td><b>Customer:</b></td><td>{customer_name}</td></tr>
                <tr><td><b>Contact:</b></td><td>{order.contact_name or '-'}</td></tr>
                <tr><td><b>Customer PO:</b></td><td>{order.customer_po_ref or '-'}</td></tr>
                <tr><td><b>Status:</b></td><td>{order.status or '-'}</td></tr>
            </table>

            <h3>Line Items</h3>
            <table>
                <tr>
                    <th>Line</th>
                    <th>Quantity</th>
                    <th>Base/Lot ID</th>
                    <th>Part ID</th>
                    <th>Description</th>
                    <th>Unit Price</th>
                    <th>Line Total</th>
                </tr>
        """

        for item in order.line_items:
            html += f"""
                <tr>
                    <td>{item.line_number}</td>
                    <td>{item.formatted_quantity()}</td>
                    <td>{item.base_lot_id or '-'}</td>
                    <td>{item.part_id or '-'}</td>
                    <td>{item.description or '-'}</td>
                    <td>{item.formatted_unit_price()}</td>
                    <td>{item.formatted_line_total()}</td>
                </tr>
            """

        html += f"""
            </table>

            <div class='totals'>
                <p>Total: {order.formatted_total_amount()}</p>
            </div>
        </body>
        </html>
        """

        return html
