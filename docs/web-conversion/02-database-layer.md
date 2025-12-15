# 02 - Database Layer

## Overview

The database layer handles all communication with the Visual/SAMCO SQL Server database. This is a **read-only** connection to an existing production database.

## SQL Server Connection

### Connection Pool Configuration (src/database/connection.ts)

```typescript
import sql from 'mssql';
import { config } from '../config';
import { logger } from '../utils/logger';

// Connection pool configuration
const poolConfig: sql.config = {
  server: config.db.server,
  port: config.db.port,
  database: config.db.database,
  user: config.db.user,
  password: config.db.password,
  options: {
    encrypt: false,
    trustServerCertificate: true,
    enableArithAbort: true,
  },
  pool: {
    min: config.db.pool.min,
    max: config.db.pool.max,
    idleTimeoutMillis: config.db.pool.idleTimeoutMillis,
  },
  connectionTimeout: 10000,  // 10 seconds
  requestTimeout: 30000,     // 30 seconds
};

let pool: sql.ConnectionPool | null = null;

/**
 * Initialize database connection pool with retry logic
 */
export async function connectDatabase(retries = 3, delay = 2000): Promise<sql.ConnectionPool> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      pool = await new sql.ConnectionPool(poolConfig).connect();
      logger.info('Database connection pool established');

      // Test connection
      await pool.request().query('SELECT 1 AS healthCheck');
      logger.info('Database health check passed');

      return pool;
    } catch (error) {
      logger.error(`Database connection attempt ${attempt}/${retries} failed:`, error);

      if (attempt < retries) {
        logger.info(`Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw new Error(`Failed to connect to database after ${retries} attempts`);
      }
    }
  }
  throw new Error('Database connection failed');
}

/**
 * Get the active connection pool
 */
export function getPool(): sql.ConnectionPool {
  if (!pool) {
    throw new Error('Database pool not initialized. Call connectDatabase() first.');
  }
  return pool;
}

/**
 * Close the connection pool gracefully
 */
export async function closeDatabase(): Promise<void> {
  if (pool) {
    await pool.close();
    pool = null;
    logger.info('Database connection pool closed');
  }
}

/**
 * Execute a query with automatic connection handling
 */
export async function executeQuery<T>(
  query: string,
  params?: Record<string, unknown>
): Promise<T[]> {
  const request = getPool().request();

  // Add parameters if provided
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      request.input(key, value);
    }
  }

  const result = await request.query(query);
  return result.recordset as T[];
}

/**
 * Execute a query and return single result
 */
export async function executeQuerySingle<T>(
  query: string,
  params?: Record<string, unknown>
): Promise<T | null> {
  const results = await executeQuery<T>(query, params);
  return results[0] || null;
}
```

## Key Database Tables

### Customer Order Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `CUSTOMER_ORDER` | Customer orders/jobs | `ID`, `CUSTOMER_ID`, `ORDER_DATE`, `TOTAL_AMT_ORDERED`, `CUSTOMER_PO_REF` |
| `CUSTOMER` | Customer master data | `ID`, `NAME`, `ADDR_*`, `BILL_TO_*` |
| `CUST_ORDER_LINE` | Order line items | `LINE_NO`, `PART_ID`, `ORDER_QTY`, `UNIT_PRICE`, `TOTAL_AMT_ORDERED` |
| `CUST_LINE_BINARY` | Binary text details | `BITS` (encoded as IMAGE/VARBINARY) |

### Part/Inventory Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `PART` | Part master data | `ID`, `DESCRIPTION`, `STOCK_UM`, costs, quantities, flags |
| `PURC_ORDER_LINE` | Purchase order lines | `PART_ID`, `VENDOR_ID`, `USER_ORDER_QTY`, `UNIT_PRICE`, `DESIRED_RECV_DATE` |
| `VENDOR` | Vendor master | `ID`, `NAME` |

### Work Order Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `WORK_ORDER` | Manufacturing work orders | `BASE_ID`, `LOT_ID`, `SUB_ID`, `PART_ID`, `ORDER_QTY`, `STATUS` |
| `OPERATION` | Routing operations | `SEQUENCE_NO`, `DEPARTMENT_ID`, `SETUP_HRS`, `RUN_HRS` |
| `REQUIREMENT` | BOM requirements | `PART_ID`, `QTY_PER_PIECE`, `SUBORD_WO_SUB_ID` |
| `LABOR_TICKET` | Labor transactions | `EMPLOYEE_ID`, `LABOR_DATE`, `SETUP_HRS`, `RUN_HRS`, `LABOR_RATE` |
| `INVENTORY_TRANS` | Material transactions | `PART_ID`, `TRANS_TYPE`, `QUANTITY`, `TRANS_DATE` |
| `WIP_BALANCE` | WIP costs | `MATERIAL_COST`, `LABOR_COST`, `BURDEN_COST` |
| `WORKORDER_BINARY` | Work order notes | `BITS` (binary) |
| `REQUIREMENT_BINARY` | Requirement notes | `BITS` (binary) |

## Query Files

### Order Queries (src/database/queries/order.queries.ts)

```typescript
import sql from 'mssql';
import { getPool } from '../connection';
import { OrderSummary, OrderHeader, OrderLineItem, Customer } from '../../models/order.model';

/**
 * Get recent orders with customer info
 */
export async function getRecentOrders(limit: number = 100): Promise<OrderSummary[]> {
  const query = `
    SELECT TOP (@limit)
      co.ID AS jobNumber,
      c.NAME AS customerName,
      co.ORDER_DATE AS orderDate,
      co.TOTAL_AMT_ORDERED AS totalAmount,
      co.CUSTOMER_PO_REF AS customerPO
    FROM CUSTOMER_ORDER co WITH (NOLOCK)
    INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
    ORDER BY co.ORDER_DATE DESC, co.ID DESC
  `;

  const result = await getPool()
    .request()
    .input('limit', sql.Int, limit)
    .query(query);

  return result.recordset;
}

/**
 * Search orders by date range
 */
export async function getOrdersByDateRange(
  startDate?: Date,
  endDate?: Date,
  limit: number = 100
): Promise<OrderSummary[]> {
  let query = `
    SELECT TOP (@limit)
      co.ID AS jobNumber,
      c.NAME AS customerName,
      co.ORDER_DATE AS orderDate,
      co.TOTAL_AMT_ORDERED AS totalAmount,
      co.CUSTOMER_PO_REF AS customerPO
    FROM CUSTOMER_ORDER co WITH (NOLOCK)
    INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
    WHERE 1=1
  `;

  const request = getPool().request().input('limit', sql.Int, limit);

  if (startDate) {
    query += ' AND co.ORDER_DATE >= @startDate';
    request.input('startDate', sql.Date, startDate);
  }

  if (endDate) {
    query += ' AND co.ORDER_DATE <= @endDate';
    request.input('endDate', sql.Date, endDate);
  }

  query += ' ORDER BY co.ORDER_DATE DESC, co.ID DESC';

  const result = await request.query(query);
  return result.recordset;
}

/**
 * Get order by job number
 */
export async function getOrderByJobNumber(jobNumber: string): Promise<OrderHeader | null> {
  const query = `
    SELECT
      co.ID AS jobNumber,
      co.ORDER_DATE AS orderDate,
      co.TOTAL_AMT_ORDERED AS totalAmount,
      co.CUSTOMER_PO_REF AS customerPO,
      co.DESIRED_SHIP_DATE AS desiredShipDate,
      co.PROMISED_DATE AS promisedDate,
      co.NOTE_1 AS note1,
      co.NOTE_2 AS note2,
      -- Customer shipping info
      c.ID AS customerId,
      c.NAME AS customerName,
      c.ADDR_1 AS shipAddr1,
      c.ADDR_2 AS shipAddr2,
      c.CITY AS shipCity,
      c.STATE AS shipState,
      c.ZIPCODE AS shipZip,
      c.COUNTRY AS shipCountry,
      -- Customer billing info
      c.BILL_TO_NAME AS billToName,
      c.BILL_TO_ADDR_1 AS billAddr1,
      c.BILL_TO_ADDR_2 AS billAddr2,
      c.BILL_TO_CITY AS billCity,
      c.BILL_TO_STATE AS billState,
      c.BILL_TO_ZIPCODE AS billZip,
      c.BILL_TO_COUNTRY AS billCountry,
      -- Contact info
      c.CONTACT AS contactName,
      c.PHONE AS phoneNumber,
      c.FAX AS faxNumber,
      c.E_MAIL AS email
    FROM CUSTOMER_ORDER co WITH (NOLOCK)
    INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
    WHERE co.ID = @jobNumber
  `;

  const result = await getPool()
    .request()
    .input('jobNumber', sql.VarChar, jobNumber)
    .query(query);

  if (result.recordset.length === 0) {
    return null;
  }

  return result.recordset[0];
}

/**
 * Get order line items
 */
export async function getOrderLineItems(jobNumber: string): Promise<OrderLineItem[]> {
  const query = `
    SELECT
      col.LINE_NO AS lineNumber,
      col.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      col.ORDER_QTY AS orderQty,
      col.UNIT_PRICE AS unitPrice,
      col.TOTAL_AMT_ORDERED AS lineTotal,
      col.DESIRED_SHIP_DATE AS desiredShipDate,
      col.PROMISED_SHIP_DATE AS promisedShipDate,
      col.BASE_ID AS baseId,
      col.LOT_ID AS lotId,
      -- Binary details (converted to text)
      CAST(CAST(clb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS binaryDetails
    FROM CUST_ORDER_LINE col WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON col.PART_ID = p.ID
    LEFT JOIN CUST_LINE_BINARY clb WITH (NOLOCK)
      ON col.CUST_ORDER_ID = clb.CUST_ORDER_ID
      AND col.LINE_NO = clb.LINE_NO
    WHERE col.CUST_ORDER_ID = @jobNumber
    ORDER BY col.LINE_NO
  `;

  const result = await getPool()
    .request()
    .input('jobNumber', sql.VarChar, jobNumber)
    .query(query);

  return result.recordset;
}

/**
 * Search orders by customer name
 */
export async function searchByCustomerName(
  customerName: string,
  startDate?: Date,
  endDate?: Date,
  limit: number = 100
): Promise<OrderSummary[]> {
  let query = `
    SELECT TOP (@limit)
      co.ID AS jobNumber,
      c.NAME AS customerName,
      co.ORDER_DATE AS orderDate,
      co.TOTAL_AMT_ORDERED AS totalAmount,
      co.CUSTOMER_PO_REF AS customerPO
    FROM CUSTOMER_ORDER co WITH (NOLOCK)
    INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
    WHERE c.NAME LIKE @customerPattern
  `;

  const request = getPool()
    .request()
    .input('limit', sql.Int, limit)
    .input('customerPattern', sql.VarChar, `%${customerName}%`);

  if (startDate) {
    query += ' AND co.ORDER_DATE >= @startDate';
    request.input('startDate', sql.Date, startDate);
  }

  if (endDate) {
    query += ' AND co.ORDER_DATE <= @endDate';
    request.input('endDate', sql.Date, endDate);
  }

  query += ' ORDER BY co.ORDER_DATE DESC, co.ID DESC';

  const result = await request.query(query);
  return result.recordset;
}
```

### Part Queries (src/database/queries/part.queries.ts)

```typescript
import sql from 'mssql';
import { getPool } from '../connection';
import { Part, WhereUsed, PurchaseHistory } from '../../models/part.model';

/**
 * Get part by part number
 */
export async function getPartByNumber(partNumber: string): Promise<Part | null> {
  const query = `
    SELECT
      p.ID AS partId,
      p.DESCRIPTION AS description,
      p.STOCK_UM AS stockUm,
      p.MATERIAL_COST AS materialCost,
      p.LABOR_COST AS laborCost,
      p.BURDEN_COST AS burdenCost,
      p.SERVICE_COST AS serviceCost,
      p.STANDARD_COST AS standardCost,
      p.LAST_COST AS lastCost,
      p.AVG_COST AS avgCost,
      p.QTY_ON_HAND AS qtyOnHand,
      p.QTY_ON_ORDER AS qtyOnOrder,
      p.QTY_ALLOCATED AS qtyAllocated,
      p.QTY_AVAILABLE AS qtyAvailable,
      p.PURCHASED AS purchased,
      p.FABRICATED AS fabricated,
      p.STOCKED AS stocked,
      v.NAME AS vendorName
    FROM PART p WITH (NOLOCK)
    LEFT JOIN VENDOR v WITH (NOLOCK) ON p.PREF_VENDOR_ID = v.ID
    WHERE p.ID = @partNumber
  `;

  const result = await getPool()
    .request()
    .input('partNumber', sql.VarChar, partNumber)
    .query(query);

  return result.recordset[0] || null;
}

/**
 * Search parts by partial number
 */
export async function searchParts(
  searchPattern: string,
  limit: number = 100
): Promise<Part[]> {
  const query = `
    SELECT TOP (@limit)
      p.ID AS partId,
      p.DESCRIPTION AS description,
      p.STOCK_UM AS stockUm,
      p.STANDARD_COST AS standardCost,
      p.QTY_ON_HAND AS qtyOnHand,
      p.QTY_AVAILABLE AS qtyAvailable
    FROM PART p WITH (NOLOCK)
    WHERE p.ID LIKE @searchPattern
    ORDER BY p.ID
  `;

  const result = await getPool()
    .request()
    .input('limit', sql.Int, limit)
    .input('searchPattern', sql.VarChar, `%${searchPattern}%`)
    .query(query);

  return result.recordset;
}

/**
 * Get where-used information for a part
 */
export async function getWhereUsed(partNumber: string, limit: number = 100): Promise<WhereUsed[]> {
  const query = `
    SELECT TOP (@limit)
      r.WORKORDER_BASE_ID AS workOrderBaseId,
      r.WORKORDER_LOT_ID AS workOrderLotId,
      r.WORKORDER_SUB_ID AS workOrderSubId,
      wo.PART_ID AS parentPartId,
      p.DESCRIPTION AS parentDescription,
      wo.STATUS AS workOrderStatus,
      r.QTY_PER_PIECE AS qtyPer,
      r.FIXED_QTY AS fixedQty
    FROM REQUIREMENT r WITH (NOLOCK)
    INNER JOIN WORK_ORDER wo WITH (NOLOCK)
      ON r.WORKORDER_BASE_ID = wo.BASE_ID
      AND r.WORKORDER_LOT_ID = wo.LOT_ID
      AND r.WORKORDER_SUB_ID = wo.SUB_ID
    INNER JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
    WHERE r.PART_ID = @partNumber
    ORDER BY wo.DESIRED_START_DATE DESC
  `;

  const result = await getPool()
    .request()
    .input('partNumber', sql.VarChar, partNumber)
    .input('limit', sql.Int, limit)
    .query(query);

  return result.recordset;
}

/**
 * Get purchase history for a part
 */
export async function getPurchaseHistory(
  partNumber: string,
  limit: number = 100
): Promise<PurchaseHistory[]> {
  const query = `
    SELECT TOP (@limit)
      pol.PURC_ORDER_ID AS purchaseOrderId,
      pol.LINE_NO AS lineNumber,
      v.NAME AS vendorName,
      pol.USER_ORDER_QTY AS orderQty,
      pol.UNIT_PRICE AS unitPrice,
      pol.DESIRED_RECV_DATE AS desiredReceiveDate,
      pol.TOTAL_RECEIVED_QTY AS receivedQty,
      pol.LAST_RECV_DATE AS lastReceiveDate
    FROM PURC_ORDER_LINE pol WITH (NOLOCK)
    INNER JOIN PURC_ORDER po WITH (NOLOCK) ON pol.PURC_ORDER_ID = po.ID
    INNER JOIN VENDOR v WITH (NOLOCK) ON po.VENDOR_ID = v.ID
    WHERE pol.PART_ID = @partNumber
    ORDER BY pol.DESIRED_RECV_DATE DESC
  `;

  const result = await getPool()
    .request()
    .input('partNumber', sql.VarChar, partNumber)
    .input('limit', sql.Int, limit)
    .query(query);

  return result.recordset;
}
```

### Work Order Queries (src/database/queries/workorder.queries.ts)

```typescript
import sql from 'mssql';
import { getPool } from '../connection';
import {
  WorkOrder,
  WorkOrderHeader,
  Operation,
  Requirement,
  LaborTicket,
  InventoryTransaction,
  WIPBalance,
} from '../../models/workorder.model';

/**
 * Search work orders by base ID pattern
 */
export async function searchWorkOrders(
  baseIdPattern: string,
  limit: number = 100
): Promise<WorkOrder[]> {
  const query = `
    SELECT TOP (@limit)
      wo.BASE_ID AS baseId,
      wo.LOT_ID AS lotId,
      wo.SUB_ID AS subId,
      wo.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      wo.ORDER_QTY AS orderQty,
      wo.STATUS AS status,
      wo.TYPE AS type,
      wo.DESIRED_START_DATE AS desiredStartDate,
      wo.DESIRED_COMPL_DATE AS desiredComplDate,
      wo.ACTUAL_START_DATE AS actualStartDate,
      wo.ACTUAL_COMPL_DATE AS actualComplDate
    FROM WORK_ORDER wo WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
    WHERE wo.BASE_ID LIKE @baseIdPattern
    ORDER BY wo.BASE_ID, wo.LOT_ID, wo.SUB_ID
  `;

  const result = await getPool()
    .request()
    .input('baseIdPattern', sql.VarChar, `${baseIdPattern}%`)
    .input('limit', sql.Int, limit)
    .query(query);

  return result.recordset;
}

/**
 * Get work order header with aggregate counts for lazy loading
 */
export async function getWorkOrderHeader(
  baseId: string,
  lotId: string,
  subId: string
): Promise<WorkOrderHeader | null> {
  const query = `
    SELECT
      wo.BASE_ID AS baseId,
      wo.LOT_ID AS lotId,
      wo.SUB_ID AS subId,
      wo.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      wo.ORDER_QTY AS orderQty,
      wo.COMPLETED_QTY AS completedQty,
      wo.SCRAPPED_QTY AS scrappedQty,
      wo.STATUS AS status,
      wo.TYPE AS type,
      wo.DESIRED_START_DATE AS desiredStartDate,
      wo.DESIRED_COMPL_DATE AS desiredComplDate,
      wo.ACTUAL_START_DATE AS actualStartDate,
      wo.ACTUAL_COMPL_DATE AS actualComplDate,
      wo.PRIORITY AS priority,
      wo.CUST_ORDER_ID AS custOrderId,
      wo.CUST_ORDER_LINE_NO AS custOrderLineNo,
      CAST(CAST(wob.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes,
      -- Aggregate counts for lazy loading indicators
      (SELECT COUNT(*) FROM OPERATION o WITH (NOLOCK)
       WHERE o.WORKORDER_BASE_ID = wo.BASE_ID
         AND o.WORKORDER_LOT_ID = wo.LOT_ID
         AND o.WORKORDER_SUB_ID = wo.SUB_ID) AS operationCount,
      (SELECT COUNT(*) FROM LABOR_TICKET lt WITH (NOLOCK)
       WHERE lt.WORKORDER_BASE_ID = wo.BASE_ID
         AND lt.WORKORDER_LOT_ID = wo.LOT_ID
         AND lt.WORKORDER_SUB_ID = wo.SUB_ID) AS laborTicketCount,
      (SELECT COUNT(*) FROM INVENTORY_TRANS it WITH (NOLOCK)
       WHERE it.WORKORDER_BASE_ID = wo.BASE_ID
         AND it.WORKORDER_LOT_ID = wo.LOT_ID
         AND it.WORKORDER_SUB_ID = wo.SUB_ID) AS inventoryTransCount
    FROM WORK_ORDER wo WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
    LEFT JOIN WORKORDER_BINARY wob WITH (NOLOCK)
      ON wo.BASE_ID = wob.BASE_ID
      AND wo.LOT_ID = wob.LOT_ID
      AND wo.SUB_ID = wob.SUB_ID
    WHERE wo.BASE_ID = @baseId
      AND wo.LOT_ID = @lotId
      AND wo.SUB_ID = @subId
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset[0] || null;
}

/**
 * Get operations for a work order
 */
export async function getOperations(
  baseId: string,
  lotId: string,
  subId: string
): Promise<Operation[]> {
  const query = `
    SELECT
      o.SEQUENCE_NO AS sequenceNo,
      o.RESOURCE_ID AS resourceId,
      o.DEPARTMENT_ID AS departmentId,
      d.DESCRIPTION AS departmentName,
      o.SETUP_HRS AS setupHrs,
      o.RUN_HRS AS runHrs,
      o.RUN_TYPE AS runType,
      o.STATUS AS status,
      o.ACTUAL_START_DATE AS actualStartDate,
      o.ACTUAL_FINISH_DATE AS actualFinishDate,
      -- Requirement count for this operation
      (SELECT COUNT(*) FROM REQUIREMENT r WITH (NOLOCK)
       WHERE r.WORKORDER_BASE_ID = o.WORKORDER_BASE_ID
         AND r.WORKORDER_LOT_ID = o.WORKORDER_LOT_ID
         AND r.WORKORDER_SUB_ID = o.WORKORDER_SUB_ID
         AND r.OPERATION_SEQ_NO = o.SEQUENCE_NO) AS requirementCount
    FROM OPERATION o WITH (NOLOCK)
    LEFT JOIN DEPARTMENT d WITH (NOLOCK) ON o.DEPARTMENT_ID = d.ID
    WHERE o.WORKORDER_BASE_ID = @baseId
      AND o.WORKORDER_LOT_ID = @lotId
      AND o.WORKORDER_SUB_ID = @subId
    ORDER BY o.SEQUENCE_NO
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset;
}

/**
 * Get requirements for an operation
 */
export async function getRequirements(
  baseId: string,
  lotId: string,
  subId: string,
  operationSeqNo?: number
): Promise<Requirement[]> {
  let query = `
    SELECT
      r.PIECE_NO AS pieceNo,
      r.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      r.QTY_PER_PIECE AS qtyPerPiece,
      r.FIXED_QTY AS fixedQty,
      r.SCRAP_PERCENT AS scrapPercent,
      r.OPERATION_SEQ_NO AS operationSeqNo,
      r.SUBORD_WO_SUB_ID AS subordWoSubId,
      r.QTY_ISSUED AS qtyIssued,
      r.QTY_ALLOCATED AS qtyAllocated,
      CAST(CAST(rb.BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
    FROM REQUIREMENT r WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
    LEFT JOIN REQUIREMENT_BINARY rb WITH (NOLOCK)
      ON r.WORKORDER_BASE_ID = rb.WORKORDER_BASE_ID
      AND r.WORKORDER_LOT_ID = rb.WORKORDER_LOT_ID
      AND r.WORKORDER_SUB_ID = rb.WORKORDER_SUB_ID
      AND r.PIECE_NO = rb.PIECE_NO
    WHERE r.WORKORDER_BASE_ID = @baseId
      AND r.WORKORDER_LOT_ID = @lotId
      AND r.WORKORDER_SUB_ID = @subId
  `;

  const request = getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId);

  if (operationSeqNo !== undefined) {
    query += ' AND r.OPERATION_SEQ_NO = @operationSeqNo';
    request.input('operationSeqNo', sql.Int, operationSeqNo);
  }

  query += ' ORDER BY r.PIECE_NO';

  const result = await request.query(query);
  return result.recordset;
}

/**
 * Get labor tickets for a work order
 */
export async function getLaborTickets(
  baseId: string,
  lotId: string,
  subId: string
): Promise<LaborTicket[]> {
  const query = `
    SELECT
      lt.EMPLOYEE_ID AS employeeId,
      e.NAME AS employeeName,
      lt.LABOR_DATE AS laborDate,
      lt.SEQUENCE_NO AS operationSeqNo,
      lt.SETUP_HRS AS setupHrs,
      lt.RUN_HRS AS runHrs,
      lt.LABOR_RATE AS laborRate,
      lt.TOTAL_LABOR_COST AS totalLaborCost,
      lt.BURDEN_COST AS burdenCost,
      lt.QTY_COMPLETED AS qtyCompleted,
      lt.QTY_SCRAPPED AS qtyScrapped
    FROM LABOR_TICKET lt WITH (NOLOCK)
    LEFT JOIN EMPLOYEE e WITH (NOLOCK) ON lt.EMPLOYEE_ID = e.ID
    WHERE lt.WORKORDER_BASE_ID = @baseId
      AND lt.WORKORDER_LOT_ID = @lotId
      AND lt.WORKORDER_SUB_ID = @subId
    ORDER BY lt.LABOR_DATE DESC, lt.SEQUENCE_NO
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset;
}

/**
 * Get inventory transactions for a work order
 */
export async function getInventoryTransactions(
  baseId: string,
  lotId: string,
  subId: string
): Promise<InventoryTransaction[]> {
  const query = `
    SELECT
      it.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      it.TRANS_TYPE AS transType,
      it.QUANTITY AS quantity,
      it.TRANS_DATE AS transDate,
      it.LOCATION_ID AS locationId,
      it.UNIT_COST AS unitCost,
      it.TOTAL_COST AS totalCost
    FROM INVENTORY_TRANS it WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON it.PART_ID = p.ID
    WHERE it.WORKORDER_BASE_ID = @baseId
      AND it.WORKORDER_LOT_ID = @lotId
      AND it.WORKORDER_SUB_ID = @subId
    ORDER BY it.TRANS_DATE DESC
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset;
}

/**
 * Get WIP balance for a work order
 */
export async function getWIPBalance(
  baseId: string,
  lotId: string,
  subId: string
): Promise<WIPBalance | null> {
  const query = `
    SELECT
      wb.MATERIAL_COST AS materialCost,
      wb.LABOR_COST AS laborCost,
      wb.BURDEN_COST AS burdenCost,
      wb.SERVICE_COST AS serviceCost,
      (wb.MATERIAL_COST + wb.LABOR_COST + wb.BURDEN_COST + wb.SERVICE_COST) AS totalCost
    FROM WIP_BALANCE wb WITH (NOLOCK)
    WHERE wb.WORKORDER_BASE_ID = @baseId
      AND wb.WORKORDER_LOT_ID = @lotId
      AND wb.WORKORDER_SUB_ID = @subId
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset[0] || null;
}

/**
 * Get work order hierarchy using recursive CTE
 * Returns parent and all child work orders
 */
export async function getWorkOrderHierarchy(
  baseId: string,
  lotId: string,
  subId: string
): Promise<WorkOrder[]> {
  const query = `
    WITH work_order_hierarchy AS (
      -- Base case: root work order
      SELECT
        wo.BASE_ID,
        wo.LOT_ID,
        wo.SUB_ID,
        wo.PART_ID,
        wo.ORDER_QTY,
        wo.STATUS,
        wo.TYPE,
        0 AS level,
        CAST(wo.SUB_ID AS VARCHAR(MAX)) AS path
      FROM WORK_ORDER wo WITH (NOLOCK)
      WHERE wo.BASE_ID = @baseId
        AND wo.LOT_ID = @lotId
        AND wo.SUB_ID = @subId

      UNION ALL

      -- Recursive case: find children via SUBORD_WO_SUB_ID
      SELECT
        child.BASE_ID,
        child.LOT_ID,
        child.SUB_ID,
        child.PART_ID,
        child.ORDER_QTY,
        child.STATUS,
        child.TYPE,
        parent.level + 1,
        parent.path + '/' + child.SUB_ID
      FROM WORK_ORDER child WITH (NOLOCK)
      INNER JOIN work_order_hierarchy parent
        ON child.BASE_ID = parent.BASE_ID
        AND child.LOT_ID = parent.LOT_ID
      INNER JOIN REQUIREMENT r WITH (NOLOCK)
        ON r.WORKORDER_BASE_ID = parent.BASE_ID
        AND r.WORKORDER_LOT_ID = parent.LOT_ID
        AND r.WORKORDER_SUB_ID = parent.SUB_ID
        AND r.SUBORD_WO_SUB_ID = child.SUB_ID
      WHERE child.SUB_ID != '0'
    )
    SELECT
      h.BASE_ID AS baseId,
      h.LOT_ID AS lotId,
      h.SUB_ID AS subId,
      h.PART_ID AS partId,
      p.DESCRIPTION AS partDescription,
      h.ORDER_QTY AS orderQty,
      h.STATUS AS status,
      h.TYPE AS type,
      h.level AS hierarchyLevel,
      h.path AS hierarchyPath
    FROM work_order_hierarchy h
    INNER JOIN PART p WITH (NOLOCK) ON h.PART_ID = p.ID
    ORDER BY h.path
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset;
}
```

## Query Patterns

### Pattern 1: WITH (NOLOCK) Hint
All queries use `WITH (NOLOCK)` since this is a read-only application. This avoids lock contention with the production database.

### Pattern 2: Parameterized Queries
All user inputs are parameterized to prevent SQL injection:
```typescript
request.input('partNumber', sql.VarChar, partNumber);
```

### Pattern 3: Dynamic WHERE Clauses
For optional filters, build queries dynamically:
```typescript
let query = 'SELECT ... WHERE 1=1';
if (startDate) {
  query += ' AND ORDER_DATE >= @startDate';
  request.input('startDate', sql.Date, startDate);
}
```

### Pattern 4: Aggregate Counts for Lazy Loading
Include counts to indicate expandable items without fetching all data:
```sql
(SELECT COUNT(*) FROM OPERATION WHERE ...) AS operationCount
```

### Pattern 5: Binary Data Conversion
Binary text columns require conversion:
```sql
CAST(CAST(BITS AS VARBINARY(MAX)) AS VARCHAR(MAX)) AS notes
```
