#!/usr/bin/env python3
"""
CC02 v37.0 Phase 3: API Documentation Generator
自動的にOpenAPI/Swagger定義を生成し、API仕様書を改善
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi.openapi.utils import get_openapi

from app.main import app


async def generate_api_documentation():
    """Generate comprehensive API documentation."""
    print("🔧 CC02 v37.0 Phase 3: Generating API Documentation...")

    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title="ITDO ERP System API v2",
        version="2.0.0",
        description="""
        # ITDO ERP System API v2.0
        
        A comprehensive Enterprise Resource Planning system with modern architecture.
        
        ## Features
        - User and Organization Management
        - Project and Task Management
        - Financial Management (Budgets, Expenses, Reports)
        - Inventory and Product Management
        - Customer Relationship Management (CRM)
        - Workflow and Application Management
        - Security Audit and Performance Monitoring
        
        ## Authentication
        This API uses OAuth2 with Bearer tokens. Include your token in the Authorization header:
        ```
        Authorization: Bearer <your-token>
        ```
        
        ## Rate Limiting
        API calls are rate-limited to prevent abuse. Current limits:
        - 1000 requests per hour for authenticated users
        - 100 requests per hour for unauthenticated endpoints
        
        ## Error Responses
        All error responses follow RFC 7807 Problem Details format:
        ```json
        {
            "type": "https://example.com/probs/out-of-credit",
            "title": "You do not have enough credit.",
            "status": 403,
            "detail": "Your current balance is 30, but that costs 50.",
            "instance": "/account/12345/msgs/abc"
        }
        ```
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.itdo-erp.com", "description": "Production server"}
        ]
    )

    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "ITDO ERP Support",
        "email": "support@itdo-erp.com",
        "url": "https://docs.itdo-erp.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://auth.itdo-erp.com/oauth/authorize",
                    "tokenUrl": "https://auth.itdo-erp.com/oauth/token",
                    "scopes": {
                        "read": "Read access to resources",
                        "write": "Write access to resources",
                        "admin": "Administrative access"
                    }
                }
            }
        }
    }

    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"OAuth2": ["read", "write"]}
    ]

    # Add tags with descriptions
    openapi_schema["tags"] = [
        {"name": "health", "description": "System health and status endpoints"},
        {"name": "auth", "description": "Authentication and authorization"},
        {"name": "users", "description": "User management operations"},
        {"name": "organizations", "description": "Organization management"},
        {"name": "projects", "description": "Project and task management"},
        {"name": "financial", "description": "Financial management (budgets, expenses, reports)"},
        {"name": "inventory", "description": "Inventory and product management"},
        {"name": "crm", "description": "Customer relationship management"},
        {"name": "workflow", "description": "Workflow and application management"},
        {"name": "security", "description": "Security audit and monitoring"},
        {"name": "monitoring", "description": "Performance monitoring and metrics"},
        {"name": "analytics", "description": "Business analytics and reporting"}
    ]

    # Save OpenAPI spec in multiple formats
    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # JSON format
    with open(docs_dir / "openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    # YAML format
    with open(docs_dir / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)

    print("✅ OpenAPI documentation generated:")
    print(f"   - JSON: {docs_dir / 'openapi.json'}")
    print(f"   - YAML: {docs_dir / 'openapi.yaml'}")

    # Generate API reference documentation
    await generate_api_reference(openapi_schema, docs_dir)

    return openapi_schema


async def generate_api_reference(schema: Dict[str, Any], docs_dir: Path):
    """Generate human-readable API reference documentation."""
    print("📚 Generating API Reference Documentation...")

    reference_md = []
    reference_md.append("# ITDO ERP API Reference\n")
    reference_md.append("Generated automatically from OpenAPI specification.\n")
    reference_md.append(f"**Version:** {schema['info']['version']}\n")
    reference_md.append(f"**Description:** {schema['info']['description']}\n")

    # Group endpoints by tags
    paths = schema.get("paths", {})
    endpoints_by_tag = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                tags = details.get("tags", ["untagged"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "details": details
                    })

    # Generate documentation for each tag
    for tag, endpoints in sorted(endpoints_by_tag.items()):
        tag_info = next((t for t in schema.get("tags", []) if t["name"] == tag), {"description": ""})

        reference_md.append(f"\n## {tag.title()}\n")
        if tag_info.get("description"):
            reference_md.append(f"{tag_info['description']}\n")

        for endpoint in sorted(endpoints, key=lambda x: (x["path"], x["method"])):
            reference_md.append(f"\n### {endpoint['method']} {endpoint['path']}\n")

            details = endpoint["details"]
            if details.get("summary"):
                reference_md.append(f"**Summary:** {details['summary']}\n")

            if details.get("description"):
                reference_md.append(f"**Description:** {details['description']}\n")

            # Parameters
            if details.get("parameters"):
                reference_md.append("**Parameters:**\n")
                for param in details["parameters"]:
                    required = " (required)" if param.get("required") else " (optional)"
                    reference_md.append(f"- `{param['name']}` ({param['in']}){required}: {param.get('description', 'No description')}\n")

            # Request body
            if details.get("requestBody"):
                reference_md.append("**Request Body:**\n")
                content = details["requestBody"].get("content", {})
                for media_type, schema_info in content.items():
                    reference_md.append(f"- Content-Type: `{media_type}`\n")
                    if schema_info.get("schema", {}).get("$ref"):
                        schema_name = schema_info["schema"]["$ref"].split("/")[-1]
                        reference_md.append(f"- Schema: `{schema_name}`\n")

            # Responses
            if details.get("responses"):
                reference_md.append("**Responses:**\n")
                for status_code, response in details["responses"].items():
                    description = response.get("description", "No description")
                    reference_md.append(f"- `{status_code}`: {description}\n")

    # Save reference documentation
    reference_file = docs_dir / "api-reference.md"
    with open(reference_file, "w", encoding="utf-8") as f:
        f.write("".join(reference_md))

    print(f"✅ API Reference documentation generated: {reference_file}")

    # Generate API examples
    await generate_api_examples(schema, docs_dir)


async def generate_api_examples(schema: Dict[str, Any], docs_dir: Path):
    """Generate API usage examples."""
    print("💡 Generating API Usage Examples...")

    examples_dir = docs_dir / "examples"
    examples_dir.mkdir(exist_ok=True)

    # Common examples
    examples = {
        "authentication.md": """# Authentication Examples

## Bearer Token Authentication

```bash
# Get user profile
curl -X GET "http://localhost:8000/api/v1/users/me" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -H "Content-Type: application/json"
```

## Login Example

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "user@example.com",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```
""",

        "user_management.md": """# User Management Examples

## Create User

```bash
curl -X POST "http://localhost:8000/api/v1/users" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "full_name": "New User",
    "is_active": true
  }'
```

## List Users with Pagination

```bash
curl -X GET "http://localhost:8000/api/v1/users?limit=10&offset=0" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Update User

```bash
curl -X PUT "http://localhost:8000/api/v1/users/123" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "full_name": "Updated Name",
    "is_active": true
  }'
```
""",

        "error_handling.md": """# Error Handling Examples

## Standard Error Response Format

All API errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://docs.itdo-erp.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request contains invalid data",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

## Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data  
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

When rate limits are exceeded:

```json
{
  "type": "https://docs.itdo-erp.com/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "API rate limit exceeded. Try again later.",
  "instance": "/api/v1/users",
  "retry_after": 3600
}
```
"""
    }

    # Write example files
    for filename, content in examples.items():
        example_file = examples_dir / filename
        with open(example_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Example generated: {example_file}")


async def validate_api_documentation():
    """Validate generated API documentation."""
    print("🔍 Validating API Documentation...")

    docs_dir = Path("docs/api")

    # Check if files exist
    required_files = [
        "openapi.json",
        "openapi.yaml",
        "api-reference.md",
        "examples/authentication.md",
        "examples/user_management.md",
        "examples/error_handling.md"
    ]

    for file_path in required_files:
        full_path = docs_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing: {full_path}")
            return False
        print(f"✅ Found: {full_path}")

    # Validate OpenAPI schema
    try:
        with open(docs_dir / "openapi.json", "r") as f:
            schema = json.load(f)

        required_schema_fields = ["openapi", "info", "paths"]
        for field in required_schema_fields:
            if field not in schema:
                print(f"❌ Missing OpenAPI field: {field}")
                return False

        print("✅ OpenAPI schema validation passed")
        print(f"   - Endpoints: {len(schema.get('paths', {}))}")
        print(f"   - Components: {len(schema.get('components', {}).get('schemas', {}))}")

        return True
    except Exception as e:
        print(f"❌ OpenAPI schema validation failed: {e}")
        return False


async def main():
    """Main function for API documentation generation."""
    print("🚀 Starting CC02 v37.0 Phase 3: API Quality Improvement")
    print("=" * 60)

    try:
        # Generate documentation
        schema = await generate_api_documentation()

        # Validate documentation
        is_valid = await validate_api_documentation()

        if is_valid:
            print("\n🎉 API Documentation Generation Complete!")
            print("=" * 60)
            print("📁 Generated Files:")
            print("   - docs/api/openapi.json")
            print("   - docs/api/openapi.yaml")
            print("   - docs/api/api-reference.md")
            print("   - docs/api/examples/*.md")
            print("\n🔗 Next Steps:")
            print("   - Review generated documentation")
            print("   - Update API descriptions as needed")
            print("   - Deploy to documentation portal")
            return True
        else:
            print("\n❌ Documentation validation failed!")
            return False

    except Exception as e:
        print(f"\n❌ Error generating API documentation: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
