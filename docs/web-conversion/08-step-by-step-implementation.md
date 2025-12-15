# 08 - Step-by-Step Implementation Guide

This guide walks you through building the Express backend file by file, in the correct dependency order.

---

## Phase 1: Project Setup

### Step 1.1: Create project directory and initialize npm

```bash
mkdir server
cd server
npm init -y
```

### Step 1.2: Install dependencies

```bash
npm install express mssql cors helmet compression dotenv winston express-validator http-status-codes
npm install -D nodemon jest supertest eslint
```

### Step 1.3: Create directory structure

```bash
mkdir -p src/config src/database/queries src/utils src/middleware src/services src/controllers src/routes
```

---

## Phase 2: Configuration Files (No Dependencies)

### Step 2.1: Create `.env` file

**File: `server/.env`**

```env
NODE_ENV=development
PORT=3001

DB_SERVER=10.10.10.142
DB_PORT=1433
DB_DATABASE=SAMCO
DB_USER=sa
DB_PASSWORD=your_password_here

CORS_ORIGIN=http://localhost:3000
LOG_LEVEL=info

DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=500
```

### Step 2.2: Create `.env.example` (same content, no password)

**File: `server/.env.example`**

```env
NODE_ENV=development
PORT=3001

DB_SERVER=10.10.10.142
DB_PORT=1433
DB_DATABASE=SAMCO
DB_USER=sa
DB_PASSWORD=

CORS_ORIGIN=http://localhost:3000
LOG_LEVEL=info

DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=500
```

### Step 2.3: Create config loader

**File: `server/src/config/index.js`**

```javascript
require('dotenv').config();

const config = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3001', 10),

  db: {
    server: process.env.DB_SERVER || '10.10.10.142',
    port: parseInt(process.env.DB_PORT || '1433', 10),
    database: process.env.DB_DATABASE || 'SAMCO',
    user: process.env.DB_USER || 'sa',
    password: process.env.DB_PASSWORD || '',
    options: {
      encrypt: false,
      trustServerCertificate: true,
      enableArithAbort: true,
    },
    pool: {
      min: 2,
      max: 10,
      idleTimeoutMillis: 30000,
    },
  },

  logLevel: process.env.LOG_LEVEL || 'info',
  defaultPageSize: parseInt(process.env.DEFAULT_PAGE_SIZE || '100', 10),
  maxPageSize: parseInt(process.env.MAX_PAGE_SIZE || '500', 10),
};

module.exports = config;
```

### Step 2.4: Create package.json scripts

**File: `server/package.json`** (update scripts section)

```json
{
  "name": "visual-db-server",
  "version": "1.0.0",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint src/**/*.js"
  }
}
```

---

## Phase 3: Utilities (Config dependency only)

### Step 3.1: Create logger

**File: `server/src/utils/logger.js`**

```javascript
const winston = require('winston');
const config = require('../config');

const logger = winston.createLogger({
  level: config.logLevel,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
    }),
  ],
});

module.exports = logger;
```

### Step 3.2: Create custom error classes

**File: `server/src/utils/errors.js`**

```javascript
class AppError extends Error {
  constructor(message, statusCode, code) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, details = []) {
    super(message, 400, 'VALIDATION_ERROR');
    this.details = details;
  }
}

class NotFoundError extends AppError {
  constructor(resource, identifier) {
    super(`${resource} not found: ${identifier}`, 404, 'NOT_FOUND');
    this.resource = resource;
    this.identifier = identifier;
  }
}

class DatabaseError extends AppError {
  constructor(message, originalError) {
    super(message, 500, 'DATABASE_ERROR');
    this.originalError = originalError;
  }
}

module.exports = {
  AppError,
  ValidationError,
  NotFoundError,
  DatabaseError,
};
```

### Step 3.3: Create formatters

**File: `server/src/utils/formatters.js`**

```javascript
/**
 * Format date to YYYY-MM-DD
 * @param {Date|string} date
 * @returns {string|null}
 */
function formatDate(date) {
  if (!date) return null;
  const d = new Date(date);
  return d.toISOString().split('T')[0];
}

/**
 * Format currency to 2 decimal places
 * @param {number} amount
 * @returns {string}
 */
function formatCurrency(amount) {
  if (amount == null) return '0.00';
  return Number(amount).toFixed(2);
}

/**
 * Format work order ID from components
 * @param {string} baseId
 * @param {string} lotId
 * @param {string} subId
 * @returns {string}
 */
function formatWorkOrderId(baseId, lotId, subId) {
  return `${baseId}-${lotId}-${subId}`;
}

/**
 * Parse work order ID string into components
 * @param {string} workOrderId
 * @returns {{baseId: string, lotId: string, subId: string}}
 */
function parseWorkOrderId(workOrderId) {
  const parts = workOrderId.split('-');
  if (parts.length !== 3) {
    throw new Error('Invalid work order ID format. Expected: BASE-LOT-SUB');
  }
  return {
    baseId: parts[0],
    lotId: parts[1],
    subId: parts[2],
  };
}

/**
 * Clean binary text from database
 * @param {string|null} binaryText
 * @returns {string|null}
 */
function cleanBinaryText(binaryText) {
  if (!binaryText) return null;
  // Remove null characters and trim
  return binaryText.replace(/\x00/g, '').trim() || null;
}

module.exports = {
  formatDate,
  formatCurrency,
  formatWorkOrderId,
  parseWorkOrderId,
  cleanBinaryText,
};
```

### Step 3.4: Create utils index

**File: `server/src/utils/index.js`**

```javascript
const logger = require('./logger');
const errors = require('./errors');
const formatters = require('./formatters');

module.exports = {
  logger,
  ...errors,
  ...formatters,
};
```

---

## Phase 4: Database Layer

### Step 4.1: Create database connection

**File: `server/src/database/connection.js`**

```javascript
const sql = require('mssql');
const config = require('../config');
const logger = require('../utils/logger');

const poolConfig = {
  server: config.db.server,
  port: config.db.port,
  database: config.db.database,
  user: config.db.user,
  password: config.db.password,
  options: config.db.options,
  pool: config.db.pool,
  connectionTimeout: 10000,
  requestTimeout: 30000,
};

let pool = null;

async function connectDatabase(retries = 3, delay = 2000) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      pool = await new sql.ConnectionPool(poolConfig).connect();
      logger.info('Database connection pool established');

      await pool.request().query('SELECT 1 AS healthCheck');
      logger.info('Database health check passed');

      return pool;
    } catch (error) {
      logger.error(`Database connection attempt ${attempt}/${retries} failed:`, error.message);

      if (attempt < retries) {
        logger.info(`Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw new Error(`Failed to connect to database after ${retries} attempts`);
      }
    }
  }
}

function getPool() {
  if (!pool) {
    throw new Error('Database pool not initialized. Call connectDatabase() first.');
  }
  return pool;
}

async function closeDatabase() {
  if (pool) {
    await pool.close();
    pool = null;
    logger.info('Database connection pool closed');
  }
}

async function executeQuery(query, params = {}) {
  const request = getPool().request();
  for (const [key, value] of Object.entries(params)) {
    request.input(key, value);
  }
  const result = await request.query(query);
  return result.recordset;
}

async function executeQuerySingle(query, params = {}) {
  const results = await executeQuery(query, params);
  return results[0] || null;
}

module.exports = {
  connectDatabase,
  getPool,
  closeDatabase,
  executeQuery,
  executeQuerySingle,
  sql,
};
```

### Step 4.2: Create order queries

**File: `server/src/database/queries/order.queries.js`**

```javascript
const { getPool, sql } = require('../connection');

async function getRecentOrders(limit = 100) {
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

async function getOrderByJobNumber(jobNumber) {
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
      c.ID AS customerId,
      c.NAME AS customerName,
      c.ADDR_1 AS shipAddr1,
      c.ADDR_2 AS shipAddr2,
      c.CITY AS shipCity,
      c.STATE AS shipState,
      c.ZIPCODE AS shipZip,
      c.COUNTRY AS shipCountry,
      c.BILL_TO_NAME AS billToName,
      c.BILL_TO_ADDR_1 AS billAddr1,
      c.BILL_TO_ADDR_2 AS billAddr2,
      c.BILL_TO_CITY AS billCity,
      c.BILL_TO_STATE AS billState,
      c.BILL_TO_ZIPCODE AS billZip,
      c.BILL_TO_COUNTRY AS billCountry,
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

  return result.recordset[0] || null;
}

async function getOrderLineItems(jobNumber) {
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

async function searchByCustomerName(customerName, startDate, endDate, limit = 100) {
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

module.exports = {
  getRecentOrders,
  getOrderByJobNumber,
  getOrderLineItems,
  searchByCustomerName,
};
```

### Step 4.3: Create part queries

**File: `server/src/database/queries/part.queries.js`**

```javascript
const { getPool, sql } = require('../connection');

async function getPartByNumber(partNumber) {
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

async function searchParts(searchPattern, limit = 100) {
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

async function getWhereUsed(partNumber, limit = 100) {
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

async function getPurchaseHistory(partNumber, limit = 100) {
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

module.exports = {
  getPartByNumber,
  searchParts,
  getWhereUsed,
  getPurchaseHistory,
};
```

### Step 4.4: Create work order queries

**File: `server/src/database/queries/workorder.queries.js`**

```javascript
const { getPool, sql } = require('../connection');

async function searchWorkOrders(baseIdPattern, limit = 100) {
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
      wo.DESIRED_COMPL_DATE AS desiredComplDate
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

async function getWorkOrderHeader(baseId, lotId, subId) {
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
      (SELECT COUNT(*) FROM OPERATION o WITH (NOLOCK)
       WHERE o.WORKORDER_BASE_ID = wo.BASE_ID
         AND o.WORKORDER_LOT_ID = wo.LOT_ID
         AND o.WORKORDER_SUB_ID = wo.SUB_ID) AS operationCount,
      (SELECT COUNT(*) FROM LABOR_TICKET lt WITH (NOLOCK)
       WHERE lt.WORKORDER_BASE_ID = wo.BASE_ID
         AND lt.WORKORDER_LOT_ID = wo.LOT_ID
         AND lt.WORKORDER_SUB_ID = wo.SUB_ID) AS laborTicketCount
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

async function getOperations(baseId, lotId, subId) {
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
      o.ACTUAL_FINISH_DATE AS actualFinishDate
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

async function getRequirements(baseId, lotId, subId) {
  const query = `
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
      r.QTY_ALLOCATED AS qtyAllocated
    FROM REQUIREMENT r WITH (NOLOCK)
    INNER JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
    WHERE r.WORKORDER_BASE_ID = @baseId
      AND r.WORKORDER_LOT_ID = @lotId
      AND r.WORKORDER_SUB_ID = @subId
    ORDER BY r.PIECE_NO
  `;

  const result = await getPool()
    .request()
    .input('baseId', sql.VarChar, baseId)
    .input('lotId', sql.VarChar, lotId)
    .input('subId', sql.VarChar, subId)
    .query(query);

  return result.recordset;
}

async function getLaborTickets(baseId, lotId, subId) {
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

async function getWorkOrderHierarchy(baseId, lotId, subId) {
  const query = `
    WITH work_order_hierarchy AS (
      SELECT
        wo.BASE_ID,
        wo.LOT_ID,
        wo.SUB_ID,
        wo.PART_ID,
        wo.ORDER_QTY,
        wo.STATUS,
        0 AS level,
        CAST(wo.SUB_ID AS VARCHAR(MAX)) AS path
      FROM WORK_ORDER wo WITH (NOLOCK)
      WHERE wo.BASE_ID = @baseId
        AND wo.LOT_ID = @lotId
        AND wo.SUB_ID = @subId

      UNION ALL

      SELECT
        child.BASE_ID,
        child.LOT_ID,
        child.SUB_ID,
        child.PART_ID,
        child.ORDER_QTY,
        child.STATUS,
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

module.exports = {
  searchWorkOrders,
  getWorkOrderHeader,
  getOperations,
  getRequirements,
  getLaborTickets,
  getWorkOrderHierarchy,
};
```

### Step 4.5: Create database index

**File: `server/src/database/index.js`**

```javascript
const {
  connectDatabase,
  closeDatabase,
  getPool,
  executeQuery,
  executeQuerySingle,
  sql,
} = require('./connection');

const orderQueries = require('./queries/order.queries');
const partQueries = require('./queries/part.queries');
const workorderQueries = require('./queries/workorder.queries');

module.exports = {
  connectDatabase,
  closeDatabase,
  getPool,
  executeQuery,
  executeQuerySingle,
  sql,
  orderQueries,
  partQueries,
  workorderQueries,
};
```

---

## Phase 5: Middleware

### Step 5.1: Create error middleware

**File: `server/src/middleware/error.middleware.js`**

```javascript
const logger = require('../utils/logger');
const { AppError } = require('../utils/errors');

function errorMiddleware(err, req, res, next) {
  // Log the error
  logger.error('Error:', {
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
  });

  // Handle known operational errors
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details || undefined,
      },
    });
  }

  // Handle SQL Server errors
  if (err.code === 'ESOCKET' || err.code === 'ECONNREFUSED') {
    return res.status(503).json({
      success: false,
      error: {
        code: 'DATABASE_UNAVAILABLE',
        message: 'Database connection unavailable',
      },
    });
  }

  // Default to 500 for unknown errors
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: process.env.NODE_ENV === 'production'
        ? 'An unexpected error occurred'
        : err.message,
    },
  });
}

module.exports = { errorMiddleware };
```

### Step 5.2: Create logging middleware

**File: `server/src/middleware/logging.middleware.js`**

```javascript
const logger = require('../utils/logger');

function loggingMiddleware(req, res, next) {
  const startTime = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - startTime;
    logger.info('Request completed', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: `${duration}ms`,
    });
  });

  next();
}

module.exports = { loggingMiddleware };
```

### Step 5.3: Create validation middleware

**File: `server/src/middleware/validation.middleware.js`**

```javascript
const { validationResult } = require('express-validator');
const { ValidationError } = require('../utils/errors');

function validate(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    const details = errors.array().map(err => ({
      field: err.path,
      message: err.msg,
    }));
    throw new ValidationError('Validation failed', details);
  }
  next();
}

module.exports = { validate };
```

### Step 5.4: Create middleware index

**File: `server/src/middleware/index.js`**

```javascript
const { errorMiddleware } = require('./error.middleware');
const { loggingMiddleware } = require('./logging.middleware');
const { validate } = require('./validation.middleware');

module.exports = {
  errorMiddleware,
  loggingMiddleware,
  validate,
};
```

---

## Phase 6: Services

### Step 6.1: Create async handler helper

**File: `server/src/utils/asyncHandler.js`**

```javascript
/**
 * Wraps async route handlers to catch errors
 * @param {Function} fn - Async function to wrap
 * @returns {Function}
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = { asyncHandler };
```

### Step 6.2: Create order service

**File: `server/src/services/order.service.js`**

```javascript
const orderQueries = require('../database/queries/order.queries');
const { NotFoundError } = require('../utils/errors');
const { formatDate, formatCurrency, cleanBinaryText } = require('../utils/formatters');

async function getRecentOrders(limit) {
  const orders = await orderQueries.getRecentOrders(limit);
  return orders.map(transformOrderSummary);
}

async function getOrderByJobNumber(jobNumber) {
  const order = await orderQueries.getOrderByJobNumber(jobNumber);
  if (!order) {
    throw new NotFoundError('Order', jobNumber);
  }
  return transformOrderDetail(order);
}

async function getOrderLineItems(jobNumber) {
  const lines = await orderQueries.getOrderLineItems(jobNumber);
  return lines.map(transformLineItem);
}

async function searchByCustomerName(customerName, startDate, endDate, limit) {
  const orders = await orderQueries.searchByCustomerName(customerName, startDate, endDate, limit);
  return orders.map(transformOrderSummary);
}

function transformOrderSummary(row) {
  return {
    jobNumber: row.jobNumber,
    customerName: row.customerName,
    orderDate: formatDate(row.orderDate),
    totalAmount: formatCurrency(row.totalAmount),
    customerPO: row.customerPO || null,
  };
}

function transformOrderDetail(row) {
  return {
    jobNumber: row.jobNumber,
    orderDate: formatDate(row.orderDate),
    totalAmount: formatCurrency(row.totalAmount),
    customerPO: row.customerPO || null,
    desiredShipDate: formatDate(row.desiredShipDate),
    promisedDate: formatDate(row.promisedDate),
    notes: [row.note1, row.note2].filter(Boolean),
    customer: {
      id: row.customerId,
      name: row.customerName,
      shipping: {
        address1: row.shipAddr1,
        address2: row.shipAddr2,
        city: row.shipCity,
        state: row.shipState,
        zip: row.shipZip,
        country: row.shipCountry,
      },
      billing: {
        name: row.billToName,
        address1: row.billAddr1,
        address2: row.billAddr2,
        city: row.billCity,
        state: row.billState,
        zip: row.billZip,
        country: row.billCountry,
      },
      contact: {
        name: row.contactName,
        phone: row.phoneNumber,
        fax: row.faxNumber,
        email: row.email,
      },
    },
  };
}

function transformLineItem(row) {
  return {
    lineNumber: row.lineNumber,
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    unitPrice: formatCurrency(row.unitPrice),
    lineTotal: formatCurrency(row.lineTotal),
    desiredShipDate: formatDate(row.desiredShipDate),
    promisedShipDate: formatDate(row.promisedShipDate),
    workOrder: row.baseId ? { baseId: row.baseId, lotId: row.lotId } : null,
    details: cleanBinaryText(row.binaryDetails),
  };
}

module.exports = {
  getRecentOrders,
  getOrderByJobNumber,
  getOrderLineItems,
  searchByCustomerName,
};
```

### Step 6.3: Create part service

**File: `server/src/services/part.service.js`**

```javascript
const partQueries = require('../database/queries/part.queries');
const { NotFoundError } = require('../utils/errors');
const { formatCurrency, formatWorkOrderId } = require('../utils/formatters');

async function getPartByNumber(partNumber) {
  const part = await partQueries.getPartByNumber(partNumber);
  if (!part) {
    throw new NotFoundError('Part', partNumber);
  }
  return transformPartDetail(part);
}

async function searchParts(searchPattern, limit) {
  const parts = await partQueries.searchParts(searchPattern, limit);
  return parts.map(transformPartSummary);
}

async function getWhereUsed(partNumber, limit) {
  const usages = await partQueries.getWhereUsed(partNumber, limit);
  return usages.map(row => ({
    workOrderId: formatWorkOrderId(row.workOrderBaseId, row.workOrderLotId, row.workOrderSubId),
    parentPartId: row.parentPartId,
    parentDescription: row.parentDescription,
    workOrderStatus: row.workOrderStatus,
    qtyPer: row.qtyPer,
    fixedQty: row.fixedQty,
  }));
}

async function getPurchaseHistory(partNumber, limit) {
  const history = await partQueries.getPurchaseHistory(partNumber, limit);
  return history.map(row => ({
    purchaseOrderId: row.purchaseOrderId,
    lineNumber: row.lineNumber,
    vendorName: row.vendorName,
    orderQty: row.orderQty,
    unitPrice: formatCurrency(row.unitPrice),
    receivedQty: row.receivedQty,
  }));
}

function transformPartDetail(row) {
  return {
    partId: row.partId,
    description: row.description,
    stockUm: row.stockUm,
    costs: {
      material: formatCurrency(row.materialCost),
      labor: formatCurrency(row.laborCost),
      burden: formatCurrency(row.burdenCost),
      service: formatCurrency(row.serviceCost),
      standard: formatCurrency(row.standardCost),
      last: formatCurrency(row.lastCost),
      average: formatCurrency(row.avgCost),
    },
    quantities: {
      onHand: row.qtyOnHand,
      onOrder: row.qtyOnOrder,
      allocated: row.qtyAllocated,
      available: row.qtyAvailable,
    },
    flags: {
      purchased: Boolean(row.purchased),
      fabricated: Boolean(row.fabricated),
      stocked: Boolean(row.stocked),
    },
    vendorName: row.vendorName || null,
  };
}

function transformPartSummary(row) {
  return {
    partId: row.partId,
    description: row.description,
    stockUm: row.stockUm,
    standardCost: formatCurrency(row.standardCost),
    qtyOnHand: row.qtyOnHand,
    qtyAvailable: row.qtyAvailable,
  };
}

module.exports = {
  getPartByNumber,
  searchParts,
  getWhereUsed,
  getPurchaseHistory,
};
```

### Step 6.4: Create work order service

**File: `server/src/services/workorder.service.js`**

```javascript
const workorderQueries = require('../database/queries/workorder.queries');
const { NotFoundError, ValidationError } = require('../utils/errors');
const { formatDate, formatWorkOrderId, parseWorkOrderId, cleanBinaryText } = require('../utils/formatters');

async function searchWorkOrders(baseIdPattern, limit) {
  const workOrders = await workorderQueries.searchWorkOrders(baseIdPattern, limit);
  return workOrders.map(transformWorkOrderSummary);
}

async function getWorkOrderById(workOrderId) {
  const { baseId, lotId, subId } = parseWorkOrderId(workOrderId);
  const header = await workorderQueries.getWorkOrderHeader(baseId, lotId, subId);
  if (!header) {
    throw new NotFoundError('Work Order', workOrderId);
  }
  return transformWorkOrderDetail(header);
}

async function getOperations(workOrderId) {
  const { baseId, lotId, subId } = parseWorkOrderId(workOrderId);
  const operations = await workorderQueries.getOperations(baseId, lotId, subId);
  return operations.map(transformOperation);
}

async function getRequirements(workOrderId) {
  const { baseId, lotId, subId } = parseWorkOrderId(workOrderId);
  const requirements = await workorderQueries.getRequirements(baseId, lotId, subId);
  return requirements.map(transformRequirement);
}

async function getLaborTickets(workOrderId) {
  const { baseId, lotId, subId } = parseWorkOrderId(workOrderId);
  const tickets = await workorderQueries.getLaborTickets(baseId, lotId, subId);
  return tickets.map(transformLaborTicket);
}

async function getWorkOrderHierarchy(workOrderId) {
  const { baseId, lotId, subId } = parseWorkOrderId(workOrderId);
  const hierarchy = await workorderQueries.getWorkOrderHierarchy(baseId, lotId, subId);
  return hierarchy.map(row => ({
    workOrderId: formatWorkOrderId(row.baseId, row.lotId, row.subId),
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    status: row.status,
    level: row.hierarchyLevel,
    path: row.hierarchyPath,
  }));
}

function transformWorkOrderSummary(row) {
  return {
    workOrderId: formatWorkOrderId(row.baseId, row.lotId, row.subId),
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    status: row.status,
    type: row.type,
    desiredStartDate: formatDate(row.desiredStartDate),
    desiredComplDate: formatDate(row.desiredComplDate),
  };
}

function transformWorkOrderDetail(row) {
  return {
    workOrderId: formatWorkOrderId(row.baseId, row.lotId, row.subId),
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    completedQty: row.completedQty,
    scrappedQty: row.scrappedQty,
    status: row.status,
    type: row.type,
    priority: row.priority,
    desiredStartDate: formatDate(row.desiredStartDate),
    desiredComplDate: formatDate(row.desiredComplDate),
    actualStartDate: formatDate(row.actualStartDate),
    actualComplDate: formatDate(row.actualComplDate),
    custOrderId: row.custOrderId || null,
    custOrderLineNo: row.custOrderLineNo || null,
    notes: cleanBinaryText(row.notes),
    counts: {
      operations: row.operationCount,
      laborTickets: row.laborTicketCount,
    },
  };
}

function transformOperation(row) {
  return {
    sequenceNo: row.sequenceNo,
    resourceId: row.resourceId,
    departmentId: row.departmentId,
    departmentName: row.departmentName,
    setupHrs: row.setupHrs,
    runHrs: row.runHrs,
    runType: row.runType,
    status: row.status,
    actualStartDate: formatDate(row.actualStartDate),
    actualFinishDate: formatDate(row.actualFinishDate),
  };
}

function transformRequirement(row) {
  return {
    pieceNo: row.pieceNo,
    partId: row.partId,
    partDescription: row.partDescription,
    qtyPerPiece: row.qtyPerPiece,
    fixedQty: row.fixedQty,
    scrapPercent: row.scrapPercent,
    operationSeqNo: row.operationSeqNo,
    subordWoSubId: row.subordWoSubId,
    qtyIssued: row.qtyIssued,
    qtyAllocated: row.qtyAllocated,
  };
}

function transformLaborTicket(row) {
  return {
    employeeId: row.employeeId,
    employeeName: row.employeeName,
    laborDate: formatDate(row.laborDate),
    operationSeqNo: row.operationSeqNo,
    setupHrs: row.setupHrs,
    runHrs: row.runHrs,
    laborRate: row.laborRate,
    totalLaborCost: row.totalLaborCost,
    qtyCompleted: row.qtyCompleted,
    qtyScrapped: row.qtyScrapped,
  };
}

module.exports = {
  searchWorkOrders,
  getWorkOrderById,
  getOperations,
  getRequirements,
  getLaborTickets,
  getWorkOrderHierarchy,
};
```

### Step 6.5: Create services index

**File: `server/src/services/index.js`**

```javascript
const orderService = require('./order.service');
const partService = require('./part.service');
const workorderService = require('./workorder.service');

module.exports = {
  orderService,
  partService,
  workorderService,
};
```

---

## Phase 7: Controllers

### Step 7.1: Create order controller

**File: `server/src/controllers/order.controller.js`**

```javascript
const orderService = require('../services/order.service');
const config = require('../config');

async function getRecentOrders(req, res) {
  const limit = Math.min(
    parseInt(req.query.limit) || config.defaultPageSize,
    config.maxPageSize
  );
  const orders = await orderService.getRecentOrders(limit);
  res.json({ success: true, data: orders, count: orders.length });
}

async function getOrderByJobNumber(req, res) {
  const { jobNumber } = req.params;
  const order = await orderService.getOrderByJobNumber(jobNumber);
  res.json({ success: true, data: order });
}

async function getOrderLineItems(req, res) {
  const { jobNumber } = req.params;
  const lines = await orderService.getOrderLineItems(jobNumber);
  res.json({ success: true, data: lines, count: lines.length });
}

async function searchOrders(req, res) {
  const { customer, startDate, endDate, limit } = req.query;
  const maxLimit = Math.min(parseInt(limit) || config.defaultPageSize, config.maxPageSize);

  const orders = await orderService.searchByCustomerName(
    customer,
    startDate ? new Date(startDate) : null,
    endDate ? new Date(endDate) : null,
    maxLimit
  );
  res.json({ success: true, data: orders, count: orders.length });
}

module.exports = {
  getRecentOrders,
  getOrderByJobNumber,
  getOrderLineItems,
  searchOrders,
};
```

### Step 7.2: Create part controller

**File: `server/src/controllers/part.controller.js`**

```javascript
const partService = require('../services/part.service');
const config = require('../config');

async function getPartByNumber(req, res) {
  const { partNumber } = req.params;
  const part = await partService.getPartByNumber(partNumber);
  res.json({ success: true, data: part });
}

async function searchParts(req, res) {
  const { q, limit } = req.query;
  const maxLimit = Math.min(parseInt(limit) || config.defaultPageSize, config.maxPageSize);
  const parts = await partService.searchParts(q, maxLimit);
  res.json({ success: true, data: parts, count: parts.length });
}

async function getWhereUsed(req, res) {
  const { partNumber } = req.params;
  const { limit } = req.query;
  const maxLimit = Math.min(parseInt(limit) || config.defaultPageSize, config.maxPageSize);
  const usages = await partService.getWhereUsed(partNumber, maxLimit);
  res.json({ success: true, data: usages, count: usages.length });
}

async function getPurchaseHistory(req, res) {
  const { partNumber } = req.params;
  const { limit } = req.query;
  const maxLimit = Math.min(parseInt(limit) || config.defaultPageSize, config.maxPageSize);
  const history = await partService.getPurchaseHistory(partNumber, maxLimit);
  res.json({ success: true, data: history, count: history.length });
}

module.exports = {
  getPartByNumber,
  searchParts,
  getWhereUsed,
  getPurchaseHistory,
};
```

### Step 7.3: Create work order controller

**File: `server/src/controllers/workorder.controller.js`**

```javascript
const workorderService = require('../services/workorder.service');
const config = require('../config');

async function searchWorkOrders(req, res) {
  const { baseId, limit } = req.query;
  const maxLimit = Math.min(parseInt(limit) || config.defaultPageSize, config.maxPageSize);
  const workOrders = await workorderService.searchWorkOrders(baseId, maxLimit);
  res.json({ success: true, data: workOrders, count: workOrders.length });
}

async function getWorkOrderById(req, res) {
  const { workOrderId } = req.params;
  const workOrder = await workorderService.getWorkOrderById(workOrderId);
  res.json({ success: true, data: workOrder });
}

async function getOperations(req, res) {
  const { workOrderId } = req.params;
  const operations = await workorderService.getOperations(workOrderId);
  res.json({ success: true, data: operations, count: operations.length });
}

async function getRequirements(req, res) {
  const { workOrderId } = req.params;
  const requirements = await workorderService.getRequirements(workOrderId);
  res.json({ success: true, data: requirements, count: requirements.length });
}

async function getLaborTickets(req, res) {
  const { workOrderId } = req.params;
  const tickets = await workorderService.getLaborTickets(workOrderId);
  res.json({ success: true, data: tickets, count: tickets.length });
}

async function getWorkOrderHierarchy(req, res) {
  const { workOrderId } = req.params;
  const hierarchy = await workorderService.getWorkOrderHierarchy(workOrderId);
  res.json({ success: true, data: hierarchy, count: hierarchy.length });
}

module.exports = {
  searchWorkOrders,
  getWorkOrderById,
  getOperations,
  getRequirements,
  getLaborTickets,
  getWorkOrderHierarchy,
};
```

### Step 7.4: Create controllers index

**File: `server/src/controllers/index.js`**

```javascript
const orderController = require('./order.controller');
const partController = require('./part.controller');
const workorderController = require('./workorder.controller');

module.exports = {
  orderController,
  partController,
  workorderController,
};
```

---

## Phase 8: Routes

### Step 8.1: Create order routes

**File: `server/src/routes/order.routes.js`**

```javascript
const express = require('express');
const { query, param } = require('express-validator');
const orderController = require('../controllers/order.controller');
const { validate } = require('../middleware/validation.middleware');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();

// GET /api/v1/orders - Get recent orders
router.get('/',
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(orderController.getRecentOrders)
);

// GET /api/v1/orders/search - Search orders
router.get('/search',
  query('customer').notEmpty().withMessage('Customer name is required'),
  query('startDate').optional().isISO8601(),
  query('endDate').optional().isISO8601(),
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(orderController.searchOrders)
);

// GET /api/v1/orders/:jobNumber - Get order by job number
router.get('/:jobNumber',
  param('jobNumber').notEmpty(),
  validate,
  asyncHandler(orderController.getOrderByJobNumber)
);

// GET /api/v1/orders/:jobNumber/lines - Get order line items
router.get('/:jobNumber/lines',
  param('jobNumber').notEmpty(),
  validate,
  asyncHandler(orderController.getOrderLineItems)
);

module.exports = router;
```

### Step 8.2: Create part routes

**File: `server/src/routes/part.routes.js`**

```javascript
const express = require('express');
const { query, param } = require('express-validator');
const partController = require('../controllers/part.controller');
const { validate } = require('../middleware/validation.middleware');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();

// GET /api/v1/parts/search - Search parts
router.get('/search',
  query('q').notEmpty().withMessage('Search query is required'),
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(partController.searchParts)
);

// GET /api/v1/parts/:partNumber - Get part by number
router.get('/:partNumber',
  param('partNumber').notEmpty(),
  validate,
  asyncHandler(partController.getPartByNumber)
);

// GET /api/v1/parts/:partNumber/where-used - Get where-used
router.get('/:partNumber/where-used',
  param('partNumber').notEmpty(),
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(partController.getWhereUsed)
);

// GET /api/v1/parts/:partNumber/purchase-history - Get purchase history
router.get('/:partNumber/purchase-history',
  param('partNumber').notEmpty(),
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(partController.getPurchaseHistory)
);

module.exports = router;
```

### Step 8.3: Create work order routes

**File: `server/src/routes/workorder.routes.js`**

```javascript
const express = require('express');
const { query, param } = require('express-validator');
const workorderController = require('../controllers/workorder.controller');
const { validate } = require('../middleware/validation.middleware');
const { asyncHandler } = require('../utils/asyncHandler');

const router = express.Router();

// GET /api/v1/workorders - Search work orders
router.get('/',
  query('baseId').notEmpty().withMessage('Base ID is required'),
  query('limit').optional().isInt({ min: 1, max: 500 }),
  validate,
  asyncHandler(workorderController.searchWorkOrders)
);

// GET /api/v1/workorders/:workOrderId - Get work order by ID
router.get('/:workOrderId',
  param('workOrderId').matches(/^.+-.+-.+$/).withMessage('Invalid work order ID format (expected BASE-LOT-SUB)'),
  validate,
  asyncHandler(workorderController.getWorkOrderById)
);

// GET /api/v1/workorders/:workOrderId/operations - Get operations
router.get('/:workOrderId/operations',
  param('workOrderId').matches(/^.+-.+-.+$/),
  validate,
  asyncHandler(workorderController.getOperations)
);

// GET /api/v1/workorders/:workOrderId/requirements - Get requirements
router.get('/:workOrderId/requirements',
  param('workOrderId').matches(/^.+-.+-.+$/),
  validate,
  asyncHandler(workorderController.getRequirements)
);

// GET /api/v1/workorders/:workOrderId/labor - Get labor tickets
router.get('/:workOrderId/labor',
  param('workOrderId').matches(/^.+-.+-.+$/),
  validate,
  asyncHandler(workorderController.getLaborTickets)
);

// GET /api/v1/workorders/:workOrderId/hierarchy - Get hierarchy
router.get('/:workOrderId/hierarchy',
  param('workOrderId').matches(/^.+-.+-.+$/),
  validate,
  asyncHandler(workorderController.getWorkOrderHierarchy)
);

module.exports = router;
```

### Step 8.4: Create routes index

**File: `server/src/routes/index.js`**

```javascript
const express = require('express');
const orderRoutes = require('./order.routes');
const partRoutes = require('./part.routes');
const workorderRoutes = require('./workorder.routes');

const router = express.Router();

router.use('/orders', orderRoutes);
router.use('/parts', partRoutes);
router.use('/workorders', workorderRoutes);

module.exports = router;
```

---

## Phase 9: Application Entry Points

### Step 9.1: Create Express app

**File: `server/src/app.js`**

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { errorMiddleware, loggingMiddleware } = require('./middleware');
const routes = require('./routes');

const app = express();

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Compression
app.use(compression());

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use(loggingMiddleware);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/v1', routes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
    },
  });
});

// Global error handler
app.use(errorMiddleware);

module.exports = app;
```

### Step 9.2: Create server entry point

**File: `server/src/index.js`**

```javascript
const app = require('./app');
const { connectDatabase, closeDatabase } = require('./database');
const logger = require('./utils/logger');
const config = require('./config');

const PORT = config.port;

async function startServer() {
  try {
    await connectDatabase();
    logger.info('Database connection pool initialized');

    app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${config.nodeEnv}`);
      logger.info(`Health check: http://localhost:${PORT}/health`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  await closeDatabase();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');
  await closeDatabase();
  process.exit(0);
});

startServer();
```

---

## Phase 10: Test the Server

### Step 10.1: Start the server

```bash
cd server
npm run dev
```

### Step 10.2: Test endpoints

```bash
# Health check
curl http://localhost:3001/health

# Get recent orders
curl http://localhost:3001/api/v1/orders

# Get specific order
curl http://localhost:3001/api/v1/orders/JOB123

# Search parts
curl "http://localhost:3001/api/v1/parts/search?q=WIDGET"

# Get work order
curl http://localhost:3001/api/v1/workorders/BASE-LOT-SUB
```

---

## Quick Reference: File Creation Order

| Order | File | Dependencies |
|-------|------|-------------|
| 1 | `.env` | None |
| 2 | `src/config/index.js` | dotenv |
| 3 | `src/utils/logger.js` | config |
| 4 | `src/utils/errors.js` | None |
| 5 | `src/utils/formatters.js` | None |
| 6 | `src/utils/asyncHandler.js` | None |
| 7 | `src/utils/index.js` | utils/* |
| 8 | `src/database/connection.js` | config, logger |
| 9 | `src/database/queries/order.queries.js` | connection |
| 10 | `src/database/queries/part.queries.js` | connection |
| 11 | `src/database/queries/workorder.queries.js` | connection |
| 12 | `src/database/index.js` | database/* |
| 13 | `src/middleware/error.middleware.js` | logger, errors |
| 14 | `src/middleware/logging.middleware.js` | logger |
| 15 | `src/middleware/validation.middleware.js` | errors |
| 16 | `src/middleware/index.js` | middleware/* |
| 17 | `src/services/order.service.js` | queries, errors, formatters |
| 18 | `src/services/part.service.js` | queries, errors, formatters |
| 19 | `src/services/workorder.service.js` | queries, errors, formatters |
| 20 | `src/services/index.js` | services/* |
| 21 | `src/controllers/order.controller.js` | services, config |
| 22 | `src/controllers/part.controller.js` | services, config |
| 23 | `src/controllers/workorder.controller.js` | services, config |
| 24 | `src/controllers/index.js` | controllers/* |
| 25 | `src/routes/order.routes.js` | controllers, middleware, asyncHandler |
| 26 | `src/routes/part.routes.js` | controllers, middleware, asyncHandler |
| 27 | `src/routes/workorder.routes.js` | controllers, middleware, asyncHandler |
| 28 | `src/routes/index.js` | routes/* |
| 29 | `src/app.js` | middleware, routes |
| 30 | `src/index.js` | app, database, logger, config |

---

## Final Directory Structure

```
server/
├── .env
├── .env.example
├── package.json
└── src/
    ├── index.js
    ├── app.js
    ├── config/
    │   └── index.js
    ├── database/
    │   ├── index.js
    │   ├── connection.js
    │   └── queries/
    │       ├── order.queries.js
    │       ├── part.queries.js
    │       └── workorder.queries.js
    ├── utils/
    │   ├── index.js
    │   ├── logger.js
    │   ├── errors.js
    │   ├── formatters.js
    │   └── asyncHandler.js
    ├── middleware/
    │   ├── index.js
    │   ├── error.middleware.js
    │   ├── logging.middleware.js
    │   └── validation.middleware.js
    ├── services/
    │   ├── index.js
    │   ├── order.service.js
    │   ├── part.service.js
    │   └── workorder.service.js
    ├── controllers/
    │   ├── index.js
    │   ├── order.controller.js
    │   ├── part.controller.js
    │   └── workorder.controller.js
    └── routes/
        ├── index.js
        ├── order.routes.js
        ├── part.routes.js
        └── workorder.routes.js
```
