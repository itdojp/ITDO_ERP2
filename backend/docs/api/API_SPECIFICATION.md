# ITDO ERP System v2 - API Specification

## 📋 Overview

This document provides comprehensive API specifications for the ITDO ERP System v2. All APIs follow RESTful principles with OpenAPI 3.0 documentation, JSON request/response formats, and JWT-based authentication.

## 🌐 Base Configuration

### Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.itdo-erp.com/api/v1`

### Authentication
- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Token Endpoint**: `/auth/token`

### Common Headers
```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
X-Organization-ID: <organization_id>
```

### Response Format
All API responses follow this standardized format:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-01-26T10:00:00Z",
  "request_id": "uuid-v4"
}
```

## 🔐 Authentication API

### POST /auth/token
Authenticate user and obtain JWT token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "organization_id": "org_uuid"
  }
}
```

### POST /auth/refresh
Refresh JWT token using refresh token.

**Request:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

## 👥 User Management API

### GET /users
List users with pagination and filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `organization_id` (uuid): Filter by organization
- `department_id` (uuid): Filter by department
- `is_active` (bool): Filter by active status
- `search` (string): Search by name or email

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "organization_id": "org_uuid",
      "department_id": "dept_uuid",
      "roles": ["user", "project_manager"],
      "created_at": "2025-01-26T10:00:00Z",
      "updated_at": "2025-01-26T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### POST /users
Create a new user.

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "full_name": "Jane Smith",
  "organization_id": "org_uuid",
  "department_id": "dept_uuid",
  "roles": ["user"]
}
```

### GET /users/{user_id}
Get user details by ID.

### PUT /users/{user_id}
Update user information.

### DELETE /users/{user_id}
Soft delete user (deactivate).

## 🏢 Organization Management API

### GET /organizations
List organizations.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "ACME Corporation",
      "description": "Leading technology company",
      "industry": "technology",
      "size": "large",
      "address": "123 Tech Street, Silicon Valley",
      "phone": "+1-555-0123",
      "email": "contact@acme.com",
      "website": "https://acme.com",
      "is_active": true,
      "created_at": "2025-01-26T10:00:00Z"
    }
  ]
}
```

### POST /organizations
Create new organization.

### GET /organizations/{org_id}
Get organization details.

### PUT /organizations/{org_id}
Update organization.

## 🏛️ Department Management API

### GET /departments
List departments with hierarchical structure.

**Query Parameters:**
- `organization_id` (uuid, required): Organization filter
- `parent_id` (uuid): Filter by parent department
- `include_children` (bool): Include child departments

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Engineering",
      "description": "Software development team",
      "code": "ENG",
      "parent_id": null,
      "organization_id": "org_uuid",
      "manager_id": "user_uuid",
      "budget": 1000000.00,
      "path": "/engineering",
      "level": 0,
      "children": [
        {
          "id": "uuid",
          "name": "Backend Team",
          "code": "ENG-BE",
          "parent_id": "parent_uuid",
          "path": "/engineering/backend",
          "level": 1
        }
      ]
    }
  ]
}
```

### POST /departments
Create new department.

### GET /departments/{dept_id}
Get department details.

### PUT /departments/{dept_id}
Update department.

## 📊 Project Management API

### GET /projects
List projects with filtering and pagination.

**Query Parameters:**
- `organization_id` (uuid, required)
- `status` (enum): active, completed, on_hold, cancelled
- `manager_id` (uuid): Filter by project manager
- `start_date_from` (date): Filter by start date range
- `start_date_to` (date): Filter by start date range

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "ERP System Development",
      "description": "Next-generation ERP system",
      "status": "active",
      "priority": "high",
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "budget": 500000.00,
      "actual_cost": 150000.00,
      "progress_percentage": 35.5,
      "manager": {
        "id": "uuid",
        "name": "John Doe",
        "email": "john@example.com"
      },
      "organization_id": "org_uuid",
      "created_at": "2025-01-26T10:00:00Z"
    }
  ]
}
```

### POST /projects
Create new project.

**Request:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "start_date": "2025-02-01",
  "end_date": "2025-08-31",
  "budget": 250000.00,
  "manager_id": "user_uuid",
  "organization_id": "org_uuid",
  "priority": "medium",
  "tags": ["development", "mvp"]
}
```

### GET /projects/{project_id}
Get project details with tasks and resources.

### PUT /projects/{project_id}
Update project.

### GET /projects/{project_id}/tasks
Get project tasks.

### GET /projects/{project_id}/resources
Get project resource allocations.

### GET /projects/{project_id}/financial-summary
Get project financial summary.

## ✅ Task Management API

### GET /tasks
List tasks with filtering.

**Query Parameters:**
- `project_id` (uuid): Filter by project
- `assignee_id` (uuid): Filter by assignee
- `status` (enum): not_started, in_progress, completed, on_hold
- `priority` (enum): low, medium, high, critical
- `due_date_from` (date): Filter by due date range
- `due_date_to` (date): Filter by due date range

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication system",
      "status": "in_progress",
      "priority": "high",
      "project": {
        "id": "uuid",
        "name": "ERP System Development"
      },
      "assignees": [
        {
          "id": "uuid",
          "name": "Jane Smith",
          "email": "jane@example.com"
        }
      ],
      "due_date": "2025-02-15",
      "estimated_hours": 40,
      "actual_hours": 25,
      "progress_percentage": 60,
      "created_by": {
        "id": "uuid",
        "name": "John Doe"
      },
      "created_at": "2025-01-26T10:00:00Z"
    }
  ]
}
```

### POST /tasks
Create new task.

### GET /tasks/{task_id}
Get task details.

### PUT /tasks/{task_id}
Update task.

### PATCH /tasks/{task_id}/status
Update task status.

### POST /tasks/{task_id}/assign
Assign user to task.

### DELETE /tasks/{task_id}/assign/{user_id}
Unassign user from task.

### GET /tasks/{task_id}/history
Get task change history.

## 🎯 Resource Management API

### GET /resources
List resources (human and material).

**Query Parameters:**
- `organization_id` (uuid, required)
- `type` (enum): human, equipment, material
- `department_id` (uuid): Filter by department
- `availability_status` (enum): available, allocated, unavailable

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Senior Developer",
      "type": "human",
      "category": "software_development",
      "description": "Experienced full-stack developer",
      "hourly_rate": 85.00,
      "availability_status": "available",
      "skills": ["Python", "React", "PostgreSQL"],
      "department_id": "dept_uuid",
      "organization_id": "org_uuid"
    },
    {
      "id": "uuid",
      "name": "Development Laptop",
      "type": "equipment",
      "category": "computer_hardware",
      "daily_cost": 25.00,
      "availability_status": "allocated",
      "specifications": {
        "brand": "Dell",
        "model": "XPS 15",
        "ram": "32GB",
        "storage": "1TB SSD"
      }
    }
  ]
}
```

### POST /resources
Create new resource.

### GET /resources/{resource_id}
Get resource details.

### PUT /resources/{resource_id}
Update resource.

### GET /resources/allocations
Get resource allocations.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "resource_id": "resource_uuid",
      "project_id": "project_uuid",
      "allocation_percentage": 80.0,
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "hourly_rate": 85.00,
      "status": "active",
      "resource": {
        "name": "Senior Developer",
        "type": "human"
      },
      "project": {
        "name": "ERP System Development"
      }
    }
  ]
}
```

### POST /resources/allocations
Create resource allocation.

### PUT /resources/allocations/{allocation_id}
Update resource allocation.

### DELETE /resources/allocations/{allocation_id}
Remove resource allocation.

## 💰 Financial Management API

### GET /financial/accounts
List chart of accounts.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "account_code": "1000",
      "account_name": "Cash",
      "account_type": "asset",
      "parent_account_id": null,
      "is_active": true,
      "balance": 150000.00,
      "organization_id": "org_uuid"
    }
  ]
}
```

### GET /financial/journal-entries
List journal entries.

**Query Parameters:**
- `organization_id` (uuid, required)
- `account_id` (uuid): Filter by account
- `date_from` (date): Date range filter
- `date_to` (date): Date range filter
- `amount_min` (decimal): Amount range filter
- `amount_max` (decimal): Amount range filter

### POST /financial/journal-entries
Create journal entry.

**Request:**
```json
{
  "description": "Sales revenue",
  "entry_date": "2025-01-26",
  "reference_number": "INV-2025-001",
  "entries": [
    {
      "account_id": "account_uuid",
      "debit_amount": 1500.00,
      "credit_amount": 0.00,
      "description": "Cash received"
    },
    {
      "account_id": "revenue_account_uuid",
      "debit_amount": 0.00,
      "credit_amount": 1500.00,
      "description": "Sales revenue"
    }
  ],
  "organization_id": "org_uuid"
}
```

### GET /financial/reports/balance-sheet
Generate balance sheet.

**Query Parameters:**
- `organization_id` (uuid, required)
- `as_of_date` (date, required)
- `currency` (string, default: "USD")

### GET /financial/reports/income-statement
Generate income statement.

**Query Parameters:**
- `organization_id` (uuid, required)
- `start_date` (date, required)
- `end_date` (date, required)
- `currency` (string, default: "USD")

### GET /financial/reports/cash-flow
Generate cash flow statement.

### GET /financial/budgets
List budgets.

### POST /financial/budgets
Create budget.

### GET /financial/budgets/{budget_id}
Get budget details.

### PUT /financial/budgets/{budget_id}
Update budget.

## 📦 Inventory Management API

### GET /inventory
List inventory items.

**Query Parameters:**
- `organization_id` (uuid, required)
- `category` (string): Filter by category
- `low_stock` (bool): Show only low stock items
- `search` (string): Search by name or SKU

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Widget Alpha",
      "description": "High-quality widget for manufacturing",
      "sku": "WID-ALPHA-001",
      "category": "components",
      "quantity_on_hand": 150,
      "quantity_reserved": 20,
      "quantity_available": 130,
      "reorder_level": 50,
      "reorder_quantity": 200,
      "unit_cost": 15.50,
      "selling_price": 25.00,
      "location": "Warehouse A, Shelf 12",
      "supplier": "ACME Suppliers",
      "organization_id": "org_uuid",
      "last_movement_date": "2025-01-25T14:30:00Z"
    }
  ]
}
```

### POST /inventory
Add new inventory item.

### GET /inventory/{item_id}
Get inventory item details.

### PUT /inventory/{item_id}
Update inventory item.

### GET /inventory/movements
List inventory movements.

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "inventory_item_id": "item_uuid",
      "movement_type": "sale",
      "quantity": -10,
      "unit_cost": 15.50,
      "total_value": -155.00,
      "reference_type": "sales_order",
      "reference_id": "order_uuid",
      "movement_date": "2025-01-26T10:00:00Z",
      "notes": "Sold to customer ABC",
      "created_by": "user_uuid"
    }
  ]
}
```

### POST /inventory/movements
Record inventory movement.

### GET /inventory/reorder-alerts
Get items that need reordering.

### GET /inventory/valuation-report
Generate inventory valuation report.

## 🔗 Financial Integration API

### GET /financial-integration/dashboard/comprehensive
Get comprehensive financial dashboard.

**Query Parameters:**
- `organization_id` (uuid, required)
- `period` (enum): 1m, 3m, 6m, 12m, ytd
- `include_predictions` (bool): Include AI predictions
- `include_risk_analysis` (bool): Include risk analysis

**Response:**
```json
{
  "organization_id": "org_uuid",
  "period": "12m",
  "dashboard_data": {
    "financial_overview": {
      "total_revenue": 2500000.00,
      "total_expenses": 1800000.00,
      "net_profit": 700000.00,
      "profit_margin": 28.0,
      "cash_position": 450000.00
    },
    "project_financial_summary": {
      "total_budget": 1500000.00,
      "spent_amount": 850000.00,
      "remaining_budget": 650000.00,
      "budget_utilization": 56.7
    },
    "resource_cost_analysis": {
      "human_resources_cost": 1200000.00,
      "equipment_cost": 150000.00,
      "material_cost": 300000.00,
      "overhead_cost": 150000.00
    },
    "inventory_valuation": {
      "total_inventory_value": 500000.00,
      "fast_moving_items_value": 350000.00,
      "slow_moving_items_value": 150000.00
    }
  },
  "predictions": {
    "next_quarter_revenue": 650000.00,
    "cash_flow_forecast": [
      {"month": "2025-02", "forecast": 75000.00},
      {"month": "2025-03", "forecast": 85000.00}
    ]
  },
  "risk_analysis": {
    "cash_flow_risk": "low",
    "budget_overrun_risk": "medium",
    "inventory_risk": "low"
  },
  "last_updated": "2025-01-26T10:00:00Z"
}
```

### GET /financial-integration/metrics/real-time
Get real-time financial metrics.

### GET /financial-integration/analytics/cross-module
Get cross-module analytics.

## 🔄 Multi-Currency API

### GET /multi-currency/exchange-rates
List exchange rates.

### POST /multi-currency/exchange-rates
Create/update exchange rate.

### GET /multi-currency/transactions
List multi-currency transactions.

### POST /multi-currency/transactions
Create multi-currency transaction.

### GET /multi-currency/exposure-report
Generate currency exposure report.

## ⚡ Health & Monitoring API

### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "auth_service": "healthy"
  },
  "metrics": {
    "response_time_ms": 45,
    "memory_usage_mb": 256,
    "active_connections": 15
  }
}
```

### GET /health/detailed
Detailed health check with component status.

## 📊 Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Unprocessable Entity
- `429` - Too Many Requests
- `500` - Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2025-01-26T10:00:00Z",
  "request_id": "uuid-v4"
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED` - Missing or invalid token
- `PERMISSION_DENIED` - Insufficient permissions
- `VALIDATION_ERROR` - Invalid input data
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `DUPLICATE_RESOURCE` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `SYSTEM_ERROR` - Internal system error

## 🔒 Rate Limiting

### Rate Limits
- **Authentication endpoints**: 5 requests per minute
- **Read operations**: 100 requests per minute
- **Write operations**: 60 requests per minute
- **Report generation**: 10 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643289600
```

## 📄 Pagination

### Query Parameters
- `page` (int): Page number (1-based, default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)

### Response Format
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "has_next": true,
  "has_previous": false
}
```

## 🔍 Filtering & Searching

### Common Query Parameters
- `search` (string): Full-text search
- `sort_by` (string): Field to sort by
- `sort_order` (enum): asc, desc
- Date filters: `{field}_from`, `{field}_to`
- Range filters: `{field}_min`, `{field}_max`

### Example
```
GET /api/v1/projects?search=ERP&status=active&sort_by=created_at&sort_order=desc&start_date_from=2025-01-01&budget_min=100000
```

## 📚 OpenAPI Documentation

Interactive API documentation is available at:
- **Development**: `http://localhost:8000/docs`
- **Production**: `https://api.itdo-erp.com/docs`

Alternative ReDoc documentation:
- **Development**: `http://localhost:8000/redoc`
- **Production**: `https://api.itdo-erp.com/redoc`

## 🧪 Testing

### Test Environments
- **Development**: `http://localhost:8000/api/v1`
- **Staging**: `https://staging-api.itdo-erp.com/api/v1`
- **Production**: `https://api.itdo-erp.com/api/v1`

### Example cURL Commands

**Authentication:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username":"user@example.com","password":"password"}'
```

**List Projects:**
```bash
curl -X GET "http://localhost:8000/api/v1/projects?organization_id=org_uuid" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json"
```

**Create Project:**
```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name":"New Project","description":"Test project","start_date":"2025-02-01","end_date":"2025-08-31","budget":250000.00,"organization_id":"org_uuid"}'
```

---

## 📝 Document Information

- **Version**: 2.0
- **Last Updated**: 2025-01-26
- **API Version**: v1
- **OpenAPI Version**: 3.0.3

---

*This document is part of the ITDO ERP System v2 technical documentation suite.*