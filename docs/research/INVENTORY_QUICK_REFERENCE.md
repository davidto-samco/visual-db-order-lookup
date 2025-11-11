# Inventory Module - Quick Reference

## Core Tables

| Table | Purpose |
|-------|---------|
| **PART** | Part master data (part numbers, descriptions, costs, quantities) |
| **INVENTORY_TRANS** | Inventory transactions (links parts to orders/work orders) |
| **PURC_ORDER_LINE** | Purchase order lines (purchase history) |
| **PURCHASE_ORDER** | Purchase order headers |
| **VENDOR** | Vendor master data |

## Three Key Queries

### 1. Part Lookup
```sql
SELECT p.ID, p.DESCRIPTION, p.STOCK_UM, p.UNIT_PRICE, p.QTY_ON_HAND, v.NAME
FROM PART p WITH (NOLOCK)
LEFT JOIN VENDOR v WITH (NOLOCK) ON p.PREF_VENDOR_ID = v.ID
WHERE p.ID = ?
```

### 2. Where-Used (Orders Using Part)
```sql
SELECT it.CUST_ORDER_ID, it.WORKORDER_BASE_ID, it.TRANSACTION_DATE,
       it.QTY, c.NAME
FROM INVENTORY_TRANS it WITH (NOLOCK)
LEFT JOIN CUSTOMER_ORDER co WITH (NOLOCK) ON it.CUST_ORDER_ID = co.ID
LEFT JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE it.PART_ID = ? AND it.TYPE = 'I'
ORDER BY it.TRANSACTION_DATE DESC
```

### 3. Purchase History
```sql
SELECT po.ID, po.ORDER_DATE, v.NAME, pol.USER_ORDER_QTY,
       pol.UNIT_PRICE, pol.TOTAL_AMT_ORDERED
FROM PURC_ORDER_LINE pol WITH (NOLOCK)
INNER JOIN PURCHASE_ORDER po WITH (NOLOCK) ON pol.PURC_ORDER_ID = po.ID
INNER JOIN VENDOR v WITH (NOLOCK) ON po.VENDOR_ID = v.ID
WHERE pol.PART_ID = ?
ORDER BY po.ORDER_DATE DESC
```

## Key PART Table Columns

- `ID` - Part number (Primary Key)
- `DESCRIPTION` - Part description (40 chars)
- `STOCK_UM` - Unit of measure
- `UNIT_MATERIAL_COST` - Material cost
- `UNIT_LABOR_COST` - Labor cost
- `UNIT_PRICE` - Selling price
- `MATERIAL_CODE` - Material specification
- `QTY_ON_HAND` - Current inventory
- `QTY_AVAILABLE_ISS` - Available quantity
- `DRAWING_ID` - Drawing reference
- `PREF_VENDOR_ID` - Preferred vendor

## Test Parts

- **F0195**: SLW 1/2 (995 POs, best for testing)
- **R5000**: ROLL TOOLING SLUGS (885 POs)
- **PF004**: 1/4 - 20 x 3/4" BOLT (has order history)

## Extended Description

For longer descriptions, query `PART_BINARY`:
```sql
SELECT BITS FROM PART_BINARY WITH (NOLOCK)
WHERE PART_ID = ? AND RTRIM(TYPE) = 'D'
```
Decode as UTF-8 text.

---

See **INVENTORY_SCHEMA_RESEARCH_REPORT.md** for complete details.
