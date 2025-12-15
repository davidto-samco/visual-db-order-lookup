# 05 - Service Layer

## Overview

The service layer contains the business logic and orchestrates database queries. Each service corresponds to a module in the original PyQt6 application.

## File Structure

```
src/services/
├── index.js              # Export all services
├── order.service.js      # Sales module business logic
├── part.service.js       # Inventory module business logic
├── workorder.service.js  # Engineering module business logic
└── bom.service.js        # BOM hierarchy operations
```

---

## Order Service (src/services/order.service.js)

Maps to: `visual_order_lookup/services/order_service.py`

```javascript
const orderQueries = require('../database/queries/order.queries');
const {
  toOrderSummary,
  toOrderHeader,
  toOrderLineItem,
} = require('../models/transformers');
const { OrderNotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get recent orders
 * Maps to: OrderService.load_recent_orders()
 * @param {number} limit - Maximum orders to return
 * @returns {Promise<Array>}
 */
async function getRecentOrders(limit = 100) {
  logger.debug(`Fetching ${limit} recent orders`);

  const rows = await orderQueries.getRecentOrders(limit);
  return rows.map(toOrderSummary);
}

/**
 * Filter orders by date range
 * Maps to: OrderService.filter_by_date_range()
 * @param {Object} filter - Date range filter
 * @param {Date} [filter.startDate]
 * @param {Date} [filter.endDate]
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function filterByDateRange(filter, limit = 100) {
  logger.debug('Filtering orders by date range', { filter, limit });

  const rows = await orderQueries.getOrdersByDateRange(
    filter.startDate,
    filter.endDate,
    limit
  );
  return rows.map(toOrderSummary);
}

/**
 * Get order by job number
 * Maps to: OrderService.get_order_by_job_number()
 * @param {string} jobNumber - The job number
 * @returns {Promise<Object>}
 */
async function getOrderByJobNumber(jobNumber) {
  // Validation
  if (!jobNumber || !jobNumber.trim()) {
    throw new ValidationError('Job number cannot be empty');
  }

  const trimmedJobNumber = jobNumber.trim();
  logger.debug(`Fetching order: ${trimmedJobNumber}`);

  const row = await orderQueries.getOrderByJobNumber(trimmedJobNumber);

  if (!row) {
    throw new OrderNotFoundError(trimmedJobNumber);
  }

  const order = toOrderHeader(row);

  // Fetch line items
  const lineItemRows = await orderQueries.getOrderLineItems(trimmedJobNumber);
  order.lineItems = lineItemRows.map(toOrderLineItem);

  return order;
}

/**
 * Search orders by customer name
 * Maps to: OrderService.search_by_customer_name()
 * @param {string} customerName - Customer name pattern
 * @param {Object} [filter] - Optional date filter
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function searchByCustomerName(customerName, filter = {}, limit = 100) {
  // Validation
  if (!customerName || !customerName.trim()) {
    throw new ValidationError('Customer name cannot be empty');
  }

  const trimmedName = customerName.trim();
  logger.debug(`Searching orders for customer: ${trimmedName}`, { filter, limit });

  const rows = await orderQueries.searchByCustomerName(
    trimmedName,
    filter.startDate,
    filter.endDate,
    limit
  );

  return rows.map(toOrderSummary);
}

/**
 * Get order line items only
 * @param {string} jobNumber - The job number
 * @returns {Promise<Array>}
 */
async function getOrderLineItems(jobNumber) {
  if (!jobNumber || !jobNumber.trim()) {
    throw new ValidationError('Job number cannot be empty');
  }

  const trimmedJobNumber = jobNumber.trim();
  logger.debug(`Fetching line items for order: ${trimmedJobNumber}`);

  const rows = await orderQueries.getOrderLineItems(trimmedJobNumber);
  return rows.map(toOrderLineItem);
}

module.exports = {
  getRecentOrders,
  filterByDateRange,
  getOrderByJobNumber,
  searchByCustomerName,
  getOrderLineItems,
};
```

---

## Part Service (src/services/part.service.js)

Maps to: `visual_order_lookup/services/part_service.py`

```javascript
const partQueries = require('../database/queries/part.queries');
const {
  toPart,
  toWhereUsed,
  toPurchaseHistory,
} = require('../models/transformers');
const { PartNotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get part by part number
 * Maps to: PartService.search_by_part_number()
 * @param {string} partNumber - The part ID
 * @returns {Promise<Object>}
 */
async function getPartByNumber(partNumber) {
  // Validation
  if (!partNumber || !partNumber.trim()) {
    throw new ValidationError('Part number cannot be empty');
  }

  const trimmedPartNumber = partNumber.trim().toUpperCase();
  logger.debug(`Fetching part: ${trimmedPartNumber}`);

  const row = await partQueries.getPartByNumber(trimmedPartNumber);

  if (!row) {
    throw new PartNotFoundError(trimmedPartNumber);
  }

  return toPart(row);
}

/**
 * Search parts by partial number
 * @param {string} searchPattern - Search pattern
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function searchParts(searchPattern, limit = 100) {
  if (!searchPattern || !searchPattern.trim()) {
    throw new ValidationError('Search pattern cannot be empty');
  }

  const trimmedPattern = searchPattern.trim().toUpperCase();
  logger.debug(`Searching parts with pattern: ${trimmedPattern}`);

  const rows = await partQueries.searchParts(trimmedPattern, limit);

  return rows.map(row => ({
    partId: row.partId,
    description: row.description,
    stockUm: row.stockUm,
    standardCost: row.standardCost,
    qtyOnHand: row.qtyOnHand,
    qtyAvailable: row.qtyAvailable,
  }));
}

/**
 * Get where-used information for a part
 * Maps to: PartService.get_where_used()
 * @param {string} partNumber - The part ID
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function getWhereUsed(partNumber, limit = 100) {
  if (!partNumber || !partNumber.trim()) {
    throw new ValidationError('Part number cannot be empty');
  }

  const trimmedPartNumber = partNumber.trim().toUpperCase();
  logger.debug(`Fetching where-used for part: ${trimmedPartNumber}`);

  const rows = await partQueries.getWhereUsed(trimmedPartNumber, limit);
  return rows.map(toWhereUsed);
}

/**
 * Get purchase history for a part
 * Maps to: PartService.get_purchase_history()
 * @param {string} partNumber - The part ID
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function getPurchaseHistory(partNumber, limit = 100) {
  if (!partNumber || !partNumber.trim()) {
    throw new ValidationError('Part number cannot be empty');
  }

  const trimmedPartNumber = partNumber.trim().toUpperCase();
  logger.debug(`Fetching purchase history for part: ${trimmedPartNumber}`);

  const rows = await partQueries.getPurchaseHistory(trimmedPartNumber, limit);
  return rows.map(toPurchaseHistory);
}

module.exports = {
  getPartByNumber,
  searchParts,
  getWhereUsed,
  getPurchaseHistory,
};
```

---

## Work Order Service (src/services/workorder.service.js)

Maps to: `visual_order_lookup/services/work_order_service.py`

```javascript
const workorderQueries = require('../database/queries/workorder.queries');
const {
  toWorkOrder,
  toWorkOrderHeader,
  toOperation,
  toRequirement,
  toLaborTicket,
  toInventoryTransaction,
  toWIPBalance,
} = require('../models/transformers');
const { WorkOrderNotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Search work orders by base ID pattern
 * Maps to: WorkOrderService.search_work_orders()
 * @param {string} baseIdPattern - Base ID search pattern
 * @param {number} limit - Maximum results
 * @returns {Promise<Array>}
 */
async function searchWorkOrders(baseIdPattern, limit = 100) {
  if (!baseIdPattern || !baseIdPattern.trim()) {
    throw new ValidationError('Base ID pattern cannot be empty');
  }

  const trimmedPattern = baseIdPattern.trim().toUpperCase();
  logger.debug(`Searching work orders with pattern: ${trimmedPattern}`);

  const rows = await workorderQueries.searchWorkOrders(trimmedPattern, limit);
  return rows.map(toWorkOrder);
}

/**
 * Get work order header with counts
 * Maps to: WorkOrderService.get_work_order_header()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Object>}
 */
async function getWorkOrderHeader(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching work order: ${baseId}/${lotId}/${subId}`);

  const row = await workorderQueries.getWorkOrderHeader(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  if (!row) {
    throw new WorkOrderNotFoundError(baseId, lotId, subId);
  }

  return toWorkOrderHeader(row);
}

/**
 * Get operations for a work order (lazy load)
 * Maps to: WorkOrderService.get_operations()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Array>}
 */
async function getOperations(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching operations for: ${baseId}/${lotId}/${subId}`);

  const rows = await workorderQueries.getOperations(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  return rows.map(toOperation);
}

/**
 * Get requirements for a work order or operation (lazy load)
 * Maps to: WorkOrderService.get_requirements()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @param {number} [operationSeqNo] - Optional operation sequence filter
 * @returns {Promise<Array>}
 */
async function getRequirements(baseId, lotId, subId, operationSeqNo) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching requirements for: ${baseId}/${lotId}/${subId}`, {
    operationSeqNo,
  });

  const rows = await workorderQueries.getRequirements(
    baseId.trim(),
    lotId.trim(),
    subId.trim(),
    operationSeqNo
  );

  return rows.map(row => toRequirement(row, baseId.trim(), lotId.trim()));
}

/**
 * Get labor tickets for a work order (lazy load)
 * Maps to: WorkOrderService.get_labor_tickets()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Array>}
 */
async function getLaborTickets(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching labor tickets for: ${baseId}/${lotId}/${subId}`);

  const rows = await workorderQueries.getLaborTickets(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  return rows.map(toLaborTicket);
}

/**
 * Get inventory transactions for a work order (lazy load)
 * Maps to: WorkOrderService.get_inventory_transactions()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Array>}
 */
async function getInventoryTransactions(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching inventory transactions for: ${baseId}/${lotId}/${subId}`);

  const rows = await workorderQueries.getInventoryTransactions(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  return rows.map(toInventoryTransaction);
}

/**
 * Get WIP balance for a work order
 * Maps to: WorkOrderService.get_wip_balance()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Object|null>}
 */
async function getWIPBalance(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching WIP balance for: ${baseId}/${lotId}/${subId}`);

  const row = await workorderQueries.getWIPBalance(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  return row ? toWIPBalance(row) : null;
}

/**
 * Get work order hierarchy (recursive)
 * Maps to: WorkOrderService.get_work_order_hierarchy()
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @param {string} subId - Work order sub ID
 * @returns {Promise<Array>}
 */
async function getWorkOrderHierarchy(baseId, lotId, subId) {
  validateWorkOrderId(baseId, lotId, subId);

  logger.debug(`Fetching hierarchy for: ${baseId}/${lotId}/${subId}`);

  const rows = await workorderQueries.getWorkOrderHierarchy(
    baseId.trim(),
    lotId.trim(),
    subId.trim()
  );

  return rows.map(toWorkOrder);
}

/**
 * Validate work order ID components
 * @param {string} baseId
 * @param {string} lotId
 * @param {string} subId
 */
function validateWorkOrderId(baseId, lotId, subId) {
  if (!baseId || !baseId.trim()) {
    throw new ValidationError('Base ID cannot be empty');
  }
  if (!lotId || !lotId.trim()) {
    throw new ValidationError('Lot ID cannot be empty');
  }
  if (subId === undefined || subId === null || subId.toString().trim() === '') {
    throw new ValidationError('Sub ID cannot be empty');
  }
}

module.exports = {
  searchWorkOrders,
  getWorkOrderHeader,
  getOperations,
  getRequirements,
  getLaborTickets,
  getInventoryTransactions,
  getWIPBalance,
  getWorkOrderHierarchy,
};
```

---

## Service Index (src/services/index.js)

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

## Python to JavaScript Mapping Summary

| Python Service Method | JavaScript Function |
|-----------------------|---------------------|
| `OrderService.load_recent_orders()` | `orderService.getRecentOrders()` |
| `OrderService.filter_by_date_range()` | `orderService.filterByDateRange()` |
| `OrderService.get_order_by_job_number()` | `orderService.getOrderByJobNumber()` |
| `OrderService.search_by_customer_name()` | `orderService.searchByCustomerName()` |
| `PartService.search_by_part_number()` | `partService.getPartByNumber()` |
| `PartService.get_where_used()` | `partService.getWhereUsed()` |
| `PartService.get_purchase_history()` | `partService.getPurchaseHistory()` |
| `WorkOrderService.search_work_orders()` | `workorderService.searchWorkOrders()` |
| `WorkOrderService.get_work_order_header()` | `workorderService.getWorkOrderHeader()` |
| `WorkOrderService.get_operations()` | `workorderService.getOperations()` |
| `WorkOrderService.get_requirements()` | `workorderService.getRequirements()` |
| `WorkOrderService.get_labor_tickets()` | `workorderService.getLaborTickets()` |
| `WorkOrderService.get_inventory_transactions()` | `workorderService.getInventoryTransactions()` |
| `WorkOrderService.get_wip_balance()` | `workorderService.getWIPBalance()` |
| `WorkOrderService.get_work_order_hierarchy()` | `workorderService.getWorkOrderHierarchy()` |

---

## Key Differences from Python Implementation

### 1. Async/Await vs Threading
**Python (PyQt6):**
```python
class DatabaseWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = self.service.operation()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

**JavaScript (Express):**
```javascript
// No manual threading needed - Express handles async naturally
async function getRecentOrders(limit) {
  const rows = await orderQueries.getRecentOrders(limit);
  return rows.map(toOrderSummary);
}
```

### 2. Error Handling
**Python:**
```python
except pyodbc.Error as e:
    logger.error(f"Database error: {e}")
    raise Exception(f"Failed to search: {str(e)}")
```

**JavaScript:**
```javascript
// Errors propagate automatically through async/await
// Global error middleware handles translation to HTTP responses
throw new OrderNotFoundError(jobNumber);
```

### 3. Class-based vs Function-based
**Python:**
```python
class OrderService:
    def __init__(self, connection):
        self.connection = connection

    def get_order_by_job_number(self, job_number):
        # ...
```

**JavaScript:**
```javascript
// Simpler function-based approach
async function getOrderByJobNumber(jobNumber) {
  // Connection pool handled by database layer
}

module.exports = { getOrderByJobNumber };
```
