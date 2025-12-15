# Database Schema Reference

This document provides a reference for all SQL Server tables accessed by the Visual Order Lookup application, along with the queries needed for the Express migration.

## Database Connection

- **Server**: 10.10.10.142
- **Port**: 1433
- **Database**: SAMCO
- **Access**: Read-only

## Table Overview

| Table | Module | Description |
|-------|--------|-------------|
| CUSTOMER_ORDER | Sales | Order headers |
| CUSTOMER | Sales | Customer master |
| CUST_ORDER_LINE | Sales | Order line items |
| CUST_LINE_BINARY | Sales | Line item extended text |
| CUST_ORDER_BINARY | Sales | Order extended text |
| SALES_REP | Sales | Sales representative info |
| PART | Inventory | Part master data |
| VENDOR | Inventory | Vendor master |
| REQUIREMENT | Inventory/Eng | BOM requirements |
| WORK_ORDER | Eng | Work order headers |
| OPERATION | Eng | Manufacturing operations |
| LABOR_TICKET | Eng | Labor transactions |
| INVENTORY_TRANS | Eng | Material transactions |
| WIP_BALANCE | Eng | Cost accumulation |
| PURC_ORDER_LINE | Inventory | Purchase order lines |
| PURC_ORDER_HDR | Inventory | Purchase order headers |

---

## Sales Module Tables

### CUSTOMER_ORDER

Main order header table.

| Column | Type | Description |
|--------|------|-------------|
| ID | VARCHAR(30) | Primary key (Job Number) |
| CUSTOMER_ID | VARCHAR(30) | FK to CUSTOMER |
| ORDER_DATE | DATE | Order date |
| DESIRED_SHIP_DATE | DATE | Requested ship date |
| CUSTOMER_PO_REF | VARCHAR(50) | Customer PO reference |
| CONTACT_NAME | VARCHAR(50) | Contact person |
| CONTACT_PHONE | VARCHAR(20) | Contact phone |
| CONTACT_EMAIL | VARCHAR(100) | Contact email |
| TOTAL_AMT_ORDERED | DECIMAL(15,2) | Total order amount |
| PAYMENT_TERMS | VARCHAR(20) | Payment terms code |
| SALESREP_ID | VARCHAR(10) | FK to SALES_REP |
| STATUS | VARCHAR(1) | Order status |

### CUSTOMER

Customer master data.

| Column | Type | Description |
|--------|------|-------------|
| ID | VARCHAR(30) | Primary key |
| NAME | VARCHAR(50) | Customer name |
| ADDR_1 | VARCHAR(50) | Ship-to address line 1 |
| ADDR_2 | VARCHAR(50) | Ship-to address line 2 |
| CITY | VARCHAR(30) | Ship-to city |
| STATE | VARCHAR(10) | Ship-to state |
| ZIPCODE | VARCHAR(15) | Ship-to ZIP |
| COUNTRY | VARCHAR(30) | Ship-to country |
| BILL_TO_ADDR_1 | VARCHAR(50) | Bill-to address line 1 |
| BILL_TO_ADDR_2 | VARCHAR(50) | Bill-to address line 2 |
| BILL_TO_CITY | VARCHAR(30) | Bill-to city |
| BILL_TO_STATE | VARCHAR(10) | Bill-to state |
| BILL_TO_ZIPCODE | VARCHAR(15) | Bill-to ZIP |
| BILL_TO_COUNTRY | VARCHAR(30) | Bill-to country |

### CUST_ORDER_LINE

Order line items.

| Column | Type | Description |
|--------|------|-------------|
| CUST_ORDER_ID | VARCHAR(30) | FK to CUSTOMER_ORDER |
| LINE_NO | INT | Line number (PK part) |
| PART_ID | VARCHAR(30) | FK to PART |
| ORDER_QTY | DECIMAL(15,4) | Quantity ordered |
| UNIT_PRICE | DECIMAL(15,4) | Unit price |
| EXTENDED_PRICE | DECIMAL(15,2) | Extended price |
| BASE_ID | VARCHAR(30) | Work order BASE_ID |
| LOT_ID | VARCHAR(2) | Work order LOT_ID |

### CUST_LINE_BINARY

Extended line item descriptions stored as binary data.

| Column | Type | Description |
|--------|------|-------------|
| CUST_ORDER_ID | VARCHAR(30) | FK to CUSTOMER_ORDER |
| CUST_ORDER_LINE_NO | INT | FK to line number |
| BITS | VARBINARY(MAX) | Binary description data |

### CUST_ORDER_BINARY

Extended order descriptions.

| Column | Type | Description |
|--------|------|-------------|
| CUST_ORDER_ID | VARCHAR(30) | FK to CUSTOMER_ORDER |
| BITS | VARBINARY(MAX) | Project description |

---

## Inventory Module Tables

### PART

Part master data.

| Column | Type | Description |
|--------|------|-------------|
| ID | VARCHAR(30) | Primary key |
| DESCRIPTION | VARCHAR(50) | Part description |
| STOCK_UM | VARCHAR(10) | Unit of measure |
| PRODUCT_CODE | VARCHAR(10) | Product classification |
| COMMODITY_CODE | VARCHAR(10) | Commodity code |
| STANDARD_COST | DECIMAL(15,4) | Standard cost |
| AVERAGE_COST | DECIMAL(15,4) | Average cost |
| LAST_COST | DECIMAL(15,4) | Last purchase cost |
| LIST_PRICE | DECIMAL(15,4) | List price |
| QTY_ON_HAND | DECIMAL(15,4) | Current inventory |
| QTY_ON_ORDER | DECIMAL(15,4) | On PO qty |
| QTY_ALLOCATED | DECIMAL(15,4) | Allocated qty |
| VENDOR_ID | VARCHAR(30) | Primary vendor FK |
| MAKE_BUY_CODE | CHAR(1) | M=Make, B=Buy |
| ABC | CHAR(1) | ABC classification |
| PHANTOM_FLAG | CHAR(1) | Y=Phantom BOM |
| STATUS | CHAR(1) | A=Active |

### VENDOR

Vendor master.

| Column | Type | Description |
|--------|------|-------------|
| ID | VARCHAR(30) | Primary key |
| NAME | VARCHAR(50) | Vendor name |

### PURC_ORDER_HDR

Purchase order headers.

| Column | Type | Description |
|--------|------|-------------|
| ID | VARCHAR(30) | PO number (PK) |
| VENDOR_ID | VARCHAR(30) | FK to VENDOR |
| ORDER_DATE | DATE | PO date |
| CURRENCY_ID | VARCHAR(3) | Currency code |

### PURC_ORDER_LINE

Purchase order line items.

| Column | Type | Description |
|--------|------|-------------|
| PURC_ORDER_ID | VARCHAR(30) | FK to PURC_ORDER_HDR |
| LINE_NO | INT | Line number |
| PART_ID | VARCHAR(30) | FK to PART |
| VENDOR_ID | VARCHAR(30) | Vendor for this line |
| ORDER_QTY | DECIMAL(15,4) | Order quantity |
| RECEIVED_QTY | DECIMAL(15,4) | Received quantity |
| UNIT_PRICE | DECIMAL(15,4) | Unit price |

---

## Engineering Module Tables

### WORK_ORDER

Manufacturing work order headers.

| Column | Type | Description |
|--------|------|-------------|
| BASE_ID | VARCHAR(30) | Job number (PK part) |
| LOT_ID | VARCHAR(2) | Lot identifier (PK part) |
| SUB_ID | VARCHAR(2) | Sub-assembly ID (PK part) |
| PART_ID | VARCHAR(30) | FK to PART being made |
| DESIRED_QTY | DECIMAL(15,4) | Quantity to make |
| COMPLETED_QTY | DECIMAL(15,4) | Quantity completed |
| STATUS | VARCHAR(10) | Work order status |
| ORDER_DATE | DATE | WO creation date |
| DESIRED_DATE | DATE | Desired completion |
| COMPLETED_DATE | DATE | Actual completion |

**Composite Primary Key**: (BASE_ID, LOT_ID, SUB_ID)

### OPERATION

Manufacturing routing operations.

| Column | Type | Description |
|--------|------|-------------|
| WORKORDER_BASE_ID | VARCHAR(30) | FK to WORK_ORDER |
| WORKORDER_LOT_ID | VARCHAR(2) | FK to WORK_ORDER |
| WORKORDER_SUB_ID | VARCHAR(2) | FK to WORK_ORDER |
| SEQUENCE_NO | INT | Operation sequence (PK part) |
| OPERATION_ID | VARCHAR(10) | Operation code |
| DESCRIPTION | VARCHAR(50) | Operation description |
| DEPARTMENT | VARCHAR(10) | Department code |
| WORK_CENTER_ID | VARCHAR(10) | Work center |
| SETUP_HRS | DECIMAL(10,4) | Setup hours |
| RUN_HRS | DECIMAL(10,4) | Run hours per unit |
| STATUS | VARCHAR(10) | Operation status |

### REQUIREMENT

Bill of materials requirements.

| Column | Type | Description |
|--------|------|-------------|
| WORKORDER_BASE_ID | VARCHAR(30) | FK to WORK_ORDER |
| WORKORDER_LOT_ID | VARCHAR(2) | FK to WORK_ORDER |
| WORKORDER_SUB_ID | VARCHAR(2) | FK to WORK_ORDER |
| OPERATION_SEQ_NO | INT | FK to OPERATION sequence |
| PART_ID | VARCHAR(30) | Required part FK |
| QTY_PER | DECIMAL(15,6) | Quantity per assembly |
| FIXED_QTY | DECIMAL(15,4) | Fixed quantity |
| SCRAP_PERCENT | DECIMAL(5,2) | Scrap percentage |
| SUBORD_WO_SUB_ID | VARCHAR(2) | Child work order SUB_ID |

**Note**: `SUBORD_WO_SUB_ID` links to a child work order when the requirement is a sub-assembly.

### LABOR_TICKET

Labor hour tracking.

| Column | Type | Description |
|--------|------|-------------|
| WORKORDER_BASE_ID | VARCHAR(30) | FK to WORK_ORDER |
| WORKORDER_LOT_ID | VARCHAR(2) | FK to WORK_ORDER |
| WORKORDER_SUB_ID | VARCHAR(2) | FK to WORK_ORDER |
| EMPLOYEE_ID | VARCHAR(10) | Employee code |
| LABOR_DATE | DATE | Date worked |
| OPERATION_SEQ_NO | INT | FK to OPERATION |
| SETUP_HRS | DECIMAL(10,4) | Setup hours |
| RUN_HRS | DECIMAL(10,4) | Run hours |

### INVENTORY_TRANS

Material transactions.

| Column | Type | Description |
|--------|------|-------------|
| WORKORDER_BASE_ID | VARCHAR(30) | FK to WORK_ORDER |
| WORKORDER_LOT_ID | VARCHAR(2) | FK to WORK_ORDER |
| WORKORDER_SUB_ID | VARCHAR(2) | FK to WORK_ORDER |
| PART_ID | VARCHAR(30) | FK to PART |
| TRANS_TYPE | VARCHAR(10) | Issue, Return, Scrap |
| QUANTITY | DECIMAL(15,4) | Transaction quantity |
| TRANS_DATE | DATE | Transaction date |
| LOT_ID | VARCHAR(30) | Inventory lot |
| LOCATION_ID | VARCHAR(10) | Warehouse location |

### WIP_BALANCE

Work-in-progress cost accumulation.

| Column | Type | Description |
|--------|------|-------------|
| WORKORDER_BASE_ID | VARCHAR(30) | FK to WORK_ORDER |
| WORKORDER_LOT_ID | VARCHAR(2) | FK to WORK_ORDER |
| WORKORDER_SUB_ID | VARCHAR(2) | FK to WORK_ORDER |
| MATERIAL_COST | DECIMAL(15,2) | Material cost |
| LABOR_COST | DECIMAL(15,2) | Labor cost |
| BURDEN_COST | DECIMAL(15,2) | Overhead cost |
| TOTAL_COST | DECIMAL(15,2) | Total WIP cost |

---

## SQL Query Reference

### Sales Module Queries

#### Get Recent Orders
```sql
SELECT TOP (@limit)
    co.ID AS jobNumber,
    c.NAME AS customerName,
    co.CUSTOMER_PO_REF AS poNumber,
    co.ORDER_DATE AS orderDate,
    co.TOTAL_AMT_ORDERED AS totalAmount
FROM CUSTOMER_ORDER co
LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
ORDER BY co.ORDER_DATE DESC, co.ID DESC
```

#### Filter Orders by Date Range
```sql
SELECT TOP (@limit)
    co.ID AS jobNumber,
    c.NAME AS customerName,
    co.CUSTOMER_PO_REF AS poNumber,
    co.ORDER_DATE AS orderDate,
    co.TOTAL_AMT_ORDERED AS totalAmount
FROM CUSTOMER_ORDER co
LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
WHERE co.ORDER_DATE >= @startDate
  AND co.ORDER_DATE <= @endDate
ORDER BY co.ORDER_DATE DESC, co.ID DESC
```

#### Search by Job Number
```sql
SELECT
    co.ID AS id,
    co.ID AS jobNumber,
    co.ORDER_DATE AS orderDate,
    co.DESIRED_SHIP_DATE AS desiredShipDate,
    co.CUSTOMER_PO_REF AS poNumber,
    co.CONTACT_NAME AS contactName,
    co.CONTACT_PHONE AS contactPhone,
    co.CONTACT_EMAIL AS contactEmail,
    co.TOTAL_AMT_ORDERED AS totalAmount,
    co.PAYMENT_TERMS AS paymentTerms,
    c.ID AS customerId,
    c.NAME AS customerName,
    c.ADDR_1 AS shipAddr1,
    c.ADDR_2 AS shipAddr2,
    c.CITY AS shipCity,
    c.STATE AS shipState,
    c.ZIPCODE AS shipZip,
    c.COUNTRY AS shipCountry,
    c.BILL_TO_ADDR_1 AS billAddr1,
    c.BILL_TO_ADDR_2 AS billAddr2,
    c.BILL_TO_CITY AS billCity,
    c.BILL_TO_STATE AS billState,
    c.BILL_TO_ZIPCODE AS billZip,
    c.BILL_TO_COUNTRY AS billCountry,
    sr.NAME AS salesRepName
FROM CUSTOMER_ORDER co
LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
LEFT JOIN SALES_REP sr ON co.SALESREP_ID = sr.ID
WHERE co.ID = @jobNumber
```

#### Get Order Line Items
```sql
SELECT
    col.LINE_NO AS lineNo,
    col.PART_ID AS partId,
    p.DESCRIPTION AS description,
    col.ORDER_QTY AS orderQty,
    col.UNIT_PRICE AS unitPrice,
    col.EXTENDED_PRICE AS extendedPrice,
    col.BASE_ID AS baseId,
    col.LOT_ID AS lotId,
    clb.BITS AS bits
FROM CUST_ORDER_LINE col
LEFT JOIN PART p ON col.PART_ID = p.ID
LEFT JOIN CUST_LINE_BINARY clb
    ON col.CUST_ORDER_ID = clb.CUST_ORDER_ID
    AND col.LINE_NO = clb.CUST_ORDER_LINE_NO
WHERE col.CUST_ORDER_ID = @orderId
ORDER BY col.LINE_NO
```

#### Search by Customer Name
```sql
SELECT TOP (@limit)
    co.ID AS jobNumber,
    c.NAME AS customerName,
    co.CUSTOMER_PO_REF AS poNumber,
    co.ORDER_DATE AS orderDate,
    co.TOTAL_AMT_ORDERED AS totalAmount
FROM CUSTOMER_ORDER co
LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
WHERE UPPER(c.NAME) LIKE '%' + UPPER(@customerName) + '%'
ORDER BY co.ORDER_DATE DESC, co.ID DESC
```

### Inventory Module Queries

#### Get Part by ID
```sql
SELECT
    p.ID AS id,
    p.DESCRIPTION AS description,
    p.STOCK_UM AS stockUm,
    p.PRODUCT_CODE AS productCode,
    p.COMMODITY_CODE AS commodityCode,
    p.STANDARD_COST AS standardCost,
    p.AVERAGE_COST AS averageCost,
    p.LAST_COST AS lastCost,
    p.LIST_PRICE AS listPrice,
    p.QTY_ON_HAND AS qtyOnHand,
    p.QTY_ON_ORDER AS qtyOnOrder,
    p.QTY_ALLOCATED AS qtyAllocated,
    p.VENDOR_ID AS vendorId,
    v.NAME AS vendorName,
    p.MAKE_BUY_CODE AS makeBuyCode,
    p.ABC AS abc,
    p.PHANTOM_FLAG AS phantomFlag,
    p.STATUS AS status
FROM PART p
LEFT JOIN VENDOR v ON p.VENDOR_ID = v.ID
WHERE p.ID = @partId
```

#### Get Where Used (BOM Usage)
```sql
SELECT
    r.WORKORDER_BASE_ID AS baseId,
    r.WORKORDER_LOT_ID AS lotId,
    r.WORKORDER_SUB_ID AS subId,
    wo.PART_ID AS partId,
    r.QTY_PER AS qtyPer,
    r.FIXED_QTY AS fixedQty,
    r.SCRAP_PERCENT AS scrapPercent,
    wo.STATUS AS status
FROM REQUIREMENT r
JOIN WORK_ORDER wo
    ON r.WORKORDER_BASE_ID = wo.BASE_ID
    AND r.WORKORDER_LOT_ID = wo.LOT_ID
    AND r.WORKORDER_SUB_ID = wo.SUB_ID
WHERE r.PART_ID = @partId
ORDER BY r.WORKORDER_BASE_ID DESC
```

#### Get Purchase History
```sql
SELECT
    pol.PURC_ORDER_ID AS poNumber,
    pol.LINE_NO AS lineNo,
    pol.VENDOR_ID AS vendorId,
    v.NAME AS vendorName,
    poh.ORDER_DATE AS orderDate,
    pol.ORDER_QTY AS orderQty,
    pol.RECEIVED_QTY AS receivedQty,
    pol.UNIT_PRICE AS unitPrice,
    poh.CURRENCY_ID AS currencyId
FROM PURC_ORDER_LINE pol
JOIN PURC_ORDER_HDR poh ON pol.PURC_ORDER_ID = poh.ID
LEFT JOIN VENDOR v ON pol.VENDOR_ID = v.ID
WHERE pol.PART_ID = @partId
ORDER BY poh.ORDER_DATE DESC
```

### Engineering Module Queries

#### Search Work Orders
```sql
SELECT TOP (@limit)
    wo.BASE_ID AS baseId,
    wo.LOT_ID AS lotId,
    wo.SUB_ID AS subId,
    wo.PART_ID AS partId,
    p.DESCRIPTION AS partDescription,
    wo.DESIRED_QTY AS desiredQty,
    wo.STATUS AS status,
    wo.ORDER_DATE AS orderDate
FROM WORK_ORDER wo
LEFT JOIN PART p ON wo.PART_ID = p.ID
WHERE wo.BASE_ID LIKE @baseIdPattern + '%'
ORDER BY wo.BASE_ID DESC, wo.LOT_ID, wo.SUB_ID
```

#### Get Work Order Header with Counts
```sql
SELECT
    wo.BASE_ID AS baseId,
    wo.LOT_ID AS lotId,
    wo.SUB_ID AS subId,
    wo.PART_ID AS partId,
    p.DESCRIPTION AS partDescription,
    wo.DESIRED_QTY AS desiredQty,
    wo.COMPLETED_QTY AS completedQty,
    wo.STATUS AS status,
    wo.ORDER_DATE AS orderDate,
    wo.DESIRED_DATE AS desiredDate,
    wo.COMPLETED_DATE AS completedDate,
    (SELECT COUNT(*) FROM OPERATION o
     WHERE o.WORKORDER_BASE_ID = wo.BASE_ID
       AND o.WORKORDER_LOT_ID = wo.LOT_ID
       AND o.WORKORDER_SUB_ID = wo.SUB_ID) AS operationCount,
    (SELECT COUNT(*) FROM REQUIREMENT r
     WHERE r.WORKORDER_BASE_ID = wo.BASE_ID
       AND r.WORKORDER_LOT_ID = wo.LOT_ID
       AND r.WORKORDER_SUB_ID = wo.SUB_ID) AS requirementCount,
    (SELECT COUNT(*) FROM LABOR_TICKET lt
     WHERE lt.WORKORDER_BASE_ID = wo.BASE_ID
       AND lt.WORKORDER_LOT_ID = wo.LOT_ID
       AND lt.WORKORDER_SUB_ID = wo.SUB_ID) AS laborCount,
    (SELECT COUNT(*) FROM INVENTORY_TRANS it
     WHERE it.WORKORDER_BASE_ID = wo.BASE_ID
       AND it.WORKORDER_LOT_ID = wo.LOT_ID
       AND it.WORKORDER_SUB_ID = wo.SUB_ID) AS transactionCount
FROM WORK_ORDER wo
LEFT JOIN PART p ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = @baseId
  AND wo.LOT_ID = @lotId
  AND wo.SUB_ID = @subId
```

#### Get Operations
```sql
SELECT
    o.SEQUENCE_NO AS sequenceNo,
    o.OPERATION_ID AS operationId,
    o.DESCRIPTION AS description,
    o.DEPARTMENT AS department,
    o.WORK_CENTER_ID AS workCenter,
    o.SETUP_HRS AS setupHrs,
    o.RUN_HRS AS runHrsPer,
    o.STATUS AS status
FROM OPERATION o
WHERE o.WORKORDER_BASE_ID = @baseId
  AND o.WORKORDER_LOT_ID = @lotId
  AND o.WORKORDER_SUB_ID = @subId
ORDER BY o.SEQUENCE_NO
```

#### Get Requirements
```sql
SELECT
    r.PART_ID AS partId,
    p.DESCRIPTION AS description,
    r.QTY_PER AS qtyPer,
    r.FIXED_QTY AS fixedQty,
    r.SCRAP_PERCENT AS scrapPercent,
    r.SUBORD_WO_SUB_ID AS subordWoSubId,
    CASE WHEN r.SUBORD_WO_SUB_ID IS NOT NULL THEN 1 ELSE 0 END AS hasChildWorkOrder
FROM REQUIREMENT r
LEFT JOIN PART p ON r.PART_ID = p.ID
WHERE r.WORKORDER_BASE_ID = @baseId
  AND r.WORKORDER_LOT_ID = @lotId
  AND r.WORKORDER_SUB_ID = @subId
  AND (@seqNo IS NULL OR r.OPERATION_SEQ_NO = @seqNo)
ORDER BY r.OPERATION_SEQ_NO, r.PART_ID
```

#### Get Labor Tickets
```sql
SELECT
    lt.EMPLOYEE_ID AS employeeId,
    lt.LABOR_DATE AS laborDate,
    lt.SETUP_HRS AS setupHrs,
    lt.RUN_HRS AS runHrs,
    lt.OPERATION_SEQ_NO AS operationSeqNo
FROM LABOR_TICKET lt
WHERE lt.WORKORDER_BASE_ID = @baseId
  AND lt.WORKORDER_LOT_ID = @lotId
  AND lt.WORKORDER_SUB_ID = @subId
ORDER BY lt.LABOR_DATE DESC
```

#### Get Inventory Transactions
```sql
SELECT
    it.PART_ID AS partId,
    it.TRANS_TYPE AS transType,
    it.QUANTITY AS quantity,
    it.TRANS_DATE AS transDate,
    it.LOT_ID AS lotId,
    it.LOCATION_ID AS location
FROM INVENTORY_TRANS it
WHERE it.WORKORDER_BASE_ID = @baseId
  AND it.WORKORDER_LOT_ID = @lotId
  AND it.WORKORDER_SUB_ID = @subId
ORDER BY it.TRANS_DATE DESC
```

#### Get WIP Balance
```sql
SELECT
    wb.MATERIAL_COST AS materialCost,
    wb.LABOR_COST AS laborCost,
    wb.BURDEN_COST AS burdenCost,
    wb.TOTAL_COST AS totalCost
FROM WIP_BALANCE wb
WHERE wb.WORKORDER_BASE_ID = @baseId
  AND wb.WORKORDER_LOT_ID = @lotId
  AND wb.WORKORDER_SUB_ID = @subId
```

### BOM Queries

#### Get Job Assemblies (Top Level)
```sql
SELECT
    wo.BASE_ID AS baseId,
    wo.LOT_ID AS lotId,
    wo.SUB_ID AS subId,
    wo.PART_ID AS partId,
    p.DESCRIPTION AS description,
    NULL AS qtyPer,
    p.MAKE_BUY_CODE AS makeBuyCode,
    CASE WHEN EXISTS (
        SELECT 1 FROM REQUIREMENT r
        WHERE r.WORKORDER_BASE_ID = wo.BASE_ID
          AND r.WORKORDER_LOT_ID = wo.LOT_ID
          AND r.WORKORDER_SUB_ID = wo.SUB_ID
    ) THEN 1 ELSE 0 END AS hasChildren
FROM WORK_ORDER wo
LEFT JOIN PART p ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = @jobNumber
  AND wo.LOT_ID = '00'
ORDER BY wo.SUB_ID
```

#### Get BOM Children
```sql
SELECT
    COALESCE(cwo.BASE_ID, r.WORKORDER_BASE_ID) AS baseId,
    COALESCE(cwo.LOT_ID, r.WORKORDER_LOT_ID) AS lotId,
    COALESCE(cwo.SUB_ID, r.SUBORD_WO_SUB_ID) AS subId,
    r.PART_ID AS partId,
    p.DESCRIPTION AS description,
    r.QTY_PER AS qtyPer,
    p.MAKE_BUY_CODE AS makeBuyCode,
    CASE WHEN EXISTS (
        SELECT 1 FROM REQUIREMENT cr
        WHERE cr.WORKORDER_BASE_ID = COALESCE(cwo.BASE_ID, r.WORKORDER_BASE_ID)
          AND cr.WORKORDER_LOT_ID = COALESCE(cwo.LOT_ID, r.WORKORDER_LOT_ID)
          AND cr.WORKORDER_SUB_ID = COALESCE(cwo.SUB_ID, r.SUBORD_WO_SUB_ID)
    ) THEN 1 ELSE 0 END AS hasChildren
FROM REQUIREMENT r
LEFT JOIN PART p ON r.PART_ID = p.ID
LEFT JOIN WORK_ORDER cwo
    ON cwo.BASE_ID = r.WORKORDER_BASE_ID
    AND cwo.LOT_ID = r.WORKORDER_LOT_ID
    AND cwo.SUB_ID = r.SUBORD_WO_SUB_ID
WHERE r.WORKORDER_BASE_ID = @baseId
  AND r.WORKORDER_LOT_ID = @lotId
  AND r.WORKORDER_SUB_ID = @subId
ORDER BY r.OPERATION_SEQ_NO, r.PART_ID
```

---

## Binary Data Handling

The `BITS` column in `CUST_LINE_BINARY` and `CUST_ORDER_BINARY` contains text data stored as binary. In Node.js with the `mssql` package:

```typescript
// Converting binary to string
function decodeBinaryText(bits: Buffer | null): string | null {
  if (!bits) return null;

  // Try UTF-16LE first (common in SQL Server)
  try {
    return bits.toString('utf16le').replace(/\0/g, '').trim();
  } catch {
    // Fallback to UTF-8
    return bits.toString('utf8').replace(/\0/g, '').trim();
  }
}
```

---

## Index Recommendations

For optimal query performance in the web application, ensure these indexes exist:

```sql
-- Orders
CREATE INDEX IX_CUSTOMER_ORDER_DATE ON CUSTOMER_ORDER(ORDER_DATE DESC);
CREATE INDEX IX_CUSTOMER_ORDER_CUSTOMER ON CUSTOMER_ORDER(CUSTOMER_ID);

-- Work Orders
CREATE INDEX IX_WORK_ORDER_BASE_ID ON WORK_ORDER(BASE_ID);
CREATE INDEX IX_REQUIREMENT_WO ON REQUIREMENT(WORKORDER_BASE_ID, WORKORDER_LOT_ID, WORKORDER_SUB_ID);

-- Parts
CREATE INDEX IX_PURC_ORDER_LINE_PART ON PURC_ORDER_LINE(PART_ID);
CREATE INDEX IX_REQUIREMENT_PART ON REQUIREMENT(PART_ID);
```

---

*Document Version: 1.0*
*Last Updated: December 2024*
