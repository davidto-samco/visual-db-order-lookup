# 04 - Data Models

## Overview

This document defines the JavaScript data structures and JSDoc type definitions that mirror the Python DTOs from the existing application. These models serve as the contract between database queries and API responses.

## File Structure

```
src/models/
├── index.js              # Export all models
├── constants.js          # Status codes and lookup tables
└── transformers.js       # Row to response object transformers
```

---

## Constants (src/models/constants.js)

```javascript
/**
 * Work order status codes
 */
const WORK_ORDER_STATUS = {
  'F': 'Firm Planned',
  'R': 'Released',
  'S': 'Started',
  'C': 'Complete',
  'X': 'Cancelled',
  'H': 'Hold',
};

/**
 * Work order type codes
 */
const WORK_ORDER_TYPE = {
  'M': 'Make',
  'B': 'Buy',
  'S': 'Stock',
  'R': 'Rework',
};

/**
 * Operation status codes
 */
const OPERATION_STATUS = {
  'P': 'Pending',
  'R': 'Ready',
  'S': 'Started',
  'C': 'Complete',
};

/**
 * Inventory transaction type codes
 */
const INVENTORY_TRANS_TYPE = {
  'I': 'Issue',
  'R': 'Return',
  'S': 'Scrap',
  'A': 'Adjust',
  'T': 'Transfer',
};

/**
 * Run type codes
 */
const RUN_TYPE = {
  'H': 'Hours per piece',
  'P': 'Pieces per hour',
  'L': 'Hours per lot',
};

module.exports = {
  WORK_ORDER_STATUS,
  WORK_ORDER_TYPE,
  OPERATION_STATUS,
  INVENTORY_TRANS_TYPE,
  RUN_TYPE,
};
```

---

## JSDoc Type Definitions

These JSDoc comments provide type information for IDE support and documentation.

### Common Types

```javascript
/**
 * @typedef {Object} ApiResponse
 * @property {boolean} success - Whether the request succeeded
 * @property {*} [data] - Response data
 * @property {ApiError} [error] - Error information
 * @property {ResponseMeta} [meta] - Response metadata
 */

/**
 * @typedef {Object} ApiError
 * @property {string} code - Error code
 * @property {string} message - Error message
 * @property {Object} [details] - Additional error details
 */

/**
 * @typedef {Object} ResponseMeta
 * @property {string} timestamp - ISO timestamp
 * @property {number} [count] - Number of results
 * @property {Object} [filters] - Applied filters
 */

/**
 * @typedef {Object} Address
 * @property {string} [address1]
 * @property {string} [address2]
 * @property {string} [city]
 * @property {string} [state]
 * @property {string} [zip]
 * @property {string} [country]
 */
```

### Order Types

```javascript
/**
 * @typedef {Object} OrderSummary
 * @property {string} jobNumber
 * @property {string} customerName
 * @property {Date} orderDate
 * @property {number} totalAmount
 * @property {string} [customerPO]
 * @property {Object} [formatted] - Formatted display values
 * @property {string} [formatted.orderDate]
 * @property {string} [formatted.totalAmount]
 */

/**
 * @typedef {Object} CustomerContact
 * @property {string} [name]
 * @property {string} [phone]
 * @property {string} [fax]
 * @property {string} [email]
 */

/**
 * @typedef {Object} Customer
 * @property {string} id
 * @property {string} name
 * @property {Address} shipping
 * @property {Address} billing
 * @property {CustomerContact} contact
 */

/**
 * @typedef {Object} OrderLineItem
 * @property {number} lineNumber
 * @property {string} partId
 * @property {string} [partDescription]
 * @property {number} orderQty
 * @property {number} unitPrice
 * @property {number} lineTotal
 * @property {Date} [desiredShipDate]
 * @property {Date} [promisedShipDate]
 * @property {string} [baseId]
 * @property {string} [lotId]
 * @property {string} [binaryDetails]
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} OrderHeader
 * @property {string} jobNumber
 * @property {Date} orderDate
 * @property {number} totalAmount
 * @property {string} [customerPO]
 * @property {Date} [desiredShipDate]
 * @property {Date} [promisedDate]
 * @property {string[]} [notes]
 * @property {Customer} customer
 * @property {OrderLineItem[]} [lineItems]
 * @property {Object} [formatted]
 */
```

### Part Types

```javascript
/**
 * @typedef {Object} PartCosts
 * @property {number} material
 * @property {number} labor
 * @property {number} burden
 * @property {number} service
 * @property {number} standard
 * @property {number} last
 * @property {number} average
 */

/**
 * @typedef {Object} PartQuantities
 * @property {number} onHand
 * @property {number} onOrder
 * @property {number} allocated
 * @property {number} available
 */

/**
 * @typedef {Object} PartFlags
 * @property {boolean} purchased
 * @property {boolean} fabricated
 * @property {boolean} stocked
 */

/**
 * @typedef {Object} Part
 * @property {string} partId
 * @property {string} description
 * @property {string} stockUm
 * @property {PartCosts} costs
 * @property {PartQuantities} quantities
 * @property {PartFlags} flags
 * @property {string} [vendorName]
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} WorkOrderId
 * @property {string} baseId
 * @property {string} lotId
 * @property {string} subId
 */

/**
 * @typedef {Object} WhereUsed
 * @property {WorkOrderId} workOrderId
 * @property {string} parentPartId
 * @property {string} parentDescription
 * @property {string} workOrderStatus
 * @property {number} qtyPer
 * @property {number} fixedQty
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} PurchaseHistory
 * @property {string} purchaseOrderId
 * @property {number} lineNumber
 * @property {string} vendorName
 * @property {number} orderQty
 * @property {number} unitPrice
 * @property {Date} [desiredReceiveDate]
 * @property {number} receivedQty
 * @property {Date} [lastReceiveDate]
 * @property {Object} [formatted]
 */
```

### Work Order Types

```javascript
/**
 * @typedef {Object} WorkOrderDates
 * @property {Date} [desiredStart]
 * @property {Date} [desiredCompl]
 * @property {Date} [actualStart]
 * @property {Date} [actualCompl]
 */

/**
 * @typedef {Object} WorkOrderQuantities
 * @property {number} ordered
 * @property {number} completed
 * @property {number} scrapped
 */

/**
 * @typedef {Object} WorkOrder
 * @property {WorkOrderId} id
 * @property {string} partId
 * @property {string} partDescription
 * @property {number} orderQty
 * @property {string} status
 * @property {string} type
 * @property {WorkOrderDates} dates
 * @property {number} [hierarchyLevel]
 * @property {string} [hierarchyPath]
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} WorkOrderCounts
 * @property {number} operations
 * @property {number} laborTickets
 * @property {number} inventoryTrans
 */

/**
 * @typedef {Object} WorkOrderHeader
 * @property {WorkOrderId} id
 * @property {string} partId
 * @property {string} partDescription
 * @property {WorkOrderQuantities} quantities
 * @property {string} status
 * @property {string} type
 * @property {number} [priority]
 * @property {WorkOrderDates} dates
 * @property {Object} [customerOrder]
 * @property {string} [notes]
 * @property {WorkOrderCounts} counts
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} Operation
 * @property {number} sequenceNo
 * @property {string} [resourceId]
 * @property {string} departmentId
 * @property {string} [departmentName]
 * @property {number} setupHrs
 * @property {number} runHrs
 * @property {string} runType
 * @property {string} status
 * @property {Object} dates
 * @property {number} requirementCount
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} Requirement
 * @property {number} pieceNo
 * @property {string} partId
 * @property {string} partDescription
 * @property {number} qtyPerPiece
 * @property {number} fixedQty
 * @property {number} scrapPercent
 * @property {number} operationSeqNo
 * @property {string} [subordWoSubId]
 * @property {Object} quantities
 * @property {string} [notes]
 * @property {boolean} isSubWorkOrder
 * @property {WorkOrderId} [subWorkOrder]
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} LaborTicket
 * @property {string} employeeId
 * @property {string} [employeeName]
 * @property {Date} laborDate
 * @property {number} operationSeqNo
 * @property {Object} hours
 * @property {number} laborRate
 * @property {Object} costs
 * @property {Object} quantities
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} InventoryTransaction
 * @property {string} partId
 * @property {string} partDescription
 * @property {string} transType
 * @property {number} quantity
 * @property {Date} transDate
 * @property {string} [locationId]
 * @property {Object} costs
 * @property {Object} [formatted]
 */

/**
 * @typedef {Object} WIPBalance
 * @property {Object} costs
 * @property {number} costs.material
 * @property {number} costs.labor
 * @property {number} costs.burden
 * @property {number} costs.service
 * @property {number} costs.total
 * @property {Object} [formatted]
 */
```

---

## Transformers (src/models/transformers.js)

```javascript
const { formatDate, formatCurrency, formatNumber } = require('../utils/formatters');
const {
  WORK_ORDER_STATUS,
  WORK_ORDER_TYPE,
  OPERATION_STATUS,
  INVENTORY_TRANS_TYPE,
  RUN_TYPE,
} = require('./constants');

/**
 * Transform database row to OrderSummary
 * @param {Object} row - Database row
 * @returns {OrderSummary}
 */
function toOrderSummary(row) {
  return {
    jobNumber: row.jobNumber,
    customerName: row.customerName,
    orderDate: new Date(row.orderDate),
    totalAmount: row.totalAmount,
    customerPO: row.customerPO || undefined,
    formatted: {
      orderDate: formatDate(row.orderDate),
      totalAmount: formatCurrency(row.totalAmount),
    },
  };
}

/**
 * Transform database row to OrderHeader
 * @param {Object} row - Database row
 * @returns {OrderHeader}
 */
function toOrderHeader(row) {
  const customer = {
    id: row.customerId,
    name: row.customerName,
    shipping: {
      address1: row.shipAddr1 || undefined,
      address2: row.shipAddr2 || undefined,
      city: row.shipCity || undefined,
      state: row.shipState || undefined,
      zip: row.shipZip || undefined,
      country: row.shipCountry || undefined,
    },
    billing: {
      name: row.billToName || undefined,
      address1: row.billAddr1 || undefined,
      address2: row.billAddr2 || undefined,
      city: row.billCity || undefined,
      state: row.billState || undefined,
      zip: row.billZip || undefined,
      country: row.billCountry || undefined,
    },
    contact: {
      name: row.contactName || undefined,
      phone: row.phoneNumber || undefined,
      fax: row.faxNumber || undefined,
      email: row.email || undefined,
    },
  };

  const notes = [];
  if (row.note1) notes.push(row.note1);
  if (row.note2) notes.push(row.note2);

  return {
    jobNumber: row.jobNumber,
    orderDate: new Date(row.orderDate),
    totalAmount: row.totalAmount,
    customerPO: row.customerPO || undefined,
    desiredShipDate: row.desiredShipDate ? new Date(row.desiredShipDate) : undefined,
    promisedDate: row.promisedDate ? new Date(row.promisedDate) : undefined,
    notes: notes.length > 0 ? notes : undefined,
    customer,
    formatted: {
      orderDate: formatDate(row.orderDate),
      totalAmount: formatCurrency(row.totalAmount),
      desiredShipDate: row.desiredShipDate ? formatDate(row.desiredShipDate) : undefined,
      promisedDate: row.promisedDate ? formatDate(row.promisedDate) : undefined,
    },
  };
}

/**
 * Transform database row to OrderLineItem
 * @param {Object} row - Database row
 * @returns {OrderLineItem}
 */
function toOrderLineItem(row) {
  return {
    lineNumber: row.lineNumber,
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    unitPrice: row.unitPrice,
    lineTotal: row.lineTotal,
    desiredShipDate: row.desiredShipDate ? new Date(row.desiredShipDate) : undefined,
    promisedShipDate: row.promisedShipDate ? new Date(row.promisedShipDate) : undefined,
    baseId: row.baseId || undefined,
    lotId: row.lotId || undefined,
    binaryDetails: row.binaryDetails || undefined,
    formatted: {
      unitPrice: formatCurrency(row.unitPrice),
      lineTotal: formatCurrency(row.lineTotal),
      desiredShipDate: row.desiredShipDate ? formatDate(row.desiredShipDate) : undefined,
    },
  };
}

/**
 * Transform database row to Part
 * @param {Object} row - Database row
 * @returns {Part}
 */
function toPart(row) {
  return {
    partId: row.partId,
    description: row.description,
    stockUm: row.stockUm,
    costs: {
      material: row.materialCost,
      labor: row.laborCost,
      burden: row.burdenCost,
      service: row.serviceCost,
      standard: row.standardCost,
      last: row.lastCost,
      average: row.avgCost,
    },
    quantities: {
      onHand: row.qtyOnHand,
      onOrder: row.qtyOnOrder,
      allocated: row.qtyAllocated,
      available: row.qtyAvailable,
    },
    flags: {
      purchased: row.purchased === 'Y',
      fabricated: row.fabricated === 'Y',
      stocked: row.stocked === 'Y',
    },
    vendorName: row.vendorName || undefined,
    formatted: {
      standardCost: formatCurrency(row.standardCost),
      qtyAvailable: `${formatNumber(row.qtyAvailable)} ${row.stockUm}`,
    },
  };
}

/**
 * Transform database row to WhereUsed
 * @param {Object} row - Database row
 * @returns {WhereUsed}
 */
function toWhereUsed(row) {
  return {
    workOrderId: {
      baseId: row.workOrderBaseId,
      lotId: row.workOrderLotId,
      subId: row.workOrderSubId,
    },
    parentPartId: row.parentPartId,
    parentDescription: row.parentDescription,
    workOrderStatus: row.workOrderStatus,
    qtyPer: row.qtyPer,
    fixedQty: row.fixedQty,
    formatted: {
      workOrderId: formatWorkOrderId(row.workOrderBaseId, row.workOrderSubId, row.workOrderLotId),
      status: WORK_ORDER_STATUS[row.workOrderStatus] || row.workOrderStatus,
    },
  };
}

/**
 * Transform database row to PurchaseHistory
 * @param {Object} row - Database row
 * @returns {PurchaseHistory}
 */
function toPurchaseHistory(row) {
  return {
    purchaseOrderId: row.purchaseOrderId,
    lineNumber: row.lineNumber,
    vendorName: row.vendorName,
    orderQty: row.orderQty,
    unitPrice: row.unitPrice,
    desiredReceiveDate: row.desiredReceiveDate ? new Date(row.desiredReceiveDate) : undefined,
    receivedQty: row.receivedQty,
    lastReceiveDate: row.lastReceiveDate ? new Date(row.lastReceiveDate) : undefined,
    formatted: {
      unitPrice: formatCurrency(row.unitPrice),
      desiredReceiveDate: row.desiredReceiveDate ? formatDate(row.desiredReceiveDate) : undefined,
    },
  };
}

/**
 * Transform database row to WorkOrder
 * @param {Object} row - Database row
 * @returns {WorkOrder}
 */
function toWorkOrder(row) {
  return {
    id: {
      baseId: row.baseId,
      lotId: row.lotId,
      subId: row.subId,
    },
    partId: row.partId,
    partDescription: row.partDescription,
    orderQty: row.orderQty,
    status: row.status,
    type: row.type,
    dates: {
      desiredStart: row.desiredStartDate ? new Date(row.desiredStartDate) : undefined,
      desiredCompl: row.desiredComplDate ? new Date(row.desiredComplDate) : undefined,
      actualStart: row.actualStartDate ? new Date(row.actualStartDate) : undefined,
      actualCompl: row.actualComplDate ? new Date(row.actualComplDate) : undefined,
    },
    hierarchyLevel: row.hierarchyLevel,
    hierarchyPath: row.hierarchyPath,
    formatted: {
      id: formatWorkOrderId(row.baseId, row.subId, row.lotId),
      status: WORK_ORDER_STATUS[row.status] || row.status,
      type: WORK_ORDER_TYPE[row.type] || row.type,
    },
  };
}

/**
 * Transform database row to WorkOrderHeader
 * @param {Object} row - Database row
 * @returns {WorkOrderHeader}
 */
function toWorkOrderHeader(row) {
  const base = toWorkOrder(row);
  return {
    ...base,
    quantities: {
      ordered: row.orderQty,
      completed: row.completedQty || 0,
      scrapped: row.scrappedQty || 0,
    },
    priority: row.priority,
    customerOrder: row.custOrderId
      ? { orderId: row.custOrderId, lineNo: row.custOrderLineNo }
      : undefined,
    notes: row.notes || undefined,
    counts: {
      operations: row.operationCount || 0,
      laborTickets: row.laborTicketCount || 0,
      inventoryTrans: row.inventoryTransCount || 0,
    },
  };
}

/**
 * Transform database row to Operation
 * @param {Object} row - Database row
 * @returns {Operation}
 */
function toOperation(row) {
  return {
    sequenceNo: row.sequenceNo,
    resourceId: row.resourceId || undefined,
    departmentId: row.departmentId,
    departmentName: row.departmentName || undefined,
    setupHrs: row.setupHrs,
    runHrs: row.runHrs,
    runType: row.runType,
    status: row.status,
    dates: {
      actualStart: row.actualStartDate ? new Date(row.actualStartDate) : undefined,
      actualFinish: row.actualFinishDate ? new Date(row.actualFinishDate) : undefined,
    },
    requirementCount: row.requirementCount,
    formatted: {
      status: OPERATION_STATUS[row.status] || row.status,
      runType: RUN_TYPE[row.runType] || row.runType,
    },
  };
}

/**
 * Transform database row to Requirement
 * @param {Object} row - Database row
 * @param {string} baseId - Work order base ID
 * @param {string} lotId - Work order lot ID
 * @returns {Requirement}
 */
function toRequirement(row, baseId, lotId) {
  const isSubWorkOrder = row.subordWoSubId !== null && row.subordWoSubId !== '';

  return {
    pieceNo: row.pieceNo,
    partId: row.partId,
    partDescription: row.partDescription,
    qtyPerPiece: row.qtyPerPiece,
    fixedQty: row.fixedQty,
    scrapPercent: row.scrapPercent,
    operationSeqNo: row.operationSeqNo,
    subordWoSubId: row.subordWoSubId || undefined,
    quantities: {
      issued: row.qtyIssued,
      allocated: row.qtyAllocated,
    },
    notes: row.notes || undefined,
    isSubWorkOrder,
    subWorkOrder: isSubWorkOrder
      ? { baseId, lotId, subId: row.subordWoSubId }
      : undefined,
    formatted: {
      qtyPer: `${formatNumber(row.qtyPerPiece, 2)} per piece`,
      scrapPercent: row.scrapPercent > 0 ? `${formatNumber(row.scrapPercent, 1)}%` : undefined,
    },
  };
}

/**
 * Transform database row to LaborTicket
 * @param {Object} row - Database row
 * @returns {LaborTicket}
 */
function toLaborTicket(row) {
  return {
    employeeId: row.employeeId,
    employeeName: row.employeeName || undefined,
    laborDate: new Date(row.laborDate),
    operationSeqNo: row.operationSeqNo,
    hours: {
      setup: row.setupHrs,
      run: row.runHrs,
    },
    laborRate: row.laborRate,
    costs: {
      labor: row.totalLaborCost,
      burden: row.burdenCost,
    },
    quantities: {
      completed: row.qtyCompleted,
      scrapped: row.qtyScrapped,
    },
    formatted: {
      laborDate: formatDate(row.laborDate),
      laborCost: formatCurrency(row.totalLaborCost),
      totalHours: `${formatNumber(row.setupHrs + row.runHrs, 1)} hrs`,
    },
  };
}

/**
 * Transform database row to InventoryTransaction
 * @param {Object} row - Database row
 * @returns {InventoryTransaction}
 */
function toInventoryTransaction(row) {
  return {
    partId: row.partId,
    partDescription: row.partDescription,
    transType: row.transType,
    quantity: row.quantity,
    transDate: new Date(row.transDate),
    locationId: row.locationId || undefined,
    costs: {
      unit: row.unitCost,
      total: row.totalCost,
    },
    formatted: {
      transType: INVENTORY_TRANS_TYPE[row.transType] || row.transType,
      transDate: formatDate(row.transDate),
      totalCost: formatCurrency(row.totalCost),
    },
  };
}

/**
 * Transform database row to WIPBalance
 * @param {Object} row - Database row
 * @returns {WIPBalance}
 */
function toWIPBalance(row) {
  return {
    costs: {
      material: row.materialCost,
      labor: row.laborCost,
      burden: row.burdenCost,
      service: row.serviceCost,
      total: row.totalCost,
    },
    formatted: {
      materialCost: formatCurrency(row.materialCost),
      laborCost: formatCurrency(row.laborCost),
      burdenCost: formatCurrency(row.burdenCost),
      totalCost: formatCurrency(row.totalCost),
    },
  };
}

/**
 * Format work order ID as BASE-SUB/LOT
 * @param {string} baseId
 * @param {string} subId
 * @param {string} lotId
 * @returns {string}
 */
function formatWorkOrderId(baseId, subId, lotId) {
  return `${baseId}-${subId}/${lotId}`;
}

module.exports = {
  toOrderSummary,
  toOrderHeader,
  toOrderLineItem,
  toPart,
  toWhereUsed,
  toPurchaseHistory,
  toWorkOrder,
  toWorkOrderHeader,
  toOperation,
  toRequirement,
  toLaborTicket,
  toInventoryTransaction,
  toWIPBalance,
  formatWorkOrderId,
};
```

---

## Formatters (src/utils/formatters.js)

```javascript
/**
 * Format date as MM/DD/YYYY
 * @param {Date|string|null|undefined} date
 * @returns {string}
 */
function formatDate(date) {
  if (!date) return '';
  const d = date instanceof Date ? date : new Date(date);
  if (isNaN(d.getTime())) return '';

  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const year = d.getFullYear();

  return `${month}/${day}/${year}`;
}

/**
 * Format number as currency ($X,XXX.XX)
 * @param {number|null|undefined} value
 * @returns {string}
 */
function formatCurrency(value) {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

/**
 * Format number with thousand separators
 * @param {number|null|undefined} value
 * @param {number} decimals
 * @returns {string}
 */
function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format percentage
 * @param {number|null|undefined} value
 * @returns {string}
 */
function formatPercent(value) {
  if (value === null || value === undefined) return '';
  return `${formatNumber(value, 1)}%`;
}

/**
 * Format hours
 * @param {number|null|undefined} value
 * @returns {string}
 */
function formatHours(value) {
  if (value === null || value === undefined) return '';
  return `${formatNumber(value, 1)} hrs`;
}

module.exports = {
  formatDate,
  formatCurrency,
  formatNumber,
  formatPercent,
  formatHours,
};
```

---

## Index Exports (src/models/index.js)

```javascript
const constants = require('./constants');
const transformers = require('./transformers');

module.exports = {
  ...constants,
  ...transformers,
};
```
