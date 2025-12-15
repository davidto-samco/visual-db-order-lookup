# 06 - Error Handling & Logging

## Overview

This document covers error handling strategies, custom error classes, HTTP status code mapping, and logging configuration for the Express backend.

---

## Custom Error Classes (src/utils/errors.js)

```javascript
const { StatusCodes } = require('http-status-codes');

/**
 * Base application error
 */
class AppError extends Error {
  constructor(
    message,
    statusCode = StatusCodes.INTERNAL_SERVER_ERROR,
    code = 'INTERNAL_ERROR',
    isOperational = true,
    details = null
  ) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = isOperational;
    this.details = details;

    // Maintains proper stack trace
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * Validation error (400 Bad Request)
 */
class ValidationError extends AppError {
  constructor(message, details = null) {
    super(message, StatusCodes.BAD_REQUEST, 'VALIDATION_ERROR', true, details);
  }
}

/**
 * Resource not found error (404)
 */
class NotFoundError extends AppError {
  constructor(resource, identifier) {
    super(
      `${resource} not found: ${identifier}`,
      StatusCodes.NOT_FOUND,
      'NOT_FOUND',
      true,
      { resource, identifier }
    );
  }
}

/**
 * Order not found error
 */
class OrderNotFoundError extends NotFoundError {
  constructor(jobNumber) {
    super('Order', jobNumber);
    this.code = 'ORDER_NOT_FOUND';
  }
}

/**
 * Part not found error
 */
class PartNotFoundError extends NotFoundError {
  constructor(partNumber) {
    super('Part', partNumber);
    this.code = 'PART_NOT_FOUND';
  }
}

/**
 * Work order not found error
 */
class WorkOrderNotFoundError extends AppError {
  constructor(baseId, lotId, subId) {
    const identifier = `${baseId}-${subId}/${lotId}`;
    super(
      `Work order not found: ${identifier}`,
      StatusCodes.NOT_FOUND,
      'WORK_ORDER_NOT_FOUND',
      true,
      { baseId, lotId, subId }
    );
  }
}

/**
 * Job not found error
 */
class JobNotFoundError extends NotFoundError {
  constructor(jobNumber) {
    super('Job', jobNumber);
    this.code = 'JOB_NOT_FOUND';
  }
}

/**
 * Database error (500)
 */
class DatabaseError extends AppError {
  constructor(message, originalError = null) {
    super(
      `Database error: ${message}`,
      StatusCodes.INTERNAL_SERVER_ERROR,
      'DATABASE_ERROR',
      true,
      originalError ? { originalMessage: originalError.message } : null
    );
  }
}

/**
 * Database connection error
 */
class DatabaseConnectionError extends AppError {
  constructor(message = 'Failed to connect to database') {
    super(message, StatusCodes.SERVICE_UNAVAILABLE, 'DATABASE_CONNECTION_ERROR', false);
  }
}

/**
 * Check if error is operational (expected) vs programming error
 * @param {Error} error
 * @returns {boolean}
 */
function isOperationalError(error) {
  if (error instanceof AppError) {
    return error.isOperational;
  }
  return false;
}

module.exports = {
  AppError,
  ValidationError,
  NotFoundError,
  OrderNotFoundError,
  PartNotFoundError,
  WorkOrderNotFoundError,
  JobNotFoundError,
  DatabaseError,
  DatabaseConnectionError,
  isOperationalError,
};
```

---

## Error Middleware (src/middleware/error.middleware.js)

```javascript
const { StatusCodes } = require('http-status-codes');
const { AppError, isOperationalError } = require('../utils/errors');
const logger = require('../utils/logger');
const config = require('../config');

/**
 * Global error handling middleware
 * @param {Error} err
 * @param {Request} req
 * @param {Response} res
 * @param {Function} next
 */
function errorMiddleware(err, req, res, next) {
  // Log the error
  if (isOperationalError(err)) {
    logger.warn('Operational error:', {
      code: err.code,
      message: err.message,
      path: req.path,
      method: req.method,
    });
  } else {
    logger.error('Unexpected error:', {
      message: err.message,
      stack: err.stack,
      path: req.path,
      method: req.method,
    });
  }

  // Build error response
  const response = {
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
  };

  let statusCode = StatusCodes.INTERNAL_SERVER_ERROR;

  if (err instanceof AppError) {
    statusCode = err.statusCode;
    response.error.code = err.code;
    response.error.message = err.message;

    if (err.details) {
      response.error.details = err.details;
    }
  } else if (err.name === 'SyntaxError') {
    // JSON parse error
    statusCode = StatusCodes.BAD_REQUEST;
    response.error.code = 'INVALID_JSON';
    response.error.message = 'Invalid JSON in request body';
  } else if (err.name === 'RequestError' || err.name === 'ConnectionError') {
    // MSSQL connection error
    statusCode = StatusCodes.SERVICE_UNAVAILABLE;
    response.error.code = 'DATABASE_UNAVAILABLE';
    response.error.message = 'Database service is temporarily unavailable';
  }

  // Include stack trace in development
  if (config.nodeEnv === 'development') {
    response.error.stack = err.stack;
  }

  res.status(statusCode).json(response);
}

/**
 * 404 handler for unknown routes
 * @param {Request} req
 * @param {Response} res
 */
function notFoundHandler(req, res) {
  const response = {
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
    },
  };

  res.status(StatusCodes.NOT_FOUND).json(response);
}

/**
 * Async handler wrapper to catch promise rejections
 * @param {Function} fn - Async route handler
 * @returns {Function}
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = {
  errorMiddleware,
  notFoundHandler,
  asyncHandler,
};
```

---

## Validation Middleware (src/middleware/validation.middleware.js)

```javascript
const { validationResult } = require('express-validator');
const { ValidationError } = require('../utils/errors');

/**
 * Validate request using express-validator chains
 * @param {Array} validations - Array of validation chains
 * @returns {Function}
 */
function validate(validations) {
  return async (req, res, next) => {
    // Run all validations
    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);

    if (errors.isEmpty()) {
      return next();
    }

    // Format validation errors
    const formattedErrors = errors.array().map(err => ({
      field: err.type === 'field' ? err.path : undefined,
      message: err.msg,
    }));

    next(new ValidationError('Validation failed', { errors: formattedErrors }));
  };
}

module.exports = { validate };
```

---

## Validation Chains (src/middleware/validators.js)

```javascript
const { query, param } = require('express-validator');

const orderValidations = {
  jobNumber: param('jobNumber')
    .trim()
    .notEmpty()
    .withMessage('Job number is required'),

  limit: query('limit')
    .optional()
    .isInt({ min: 1, max: 500 })
    .withMessage('Limit must be between 1 and 500')
    .toInt(),

  startDate: query('startDate')
    .optional()
    .isISO8601()
    .withMessage('Start date must be a valid ISO 8601 date')
    .toDate(),

  endDate: query('endDate')
    .optional()
    .isISO8601()
    .withMessage('End date must be a valid ISO 8601 date')
    .toDate(),

  customerName: query('customer')
    .optional()
    .trim()
    .isLength({ min: 1 })
    .withMessage('Customer name must not be empty'),
};

const partValidations = {
  partNumber: param('partNumber')
    .trim()
    .notEmpty()
    .withMessage('Part number is required'),

  searchPattern: query('q')
    .trim()
    .notEmpty()
    .withMessage('Search pattern is required'),
};

const workOrderValidations = {
  baseId: param('baseId')
    .trim()
    .notEmpty()
    .withMessage('Base ID is required'),

  lotId: param('lotId')
    .trim()
    .notEmpty()
    .withMessage('Lot ID is required'),

  subId: param('subId')
    .trim()
    .notEmpty()
    .withMessage('Sub ID is required'),

  operationSeqNo: query('operationSeqNo')
    .optional()
    .isInt({ min: 0 })
    .withMessage('Operation sequence number must be a non-negative integer')
    .toInt(),
};

module.exports = {
  orderValidations,
  partValidations,
  workOrderValidations,
};
```

---

## Logger Configuration (src/utils/logger.js)

```javascript
const winston = require('winston');
const config = require('../config');

const { combine, timestamp, printf, colorize, errors } = winston.format;

/**
 * Custom log format
 */
const logFormat = printf(({ level, message, timestamp, stack, ...metadata }) => {
  let log = `${timestamp} [${level}]: ${message}`;

  // Include metadata if present
  if (Object.keys(metadata).length > 0) {
    log += ` ${JSON.stringify(metadata)}`;
  }

  // Include stack trace for errors
  if (stack) {
    log += `\n${stack}`;
  }

  return log;
});

/**
 * Create logger instance
 */
const logger = winston.createLogger({
  level: config.logLevel,
  format: combine(
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    errors({ stack: true }),
    logFormat
  ),
  transports: [
    // Console transport
    new winston.transports.Console({
      format: combine(colorize(), logFormat),
    }),
  ],
  // Don't exit on uncaught exceptions
  exitOnError: false,
});

// Add file transports in production
if (config.nodeEnv === 'production') {
  logger.add(
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  );

  logger.add(
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  );
}

module.exports = logger;
```

---

## Request Logging Middleware (src/middleware/logging.middleware.js)

```javascript
const logger = require('../utils/logger');

/**
 * Request logging middleware
 * @param {Request} req
 * @param {Response} res
 * @param {Function} next
 */
function loggingMiddleware(req, res, next) {
  const startTime = Date.now();

  // Log request
  logger.info(`--> ${req.method} ${req.path}`, {
    query: Object.keys(req.query).length > 0 ? req.query : undefined,
    params: Object.keys(req.params).length > 0 ? req.params : undefined,
    ip: req.ip,
  });

  // Log response on finish
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const level = res.statusCode >= 400 ? 'warn' : 'info';

    logger[level](`<-- ${req.method} ${req.path} ${res.statusCode}`, {
      duration: `${duration}ms`,
    });
  });

  next();
}

module.exports = { loggingMiddleware };
```

---

## Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `INVALID_JSON` | 400 | Malformed JSON body |
| `NOT_FOUND` | 404 | Generic resource not found |
| `ORDER_NOT_FOUND` | 404 | Order with given job number not found |
| `PART_NOT_FOUND` | 404 | Part with given part number not found |
| `WORK_ORDER_NOT_FOUND` | 404 | Work order with given ID not found |
| `JOB_NOT_FOUND` | 404 | Job with given number not found |
| `DATABASE_ERROR` | 500 | Database query error |
| `DATABASE_UNAVAILABLE` | 503 | Cannot connect to database |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Error Response Examples

### Validation Error (400)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "errors": [
        {
          "field": "startDate",
          "message": "Start date must be a valid ISO 8601 date"
        }
      ]
    }
  }
}
```

### Not Found Error (404)
```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order not found: 999999",
    "details": {
      "resource": "Order",
      "identifier": "999999"
    }
  }
}
```

### Database Error (500)
```json
{
  "success": false,
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Database error: Connection timeout"
  }
}
```

### Development Error (with stack trace)
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Cannot read property 'id' of undefined",
    "stack": "TypeError: Cannot read property 'id' of undefined\n    at getOrderByJobNumber (/src/services/order.service.js:45:12)\n    ..."
  }
}
```

---

## Python to JavaScript Error Mapping

| Python Exception | JavaScript Error Class |
|------------------|------------------------|
| `ValueError` | `ValidationError` |
| `pyodbc.Error` | `DatabaseError` |
| Custom `WorkOrderNotFoundError` | `WorkOrderNotFoundError` |
| Generic `Exception` | `AppError` |
