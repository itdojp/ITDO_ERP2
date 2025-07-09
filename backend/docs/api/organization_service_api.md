# Organization Service API Documentation

## Overview
Organization Service provides comprehensive management capabilities for organizational structures, including companies, subsidiaries, departments, and their relationships.

## Base URL
```
http://localhost:8000/api/v1/organizations
```

## Authentication
All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Core Endpoints

### 1. List Organizations
Get paginated list of organizations with filtering options.

**Endpoint:** `GET /`

**Parameters:**
- `skip` (int, optional): Number of items to skip (default: 0)
- `limit` (int, optional): Number of items to return (default: 100, max: 1000)
- `search` (string, optional): Search query for organization name
- `active_only` (bool, optional): Only return active organizations (default: true)
- `industry` (string, optional): Filter by industry category

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "code": "ACME-001",
      "name": "Acme Corporation",
      "name_en": "Acme Corporation",
      "is_active": true,
      "parent_id": null,
      "parent_name": null,
      "department_count": 5,
      "user_count": 25
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### 2. Get Organization by ID
Retrieve detailed information about a specific organization.

**Endpoint:** `GET /{organization_id}`

**Response:**
```json
{
  "id": 1,
  "code": "ACME-001",
  "name": "Acme Corporation",
  "name_en": "Acme Corporation",
  "is_active": true,
  "phone": "+81-3-1234-5678",
  "email": "contact@acme.co.jp",
  "website": "https://acme.co.jp",
  "postal_code": "100-0001",
  "prefecture": "Tokyo",
  "city": "Chiyoda",
  "address_line1": "1-1-1 Marunouchi",
  "full_address": "〒100-0001 Tokyo Chiyoda 1-1-1 Marunouchi",
  "business_type": "株式会社",
  "industry": "IT",
  "capital": 100000000,
  "employee_count": 250,
  "parent_id": null,
  "parent": null,
  "settings": {
    "fiscal_year_start": "04-01",
    "default_currency": "JPY",
    "time_zone": "Asia/Tokyo"
  },
  "is_subsidiary": false,
  "is_parent": true,
  "subsidiary_count": 3,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 3. Create Organization
Create a new organization.

**Endpoint:** `POST /`

**Request Body:**
```json
{
  "code": "NEW-ORG-001",
  "name": "New Organization",
  "name_en": "New Organization",
  "phone": "+81-3-1234-5678",
  "email": "contact@neworg.co.jp",
  "website": "https://neworg.co.jp",
  "postal_code": "100-0001",
  "prefecture": "Tokyo",
  "city": "Chiyoda",
  "address_line1": "1-1-1 Marunouchi",
  "business_type": "株式会社",
  "industry": "IT",
  "capital": 50000000,
  "employee_count": 100,
  "parent_id": null,
  "is_active": true,
  "settings": {
    "fiscal_year_start": "04-01",
    "default_currency": "JPY"
  }
}
```

**Response:** Organization object (same as GET /{organization_id})

### 4. Update Organization
Update an existing organization.

**Endpoint:** `PUT /{organization_id}`

**Request Body:** Partial organization data (same structure as POST, all fields optional)

**Response:** Updated organization object

### 5. Delete Organization
Soft delete an organization.

**Endpoint:** `DELETE /{organization_id}`

**Response:**
```json
{
  "success": true,
  "message": "Organization deleted successfully",
  "id": 1
}
```

## Enhanced Endpoints (Phase 2)

### 6. Get Organization by Code
Retrieve organization by unique code.

**Endpoint:** `GET /code/{code}`

**Example:** `GET /code/ACME-001`

**Response:** Organization object (same as GET /{organization_id})

### 7. Get Organization Statistics
Get detailed statistics for an organization.

**Endpoint:** `GET /{organization_id}/statistics`

**Response:**
```json
{
  "department_count": 5,
  "user_count": 25,
  "active_subsidiaries": 2,
  "total_subsidiaries": 3,
  "hierarchy_depth": 1
}
```

### 8. Update Organization Settings
Update organization-specific settings.

**Endpoint:** `PUT /{organization_id}/settings`

**Request Body:**
```json
{
  "fiscal_year_start": "04-01",
  "default_currency": "JPY",
  "time_zone": "Asia/Tokyo",
  "custom_fields": {
    "department_code_prefix": "DEPT-",
    "employee_id_format": "EMP-{:06d}"
  }
}
```

**Response:** Updated organization object

## Hierarchy Endpoints

### 9. Get Organization Tree
Get complete organization hierarchy as a tree structure.

**Endpoint:** `GET /tree`

**Response:**
```json
[
  {
    "id": 1,
    "code": "PARENT-ORG",
    "name": "Parent Organization",
    "is_active": true,
    "level": 0,
    "parent_id": null,
    "children": [
      {
        "id": 2,
        "code": "SUB-ORG-1",
        "name": "Subsidiary 1",
        "is_active": true,
        "level": 1,
        "parent_id": 1,
        "children": []
      }
    ]
  }
]
```

### 10. Get Subsidiaries
Get direct or recursive subsidiaries of an organization.

**Endpoint:** `GET /{organization_id}/subsidiaries`

**Parameters:**
- `recursive` (bool, optional): Get all subsidiaries recursively (default: false)

**Response:**
```json
[
  {
    "id": 2,
    "code": "SUB-ORG-1",
    "name": "Subsidiary 1",
    "name_en": "Subsidiary 1",
    "is_active": true
  }
]
```

## Status Management Endpoints

### 11. Activate Organization
Activate an inactive organization.

**Endpoint:** `POST /{organization_id}/activate`

**Response:** Updated organization object

### 12. Deactivate Organization
Deactivate an active organization.

**Endpoint:** `POST /{organization_id}/deactivate`

**Response:** Updated organization object

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes
- `PERMISSION_DENIED` (403): Insufficient permissions
- `NOT_FOUND` (404): Organization not found
- `DUPLICATE_CODE` (409): Organization code already exists
- `HAS_SUBSIDIARIES` (409): Cannot delete organization with active subsidiaries
- `VALIDATION_ERROR` (422): Invalid request data

## Permissions

### Required Permissions
- `organizations.read`: View organizations
- `organizations.create`: Create new organizations
- `organizations.update`: Update existing organizations
- `organizations.delete`: Delete organizations
- `organizations.activate`: Activate/deactivate organizations

### Administrative Operations
Most write operations require either:
1. Superuser status, OR
2. Specific organization permissions within the user's scope

## Usage Examples

### Search Organizations
```bash
curl -X GET "http://localhost:8000/api/v1/organizations?search=Acme&industry=IT" \
  -H "Authorization: Bearer <token>"
```

### Create Subsidiary
```bash
curl -X POST "http://localhost:8000/api/v1/organizations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ACME-SUB-001",
    "name": "Acme Subsidiary",
    "parent_id": 1,
    "is_active": true
  }'
```

### Update Settings
```bash
curl -X PUT "http://localhost:8000/api/v1/organizations/1/settings" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year_start": "01-01",
    "default_currency": "USD"
  }'
```

### Get Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/organizations/1/statistics" \
  -H "Authorization: Bearer <token>"
```

## Notes

1. **JSON Settings**: The `settings` field accepts arbitrary JSON data for organization-specific configuration.

2. **Hierarchy Validation**: Circular references in organization hierarchy are automatically prevented.

3. **Soft Delete**: Organizations are soft deleted by default to maintain referential integrity.

4. **Audit Trail**: All modifications include audit information (created_by, updated_by, timestamps).

5. **Performance**: Large result sets are paginated. Use appropriate `limit` and `skip` parameters.