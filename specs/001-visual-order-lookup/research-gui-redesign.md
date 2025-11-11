# GUI Redesign Research - Visual Order Lookup

**Date**: 2025-11-05
**Purpose**: Redesign GUI and order acknowledgement based on Visual legacy interface references
**References**:
- `.context/customer_order_entry_figma.svg` - Visual legacy GUI layout
- `.context/order_4049_ack.html` - Professional order acknowledgement template

## Design Goals

1. **Authentic Visual Legacy Aesthetic**: Match the look and feel of the original Visual ERP system
2. **Professional Order Reports**: SAMCO-branded acknowledgements with ISO certification badge
3. **Print Preview Capability**: Enable print preview before printing order acknowledgements
4. **Familiar Navigation**: Sidebar-based navigation familiar to Visual users

## Research Findings

### 1. GUI Layout Redesign

#### Decision: Sidebar Navigation with Toolbar

**Rationale**:
- The `customer_order_entry_figma.svg` shows a classic Visual ERP interface with left sidebar navigation
- This pattern is familiar to users transitioning from Visual software
- Provides visual context of where users are in the application hierarchy

**Implementation Approach**:

```python
# Main Window Structure
QMainWindow
├── QWidget (sidebar, 180px fixed width)
│   ├── Sales Section (QListWidget or custom)
│   │   └── Customer Order Entry (highlighted)
│   └── Inventory Section
│       ├── Purchasing
│       ├── Scheduling
│       └── Eng/Mfg
├── QToolBar (horizontal, 36px height)
│   ├── Save button (💾)
│   ├── Open button (📂)
│   ├── Print button (🖨️)
│   ├── Search button (🔍)
│   └── [other actions]
└── QWidget (main content area)
    ├── QTabWidget (Contact, Other tabs)
    └── QSplitter or stacked layout
        ├── Order list (QTableView)
        └── Order details (QTextBrowser + print controls)
```

**Alternatives Considered**:
- Menu bar only: Too minimal, doesn't match Visual aesthetics
- MDI (Multiple Document Interface): Too complex for this use case
- Ribbon interface: Too modern, not matching Visual legacy

**PyQt6 Widgets**:
- `QListWidget` for sidebar navigation with custom styling
- `QToolBar` with `QAction` objects for toolbar buttons
- `QTabWidget` for tab interface
- Custom QSS (Qt Style Sheets) for Visual aesthetic

### 2. Visual Aesthetic Styling

#### Decision: Windows 95/2000 Classic Theme with Gray Palette

**Rationale**:
- Original Visual software used Windows classic theming
- Users expect familiar gray backgrounds, inset borders, button reliefs
- Professional business software aesthetic, not consumer-grade

**Color Palette** (from SVG analysis):
```css
Background: #f0f0f0 (light gray)
Sidebar: #e8e8e8 (slightly darker gray)
Selected item: #d0d8e0 (blue-gray tint)
Form background: #c0c0c0 (medium gray)
Content panel: #ffffff (white)
Grid header: #c0c0c0 (medium gray)
Grid lines: #d0d0d0 (light grid)
Borders: #808080, #999999, #aaa (various grays)
Button highlight: #fff (white edge for raised effect)
```

**Qt Style Sheet (QSS) Implementation**:

```qss
/* Sidebar styling */
QListWidget#sidebar {
    background-color: #e8e8e8;
    border: 1px solid #999;
    font-family: Arial, sans-serif;
    font-size: 10pt;
}

QListWidget#sidebar::item:selected {
    background-color: #d0d8e0;
    border: 1px solid #aaa;
}

/* Toolbar styling */
QToolBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e8e8e8, stop:1 #d0d0d0);
    border: 2px solid #808080;
    spacing: 4px;
    padding: 2px;
}

QToolButton {
    background-color: #d0d0d0;
    border: 1px outset #fff;
    border-right: 1px solid #808080;
    border-bottom: 1px solid #808080;
    padding: 4px;
}

QToolButton:pressed {
    border: 1px inset #808080;
}

/* Form area styling */
QWidget#formContainer {
    background-color: #c0c0c0;
    border: 2px solid #808080;
}

QWidget#formPanel {
    background-color: #ffffff;
    border: 2px inset #808080;
}

/* Tab widget styling */
QTabWidget::pane {
    border: 1px solid #808080;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #d0d0d0;
    border: 1px solid #808080;
    padding: 5px 15px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: none;
}

/* Table/Grid styling */
QTableView {
    gridline-color: #d0d0d0;
    border: 1px solid #808080;
    selection-background-color: #d0d8e0;
}

QHeaderView::section {
    background-color: #c0c0c0;
    border: 1px solid #808080;
    padding: 5px;
    font-weight: bold;
}
```

**Alternatives Considered**:
- Modern flat design: Rejected, not matching Visual legacy
- Dark theme: Rejected, business software expectation is light themes
- Native OS theming: Rejected, inconsistent across Windows versions

### 3. Order Acknowledgement Redesign

#### Decision: Professional SAMCO-Branded Template with ISO Badge

**Rationale**:
- `order_4049_ack.html` shows official company branding expected by customers
- ISO 9001 certification badge demonstrates quality management compliance
- Professional formatting matches customer expectations for formal documents
- Base/Lot ID system (e.g., "4049/01") critical for manufacturing traceability

**Template Structure**:

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: letter; margin: 0.5in; }
        body { font-family: Arial; font-size: 10pt; }
        .header { display: flex; justify-content: space-between; }
        .logo { font-size: 32pt; font-weight: bold; font-style: italic; }
        .iso-badge {
            border: 2px solid black;
            border-radius: 50%;
            width: 80px; height: 80px;
            text-align: center;
        }
        .doc-title {
            text-align: center;
            font-size: 14pt;
            font-weight: bold;
            border-top: 2px solid black;
            border-bottom: 2px solid black;
            padding: 10px 0;
        }
        /* ... rest of styling ... */
    </style>
</head>
<body>
    <!-- Header with SAMCO logo and ISO badge -->
    <div class="header">
        <div>
            <div class="logo">SAMCO</div>
            <div class="company-info">Machinery Limited</div>
        </div>
        <div class="iso-badge">
            <div>ISO 9001</div>
            <div style="font-size: 16pt;">QMI</div>
            <div>{{ order.order_id }}</div>
            <div>THETRA</div>
        </div>
    </div>

    <!-- Document title -->
    <div class="doc-title">CUSTOMER ORDER ACKNOWLEDGEMENT</div>

    <!-- Info table with order details -->
    <table class="info-table">
        <tr>
            <td class="label">CUSTOMER</td>
            <td>{{ order.customer.name }}</td>
            <td class="label">QUOTE ID</td>
            <td>{{ order.quote_id|na }}</td>
        </tr>
        <!-- ... additional rows ... -->
    </table>

    <!-- Side-by-side addresses -->
    <div>
        <div class="address-table">
            <div class="section-title">Bill To</div>
            <div class="address-box">
                {{ order.customer.bill_to_name|na }}<br>
                {{ order.customer.bill_to_address_1|na }}<br>
                <!-- ... -->
            </div>
        </div>
        <div class="address-table">
            <div class="section-title">Ship To</div>
            <div class="address-box">
                {{ order.customer.name }}<br>
                {{ order.customer.address_1|na }}<br>
                <!-- ... -->
            </div>
        </div>
    </div>

    <!-- Line items table -->
    <table class="items-table">
        <thead>
            <tr>
                <th>Qty</th>
                <th>Base / Lot ID</th>
                <th>Description</th>
                <th>Unit Price</th>
                <th>Price(USD)</th>
            </tr>
        </thead>
        <tbody>
            {% for item in order.line_items %}
            <tr>
                <td class="line-no">{{ item.quantity }}</td>
                <td class="base-lot">{{ item.base_lot_id }}</td>
                <td>{{ item.description|na }}</td>
                <td class="price">{{ item.formatted_unit_price() }}</td>
                <td class="price">{{ item.formatted_line_total() }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- Total -->
    <div class="total-row">
        <strong>Order Amount: {{ order.formatted_total_amount() }}</strong>
    </div>
</body>
</html>
```

**Jinja2 Template Updates**:
- Replace existing `order_acknowledgement.html` with SAMCO-branded version
- Ensure ISO badge includes order ID dynamically
- Add `@page` CSS for proper PDF generation
- Use `base_lot_id` property from OrderLineItem model

**Alternatives Considered**:
- Generic template without branding: Rejected, unprofessional for customer-facing documents
- Modern minimalist design: Rejected, doesn't match Visual legacy expectations
- Color printing template: Rejected, most facilities use B&W printers

### 4. Print Preview Implementation

#### Decision: Use QPrintPreviewDialog for Pre-Print Review

**Rationale**:
- Users want to verify report formatting before sending to printer
- Prevents wasted paper from incorrect print settings
- Allows page layout adjustments (landscape vs portrait, margins)
- Standard practice in business software

**Implementation**:

```python
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt6.QtGui import QPageSize

class OrderDetailView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... existing setup ...

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
            preview_dialog.paintRequested.connect(lambda p: self.text_browser.print(p))

            # Show dialog (modal)
            preview_dialog.exec()

            logger.info(f"Print preview shown for order {self.current_order.order_id}")

        except Exception as e:
            logger.error(f"Error showing print preview: {e}")
            from visual_order_lookup.ui.dialogs import ErrorHandler
            ErrorHandler.show_general_error(f"Failed to show print preview: {str(e)}", self)

    def print_order(self):
        """Print order acknowledgement directly (existing functionality)."""
        # Keep existing direct print functionality
        # ...

    def setup_ui(self):
        # ... existing UI setup ...

        # Update button connections
        self.print_preview_button = QPushButton("Print Preview")
        self.print_preview_button.clicked.connect(self.show_print_preview)
        self.print_preview_button.setEnabled(False)
        header_layout.addWidget(self.print_preview_button)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_order)
        self.print_button.setEnabled(False)
        header_layout.addWidget(self.print_button)

        # ... rest of UI ...
```

**UI Changes**:
- Add "Print Preview" button next to existing "Print" button
- "Print Preview" opens QPrintPreviewDialog
- "Print" button sends directly to default printer (existing behavior)
- Both buttons disabled until order is loaded

**Alternatives Considered**:
- Custom preview widget: Too complex, reinventing Qt functionality
- Web-based preview: Requires additional dependencies (Qt WebEngine)
- Preview in main window: Clutters UI, modal dialog is cleaner

### 5. Data Model Enhancements

#### Decision: Add Quote ID and Revision Fields to OrderHeader

**Rationale**:
- `order_4049_ack.html` includes Quote ID and Revision fields in info table
- These fields may exist in Visual database but not currently mapped
- Professional acknowledgements should include all available order metadata

**Model Updates**:

```python
@dataclass
class OrderHeader:
    """Complete order information for acknowledgement."""
    order_id: str
    customer: Optional[Customer]
    order_date: date
    customer_po_ref: Optional[str]
    promise_date: Optional[date]
    contact_name: str
    contact_phone: Optional[str]
    contact_fax: Optional[str]
    terms_description: Optional[str]
    line_items: List[OrderLineItem]
    total_amount: Decimal
    currency_id: str = "USD"

    # NEW FIELDS for redesigned template
    quote_id: Optional[str] = None  # Quote reference number
    revision_number: Optional[int] = None  # Revision number (integer)
    revision_date: Optional[date] = None  # Date of last revision
    sales_rep: Optional[str] = None  # Sales representative name
    desired_ship_date: Optional[date] = None  # Customer requested ship date
    factory_acceptance_date_estimated: Optional[date] = None  # Estimated FAT
    factory_acceptance_date_firmed: Optional[date] = None  # Confirmed FAT

    def formatted_revision(self) -> str:
        """Format revision number for display."""
        return f"Rev. {self.revision_number}" if self.revision_number else "N/A"
```

**Database Query Updates**:
- Update `search_by_job_number()` query to SELECT additional fields from CUSTOMER_ORDER table
- Map database columns to new model fields
- Handle NULL values appropriately

**Alternatives Considered**:
- Ignore missing fields: Rejected, incomplete professional documents
- Separate DTO for acknowledgements: Rejected, adds complexity without benefit

## Implementation Recommendations

### Phase 1: Update Order Acknowledgement Template
1. Replace `visual_order_lookup/templates/order_acknowledgement.html` with SAMCO-branded version
2. Update Jinja2 template with header, ISO badge, info table, addresses, line items
3. Test PDF generation with `@page` CSS rules

### Phase 2: Add Print Preview
1. Add `show_print_preview()` method to `OrderDetailView`
2. Create "Print Preview" button in UI
3. Connect signal to `QPrintPreviewDialog.paintRequested`
4. Test with various orders (small, large, missing data)

### Phase 3: Enhance Data Model
1. Add new fields to `OrderHeader` dataclass
2. Update SQL queries to retrieve quote_id, revision_number, etc.
3. Update template to display new fields
4. Handle NULL values with |na filter

### Phase 4: Redesign Main Window GUI
1. Create sidebar navigation widget (QListWidget or custom)
2. Style sidebar with Visual aesthetic (QSS)
3. Create toolbar with icon buttons
4. Reorganize main content area with tabs
5. Apply gray color palette throughout
6. Test navigation flow

### Phase 5: Polish and Testing
1. Apply complete QSS stylesheet for Visual aesthetic
2. Test all colors, borders, button states
3. Verify print preview works correctly
4. Compare to `customer_order_entry_figma.svg` for accuracy
5. User acceptance testing with Pam, Cindy, Efron

## Success Criteria

- ✅ Main window matches Visual legacy layout from SVG (sidebar, toolbar, tabs, form area)
- ✅ Order acknowledgement matches SAMCO template from HTML (header, ISO badge, addresses, line items)
- ✅ Print preview shows accurate representation before printing
- ✅ Visual aesthetic (gray palette, borders, reliefs) matches Windows 95/2000 classic theme
- ✅ All new fields (quote ID, revision, sales rep, FAT dates) display correctly
- ✅ Users report interface is familiar and professional

## References

- **Visual GUI Layout**: `.context/customer_order_entry_figma.svg`
- **Order Acknowledgement**: `.context/order_4049_ack.html`
- **PyQt6 Documentation**: https://doc.qt.io/qtforpython-6/
- **Qt Style Sheets**: https://doc.qt.io/qt-6/stylesheet-reference.html
- **QPrintPreviewDialog**: https://doc.qt.io/qt-6/qprintpreviewdialog.html

---

**Status**: Research complete, ready for implementation planning
