# Python to Express Migration Documentation

This directory contains comprehensive documentation for migrating the Visual Order Lookup application from a Python/PyQt6 desktop application to an Express.js web application.

## Documents

| Document | Description |
|----------|-------------|
| [EXPRESS_MIGRATION_GUIDE.md](./EXPRESS_MIGRATION_GUIDE.md) | Complete migration guide covering architecture, technology stack, code examples, and migration phases |
| [API_SPECIFICATION.yaml](./API_SPECIFICATION.yaml) | OpenAPI 3.0 specification for all REST API endpoints |
| [TYPESCRIPT_INTERFACES.ts](./TYPESCRIPT_INTERFACES.ts) | TypeScript interfaces for all data models |
| [DATABASE_SCHEMA_REFERENCE.md](./DATABASE_SCHEMA_REFERENCE.md) | SQL Server table documentation and query reference |
| [QUICKSTART.md](./QUICKSTART.md) | Quick setup guide for the Express backend and React frontend |

## Quick Start

1. Read the [EXPRESS_MIGRATION_GUIDE.md](./EXPRESS_MIGRATION_GUIDE.md) for a complete understanding of the migration
2. Follow [QUICKSTART.md](./QUICKSTART.md) to set up the development environment
3. Reference [API_SPECIFICATION.yaml](./API_SPECIFICATION.yaml) for API design
4. Copy types from [TYPESCRIPT_INTERFACES.ts](./TYPESCRIPT_INTERFACES.ts) to your project
5. Use [DATABASE_SCHEMA_REFERENCE.md](./DATABASE_SCHEMA_REFERENCE.md) for SQL query reference

## Architecture Overview

### Current State (Python Desktop)
```
PyQt6 Desktop App
├── UI Layer (Qt Widgets)
├── Service Layer (Python)
├── Database Layer (pyodbc)
└── SQL Server
```

### Target State (Express Web)
```
React Frontend          Express.js Backend
├── Components    <-->  ├── Routes
├── API Client          ├── Services
└── State Mgmt          ├── Database Layer (mssql)
                        └── SQL Server
```

## Key Technologies

| Current | Target |
|---------|--------|
| Python 3.11+ | Node.js 20 LTS |
| PyQt6 | Express.js + React |
| pyodbc | mssql (tedious) |
| python-dotenv | dotenv |
| Jinja2 | EJS or React |
| pytest | Jest + Supertest |

## Migration Phases Summary

1. **Phase 1**: Backend API (Express routes and services)
2. **Phase 2**: Frontend Foundation (React app with Sales module)
3. **Phase 3**: Complete Modules (Inventory and Engineering)
4. **Phase 4**: Authentication & Security
5. **Phase 5**: Deployment & Testing

## Support

For questions about the original Python application, refer to:
- `/README.md` - User documentation
- `/CLAUDE.md` - Development guidelines
- `/specs/` - Feature specifications
