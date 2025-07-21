# API Versioning Strategy - ITDO ERP System

## Overview

The ITDO ERP System implements a comprehensive API versioning strategy to ensure backward compatibility, smooth migrations, and clear deprecation policies.

## Versioning Strategy

### 1. URL-based Versioning (Primary)

API versions are specified in the URL path:
- `GET /api/v1/users` - Version 1
- `GET /api/v2/users` - Version 2
- `GET /api/v2.1/users` - Version 2.1 (minor update)

### 2. Header-based Versioning (Alternative)

When URL versioning is not practical:
```http
GET /api/users
API-Version: v2
```

### 3. Default Version

When no version is specified, the system defaults to `v1` for backward compatibility.

## Version Lifecycle

### 1. Development Phase
- New versions start in development
- Breaking changes are allowed
- Documentation is updated continuously

### 2. Stable Release
- Version becomes publicly available
- API contracts are frozen
- Only backward-compatible changes allowed

### 3. Deprecation
- Minimum 6-month deprecation notice
- Deprecation warnings in response headers
- Migration guides provided

### 4. Sunset/Removal
- Version is removed after sunset date
- Clients receive 410 Gone responses

## Response Headers

### Deprecation Headers (RFC 8594)

For deprecated versions:
```http
Deprecation: true; date="Fri, 11 Nov 2024 23:59:59 GMT"
Sunset: Fri, 11 May 2025 23:59:59 GMT
Warning: 299 - "API version v1 is deprecated and will be removed on 2025-05-11"
```

### Version Information

All responses include:
```http
API-Version: v2
API-Supported-Versions: v1, v2, v2.1
```

## Version Discovery

### API Versions Endpoint

```http
GET /api/versions
```

Response:
```json
{
  "supported_versions": ["v1", "v2"],
  "default_version": "v1",
  "versions": {
    "v1": {
      "description": "ITDO ERP API Version 1 - Initial release",
      "docs_url": "/api/v1/docs",
      "openapi_url": "/api/v1/openapi.json",
      "deprecated": true,
      "deprecation_info": {
        "deprecation_date": "2024-12-31T00:00:00Z",
        "removal_date": "2025-06-30T00:00:00Z",
        "warning": "API version v1 is deprecated..."
      }
    },
    "v2": {
      "description": "ITDO ERP API Version 2 - Enhanced features",
      "docs_url": "/api/v2/docs",
      "openapi_url": "/api/v2/openapi.json",
      "deprecated": false,
      "deprecation_info": null
    }
  }
}
```

## Breaking Changes Policy

### What Constitutes a Breaking Change

1. **Removing endpoints** - Requires major version bump
2. **Removing response fields** - Requires major version bump
3. **Changing field types** - Requires major version bump
4. **Changing required parameters** - Requires major version bump
5. **Changing error response formats** - Requires major version bump

### Non-breaking Changes

1. **Adding new endpoints** - Minor version bump
2. **Adding optional parameters** - Minor version bump
3. **Adding response fields** - Minor version bump
4. **Bug fixes** - Patch version bump

## Migration Guidelines

### For API Consumers

1. **Always specify version** in your requests
2. **Monitor deprecation headers** for sunset notices
3. **Use version discovery** to check supported versions
4. **Test against new versions** before migration
5. **Update gradually** rather than all at once

### Migration Process

1. **Review changelog** for breaking changes
2. **Update client code** to handle new formats
3. **Test thoroughly** against new version
4. **Deploy gradually** with feature flags
5. **Monitor error rates** during migration

## Code Examples

### Version Detection in Middleware

```python
from app.core.versioning import get_version_from_request

def get_api_version(request: Request) -> str:
    return get_version_from_request(request)
```

### Version Validation

```python
from app.core.versioning import validate_version, version_manager

version = get_version_from_request(request)
if not version_manager.is_supported(version):
    raise HTTPException(400, f"Unsupported version: {version}")
```

### Deprecation Management

```python
from datetime import datetime, timedelta
from app.core.versioning import version_manager

# Deprecate a version
version_manager.deprecate_version(
    "v1",
    deprecation_date=datetime(2024, 12, 31),
    removal_date=datetime(2025, 6, 30)
)
```

## Testing Strategy

### Version-specific Tests

```python
def test_v1_user_response():
    response = client.get("/api/v1/users/1")
    assert "id" in response.json()  # v1 format

def test_v2_user_response():
    response = client.get("/api/v2/users/1")
    assert "user_id" in response.json()  # v2 format
```

### Deprecation Header Tests

```python
def test_deprecated_version_headers():
    response = client.get("/api/v1/users")
    assert "Deprecation" in response.headers
    assert "Sunset" in response.headers
```

## Monitoring and Analytics

### Version Usage Tracking

- Monitor version usage in access logs
- Track deprecation warning acknowledgment
- Measure migration progress over time

### Metrics to Track

1. **Requests per version** - Usage distribution
2. **Error rates by version** - Quality metrics
3. **Migration velocity** - Adoption of new versions
4. **Client distribution** - Which clients use which versions

## Best Practices

### For API Designers

1. **Design for compatibility** from the start
2. **Use semantic versioning** consistently
3. **Provide clear migration paths**
4. **Document all changes** thoroughly
5. **Maintain backward compatibility** when possible

### For API Consumers

1. **Pin to specific versions** in production
2. **Handle version errors gracefully**
3. **Monitor deprecation notices**
4. **Test new versions early**
5. **Automate version checking**

## Troubleshooting

### Common Issues

1. **Unsupported Version Error**
   - Solution: Check `/api/versions` for supported versions

2. **Missing Version Headers**
   - Solution: Ensure middleware is properly configured

3. **Unexpected Response Format**
   - Solution: Verify correct version is being used

4. **Deprecation Warnings**
   - Solution: Plan migration to newer version

## Related Documentation

- [API Authentication Guide](./api_authentication.md)
- [Breaking Changes Changelog](./api_changelog.md)
- [Client SDK Documentation](./client_sdks.md)
- [OpenAPI Specifications](./openapi_specs/)