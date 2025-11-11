# Data Model: Visual Database Multi-Module Application

**Date**: 2025-11-07 (Updated from 2025-11-04)
**Feature**: Visual Database Order Lookup - Three Module Expansion
**Purpose**: Define data structures and relationships for Sales, Inventory, and Engineering modules

## Overview

This document defines the data model for the Visual Database Order Lookup application across three modules:
1. **Sales Module** - Customer order lookup (existing)
2. **Inventory Module** - Part maintenance and where-used queries (new)
3. **Engineering Module** - BOM hierarchy display (new)

The model consists of **Data Transfer Objects (DTOs)** that represent data retrieved from the Visual SQL Server database and displayed in the PyQt6 UI.

**Important**: This application does NOT create or modify database schemas. All entities are read-only views of existing Visual database tables.

---

## Sales Module Entities

### 1. OrderSummary

**Purpose**: Lightweight representation of an order for list display

**Used in**:
- Default order list on startup (FR-001)
- Date range filter results (FR-010)
- Customer name search results (FR-019)

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `job_number` | `str` | Yes | Unique order identifier (e.g., "4049") | `CUSTOMER_ORDER.ID` |
| `customer_name` | `str` | Yes | Customer company name | `CUSTOMER.NAME` |
| `order_date` | `date` | Yes | Date order was placed | `CUSTOMER_ORDER.ORDER_DATE` |
| `total_amount` | `Decimal` | Yes | Total order value | `CUSTOMER_ORDER.TOTAL_AMT_ORDERED` |

**Validation Rules**:
- `job_number`: Non-empty string, max 15 characters
- `customer_name`: Non-empty string, max 100 characters
- `order_date`: Valid date between 1985-01-01 and current date
- `total_amount`: Non-negative decimal with 2 decimal places

**Display Format**:
```
Job Number: "4049"
Customer Name: "THE TRANE COMPANY"
Order Date: "12/20/2000"
Total Amount: "$1,751,000.00"
```

**Python Class**:
```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass
class OrderSummary:
    job_number: str
    customer_name: str
    order_date: date
    total_amount: Decimal

    def formatted_date(self) -> str:
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_amount(self) -> str:
        return f"${self.total_amount:,.2f}"
```

---

### 2. OrderHeader

**Purpose**: Complete order information for order acknowledgement display

**Used in**:
- Order detail view (FR-021)
- Order acknowledgement report (User Story 5)

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `order_id` | `str` | Yes | Unique order identifier | `CUSTOMER_ORDER.ID` |
| `order_date` | `date` | Yes | Date order was placed | `CUSTOMER_ORDER.ORDER_DATE` |
| `customer_po_ref` | `str` | No | Customer's PO reference | `CUSTOMER_ORDER.CUSTOMER_PO_REF` |
| `contact_first_name` | `str` | No | Contact person first name | `CUSTOMER_ORDER.CONTACT_FIRST_NAME` |
| `contact_last_name` | `str` | No | Contact person last name | `CUSTOMER_ORDER.CONTACT_LAST_NAME` |
| `contact_phone` | `str` | No | Contact phone number | `CUSTOMER_ORDER.CONTACT_PHONE` |
| `contact_fax` | `str` | No | Contact fax number | `CUSTOMER_ORDER.CONTACT_FAX` |
| `promise_date` | `date` | No | Promised delivery date | `CUSTOMER_ORDER.PROMISE_DATE` |
| `total_amount` | `Decimal` | Yes | Total order value | `CUSTOMER_ORDER.TOTAL_AMT_ORDERED` |
| `currency_id` | `str` | Yes | Currency code (e.g., "USD") | `CUSTOMER_ORDER.CURRENCY_ID` |
| `terms_description` | `str` | No | Payment terms | `CUSTOMER_ORDER.TERMS_DESCRIPTION` |
| `customer` | `Customer` | Yes | Associated customer | JOIN with `CUSTOMER` table |
| `line_items` | `List[OrderLineItem]` | Yes | Order line items | JOIN with `CUST_ORDER_LINE` table |

**Validation Rules**:
- `order_id`: Non-empty string, max 15 characters
- `order_date`: Valid date
- `contact_phone`: Optional, max 20 characters
- `total_amount`: Non-negative decimal
- `customer`: Must be valid Customer object
- `line_items`: Non-empty list

**Display Notes**:
- Missing optional fields display as "N/A" (FR-024)
- Dates formatted as MM/DD/YYYY (FR-026)
- Currency formatted with symbol (FR-025)

**Python Class**:
```python
@dataclass
class OrderHeader:
    order_id: str
    order_date: date
    customer_po_ref: Optional[str]
    contact_first_name: Optional[str]
    contact_last_name: Optional[str]
    contact_phone: Optional[str]
    contact_fax: Optional[str]
    promise_date: Optional[date]
    total_amount: Decimal
    currency_id: str
    terms_description: Optional[str]
    customer: 'Customer'
    line_items: List['OrderLineItem']

    @property
    def contact_full_name(self) -> str:
        first = self.contact_first_name or ""
        last = self.contact_last_name or ""
        return f"{first} {last}".strip() or "N/A"

    def formatted_date(self) -> str:
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_amount(self) -> str:
        symbol = "$" if self.currency_id == "USD" else self.currency_id
        return f"{symbol}{self.total_amount:,.2f}"
```

---

### 3. Customer

**Purpose**: Customer information including billing and shipping addresses

**Used in**:
- OrderHeader.customer attribute
- Order acknowledgement report display

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `customer_id` | `str` | Yes | Unique customer identifier | `CUSTOMER.ID` |
| `name` | `str` | Yes | Customer company name | `CUSTOMER.NAME` |
| `address_1` | `str` | No | Primary address line 1 | `CUSTOMER.ADDR_1` |
| `address_2` | `str` | No | Primary address line 2 | `CUSTOMER.ADDR_2` |
| `city` | `str` | No | City | `CUSTOMER.CITY` |
| `state` | `str` | No | State/province | `CUSTOMER.STATE` |
| `zip_code` | `str` | No | Postal code | `CUSTOMER.ZIPCODE` |
| `country` | `str` | No | Country | `CUSTOMER.COUNTRY` |
| `bill_to_name` | `str` | No | Billing address name | `CUSTOMER.BILL_TO_NAME` |
| `bill_to_address_1` | `str` | No | Billing address line 1 | `CUSTOMER.BILL_TO_ADDR_1` |
| `bill_to_address_2` | `str` | No | Billing address line 2 | `CUSTOMER.BILL_TO_ADDR_2` |
| `bill_to_address_3` | `str` | No | Billing address line 3 | `CUSTOMER.BILL_TO_ADDR_3` |
| `bill_to_city` | `str` | No | Billing city | `CUSTOMER.BILL_TO_CITY` |
| `bill_to_state` | `str` | No | Billing state | `CUSTOMER.BILL_TO_STATE` |
| `bill_to_zip_code` | `str` | No | Billing postal code | `CUSTOMER.BILL_TO_ZIPCODE` |
| `bill_to_country` | `str` | No | Billing country | `CUSTOMER.BILL_TO_COUNTRY` |

**Validation Rules**:
- `customer_id`: Non-empty string, max 15 characters
- `name`: Non-empty string, max 100 characters
- All address fields: Optional, max 100 characters each

**Python Class**:
```python
@dataclass
class Customer:
    customer_id: str
    name: str
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    bill_to_name: Optional[str] = None
    bill_to_address_1: Optional[str] = None
    bill_to_address_2: Optional[str] = None
    bill_to_address_3: Optional[str] = None
    bill_to_city: Optional[str] = None
    bill_to_state: Optional[str] = None
    bill_to_zip_code: Optional[str] = None
    bill_to_country: Optional[str] = None

    def formatted_ship_to_address(self) -> List[str]:
        """Returns ship-to address as list of non-empty lines"""
        lines = []
        if self.name: lines.append(self.name)
        if self.address_1: lines.append(self.address_1)
        if self.address_2: lines.append(self.address_2)
        city_state_zip = ", ".join(filter(None, [self.city, self.state, self.zip_code]))
        if city_state_zip: lines.append(city_state_zip)
        if self.country: lines.append(self.country)
        return lines if lines else ["N/A"]

    def formatted_bill_to_address(self) -> List[str]:
        """Returns bill-to address as list of non-empty lines"""
        lines = []
        if self.bill_to_name: lines.append(self.bill_to_name)
        if self.bill_to_address_1: lines.append(self.bill_to_address_1)
        if self.bill_to_address_2: lines.append(self.bill_to_address_2)
        if self.bill_to_address_3: lines.append(self.bill_to_address_3)
        city_state_zip = ", ".join(filter(None, [self.bill_to_city, self.bill_to_state, self.bill_to_zip_code]))
        if city_state_zip: lines.append(city_state_zip)
        if self.bill_to_country: lines.append(self.bill_to_country)
        return lines if lines else ["N/A"]
```

---

### 4. OrderLineItem

**Purpose**: Individual line items within an order

**Used in**:
- OrderHeader.line_items list
- Order acknowledgement line items table

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `line_number` | `int` | Yes | Line item sequence number | `CUST_ORDER_LINE.LINE_NO` |
| `order_id` | `str` | Yes | Associated order ID | `CUST_ORDER_LINE.CUST_ORDER_ID` |
| `part_id` | `str` | No | Part identifier | `CUST_ORDER_LINE.PART_ID` |
| `quantity` | `Decimal` | Yes | Order quantity | `CUST_ORDER_LINE.ORDER_QTY` |
| `unit_price` | `Decimal` | Yes | Price per unit | `CUST_ORDER_LINE.UNIT_PRICE` |
| `line_total` | `Decimal` | Yes | Total for line item | `CUST_ORDER_LINE.TOTAL_AMT_ORDERED` |
| `description` | `str` | No | Line item description | `CUST_ORDER_LINE.MISC_REFERENCE` |
| `promise_date` | `date` | No | Line-specific promise date | `CUST_ORDER_LINE.PROMISE_DATE` |

**Computed Fields**:
- `base_lot_id`: Formatted as "{order_id}/{line_number:02d}" (e.g., "4049/01")

**Validation Rules**:
- `line_number`: Positive integer
- `order_id`: Non-empty string matching parent order
- `quantity`: Positive decimal
- `unit_price`: Non-negative decimal
- `line_total`: Non-negative decimal (should equal quantity * unit_price, but use database value)

**Python Class**:
```python
@dataclass
class OrderLineItem:
    line_number: int
    order_id: str
    part_id: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    description: Optional[str]
    promise_date: Optional[date]

    @property
    def base_lot_id(self) -> str:
        return f"{self.order_id}/{self.line_number:02d}"

    def formatted_unit_price(self) -> str:
        return f"${self.unit_price:,.2f}"

    def formatted_line_total(self) -> str:
        return f"${self.line_total:,.2f}"
```

---

## Supporting Entities

### 5. DateRangeFilter

**Purpose**: Represents user-specified date range for filtering orders

**Used in**:
- Date range filter UI component (FR-006 to FR-014)
- Order list filtering logic

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_date` | `date` | No | Filter start date (inclusive) |
| `end_date` | `date` | No | Filter end date (inclusive) |

**Validation Rules**:
- At least one of `start_date` or `end_date` must be provided
- If both provided, `start_date` must be <= `end_date` (FR-008)
- `start_date`: If provided, must be >= 1985-01-01 (historical data start)
- `end_date`: If provided, must be <= current date

**Business Logic**:
- If only `start_date`: Filter orders >= start_date (FR-011)
- If only `end_date`: Filter orders <= end_date (FR-011)
- If both: Filter orders between dates (inclusive) (FR-010)

**Python Class**:
```python
@dataclass
class DateRangeFilter:
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def validate(self) -> bool:
        """Returns True if filter is valid"""
        if self.start_date is None and self.end_date is None:
            return False  # At least one date required

        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                return False  # Start must be before end

        return True

    def to_sql_where_clause(self) -> str:
        """Generate SQL WHERE clause for this filter"""
        if self.start_date and self.end_date:
            return f"ORDER_DATE BETWEEN '{self.start_date}' AND '{self.end_date}'"
        elif self.start_date:
            return f"ORDER_DATE >= '{self.start_date}'"
        elif self.end_date:
            return f"ORDER_DATE <= '{self.end_date}'"
        else:
            return "1=1"  # No filter
```

---

## Entity Relationships

```
OrderSummary
    ├── job_number (PK)
    └── Used for: List display, filtering, search results

OrderHeader
    ├── order_id (PK)
    ├── customer (FK) ──> Customer
    │   └── customer_id (PK)
    └── line_items (1:N) ──> OrderLineItem
        └── (order_id, line_number) (PK)

DateRangeFilter
    └── Used to filter: OrderSummary queries
```

**Relationship Notes**:
- OrderSummary and OrderHeader represent the same physical database record, but with different detail levels
- OrderHeader always includes Customer and OrderLineItem collections
- DateRangeFilter is not persisted, only used for query building

---

## Data Flow

### 1. Application Startup Flow
```
Database → OrderSummary (100 records)
         → QTableView display
         → User selects order
         → Load OrderHeader + Customer + OrderLineItems
         → Display in order detail view
```

### 2. Date Filter Flow
```
User input → DateRangeFilter validation
          → SQL query with date range
          → OrderSummary results
          → QTableView update
```

### 3. Search Flow
```
User input → Search type (job number / customer name)
          → SQL query with WHERE clause
          → OrderSummary results (or single OrderHeader for job number)
          → Display results
```

---

## Validation & Error Handling

### Required Field Violations
- If database returns NULL for required field → Log error, show "N/A" in UI (graceful degradation)
- Missing customer record for order → Show error message "Customer information not found"
- Empty line items for order → Show warning "No line items found for this order"

### Data Type Mismatches
- Invalid date format → Log error, show "Invalid Date"
- Non-numeric amount → Log error, show "$0.00"
- NULL decimal values → Treat as 0.00

### Business Rule Violations
- Negative amounts → Log warning, display absolute value with "(Credit)" notation
- Future order dates → Log warning, display as-is (historical data may have anomalies)

---

## Database Mapping

| Python Class | Database Table | Primary Key |
|--------------|----------------|-------------|
| `OrderSummary` | `CUSTOMER_ORDER` JOIN `CUSTOMER` | `CUSTOMER_ORDER.ID` |
| `OrderHeader` | `CUSTOMER_ORDER` | `CUSTOMER_ORDER.ID` |
| `Customer` | `CUSTOMER` | `CUSTOMER.ID` |
| `OrderLineItem` | `CUST_ORDER_LINE` | `(CUST_ORDER_ID, LINE_NO)` |
| `DateRangeFilter` | N/A (UI only) | N/A |

**See `contracts/database-schema.sql` for complete table definitions and relationships.**

---

## Performance Considerations

### Lazy Loading
- OrderLineItems are NOT loaded until user views order details
- Customer information loaded only when needed (not in OrderSummary)

### Caching Strategy
- OrderSummary list cached after initial load (invalidate on filter/search)
- OrderHeader cached for viewed orders (LRU cache, max 20 entries)
- No persistent caching (per constitution: "Order data displayed only, not cached locally")

### Result Limits
- Default order list: 100 records (FR-001)
- Date range filter: 1000 records max (FR-013)
- Customer name search: 100 results max

---

## Testing Data

### Mock Data for Unit Tests

Located in `tests/fixtures/`:

**`mock_orders.json`**:
```json
[
    {
        "job_number": "4049",
        "customer_name": "THE TRANE COMPANY",
        "order_date": "2000-12-20",
        "total_amount": "1751000.00"
    },
    {
        "job_number": "8113",
        "customer_name": "ARCADIA",
        "order_date": "2005-03-15",
        "total_amount": "250000.00"
    }
]
```

**`mock_customers.json`**:
```json
[
    {
        "customer_id": "TRANE",
        "name": "THE TRANE COMPANY",
        "address_1": "6200 TROUP HIGHWAY",
        "city": "TYLER",
        "state": "TX",
        "zip_code": "75707",
        "country": "USA",
        "bill_to_name": "TRANE RESIDENTIAL SYSTEMS",
        "bill_to_address_1": "PO BOX 981395",
        "bill_to_city": "EL PASO",
        "bill_to_state": "TX",
        "bill_to_zip_code": "79998-1395",
        "bill_to_country": "USA"
    }
]
```

---

---

## Inventory Module Entities

### 6. Part

**Purpose**: Part master data for inventory lookups

**Used in**:
- Part search by part number (RT-005)
- Part detail view display
- Part info tab in Inventory module

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `part_id` | `str` | Yes | Unique part identifier | `PART.ID` |
| `part_number` | `str` | Yes | Part number (same as part_id) | `PART.ID` |
| `description` | `str` | Yes | Part description (short) | `PART.DESCRIPTION` |
| `extended_description` | `str` | No | Extended description | `PART_BINARY.BITS` (TYPE='D') |
| `unit_of_measure` | `str` | Yes | Unit of measure (EA, IN, FT) | `PART.STOCK_UM` |
| `unit_material_cost` | `Decimal` | No | Material cost per unit | `PART.UNIT_MATERIAL_COST` |
| `unit_labor_cost` | `Decimal` | No | Labor cost per unit | `PART.UNIT_LABOR_COST` |
| `unit_burden_cost` | `Decimal` | No | Burden cost per unit | `PART.UNIT_BURDEN_COST` |
| `unit_price` | `Decimal` | No | Selling price per unit | `PART.UNIT_PRICE` |
| `material_code` | `str` | No | Material specification | `PART.MATERIAL_CODE` |
| `qty_on_hand` | `Decimal` | No | Current inventory quantity | `PART.QTY_ON_HAND` |
| `qty_available` | `Decimal` | No | Available for issue | `PART.QTY_AVAILABLE_ISS` |
| `qty_on_order` | `Decimal` | No | Quantity on POs | `PART.QTY_ON_ORDER` |
| `qty_in_demand` | `Decimal` | No | Quantity allocated | `PART.QTY_IN_DEMAND` |
| `drawing_id` | `str` | No | Drawing/blueprint reference | `PART.DRAWING_ID` |
| `drawing_revision` | `str` | No | Drawing revision | `PART.DRAWING_REV_NO` |
| `vendor_id` | `str` | No | Preferred vendor ID | `PART.PREF_VENDOR_ID` |
| `vendor_name` | `str` | No | Preferred vendor name | `VENDOR.NAME` (JOIN) |
| `is_purchased` | `bool` | Yes | Y/N if part is purchased | `PART.PURCHASED = 'Y'` |
| `is_fabricated` | `bool` | Yes | Y/N if part is fabricated | `PART.FABRICATED = 'Y'` |
| `is_stocked` | `bool` | Yes | Y/N if part is stocked | `PART.STOCKED = 'Y'` |
| `weight` | `Decimal` | No | Part weight | `PART.WEIGHT` |
| `weight_um` | `str` | No | Weight unit of measure | `PART.WEIGHT_UM` |

**Validation Rules**:
- `part_number`: Non-empty string, max 30 characters
- `description`: Non-empty string, max 40 characters
- All cost/price fields: Non-negative decimal
- All quantity fields: Non-negative decimal

**Python Class**:
```python
@dataclass
class Part:
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
        """Calculate total unit cost (material + labor + burden)"""
        material = self.unit_material_cost or Decimal('0')
        labor = self.unit_labor_cost or Decimal('0')
        burden = self.unit_burden_cost or Decimal('0')
        return material + labor + burden

    def formatted_unit_price(self) -> str:
        if self.unit_price:
            return f"${self.unit_price:,.2f}"
        return "N/A"
```

---

### 7. WhereUsed

**Purpose**: Records of where a part has been used (orders, work orders)

**Used in**:
- "Where Used" tab in Inventory module
- Part usage history display

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `part_number` | `str` | Yes | Part identifier | `INVENTORY_TRANS.PART_ID` |
| `cust_order_id` | `str` | No | Customer order reference | `INVENTORY_TRANS.CUST_ORDER_ID` |
| `cust_order_line_no` | `int` | No | Order line number | `INVENTORY_TRANS.CUST_ORDER_LINE_NO` |
| `work_order` | `str` | No | Work order (base_id/lot_id) | `WORKORDER_BASE_ID + '/' + WORKORDER_LOT_ID` |
| `transaction_date` | `date` | Yes | When part was used | `INVENTORY_TRANS.TRANSACTION_DATE` |
| `quantity` | `Decimal` | Yes | Quantity used/issued | `INVENTORY_TRANS.QTY` |
| `customer_name` | `str` | No | Customer name (if order) | `CUSTOMER.NAME` (JOIN) |
| `warehouse_id` | `str` | No | Source warehouse | `INVENTORY_TRANS.WAREHOUSE_ID` |
| `location_id` | `str` | No | Source location | `INVENTORY_TRANS.LOCATION_ID` |

**Validation Rules**:
- `part_number`: Non-empty string
- `transaction_date`: Valid date
- `quantity`: Positive decimal
- At least one of `cust_order_id` or `work_order` should be populated

**Python Class**:
```python
@dataclass
class WhereUsed:
    part_number: str
    cust_order_id: Optional[str]
    cust_order_line_no: Optional[int]
    work_order: Optional[str]
    transaction_date: date
    quantity: Decimal
    customer_name: Optional[str]
    warehouse_id: Optional[str]
    location_id: Optional[str]

    @property
    def order_reference(self) -> str:
        """Returns order reference (order ID or work order)"""
        if self.cust_order_id:
            return f"Order {self.cust_order_id}"
        elif self.work_order:
            return f"WO {self.work_order}"
        return "Internal/Stock"

    def formatted_date(self) -> str:
        return self.transaction_date.strftime("%m/%d/%Y")
```

---

### 8. PurchaseHistory

**Purpose**: Purchase order history for a part

**Used in**:
- "Purchase History" tab in Inventory module
- Vendor and PO tracking

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `part_number` | `str` | Yes | Part identifier | `PURC_ORDER_LINE.PART_ID` |
| `po_number` | `str` | Yes | Purchase order number | `PURCHASE_ORDER.ID` |
| `line_number` | `int` | Yes | PO line number | `PURC_ORDER_LINE.LINE_NO` |
| `order_date` | `date` | Yes | PO date | `PURCHASE_ORDER.ORDER_DATE` |
| `vendor_name` | `str` | Yes | Vendor name | `VENDOR.NAME` |
| `vendor_id` | `str` | Yes | Vendor identifier | `PURCHASE_ORDER.VENDOR_ID` |
| `vendor_part_id` | `str` | No | Vendor's part number | `PURC_ORDER_LINE.VENDOR_PART_ID` |
| `quantity` | `Decimal` | Yes | Ordered quantity | `PURC_ORDER_LINE.USER_ORDER_QTY` |
| `unit_price` | `Decimal` | Yes | Price per unit | `PURC_ORDER_LINE.UNIT_PRICE` |
| `line_total` | `Decimal` | Yes | Total for PO line | `PURC_ORDER_LINE.TOTAL_AMT_ORDERED` |
| `desired_receive_date` | `date` | No | Requested delivery date | `PURC_ORDER_LINE.DESIRED_RECV_DATE` |
| `last_received_date` | `date` | No | Last receipt date | `PURC_ORDER_LINE.LAST_RECEIVED_DATE` |

**Validation Rules**:
- `po_number`: Non-empty string
- `order_date`: Valid date
- `quantity`: Positive decimal
- `unit_price`: Non-negative decimal
- `line_total`: Non-negative decimal

**Python Class**:
```python
@dataclass
class PurchaseHistory:
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

    def formatted_order_date(self) -> str:
        return self.order_date.strftime("%m/%d/%Y")

    def formatted_unit_price(self) -> str:
        return f"${self.unit_price:,.2f}"

    def formatted_line_total(self) -> str:
        return f"${self.line_total:,.2f}"
```

---

## Engineering Module Entities

### 9. BOMNode

**Purpose**: Represents a node in the Bill of Materials hierarchy

**Used in**:
- BOM tree display in Engineering module
- Hierarchical part structure navigation

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `job_number` | `str` | Yes | Job/project number | `WORK_ORDER.BASE_ID` |
| `lot_id` | `str` | Yes | Assembly/lot identifier | `WORK_ORDER.LOT_ID` |
| `sub_id` | `str` | Yes | Component sequence | `WORK_ORDER.SUB_ID` |
| `base_lot_id` | `str` | Yes | Formatted job/lot (e.g., "8113/26") | `BASE_ID + '/' + LOT_ID` |
| `part_id` | `str` | No | Part identifier | `WORK_ORDER.PART_ID` |
| `description` | `str` | No | Part/assembly description | `PART.DESCRIPTION` |
| `drawing_id` | `str` | No | Drawing number | `WORK_ORDER.DRAWING_ID` or `PART.DRAWING_ID` |
| `drawing_revision` | `str` | No | Drawing revision | `WORK_ORDER.DRAWING_REV_NO` |
| `quantity` | `Decimal` | No | Desired quantity | `WORK_ORDER.DESIRED_QTY` |
| `material_code` | `str` | No | Material specification | `PART.MATERIAL_CODE` |
| `node_type` | `str` | Yes | Node type: 'A', 'M', 'P', 'O' | Computed from PART flags |
| `is_assembly` | `bool` | Yes | True if assembly/header | `node_type == 'A'` |
| `is_manufactured` | `bool` | Yes | True if manufactured part | `node_type == 'M'` |
| `is_purchased` | `bool` | Yes | True if purchased part | `node_type == 'P'` |
| `depth` | `int` | Yes | Tree depth (0=root, 1=assembly, 2+=parts) | Computed during tree build |
| `parent_key` | `str` | No | Parent node key for hierarchy | Computed (LOT_ID for parts) |
| `is_loaded` | `bool` | Yes | True if children have been loaded | Used for lazy loading |

**Node Type Classification**:
- **'A' (Assembly)**: `FABRICATED='Y'` AND has child work orders
- **'M' (Manufactured)**: `FABRICATED='Y'` AND `PURCHASED!='Y'`
- **'P' (Purchased)**: `PURCHASED='Y'`
- **'O' (Other)**: Default fallback

**Validation Rules**:
- `job_number`: Non-empty string
- `lot_id`: Non-empty string
- `sub_id`: Non-empty string
- `node_type`: Must be 'A', 'M', 'P', or 'O'
- `depth`: Non-negative integer

**Python Class**:
```python
@dataclass
class BOMNode:
    job_number: str
    lot_id: str
    sub_id: str
    base_lot_id: str
    part_id: Optional[str]
    description: Optional[str]
    drawing_id: Optional[str]
    drawing_revision: Optional[str]
    quantity: Optional[Decimal]
    material_code: Optional[str]
    node_type: str
    is_assembly: bool
    is_manufactured: bool
    is_purchased: bool
    depth: int
    parent_key: Optional[str]
    is_loaded: bool = False

    @property
    def display_text(self) -> str:
        """Returns formatted text for tree display"""
        parts = [self.base_lot_id]
        if self.description:
            parts.append(self.description)
        if self.drawing_id:
            parts.append(f"Dwg: {self.drawing_id}")
        return " - ".join(parts)

    @property
    def color_code(self) -> str:
        """Returns color for tree display (white/black/red)"""
        if self.is_assembly:
            return "blue"  # Assembly (white in Visual, blue for visibility)
        elif self.is_manufactured:
            return "black"  # Manufactured part
        elif self.is_purchased:
            return "red"  # Purchased part
        return "gray"  # Other

    @property
    def unique_key(self) -> str:
        """Returns unique identifier for this node"""
        return f"{self.job_number}/{self.lot_id}/{self.sub_id}"
```

---

### 10. Job

**Purpose**: Job/project header information for Engineering module

**Used in**:
- Job selection and BOM root display
- Job metadata display

**Attributes**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `job_number` | `str` | Yes | Job identifier | `WORK_ORDER.BASE_ID` |
| `customer_id` | `str` | No | Customer reference | `WORK_ORDER.WBS_CUST_ORDER_ID` |
| `customer_name` | `str` | No | Customer name | `CUSTOMER.NAME` (JOIN) |
| `description` | `str` | No | Job description | From CUSTOMER_ORDER or first WO |
| `start_date` | `date` | No | Job start date | Min WORK_ORDER date |
| `assembly_count` | `int` | Yes | Number of assemblies | Count distinct LOT_IDs |

**Validation Rules**:
- `job_number`: Non-empty string
- `assembly_count`: Non-negative integer

**Python Class**:
```python
@dataclass
class Job:
    job_number: str
    customer_id: Optional[str]
    customer_name: Optional[str]
    description: Optional[str]
    start_date: Optional[date]
    assembly_count: int

    @property
    def display_name(self) -> str:
        """Returns formatted job name for display"""
        if self.description:
            return f"Job {self.job_number} - {self.description}"
        return f"Job {self.job_number}"
```

---

## Entity Relationships (Updated)

```
Sales Module:
  OrderSummary ──> OrderHeader
                    ├─> Customer
                    └─> OrderLineItem (1:N)

Inventory Module:
  Part ─┬─> WhereUsed (1:N)
        └─> PurchaseHistory (1:N)

Engineering Module:
  Job ──> BOMNode (1:N, hierarchical)
          ├─> BOMNode children (1:N, self-referential)
          └─> Part (N:1, via part_id)

Cross-Module:
  WhereUsed ──> OrderHeader (via cust_order_id)
  WhereUsed ──> BOMNode (via work_order)
  BOMNode ──> Part (via part_id)
```

---

## Module-Specific Data Flow

### Inventory Module Flow
```
User input: part_number
  → Part lookup (PART table)
  → Display Part details
  → User clicks "Where Used" tab
     → WhereUsed query (INVENTORY_TRANS)
     → Display usage history
  → User clicks "Purchase History" tab
     → PurchaseHistory query (PURC_ORDER_LINE)
     → Display PO history
```

### Engineering Module Flow
```
User input: job_number
  → Job lookup (aggregate WORK_ORDER data)
  → Load top-level assemblies (LOT_IDs, collapsed)
  → User expands assembly
     → Lazy load: query parts for that LOT_ID
     → Build BOMNode children
     → Display in tree with color coding
  → User expands part (if has children)
     → Recursive lazy load
```

---

## Database Mapping (Updated)

| Python Class | Database Table(s) | Primary Key |
|--------------|-------------------|-------------|
| **Sales Module** |
| `OrderSummary` | `CUSTOMER_ORDER` + `CUSTOMER` | `CUSTOMER_ORDER.ID` |
| `OrderHeader` | `CUSTOMER_ORDER` | `CUSTOMER_ORDER.ID` |
| `Customer` | `CUSTOMER` | `CUSTOMER.ID` |
| `OrderLineItem` | `CUST_ORDER_LINE` | `(CUST_ORDER_ID, LINE_NO)` |
| `DateRangeFilter` | N/A (UI only) | N/A |
| **Inventory Module** |
| `Part` | `PART` + `PART_BINARY` + `VENDOR` | `PART.ID` |
| `WhereUsed` | `INVENTORY_TRANS` + `CUSTOMER_ORDER` + `CUSTOMER` | N/A (transaction log) |
| `PurchaseHistory` | `PURC_ORDER_LINE` + `PURCHASE_ORDER` + `VENDOR` | `(PURC_ORDER_ID, LINE_NO)` |
| **Engineering Module** |
| `BOMNode` | `WORK_ORDER` + `PART` | `(BASE_ID, LOT_ID, SUB_ID)` |
| `Job` | `WORK_ORDER` (aggregate) + `CUSTOMER_ORDER` | `BASE_ID` |

---

## Testing Data (Updated)

### Inventory Module Test Data

**Test Parts** (validated in database):
- **F0195** - "SLW 1/2" - 995 POs, Vendor: KARRIC
- **PF004** - "1/4 - 20 x 3/4" BOLT GRADE"
- **PP001** - "ISYS MODULE CLIP"

**Mock Files**:
- `tests/fixtures/mock_parts.json`
- `tests/fixtures/mock_where_used.json`
- `tests/fixtures/mock_purchase_history.json`

### Engineering Module Test Data

**Test Jobs** (validated in database):
- **Job 8113** - 702 work orders, 15 assemblies, 330+ parts in assembly 26
- **Job 8059** - 33 work orders, 4 assemblies

**Mock Files**:
- `tests/fixtures/mock_bom_nodes.json`
- `tests/fixtures/mock_jobs.json`

---

## Summary

This data model provides:
- ✅ Clear separation between list view (OrderSummary) and detail view (OrderHeader) for Sales module
- ✅ Comprehensive part data model with where-used and purchase history for Inventory module
- ✅ Hierarchical BOM structure with lazy loading support for Engineering module
- ✅ Type-safe Python dataclasses with validation across all modules
- ✅ Proper handling of NULL values (Optional types)
- ✅ Formatted display methods for UI rendering
- ✅ Read-only design (no database write operations)
- ✅ Performance-optimized with lazy loading and caching
- ✅ Comprehensive test fixtures for unit testing
- ✅ Cross-module entity relationships (WhereUsed → OrderHeader, BOMNode → Part)

**Total Entities**: 10 (4 Sales + 3 Inventory + 2 Engineering + 1 UI helper)

All entities map directly to Visual database tables with no schema modifications required (constitution compliance).
