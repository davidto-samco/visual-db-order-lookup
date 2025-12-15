# 01 - Backend Architecture

## Project Structure

```
server/
├── src/
│   ├── index.js                    # Application entry point
│   ├── app.js                      # Express app configuration
│   ├── config/
│   │   ├── index.js                # Configuration loader
│   │   └── database.js             # Database configuration
│   ├── database/
│   │   ├── connection.js           # SQL Server connection pool
│   │   ├── queries/
│   │   │   ├── order.queries.js    # Order-related SQL queries
│   │   │   ├── part.queries.js     # Part-related SQL queries
│   │   │   └── workorder.queries.js # Work order SQL queries
│   │   └── index.js                # Database exports
│   ├── models/
│   │   ├── order.model.js          # Order data structures
│   │   ├── part.model.js           # Part data structures
│   │   ├── workorder.model.js      # Work order data structures
│   │   └── index.js                # Model exports
│   ├── services/
│   │   ├── order.service.js        # Order business logic
│   │   ├── part.service.js         # Part business logic
│   │   ├── workorder.service.js    # Work order business logic
│   │   ├── bom.service.js          # BOM hierarchy logic
│   │   └── index.js                # Service exports
│   ├── controllers/
│   │   ├── order.controller.js     # Order route handlers
│   │   ├── part.controller.js      # Part route handlers
│   │   ├── workorder.controller.js # Work order route handlers
│   │   └── index.js                # Controller exports
│   ├── routes/
│   │   ├── order.routes.js         # /api/v1/orders routes
│   │   ├── part.routes.js          # /api/v1/parts routes
│   │   ├── workorder.routes.js     # /api/v1/workorders routes
│   │   └── index.js                # Route aggregation
│   ├── middleware/
│   │   ├── error.middleware.js     # Global error handler
│   │   ├── validation.middleware.js # Request validation
│   │   └── logging.middleware.js   # Request logging
│   └── utils/
│       ├── formatters.js           # Data formatting utilities
│       ├── logger.js               # Winston logger configuration
│       └── errors.js               # Custom error classes
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── utils/
│   └── integration/
│       └── routes/
├── package.json
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
    "nodemon": "^3.0.2",
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "eslint": "^8.55.0"
  }
}
```

## Entry Point (src/index.js)

```javascript
const app = require('./app');
const { connectDatabase, closeDatabase } = require('./database');
const logger = require('./utils/logger');
const config = require('./config');

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

## Express App Configuration (src/app.js)

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { errorMiddleware } = require('./middleware/error.middleware');
const { loggingMiddleware } = require('./middleware/logging.middleware');
const routes = require('./routes');

const app = express();

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

module.exports = app;
```

## Configuration (src/config/index.js)

```javascript
require('dotenv').config();

const config = {
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

module.exports = config;
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
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.js",
    "lint:fix": "eslint src/**/*.js --fix"
  }
}
```

## ESLint Configuration (.eslintrc.js)

```javascript
module.exports = {
  env: {
    node: true,
    es2022: true,
    jest: true,
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  rules: {
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': 'warn',
    'semi': ['error', 'always'],
    'quotes': ['error', 'single'],
  },
};
```
