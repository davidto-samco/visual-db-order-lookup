# 04 - Data Models

## Overview

This document defines the TypeScript interfaces and types that mirror the Python DTOs from the existing application. These models serve as the contract between database queries and API responses.

## File Structure

```
src/models/
├── index.ts              # Export all models
├── common.model.ts       # Shared types and utilities
├── order.model.ts        # Order-related interfaces
├── part.model.ts         # Part-related interfaces
└── workorder.model.ts    # Work order interfaces
```

---

## Common Models (src/models/common.model.ts)

```typescript
/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: ResponseMeta;
}

/**
 * Error response structure
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Response metadata
 */
export interface ResponseMeta {
  timestamp: string;
  count?: number;
  filters?: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * Date range filter
 */
export interface DateRangeFilter {
  startDate?: Date;
  endDate?: Date;
}

/**
 * Pagination options
 */
export interface PaginationOptions {
  limit?: number;
  offset?: number;
}

/**
 * Address structure
 */
export interface Address {
  address1?: string;
  address2?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
}

/**
 * Formatted display values
 */
export interface FormattedFields {
  [key: string]: string | undefined;
}
```

---

## Order Models (src/models/order.model.ts)

```typescript
import { Address, FormattedFields } from './common.model';

/**
 * Order summary for list views
 * Maps to: Python OrderSummary dataclass
 */
export interface OrderSummary {
  jobNumber: string;
  customerName: string;
  orderDate: Date;
  totalAmount: number;
  customerPO?: string;
  formatted?: OrderSummaryFormatted;
}

export interface OrderSummaryFormatted extends FormattedFields {
  orderDate: string;      // MM/DD/YYYY
  totalAmount: string;    // $X,XXX.XX
}

/**
 * Customer contact information
 */
export interface CustomerContact {
  name?: string;
  phone?: string;
  fax?: string;
  email?: string;
}

/**
 * Customer with addresses
 * Maps to: Python Customer dataclass
 */
export interface Customer {
  id: string;
  name: string;
  shipping: Address;
  billing: Address & { name?: string };
  contact: CustomerContact;
}

/**
 * Order line item
 * Maps to: Python OrderLineItem dataclass
 */
export interface OrderLineItem {
  lineNumber: number;
  partId: string;
  partDescription?: string;
  orderQty: number;
  unitPrice: number;
  lineTotal: number;
  desiredShipDate?: Date;
  promisedShipDate?: Date;
  baseId?: string;
  lotId?: string;
  binaryDetails?: string;
  formatted?: OrderLineItemFormatted;
}

export interface OrderLineItemFormatted extends FormattedFields {
  unitPrice: string;
  lineTotal: string;
  desiredShipDate?: string;
  promisedShipDate?: string;
}

/**
 * Complete order header with customer and line items
 * Maps to: Python OrderHeader dataclass
 */
export interface OrderHeader {
  jobNumber: string;
  orderDate: Date;
  totalAmount: number;
  customerPO?: string;
  desiredShipDate?: Date;
  promisedDate?: Date;
  notes?: string[];
  customer: Customer;
  lineItems?: OrderLineItem[];
  formatted?: OrderHeaderFormatted;
}

export interface OrderHeaderFormatted extends FormattedFields {
  orderDate: string;
  totalAmount: string;
  desiredShipDate?: string;
  promisedDate?: string;
}

/**
 * Database row type for order query results
 */
export interface OrderRow {
  jobNumber: string;
  orderDate: Date;
  totalAmount: number;
  customerPO: string | null;
  desiredShipDate: Date | null;
  promisedDate: Date | null;
  note1: string | null;
  note2: string | null;
  customerId: string;
  customerName: string;
  shipAddr1: string | null;
  shipAddr2: string | null;
  shipCity: string | null;
  shipState: string | null;
  shipZip: string | null;
  shipCountry: string | null;
  billToName: string | null;
  billAddr1: string | null;
  billAddr2: string | null;
  billCity: string | null;
  billState: string | null;
  billZip: string | null;
  billCountry: string | null;
  contactName: string | null;
  phoneNumber: string | null;
  faxNumber: string | null;
  email: string | null;
}
```

---

## Part Models (src/models/part.model.ts)

```typescript
import { FormattedFields } from './common.model';

/**
 * Part cost breakdown
 */
export interface PartCosts {
  material: number;
  labor: number;
  burden: number;
  service: number;
  standard: number;
  last: number;
  average: number;
}

/**
 * Part quantity levels
 */
export interface PartQuantities {
  onHand: number;
  onOrder: number;
  allocated: number;
  available: number;
}

/**
 * Part flags
 */
export interface PartFlags {
  purchased: boolean;
  fabricated: boolean;
  stocked: boolean;
}

/**
 * Part master data
 * Maps to: Python Part dataclass
 */
export interface Part {
  partId: string;
  description: string;
  stockUm: string;
  costs: PartCosts;
  quantities: PartQuantities;
  flags: PartFlags;
  vendorName?: string;
  formatted?: PartFormatted;
}

export interface PartFormatted extends FormattedFields {
  standardCost: string;
  qtyAvailable: string;
}

/**
 * Simplified part for search results
 */
export interface PartSearchResult {
  partId: string;
  description: string;
  stockUm: string;
  standardCost: number;
  qtyOnHand: number;
  qtyAvailable: number;
}

/**
 * Work order ID composite key
 */
export interface WorkOrderId {
  baseId: string;
  lotId: string;
  subId: string;
}

/**
 * Where-used record showing which work orders use a part
 * Maps to: Python WhereUsed dataclass
 */
export interface WhereUsed {
  workOrderId: WorkOrderId;
  parentPartId: string;
  parentDescription: string;
  workOrderStatus: string;
  qtyPer: number;
  fixedQty: number;
  formatted?: WhereUsedFormatted;
}

export interface WhereUsedFormatted extends FormattedFields {
  workOrderId: string;    // BASE-SUB/LOT format
  status: string;         // Human-readable status
}

/**
 * Purchase history record
 * Maps to: Python PurchaseHistory dataclass
 */
export interface PurchaseHistory {
  purchaseOrderId: string;
  lineNumber: number;
  vendorName: string;
  orderQty: number;
  unitPrice: number;
  desiredReceiveDate?: Date;
  receivedQty: number;
  lastReceiveDate?: Date;
  formatted?: PurchaseHistoryFormatted;
}

export interface PurchaseHistoryFormatted extends FormattedFields {
  unitPrice: string;
  desiredReceiveDate?: string;
  lastReceiveDate?: string;
}

/**
 * Database row type for part query results
 */
export interface PartRow {
  partId: string;
  description: string;
  stockUm: string;
  materialCost: number;
  laborCost: number;
  burdenCost: number;
  serviceCost: number;
  standardCost: number;
  lastCost: number;
  avgCost: number;
  qtyOnHand: number;
  qtyOnOrder: number;
  qtyAllocated: number;
  qtyAvailable: number;
  purchased: string;    // Y/N
  fabricated: string;   // Y/N
  stocked: string;      // Y/N
  vendorName: string | null;
}
```

---

## Work Order Models (src/models/workorder.model.ts)

```typescript
import { FormattedFields } from './common.model';

/**
 * Work order composite key
 */
export interface WorkOrderId {
  baseId: string;
  lotId: string;
  subId: string;
}

/**
 * Work order date fields
 */
export interface WorkOrderDates {
  desiredStart?: Date;
  desiredCompl?: Date;
  actualStart?: Date;
  actualCompl?: Date;
}

/**
 * Work order quantities
 */
export interface WorkOrderQuantities {
  ordered: number;
  completed: number;
  scrapped: number;
}

/**
 * Work order for list views
 * Maps to: Python WorkOrder dataclass
 */
export interface WorkOrder {
  id: WorkOrderId;
  partId: string;
  partDescription: string;
  orderQty: number;
  status: string;
  type: string;
  dates: WorkOrderDates;
  hierarchyLevel?: number;
  hierarchyPath?: string;
  formatted?: WorkOrderFormatted;
}

export interface WorkOrderFormatted extends FormattedFields {
  id: string;           // BASE-SUB/LOT format
  status: string;       // Human-readable status
  type: string;         // Human-readable type
}

/**
 * Aggregate counts for lazy loading indicators
 */
export interface WorkOrderCounts {
  operations: number;
  laborTickets: number;
  inventoryTrans: number;
}

/**
 * Customer order reference
 */
export interface CustomerOrderRef {
  orderId?: string;
  lineNo?: number;
}

/**
 * Work order header with full details
 * Maps to: Python WorkOrder dataclass (extended)
 */
export interface WorkOrderHeader extends WorkOrder {
  quantities: WorkOrderQuantities;
  priority?: number;
  customerOrder?: CustomerOrderRef;
  notes?: string;
  counts: WorkOrderCounts;
}

/**
 * Operation/routing step
 * Maps to: Python Operation dataclass
 */
export interface Operation {
  sequenceNo: number;
  resourceId?: string;
  departmentId: string;
  departmentName?: string;
  setupHrs: number;
  runHrs: number;
  runType: string;
  status: string;
  dates: {
    actualStart?: Date;
    actualFinish?: Date;
  };
  requirementCount: number;
  formatted?: OperationFormatted;
}

export interface OperationFormatted extends FormattedFields {
  status: string;
  runType: string;
}

/**
 * Requirement/BOM item
 * Maps to: Python Requirement dataclass
 */
export interface Requirement {
  pieceNo: number;
  partId: string;
  partDescription: string;
  qtyPerPiece: number;
  fixedQty: number;
  scrapPercent: number;
  operationSeqNo: number;
  subordWoSubId?: string;
  quantities: {
    issued: number;
    allocated: number;
  };
  notes?: string;
  isSubWorkOrder: boolean;
  subWorkOrder?: WorkOrderId;
  formatted?: RequirementFormatted;
}

export interface RequirementFormatted extends FormattedFields {
  qtyPer: string;
  scrapPercent?: string;
}

/**
 * Labor ticket
 * Maps to: Python LaborTicket dataclass
 */
export interface LaborTicket {
  employeeId: string;
  employeeName?: string;
  laborDate: Date;
  operationSeqNo: number;
  hours: {
    setup: number;
    run: number;
  };
  laborRate: number;
  costs: {
    labor: number;
    burden: number;
  };
  quantities: {
    completed: number;
    scrapped: number;
  };
  formatted?: LaborTicketFormatted;
}

export interface LaborTicketFormatted extends FormattedFields {
  laborDate: string;
  laborCost: string;
  totalHours: string;
}

/**
 * Inventory transaction
 * Maps to: Python InventoryTransaction dataclass
 */
export interface InventoryTransaction {
  partId: string;
  partDescription: string;
  transType: string;
  quantity: number;
  transDate: Date;
  locationId?: string;
  costs: {
    unit: number;
    total: number;
  };
  formatted?: InventoryTransFormatted;
}

export interface InventoryTransFormatted extends FormattedFields {
  transType: string;
  transDate: string;
  totalCost: string;
}

/**
 * WIP (Work In Progress) balance
 * Maps to: Python WIPBalance dataclass
 */
export interface WIPBalance {
  costs: {
    material: number;
    labor: number;
    burden: number;
    service: number;
    total: number;
  };
  formatted?: WIPBalanceFormatted;
}

export interface WIPBalanceFormatted extends FormattedFields {
  materialCost: string;
  laborCost: string;
  burdenCost: string;
  totalCost: string;
}

/**
 * Work order status codes
 */
export const WORK_ORDER_STATUS: Record<string, string> = {
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
export const WORK_ORDER_TYPE: Record<string, string> = {
  'M': 'Make',
  'B': 'Buy',
  'S': 'Stock',
  'R': 'Rework',
};

/**
 * Operation status codes
 */
export const OPERATION_STATUS: Record<string, string> = {
  'P': 'Pending',
  'R': 'Ready',
  'S': 'Started',
  'C': 'Complete',
};

/**
 * Inventory transaction type codes
 */
export const INVENTORY_TRANS_TYPE: Record<string, string> = {
  'I': 'Issue',
  'R': 'Return',
  'S': 'Scrap',
  'A': 'Adjust',
  'T': 'Transfer',
};

/**
 * Run type codes
 */
export const RUN_TYPE: Record<string, string> = {
  'H': 'Hours per piece',
  'P': 'Pieces per hour',
  'L': 'Hours per lot',
};
```

---

## Index Exports (src/models/index.ts)

```typescript
// Common models
export * from './common.model';

// Order models
export * from './order.model';

// Part models
export * from './part.model';

// Work order models
export * from './workorder.model';
```

---

## Utility Functions for Transformation

### Row to Model Transformers (src/utils/transformers.ts)

```typescript
import {
  OrderSummary,
  OrderHeader,
  OrderLineItem,
  OrderRow,
  Customer,
} from '../models/order.model';
import {
  Part,
  PartRow,
  WhereUsed,
  PurchaseHistory,
} from '../models/part.model';
import {
  WorkOrder,
  WorkOrderHeader,
  Operation,
  Requirement,
  LaborTicket,
  InventoryTransaction,
  WIPBalance,
  WORK_ORDER_STATUS,
  WORK_ORDER_TYPE,
  OPERATION_STATUS,
  INVENTORY_TRANS_TYPE,
  RUN_TYPE,
} from '../models/workorder.model';
import { formatDate, formatCurrency, formatNumber } from './formatters';

/**
 * Transform database row to OrderSummary
 */
export function toOrderSummary(row: any): OrderSummary {
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
 */
export function toOrderHeader(row: OrderRow): OrderHeader {
  const customer: Customer = {
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

  const notes: string[] = [];
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
 * Transform database row to Part
 */
export function toPart(row: PartRow): Part {
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
 * Transform database row to WorkOrder
 */
export function toWorkOrder(row: any): WorkOrder {
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
 */
export function toWorkOrderHeader(row: any): WorkOrderHeader {
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
 * Format work order ID as BASE-SUB/LOT
 */
export function formatWorkOrderId(baseId: string, subId: string, lotId: string): string {
  return `${baseId}-${subId}/${lotId}`;
}
```

---

## Formatters (src/utils/formatters.ts)

```typescript
/**
 * Format date as MM/DD/YYYY
 */
export function formatDate(date: Date | string | null | undefined): string {
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
 */
export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

/**
 * Format number with thousand separators
 */
export function formatNumber(value: number | null | undefined, decimals: number = 0): string {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format percentage
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '';
  return `${formatNumber(value, 1)}%`;
}

/**
 * Format hours
 */
export function formatHours(value: number | null | undefined): string {
  if (value === null || value === undefined) return '';
  return `${formatNumber(value, 1)} hrs`;
}
```
