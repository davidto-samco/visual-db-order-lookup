# 03 - API Endpoints

## Base URL

```
http://localhost:3001/api/v1
```

## Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "count": 100
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Order with job number 123456 not found",
    "details": { ... }
  }
}
```

---

## Orders API

### GET /orders/recent
Get recent customer orders.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 100 | Maximum orders to return (max: 500) |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "jobNumber": "123456",
      "customerName": "ACME CORPORATION",
      "orderDate": "2024-01-15",
      "totalAmount": 15234.50,
      "customerPO": "PO-2024-001",
      "formatted": {
        "orderDate": "01/15/2024",
        "totalAmount": "$15,234.50"
      }
    }
  ],
  "meta": {
    "count": 100,
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
}
```

---

### GET /orders/search
Search orders with filters.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | No | Customer name pattern (partial match) |
| `startDate` | string | No | Start date (YYYY-MM-DD) |
| `endDate` | string | No | End date (YYYY-MM-DD) |
| `limit` | number | No | Maximum orders (default: 100, max: 500) |

**Example:**
```
GET /orders/search?customer=ACME&startDate=2024-01-01&endDate=2024-12-31
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "jobNumber": "123456",
      "customerName": "ACME CORPORATION",
      "orderDate": "2024-01-15",
      "totalAmount": 15234.50,
      "customerPO": "PO-2024-001",
      "formatted": {
        "orderDate": "01/15/2024",
        "totalAmount": "$15,234.50"
      }
    }
  ],
  "meta": {
    "count": 25,
    "filters": {
      "customer": "ACME",
      "startDate": "2024-01-01",
      "endDate": "2024-12-31"
    }
  }
}
```

---

### GET /orders/:jobNumber
Get order details by job number.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `jobNumber` | string | The order job number |

**Response:**
```json
{
  "success": true,
  "data": {
    "jobNumber": "123456",
    "orderDate": "2024-01-15",
    "totalAmount": 15234.50,
    "customerPO": "PO-2024-001",
    "desiredShipDate": "2024-02-15",
    "promisedDate": "2024-02-20",
    "notes": ["Rush order", "Customer requires certification"],
    "customer": {
      "id": "CUST001",
      "name": "ACME CORPORATION",
      "shipping": {
        "address1": "123 Main Street",
        "address2": "Suite 100",
        "city": "Chicago",
        "state": "IL",
        "zip": "60601",
        "country": "USA"
      },
      "billing": {
        "name": "ACME CORPORATION - AP",
        "address1": "456 Finance Ave",
        "city": "Chicago",
        "state": "IL",
        "zip": "60602",
        "country": "USA"
      },
      "contact": {
        "name": "John Smith",
        "phone": "312-555-1234",
        "fax": "312-555-1235",
        "email": "john.smith@acme.com"
      }
    },
    "formatted": {
      "orderDate": "01/15/2024",
      "totalAmount": "$15,234.50",
      "desiredShipDate": "02/15/2024",
      "promisedDate": "02/20/2024"
    }
  }
}
```

**Error (404):**
```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order with job number 999999 not found"
  }
}
```

---

### GET /orders/:jobNumber/lines
Get order line items.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `jobNumber` | string | The order job number |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "lineNumber": 1,
      "partId": "WIDGET-001",
      "partDescription": "Standard Widget Assembly",
      "orderQty": 100,
      "unitPrice": 45.50,
      "lineTotal": 4550.00,
      "desiredShipDate": "2024-02-15",
      "promisedShipDate": "2024-02-20",
      "baseId": "WO123456",
      "lotId": "1",
      "binaryDetails": "Special coating required per customer spec XYZ-123",
      "formatted": {
        "unitPrice": "$45.50",
        "lineTotal": "$4,550.00",
        "desiredShipDate": "02/15/2024"
      }
    }
  ],
  "meta": {
    "count": 5,
    "jobNumber": "123456"
  }
}
```

---

## Parts API

### GET /parts/:partNumber
Get part details by part number.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `partNumber` | string | The part ID |

**Response:**
```json
{
  "success": true,
  "data": {
    "partId": "WIDGET-001",
    "description": "Standard Widget Assembly",
    "stockUm": "EA",
    "costs": {
      "material": 12.50,
      "labor": 8.25,
      "burden": 4.15,
      "service": 0.00,
      "standard": 24.90,
      "last": 23.85,
      "average": 24.25
    },
    "quantities": {
      "onHand": 500,
      "onOrder": 200,
      "allocated": 150,
      "available": 350
    },
    "flags": {
      "purchased": false,
      "fabricated": true,
      "stocked": true
    },
    "vendorName": "SUPPLIER ABC",
    "formatted": {
      "standardCost": "$24.90",
      "qtyAvailable": "350 EA"
    }
  }
}
```

---

### GET /parts/search
Search parts by partial part number.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search pattern |
| `limit` | number | No | Maximum results (default: 100) |

**Example:**
```
GET /parts/search?q=WIDGET&limit=50
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "partId": "WIDGET-001",
      "description": "Standard Widget Assembly",
      "stockUm": "EA",
      "standardCost": 24.90,
      "qtyOnHand": 500,
      "qtyAvailable": 350
    }
  ],
  "meta": {
    "count": 15,
    "searchPattern": "WIDGET"
  }
}
```

---

### GET /parts/:partNumber/where-used
Get where-used information (which work orders use this part).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `partNumber` | string | The part ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 100 | Maximum results |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "workOrderId": {
        "baseId": "WO123456",
        "lotId": "1",
        "subId": "0"
      },
      "parentPartId": "ASSEMBLY-001",
      "parentDescription": "Main Assembly Unit",
      "workOrderStatus": "R",
      "qtyPer": 2.0,
      "fixedQty": 0.0,
      "formatted": {
        "workOrderId": "WO123456-0/1",
        "status": "Released"
      }
    }
  ],
  "meta": {
    "count": 25,
    "partNumber": "WIDGET-001"
  }
}
```

---

### GET /parts/:partNumber/purchase-history
Get purchase order history for a part.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `partNumber` | string | The part ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 100 | Maximum results |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "purchaseOrderId": "PO-2024-001",
      "lineNumber": 1,
      "vendorName": "SUPPLIER ABC",
      "orderQty": 500,
      "unitPrice": 12.50,
      "desiredReceiveDate": "2024-02-01",
      "receivedQty": 500,
      "lastReceiveDate": "2024-01-28",
      "formatted": {
        "unitPrice": "$12.50",
        "desiredReceiveDate": "02/01/2024"
      }
    }
  ],
  "meta": {
    "count": 10,
    "partNumber": "WIDGET-001"
  }
}
```

---

## Work Orders API

### GET /workorders/search
Search work orders by base ID pattern.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `baseId` | string | Yes | Base ID pattern (prefix match) |
| `limit` | number | No | Maximum results (default: 100) |

**Example:**
```
GET /workorders/search?baseId=WO1234&limit=50
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": {
        "baseId": "WO123456",
        "lotId": "1",
        "subId": "0"
      },
      "partId": "ASSEMBLY-001",
      "partDescription": "Main Assembly Unit",
      "orderQty": 100,
      "status": "R",
      "type": "M",
      "dates": {
        "desiredStart": "2024-01-15",
        "desiredCompl": "2024-02-15",
        "actualStart": "2024-01-16",
        "actualCompl": null
      },
      "formatted": {
        "id": "WO123456-0/1",
        "status": "Released",
        "type": "Make"
      }
    }
  ],
  "meta": {
    "count": 25,
    "searchPattern": "WO1234"
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId
Get work order header with aggregate counts.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `baseId` | string | Work order base ID |
| `lotId` | string | Work order lot ID |
| `subId` | string | Work order sub ID |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": {
      "baseId": "WO123456",
      "lotId": "1",
      "subId": "0"
    },
    "partId": "ASSEMBLY-001",
    "partDescription": "Main Assembly Unit",
    "quantities": {
      "ordered": 100,
      "completed": 50,
      "scrapped": 2
    },
    "status": "R",
    "type": "M",
    "priority": 5,
    "dates": {
      "desiredStart": "2024-01-15",
      "desiredCompl": "2024-02-15",
      "actualStart": "2024-01-16",
      "actualCompl": null
    },
    "customerOrder": {
      "orderId": "123456",
      "lineNo": 1
    },
    "notes": "Special handling required",
    "counts": {
      "operations": 5,
      "laborTickets": 25,
      "inventoryTrans": 15
    },
    "formatted": {
      "id": "WO123456-0/1",
      "status": "Released",
      "type": "Make"
    }
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/operations
Get operations for a work order.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `baseId` | string | Work order base ID |
| `lotId` | string | Work order lot ID |
| `subId` | string | Work order sub ID |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "sequenceNo": 10,
      "resourceId": "CNC-001",
      "departmentId": "MACH",
      "departmentName": "Machining",
      "setupHrs": 1.5,
      "runHrs": 8.0,
      "runType": "H",
      "status": "C",
      "dates": {
        "actualStart": "2024-01-16",
        "actualFinish": "2024-01-17"
      },
      "requirementCount": 3,
      "formatted": {
        "status": "Complete",
        "runType": "Hours per piece"
      }
    }
  ],
  "meta": {
    "count": 5,
    "workOrderId": "WO123456-0/1"
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/requirements
Get requirements (BOM) for a work order or specific operation.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `baseId` | string | Work order base ID |
| `lotId` | string | Work order lot ID |
| `subId` | string | Work order sub ID |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operationSeqNo` | number | No | Filter by operation sequence |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "pieceNo": 1,
      "partId": "WIDGET-001",
      "partDescription": "Standard Widget Assembly",
      "qtyPerPiece": 2.0,
      "fixedQty": 0.0,
      "scrapPercent": 5.0,
      "operationSeqNo": 10,
      "subordWoSubId": null,
      "quantities": {
        "issued": 200,
        "allocated": 10
      },
      "notes": null,
      "isSubWorkOrder": false,
      "formatted": {
        "qtyPer": "2.0 per piece",
        "scrapPercent": "5.0%"
      }
    },
    {
      "pieceNo": 2,
      "partId": "SUB-ASSY-001",
      "partDescription": "Sub Assembly Component",
      "qtyPerPiece": 1.0,
      "fixedQty": 0.0,
      "scrapPercent": 0.0,
      "operationSeqNo": 10,
      "subordWoSubId": "1",
      "quantities": {
        "issued": 0,
        "allocated": 100
      },
      "notes": null,
      "isSubWorkOrder": true,
      "subWorkOrder": {
        "baseId": "WO123456",
        "lotId": "1",
        "subId": "1"
      },
      "formatted": {
        "qtyPer": "1.0 per piece"
      }
    }
  ],
  "meta": {
    "count": 8,
    "workOrderId": "WO123456-0/1",
    "operationSeqNo": 10
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/labor
Get labor tickets for a work order.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "employeeId": "EMP001",
      "employeeName": "John Doe",
      "laborDate": "2024-01-17",
      "operationSeqNo": 10,
      "hours": {
        "setup": 0.5,
        "run": 4.0
      },
      "laborRate": 25.00,
      "costs": {
        "labor": 112.50,
        "burden": 45.00
      },
      "quantities": {
        "completed": 50,
        "scrapped": 1
      },
      "formatted": {
        "laborDate": "01/17/2024",
        "laborCost": "$112.50",
        "totalHours": "4.5 hrs"
      }
    }
  ],
  "meta": {
    "count": 25,
    "workOrderId": "WO123456-0/1"
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/inventory
Get inventory transactions for a work order.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "partId": "WIDGET-001",
      "partDescription": "Standard Widget Assembly",
      "transType": "I",
      "quantity": 200,
      "transDate": "2024-01-16",
      "locationId": "MAIN",
      "costs": {
        "unit": 12.50,
        "total": 2500.00
      },
      "formatted": {
        "transType": "Issue",
        "transDate": "01/16/2024",
        "totalCost": "$2,500.00"
      }
    }
  ],
  "meta": {
    "count": 15,
    "workOrderId": "WO123456-0/1"
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/wip
Get WIP (Work In Progress) balance for a work order.

**Response:**
```json
{
  "success": true,
  "data": {
    "costs": {
      "material": 5000.00,
      "labor": 2500.00,
      "burden": 1000.00,
      "service": 0.00,
      "total": 8500.00
    },
    "formatted": {
      "materialCost": "$5,000.00",
      "laborCost": "$2,500.00",
      "burdenCost": "$1,000.00",
      "totalCost": "$8,500.00"
    }
  }
}
```

---

### GET /workorders/:baseId/:lotId/:subId/hierarchy
Get full work order hierarchy (parent and all child work orders).

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": {
        "baseId": "WO123456",
        "lotId": "1",
        "subId": "0"
      },
      "partId": "ASSEMBLY-001",
      "partDescription": "Main Assembly Unit",
      "orderQty": 100,
      "status": "R",
      "type": "M",
      "hierarchyLevel": 0,
      "hierarchyPath": "0",
      "formatted": {
        "id": "WO123456-0/1",
        "status": "Released"
      }
    },
    {
      "id": {
        "baseId": "WO123456",
        "lotId": "1",
        "subId": "1"
      },
      "partId": "SUB-ASSY-001",
      "partDescription": "Sub Assembly Component",
      "orderQty": 100,
      "status": "R",
      "type": "M",
      "hierarchyLevel": 1,
      "hierarchyPath": "0/1",
      "formatted": {
        "id": "WO123456-1/1",
        "status": "Released"
      }
    }
  ],
  "meta": {
    "count": 5,
    "rootWorkOrderId": "WO123456-0/1"
  }
}
```

---

## Health & Status Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "database": "connected"
}
```

---

## Status Codes Summary

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Database/server error |
