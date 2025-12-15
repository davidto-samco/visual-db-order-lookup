/**
 * Visual Order Lookup - TypeScript Interfaces Reference
 *
 * This file contains all TypeScript interfaces needed for the Express migration.
 * Copy these to src/types/index.ts in your Express project.
 */

// ============================================
// ORDER INTERFACES
// ============================================

export interface OrderSummary {
  jobNumber: string;
  customerName: string;
  poNumber: string | null;
  orderDate: Date | null;
  totalAmount: number | null;
}

export interface Address {
  line1: string | null;
  line2: string | null;
  city: string | null;
  state: string | null;
  zipCode: string | null;
  country: string | null;
}

export interface Customer {
  id: string;
  name: string;
  shipToAddress: Address;
  billToAddress: Address;
}

export interface OrderLineItem {
  lineNo: number;
  partId: string;
  description: string | null;
  orderQty: number;
  unitPrice: number;
  extendedPrice: number;
  baseId: string | null;
  lotId: string | null;
  binaryDescription: string | null;
}

export interface OrderHeader {
  id: string;
  jobNumber: string;
  orderDate: Date | null;
  desiredShipDate: Date | null;
  customer: Customer;
  poNumber: string | null;
  contactName: string | null;
  contactPhone: string | null;
  contactEmail: string | null;
  lineItems: OrderLineItem[];
  totalAmount: number;
  paymentTerms: string | null;
  projectDescription: string | null;
  salesRepName: string | null;
}

export interface DateRangeFilter {
  startDate?: Date;
  endDate?: Date;
  limit?: number;
}

// ============================================
// PART INTERFACES
// ============================================

export interface Part {
  id: string;
  description: string | null;
  stockUm: string | null;
  productCode: string | null;
  commodityCode: string | null;
  standardCost: number;
  averageCost: number;
  lastCost: number;
  listPrice: number;
  qtyOnHand: number;
  qtyOnOrder: number;
  qtyAllocated: number;
  vendorId: string | null;
  vendorName: string | null;
  makeBuyCode: string | null;
  abc: string | null;
  phantomFlag: boolean;
  isActive: boolean;
}

export interface WhereUsed {
  baseId: string;
  lotId: string;
  subId: string;
  partId: string;
  qtyPer: number;
  fixedQty: number;
  scrapPercent: number;
  status: string | null;
}

export interface PurchaseHistory {
  poNumber: string;
  lineNo: number;
  vendorId: string;
  vendorName: string | null;
  orderDate: Date | null;
  orderQty: number;
  receivedQty: number;
  unitPrice: number;
  currencyId: string | null;
}

// ============================================
// WORK ORDER INTERFACES
// ============================================

export interface WorkOrderKey {
  baseId: string;
  lotId: string;
  subId: string;
}

export interface WorkOrderSummary extends WorkOrderKey {
  partId: string;
  partDescription: string | null;
  desiredQty: number;
  status: string | null;
  orderDate: Date | null;
}

export interface WorkOrderHeader extends WorkOrderSummary {
  completedQty: number;
  desiredDate: Date | null;
  completedDate: Date | null;
  operationCount: number;
  requirementCount: number;
  laborCount: number;
  transactionCount: number;
}

export interface Operation {
  sequenceNo: number;
  operationId: string;
  description: string | null;
  department: string | null;
  workCenter: string | null;
  setupHrs: number;
  runHrsPer: number;
  status: string | null;
}

export interface Requirement {
  partId: string;
  description: string | null;
  qtyPer: number;
  fixedQty: number;
  scrapPercent: number;
  subordWoSubId: string | null;
  hasChildWorkOrder: boolean;
}

export interface LaborTicket {
  employeeId: string;
  laborDate: Date;
  setupHrs: number;
  runHrs: number;
  operationSeqNo: number;
}

export interface InventoryTransaction {
  partId: string;
  transType: string;
  quantity: number;
  transDate: Date;
  lotId: string | null;
  location: string | null;
}

export interface WIPBalance {
  materialCost: number;
  laborCost: number;
  burdenCost: number;
  totalCost: number;
}

// ============================================
// BOM INTERFACES
// ============================================

export interface JobBOMInfo {
  jobNumber: string;
  customerName: string;
  orderDate: Date | null;
  assemblyCount: number;
}

export type BOMNodeType = 'assembly' | 'manufactured' | 'purchased';

export interface BOMNode extends WorkOrderKey {
  partId: string;
  description: string | null;
  qtyPer: number | null;
  makeBuyCode: string | null;
  hasChildren: boolean;
  nodeType: BOMNodeType;
  children?: BOMNode[];
}

// ============================================
// API RESPONSE INTERFACES
// ============================================

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
}

export interface ApiResponse<T> {
  data: T;
  meta?: PaginationMeta;
}

export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface ListResponse<T> extends ApiResponse<T[]> {
  meta: PaginationMeta;
}

// ============================================
// REQUEST INTERFACES
// ============================================

export interface OrderQueryParams {
  limit?: number;
  startDate?: string;
  endDate?: string;
  customer?: string;
}

export interface WorkOrderSearchParams {
  baseId: string;
  limit?: number;
}

// ============================================
// DATABASE ROW INTERFACES
// ============================================

/**
 * Raw database row types for mapping SQL results
 * These represent the shape of data returned from SQL queries
 * before being transformed to the domain models above.
 */

export interface OrderSummaryRow {
  job_number: string;
  customer_name: string | null;
  po_number: string | null;
  order_date: Date | null;
  total_amount: number | null;
}

export interface OrderHeaderRow {
  id: string;
  job_number: string;
  order_date: Date | null;
  desired_ship_date: Date | null;
  customer_po_ref: string | null;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  total_amt_ordered: number | null;
  payment_terms: string | null;
  customer_id: string;
  customer_name: string | null;
  ship_addr_1: string | null;
  ship_addr_2: string | null;
  ship_city: string | null;
  ship_state: string | null;
  ship_zip: string | null;
  ship_country: string | null;
  bill_addr_1: string | null;
  bill_addr_2: string | null;
  bill_city: string | null;
  bill_state: string | null;
  bill_zip: string | null;
  bill_country: string | null;
}

export interface OrderLineItemRow {
  line_no: number;
  part_id: string;
  description: string | null;
  order_qty: number;
  unit_price: number;
  extended_price: number;
  base_id: string | null;
  lot_id: string | null;
  bits: Buffer | null;
}

export interface PartRow {
  id: string;
  description: string | null;
  stock_um: string | null;
  product_code: string | null;
  commodity_code: string | null;
  standard_cost: number;
  average_cost: number;
  last_cost: number;
  list_price: number;
  qty_on_hand: number;
  qty_on_order: number;
  qty_allocated: number;
  vendor_id: string | null;
  vendor_name: string | null;
  make_buy_code: string | null;
  abc: string | null;
  phantom_flag: string | null;
  status: string | null;
}

export interface WorkOrderRow {
  base_id: string;
  lot_id: string;
  sub_id: string;
  part_id: string;
  part_description: string | null;
  desired_qty: number;
  completed_qty: number;
  status: string | null;
  order_date: Date | null;
  desired_date: Date | null;
  completed_date: Date | null;
}

// ============================================
// UTILITY TYPES
// ============================================

/**
 * Maps SQL NULL to undefined for optional fields
 */
export type Nullable<T> = T | null;

/**
 * Make specific properties optional
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Extract the data type from an API response
 */
export type ExtractData<T> = T extends ApiResponse<infer U> ? U : never;

// ============================================
// SERVICE INTERFACES
// ============================================

export interface IOrderService {
  getRecentOrders(limit?: number): Promise<OrderSummary[]>;
  filterByDateRange(filter: DateRangeFilter): Promise<OrderSummary[]>;
  getOrderByJobNumber(jobNumber: string): Promise<OrderHeader | null>;
  searchByCustomerName(name: string, limit?: number): Promise<OrderSummary[]>;
}

export interface IPartService {
  getPartById(partId: string): Promise<Part | null>;
  getWhereUsed(partId: string): Promise<WhereUsed[]>;
  getPurchaseHistory(partId: string): Promise<PurchaseHistory[]>;
}

export interface IWorkOrderService {
  searchWorkOrders(baseIdPattern: string, limit?: number): Promise<WorkOrderSummary[]>;
  getWorkOrderHeader(key: WorkOrderKey): Promise<WorkOrderHeader | null>;
  getOperations(key: WorkOrderKey): Promise<Operation[]>;
  getRequirements(key: WorkOrderKey, seqNo?: number): Promise<Requirement[]>;
  getLaborTickets(key: WorkOrderKey): Promise<LaborTicket[]>;
  getInventoryTransactions(key: WorkOrderKey): Promise<InventoryTransaction[]>;
  getWIPBalance(key: WorkOrderKey): Promise<WIPBalance | null>;
}

export interface IBOMService {
  getJobInfo(jobNumber: string): Promise<JobBOMInfo | null>;
  getAssemblies(jobNumber: string): Promise<BOMNode[]>;
  getChildren(key: WorkOrderKey): Promise<BOMNode[]>;
}

// ============================================
// ERROR TYPES
// ============================================

export class OrderNotFoundError extends Error {
  constructor(jobNumber: string) {
    super(`Order not found: ${jobNumber}`);
    this.name = 'OrderNotFoundError';
  }
}

export class PartNotFoundError extends Error {
  constructor(partId: string) {
    super(`Part not found: ${partId}`);
    this.name = 'PartNotFoundError';
  }
}

export class WorkOrderNotFoundError extends Error {
  public readonly baseId: string;
  public readonly lotId: string;
  public readonly subId: string;

  constructor(baseId: string, lotId: string, subId: string) {
    super(`Work order not found: ${baseId}-${lotId}-${subId}`);
    this.name = 'WorkOrderNotFoundError';
    this.baseId = baseId;
    this.lotId = lotId;
    this.subId = subId;
  }
}

export class DatabaseConnectionError extends Error {
  constructor(message: string) {
    super(`Database connection failed: ${message}`);
    this.name = 'DatabaseConnectionError';
  }
}

export class ValidationError extends Error {
  public readonly field: string;
  public readonly value: unknown;

  constructor(field: string, message: string, value?: unknown) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
  }
}
