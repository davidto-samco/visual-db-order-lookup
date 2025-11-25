# Data Model: Engineering Module - Work Order Hierarchy

**Date**: 2025-01-14
**Feature**: 003-engineering-work-order-hierarchy
**Status**: Phase 1 Design

## Entity Overview

The Engineering module manages hierarchical work order data with 7 entity types representing different aspects of manufacturing orders:

```
WorkOrder (Header)
    ├── Operation (Routing/Operations)
    │   └── Requirement (Materials per operation)
    │       └── Part (Component details)
    ├── LaborTicket (Labor transactions)
    ├── InventoryTransaction (Material transactions)
    └── WIPBalance (WIP costs)
```

##

 Entity Definitions

### 1. WorkOrder (Header)

Represents a manufacturing or engineering work order with basic information.

```python
@dataclass
class WorkOrder:
    """Work order header from WORK_ORDER table."""

    # Primary key (composite)
    base_id: str          # BASE_ID (varchar 30) - base work order identifier
    lot_id: str           # LOT_ID (varchar 30) - lot identifier
    sub_id: str           # SUB_ID (varchar 30) - sub identifier

    # Manufactured part
    part_id: str          # PART_ID (varchar 30) - what's being manufactured
    part_description: Optional[str]  # From PART table join

    # Order details
    order_qty: Decimal    # ORDER_QTY - quantity to produce
    type: str             # TYPE (char 1) - M=Manufacturing, W=Work Order
    status: str           # STATUS (varchar 10) - Open, Closed, etc.

    # Dates
    start_date: Optional[date]     # START_DATE
    complete_date: Optional[date]  # COMPLETE_DATE
    created_date: datetime         # Date work order created

    def formatted_id(self) -> str:
        """Format work order ID as displayed: BASE_ID[-SUB_ID]/LOT_ID."""
        if self.sub_id:
            return f"{self.base_id}-{self.sub_id}/{self.lot_id}"
        return f"{self.base_id}/{self.lot_id}"

    def formatted_status(self) -> str:
        """Format status with prefix: [C] for Closed."""
        if self.status == "Closed":
            return "[C]"
        return f"[{self.status[0]}]"  # [O] for Open, etc.

    def formatted_qty(self) -> str:
        """Format quantity as displayed: 1.0000."""
        return f"{self.order_qty:.4f}"
```

**Database Mapping**:
- Source: `WORK_ORDER` table
- Join: `LEFT JOIN PART ON WORK_ORDER.PART_ID = PART.ID`
- Primary Key: `(BASE_ID, LOT_ID, SUB_ID)`

### 2. Operation (Routing Step)

Represents a single manufacturing operation/routing step in the work order.

```python
@dataclass
class Operation:
    """Manufacturing operation from OPERATION table."""

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Operation identification
    sequence: int         # SEQUENCE (smallint) - operation sequence number
    operation_id: str     # OPERATION_ID (varchar 30)
    description: str      # DESCRIPTION (varchar 255)

    # Department/routing
    department_id: Optional[str]  # DEPARTMENT_ID (varchar 30)

    # Time standards
    setup_hrs: Decimal    # SETUP_HRS - setup time
    run_hrs: Decimal      # RUN_HRS - run time per unit

    # Status
    status: Optional[str] # Operation status

    def formatted_sequence(self) -> str:
        """Format sequence as displayed: [10]."""
        return f"[{self.sequence}]"

    def formatted_description(self) -> str:
        """Format operation for display: [10] - GEAR CUTTING."""
        return f"{self.formatted_sequence()} - {self.description}"

    def formatted_hours(self) -> str:
        """Format time info: Setup: 0.50 Hrs, Run: 1.00 Hrs/unit."""
        return f"Setup: {self.setup_hrs:.2f} Hrs, Run: {self.run_hrs:.2f} Hrs/unit"
```

**Database Mapping**:
- Source: `OPERATION` table
- Foreign Key: `(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID)`
- Order: `ORDER BY SEQUENCE`

### 3. Requirement (Material per Operation)

Represents a component/material required for a specific operation.

```python
@dataclass
class Requirement:
    """BOM requirement from REQUIREMENT table."""

    # Foreign key to work order and operation
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str
    operation_seq_no: int  # Links to Operation.sequence

    # Part information
    part_id: str          # PART_ID (varchar 30) - required component
    part_description: Optional[str]  # From PART table join
    part_type: Optional[str]         # From PART table

    # Quantities
    qty_per: Decimal      # QTY_PER (decimal 15,8) - quantity per assembly
    fixed_qty: Decimal    # FIXED_QTY (decimal 14,4) - fixed quantity
    scrap_percent: Decimal  # SCRAP_PERCENT (decimal 5,2)

    # Additional fields
    piece_no: Optional[int]  # PIECE_NO - piece number identifier

    def formatted_part(self) -> str:
        """Format part for display: M28803 - TOP BEARING COVER."""
        return f"{self.part_id} - {self.part_description or 'Unknown'}"

    def formatted_qty(self) -> str:
        """Format quantity: Qty: 1.0000."""
        return f"Qty: {self.qty_per:.4f}"

    def formatted_scrap(self) -> str:
        """Format scrap percentage: 5.00%."""
        return f"{self.scrap_percent:.2f}%"

    def formatted_display(self) -> str:
        """Full display: M28803 - TOP BEARING COVER - Qty: 1.0000."""
        return f"{self.formatted_part()} - {self.formatted_qty()}"
```

**Database Mapping**:
- Source: `REQUIREMENT` table
- Joins: `LEFT JOIN PART ON REQUIREMENT.PART_ID = PART.ID`
- Foreign Key: `(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID, OPERATION_SEQ_NO)`
- Order: `ORDER BY PART_ID`

### 4. Part (Component Detail)

Extended part information for requirements (reuses existing Part model from Inventory module).

```python
@dataclass
class Part:
    """Part master data from PART table (existing model - reference only)."""

    id: str                    # Part number (PK)
    description: str           # Part description
    type: str                  # Part type (Purchased, Manufactured, etc.)
    unit_of_measure: str       # Unit of measure
    unit_material_cost: Decimal
    unit_labor_cost: Decimal
    unit_burden_cost: Decimal

    # (Other fields from existing Part model)
```

**Note**: This entity already exists in `visual_order_lookup/database/models.py`. No new model needed, just reference existing Part class.

### 5. LaborTicket (Labor Transaction)

Represents labor hours charged to work order operations.

```python
@dataclass
class LaborTicket:
    """Labor transaction from LABOR_TICKET table."""

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str
    operation_seq: Optional[int]  # Which operation (may be NULL for non-operation labor)

    # Employee information
    employee_id: str      # EMPLOYEE_ID (varchar 30)
    employee_name: Optional[str]  # From EMPLOYEE table join (if available)

    # Time tracking
    labor_date: date      # LABOR_DATE
    setup_hrs: Decimal    # SETUP_HRS
    run_hrs: Decimal      # RUN_HRS
    total_hrs: Decimal    # Calculated: setup_hrs + run_hrs

    # Cost
    labor_rate: Decimal   # LABOR_RATE ($/hr)
    total_cost: Decimal   # Calculated: total_hrs * labor_rate

    def formatted_employee(self) -> str:
        """Format employee: Employee 950."""
        if self.employee_name:
            return f"{self.employee_name} ({self.employee_id})"
        return f"Employee {self.employee_id}"

    def formatted_date(self) -> str:
        """Format date: 8/15/2011."""
        return self.labor_date.strftime("%m/%d/%Y")

    def formatted_hours(self) -> str:
        """Format hours: 0.50 Hrs."""
        return f"{self.total_hrs:.2f} Hrs"

    def formatted_display(self) -> str:
        """Full display: [LABOR] Employee 950 - 8/15/2011 - 0.50 Hrs."""
        return f"[LABOR] {self.formatted_employee()} - {self.formatted_date()} - {self.formatted_hours()}"
```

**Database Mapping**:
- Source: `LABOR_TICKET` table
- Foreign Key: `(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID)`
- Optional Join: `LEFT JOIN EMPLOYEE ON LABOR_TICKET.EMPLOYEE_ID = EMPLOYEE.ID`
- Order: `ORDER BY LABOR_DATE DESC`

### 6. InventoryTransaction (Material Transaction)

Represents material issues, returns, or scrap transactions for work orders.

```python
@dataclass
class InventoryTransaction:
    """Material transaction from INVENTORY_TRANS table."""

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Part and transaction
    part_id: str          # PART_ID (varchar 30)
    part_description: Optional[str]  # From PART table join
    trans_type: str       # TRANS_TYPE (varchar 10) - Issue, Return, Scrap
    quantity: Decimal     # QUANTITY

    # Location and timing
    trans_date: datetime  # TRANS_DATE
    location_id: Optional[str]  # LOCATION_ID (varchar 30) - warehouse location

    # Additional tracking
    lot_serial: Optional[str]  # LOT_SERIAL_NO - lot/serial tracking

    def formatted_type(self) -> str:
        """Format transaction type: Issue, Return, Scrap."""
        return self.trans_type

    def formatted_date(self) -> str:
        """Format date: 8/15/2011."""
        return self.trans_date.strftime("%m/%d/%Y")

    def formatted_qty(self) -> str:
        """Format quantity: 1.0000."""
        return f"{self.quantity:.4f}"

    def formatted_display(self) -> str:
        """Full display: [MATERIAL] M28803 - Issue - 1.0000 - 8/15/2011."""
        return f"[MATERIAL] {self.part_id} - {self.trans_type} - {self.formatted_qty()} - {self.formatted_date()}"
```

**Database Mapping**:
- Source: `INVENTORY_TRANS` table
- Join: `LEFT JOIN PART ON INVENTORY_TRANS.PART_ID = PART.ID`
- Foreign Key: `(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID)`
- Filter: `WHERE WORKORDER_BASE_ID IS NOT NULL` (only WO-related transactions)
- Order: `ORDER BY TRANS_DATE DESC`

### 7. WIPBalance (Work-in-Progress Costs)

Represents accumulated costs for a work order.

```python
@dataclass
class WIPBalance:
    """WIP cost accumulation from WIP_BALANCE table."""

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Cost breakdown
    material_cost: Decimal  # MATERIAL_COST
    labor_cost: Decimal     # LABOR_COST
    burden_cost: Decimal    # BURDEN_COST (overhead)
    total_cost: Decimal     # TOTAL_COST (sum of above)

    # Additional tracking
    last_updated: Optional[datetime]  # When costs were last calculated

    def formatted_material(self) -> str:
        """Format material cost: Material Cost: $1,250.00."""
        return f"Material Cost: ${self.material_cost:,.2f}"

    def formatted_labor(self) -> str:
        """Format labor cost: Labor Cost: $450.00."""
        return f"Labor Cost: ${self.labor_cost:,.2f}"

    def formatted_burden(self) -> str:
        """Format burden cost: Burden Cost: $200.00."""
        return f"Burden Cost: ${self.burden_cost:,.2f}"

    def formatted_total(self) -> str:
        """Format total cost: Total Cost: $1,900.00."""
        return f"Total Cost: ${self.total_cost:,.2f}"

    def formatted_display(self) -> str:
        """Full display: [WIP] Material: $1,250.00, Labor: $450.00, Burden: $200.00, Total: $1,900.00."""
        return f"[WIP] {self.formatted_material()}, {self.formatted_labor()}, {self.formatted_burden()}, {self.formatted_total()}"
```

**Database Mapping**:
- Source: `WIP_BALANCE` table
- Primary Key: `(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID)`
- Note: Typically one record per work order

## Entity Relationships

```
WorkOrder (1) ────┬──── (0..*) Operation
                  │         └──── (0..*) Requirement
                  │                   └──── (1) Part
                  │
                  ├──── (0..*) LaborTicket
                  ├──── (0..*) InventoryTransaction
                  └──── (0..1) WIPBalance
```

### Relationship Rules

1. **WorkOrder → Operation**: One-to-many
   - A work order may have 0 to N operations (routing steps)
   - Operations ordered by SEQUENCE

2. **Operation → Requirement**: One-to-many
   - Each operation may require 0 to N parts/materials
   - Requirements specific to operation (same part may appear in multiple operations)

3. **Requirement → Part**: Many-to-one
   - Multiple requirements may reference same Part
   - Part information comes from PART master table

4. **WorkOrder → LaborTicket**: One-to-many
   - Work order may have 0 to N labor transactions
   - Labor may or may not be tied to specific operation

5. **WorkOrder → InventoryTransaction**: One-to-many
   - Work order may have 0 to N material transactions
   - Transactions include issues, returns, scrap

6. **WorkOrder → WIPBalance**: One-to-zero-or-one
   - Each work order has at most one WIP balance record
   - Balance accumulates costs from labor and materials

## Validation Rules

### WorkOrder
- `base_id`, `lot_id`, `sub_id` cannot be empty
- `order_qty` must be > 0
- `type` must be 'M' or 'W'
- `status` must be valid status code

### Operation
- `sequence` must be > 0
- `setup_hrs` >= 0
- `run_hrs` >= 0
- Must belong to valid WorkOrder

### Requirement
- `part_id` must exist in PART table
- `qty_per` must be > 0 (or `fixed_qty` > 0)
- `scrap_percent` >= 0 and <= 100
- Must belong to valid Operation

### LaborTicket
- `labor_date` cannot be future date
- `total_hrs` = `setup_hrs` + `run_hrs` must be > 0
- `labor_rate` >= 0

### InventoryTransaction
- `quantity` must be non-zero
- `trans_type` must be valid (Issue, Return, Scrap)
- `trans_date` cannot be future date

### WIPBalance
- All cost fields >= 0
- `total_cost` should equal `material_cost` + `labor_cost` + `burden_cost`

## State Transitions

### WorkOrder Status
```
[Created] → [Open] → [In Progress] → [Closed]
              ↓
          [Cancelled]
```

**Note**: This application is read-only, so state transitions are informational only. Work order status changes happen in VISUAL Enterprise or current production system.

## Tree Node Data Structure

For UI tree representation, each node stores:

```python
@dataclass
class TreeNodeData:
    """Data stored in QTreeWidgetItem.data(0, Qt.UserRole)."""

    node_type: str        # "HEADER", "OPERATION", "REQUIREMENT", "LABOR", "MATERIAL", "WIP"
    base_id: str
    lot_id: str
    sub_id: str

    # Type-specific fields
    operation_seq: Optional[int]  # For OPERATION, REQUIREMENT nodes
    part_id: Optional[str]        # For REQUIREMENT nodes
    trans_id: Optional[int]       # For LABOR, MATERIAL nodes

    # Lazy loading flag
    children_loaded: bool = False

    # Display data (cached)
    display_text: str
    entity_data: Any      # Reference to actual dataclass (WorkOrder, Operation, etc.)
```

This structure enables:
- Type-specific lazy loading queries
- Caching of loaded children
- Context-aware tree operations (expand, export, etc.)

## Next Phase: API Contracts

Phase 1 will continue with:
- WorkOrderService interface definition (contracts/engineering_service.yaml)
- SQL query specifications (contracts/work_order_queries.sql)
- Tree control interface specification
