# 07 - Implementation Roadmap

## Overview

This document provides a step-by-step guide for implementing the Express backend. Follow these phases in order for a structured approach.

---

## Phase 1: Project Setup

### 1.1 Initialize Node.js Project

```bash
# Create server directory
mkdir server
cd server

# Initialize package.json
npm init -y

# Install production dependencies
npm install express mssql cors helmet compression dotenv winston express-validator http-status-codes

# Install development dependencies
npm install -D nodemon jest supertest eslint
```

### 1.2 Create Directory Structure

```bash
mkdir -p src/{config,database/queries,models,services,controllers,routes,middleware,utils}
mkdir -p tests/{unit,integration}
touch src/index.js src/app.js
```

### 1.3 Configure Environment

Create `.env`:
```env
NODE_ENV=development
PORT=3001
DB_SERVER=10.10.10.142
DB_PORT=1433
DB_DATABASE=SAMCO
DB_USER=sa
DB_PASSWORD=your_password
CORS_ORIGIN=http://localhost:3000
LOG_LEVEL=debug
```

### 1.4 Add NPM Scripts

Update `package.json`:
```json
{
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "lint": "eslint src/**/*.js"
  }
}
```

### Verification Checkpoint
- [ ] `npm run dev` starts without errors
- [ ] ESLint passes

---

## Phase 2: Core Infrastructure

### 2.1 Configuration Module

Create `src/config/index.js` with database and app configuration.

### 2.2 Logger Setup

Create `src/utils/logger.js` with Winston configuration.

### 2.3 Database Connection

Create `src/database/connection.js` with:
- Connection pool initialization
- Retry logic (3 attempts, 2-second delays)
- Health check query
- Graceful shutdown

### 2.4 Error Classes

Create `src/utils/errors.js` with custom error hierarchy.

### 2.5 Express App Setup

Create `src/app.js` with middleware stack:
- Helmet (security)
- CORS
- Compression
- JSON body parser
- Request logging

Create `src/index.js` with server startup and graceful shutdown.

### Verification Checkpoint
- [ ] Server starts and connects to database
- [ ] Health endpoint returns `{ status: "healthy" }`
- [ ] Database connection error is handled gracefully

---

## Phase 3: Orders Module (Sales)

### 3.1 Order Queries

Create `src/database/queries/order.queries.js`:
- `getRecentOrders(limit)`
- `getOrdersByDateRange(startDate, endDate, limit)`
- `getOrderByJobNumber(jobNumber)`
- `getOrderLineItems(jobNumber)`
- `searchByCustomerName(name, startDate, endDate, limit)`

### 3.2 Order Transformers

Add to `src/models/transformers.js`:
- `toOrderSummary(row)`
- `toOrderHeader(row)`
- `toOrderLineItem(row)`

### 3.3 Order Service

Create `src/services/order.service.js`:
- Implement all business logic functions
- Add input validation
- Transform database rows to response objects

### 3.4 Order Controller

Create `src/controllers/order.controller.js`:
- Handle request/response
- Call service functions
- Format API responses

### 3.5 Order Routes

Create `src/routes/order.routes.js`:
- `GET /orders/recent`
- `GET /orders/search`
- `GET /orders/:jobNumber`
- `GET /orders/:jobNumber/lines`

### 3.6 Integration

Wire up routes in `src/routes/index.js` and `src/app.js`.

### Verification Checkpoint
Test each endpoint:
- [ ] `GET /api/v1/orders/recent?limit=10` returns orders
- [ ] `GET /api/v1/orders/search?customer=TEST` returns filtered results
- [ ] `GET /api/v1/orders/{validJobNumber}` returns order details
- [ ] `GET /api/v1/orders/{invalidJobNumber}` returns 404
- [ ] `GET /api/v1/orders/{jobNumber}/lines` returns line items

---

## Phase 4: Parts Module (Inventory)

### 4.1 Part Queries

Create `src/database/queries/part.queries.js`:
- `getPartByNumber(partNumber)`
- `searchParts(pattern, limit)`
- `getWhereUsed(partNumber, limit)`
- `getPurchaseHistory(partNumber, limit)`

### 4.2 Part Transformers

Add to `src/models/transformers.js`:
- `toPart(row)`
- `toWhereUsed(row)`
- `toPurchaseHistory(row)`

### 4.3 Part Service

Create `src/services/part.service.js`:
- Implement all functions
- Handle case-insensitive part numbers (uppercase)

### 4.4 Part Controller & Routes

Create controller and routes:
- `GET /parts/search`
- `GET /parts/:partNumber`
- `GET /parts/:partNumber/where-used`
- `GET /parts/:partNumber/purchase-history`

### Verification Checkpoint
- [ ] `GET /api/v1/parts/search?q=WIDGET` returns matching parts
- [ ] `GET /api/v1/parts/{validPartNumber}` returns part details
- [ ] `GET /api/v1/parts/{partNumber}/where-used` returns usage data
- [ ] `GET /api/v1/parts/{partNumber}/purchase-history` returns PO history

---

## Phase 5: Work Orders Module (Engineering)

### 5.1 Work Order Queries

Create `src/database/queries/workorder.queries.js`:
- `searchWorkOrders(baseIdPattern, limit)`
- `getWorkOrderHeader(baseId, lotId, subId)`
- `getOperations(baseId, lotId, subId)`
- `getRequirements(baseId, lotId, subId, operationSeqNo?)`
- `getLaborTickets(baseId, lotId, subId)`
- `getInventoryTransactions(baseId, lotId, subId)`
- `getWIPBalance(baseId, lotId, subId)`
- `getWorkOrderHierarchy(baseId, lotId, subId)` - recursive CTE

### 5.2 Work Order Transformers

Add to `src/models/transformers.js`:
- `toWorkOrder(row)`
- `toWorkOrderHeader(row)`
- `toOperation(row)`
- `toRequirement(row)`
- `toLaborTicket(row)`
- `toInventoryTransaction(row)`
- `toWIPBalance(row)`

### 5.3 Work Order Service

Create `src/services/workorder.service.js`:
- Handle composite key validation
- Support lazy loading pattern

### 5.4 Work Order Controller & Routes

Create controller and routes:
- `GET /workorders/search`
- `GET /workorders/:baseId/:lotId/:subId`
- `GET /workorders/:baseId/:lotId/:subId/operations`
- `GET /workorders/:baseId/:lotId/:subId/requirements`
- `GET /workorders/:baseId/:lotId/:subId/labor`
- `GET /workorders/:baseId/:lotId/:subId/inventory`
- `GET /workorders/:baseId/:lotId/:subId/wip`
- `GET /workorders/:baseId/:lotId/:subId/hierarchy`

### Verification Checkpoint
- [ ] `GET /api/v1/workorders/search?baseId=WO123` returns work orders
- [ ] `GET /api/v1/workorders/WO123/1/0` returns header with counts
- [ ] Lazy load endpoints return correct data
- [ ] Hierarchy endpoint returns recursive tree

---

## Phase 6: Validation & Error Handling

### 6.1 Request Validation

Create validation chains for all endpoints using express-validator:
- Path parameters
- Query parameters
- Date formats
- Numeric ranges

### 6.2 Error Middleware

Implement global error handler:
- Map AppError to HTTP responses
- Handle database errors
- Include stack traces in development

### 6.3 Response Formatting

Ensure consistent response format:
- Success wrapper with data and meta
- Error wrapper with code and message
- Formatted display values

### Verification Checkpoint
- [ ] Invalid date format returns 400 with clear message
- [ ] Missing required params return 400
- [ ] Not found returns 404 with resource info
- [ ] Database errors return 500/503

---

## Phase 7: Testing

### 7.1 Unit Tests

Create tests for:
- Services (mock database queries)
- Transformers (row to model)
- Formatters (date, currency)
- Validators

### 7.2 Integration Tests

Create tests for:
- Full request/response cycles
- Database connection handling
- Error scenarios

### 7.3 Test Configuration

Set up Jest configuration in `package.json`:
```json
{
  "jest": {
    "testEnvironment": "node",
    "coverageDirectory": "coverage",
    "collectCoverageFrom": ["src/**/*.js"]
  }
}
```

### Verification Checkpoint
- [ ] All unit tests pass
- [ ] Integration tests with test database pass
- [ ] Code coverage > 80%

---

## Phase 8: Documentation & Polish

### 8.1 API Documentation

Consider adding Swagger/OpenAPI:
```bash
npm install swagger-ui-express swagger-jsdoc
```

### 8.2 Health Endpoints

Enhance health check:
- `/health` - Basic health
- `/health/db` - Database connectivity

### 8.3 Performance

- Verify query performance
- Add query timing logs
- Consider caching for master data

### Verification Checkpoint
- [ ] API documentation accessible
- [ ] Health endpoints work
- [ ] Response times acceptable

---

## Implementation Order Summary

```
Phase 1: Project Setup (Foundation)
    └── Phase 2: Core Infrastructure
            └── Phase 3: Orders Module
                    └── Phase 4: Parts Module
                            └── Phase 5: Work Orders Module
                                    └── Phase 6: Validation & Error Handling
                                            └── Phase 7: Testing
                                                    └── Phase 8: Documentation
```

---

## Key Files Checklist

### Configuration
- [ ] `src/config/index.js`
- [ ] `.env`
- [ ] `package.json`
- [ ] `.eslintrc.js`

### Core
- [ ] `src/index.js`
- [ ] `src/app.js`
- [ ] `src/database/connection.js`
- [ ] `src/utils/logger.js`
- [ ] `src/utils/errors.js`
- [ ] `src/utils/formatters.js`

### Models
- [ ] `src/models/constants.js`
- [ ] `src/models/transformers.js`
- [ ] `src/models/index.js`

### Database Queries
- [ ] `src/database/queries/order.queries.js`
- [ ] `src/database/queries/part.queries.js`
- [ ] `src/database/queries/workorder.queries.js`

### Services
- [ ] `src/services/order.service.js`
- [ ] `src/services/part.service.js`
- [ ] `src/services/workorder.service.js`
- [ ] `src/services/index.js`

### Controllers
- [ ] `src/controllers/order.controller.js`
- [ ] `src/controllers/part.controller.js`
- [ ] `src/controllers/workorder.controller.js`
- [ ] `src/controllers/index.js`

### Routes
- [ ] `src/routes/order.routes.js`
- [ ] `src/routes/part.routes.js`
- [ ] `src/routes/workorder.routes.js`
- [ ] `src/routes/index.js`

### Middleware
- [ ] `src/middleware/error.middleware.js`
- [ ] `src/middleware/validation.middleware.js`
- [ ] `src/middleware/validators.js`
- [ ] `src/middleware/logging.middleware.js`

---

## Migration Notes from Python

### Code Reuse Potential

| Component | Reuse Level | Notes |
|-----------|-------------|-------|
| SQL Queries | ~95% | Minor syntax adjustments for mssql package |
| Business Logic | ~90% | Same patterns, different syntax |
| Data Models | ~80% | Plain objects instead of dataclasses |
| Error Handling | ~70% | Different exception hierarchy |
| Configuration | ~60% | Same .env pattern |
| UI Layer | 0% | Completely replaced by React |

### Key Differences

1. **Async Model**: Express uses promises/async-await vs Python's threading
2. **Module System**: CommonJS `require()` vs Python imports
3. **Connection Pool**: mssql pool vs single pyodbc connection
4. **Error Propagation**: Middleware-based vs try/catch blocks
5. **Data Transformation**: Explicit transformer functions vs constructor logic

### Testing Strategy

When implementing, you can validate against the existing Python application:
1. Run both applications simultaneously
2. Make equivalent API calls
3. Compare response data structures
4. Verify formatting matches
