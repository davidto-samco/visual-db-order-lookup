# Express Migration Quick Start Guide

This guide helps you quickly set up the new Express.js backend and React frontend for the Visual Order Lookup application.

## Prerequisites

- Node.js 20 LTS or higher
- npm or yarn
- Access to SQL Server database (10.10.10.142)
- Git

## Backend Setup

### 1. Create Project

```bash
# Create directory
mkdir visual-order-lookup-api
cd visual-order-lookup-api

# Initialize Node.js project
npm init -y

# Install dependencies
npm install express mssql dotenv cors helmet express-rate-limit winston

# Install dev dependencies
npm install -D typescript ts-node nodemon @types/node @types/express @types/cors jest ts-jest @types/jest supertest @types/supertest eslint prettier
```

### 2. Configure TypeScript

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 3. Create Directory Structure

```bash
mkdir -p src/{config,database/{models,queries},services,routes,middleware,utils,types}
mkdir -p tests/{unit,integration}
```

### 4. Create Environment File

Create `.env`:

```bash
# Server
PORT=3000
NODE_ENV=development

# Database
DB_SERVER=10.10.10.142
DB_PORT=1433
DB_NAME=SAMCO
DB_USER=sa
DB_PASSWORD=your_password_here

# Pool settings
DB_POOL_MIN=2
DB_POOL_MAX=10

# CORS
ALLOWED_ORIGINS=http://localhost:5173
```

### 5. Create Core Files

**src/config/database.ts**
```typescript
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
    min: parseInt(process.env.DB_POOL_MIN || '2'),
    max: parseInt(process.env.DB_POOL_MAX || '10'),
    idleTimeoutMillis: 30000,
  },
  connectionTimeout: 10000,
  requestTimeout: 30000,
};

let pool: sql.ConnectionPool | null = null;

export async function getPool(): Promise<sql.ConnectionPool> {
  if (!pool) {
    pool = await sql.connect(config);
    console.log('Database connected');
  }
  return pool;
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.close();
    pool = null;
  }
}
```

**src/app.ts**
```typescript
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import routes from './routes';
import { errorHandler } from './middleware/error-handler';

const app = express();

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173'],
  credentials: true,
}));
app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 1000,
}));

// Body parsing
app.use(express.json({ limit: '1mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api', routes);

// Error handling
app.use(errorHandler);

export default app;
```

**src/index.ts**
```typescript
import 'dotenv/config';
import app from './app';
import { getPool, closePool } from './config/database';

const PORT = process.env.PORT || 3000;

async function start() {
  try {
    // Connect to database
    await getPool();

    // Start server
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down...');
  await closePool();
  process.exit(0);
});

start();
```

**src/middleware/error-handler.ts**
```typescript
import { Request, Response, NextFunction } from 'express';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  console.error('Error:', err);

  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: err.message,
      code: 'VALIDATION_ERROR',
    });
  }

  if (err.name === 'NotFoundError') {
    return res.status(404).json({
      error: err.message,
      code: 'NOT_FOUND',
    });
  }

  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR',
  });
}
```

**src/routes/index.ts**
```typescript
import { Router } from 'express';
import orderRoutes from './order.routes';
// import partRoutes from './part.routes';
// import workOrderRoutes from './work-order.routes';

const router = Router();

router.use('/orders', orderRoutes);
// router.use('/parts', partRoutes);
// router.use('/work-orders', workOrderRoutes);

export default router;
```

**src/routes/order.routes.ts**
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import * as orderService from '../services/order.service';

const router = Router();

router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const orders = await orderService.getRecentOrders(limit);
    res.json({ data: orders });
  } catch (error) {
    next(error);
  }
});

router.get('/:jobNumber', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const order = await orderService.getOrderByJobNumber(req.params.jobNumber);
    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }
    res.json({ data: order });
  } catch (error) {
    next(error);
  }
});

export default router;
```

**src/services/order.service.ts**
```typescript
import { getPool } from '../config/database';

export interface OrderSummary {
  jobNumber: string;
  customerName: string;
  poNumber: string | null;
  orderDate: Date | null;
  totalAmount: number | null;
}

export async function getRecentOrders(limit: number = 100): Promise<OrderSummary[]> {
  const pool = await getPool();
  const result = await pool.request()
    .input('limit', limit)
    .query(`
      SELECT TOP (@limit)
        co.ID AS jobNumber,
        c.NAME AS customerName,
        co.CUSTOMER_PO_REF AS poNumber,
        co.ORDER_DATE AS orderDate,
        co.TOTAL_AMT_ORDERED AS totalAmount
      FROM CUSTOMER_ORDER co
      LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
      ORDER BY co.ORDER_DATE DESC, co.ID DESC
    `);

  return result.recordset.map(row => ({
    jobNumber: row.jobNumber,
    customerName: row.customerName || 'Unknown',
    poNumber: row.poNumber,
    orderDate: row.orderDate,
    totalAmount: row.totalAmount,
  }));
}

export async function getOrderByJobNumber(jobNumber: string): Promise<any | null> {
  const pool = await getPool();
  const result = await pool.request()
    .input('jobNumber', jobNumber.toUpperCase())
    .query(`
      SELECT
        co.ID AS jobNumber,
        co.ORDER_DATE AS orderDate,
        co.CUSTOMER_PO_REF AS poNumber,
        c.NAME AS customerName,
        co.TOTAL_AMT_ORDERED AS totalAmount
      FROM CUSTOMER_ORDER co
      LEFT JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
      WHERE co.ID = @jobNumber
    `);

  if (result.recordset.length === 0) {
    return null;
  }

  return result.recordset[0];
}
```

### 6. Add Package Scripts

Update `package.json`:

```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "lint": "eslint src --ext .ts"
  }
}
```

### 7. Start Development Server

```bash
npm run dev
```

Test the API:
```bash
curl http://localhost:3000/health
curl http://localhost:3000/api/orders
```

---

## Frontend Setup

### 1. Create React Project

```bash
# Create Vite React project
npm create vite@latest visual-order-lookup-web -- --template react-ts
cd visual-order-lookup-web

# Install dependencies
npm install @tanstack/react-query axios react-router-dom

# Install UI framework (choose one)
npm install @mui/material @emotion/react @emotion/styled
# OR
npm install tailwindcss postcss autoprefixer
```

### 2. Configure Environment

Create `.env`:

```bash
VITE_API_URL=http://localhost:3000/api
```

### 3. Set Up API Client

**src/api/client.ts**
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
```

**src/api/orders.ts**
```typescript
import api from './client';

export interface OrderSummary {
  jobNumber: string;
  customerName: string;
  poNumber: string | null;
  orderDate: string | null;
  totalAmount: number | null;
}

export async function getOrders(limit?: number): Promise<OrderSummary[]> {
  const { data } = await api.get('/orders', { params: { limit } });
  return data.data;
}

export async function getOrderByJobNumber(jobNumber: string) {
  const { data } = await api.get(`/orders/${encodeURIComponent(jobNumber)}`);
  return data.data;
}
```

### 4. Set Up React Query

**src/main.tsx**
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

### 5. Create Basic Components

**src/App.tsx**
```typescript
import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import SalesModule from './components/SalesModule';
import InventoryModule from './components/InventoryModule';
import EngineeringModule from './components/EngineeringModule';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="nav-sidebar">
          <h1>Visual Order Lookup</h1>
          <ul>
            <li><NavLink to="/">Sales</NavLink></li>
            <li><NavLink to="/inventory">Inventory</NavLink></li>
            <li><NavLink to="/engineering">Engineering</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SalesModule />} />
            <Route path="/inventory" element={<InventoryModule />} />
            <Route path="/engineering" element={<EngineeringModule />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

**src/components/SalesModule.tsx**
```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getOrders, getOrderByJobNumber, OrderSummary } from '../api/orders';

export default function SalesModule() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: ['orders'],
    queryFn: () => getOrders(100),
  });

  const orderDetailQuery = useQuery({
    queryKey: ['order', selectedJob],
    queryFn: () => getOrderByJobNumber(selectedJob!),
    enabled: !!selectedJob,
  });

  return (
    <div className="sales-module">
      <h2>Sales Orders</h2>

      {ordersQuery.isLoading && <p>Loading orders...</p>}
      {ordersQuery.error && <p>Error loading orders</p>}

      <div className="content-grid">
        <div className="order-list">
          <table>
            <thead>
              <tr>
                <th>Job #</th>
                <th>Customer</th>
                <th>PO</th>
                <th>Date</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {ordersQuery.data?.map((order) => (
                <tr
                  key={order.jobNumber}
                  onClick={() => setSelectedJob(order.jobNumber)}
                  className={selectedJob === order.jobNumber ? 'selected' : ''}
                >
                  <td>{order.jobNumber}</td>
                  <td>{order.customerName}</td>
                  <td>{order.poNumber || '-'}</td>
                  <td>{order.orderDate ? new Date(order.orderDate).toLocaleDateString() : '-'}</td>
                  <td>{order.totalAmount?.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selectedJob && (
          <div className="order-detail">
            <h3>Order Details: {selectedJob}</h3>
            {orderDetailQuery.isLoading && <p>Loading...</p>}
            {orderDetailQuery.data && (
              <pre>{JSON.stringify(orderDetailQuery.data, null, 2)}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**src/components/InventoryModule.tsx**
```typescript
export default function InventoryModule() {
  return (
    <div className="inventory-module">
      <h2>Inventory</h2>
      <p>Part search and details coming soon...</p>
    </div>
  );
}
```

**src/components/EngineeringModule.tsx**
```typescript
export default function EngineeringModule() {
  return (
    <div className="engineering-module">
      <h2>Engineering</h2>
      <p>Work order hierarchy coming soon...</p>
    </div>
  );
}
```

### 6. Add Basic Styles

**src/index.css**
```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
}

.app {
  display: flex;
  min-height: 100vh;
}

.nav-sidebar {
  width: 200px;
  background: #1976d2;
  color: white;
  padding: 1rem;
}

.nav-sidebar h1 {
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
}

.nav-sidebar ul {
  list-style: none;
}

.nav-sidebar a {
  display: block;
  color: white;
  text-decoration: none;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.nav-sidebar a:hover,
.nav-sidebar a.active {
  background: rgba(255, 255, 255, 0.2);
}

.main-content {
  flex: 1;
  padding: 1.5rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

th {
  background: #f5f5f5;
  font-weight: 600;
}

tr:hover {
  background: #f5f5f5;
  cursor: pointer;
}

tr.selected {
  background: #e3f2fd;
}

.order-detail {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.order-detail pre {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow: auto;
  font-size: 0.875rem;
}
```

### 7. Start Development

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Next Steps

After the basic setup is working:

1. **Complete backend routes** - Add part and work order endpoints
2. **Add authentication** - Choose and implement auth strategy
3. **Build out UI** - Complete all three modules
4. **Add tests** - Unit and integration tests
5. **Configure deployment** - Docker, CI/CD pipeline
6. **Performance optimization** - Caching, lazy loading

See the main [EXPRESS_MIGRATION_GUIDE.md](./EXPRESS_MIGRATION_GUIDE.md) for detailed implementation guidance.

---

## Troubleshooting

### Database Connection Issues

```bash
# Test SQL Server connectivity
telnet 10.10.10.142 1433

# Check ODBC drivers (for mssql package)
npm install msnodesqlv8  # Windows native driver alternative
```

### CORS Errors

Ensure the frontend URL is in `ALLOWED_ORIGINS`:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### TypeScript Errors

```bash
# Rebuild TypeScript
npm run build

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

*Document Version: 1.0*
*Last Updated: December 2024*
