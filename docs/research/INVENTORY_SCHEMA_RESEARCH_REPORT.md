# Visual Database Schema Research: Inventory - Part Maintenance Module

**Date**: 2025-11-07
**Purpose**: Research Visual database schema to support Inventory module for part lookups
**Status**: RESEARCH COMPLETE - NO CHANGES MADE

---

## Executive Summary

This research identifies all necessary tables, columns, and relationships in the Visual database to implement an Inventory - Part Maintenance module. The module will support:
1. Part master data lookup by part number
2. Where-used queries (all jobs/orders using a specific part)
3. Purchase history (vendors and POs for a part)

All tables and relationships have been validated against the live Visual database.

---

## 1. Part Master Table

### Table: `PART`

The `PART` table is the primary part master table in Visual.

#### Key Columns for Part Lookup:

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `ID` | varchar(30) | **Part Number** (Primary Key) - exact match search |
| `DESCRIPTION` | varchar(40) | Part description (short) |
| `STOCK_UM` | varchar(15) | **Unit of Measure** (EA, IN, FT, etc.) |
| `UNIT_MATERIAL_COST` | decimal | Material cost per unit |
| `UNIT_LABOR_COST` | decimal | Labor cost per unit |
| `UNIT_BURDEN_COST` | decimal | Burden/overhead cost per unit |
| `UNIT_PRICE` | decimal | Selling price per unit |
| `MATERIAL_CODE` | varchar(25) | **Material specification** code |
| `QTY_ON_HAND` | decimal | Current inventory quantity on hand |
| `QTY_AVAILABLE_ISS` | decimal | Quantity available for issue |
| `QTY_AVAILABLE_MRP` | decimal | Quantity available for MRP |
| `QTY_ON_ORDER` | decimal | Quantity on purchase orders |
| `QTY_IN_DEMAND` | decimal | Quantity allocated to orders |
| `DRAWING_ID` | varchar(30) | Drawing/blueprint reference |
| `DRAWING_REV_NO` | varchar(8) | Drawing revision number |
| `PREF_VENDOR_ID` | varchar(15) | Preferred vendor ID (FK to VENDOR.ID) |
| `PURCHASED` | char(1) | Flag: Y/N if part is purchased |
| `FABRICATED` | char(1) | Flag: Y/N if part is fabricated |
| `STOCKED` | char(1) | Flag: Y/N if part is stocked |
| `WEIGHT` | decimal | Part weight |
| `WEIGHT_UM` | varchar(15) | Weight unit of measure |

#### Sample Query - Part Lookup by Part Number:

```sql
SELECT
    p.ID AS part_number,
    p.DESCRIPTION,
    p.STOCK_UM AS unit_of_measure,
    p.UNIT_MATERIAL_COST AS material_cost,
    p.UNIT_LABOR_COST AS labor_cost,
    p.UNIT_BURDEN_COST AS burden_cost,
    p.UNIT_PRICE AS unit_price,
    p.MATERIAL_CODE AS material_spec,
    p.QTY_ON_HAND,
    p.QTY_AVAILABLE_ISS AS qty_available,
    p.QTY_ON_ORDER,
    p.QTY_IN_DEMAND,
    p.DRAWING_ID,
    p.DRAWING_REV_NO,
    p.PREF_VENDOR_ID,
    v.NAME AS vendor_name,
    p.PURCHASED,
    p.FABRICATED,
    p.STOCKED,
    p.WEIGHT,
    p.WEIGHT_UM
FROM PART p WITH (NOLOCK)
LEFT JOIN VENDOR v WITH (NOLOCK) ON p.PREF_VENDOR_ID = v.ID
WHERE p.ID = ?
```

**Example Result** (Part: PF004):
- Part Number: `PF004`
- Description: `1/4 - 20 x 3/4" BOLT GRADE - USE AF004`
- Unit of Measure: `EA`
- Material Cost: `$0.028500`
- Drawing ID: `SAE - J429`
- Purchased: `Y`, Fabricated: `N`, Stocked: `N`

---

### Related Table: `PART_BINARY`

Stores extended descriptions and binary data for parts.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `PART_ID` | varchar(30) | Part number (FK to PART.ID) |
| `TYPE` | char(1) | Type: 'D' = Description, 'B' = Binary |
| `BITS` | image | Binary data (text for TYPE='D') |
| `BITS_LENGTH` | int | Length of binary data |

#### Query for Extended Description:

```sql
SELECT BITS
FROM PART_BINARY WITH (NOLOCK)
WHERE PART_ID = ?
    AND RTRIM(TYPE) = 'D'
```

**Note**: Decode binary data as UTF-8 text for display.

---

## 2. Where-Used Query

### Table: `INVENTORY_TRANS`

The `INVENTORY_TRANS` table tracks all inventory transactions and links parts to customer orders and work orders.

#### Key Columns for Where-Used:

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `TRANSACTION_ID` | int | Unique transaction ID |
| `WORKORDER_BASE_ID` | varchar | Work order base ID |
| `WORKORDER_LOT_ID` | varchar | Work order lot ID |
| `CUST_ORDER_ID` | varchar | Customer order ID (FK to CUSTOMER_ORDER.ID) |
| `CUST_ORDER_LINE_NO` | smallint | Customer order line number |
| `PURC_ORDER_ID` | varchar | Purchase order ID |
| `PURC_ORDER_LINE_NO` | smallint | Purchase order line number |
| `PART_ID` | varchar(30) | Part number (FK to PART.ID) |
| `TYPE` | char(1) | Transaction type: 'I' = Issue, 'R' = Receipt, etc. |
| `CLASS` | char(1) | Transaction class |
| `QTY` | decimal | Transaction quantity |
| `TRANSACTION_DATE` | datetime | Date/time of transaction |
| `WAREHOUSE_ID` | varchar | Warehouse location |
| `DESCRIPTION` | varchar | Transaction description |
| `USER_ID` | varchar | User who created transaction |

#### Sample Query - Where-Used (All Orders Using a Part):

```sql
SELECT
    it.CUST_ORDER_ID AS order_id,
    it.CUST_ORDER_LINE_NO AS line_no,
    it.WORKORDER_BASE_ID + '/' + it.WORKORDER_LOT_ID AS work_order,
    it.TRANSACTION_DATE,
    it.QTY AS quantity,
    it.TYPE AS transaction_type,
    co.ORDER_DATE,
    c.ID AS customer_id,
    c.NAME AS customer_name
FROM INVENTORY_TRANS it WITH (NOLOCK)
LEFT JOIN CUSTOMER_ORDER co WITH (NOLOCK) ON it.CUST_ORDER_ID = co.ID
LEFT JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE it.PART_ID = ?
    AND it.TYPE = 'I'  -- Issue transactions (parts consumed)
ORDER BY it.TRANSACTION_DATE DESC
```

**Example Result** (Part: PF004):
- Order: N/A, Work Order: `7780/03`, Qty: 51272.0000
- Order: N/A, Work Order: `7780/01`, Qty: 24088.0000
- Order: N/A, Work Order: `7780/02`, Qty: 18378.0000

**Note**: Some transactions may have work orders without customer order IDs (internal work orders).

---

### Related Tables:

#### `WORK_ORDER`
Links work orders to parts and customer orders.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `BASE_ID` | varchar | Work order base ID |
| `LOT_ID` | varchar | Work order lot ID |
| `PART_ID` | varchar | Part being manufactured |
| `DRAWING_ID` | varchar | Drawing/blueprint reference |

#### `CUST_ORDER_LINE`
Customer order line items.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `CUST_ORDER_ID` | varchar | Customer order ID |
| `LINE_NO` | smallint | Line number |
| `PART_ID` | varchar | Part ordered |
| `CUSTOMER_PART_ID` | varchar | Customer's part number |

---

## 3. Purchase History

### Table: `PURC_ORDER_LINE`

Purchase order line items linking parts to vendors and POs.

#### Key Columns:

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `PURC_ORDER_ID` | varchar(15) | Purchase order ID (FK to PURCHASE_ORDER.ID) |
| `LINE_NO` | smallint | Line number |
| `PART_ID` | varchar(30) | Part number (FK to PART.ID) |
| `VENDOR_PART_ID` | varchar(30) | Vendor's part number |
| `USER_ORDER_QTY` | decimal | Quantity ordered (user units) |
| `ORDER_QTY` | decimal | Quantity ordered (stock units) |
| `PURCHASE_UM` | varchar(15) | Purchase unit of measure |
| `UNIT_PRICE` | decimal | Unit price |
| `TOTAL_AMT_ORDERED` | decimal | Total line amount |
| `DESIRED_RECV_DATE` | datetime | Desired receipt date |
| `LAST_RECEIVED_DATE` | datetime | Last receipt date |
| `TOTAL_RECEIVED_QTY` | decimal | Total quantity received |
| `LINE_STATUS` | char(1) | Line status |

#### Sample Query - Purchase History:

```sql
SELECT
    po.ID AS po_number,
    po.ORDER_DATE AS purchase_date,
    po.STATUS AS po_status,
    v.ID AS vendor_id,
    v.NAME AS vendor_name,
    v.CITY AS vendor_city,
    v.STATE AS vendor_state,
    pol.LINE_NO AS line_no,
    pol.USER_ORDER_QTY AS quantity,
    pol.PURCHASE_UM AS unit_of_measure,
    pol.UNIT_PRICE,
    pol.TOTAL_AMT_ORDERED AS line_total,
    pol.DESIRED_RECV_DATE,
    pol.LAST_RECEIVED_DATE,
    pol.TOTAL_RECEIVED_QTY,
    pol.LINE_STATUS
FROM PURC_ORDER_LINE pol WITH (NOLOCK)
INNER JOIN PURCHASE_ORDER po WITH (NOLOCK) ON pol.PURC_ORDER_ID = po.ID
INNER JOIN VENDOR v WITH (NOLOCK) ON po.VENDOR_ID = v.ID
WHERE pol.PART_ID = ?
ORDER BY po.ORDER_DATE DESC
```

**Example Result** (Part: PF004):
- PO: `P10-1168` Line 3, Date: 2010-04-23
- Vendor: `S.W. ANDERSON COMPANY`
- Qty: 51272.0000, Unit Price: $0.028500, Total: $1461.25

---

### Related Tables:

#### `PURCHASE_ORDER`
Purchase order header information.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `ID` | varchar | Purchase order number (Primary Key) |
| `VENDOR_ID` | varchar | Vendor ID (FK to VENDOR.ID) |
| `ORDER_DATE` | datetime | PO date |
| `DESIRED_RECV_DATE` | datetime | Desired receipt date |
| `BUYER` | varchar | Buyer name |
| `STATUS` | char(1) | PO status |

#### `VENDOR`
Vendor master data.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `ID` | varchar(15) | Vendor ID (Primary Key) |
| `NAME` | varchar(50) | Vendor name |
| `ADDR_1` | varchar(50) | Address line 1 |
| `CITY` | varchar(30) | City |
| `STATE` | varchar(10) | State/province |
| `ZIPCODE` | varchar(10) | Zip/postal code |
| `COUNTRY` | varchar(50) | Country |
| `CONTACT_PHONE` | varchar(20) | Phone number |

#### `VENDOR_PART`
Links parts to vendors with vendor-specific part numbers.

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| `PART_ID` | varchar(30) | Part number (FK to PART.ID) |
| `VENDOR_ID` | varchar(15) | Vendor ID (FK to VENDOR.ID) |
| `VENDOR_PART_ID` | varchar(30) | Vendor's part number |
| `LONG_DESCRIPTION` | image | Extended description from vendor |
| `LEADTIME_BUFFER` | smallint | Lead time buffer days |

---

## 4. Additional Useful Tables

### `PART_ALIAS`
Alternative part numbers/aliases.

| Column Name | Description |
|------------|-------------|
| `PART_ID` | Primary part number |
| `ALIAS_TYPE` | Alias type |
| `ALIAS_ID` | Alternative part number |

### `PART_LOCATION`
Part inventory by warehouse location.

| Column Name | Description |
|------------|-------------|
| `PART_ID` | Part number |
| `WAREHOUSE_ID` | Warehouse ID |
| `LOCATION_ID` | Location within warehouse |
| `QTY_ON_HAND` | Quantity at this location |

### `PART_WAREHOUSE`
Part settings by warehouse.

| Column Name | Description |
|------------|-------------|
| `PART_ID` | Part number |
| `WAREHOUSE_ID` | Warehouse ID |
| `QTY_ON_HAND` | Quantity on hand |
| `PRIMARY_LOC_ID` | Primary location in warehouse |

---

## 5. Sample Part Data

The following parts have been validated in the database and can be used for testing:

### High-Volume Purchased Parts (with extensive PO history):
- **F0195**: SLW 1/2 (995 POs, Vendor: KARRIC)
- **R5000**: ROLL TOOLING SLUGS (885 POs, Vendor: UNA)
- **F0209**: SLW 3/8 (846 POs, Vendor: KARRIC)

### Parts with Order History:
- **PP001**: ISYS MODULE CLIP - USE AP001 (used in 3 orders)
- **M0363**: BRAKE DRUM 12" DIA (used in 2 orders)
- **PF004**: 1/4 - 20 x 3/4" BOLT GRADE (multiple orders and POs)

---

## 6. Data Model Notes

### Part-to-Order Relationships:

```
PART (part master)
  |
  ├─→ CUST_ORDER_LINE (parts ordered by customers)
  |     └─→ CUSTOMER_ORDER (order header)
  |           └─→ CUSTOMER (customer info)
  |
  ├─→ INVENTORY_TRANS (inventory transactions linking parts to orders/WOs)
  |     ├─→ WORK_ORDER (work orders consuming parts)
  |     ├─→ CUSTOMER_ORDER (orders consuming parts)
  |     └─→ PURCHASE_ORDER (POs receiving parts)
  |
  └─→ PURC_ORDER_LINE (parts on purchase orders)
        └─→ PURCHASE_ORDER (PO header)
              └─→ VENDOR (vendor info)
```

### Key Relationships:
- **PART.ID** → **CUST_ORDER_LINE.PART_ID** (parts ordered)
- **PART.ID** → **INVENTORY_TRANS.PART_ID** (parts consumed/received)
- **PART.ID** → **PURC_ORDER_LINE.PART_ID** (parts purchased)
- **PART.ID** → **WORK_ORDER.PART_ID** (parts manufactured)
- **PART.PREF_VENDOR_ID** → **VENDOR.ID** (preferred vendor)

### Transaction Types in INVENTORY_TRANS:
- **'I'** = Issue (parts consumed from inventory)
- **'R'** = Receipt (parts received into inventory)
- Other types exist for adjustments, transfers, etc.

---

## 7. Implementation Recommendations

### Query Performance:
1. All queries use `WITH (NOLOCK)` hint for read-only access
2. Index on `PART.ID` (primary key)
3. Index on `INVENTORY_TRANS.PART_ID` for where-used queries
4. Index on `PURC_ORDER_LINE.PART_ID` for purchase history

### User Interface Fields:

#### Part Master Screen:
- Part Number (PART.ID)
- Description (PART.DESCRIPTION + PART_BINARY.BITS if TYPE='D')
- Unit of Measure (PART.STOCK_UM)
- Material Spec (PART.MATERIAL_CODE)
- Costs: Material, Labor, Burden (PART.UNIT_*_COST)
- Unit Price (PART.UNIT_PRICE)
- Quantities: On Hand, Available, On Order, In Demand
- Drawing ID and Rev (PART.DRAWING_ID, PART.DRAWING_REV_NO)
- Preferred Vendor (VENDOR.NAME via PART.PREF_VENDOR_ID)
- Flags: Purchased, Fabricated, Stocked

#### Where-Used Tab:
- Order/Job Number (INVENTORY_TRANS.CUST_ORDER_ID)
- Work Order (BASE_ID/LOT_ID)
- Customer Name (CUSTOMER.NAME)
- Transaction Date (INVENTORY_TRANS.TRANSACTION_DATE)
- Quantity Used (INVENTORY_TRANS.QTY)

#### Purchase History Tab:
- PO Number (PURCHASE_ORDER.ID)
- Vendor Name (VENDOR.NAME)
- PO Date (PURCHASE_ORDER.ORDER_DATE)
- Quantity (PURC_ORDER_LINE.USER_ORDER_QTY)
- Unit Price (PURC_ORDER_LINE.UNIT_PRICE)
- Total Amount (PURC_ORDER_LINE.TOTAL_AMT_ORDERED)
- Status (PURC_ORDER_LINE.LINE_STATUS)

---

## 8. Open Questions / Notes

1. **Part "PO649" mentioned in transcript**: Not found in current database. May be:
   - A historical part that's been archived
   - An example part for demonstration
   - A part from a different database/environment

2. **Transaction Types**: The `INVENTORY_TRANS.TYPE` field has multiple values beyond 'I' and 'R'. Need to determine which types are relevant for "where-used" reporting.

3. **Work Orders without Customer Orders**: Some inventory transactions have work orders but no customer order ID. These may be:
   - Internal work orders
   - Stock replenishment
   - R&D/prototype work

4. **Extended Descriptions**: The `PART_BINARY` table stores extended descriptions as binary (image) data type. Decode as UTF-8 text with error handling.

---

## 9. Test Part for Development

**Recommended Test Part**: `F0195`
- Part Number: F0195
- Description: SLW 1/2
- Has 995 purchase orders (extensive purchase history)
- Preferred Vendor: KARRIC
- Good for testing all three queries (part lookup, where-used, purchase history)

---

## Appendix: Research Scripts

The following Python scripts were created during this research and can be used for further investigation:

1. **research_part_schema.py** - Main schema research script
2. **research_part_schema_detailed.py** - Detailed PO/vendor research
3. **research_sample_parts.py** - Find sample parts for testing

All scripts are located in the project root directory.

---

**Research completed**: 2025-11-07
**No database changes made**: This was read-only research only.
