# Quick Start Guide: Inventory Module Where-Used Enhancement

**Feature**: 002-inventory-where-used-enhancement
**Date**: 2025-11-12
**Status**: Phase 1 Design
**For**: Developers implementing the BOM where-used feature

## Overview

This guide helps developers get started implementing the Inventory module's Where-Used tab enhancement. The feature replaces inventory transaction history with BOM (Bill of Materials) structure information from the REQUIREMENT and WORK_ORDER tables.

## Prerequisites

### System Requirements

- **OS**: Windows 10 or Windows 11
- **Python**: 3.11+ (verify with `python --version`)
- **Network**: WLAN access to Visual SQL Server database
- **IDE**: VS Code, PyCharm, or preferred Python IDE

### Required Knowledge

- Python 3.11+ (dataclasses, decimal, typing)
- PyQt6 (QTableWidget, signals/slots)
- SQL (SELECT, JOIN, ORDER BY)
- pyodbc (cursor operations, parameterized queries)

## Environment Setup

### 1. Install Dependencies

```bash
# From project root
cd C:\Users\dto\Desktop\Speckit\visual-legacy\visual-db-order-lookup

# Activate virtual environment (if using)
venv\Scripts\activate

# Install/verify dependencies
pip install -r requirements.txt

# Verify installations
python -c "import PyQt6; import pyodbc; print('Dependencies OK')"
```

### 2. Database Configuration

Create/verify `.env` file in project root:

```env
# Visual Database Connection
MSSQL_CONNECTION_STRING=DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=Visual;UID=readonly_user;PWD=your-password;

# Application Settings
APP_NAME=Visual Order Lookup
LOG_LEVEL=INFO
```

**Important**: Use read-only credentials (Constitutional requirement).

### 3. Test Database Connection

```bash
# Run connection test
python test_connection.py

# Expected output:
# Connected to Visual database successfully
# Server version: Microsoft SQL Server ...
```

## Project Structure

### Files to Modify

```text
visual_order_lookup/
├── database/
│   ├── models.py               ← UPDATE WhereUsed model
│   └── part_queries.py         ← ADD get_part_bom_usage() query
├── services/
│   └── part_service.py         ← UPDATE get_bom_where_used() method
├── ui/
│   └── part_detail_view.py     ← UPDATE Where Used tab display
└── tests/
    ├── database/
    │   └── test_part_queries.py ← NEW BOM query tests
    └── ui/
        └── test_part_detail_view.py ← UPDATE display tests
```

### Documentation Reference

```text
specs/002-inventory-where-used-enhancement/
├── spec.md              # Feature requirements
├── plan.md              # Implementation plan
├── research.md          # Database schema findings
├── data-model.md        # WhereUsed model definition
├── contracts/
│   └── bom_query.sql    # SQL query specification
└── quickstart.md        # This file
```

## Development Workflow

### Step 1: Update WhereUsed Model

**File**: `visual_order_lookup/database/models.py`

**Task**: Replace old WhereUsed model with new BOM structure model

**Reference**: See `data-model.md` for complete model definition

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class WhereUsed:
    """BOM usage record for a part."""
    part_number: str
    work_order_master: str
    seq_no: int
    piece_no: int
    qty_per: Decimal
    fixed_qty: Decimal
    scrap_percent: Decimal

    def formatted_work_order(self) -> str:
        return self.work_order_master

    def formatted_seq_no(self) -> str:
        return str(self.seq_no)

    def formatted_piece_no(self) -> str:
        return str(self.piece_no)

    def formatted_qty_per(self) -> str:
        return f"{self.qty_per:.4f}"

    def formatted_fixed_qty(self) -> str:
        return f"{self.fixed_qty:.4f}"

    def formatted_scrap_percent(self) -> str:
        return f"{self.scrap_percent:.2f}%"
```

**Test**: Run `pytest visual_order_lookup/tests/database/test_models.py -v`

### Step 2: Create BOM Query

**File**: `visual_order_lookup/database/part_queries.py`

**Task**: Add `get_part_bom_usage()` function

**Reference**: See `contracts/bom_query.sql` for complete query specification

```python
import logging
from typing import List
from decimal import Decimal
import pyodbc
from visual_order_lookup.database.models import WhereUsed

logger = logging.getLogger(__name__)

def get_part_bom_usage(cursor: pyodbc.Cursor, part_number: str) -> List[WhereUsed]:
    """Retrieve BOM structure records for a part.

    Args:
        cursor: Database cursor
        part_number: Part ID to search for

    Returns:
        List of WhereUsed objects (BOM records)

    Raises:
        ValueError: If part_number is empty
        Exception: If database query fails
    """
    if not part_number or not part_number.strip():
        raise ValueError("Part number cannot be empty")

    query = """
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
    """

    try:
        cursor.execute(query, (part_number.strip(),))
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append(WhereUsed(
                part_number=part_number,
                work_order_master=row.work_order_master.strip() if row.work_order_master else "",
                seq_no=row.seq_no if row.seq_no is not None else 0,
                piece_no=row.piece_no if row.piece_no is not None else 0,
                qty_per=Decimal(str(row.qty_per)) if row.qty_per is not None else Decimal("0"),
                fixed_qty=Decimal(str(row.fixed_qty)) if row.fixed_qty is not None else Decimal("0"),
                scrap_percent=Decimal(str(row.scrap_percent)) if row.scrap_percent is not None else Decimal("0"),
            ))

        logger.info(f"Retrieved {len(records)} BOM records for part {part_number}")
        return records

    except pyodbc.Error as e:
        logger.error(f"Database error retrieving BOM for part {part_number}: {e}")
        raise Exception(f"Failed to retrieve BOM data: {str(e)}")
```

**Test**: Run `pytest visual_order_lookup/tests/database/test_part_queries.py::test_get_part_bom_usage -v`

### Step 3: Update PartService

**File**: `visual_order_lookup/services/part_service.py`

**Task**: Update `get_bom_where_used()` method to use new query

```python
def get_bom_where_used(self, part_number: str) -> List[WhereUsed]:
    """Get BOM where-used records for a part.

    Args:
        part_number: Part number to search for

    Returns:
        List of WhereUsed objects (BOM records)

    Raises:
        Exception: If database operation fails
    """
    try:
        cursor = self.connection.get_cursor()
        records = part_queries.get_part_bom_usage(cursor, part_number)
        cursor.close()
        return records

    except Exception as e:
        logger.error(f"Error retrieving BOM where-used for {part_number}: {e}")
        raise
```

**Test**: Run `pytest visual_order_lookup/tests/services/test_part_service.py -v`

### Step 4: Update Where Used Tab Display

**File**: `visual_order_lookup/ui/part_detail_view.py`

**Task**: Update table columns and formatting in `_setup_ui()` and `_refresh_where_used_page()`

#### Update Table Headers

```python
# In _setup_ui() method, around line 82
self.where_used_table.setColumnCount(6)
self.where_used_table.setHorizontalHeaderLabels([
    "Work Order/Master", "Seq #", "Piece #", "Quantity Per", "Fixed Qty", "Scrap %"
])
```

#### Update Table Population

```python
# In _refresh_where_used_page() method, replace rows 328-355 with:
for row, record in enumerate(page_records):
    try:
        # Work Order/Master
        wo_item = QTableWidgetItem(record.formatted_work_order())
        self.where_used_table.setItem(row, 0, wo_item)

        # Seq #
        seq_item = QTableWidgetItem(record.formatted_seq_no())
        seq_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.where_used_table.setItem(row, 1, seq_item)

        # Piece #
        piece_item = QTableWidgetItem(record.formatted_piece_no())
        piece_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.where_used_table.setItem(row, 2, piece_item)

        # Quantity Per
        qty_per_item = QTableWidgetItem(record.formatted_qty_per())
        qty_per_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.where_used_table.setItem(row, 3, qty_per_item)

        # Fixed Qty
        fixed_qty_item = QTableWidgetItem(record.formatted_fixed_qty())
        fixed_qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.where_used_table.setItem(row, 4, fixed_qty_item)

        # Scrap %
        scrap_item = QTableWidgetItem(record.formatted_scrap_percent())
        scrap_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.where_used_table.setItem(row, 5, scrap_item)

    except Exception as e:
        logging.error(f"Error adding row {row}: {e}")
        continue
```

#### Update CSV Export

```python
# In _export_where_used() method, around line 568, update header:
writer.writerow([
    "Work Order/Master", "Seq #", "Piece #", "Quantity Per", "Fixed Qty", "Scrap %"
])

# Update data rows, around line 573:
for record in self.where_used_records:
    writer.writerow([
        record.formatted_work_order(),
        record.formatted_seq_no(),
        record.formatted_piece_no(),
        record.formatted_qty_per(),
        record.formatted_fixed_qty(),
        record.formatted_scrap_percent()
    ])
```

**Test**: Run `pytest visual_order_lookup/tests/ui/test_part_detail_view.py -v`

## Testing

### Run All Tests

```bash
# From project root
pytest visual_order_lookup/tests/ -v

# Expected output:
# test_where_used_model.py::test_formatting ✓
# test_part_queries.py::test_get_part_bom_usage ✓
# test_part_service.py::test_get_bom_where_used ✓
# test_part_detail_view.py::test_where_used_display ✓
```

### Test with Real Data

```bash
# Run application
python visual_order_lookup/main.py

# Manual test steps:
# 1. Click "Inventory" module
# 2. Search for part "F0195"
# 3. Click "Where Used" tab
# 4. Verify 6 columns displayed
# 5. Verify 6,253 total records (pagination shows 126 pages)
# 6. Verify numeric columns right-aligned
# 7. Test "Export All as CSV" button
# 8. Verify CSV contains 6 columns + all records
```

### Test Parts

| Part ID | Record Count | Test Purpose |
|---------|--------------|--------------|
| F0195   | 6,253        | Performance & pagination (126 pages) |
| F0209   | 5,004        | Export testing (large CSV) |
| R0236   | 3,487        | Medium volume (70 pages) |

## Performance Benchmarks

### Expected Performance

| Operation | Target | Expected | Test Part |
|-----------|--------|----------|-----------|
| BOM Query | <5s | 0.4s | F0195 (6,253 records) |
| Pagination Render | <1s | <0.1s | 50 records/page |
| CSV Export | <10s | ~2s | 6,253 records |

### Measuring Performance

```python
import time

start = time.time()
records = get_part_bom_usage(cursor, "F0195")
elapsed = time.time() - start
print(f"Query time: {elapsed:.3f}s for {len(records)} records")
# Expected: Query time: 0.404s for 6253 records
```

## Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'pyodbc'`
- **Solution**: `pip install pyodbc`

**Problem**: `pyodbc.Error: ('08001', '[08001] [Microsoft][ODBC Driver...]')`
- **Solution**: Verify WLAN connection and .env connection string

**Problem**: Query returns 0 records for valid part
- **Solution**: Verify table names (REQUIREMENT not BOM_DET)

**Problem**: `decimal.InvalidOperation` errors
- **Solution**: Ensure Decimal conversion: `Decimal(str(value))`

**Problem**: UI columns not aligned
- **Solution**: Set `Qt.AlignmentFlag.AlignRight` for numeric columns

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View SQL queries:

```python
logger.debug(f"Executing query: {query}")
logger.debug(f"Parameters: {part_number}")
```

## Code Style Guidelines

### Python Conventions

- Follow PEP 8 style guide
- Use type hints: `def func(part: str) -> List[WhereUsed]:`
- Docstrings: Google style format
- Line length: 100 characters max

### PyQt6 Conventions

- Signal naming: `snake_case_signal` (e.g., `search_requested`)
- Slot naming: `_on_action` (e.g., `_on_search_part`)
- Private methods: Prefix with `_` (e.g., `_refresh_where_used_page`)

### Database Conventions

- Always use `WITH (NOLOCK)` hint
- Parameterized queries: `cursor.execute(query, (param,))`
- Strip strings: `row.field.strip() if row.field else ""`

## Next Steps

1. Complete all code changes (Steps 1-4 above)
2. Run full test suite: `pytest visual_order_lookup/tests/ -v`
3. Manual testing with parts F0195, F0209, R0236
4. Performance validation (query <5s, render <1s, export <10s)
5. Code review with team
6. Create pull request referencing feature 002

## Resources

- **Spec**: `specs/002-inventory-where-used-enhancement/spec.md`
- **Research**: `specs/002-inventory-where-used-enhancement/research.md`
- **Data Model**: `specs/002-inventory-where-used-enhancement/data-model.md`
- **Query Contract**: `specs/002-inventory-where-used-enhancement/contracts/bom_query.sql`
- **Constitution**: `.specify/memory/constitution.md`

## Support

- **Database Issues**: Contact DBA for WLAN/Visual database access
- **PyQt6 Questions**: See PyQt6 documentation at https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Feature Questions**: Review spec.md or contact Spare Parts department

---

**Ready to implement**: All Phase 1 design artifacts complete. Proceed with implementation using this guide.
