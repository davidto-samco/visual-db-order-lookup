# Data Model: Inventory Module Where-Used Enhancement

**Feature**: 002-inventory-where-used-enhancement
**Date**: 2025-11-12
**Status**: Phase 1 Design

## Overview

This document defines the data model for displaying BOM (Bill of Materials) structure information in the Inventory module's "Where Used" tab. Based on Phase 0 research, the model uses the REQUIREMENT and WORK_ORDER tables from the Visual database.

**Key Discovery**: The Visual database uses REQUIREMENT (not BOM_DET) and WORK_ORDER (not BOM_MASTER) for BOM structure storage.

## Entities

### WhereUsed (Updated Model)

Represents one BOM usage record showing where a part is used in an assembly/work order.

**Purpose**: Display BOM structure information in the Where Used tab, replacing the previous inventory transaction view.

**Source**: REQUIREMENT table (BOM detail) joined with WORK_ORDER table (BOM master)

#### Fields

| Field Name | Type | Source | Nullable | Description |
|------------|------|--------|----------|-------------|
| `part_number` | str | REQUIREMENT.PART_ID | No | Part number being queried |
| `work_order_master` | str | WORK_ORDER.BASE_ID | No | Work order/assembly ID |
| `seq_no` | int | REQUIREMENT.OPERATION_SEQ_NO | No | Sequence number in BOM structure (default: 0) |
| `piece_no` | int | REQUIREMENT.PIECE_NO | No | Piece number identifier (default: 0) |
| `qty_per` | Decimal | REQUIREMENT.QTY_PER | No | Quantity of part per parent assembly (default: 0.00000000) |
| `fixed_qty` | Decimal | REQUIREMENT.FIXED_QTY | No | Fixed quantity regardless of parent qty (default: 0.0000) |
| `scrap_percent` | Decimal | REQUIREMENT.SCRAP_PERCENT | No | Scrap percentage for manufacturing (default: 0.00) |

#### Properties (Formatted Output)

| Property | Return Type | Logic | Example Output |
|----------|-------------|-------|----------------|
| `formatted_work_order()` | str | Returns `work_order_master` as-is | "7961" or "Q10-0202" |
| `formatted_seq_no()` | str | Returns `seq_no` as integer string | "10" or "0" |
| `formatted_piece_no()` | str | Returns `piece_no` as integer string | "1" or "0" |
| `formatted_qty_per()` | str | Returns `qty_per` with 4 decimal places | "1.2500" or "0.0000" |
| `formatted_fixed_qty()` | str | Returns `fixed_qty` with 4 decimal places | "5.0000" or "0.0000" |
| `formatted_scrap_percent()` | str | Returns `scrap_percent` with 2 decimals + "%" | "5.00%" or "0.00%" |

#### Data Types (Database Schema)

From Phase 0 research (REQUIREMENT table):
- `OPERATION_SEQ_NO`: smallint (2-byte integer, range: -32768 to 32767)
- `PIECE_NO`: smallint (2-byte integer)
- `QTY_PER`: decimal(15, 8) - precision 15, scale 8
- `FIXED_QTY`: decimal(14, 4) - precision 14, scale 4
- `SCRAP_PERCENT`: decimal(5, 2) - precision 5, scale 2

#### NULL Handling

**Research Finding**: All BOM fields have NOT NULL constraints with default values.

**NULL Display Strategy**:
- No NULL values exist in REQUIREMENT table for these columns
- All fields default to 0 if not explicitly set
- Display zeros as formatted values (e.g., "0.00%", "0.0000")
- **No "N/A" display needed**

#### Python Model Definition

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class WhereUsed:
    """BOM usage record for a part.

    Represents where a part is used in work orders/assemblies from the
    REQUIREMENT table. Replaces previous inventory transaction model.
    """

    part_number: str
    work_order_master: str
    seq_no: int
    piece_no: int
    qty_per: Decimal
    fixed_qty: Decimal
    scrap_percent: Decimal

    def formatted_work_order(self) -> str:
        """Format work order/master ID for display.

        Returns:
            Work order ID as-is (BASE_ID from WORK_ORDER table)
        """
        return self.work_order_master

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
```

## Relationships

### WhereUsed → Part
- **Type**: Many-to-One
- **Foreign Key**: `part_number` → PART.ID
- **Constraint**: Part must exist in PART table
- **Navigation**: WhereUsed belongs to one Part

### WhereUsed → WorkOrder
- **Type**: Many-to-One
- **Foreign Key**: `work_order_master` → WORK_ORDER.BASE_ID
- **Constraint**: Work order must exist
- **Navigation**: WhereUsed belongs to one Work Order
- **Note**: Full join requires BASE_ID + LOT_ID + SUB_ID (composite key)

### Part → WhereUsed
- **Type**: One-to-Many
- **Description**: A part can be used in multiple work orders
- **Example**: Part "F0195" has 6,253 BOM records (research finding)
- **Navigation**: Part has many WhereUsed records

## Database Query Mapping

### SQL Query → WhereUsed Model

```sql
SELECT
    wo.BASE_ID AS work_order_master,
    r.OPERATION_SEQ_NO AS seq_no,
    r.PIECE_NO AS piece_no,
    r.QTY_PER AS qty_per,
    r.FIXED_QTY AS fixed_qty,
    r.SCRAP_PERCENT AS scrap_percent
FROM REQUIREMENT r WITH (NOLOCK)
INNER JOIN WORK_ORDER wo WITH (NOLOCK)
    ON r.WORKORDER_BASE_ID = wo.BASE_ID
   AND r.WORKORDER_LOT_ID = wo.LOT_ID
   AND r.WORKORDER_SUB_ID = wo.SUB_ID
WHERE r.PART_ID = ?
ORDER BY wo.BASE_ID, r.OPERATION_SEQ_NO
```

### Python Mapping

```python
def map_row_to_where_used(row, part_number: str) -> WhereUsed:
    """Map database row to WhereUsed model.

    Args:
        row: Database cursor row from BOM query
        part_number: Part number being queried

    Returns:
        WhereUsed object
    """
    return WhereUsed(
        part_number=part_number,
        work_order_master=row.work_order_master.strip() if row.work_order_master else "",
        seq_no=row.seq_no if row.seq_no is not None else 0,
        piece_no=row.piece_no if row.piece_no is not None else 0,
        qty_per=Decimal(str(row.qty_per)) if row.qty_per is not None else Decimal("0.00000000"),
        fixed_qty=Decimal(str(row.fixed_qty)) if row.fixed_qty is not None else Decimal("0.0000"),
        scrap_percent=Decimal(str(row.scrap_percent)) if row.scrap_percent is not None else Decimal("0.00"),
    )
```

## Validation Rules

### Field Constraints

| Field | Constraint | Validation Rule |
|-------|-----------|-----------------|
| `part_number` | Required | Must be non-empty string |
| `work_order_master` | Required | Must be non-empty string from WORK_ORDER.BASE_ID |
| `seq_no` | Integer | Must be smallint range (-32768 to 32767), typically >= 0 |
| `piece_no` | Integer | Must be smallint range, typically >= 0 |
| `qty_per` | Decimal | Must be decimal(15,8), typically >= 0 |
| `fixed_qty` | Decimal | Must be decimal(14,4), typically >= 0 |
| `scrap_percent` | Decimal | Must be decimal(5,2), typically 0-100 range |

### Business Rules

1. **Sequence Ordering**: Records ordered by `work_order_master` then `seq_no`
2. **Quantity Logic**: Either `qty_per` OR `fixed_qty` is used (not both), but both stored
3. **Scrap Calculation**: Scrap percentage applies during manufacturing, not part of model validation
4. **Zero Values**: Zero values are valid and displayed (not errors)

## State Transitions

**N/A** - This is a read-only data model with no state transitions. Records are retrieved from database and displayed; no create/update/delete operations occur (per Constitution Principle III).

## Edge Cases

### Empty Result Set
- **Scenario**: Part has no BOM usage (not used in any work orders)
- **Handling**: Query returns empty list `[]`
- **UI Display**: "No BOM usage found for this part" message
- **Pagination**: Controls disabled

### Zero Values
- **Scenario**: `seq_no=0`, `piece_no=0`, `qty_per=0`, `fixed_qty=0`, `scrap_percent=0`
- **Handling**: Display as formatted zeros: "0", "0.0000", "0.00%"
- **Validation**: These are valid values, not errors

### Large Dataset
- **Scenario**: Part with 6,253 BOM records (like F0195 from research)
- **Handling**: Pagination displays 50 records per page (126 pages)
- **Performance**: Query completes in <1 second (0.404s measured)

### Work Order Formats
- **Scenario**: BASE_ID values like "7961", "Q10-0202", "4049 R3"
- **Handling**: Display as-is (no parsing or transformation)
- **Note**: Customer order linkage via WBS_CUST_ORDER_ID is unused (column empty)

## Migration from Previous Model

### Old Model (Inventory Transactions)

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
```

### New Model (BOM Structure)

```python
@dataclass
class WhereUsed:
    part_number: str
    work_order_master: str
    seq_no: int
    piece_no: int
    qty_per: Decimal
    fixed_qty: Decimal
    scrap_percent: Decimal
```

### Breaking Changes

| Change | Impact | Migration Strategy |
|--------|--------|-------------------|
| Removed `transaction_date` | High | No migration - completely different data source |
| Removed `customer_name` | Medium | Customer info available via work order if needed |
| Removed `warehouse_id`, `location_id` | Low | Not relevant for BOM structure |
| Added `seq_no`, `piece_no` | High | New BOM-specific fields |
| Added `qty_per`, `fixed_qty`, `scrap_percent` | High | Replace `quantity` field |
| Changed `work_order` → `work_order_master` | Medium | Semantic change (master assembly) |

**Migration Notes**:
- This is a **complete model replacement**, not a gradual migration
- Previous INVENTORY_TRANS query will be **deleted**, not deprecated
- No data migration required (read-only views)
- UI column headers change completely

## Performance Considerations

### Query Performance
- **Index**: PART_ID has non-clustered index (X_REQUIREMENT_1)
- **Measured**: 6,253 records retrieved in 0.404 seconds
- **Requirement**: <5 seconds for 10,000 records ✓ PASS
- **Optimization**: JOIN uses composite key (3 columns) - efficient with indexes

### Memory Footprint
- **Single Record**: ~120 bytes (WhereUsed object)
- **1,000 Records**: ~120 KB
- **10,000 Records**: ~1.2 MB
- **Pagination**: Only 50 records loaded in UI at once (~6 KB)
- **Requirement**: <100MB application memory ✓ PASS

### Display Rendering
- **Pagination Limit**: 50 records per page
- **Measured**: <1 second to render 50 rows
- **Requirement**: <1 second ✓ PASS

## Testing Recommendations

### Unit Tests

```python
def test_where_used_formatting():
    """Test formatted output methods."""
    record = WhereUsed(
        part_number="F0195",
        work_order_master="7961",
        seq_no=10,
        piece_no=1,
        qty_per=Decimal("1.2500"),
        fixed_qty=Decimal("5.0000"),
        scrap_percent=Decimal("5.00")
    )

    assert record.formatted_seq_no() == "10"
    assert record.formatted_piece_no() == "1"
    assert record.formatted_qty_per() == "1.2500"
    assert record.formatted_fixed_qty() == "5.0000"
    assert record.formatted_scrap_percent() == "5.00%"

def test_where_used_zero_values():
    """Test zero value handling."""
    record = WhereUsed(
        part_number="TEST",
        work_order_master="0000",
        seq_no=0,
        piece_no=0,
        qty_per=Decimal("0"),
        fixed_qty=Decimal("0"),
        scrap_percent=Decimal("0")
    )

    assert record.formatted_qty_per() == "0.0000"
    assert record.formatted_scrap_percent() == "0.00%"
```

### Integration Tests

```python
def test_bom_query_returns_where_used_list(db_connection):
    """Test BOM query maps to WhereUsed model."""
    cursor = db_connection.get_cursor()
    results = get_part_bom_usage(cursor, "F0195")

    assert len(results) > 0
    assert all(isinstance(r, WhereUsed) for r in results)
    assert all(r.part_number == "F0195" for r in results)

def test_bom_query_empty_result(db_connection):
    """Test part with no BOM usage."""
    cursor = db_connection.get_cursor()
    results = get_part_bom_usage(cursor, "NONEXISTENT")

    assert results == []
    assert isinstance(results, list)
```

### Test Data

Use these parts from research findings:
- **F0195**: 6,253 records (performance & pagination testing)
- **F0209**: 5,004 records (export testing)
- **R0236**: 3,487 records (medium volume testing)

## Conclusion

The WhereUsed model has been redesigned to represent BOM structure data from the REQUIREMENT and WORK_ORDER tables. All fields are required (no NULL handling needed), and formatting methods provide consistent display output. The model is optimized for read-only queries with pagination support for large datasets.

**Status**: Ready for Phase 1 implementation (database query contract definition).
