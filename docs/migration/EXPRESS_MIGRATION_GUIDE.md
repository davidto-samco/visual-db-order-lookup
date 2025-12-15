# Visual Order Lookup: Python Desktop to Express Web Migration Guide

This document provides comprehensive guidance for migrating the Visual Order Lookup application from a Python/PyQt6 desktop application to an Express.js web application.

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Comparison](#architecture-comparison)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Database Layer Migration](#database-layer-migration)
6. [API Design](#api-design)
7. [Frontend Architecture](#frontend-architecture)
8. [Service Layer Migration](#service-layer-migration)
9. [Authentication & Security](#authentication--security)
10. [Configuration Management](#configuration-management)
11. [Testing Strategy](#testing-strategy)
12. [Deployment](#deployment)
13. [Migration Phases](#migration-phases)

---

## Executive Summary

### Current State
- **Platform**: Windows Desktop Application
- **Framework**: Python 3.11+ with PyQt6
- **Database**: SQL Server (SAMCO database) via pyodbc
- **Users**: Spare Parts Department staff on local network

### Target State
- **Platform**: Web Application (browser-based)
- **Backend**: Node.js with Express.js
- **Frontend**: React (recommended) or vanilla HTML/JS
- **Database**: Same SQL Server database via mssql/tedious
- **Users**: Any device with browser on network

### Key Benefits of Migration
- Cross-platform accessibility (Windows, Mac, Linux, mobile)
- No installation required on client machines
- Centralized updates and maintenance
- Easier scalability and monitoring
- Modern development tooling and ecosystem

---

## Architecture Comparison

### Current Desktop Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PyQt6 Desktop App                     │
├─────────────────────────────────────────────────────────┤
│  UI Layer (PyQt6 Widgets)                               │
│  ├── MainWindow                                         │
│  ├── Sales Module (OrderListView, OrderDetailView)      │
│  ├── Inventory Module (PartSearchPanel, PartDetailView) │
│  └── Engineering Module (WorkOrderTreeWidget)           │
├─────────────────────────────────────────────────────────┤
│  Service Layer (Python)                                 │
│  ├── OrderService                                       │
│  ├── PartService                                        │
│  ├── BOMService                                         │
│  ├── WorkOrderService                                   │
│  └── ReportService                                      │
├─────────────────────────────────────────────────────────┤
│  Database Layer (pyodbc)                                │
│  ├── DatabaseConnection                                 │
│  ├── Models (DTOs)                                      │
│  └── Query Functions                                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  SQL Server (SAMCO)   │
              │  10.10.10.142:1433    │
              └───────────────────────┘
```

### Target Web Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Browser                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend                                │   │
│  │  ├── Sales Module (OrderList, OrderDetail)                      │   │
│  │  ├── Inventory Module (PartSearch, PartDetail)                  │   │
│  │  └── Engineering Module (WorkOrderTree)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ HTTP/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Express.js Server                               │
├─────────────────────────────────────────────────────────────────────────┤
│  Route Layer                                                            │
│  ├── /api/orders/*                                                     │
│  ├── /api/parts/*                                                      │
│  ├── /api/work-orders/*                                                │
│  └── /api/reports/*                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Service Layer (JavaScript/TypeScript)                                  │
│  ├── OrderService                                                       │
│  ├── PartService                                                        │
│  ├── BOMService                                                         │
│  ├── WorkOrderService                                                   │
│  └── ReportService                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Database Layer (mssql/tedious)                                         │
│  ├── Connection Pool                                                    │
│  ├── Models (TypeScript interfaces)                                     │
│  └── Query Functions                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  SQL Server (SAMCO)   │
                        │  10.10.10.142:1433    │
                        └───────────────────────┘
```

---

## Technology Stack

### Backend Stack

| Component | Current (Python) | Target (Express) |
|-----------|-----------------|------------------|
| Runtime | Python 3.11+ | Node.js 20 LTS |
| Web Framework | N/A | Express.js 4.x |
| Database Driver | pyodbc | mssql (tedious) |
| Configuration | python-dotenv | dotenv |
| Templates | Jinja2 | EJS or React |
| Validation | Manual | Joi or Zod |
| Logging | Python logging | Winston or Pino |
| Testing | pytest | Jest + Supertest |

### Frontend Stack (Recommended)

| Component | Technology |
|-----------|------------|
| Framework | React 18+ |
| Build Tool | Vite |
| State Management | React Query (TanStack Query) |
| Routing | React Router v6 |
| UI Components | Material UI or Tailwind CSS |
| HTTP Client | Axios or Fetch API |
| Tree Component | react-arborist (for BOM trees) |
| Table Component | TanStack Table |
| Testing | Vitest + React Testing Library |

### Development Tools

| Tool | Purpose |
|------|---------|
| TypeScript | Type safety |
| ESLint | Code linting |
| Prettier | Code formatting |
| Husky | Git hooks |
| Docker | Containerization |
| PM2 | Process management |

---

## Project Structure

### Express Backend Structure

```
visual-order-lookup-api/
├── src/
│   ├── index.ts                    # Application entry point
│   ├── app.ts                      # Express app configuration
│   ├── config/
│   │   ├── database.ts             # DB connection config
│   │   ├── environment.ts          # Environment variables
│   │   └── logger.ts               # Logging configuration
│   ├── database/
│   │   ├── connection.ts           # Connection pool management
│   │   ├── models/
│   │   │   ├── order.model.ts      # Order interfaces/types
│   │   │   ├── customer.model.ts   # Customer interfaces
│   │   │   ├── part.model.ts       # Part interfaces
│   │   │   └── work-order.model.ts # Work order interfaces
│   │   └── queries/
│   │       ├── order.queries.ts    # Order SQL queries
│   │       ├── part.queries.ts     # Part SQL queries
│   │       └── work-order.queries.ts
│   ├── services/
│   │   ├── order.service.ts        # Order business logic
│   │   ├── part.service.ts         # Part business logic
│   │   ├── bom.service.ts          # BOM hierarchy logic
│   │   ├── work-order.service.ts   # Work order logic
│   │   └── report.service.ts       # Report generation
│   ├── routes/
│   │   ├── index.ts                # Route aggregator
│   │   ├── order.routes.ts         # Order endpoints
│   │   ├── part.routes.ts          # Part endpoints
│   │   ├── work-order.routes.ts    # Work order endpoints
│   │   └── report.routes.ts        # Report endpoints
│   ├── middleware/
│   │   ├── error-handler.ts        # Global error handling
│   │   ├── validation.ts           # Request validation
│   │   ├── auth.ts                 # Authentication (if needed)
│   │   └── logging.ts              # Request logging
│   ├── utils/
│   │   ├── formatters.ts           # Date/currency formatting
│   │   └── validators.ts           # Input validation
│   └── types/
│       └── index.ts                # Shared TypeScript types
├── tests/
│   ├── unit/
│   │   └── services/
│   ├── integration/
│   │   └── routes/
│   └── fixtures/
├── templates/                      # Report templates (if using SSR)
│   └── order-acknowledgement.ejs
├── package.json
├── tsconfig.json
├── .env.example
├── .eslintrc.js
├── jest.config.js
└── Dockerfile
```

### React Frontend Structure

```
visual-order-lookup-web/
├── src/
│   ├── main.tsx                    # React entry point
│   ├── App.tsx                     # Root component
│   ├── api/
│   │   ├── client.ts               # Axios instance
│   │   ├── orders.api.ts           # Order API calls
│   │   ├── parts.api.ts            # Part API calls
│   │   └── work-orders.api.ts      # Work order API calls
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout.tsx          # Main layout
│   │   │   ├── Navigation.tsx      # Module navigation
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── sales/
│   │   │   ├── SalesModule.tsx
│   │   │   ├── OrderList.tsx
│   │   │   ├── OrderDetail.tsx
│   │   │   └── SearchPanel.tsx
│   │   ├── inventory/
│   │   │   ├── InventoryModule.tsx
│   │   │   ├── PartSearch.tsx
│   │   │   ├── PartDetail.tsx
│   │   │   └── WhereUsedTable.tsx
│   │   └── engineering/
│   │       ├── EngineeringModule.tsx
│   │       ├── WorkOrderSearch.tsx
│   │       └── WorkOrderTree.tsx
│   ├── hooks/
│   │   ├── useOrders.ts            # Order data hooks
│   │   ├── useParts.ts             # Part data hooks
│   │   └── useWorkOrders.ts        # Work order hooks
│   ├── types/
│   │   └── index.ts                # TypeScript interfaces
│   ├── utils/
│   │   └── formatters.ts           # Formatting utilities
│   └── styles/
│       └── globals.css
├── public/
│   └── images/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

---

## Database Layer Migration

### Connection Management

#### Python (Current)
```python
# database/connection.py
class DatabaseConnection:
    def __init__(self, connection_string: str):
        self._connection_string = connection_string
        self._connection: Optional[pyodbc.Connection] = None

    def connect(self) -> None:
        self._connection = pyodbc.connect(
            self._connection_string,
            timeout=10,
            autocommit=True
        )

    def get_cursor(self) -> pyodbc.Cursor:
        return self._connection.cursor()
```

#### Express (Target)
```typescript
// src/database/connection.ts
import sql from 'mssql';

const config: sql.config = {
  server: process.env.DB_SERVER || '10.10.10.142',
  port: parseInt(process.env.DB_PORT || '1433'),
  database: process.env.DB_NAME || 'SAMCO',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  options: {
    encrypt: false,
    trustServerCertificate: true,
  },
  pool: {
    min: 2,
    max: 10,
    idleTimeoutMillis: 30000,
  },
  connectionTimeout: 10000,
  requestTimeout: 30000,
};

let pool: sql.ConnectionPool | null = null;

export async function getPool(): Promise<sql.ConnectionPool> {
  if (!pool) {
    pool = await sql.connect(config);
  }
  return pool;
}

export async function query<T>(
  queryString: string,
  params?: Record<string, unknown>
): Promise<T[]> {
  const poolConnection = await getPool();
  const request = poolConnection.request();

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      request.input(key, value);
    });
  }

  const result = await request.query(queryString);
  return result.recordset as T[];
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.close();
    pool = null;
  }
}
```

### Model Migration

#### Python (Current)
```python
# database/models/core.py
@dataclass
class OrderSummary:
    job_number: str
    customer_name: str
    po_number: Optional[str]
    order_date: Optional[date]
    total_amount: Optional[Decimal]

@dataclass
class Part:
    id: str
    description: Optional[str]
    stock_um: Optional[str]
    product_code: Optional[str]
    commodity_code: Optional[str]
    # ... more fields
```

#### Express (Target)
```typescript
// src/database/models/order.model.ts
export interface OrderSummary {
  jobNumber: string;
  customerName: string;
  poNumber: string | null;
  orderDate: Date | null;
  totalAmount: number | null;
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
}
```

```typescript
// src/database/models/part.model.ts
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
```

### Query Migration

#### Python (Current)
```python
# database/queries/core.py
def get_recent_orders(cursor: pyodbc.Cursor, limit: int = 100) -> list[OrderSummary]:
    cursor.execute("""
        SELECT TOP (?)
            co.ID AS job_number,
            c.NAME AS customer_name,
            co.CUSTOMER_PO_REF AS po_number,
            co.ORDER_DATE AS order_date,
            co.TOTAL_AMT_ORDERED AS total_amount
        FROM CUSTOMER_ORDER co
        LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
        ORDER BY co.ORDER_DATE DESC, co.ID DESC
    """, (limit,))

    return [
        OrderSummary(
            job_number=row.job_number,
            customer_name=row.customer_name or "Unknown",
            po_number=row.po_number,
            order_date=row.order_date,
            total_amount=row.total_amount
        )
        for row in cursor.fetchall()
    ]
```

#### Express (Target)
```typescript
// src/database/queries/order.queries.ts
import { query } from '../connection';
import { OrderSummary } from '../models/order.model';

export async function getRecentOrders(limit: number = 100): Promise<OrderSummary[]> {
  const sql = `
    SELECT TOP (@limit)
      co.ID AS jobNumber,
      c.NAME AS customerName,
      co.CUSTOMER_PO_REF AS poNumber,
      co.ORDER_DATE AS orderDate,
      co.TOTAL_AMT_ORDERED AS totalAmount
    FROM CUSTOMER_ORDER co
    LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
    ORDER BY co.ORDER_DATE DESC, co.ID DESC
  `;

  const results = await query<{
    jobNumber: string;
    customerName: string | null;
    poNumber: string | null;
    orderDate: Date | null;
    totalAmount: number | null;
  }>(sql, { limit });

  return results.map(row => ({
    jobNumber: row.jobNumber,
    customerName: row.customerName || 'Unknown',
    poNumber: row.poNumber,
    orderDate: row.orderDate,
    totalAmount: row.totalAmount,
  }));
}

export async function searchByJobNumber(jobNumber: string): Promise<OrderHeader | null> {
  const sql = `
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
      c.COUNTRY AS shipCountry
    FROM CUSTOMER_ORDER co
    LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
    WHERE co.ID = @jobNumber
  `;

  const results = await query(sql, { jobNumber });

  if (results.length === 0) {
    return null;
  }

  // ... map to OrderHeader
}
```

---

## API Design

### RESTful Endpoints

#### Orders API

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/api/orders` | List recent orders | `limit`, `startDate`, `endDate`, `customer` |
| GET | `/api/orders/:jobNumber` | Get order details | - |
| GET | `/api/orders/:jobNumber/report` | Generate order report | `format` (html/pdf) |

#### Parts API

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/api/parts/:partId` | Get part details | - |
| GET | `/api/parts/:partId/where-used` | Get BOM usage | - |
| GET | `/api/parts/:partId/purchase-history` | Get PO history | - |

#### Work Orders API

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/api/work-orders` | Search work orders | `baseId`, `limit` |
| GET | `/api/work-orders/:baseId/:lotId/:subId` | Get work order header | - |
| GET | `/api/work-orders/:baseId/:lotId/:subId/operations` | Get operations | - |
| GET | `/api/work-orders/:baseId/:lotId/:subId/operations/:seqNo/requirements` | Get requirements | - |
| GET | `/api/work-orders/:baseId/:lotId/:subId/labor` | Get labor tickets | - |
| GET | `/api/work-orders/:baseId/:lotId/:subId/transactions` | Get inventory transactions | - |
| GET | `/api/work-orders/:baseId/:lotId/:subId/wip` | Get WIP balance | - |

#### BOM API

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/api/bom/:jobNumber` | Get job BOM info | - |
| GET | `/api/bom/:jobNumber/assemblies` | Get top-level assemblies | - |
| GET | `/api/bom/:baseId/:lotId/:subId/children` | Get child requirements | - |

### Route Implementation

```typescript
// src/routes/order.routes.ts
import { Router, Request, Response, NextFunction } from 'express';
import * as orderService from '../services/order.service';
import { validateQuery } from '../middleware/validation';
import { orderQuerySchema } from '../schemas/order.schema';

const router = Router();

// GET /api/orders
router.get(
  '/',
  validateQuery(orderQuerySchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { limit = 100, startDate, endDate, customer } = req.query;

      let orders;
      if (startDate || endDate) {
        orders = await orderService.filterByDateRange({
          startDate: startDate ? new Date(startDate as string) : undefined,
          endDate: endDate ? new Date(endDate as string) : undefined,
          limit: Number(limit),
        });
      } else if (customer) {
        orders = await orderService.searchByCustomerName(
          customer as string,
          Number(limit)
        );
      } else {
        orders = await orderService.getRecentOrders(Number(limit));
      }

      res.json({ data: orders });
    } catch (error) {
      next(error);
    }
  }
);

// GET /api/orders/:jobNumber
router.get(
  '/:jobNumber',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { jobNumber } = req.params;
      const order = await orderService.getOrderByJobNumber(jobNumber);

      if (!order) {
        return res.status(404).json({
          error: 'Order not found',
          jobNumber,
        });
      }

      res.json({ data: order });
    } catch (error) {
      next(error);
    }
  }
);

// GET /api/orders/:jobNumber/report
router.get(
  '/:jobNumber/report',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { jobNumber } = req.params;
      const { format = 'html' } = req.query;

      const order = await orderService.getOrderByJobNumber(jobNumber);

      if (!order) {
        return res.status(404).json({
          error: 'Order not found',
          jobNumber,
        });
      }

      const report = await orderService.generateReport(order, format as string);

      if (format === 'pdf') {
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader(
          'Content-Disposition',
          `attachment; filename="order-${jobNumber}.pdf"`
        );
      } else {
        res.setHeader('Content-Type', 'text/html');
      }

      res.send(report);
    } catch (error) {
      next(error);
    }
  }
);

export default router;
```

```typescript
// src/routes/index.ts
import { Router } from 'express';
import orderRoutes from './order.routes';
import partRoutes from './part.routes';
import workOrderRoutes from './work-order.routes';
import bomRoutes from './bom.routes';

const router = Router();

router.use('/orders', orderRoutes);
router.use('/parts', partRoutes);
router.use('/work-orders', workOrderRoutes);
router.use('/bom', bomRoutes);

export default router;
```

### Response Formats

```typescript
// Success response
{
  "data": { ... },
  "meta": {
    "total": 100,
    "limit": 100,
    "offset": 0
  }
}

// Error response
{
  "error": "Order not found",
  "code": "NOT_FOUND",
  "details": {
    "jobNumber": "12345"
  }
}
```

---

## Frontend Architecture

### React Component Examples

#### Sales Module

```tsx
// src/components/sales/SalesModule.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { OrderList } from './OrderList';
import { OrderDetail } from './OrderDetail';
import { SearchPanel } from './SearchPanel';
import { getOrders, getOrderByJobNumber } from '../../api/orders.api';
import type { OrderSummary, DateFilter } from '../../types';

export function SalesModule() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [filters, setFilters] = useState<DateFilter>({});

  const ordersQuery = useQuery({
    queryKey: ['orders', filters],
    queryFn: () => getOrders(filters),
  });

  const orderDetailQuery = useQuery({
    queryKey: ['order', selectedJob],
    queryFn: () => getOrderByJobNumber(selectedJob!),
    enabled: !!selectedJob,
  });

  return (
    <div className="sales-module">
      <SearchPanel
        filters={filters}
        onFilterChange={setFilters}
        onJobSearch={(job) => setSelectedJob(job)}
      />

      <div className="content-area">
        <OrderList
          orders={ordersQuery.data ?? []}
          loading={ordersQuery.isLoading}
          selectedJob={selectedJob}
          onSelect={setSelectedJob}
        />

        {selectedJob && (
          <OrderDetail
            order={orderDetailQuery.data}
            loading={orderDetailQuery.isLoading}
          />
        )}
      </div>
    </div>
  );
}
```

#### Engineering Module - Work Order Tree

```tsx
// src/components/engineering/WorkOrderTree.tsx
import { useState, useCallback } from 'react';
import { Tree, NodeApi } from 'react-arborist';
import { useQuery } from '@tanstack/react-query';
import { getWorkOrderChildren } from '../../api/work-orders.api';
import type { BOMNode } from '../../types';

interface WorkOrderTreeProps {
  rootNodes: BOMNode[];
}

export function WorkOrderTree({ rootNodes }: WorkOrderTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const loadChildren = useCallback(async (node: BOMNode) => {
    const children = await getWorkOrderChildren(
      node.baseId,
      node.lotId,
      node.subId
    );
    return children;
  }, []);

  const getNodeColor = (node: BOMNode): string => {
    if (node.hasChildren) return '#0066cc'; // Assembly - blue
    if (node.makeBuyCode === 'M') return '#000000'; // Manufactured - black
    return '#cc0000'; // Purchased - red
  };

  return (
    <Tree
      data={rootNodes}
      openByDefault={false}
      width="100%"
      height={600}
      indent={24}
      rowHeight={28}
      onToggle={(id) => {
        setExpandedIds((prev) => {
          const next = new Set(prev);
          if (next.has(id)) {
            next.delete(id);
          } else {
            next.add(id);
          }
          return next;
        });
      }}
    >
      {({ node, style, dragHandle }) => (
        <div
          style={{ ...style, color: getNodeColor(node.data) }}
          ref={dragHandle}
        >
          {node.isLeaf ? '📄' : node.isOpen ? '📂' : '📁'}{' '}
          {node.data.partId} - {node.data.description}
          {node.data.qtyPer && ` (Qty: ${node.data.qtyPer})`}
        </div>
      )}
    </Tree>
  );
}
```

### API Client

```typescript
// src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token (if needed)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

```typescript
// src/api/orders.api.ts
import api from './client';
import type { OrderSummary, OrderHeader, DateFilter } from '../types';

export async function getOrders(filters: DateFilter = {}): Promise<OrderSummary[]> {
  const params = new URLSearchParams();

  if (filters.startDate) {
    params.set('startDate', filters.startDate.toISOString());
  }
  if (filters.endDate) {
    params.set('endDate', filters.endDate.toISOString());
  }
  if (filters.customer) {
    params.set('customer', filters.customer);
  }
  if (filters.limit) {
    params.set('limit', filters.limit.toString());
  }

  const { data } = await api.get(`/orders?${params}`);
  return data.data;
}

export async function getOrderByJobNumber(jobNumber: string): Promise<OrderHeader> {
  const { data } = await api.get(`/orders/${encodeURIComponent(jobNumber)}`);
  return data.data;
}

export async function getOrderReport(
  jobNumber: string,
  format: 'html' | 'pdf' = 'html'
): Promise<Blob> {
  const { data } = await api.get(
    `/orders/${encodeURIComponent(jobNumber)}/report`,
    {
      params: { format },
      responseType: 'blob',
    }
  );
  return data;
}
```

---

## Service Layer Migration

### Order Service

#### Python (Current)
```python
# services/order_service.py
class OrderService:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def load_recent_orders(self, limit: int = 100) -> list[OrderSummary]:
        cursor = self._connection.get_cursor()
        return get_recent_orders(cursor, limit)

    def filter_by_date_range(self, date_filter: DateRangeFilter) -> list[OrderSummary]:
        cursor = self._connection.get_cursor()
        return filter_orders_by_date_range(
            cursor,
            date_filter.start_date,
            date_filter.end_date,
            date_filter.limit
        )
```

#### Express (Target)
```typescript
// src/services/order.service.ts
import * as orderQueries from '../database/queries/order.queries';
import type { OrderSummary, OrderHeader, DateRangeFilter } from '../database/models/order.model';

export async function getRecentOrders(limit: number = 100): Promise<OrderSummary[]> {
  return orderQueries.getRecentOrders(limit);
}

export async function filterByDateRange(
  filter: DateRangeFilter
): Promise<OrderSummary[]> {
  return orderQueries.filterOrdersByDateRange(
    filter.startDate,
    filter.endDate,
    filter.limit
  );
}

export async function getOrderByJobNumber(
  jobNumber: string
): Promise<OrderHeader | null> {
  // Validate input
  if (!jobNumber || jobNumber.length > 30) {
    throw new Error('Invalid job number');
  }

  return orderQueries.searchByJobNumber(jobNumber.toUpperCase());
}

export async function searchByCustomerName(
  customerName: string,
  limit: number = 100
): Promise<OrderSummary[]> {
  if (!customerName || customerName.length < 2) {
    throw new Error('Customer name must be at least 2 characters');
  }

  return orderQueries.searchByCustomerName(customerName, limit);
}
```

### Work Order Service

```typescript
// src/services/work-order.service.ts
import * as woQueries from '../database/queries/work-order.queries';
import type {
  WorkOrder,
  Operation,
  Requirement,
  LaborTicket,
  InventoryTransaction,
  WIPBalance,
} from '../database/models/work-order.model';

export class WorkOrderNotFoundError extends Error {
  constructor(baseId: string, lotId: string, subId: string) {
    super(`Work order not found: ${baseId}-${lotId}-${subId}`);
    this.name = 'WorkOrderNotFoundError';
  }
}

export async function searchWorkOrders(
  baseIdPattern: string,
  limit: number = 100
): Promise<WorkOrder[]> {
  if (!baseIdPattern || baseIdPattern.length < 2) {
    throw new Error('Base ID pattern must be at least 2 characters');
  }

  return woQueries.searchWorkOrders(baseIdPattern.toUpperCase(), limit);
}

export async function getWorkOrderHeader(
  baseId: string,
  lotId: string,
  subId: string
): Promise<WorkOrder> {
  const header = await woQueries.getWorkOrderHeader(baseId, lotId, subId);

  if (!header) {
    throw new WorkOrderNotFoundError(baseId, lotId, subId);
  }

  return header;
}

// Lazy load endpoints
export async function getOperations(
  baseId: string,
  lotId: string,
  subId: string
): Promise<Operation[]> {
  return woQueries.getOperations(baseId, lotId, subId);
}

export async function getRequirements(
  baseId: string,
  lotId: string,
  subId: string,
  seqNo?: number
): Promise<Requirement[]> {
  return woQueries.getRequirements(baseId, lotId, subId, seqNo);
}

export async function getLaborTickets(
  baseId: string,
  lotId: string,
  subId: string
): Promise<LaborTicket[]> {
  return woQueries.getLaborTickets(baseId, lotId, subId);
}

export async function getInventoryTransactions(
  baseId: string,
  lotId: string,
  subId: string
): Promise<InventoryTransaction[]> {
  return woQueries.getInventoryTransactions(baseId, lotId, subId);
}

export async function getWIPBalance(
  baseId: string,
  lotId: string,
  subId: string
): Promise<WIPBalance | null> {
  return woQueries.getWIPBalance(baseId, lotId, subId);
}
```

---

## Authentication & Security

### Authentication Options

The current desktop application has no authentication (relies on network access). For the web version, consider:

#### Option 1: Windows Authentication (NTLM/Kerberos)
Best for: Internal network only, seamless SSO with Active Directory

```typescript
// Using passport-windowsauth
import passport from 'passport';
import WindowsStrategy from 'passport-windowsauth';

passport.use(new WindowsStrategy({
  ldap: {
    url: 'ldap://your-dc.company.local',
    base: 'DC=company,DC=local',
    bindDN: 'CN=service,CN=Users,DC=company,DC=local',
    bindCredentials: process.env.LDAP_PASSWORD,
  },
}, (profile, done) => {
  done(null, profile);
}));
```

#### Option 2: Basic Authentication
Best for: Simple internal tool, quick implementation

```typescript
// src/middleware/auth.ts
import { Request, Response, NextFunction } from 'express';

const VALID_USERS = new Map([
  ['spareparts', 'password123'],
  ['admin', 'adminpass'],
]);

export function basicAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Basic ')) {
    res.setHeader('WWW-Authenticate', 'Basic realm="Visual Order Lookup"');
    return res.status(401).json({ error: 'Authentication required' });
  }

  const base64Credentials = authHeader.split(' ')[1];
  const [username, password] = Buffer.from(base64Credentials, 'base64')
    .toString()
    .split(':');

  if (VALID_USERS.get(username) !== password) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  req.user = { username };
  next();
}
```

#### Option 3: JWT Tokens
Best for: Stateless authentication, API scalability

```typescript
// src/middleware/jwt-auth.ts
import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

export function jwtAuth(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: 'Token required' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}
```

### Security Considerations

```typescript
// src/app.ts
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';

const app = express();

// Security middleware
app.use(helmet());

// CORS configuration (restrict to internal network)
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173'],
  credentials: true,
}));

// Rate limiting
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Limit each IP to 1000 requests per window
  message: { error: 'Too many requests, please try again later' },
}));

// Body parsing with size limits
app.use(express.json({ limit: '1mb' }));

// Disable X-Powered-By header
app.disable('x-powered-by');
```

### SQL Injection Prevention

All queries should use parameterized statements (already implemented in query examples above):

```typescript
// GOOD - Parameterized query
const result = await request
  .input('jobNumber', sql.NVarChar, jobNumber)
  .query('SELECT * FROM CUSTOMER_ORDER WHERE ID = @jobNumber');

// BAD - String concatenation (NEVER do this)
const result = await request.query(`SELECT * FROM CUSTOMER_ORDER WHERE ID = '${jobNumber}'`);
```

---

## Configuration Management

### Environment Variables

```bash
# .env.example

# Server Configuration
PORT=3000
NODE_ENV=development

# Database Configuration
DB_SERVER=10.10.10.142
DB_PORT=1433
DB_NAME=SAMCO
DB_USER=sa
DB_PASSWORD=your_password

# Connection Pool
DB_POOL_MIN=2
DB_POOL_MAX=10
DB_POOL_IDLE_TIMEOUT=30000
DB_CONNECTION_TIMEOUT=10000
DB_REQUEST_TIMEOUT=30000

# Authentication (choose one)
AUTH_TYPE=basic  # basic, jwt, windows
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRES_IN=8h

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://internal-server.local

# Logging
LOG_LEVEL=info
LOG_FORMAT=combined

# Application
APP_NAME=Visual Order Lookup
```

### Configuration Module

```typescript
// src/config/environment.ts
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3000'),
  nodeEnv: process.env.NODE_ENV || 'development',

  database: {
    server: process.env.DB_SERVER || '10.10.10.142',
    port: parseInt(process.env.DB_PORT || '1433'),
    database: process.env.DB_NAME || 'SAMCO',
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    pool: {
      min: parseInt(process.env.DB_POOL_MIN || '2'),
      max: parseInt(process.env.DB_POOL_MAX || '10'),
      idleTimeoutMillis: parseInt(process.env.DB_POOL_IDLE_TIMEOUT || '30000'),
    },
    connectionTimeout: parseInt(process.env.DB_CONNECTION_TIMEOUT || '10000'),
    requestTimeout: parseInt(process.env.DB_REQUEST_TIMEOUT || '30000'),
  },

  auth: {
    type: process.env.AUTH_TYPE || 'basic',
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '8h',
  },

  cors: {
    origins: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173'],
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
  },

  app: {
    name: process.env.APP_NAME || 'Visual Order Lookup',
  },
};

// Validate required configuration
export function validateConfig(): void {
  const required = ['DB_USER', 'DB_PASSWORD'];
  const missing = required.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}
```

---

## Testing Strategy

### Backend Testing

```typescript
// tests/integration/routes/orders.test.ts
import request from 'supertest';
import app from '../../../src/app';
import { getPool, closePool } from '../../../src/database/connection';

describe('Orders API', () => {
  beforeAll(async () => {
    await getPool(); // Ensure connection
  });

  afterAll(async () => {
    await closePool();
  });

  describe('GET /api/orders', () => {
    it('should return recent orders', async () => {
      const response = await request(app)
        .get('/api/orders')
        .expect(200);

      expect(response.body.data).toBeInstanceOf(Array);
      expect(response.body.data.length).toBeLessThanOrEqual(100);
    });

    it('should filter by date range', async () => {
      const response = await request(app)
        .get('/api/orders')
        .query({
          startDate: '2024-01-01',
          endDate: '2024-12-31',
        })
        .expect(200);

      expect(response.body.data).toBeInstanceOf(Array);
    });
  });

  describe('GET /api/orders/:jobNumber', () => {
    it('should return order details', async () => {
      const response = await request(app)
        .get('/api/orders/TEST123')
        .expect(200);

      expect(response.body.data).toHaveProperty('jobNumber');
      expect(response.body.data).toHaveProperty('customer');
      expect(response.body.data).toHaveProperty('lineItems');
    });

    it('should return 404 for non-existent order', async () => {
      const response = await request(app)
        .get('/api/orders/NONEXISTENT999')
        .expect(404);

      expect(response.body.error).toBe('Order not found');
    });
  });
});
```

```typescript
// tests/unit/services/order.service.test.ts
import * as orderService from '../../../src/services/order.service';
import * as orderQueries from '../../../src/database/queries/order.queries';

jest.mock('../../../src/database/queries/order.queries');

describe('OrderService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getRecentOrders', () => {
    it('should call query with correct limit', async () => {
      const mockOrders = [{ jobNumber: 'TEST1', customerName: 'Test' }];
      (orderQueries.getRecentOrders as jest.Mock).mockResolvedValue(mockOrders);

      const result = await orderService.getRecentOrders(50);

      expect(orderQueries.getRecentOrders).toHaveBeenCalledWith(50);
      expect(result).toEqual(mockOrders);
    });
  });

  describe('getOrderByJobNumber', () => {
    it('should uppercase job number', async () => {
      (orderQueries.searchByJobNumber as jest.Mock).mockResolvedValue(null);

      await orderService.getOrderByJobNumber('test123');

      expect(orderQueries.searchByJobNumber).toHaveBeenCalledWith('TEST123');
    });

    it('should throw for invalid job number', async () => {
      await expect(
        orderService.getOrderByJobNumber('')
      ).rejects.toThrow('Invalid job number');
    });
  });
});
```

### Frontend Testing

```tsx
// src/components/sales/__tests__/OrderList.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OrderList } from '../OrderList';

const mockOrders = [
  {
    jobNumber: 'JOB001',
    customerName: 'ACME Corp',
    poNumber: 'PO123',
    orderDate: new Date('2024-01-15'),
    totalAmount: 1500.00,
  },
  {
    jobNumber: 'JOB002',
    customerName: 'Widget Inc',
    poNumber: 'PO456',
    orderDate: new Date('2024-01-16'),
    totalAmount: 2500.00,
  },
];

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('OrderList', () => {
  it('renders order data in table', () => {
    render(
      <OrderList
        orders={mockOrders}
        loading={false}
        selectedJob={null}
        onSelect={jest.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByText('JOB001')).toBeInTheDocument();
    expect(screen.getByText('ACME Corp')).toBeInTheDocument();
    expect(screen.getByText('JOB002')).toBeInTheDocument();
  });

  it('calls onSelect when row clicked', () => {
    const onSelect = jest.fn();

    render(
      <OrderList
        orders={mockOrders}
        loading={false}
        selectedJob={null}
        onSelect={onSelect}
      />,
      { wrapper }
    );

    fireEvent.click(screen.getByText('JOB001'));

    expect(onSelect).toHaveBeenCalledWith('JOB001');
  });

  it('shows loading spinner when loading', () => {
    render(
      <OrderList
        orders={[]}
        loading={true}
        selectedJob={null}
        onSelect={jest.fn()}
      />,
      { wrapper }
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

---

## Deployment

### Docker Configuration

```dockerfile
# Dockerfile (Backend)
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Install ODBC drivers for SQL Server
RUN apk add --no-cache \
    unixodbc \
    unixodbc-dev \
    freetds \
    freetds-dev

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/templates ./templates

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

USER node

CMD ["node", "dist/index.js"]
```

```dockerfile
# Dockerfile (Frontend)
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production image with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: ./visual-order-lookup-api
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_SERVER=10.10.10.142
      - DB_PORT=1433
      - DB_NAME=SAMCO
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: ./visual-order-lookup-web
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api
    restart: unless-stopped

networks:
  default:
    driver: bridge
```

### PM2 Configuration (Alternative)

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'visual-order-lookup-api',
      script: './dist/index.js',
      instances: 'max',
      exec_mode: 'cluster',
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      error_file: './logs/error.log',
      out_file: './logs/out.log',
      merge_logs: true,
      time: true,
    },
  ],
};
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name visual-orders.internal;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://api:3000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health {
        proxy_pass http://api:3000/health;
    }
}
```

---

## Migration Phases

### Phase 1: Backend API (Weeks 1-2)

**Goals**: Create Express API with all endpoints

**Tasks**:
1. Set up Express project with TypeScript
2. Implement database connection pool
3. Migrate models to TypeScript interfaces
4. Implement order queries and service
5. Implement part queries and service
6. Implement work order queries and service
7. Create API routes
8. Add error handling middleware
9. Write integration tests
10. Create Docker configuration

**Deliverables**:
- Working REST API
- API documentation (OpenAPI/Swagger)
- Integration test suite

### Phase 2: Frontend Foundation (Weeks 3-4)

**Goals**: Create React application shell with navigation

**Tasks**:
1. Set up React project with Vite
2. Configure React Query for data fetching
3. Implement layout and navigation
4. Create API client module
5. Implement Sales module (list + detail)
6. Add date filtering and search
7. Style with CSS/Tailwind

**Deliverables**:
- Working Sales module
- Navigation between modules
- Basic styling

### Phase 3: Inventory & Engineering Modules (Weeks 5-6)

**Goals**: Complete remaining modules

**Tasks**:
1. Implement Inventory module (search + 3 tabs)
2. Implement Engineering module with tree view
3. Add cross-module navigation
4. Implement lazy loading for trees
5. Add export functionality (CSV, PDF)
6. Write component tests

**Deliverables**:
- Complete Inventory module
- Complete Engineering module
- Export capabilities

### Phase 4: Authentication & Security (Week 7)

**Goals**: Add authentication and security hardening

**Tasks**:
1. Choose authentication method
2. Implement auth middleware
3. Add login page (if needed)
4. Configure CORS properly
5. Add rate limiting
6. Security audit
7. Penetration testing

**Deliverables**:
- Secure authentication
- Security documentation

### Phase 5: Deployment & Testing (Week 8)

**Goals**: Production-ready deployment

**Tasks**:
1. Set up production environment
2. Configure CI/CD pipeline
3. Performance testing
4. Load testing
5. User acceptance testing
6. Documentation
7. Training materials

**Deliverables**:
- Production deployment
- CI/CD pipeline
- User documentation

---

## Appendix: Component Mapping

| Python Component | Express Equivalent | React Component |
|-----------------|-------------------|-----------------|
| `main.py` | `src/index.ts` | `src/main.tsx` |
| `MainWindow` | Express app | `App.tsx` |
| `NavigationPanel` | N/A | `Navigation.tsx` |
| `SalesModule` | `/api/orders/*` | `SalesModule.tsx` |
| `OrderListView` | `GET /api/orders` | `OrderList.tsx` |
| `OrderDetailView` | `GET /api/orders/:id` | `OrderDetail.tsx` |
| `SearchPanel` | Query params | `SearchPanel.tsx` |
| `InventoryModule` | `/api/parts/*` | `InventoryModule.tsx` |
| `PartSearchPanel` | Query params | `PartSearch.tsx` |
| `PartDetailView` | Multiple endpoints | `PartDetail.tsx` |
| `EngineeringModule` | `/api/work-orders/*` | `EngineeringModule.tsx` |
| `WorkOrderTreeWidget` | `/api/bom/*` | `WorkOrderTree.tsx` |
| `DatabaseConnection` | `connection.ts` | N/A (backend only) |
| `OrderService` | `order.service.ts` | React Query hooks |
| `PartService` | `part.service.ts` | React Query hooks |
| `WorkOrderService` | `work-order.service.ts` | React Query hooks |
| `ReportService` | `report.service.ts` | PDF.js / Print CSS |
| `LoadingDialog` | N/A | `LoadingSpinner.tsx` |
| `ErrorHandler` | Error middleware | `ErrorBoundary.tsx` |

---

## Quick Reference: Key Files to Create

### Backend (Priority Order)
1. `src/database/connection.ts`
2. `src/database/models/*.ts`
3. `src/database/queries/*.ts`
4. `src/services/*.ts`
5. `src/routes/*.ts`
6. `src/middleware/error-handler.ts`
7. `src/app.ts`
8. `src/index.ts`

### Frontend (Priority Order)
1. `src/api/client.ts`
2. `src/api/*.api.ts`
3. `src/types/index.ts`
4. `src/components/common/Layout.tsx`
5. `src/components/common/Navigation.tsx`
6. `src/components/sales/*.tsx`
7. `src/components/inventory/*.tsx`
8. `src/components/engineering/*.tsx`

---

*Document Version: 1.0*
*Last Updated: December 2024*
