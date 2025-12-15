# 05 - Service Layer

## Overview

The service layer contains the business logic and orchestrates database queries. Each service corresponds to a module in the original PyQt6 application.

## File Structure

```
src/services/
├── index.ts              # Export all services
├── order.service.ts      # Sales module business logic
├── part.service.ts       # Inventory module business logic
├── workorder.service.ts  # Engineering module business logic
└── bom.service.ts        # BOM hierarchy operations
```

---

## Order Service (src/services/order.service.ts)

Maps to: `visual_order_lookup/services/order_service.py`

```typescript
import * as orderQueries from '../database/queries/order.queries';
import {
  OrderSummary,
  OrderHeader,
  OrderLineItem,
  DateRangeFilter,
} from '../models';
import {
  toOrderSummary,
  toOrderHeader,
  toOrderLineItem,
} from '../utils/transformers';
import { OrderNotFoundError, ValidationError } from '../utils/errors';
import { logger } from '../utils/logger';

export class OrderService {
  /**
   * Get recent orders
   * Maps to: OrderService.load_recent_orders()
   */
  async getRecentOrders(limit: number = 100): Promise<OrderSummary[]> {
    logger.debug(`Fetching ${limit} recent orders`);

    const rows = await orderQueries.getRecentOrders(limit);
    return rows.map(toOrderSummary);
  }

  /**
   * Filter orders by date range
   * Maps to: OrderService.filter_by_date_range()
   */
  async filterByDateRange(
    filter: DateRangeFilter,
    limit: number = 100
  ): Promise<OrderSummary[]> {
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
   */
  async getOrderByJobNumber(jobNumber: string): Promise<OrderHeader> {
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
   */
  async searchByCustomerName(
    customerName: string,
    filter?: DateRangeFilter,
    limit: number = 100
  ): Promise<OrderSummary[]> {
    // Validation
    if (!customerName || !customerName.trim()) {
      throw new ValidationError('Customer name cannot be empty');
    }

    const trimmedName = customerName.trim();
    logger.debug(`Searching orders for customer: ${trimmedName}`, { filter, limit });

    const rows = await orderQueries.searchByCustomerName(
      trimmedName,
      filter?.startDate,
      filter?.endDate,
      limit
    );

    return rows.map(toOrderSummary);
  }

  /**
   * Get order line items only
   */
  async getOrderLineItems(jobNumber: string): Promise<OrderLineItem[]> {
    if (!jobNumber || !jobNumber.trim()) {
      throw new ValidationError('Job number cannot be empty');
    }

    const trimmedJobNumber = jobNumber.trim();
    logger.debug(`Fetching line items for order: ${trimmedJobNumber}`);

    const rows = await orderQueries.getOrderLineItems(trimmedJobNumber);
    return rows.map(toOrderLineItem);
  }
}

// Singleton instance
export const orderService = new OrderService();
```

---

## Part Service (src/services/part.service.ts)

Maps to: `visual_order_lookup/services/part_service.py`

```typescript
import * as partQueries from '../database/queries/part.queries';
import {
  Part,
  PartSearchResult,
  WhereUsed,
  PurchaseHistory,
} from '../models';
import {
  toPart,
  toWhereUsed,
  toPurchaseHistory,
} from '../utils/transformers';
import { PartNotFoundError, ValidationError } from '../utils/errors';
import { logger } from '../utils/logger';

export class PartService {
  /**
   * Get part by part number
   * Maps to: PartService.search_by_part_number()
   */
  async getPartByNumber(partNumber: string): Promise<Part> {
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
   */
  async searchParts(
    searchPattern: string,
    limit: number = 100
  ): Promise<PartSearchResult[]> {
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
   */
  async getWhereUsed(
    partNumber: string,
    limit: number = 100
  ): Promise<WhereUsed[]> {
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
   */
  async getPurchaseHistory(
    partNumber: string,
    limit: number = 100
  ): Promise<PurchaseHistory[]> {
    if (!partNumber || !partNumber.trim()) {
      throw new ValidationError('Part number cannot be empty');
    }

    const trimmedPartNumber = partNumber.trim().toUpperCase();
    logger.debug(`Fetching purchase history for part: ${trimmedPartNumber}`);

    const rows = await partQueries.getPurchaseHistory(trimmedPartNumber, limit);
    return rows.map(toPurchaseHistory);
  }
}

// Singleton instance
export const partService = new PartService();
```

---

## Work Order Service (src/services/workorder.service.ts)

Maps to: `visual_order_lookup/services/work_order_service.py`

```typescript
import * as workorderQueries from '../database/queries/workorder.queries';
import {
  WorkOrder,
  WorkOrderHeader,
  WorkOrderId,
  Operation,
  Requirement,
  LaborTicket,
  InventoryTransaction,
  WIPBalance,
} from '../models';
import {
  toWorkOrder,
  toWorkOrderHeader,
  toOperation,
  toRequirement,
  toLaborTicket,
  toInventoryTransaction,
  toWIPBalance,
} from '../utils/transformers';
import { WorkOrderNotFoundError, ValidationError } from '../utils/errors';
import { logger } from '../utils/logger';

export class WorkOrderService {
  /**
   * Search work orders by base ID pattern
   * Maps to: WorkOrderService.search_work_orders()
   */
  async searchWorkOrders(
    baseIdPattern: string,
    limit: number = 100
  ): Promise<WorkOrder[]> {
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
   */
  async getWorkOrderHeader(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<WorkOrderHeader> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getOperations(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<Operation[]> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getRequirements(
    baseId: string,
    lotId: string,
    subId: string,
    operationSeqNo?: number
  ): Promise<Requirement[]> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getLaborTickets(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<LaborTicket[]> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getInventoryTransactions(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<InventoryTransaction[]> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getWIPBalance(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<WIPBalance | null> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  async getWorkOrderHierarchy(
    baseId: string,
    lotId: string,
    subId: string
  ): Promise<WorkOrder[]> {
    this.validateWorkOrderId(baseId, lotId, subId);

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
   */
  private validateWorkOrderId(baseId: string, lotId: string, subId: string): void {
    if (!baseId || !baseId.trim()) {
      throw new ValidationError('Base ID cannot be empty');
    }
    if (!lotId || !lotId.trim()) {
      throw new ValidationError('Lot ID cannot be empty');
    }
    if (!subId || subId.trim() === '') {
      throw new ValidationError('Sub ID cannot be empty');
    }
  }
}

// Singleton instance
export const workOrderService = new WorkOrderService();
```

---

## BOM Service (src/services/bom.service.ts)

Maps to: `visual_order_lookup/services/bom_service.py`

```typescript
import * as bomQueries from '../database/queries/bom.queries';
import { BOMNode, Job } from '../models';
import { toBOMNode, toJob } from '../utils/transformers';
import { JobNotFoundError, ValidationError } from '../utils/errors';
import { logger } from '../utils/logger';

export interface BOMAssembly {
  jobNumber: string;
  lotId: string;
  partId: string;
  partDescription: string;
  orderQty: number;
  status: string;
  hasChildren: boolean;
}

export class BOMService {
  /**
   * Get job information
   * Maps to: BOMService.get_job_info()
   */
  async getJobInfo(jobNumber: string): Promise<Job> {
    if (!jobNumber || !jobNumber.trim()) {
      throw new ValidationError('Job number cannot be empty');
    }

    const trimmedJobNumber = jobNumber.trim();
    logger.debug(`Fetching job info: ${trimmedJobNumber}`);

    const row = await bomQueries.getJobInfo(trimmedJobNumber);

    if (!row) {
      throw new JobNotFoundError(trimmedJobNumber);
    }

    return toJob(row);
  }

  /**
   * Get top-level BOM assemblies for a job
   * Maps to: BOMService.get_bom_assemblies()
   */
  async getBOMAssemblies(jobNumber: string): Promise<BOMAssembly[]> {
    if (!jobNumber || !jobNumber.trim()) {
      throw new ValidationError('Job number cannot be empty');
    }

    const trimmedJobNumber = jobNumber.trim();
    logger.debug(`Fetching BOM assemblies for job: ${trimmedJobNumber}`);

    const rows = await bomQueries.getBOMAssemblies(trimmedJobNumber);

    return rows.map(row => ({
      jobNumber: row.jobNumber,
      lotId: row.lotId,
      partId: row.partId,
      partDescription: row.partDescription,
      orderQty: row.orderQty,
      status: row.status,
      hasChildren: row.childCount > 0,
    }));
  }

  /**
   * Get child parts for an assembly (lazy load)
   * Maps to: BOMService.get_assembly_parts()
   */
  async getAssemblyParts(
    jobNumber: string,
    lotId: string
  ): Promise<BOMNode[]> {
    if (!jobNumber || !jobNumber.trim()) {
      throw new ValidationError('Job number cannot be empty');
    }
    if (!lotId || !lotId.trim()) {
      throw new ValidationError('Lot ID cannot be empty');
    }

    logger.debug(`Fetching assembly parts for: ${jobNumber}/${lotId}`);

    const rows = await bomQueries.getAssemblyParts(
      jobNumber.trim(),
      lotId.trim()
    );

    return rows.map(toBOMNode);
  }

  /**
   * Get complete BOM hierarchy for a job
   * Maps to: BOMService.get_bom_hierarchy()
   */
  async getBOMHierarchy(jobNumber: string): Promise<BOMNode[]> {
    if (!jobNumber || !jobNumber.trim()) {
      throw new ValidationError('Job number cannot be empty');
    }

    const trimmedJobNumber = jobNumber.trim();
    logger.debug(`Fetching complete BOM hierarchy for job: ${trimmedJobNumber}`);

    const rows = await bomQueries.getBOMHierarchy(trimmedJobNumber);
    return rows.map(toBOMNode);
  }
}

// Singleton instance
export const bomService = new BOMService();
```

---

## Service Index (src/services/index.ts)

```typescript
export { OrderService, orderService } from './order.service';
export { PartService, partService } from './part.service';
export { WorkOrderService, workOrderService } from './workorder.service';
export { BOMService, bomService } from './bom.service';
```

---

## Python to TypeScript Mapping Summary

| Python Service Method | TypeScript Service Method |
|-----------------------|---------------------------|
| `OrderService.load_recent_orders()` | `orderService.getRecentOrders()` |
| `OrderService.filter_by_date_range()` | `orderService.filterByDateRange()` |
| `OrderService.get_order_by_job_number()` | `orderService.getOrderByJobNumber()` |
| `OrderService.search_by_customer_name()` | `orderService.searchByCustomerName()` |
| `PartService.search_by_part_number()` | `partService.getPartByNumber()` |
| `PartService.get_where_used()` | `partService.getWhereUsed()` |
| `PartService.get_purchase_history()` | `partService.getPurchaseHistory()` |
| `WorkOrderService.search_work_orders()` | `workOrderService.searchWorkOrders()` |
| `WorkOrderService.get_work_order_header()` | `workOrderService.getWorkOrderHeader()` |
| `WorkOrderService.get_operations()` | `workOrderService.getOperations()` |
| `WorkOrderService.get_requirements()` | `workOrderService.getRequirements()` |
| `WorkOrderService.get_labor_tickets()` | `workOrderService.getLaborTickets()` |
| `WorkOrderService.get_inventory_transactions()` | `workOrderService.getInventoryTransactions()` |
| `WorkOrderService.get_wip_balance()` | `workOrderService.getWIPBalance()` |
| `WorkOrderService.get_work_order_hierarchy()` | `workOrderService.getWorkOrderHierarchy()` |
| `BOMService.get_job_info()` | `bomService.getJobInfo()` |
| `BOMService.get_bom_assemblies()` | `bomService.getBOMAssemblies()` |
| `BOMService.get_assembly_parts()` | `bomService.getAssemblyParts()` |
| `BOMService.get_bom_hierarchy()` | `bomService.getBOMHierarchy()` |

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

**TypeScript (Express):**
```typescript
// No manual threading needed - Express handles async naturally
async getRecentOrders(limit: number): Promise<OrderSummary[]> {
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

**TypeScript:**
```typescript
// Errors propagate automatically through async/await
// Global error middleware handles translation to HTTP responses
throw new OrderNotFoundError(jobNumber);
```

### 3. Connection Management
**Python:**
```python
cursor = self.connection.get_cursor()
# ... use cursor
cursor.close()
```

**TypeScript:**
```typescript
// Connection pool handles connection lifecycle automatically
const rows = await orderQueries.getRecentOrders(limit);
// No manual cleanup needed
```
