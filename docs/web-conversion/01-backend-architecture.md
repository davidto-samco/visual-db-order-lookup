# 01 - Backend Architecture

## Project Structure

```
server/
├── src/
│   ├── index.ts                    # Application entry point
│   ├── app.ts                      # Express app configuration
│   ├── config/
│   │   ├── index.ts                # Configuration loader
│   │   └── database.ts             # Database configuration
│   ├── database/
│   │   ├── connection.ts           # SQL Server connection pool
│   │   ├── queries/
│   │   │   ├── order.queries.ts    # Order-related SQL queries
│   │   │   ├── part.queries.ts     # Part-related SQL queries
│   │   │   └── workorder.queries.ts # Work order SQL queries
│   │   └── index.ts                # Database exports
│   ├── models/
│   │   ├── order.model.ts          # Order DTOs/interfaces
│   │   ├── part.model.ts           # Part DTOs/interfaces
│   │   ├── workorder.model.ts      # Work order DTOs/interfaces
│   │   └── index.ts                # Model exports
│   ├── services/
│   │   ├── order.service.ts        # Order business logic
│   │   ├── part.service.ts         # Part business logic
│   │   ├── workorder.service.ts    # Work order business logic
│   │   ├── bom.service.ts          # BOM hierarchy logic
│   │   └── index.ts                # Service exports
│   ├── controllers/
│   │   ├── order.controller.ts     # Order route handlers
│   │   ├── part.controller.ts      # Part route handlers
│   │   ├── workorder.controller.ts # Work order route handlers
│   │   └── index.ts                # Controller exports
│   ├── routes/
│   │   ├── order.routes.ts         # /api/v1/orders routes
│   │   ├── part.routes.ts          # /api/v1/parts routes
│   │   ├── workorder.routes.ts     # /api/v1/workorders routes
│   │   └── index.ts                # Route aggregation
│   ├── middleware/
│   │   ├── error.middleware.ts     # Global error handler
│   │   ├── validation.middleware.ts # Request validation
│   │   └── logging.middleware.ts   # Request logging
│   ├── utils/
│   │   ├── formatters.ts           # Data formatting utilities
│   │   ├── logger.ts               # Winston logger configuration
│   │   └── errors.ts               # Custom error classes
│   └── types/
│       └── express.d.ts            # Express type extensions
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── utils/
│   └── integration/
│       └── routes/
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (React)                              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP/JSON
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        EXPRESS APPLICATION                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      MIDDLEWARE STACK                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │  │
│  │  │   CORS      │→ │  Logging    │→ │  JSON Body Parser    │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                         ROUTES                                │  │
│  │  /api/v1/orders/*    /api/v1/parts/*    /api/v1/workorders/* │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      CONTROLLERS                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │  │
│  │  │  Order     │  │   Part     │  │     WorkOrder          │  │  │
│  │  │ Controller │  │ Controller │  │     Controller         │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                       SERVICES                                │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐ ┌───────────┐  │  │
│  │  │  Order     │  │   Part     │  │WorkOrder │ │    BOM    │  │  │
│  │  │  Service   │  │  Service   │  │ Service  │ │  Service  │  │  │
│  │  └────────────┘  └────────────┘  └──────────┘ └───────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     DATABASE LAYER                            │  │
│  │  ┌─────────────────┐  ┌────────────────────────────────────┐  │  │
│  │  │ Connection Pool │  │           SQL Queries              │  │  │
│  │  │   (mssql)       │  │  order.queries  part.queries  ...  │  │  │
│  │  └─────────────────┘  └────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ TDS Protocol
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL SERVER (Visual/SAMCO)                        │
│                      10.10.10.142:1433                              │
│                       (Read-Only Access)                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Routes Layer
- Define HTTP endpoints and methods
- Apply route-specific middleware (validation)
- Delegate to controllers
- No business logic

### Controllers Layer
- Parse and validate request parameters
- Call appropriate service methods
- Format HTTP responses
- Handle HTTP-specific concerns (status codes, headers)

### Services Layer
- Implement business logic
- Coordinate database queries
- Transform data between database and API formats
- Handle business validation rules

### Database Layer
- Manage connection pool
- Execute parameterized SQL queries
- Handle database-specific error mapping
- Provide query helper functions

## Core Dependencies

```json
{
  "dependencies": {
    "express": "^4.18.2",
    "mssql": "^10.0.1",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "compression": "^1.7.4",
    "dotenv": "^16.3.1",
    "winston": "^3.11.0",
    "express-validator": "^7.0.1",
    "http-status-codes": "^2.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.2",
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.0",
    "@types/cors": "^2.8.16",
    "@types/compression": "^1.7.5",
    "ts-node": "^10.9.2",
    "ts-node-dev": "^2.0.0",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.10",
    "supertest": "^6.3.3",
    "@types/supertest": "^2.0.16",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.13.1",
    "@typescript-eslint/parser": "^6.13.1"
  }
}
```

## Entry Point (src/index.ts)

```typescript
import app from './app';
import { connectDatabase, closeDatabase } from './database';
import { logger } from './utils/logger';
import { config } from './config';

const PORT = config.port || 3001;

async function startServer() {
  try {
    // Initialize database connection pool
    await connectDatabase();
    logger.info('Database connection pool initialized');

    // Start Express server
    app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${config.nodeEnv}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  await closeDatabase();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');
  await closeDatabase();
  process.exit(0);
});

startServer();
```

## Express App Configuration (src/app.ts)

```typescript
import express, { Application } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { errorMiddleware } from './middleware/error.middleware';
import { loggingMiddleware } from './middleware/logging.middleware';
import routes from './routes';

const app: Application = express();

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Compression for responses
app.use(compression());

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use(loggingMiddleware);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/v1', routes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
    },
  });
});

// Global error handler
app.use(errorMiddleware);

export default app;
```

## Configuration (src/config/index.ts)

```typescript
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3001', 10),

  // Database configuration
  db: {
    server: process.env.DB_SERVER || '10.10.10.142',
    port: parseInt(process.env.DB_PORT || '1433', 10),
    database: process.env.DB_DATABASE || 'SAMCO',
    user: process.env.DB_USER || 'sa',
    password: process.env.DB_PASSWORD || '',
    options: {
      encrypt: false,
      trustServerCertificate: true,
      enableArithAbort: true,
    },
    pool: {
      min: 2,
      max: 10,
      idleTimeoutMillis: 30000,
    },
  },

  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',

  // API settings
  defaultPageSize: parseInt(process.env.DEFAULT_PAGE_SIZE || '100', 10),
  maxPageSize: parseInt(process.env.MAX_PAGE_SIZE || '500', 10),
};
```

## Environment Variables (.env.example)

```env
# Server Configuration
NODE_ENV=development
PORT=3001

# Database Configuration (SQL Server)
DB_SERVER=10.10.10.142
DB_PORT=1433
DB_DATABASE=SAMCO
DB_USER=sa
DB_PASSWORD=your_password_here

# CORS
CORS_ORIGIN=http://localhost:3000

# Logging
LOG_LEVEL=info

# API Settings
DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=500
```

## NPM Scripts (package.json)

```json
{
  "scripts": {
    "dev": "ts-node-dev --respawn --transpile-only src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix"
  }
}
```

## TypeScript Configuration (tsconfig.json)

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
    "sourceMap": true,
    "moduleResolution": "node",
    "baseUrl": "./src",
    "paths": {
      "@/*": ["./*"],
      "@config/*": ["config/*"],
      "@database/*": ["database/*"],
      "@models/*": ["models/*"],
      "@services/*": ["services/*"],
      "@controllers/*": ["controllers/*"],
      "@routes/*": ["routes/*"],
      "@middleware/*": ["middleware/*"],
      "@utils/*": ["utils/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```
