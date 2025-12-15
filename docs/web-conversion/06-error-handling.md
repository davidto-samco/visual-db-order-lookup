# 06 - Error Handling & Logging

## Overview

This document covers error handling strategies, custom error classes, HTTP status code mapping, and logging configuration for the Express backend.

---

## Custom Error Classes (src/utils/errors.ts)

```typescript
import { StatusCodes } from 'http-status-codes';

/**
 * Base application error
 */
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly isOperational: boolean;
  public readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    statusCode: number = StatusCodes.INTERNAL_SERVER_ERROR,
    code: string = 'INTERNAL_ERROR',
    isOperational: boolean = true,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = isOperational;
    this.details = details;

    // Maintains proper stack trace
    Error.captureStackTrace(this, this.constructor);
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

/**
 * Validation error (400 Bad Request)
 */
export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, StatusCodes.BAD_REQUEST, 'VALIDATION_ERROR', true, details);
  }
}

/**
 * Resource not found error (404)
 */
export class NotFoundError extends AppError {
  constructor(resource: string, identifier: string) {
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
export class OrderNotFoundError extends NotFoundError {
  constructor(jobNumber: string) {
    super('Order', jobNumber);
    this.code = 'ORDER_NOT_FOUND';
  }
}

/**
 * Part not found error
 */
export class PartNotFoundError extends NotFoundError {
  constructor(partNumber: string) {
    super('Part', partNumber);
    this.code = 'PART_NOT_FOUND';
  }
}

/**
 * Work order not found error
 */
export class WorkOrderNotFoundError extends AppError {
  constructor(baseId: string, lotId: string, subId: string) {
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
export class JobNotFoundError extends NotFoundError {
  constructor(jobNumber: string) {
    super('Job', jobNumber);
    this.code = 'JOB_NOT_FOUND';
  }
}

/**
 * Database error (500)
 */
export class DatabaseError extends AppError {
  constructor(message: string, originalError?: Error) {
    super(
      `Database error: ${message}`,
      StatusCodes.INTERNAL_SERVER_ERROR,
      'DATABASE_ERROR',
      true,
      originalError ? { originalMessage: originalError.message } : undefined
    );
  }
}

/**
 * Database connection error
 */
export class DatabaseConnectionError extends AppError {
  constructor(message: string = 'Failed to connect to database') {
    super(message, StatusCodes.SERVICE_UNAVAILABLE, 'DATABASE_CONNECTION_ERROR', false);
  }
}

/**
 * Check if error is operational (expected) vs programming error
 */
export function isOperationalError(error: Error): boolean {
  if (error instanceof AppError) {
    return error.isOperational;
  }
  return false;
}
```

---

## Error Middleware (src/middleware/error.middleware.ts)

```typescript
import { Request, Response, NextFunction } from 'express';
import { StatusCodes } from 'http-status-codes';
import { AppError, isOperationalError } from '../utils/errors';
import { logger } from '../utils/logger';
import { config } from '../config';

/**
 * Error response structure
 */
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    stack?: string;
  };
}

/**
 * Global error handling middleware
 */
export function errorMiddleware(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Log the error
  if (isOperationalError(err)) {
    logger.warn('Operational error:', {
      code: (err as AppError).code,
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
  const response: ErrorResponse = {
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
 */
export function notFoundHandler(req: Request, res: Response): void {
  const response: ErrorResponse = {
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
 */
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

---

## Validation Middleware (src/middleware/validation.middleware.ts)

```typescript
import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain } from 'express-validator';
import { ValidationError } from '../utils/errors';

/**
 * Validate request using express-validator chains
 */
export function validate(validations: ValidationChain[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
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

    throw new ValidationError('Validation failed', {
      errors: formattedErrors,
    });
  };
}

/**
 * Common validation chains
 */
import { query, param } from 'express-validator';

export const orderValidations = {
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

export const partValidations = {
  partNumber: param('partNumber')
    .trim()
    .notEmpty()
    .withMessage('Part number is required'),

  searchPattern: query('q')
    .trim()
    .notEmpty()
    .withMessage('Search pattern is required'),
};

export const workOrderValidations = {
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
```

---

## Logger Configuration (src/utils/logger.ts)

```typescript
import winston from 'winston';
import { config } from '../config';

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
export const logger = winston.createLogger({
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

/**
 * Create child logger with context
 */
export function createLogger(context: string) {
  return logger.child({ context });
}
```

---

## Request Logging Middleware (src/middleware/logging.middleware.ts)

```typescript
import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

/**
 * Request logging middleware
 */
export function loggingMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
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
    "stack": "TypeError: Cannot read property 'id' of undefined\n    at OrderService.getOrderByJobNumber (/src/services/order.service.ts:45:12)\n    ..."
  }
}
```

---

## Python to TypeScript Error Mapping

| Python Exception | TypeScript Error Class |
|------------------|------------------------|
| `ValueError` | `ValidationError` |
| `pyodbc.Error` | `DatabaseError` |
| Custom `WorkOrderNotFoundError` | `WorkOrderNotFoundError` |
| Generic `Exception` | `AppError` |
