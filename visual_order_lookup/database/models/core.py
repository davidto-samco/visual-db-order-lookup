"""Data transfer objects (DTOs) for order and customer information."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass
class OrderSummary:
    """Summary information for display in order list."""

    job_number: str
    customer_name: str
    order_date: date
    total_amount: Decimal
    customer_po: Optional[str] = None

    def formatted_date(self) -> str:
        """Format order date as MM/DD/YYYY."""
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_amount(self) -> str:
        """Format total amount as currency with $ and thousand separators."""
        return f"${self.total_amount:,.2f}"


@dataclass
class Customer:
    """Customer information with shipping and billing addresses."""

    customer_id: str
    name: str

    # Ship-to address
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    # Bill-to address
    bill_to_name: Optional[str] = None
    bill_to_address_1: Optional[str] = None
    bill_to_address_2: Optional[str] = None
    bill_to_address_3: Optional[str] = None
    bill_to_city: Optional[str] = None
    bill_to_state: Optional[str] = None
    bill_to_zip_code: Optional[str] = None
    bill_to_country: Optional[str] = None

    @property
    def abbreviation(self) -> str:
        """
        Generate customer abbreviation for order acknowledgement badge.

        Takes first 3 letters of first 2 significant words.
        Example: "THOMAS BUILD BUSES, INC." -> "THOBUI"
        Example: "CLARKDIETRICH BUILDING SYSTEMS, LLC" -> "CLABUI"

        Returns:
            6-character abbreviation of customer name
        """
        if not self.name:
            return "CUSTOM"

        # Clean up the name
        name = self.name.upper()
        # Remove punctuation
        for char in [',', '.', '-', '&']:
            name = name.replace(char, ' ')

        # Remove common company suffixes
        suffixes = [' LLC', ' INC', ' INCORPORATED', ' LTD', ' LIMITED',
                   ' CO', ' COMPANY', ' CORP', ' CORPORATION', ' THE']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Split into words, filter out short words
        words = [w for w in name.split() if len(w) >= 3]

        if not words:
            return self.name[:6].upper()

        # Take first 3 letters of first 2 words
        abbrev = ""
        for word in words[:2]:
            abbrev += word[:3]

        # Pad or truncate to 6 characters
        abbrev = abbrev[:6].ljust(6, 'X')

        return abbrev

    def formatted_ship_to_address(self) -> str:
        """Format ship-to address as multi-line string."""
        lines = []
        if self.address_1:
            lines.append(self.address_1)
        if self.address_2:
            lines.append(self.address_2)
        city_state_zip = ", ".join(
            filter(None, [self.city, self.state, self.zip_code])
        )
        if city_state_zip:
            lines.append(city_state_zip)
        if self.country:
            lines.append(self.country)
        return "\n".join(lines) if lines else "N/A"

    def formatted_bill_to_address(self) -> str:
        """
        Format bill-to address as multi-line string.
        Falls back to ship-to address if bill-to fields are not populated.
        """
        lines = []
        if self.bill_to_name:
            lines.append(self.bill_to_name)
        if self.bill_to_address_1:
            lines.append(self.bill_to_address_1)
        if self.bill_to_address_2:
            lines.append(self.bill_to_address_2)
        if self.bill_to_address_3:
            lines.append(self.bill_to_address_3)
        city_state_zip = ", ".join(
            filter(None, [self.bill_to_city, self.bill_to_state, self.bill_to_zip_code])
        )
        if city_state_zip:
            lines.append(city_state_zip)
        if self.bill_to_country:
            lines.append(self.bill_to_country)

        # Fallback to ship-to address if bill-to is not populated
        if not lines:
            return self.formatted_ship_to_address()

        return "\n".join(lines)


@dataclass
class OrderLineItem:
    """Individual line item within a customer order."""

    line_number: int
    order_id: str
    base_id: Optional[str]
    part_id: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    description: Optional[str] = None
    promise_date: Optional[date] = None
    binary_text: Optional[str] = None  # Additional detail text from CUST_LINE_BINARY
    has_parent_line: bool = False  # True if order has a parent line with UNIT_PRICE = 0

    @property
    def base_lot_id(self) -> str:
        """Get base/lot ID from database or generate fallback."""
        if self.base_id:
            return self.base_id
        # Fallback if base_id is not available - use line number with zero padding
        # Format as {ORDER_ID}/{LINE_NO:02d} (e.g., 4049/01, 4049/02)
        return f"{self.order_id}/{self.line_number:02d}"

    @property
    def should_show_base_lot_id(self) -> bool:
        """
        Determine if Base/Lot ID should be displayed.

        Hide Base/Lot ID when ALL conditions are true:
        - Line has non-zero price (UNIT_PRICE > 0)
        - Line has detail text in CUST_LINE_BINARY (binary_text exists)
        - Order has a parent/header line (another line with UNIT_PRICE = 0)

        Returns:
            True if Base/Lot ID should be shown, False if hidden
        """
        # Show if unit price is 0 (this is a header/parent line)
        if self.unit_price == 0:
            return True

        # Show if no detail text (standalone line without binary details)
        if not self.binary_text:
            return True

        # Show if no parent line exists (standalone line with details)
        if not self.has_parent_line:
            return True

        # Hide: this is a detail line with price > 0, has binary text, and has a parent
        return False

    def formatted_quantity(self) -> str:
        """Format quantity with up to 4 decimal places, removing trailing zeros."""
        return f"{self.quantity:.4f}".rstrip("0").rstrip(".")

    def formatted_unit_price(self) -> str:
        """Format unit price as currency."""
        return f"${self.unit_price:,.2f}"

    def formatted_line_total(self) -> str:
        """Format line total as currency."""
        return f"${self.line_total:,.2f}"


@dataclass
class OrderHeader:
    """Complete order information including customer and line items."""

    # Order identification
    order_id: str
    order_date: date
    customer_po_ref: Optional[str] = None

    # Contact information
    contact_first_name: Optional[str] = None
    contact_last_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_fax: Optional[str] = None

    # Dates
    promise_date: Optional[date] = None

    # Financial information
    total_amount: Decimal = Decimal("0.00")
    currency_id: str = "USD"

    # Terms
    terms_description: Optional[str] = None

    # Related entities
    customer: Optional[Customer] = None
    line_items: List[OrderLineItem] = field(default_factory=list)

    # New fields for SAMCO-branded acknowledgement template
    quote_id: Optional[str] = None
    revision_number: Optional[str] = None  # Can be text like "ONE" or numeric like "1"
    revision_date: Optional[date] = None
    sales_rep: Optional[str] = None
    desired_ship_date: Optional[date] = None
    factory_acceptance_date_estimated: Optional[date] = None
    factory_acceptance_date_firmed: Optional[date] = None
    project_description: Optional[str] = None  # From CUST_ORDER_BINARY

    @property
    def contact_name(self) -> str:
        """Get full contact name or N/A."""
        if self.contact_first_name and self.contact_last_name:
            return f"{self.contact_first_name} {self.contact_last_name}"
        elif self.contact_first_name:
            return self.contact_first_name
        elif self.contact_last_name:
            return self.contact_last_name
        return "N/A"

    @property
    def payment_terms(self) -> str:
        """Get payment terms with default fallback."""
        if self.terms_description:
            return self.terms_description
        return "Due on receipt"

    def formatted_date(self) -> str:
        """Format order date as MM/DD/YYYY."""
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_promise_date(self) -> str:
        """Format promise date as MM/DD/YYYY or N/A."""
        if self.promise_date:
            return self.promise_date.strftime("%m/%d/%Y")
        return "N/A"

    def formatted_factory_acceptance_date(self) -> str:
        """Format estimated factory acceptance test date as M/D/YYYY or N/A."""
        if self.factory_acceptance_date_estimated:
            # Format without leading zeros (e.g., "3/1/2006" not "03/01/2006")
            # Windows doesn't support %-m, so use formatting workaround
            if hasattr(self.factory_acceptance_date_estimated, 'strftime'):
                month = self.factory_acceptance_date_estimated.month
                day = self.factory_acceptance_date_estimated.day
                year = self.factory_acceptance_date_estimated.year
                return f"{month}/{day}/{year}"
            return "N/A"
        return "N/A"

    def formatted_total_amount(self) -> str:
        """Format total amount as currency."""
        return f"${self.total_amount:,.2f}"


@dataclass
class DateRangeFilter:
    """Date range filter for order queries."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def validate(self) -> bool:
        """Validate that start date is before or equal to end date."""
        if self.start_date and self.end_date:
            return self.start_date <= self.end_date
        return True

    def is_empty(self) -> bool:
        """Check if filter has no dates set."""
        return self.start_date is None and self.end_date is None

    def to_sql_where_clause(self) -> tuple[str, list]:
        """
        Generate SQL WHERE clause and parameters for date range filtering.

        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params = []

        if self.start_date:
            conditions.append("co.ORDER_DATE >= ?")
            params.append(self.start_date)

        if self.end_date:
            conditions.append("co.ORDER_DATE <= ?")
            params.append(self.end_date)

        if conditions:
            where_clause = " AND ".join(conditions)
            return where_clause, params
        else:
            return "", []


# ============================================================================
# Inventory Module Entities
# ============================================================================


@dataclass
class Part:
    """Part master data for inventory lookups.

    Represents a part from the Visual database PART table with associated
    vendor information. Used in Inventory module for part searches and
    part detail displays.
    """

    part_id: str
    part_number: str
    description: str
    extended_description: Optional[str]
    unit_of_measure: str
    unit_material_cost: Optional[Decimal]
    unit_labor_cost: Optional[Decimal]
    unit_burden_cost: Optional[Decimal]
    unit_price: Optional[Decimal]
    material_code: Optional[str]
    qty_on_hand: Optional[Decimal]
    qty_available: Optional[Decimal]
    qty_on_order: Optional[Decimal]
    qty_in_demand: Optional[Decimal]
    drawing_id: Optional[str]
    drawing_revision: Optional[str]
    vendor_id: Optional[str]
    vendor_name: Optional[str]
    is_purchased: bool
    is_fabricated: bool
    is_stocked: bool
    weight: Optional[Decimal]
    weight_um: Optional[str]

    @property
    def total_unit_cost(self) -> Decimal:
        """Calculate total unit cost (material + labor + burden)."""
        material = self.unit_material_cost or Decimal('0')
        labor = self.unit_labor_cost or Decimal('0')
        burden = self.unit_burden_cost or Decimal('0')
        return material + labor + burden

    def formatted_unit_price(self) -> str:
        """Format unit price as currency."""
        if self.unit_price:
            return f"${self.unit_price:,.2f}"
        return "N/A"

    def formatted_total_cost(self) -> str:
        """Format total unit cost as currency."""
        return f"${self.total_unit_cost:,.2f}"

    @property
    def part_type(self) -> str:
        """Determine part type based on flags."""
        if self.is_purchased:
            return "Purchased"
        elif self.is_fabricated:
            return "Manufactured"
        else:
            return "Assembly"


@dataclass
class WhereUsed:
    """BOM usage record for a part.

    Represents where a part is used in work orders/assemblies from the
    REQUIREMENT table. Replaces previous inventory transaction model.
    Used in Inventory module "Where Used" tab to show BOM structure information.
    """

    part_number: str
    manufactured_part_id: Optional[str]
    manufactured_part_description: Optional[str]
    work_order_master: str
    work_order_sub_id: str
    work_order_lot_id: str
    work_order_type: Optional[str]
    seq_no: int
    piece_no: int
    qty_per: Decimal
    fixed_qty: Decimal
    scrap_percent: Decimal

    def formatted_work_order(self) -> str:
        """Format work order for display.

        Format: TYPE BASE_ID[-SUB_ID][/LOT_ID]
        - Always prefix with WORKORDER_TYPE (M or W) followed by space
        - SUB_ID is omitted if it's 0 (along with the '-')
        - LOT_ID is omitted if it's 0 (along with the '/')

        Examples:
            "M 10002" (sub_id=0, lot_id=0, type=M)
            "M 10018-1" (sub_id=1, lot_id=0, type=M)
            "W 3693/46W" (sub_id=0, lot_id=46W, type=W)
            "W 3928-2/26W" (sub_id=2, lot_id=26W, type=W)

        Returns:
            Formatted work order string
        """
        # Start with BASE_ID
        wo_str = self.work_order_master

        # Check if sub_id is non-zero (treat "0" as zero)
        has_sub_id = self.work_order_sub_id and self.work_order_sub_id.strip() != "0"

        # Check if lot_id is non-zero (treat "0" as zero)
        has_lot_id = self.work_order_lot_id and self.work_order_lot_id.strip() != "0"

        # Add SUB_ID if present
        if has_sub_id:
            wo_str = f"{wo_str}-{self.work_order_sub_id}"

        # Add LOT_ID if present
        if has_lot_id:
            wo_str = f"{wo_str}/{self.work_order_lot_id}"

        # Always prefix with TYPE (M or W) followed by space
        if self.work_order_type:
            wo_type = self.work_order_type.strip().upper()
            wo_str = f"{wo_type} {wo_str}"

        return wo_str

    def formatted_manufactured_part_id(self) -> str:
        """Format manufactured part ID for display.

        Returns:
            Part ID or "N/A" if not available
        """
        return self.manufactured_part_id if self.manufactured_part_id else "N/A"

    def formatted_manufactured_part_description(self) -> str:
        """Format manufactured part description for display.

        Returns:
            Part description or empty string if not available
        """
        return self.manufactured_part_description if self.manufactured_part_description else ""

    def formatted_seq_no(self) -> str:
        """Format sequence number for display.

        Returns:
            Integer string (e.g., "10", "0")
        """
        return str(self.seq_no)

    def formatted_piece_no(self) -> str:
        """Format piece number for display.

        Returns:
            Integer string (e.g., "1", "0")
        """
        return str(self.piece_no)

    def formatted_qty_per(self) -> str:
        """Format quantity per for display.

        Returns:
            Decimal with 4 decimal places (e.g., "1.2500", "0.0000")
        """
        return f"{self.qty_per:.4f}"

    def formatted_fixed_qty(self) -> str:
        """Format fixed quantity for display.

        Returns:
            Decimal with 4 decimal places (e.g., "5.0000", "0.0000")
        """
        return f"{self.fixed_qty:.4f}"

    def formatted_scrap_percent(self) -> str:
        """Format scrap percentage for display.

        Returns:
            Decimal with 2 decimal places + "%" (e.g., "5.00%", "0.00%")
        """
        return f"{self.scrap_percent:.2f}%"


@dataclass
class PurchaseHistory:
    """Purchase order history for a part.

    Represents purchase order line items from PURC_ORDER_LINE table.
    Used in Inventory module "Purchase History" tab for vendor and PO tracking.
    """

    part_number: str
    po_number: str
    line_number: int
    order_date: date
    vendor_name: str
    vendor_id: str
    vendor_part_id: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    desired_receive_date: Optional[date]
    last_received_date: Optional[date]
    # Enhancement fields for purchase history detail
    currency: Optional[str] = None
    native_currency: Optional[str] = None
    native_unit_price: Optional[Decimal] = None
    disc_percent: Optional[Decimal] = None
    fixed_disc: Optional[Decimal] = None
    standard_unit_cost: Optional[Decimal] = None

    def formatted_order_date(self) -> str:
        """Format order date as MM/DD/YYYY."""
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_unit_price(self) -> str:
        """Format unit price as currency."""
        return f"${self.unit_price:,.2f}"

    def formatted_line_total(self) -> str:
        """Format line total as currency."""
        return f"${self.line_total:,.2f}"

    def formatted_quantity(self) -> str:
        """Format quantity with thousand separators."""
        return f"{self.quantity:,.2f}"

    def formatted_desired_date(self) -> str:
        """Format desired receive date as MM/DD/YYYY."""
        if self.desired_receive_date:
            return self.desired_receive_date.strftime("%m/%d/%Y")
        return "N/A"

    def formatted_received_date(self) -> str:
        """Format last received date as MM/DD/YYYY."""
        if self.last_received_date:
            return self.last_received_date.strftime("%m/%d/%Y")
        return "N/A"

    def formatted_currency(self) -> str:
        """Format currency code."""
        return self.currency.strip() if self.currency else ""

    def formatted_native_currency(self) -> str:
        """Format native currency code."""
        return self.native_currency.strip() if self.native_currency else ""

    def formatted_native_unit_price(self) -> str:
        """Format native unit price as decimal."""
        if self.native_unit_price is not None:
            return f"{self.native_unit_price:,.4f}"
        return "0.0000"

    def formatted_disc_percent(self) -> str:
        """Format discount percent with % symbol."""
        if self.disc_percent is not None:
            return f"{self.disc_percent:.2f}%"
        return "0.00%"

    def formatted_fixed_disc(self) -> str:
        """Format fixed discount as currency."""
        if self.fixed_disc is not None:
            return f"{self.fixed_disc:,.4f}"
        return "0.0000"

    def formatted_standard_unit_cost(self) -> str:
        """Format standard unit cost as currency."""
        if self.standard_unit_cost is not None:
            return f"{self.standard_unit_cost:,.4f}"
        return "0.0000"


@dataclass
class Job:
    """Job/Customer Order data for BOM search."""

    job_number: str
    customer_id: Optional[str]
    customer_name: str
    assembly_count: int = 0

    def formatted_header(self) -> str:
        """Format job header display."""
        return f"Job {self.job_number} - {self.customer_name} ({self.assembly_count} assemblies)"


@dataclass
class BOMNode:
    """Bill of Materials node for hierarchical tree display."""

    job_number: str
    lot_id: str
    sub_id: str
    base_lot_id: Optional[str]
    part_id: str
    part_description: Optional[str]
    node_type: str  # 'assembly', 'manufactured', 'purchased'
    is_fabricated: bool
    is_purchased: bool
    depth: int = 0
    is_loaded: bool = False  # Lazy loading flag

    @property
    def display_color(self) -> str:
        """Calculate row color based on node type.

        Returns:
            Color name for QTreeWidget styling:
            - 'blue' for assemblies (fabricated, has children)
            - 'black' for manufactured parts (fabricated, no children)
            - 'red' for purchased parts
        """
        if self.node_type == "assembly":
            return "blue"
        elif self.node_type == "purchased":
            return "red"
        else:  # manufactured
            return "black"

    @property
    def is_assembly(self) -> bool:
        """Check if node is an assembly with potential children."""
        return self.node_type == "assembly"

    @property
    def full_lot_id(self) -> str:
        """Get full lot ID path (BASE/LOT)."""
        if self.base_lot_id:
            return f"{self.base_lot_id}/{self.lot_id}"
        return self.lot_id

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"BOMNode(lot={self.lot_id}, sub={self.sub_id}, "
            f"part={self.part_id}, type={self.node_type})"
        )
