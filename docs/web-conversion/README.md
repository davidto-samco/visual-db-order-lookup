# Visual DB Order Lookup - Web Conversion Documentation

## Overview

This documentation covers the conversion of the Visual DB Order Lookup desktop application (Python/PyQt6) to a web application with:

- **Backend**: Express.js (Node.js)
- **Frontend**: React
- **Database**: SQL Server (existing Visual/SAMCO database - read-only access)

## Documentation Structure

| Document | Description |
|----------|-------------|
| [01-backend-architecture.md](./01-backend-architecture.md) | Express backend architecture and project structure |
| [02-database-layer.md](./02-database-layer.md) | SQL Server connectivity, connection pooling, query patterns |
| [03-api-endpoints.md](./03-api-endpoints.md) | REST API endpoint specifications |
| [04-data-models.md](./04-data-models.md) | TypeScript interfaces and JSON response schemas |
| [05-service-layer.md](./05-service-layer.md) | Business logic migration from Python to TypeScript |
| [06-error-handling.md](./06-error-handling.md) | Error handling, logging, and HTTP status codes |
| [07-implementation-roadmap.md](./07-implementation-roadmap.md) | Step-by-step implementation guide |

## Quick Start

Once implemented, the backend will be started with:

```bash
cd server
npm install
npm run dev
```

The API will be available at `http://localhost:3001/api/v1/`

## Current Application Modules

The existing PyQt6 application has three modules that will be exposed via REST API:

1. **Sales Module** - Customer order lookup and management
2. **Inventory Module** - Part information and where-used analysis
3. **Engineering Module** - Work order hierarchy and manufacturing data

## Key Technical Decisions

### Why Express.js?

- Lightweight and flexible for REST API development
- Large ecosystem of middleware and libraries
- Easy integration with SQL Server via `mssql` or `tedious` packages
- TypeScript support for type safety
- Well-suited for read-only database operations

### Database Strategy

- **Read-only access** to existing Visual/SAMCO SQL Server database
- **Connection pooling** for efficient multi-request handling
- **WITH (NOLOCK)** hints preserved for query optimization
- Same ODBC connection string format supported

### API Design Principles

- RESTful endpoints following resource-based naming
- Support for pagination and lazy loading (critical for large hierarchies)
- JSON responses with consistent error format
- Composite key handling for work orders (BASE_ID/LOT_ID/SUB_ID)
