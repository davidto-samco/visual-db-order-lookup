"""Work Order data models for Engineering Module.

This module defines dataclasses for work order hierarchy entities:
- WorkOrder: Manufacturing work order header
- Operation: Routing step within work order
- Requirement: Material requirement for operation
- LaborTicket: Labor transaction against work order
- InventoryTransaction: Material transaction against work order
- WIPBalance: Work-in-progress cost accumulation

All models include formatting methods for UI display.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class WorkOrder:
    """Work order header from WORK_ORDER table.

    Represents a manufacturing or engineering work order with basic information.
    Composite primary key: (base_id, lot_id, sub_id)
    """

    # Primary key (composite)
    base_id: str  # BASE_ID (varchar 30) - base work order identifier
    lot_id: str  # LOT_ID (varchar 30) - lot identifier
    sub_id: str  # SUB_ID (varchar 30) - sub identifier (empty string '' for main)

    # Manufactured part
    part_id: str  # PART_ID (varchar 30) - what's being manufactured
    part_description: Optional[str] = None  # From PART table join

    # Order details
    order_qty: Decimal = Decimal('0')  # ORDER_QTY - quantity to produce
    type: str = 'M'  # TYPE (char 1) - M=Manufacturing, W=Work Order
    status: str = 'Open'  # STATUS (varchar 10) - Open, Closed, etc.

    # Dates
    start_date: Optional[date] = None  # SCHED_START_DATE
    complete_date: Optional[date] = None  # CLOSE_DATE
    create_date: Optional[datetime] = None  # CREATE_DATE - when work order created
    desired_want_date: Optional[date] = None  # DESIRED_WANT_DATE - customer requested date
    sched_finish_date: Optional[date] = None  # SCHED_FINISH_DATE - scheduled finish date
    desired_rls_date: Optional[date] = None  # DESIRED_RLS_DATE - desired release date

    # Notes from WORKORDER_BINARY table
    notes: Optional[str] = None  # NOTES field from WORKORDER_BINARY

    # Aggregate counts for tree structure (lazy loading indicators)
    operation_count: int = 0
    labor_ticket_count: int = 0
    inventory_trans_count: int = 0

    def formatted_id(self) -> str:
        """Format work order ID as displayed: BASE_ID[-SUB_ID]/LOT_ID.

        Returns:
            Formatted ID string (e.g., "8113/26" or "8113-A/26")
        """
        if self.sub_id and self.sub_id != '0':
            return f"{self.base_id}-{self.sub_id}/{self.lot_id}"
        return f"{self.base_id}/{self.lot_id}"

    def formatted_status(self) -> str:
        """Format status with prefix: [C] for Closed.

        Returns:
            Status prefix (e.g., "[C]", "[O]")
        """
        if self.status and self.status.upper() == "CLOSED":
            return "[C]"
        if self.status:
            return f"[{self.status[0].upper()}]"
        return "[?]"

    def formatted_qty(self) -> str:
        """Format quantity as displayed: 1.0000.

        Returns:
            Formatted quantity with 4 decimal places
        """
        return f"{self.order_qty:.4f}"

    def formatted_display(self) -> str:
        """Full display format for tree root node.

        Returns:
            Complete work order display string
        """
        status_prefix = self.formatted_status()
        wo_id = self.formatted_id()
        qty = self.formatted_qty()
        desc = self.part_description or self.part_id
        return f"{status_prefix} {wo_id} - {qty} - {desc}"

    def formatted_date_diff(self) -> str:
        """Calculate difference between DESIRED_WANT_DATE and SCHED_FINISH_DATE.

        Returns negative number if behind schedule (finish date is after want date).

        Returns:
            Formatted date difference string (e.g., "-77.33")
        """
        if self.desired_want_date and self.sched_finish_date:
            diff_days = (self.desired_want_date - self.sched_finish_date).days
            # Negative means behind schedule (finish after want date)
            return f"{diff_days}"
        return ""

    def formatted_dates(self) -> str:
        """Format dates for display in column 2.

        Format: (SCHED_START_DATE) - (SCHED_FINISH_DATE)
        Example: (10/31/2011) - (10/16/2011)
        If no data: 0 - 0

        Returns:
            Formatted date range string
        """
        start_str = self.start_date.strftime('(%m/%d/%Y)') if self.start_date else '0'
        finish_str = self.sched_finish_date.strftime('(%m/%d/%Y)') if self.sched_finish_date else '0'

        return f"{start_str} - {finish_str}"


@dataclass
class Operation:
    """Manufacturing operation from OPERATION table.

    Represents a single manufacturing operation/routing step in the work order.
    Foreign key: (workorder_base_id, workorder_lot_id, workorder_sub_id)
    """

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Operation identification
    sequence: int  # SEQUENCE (smallint) - operation sequence number
    operation_id: str  # OPERATION_ID (varchar 30)
    description: str  # DESCRIPTION (varchar 255)

    # Department/routing
    department_id: Optional[str] = None  # DEPARTMENT_ID (varchar 30)

    # Time standards
    setup_hrs: Decimal = Decimal('0')  # SETUP_HRS - setup time
    run_hrs: Decimal = Decimal('0')  # RUN_HRS - run time per unit

    # Status
    status: Optional[str] = None  # Operation status

    # Aggregate count for lazy loading
    requirement_count: int = 0

    def formatted_sequence(self) -> str:
        """Format sequence as displayed: [10].

        Returns:
            Bracketed sequence number
        """
        return f"[{self.sequence}]"

    def formatted_description(self) -> str:
        """Format operation for display: [10] - GEAR CUTTING.

        Returns:
            Sequence + description (or operation_id if description is empty)
        """
        display_text = self.description if self.description else self.operation_id
        return f"{self.formatted_sequence()} - {display_text}"

    def formatted_hours(self) -> str:
        """Format time info: Setup: 0.50 Hrs, Run: 1.00 Hrs/unit.

        Returns:
            Setup and run hours formatted
        """
        return f"Setup: {self.setup_hrs:.2f} Hrs, Run: {self.run_hrs:.2f} Hrs/unit"

    def formatted_display(self) -> str:
        """Full display format for tree node.

        Returns:
            Complete operation display string
        """
        return f"{self.formatted_description()} - {self.formatted_hours()}"


@dataclass
class Requirement:
    """BOM requirement from REQUIREMENT table.

    Represents a component/material required for a specific operation.
    Foreign key: (workorder_base_id, workorder_lot_id, workorder_sub_id, operation_seq_no)
    """

    # Foreign key to work order and operation
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str
    operation_seq_no: int  # Links to Operation.sequence

    # Part information
    part_id: str  # PART_ID (varchar 30) - required component
    part_description: Optional[str] = None  # From PART table join
    part_type: Optional[str] = None  # From PART table
    unit_of_measure: Optional[str] = None  # From PART table

    # Quantities
    qty_per: Decimal = Decimal('0')  # QTY_PER (decimal 15,8) - quantity per assembly
    fixed_qty: Decimal = Decimal('0')  # FIXED_QTY (decimal 14,4) - fixed quantity
    scrap_percent: Decimal = Decimal('0')  # SCRAP_PERCENT (decimal 5,2)

    # Additional fields
    piece_no: Optional[int] = None  # PIECE_NO - piece number identifier

    # CRITICAL: Sub work order link (new discovery from user)
    subord_wo_sub_id: Optional[str] = None  # SUBORD_WO_SUB_ID - child work order link
    subord_wo_status: Optional[str] = None  # Sub work order STATUS
    subord_wo_qty: Decimal = Decimal('0')  # Sub work order DESIRED_QTY
    subord_wo_start_date: Optional[date] = None  # Sub work order SCHED_START_DATE
    subord_wo_finish_date: Optional[date] = None  # Sub work order SCHED_FINISH_DATE

    # Notes from REQUIREMENT_BINARY table
    notes: Optional[str] = None  # NOTES field from REQUIREMENT_BINARY.bits

    def formatted_part(self) -> str:
        """Format part for display: M28803 - TOP BEARING COVER.

        Returns:
            Part ID + description
        """
        return f"{self.part_id} - {self.part_description or 'Unknown'}"

    def formatted_qty(self) -> str:
        """Format quantity with optional notes: 1.0000 - NOTES.

        For sub-work-orders, use DESIRED_QTY from the work order.
        For regular requirements, use QTY_PER from the requirement.
        If notes exist from REQUIREMENT_BINARY, append them after the quantity.

        Returns:
            Formatted quantity with optional notes
        """
        if self.has_child_work_order():
            # For sub-work-orders, use the work order's DESIRED_QTY
            qty_str = f"{self.subord_wo_qty:.4f}"
        else:
            # For regular parts, use the requirement's QTY_PER
            qty_str = f"{self.qty_per:.4f}"

        # Append notes if they exist
        if self.notes:
            return f"{qty_str} - {self.notes}"
        else:
            return qty_str

    def formatted_scrap(self) -> str:
        """Format scrap percentage: 5.00%.

        Returns:
            Scrap percentage formatted
        """
        return f"{self.scrap_percent:.2f}%"

    def formatted_display(self) -> str:
        """Full display: M28803 - TOP BEARING COVER - Qty: 1.0000.
        Or for sub-work-orders: [C] 8113-314/26 - M28803 - TOP BEARING COVER
        Or for sub-work-orders without part: [C] 8113-346/26

        Returns:
            Complete requirement display string
        """
        if self.has_child_work_order():
            # Format: [STATUS] BASE_ID-SUB_ID/LOT_ID [- PART_ID - DESCRIPTION if PART_ID exists]
            status_prefix = f"[{self.subord_wo_status[0].upper()}]" if self.subord_wo_status else "[?]"
            wo_id = f"{self.workorder_base_id}-{self.subord_wo_sub_id}/{self.workorder_lot_id}"

            # Only show part info if PART_ID exists
            if self.part_id and self.part_id.strip():
                return f"{status_prefix} {wo_id} - {self.formatted_part()}"
            else:
                return f"{status_prefix} {wo_id}"
        else:
            # Regular part requirement
            return f"{self.formatted_part()} - {self.formatted_qty()}"

    def has_child_work_order(self) -> bool:
        """Check if this requirement is fulfilled by a child work order.

        Returns:
            True if SUBORD_WO_SUB_ID is populated
        """
        return bool(self.subord_wo_sub_id)

    def formatted_dates(self) -> str:
        """Format sub-work-order dates for display in column 2.

        Format: (SCHED_START_DATE) - (SCHED_FINISH_DATE)
        Example: (10/31/2011) - (10/16/2011)
        If no data: 0 - 0

        Returns:
            Formatted date range string for sub-work-order
        """
        start_str = self.subord_wo_start_date.strftime('(%m/%d/%Y)') if self.subord_wo_start_date else '0'
        finish_str = self.subord_wo_finish_date.strftime('(%m/%d/%Y)') if self.subord_wo_finish_date else '0'

        return f"{start_str} - {finish_str}"


@dataclass
class LaborTicket:
    """Labor transaction from LABOR_TICKET table.

    Represents labor hours charged to work order operations.
    Foreign key: (workorder_base_id, workorder_lot_id, workorder_sub_id)
    """

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str
    operation_seq: Optional[int] = None  # Which operation (may be NULL for non-operation labor)

    # Employee information
    employee_id: str = ''  # EMPLOYEE_ID (varchar 30)
    employee_name: Optional[str] = None  # From EMPLOYEE table join (if available)

    # Time tracking
    labor_date: Optional[date] = None  # LABOR_DATE
    setup_hrs: Decimal = Decimal('0')  # SETUP_HRS
    run_hrs: Decimal = Decimal('0')  # RUN_HRS
    total_hrs: Decimal = Decimal('0')  # Calculated: setup_hrs + run_hrs

    # Cost
    labor_rate: Decimal = Decimal('0')  # LABOR_RATE ($/hr)
    total_cost: Decimal = Decimal('0')  # Calculated: total_hrs * labor_rate

    def formatted_employee(self) -> str:
        """Format employee: Employee 950.

        Returns:
            Employee name or ID
        """
        if self.employee_name:
            return f"{self.employee_name} ({self.employee_id})"
        return f"Employee {self.employee_id}"

    def formatted_date(self) -> str:
        """Format date: 8/15/2011.

        Returns:
            Date in MM/DD/YYYY format
        """
        if self.labor_date:
            return self.labor_date.strftime("%m/%d/%Y")
        return "No Date"

    def formatted_hours(self) -> str:
        """Format hours: 0.50 Hrs.

        Returns:
            Total hours formatted
        """
        return f"{self.total_hrs:.2f} Hrs"

    def formatted_display(self) -> str:
        """Full display: [LABOR] Employee 950 - 8/15/2011 - 0.50 Hrs.

        Returns:
            Complete labor ticket display string
        """
        return f"[LABOR] {self.formatted_employee()} - {self.formatted_date()} - {self.formatted_hours()}"


@dataclass
class InventoryTransaction:
    """Material transaction from INVENTORY_TRANS table.

    Represents material issues, returns, or scrap transactions for work orders.
    Foreign key: (workorder_base_id, workorder_lot_id, workorder_sub_id)
    """

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Part and transaction
    part_id: str  # PART_ID (varchar 30)
    part_description: Optional[str] = None  # From PART table join
    trans_type: str = ''  # TRANS_TYPE (varchar 10) - Issue, Return, Scrap
    quantity: Decimal = Decimal('0')  # QUANTITY

    # Location and timing
    trans_date: Optional[datetime] = None  # TRANS_DATE
    location_id: Optional[str] = None  # LOCATION_ID (varchar 30) - warehouse location

    # Additional tracking
    lot_serial_no: Optional[str] = None  # LOT_SERIAL_NO - lot/serial tracking

    def formatted_type(self) -> str:
        """Format transaction type: Issue, Return, Scrap.

        Returns:
            Transaction type
        """
        return self.trans_type

    def formatted_date(self) -> str:
        """Format date: 8/15/2011.

        Returns:
            Date in MM/DD/YYYY format
        """
        if self.trans_date:
            return self.trans_date.strftime("%m/%d/%Y")
        return "No Date"

    def formatted_qty(self) -> str:
        """Format quantity: 1.0000.

        Returns:
            Formatted quantity
        """
        return f"{self.quantity:.4f}"

    def formatted_display(self) -> str:
        """Full display: [MATERIAL] M28803 - Issue - 1.0000 - 8/15/2011.

        Returns:
            Complete material transaction display string
        """
        return f"[MATERIAL] {self.part_id} - {self.trans_type} - {self.formatted_qty()} - {self.formatted_date()}"


@dataclass
class WIPBalance:
    """WIP cost accumulation from WIP_BALANCE table.

    Represents accumulated costs for a work order.
    Primary key: (workorder_base_id, workorder_lot_id, workorder_sub_id)
    """

    # Foreign key to work order
    workorder_base_id: str
    workorder_lot_id: str
    workorder_sub_id: str

    # Cost breakdown
    material_cost: Decimal = Decimal('0')  # MATERIAL_COST
    labor_cost: Decimal = Decimal('0')  # LABOR_COST
    burden_cost: Decimal = Decimal('0')  # BURDEN_COST (overhead)
    total_cost: Decimal = Decimal('0')  # TOTAL_COST (sum of above)

    # Additional tracking
    last_updated: Optional[datetime] = None  # When costs were last calculated

    def formatted_material(self) -> str:
        """Format material cost: Material Cost: $1,250.00.

        Returns:
            Formatted material cost
        """
        return f"Material Cost: ${self.material_cost:,.2f}"

    def formatted_labor(self) -> str:
        """Format labor cost: Labor Cost: $450.00.

        Returns:
            Formatted labor cost
        """
        return f"Labor Cost: ${self.labor_cost:,.2f}"

    def formatted_burden(self) -> str:
        """Format burden cost: Burden Cost: $200.00.

        Returns:
            Formatted burden cost
        """
        return f"Burden Cost: ${self.burden_cost:,.2f}"

    def formatted_total(self) -> str:
        """Format total cost: Total Cost: $1,900.00.

        Returns:
            Formatted total cost
        """
        return f"Total Cost: ${self.total_cost:,.2f}"

    def formatted_display(self) -> str:
        """Full display: [WIP] Material: $1,250.00, Labor: $450.00, Burden: $200.00, Total: $1,900.00.

        Returns:
            Complete WIP balance display string
        """
        return f"[WIP] {self.formatted_material()}, {self.formatted_labor()}, {self.formatted_burden()}, {self.formatted_total()}"
