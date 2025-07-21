"""Client SDK generator for API versioning system."""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from pydantic import BaseModel

from app.core.versioning import SemanticVersion, APIVersionInfo


class SDKLanguage(str):
    """Supported SDK languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"


class APIEndpoint(BaseModel):
    """API endpoint definition for SDK generation."""
    path: str
    method: str
    operation_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = {}
    tags: List[str] = []
    deprecated: bool = False
    min_version: Optional[str] = None
    max_version: Optional[str] = None


class SDKConfiguration(BaseModel):
    """SDK generation configuration."""
    package_name: str
    version: str
    language: str
    api_base_url: str
    authentication_type: str = "bearer"  # bearer, basic, api_key
    timeout: int = 30
    retry_attempts: int = 3
    include_models: bool = True
    include_examples: bool = True
    include_tests: bool = True
    output_directory: str = "./sdk"
    
    # Language-specific settings
    python_min_version: str = "3.8"
    node_min_version: str = "14.0.0"
    go_module_name: Optional[str] = None
    java_package: Optional[str] = None
    namespace: Optional[str] = None  # For C#


class BaseSDKGenerator(ABC):
    """Base class for SDK generators."""
    
    def __init__(self, config: SDKConfiguration):
        """Initialize SDK generator."""
        self.config = config
        self.endpoints: List[APIEndpoint] = []
        self.models: Dict[str, Dict[str, Any]] = {}
        self.version_info: Optional[APIVersionInfo] = None
    
    def add_endpoint(self, endpoint: APIEndpoint) -> None:
        """Add endpoint to SDK."""
        self.endpoints.append(endpoint)
    
    def add_model(self, name: str, schema: Dict[str, Any]) -> None:
        """Add model schema to SDK."""
        self.models[name] = schema
    
    def set_version_info(self, version_info: APIVersionInfo) -> None:
        """Set API version information."""
        self.version_info = version_info
    
    @abstractmethod
    def generate(self) -> Dict[str, str]:
        """Generate SDK files."""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for the language."""
        pass
    
    def write_files(self, output_dir: Optional[str] = None) -> List[str]:
        """Write generated files to disk."""
        output_dir = output_dir or self.config.output_directory
        os.makedirs(output_dir, exist_ok=True)
        
        files = self.generate()
        written_files = []
        
        for filename, content in files.items():
            file_path = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            written_files.append(file_path)
        
        return written_files


class PythonSDKGenerator(BaseSDKGenerator):
    """Python SDK generator."""
    
    def get_file_extension(self) -> str:
        return ".py"
    
    def generate(self) -> Dict[str, str]:
        """Generate Python SDK files."""
        files = {}
        
        # Main client file
        files["client.py"] = self._generate_client()
        
        # Models file
        if self.config.include_models and self.models:
            files["models.py"] = self._generate_models()
        
        # Exceptions file
        files["exceptions.py"] = self._generate_exceptions()
        
        # Configuration file
        files["config.py"] = self._generate_config()
        
        # Package init file
        files["__init__.py"] = self._generate_init()
        
        # Setup file
        files["setup.py"] = self._generate_setup()
        
        # Requirements file
        files["requirements.txt"] = self._generate_requirements()
        
        # README
        files["README.md"] = self._generate_readme()
        
        if self.config.include_tests:
            files["tests/test_client.py"] = self._generate_tests()
            files["tests/__init__.py"] = ""
        
        return files
    
    def _generate_client(self) -> str:
        """Generate main client class."""
        methods = []
        
        for endpoint in self.endpoints:
            methods.append(self._generate_method(endpoint))
        
        return f'''"""
{self.config.package_name} API Client

Generated on: {datetime.utcnow().isoformat()}
API Version: {self.config.version}
"""

import requests
from typing import Any, Dict, List, Optional, Union
from .config import Config
from .exceptions import APIError, AuthenticationError, ValidationError
from .models import *


class {self._to_pascal_case(self.config.package_name)}Client:
    """API client for {self.config.package_name}."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """Initialize API client."""
        self.config = Config(
            api_key=api_key,
            base_url=base_url or "{self.config.api_base_url}",
            timeout=timeout or {self.config.timeout}
        )
        self.session = requests.Session()
        self._setup_authentication()
    
    def _setup_authentication(self) -> None:
        """Setup authentication headers."""
        if self.config.api_key:
            self.session.headers.update({{
                "Authorization": f"Bearer {{self.config.api_key}}",
                "Content-Type": "application/json",
                "User-Agent": f"{self.config.package_name}-python-sdk/{self.config.version}"
            }})
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{{self.config.base_url}}{{endpoint}}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid authentication credentials")
            elif response.status_code == 422:
                raise ValidationError("Request validation failed", response.json())
            elif response.status_code >= 400:
                raise APIError(f"API request failed with status {{response.status_code}}", response)
            
            return response.json() if response.content else {{}}
        
        except requests.RequestException as e:
            raise APIError(f"Request failed: {{str(e)}}")

{chr(10).join(methods)}
'''
    
    def _generate_method(self, endpoint: APIEndpoint) -> str:
        """Generate method for endpoint."""
        method_name = self._to_snake_case(endpoint.operation_id or f"{endpoint.method}_{endpoint.path}")
        
        # Extract path parameters
        path_params = []
        query_params = []
        
        for param in endpoint.parameters:
            if param.get("in") == "path":
                path_params.append(param["name"])
            elif param.get("in") == "query":
                query_params.append(param["name"])
        
        # Build method signature
        params = []
        for param_name in path_params:
            params.append(f"{param_name}: str")
        
        for param_name in query_params:
            params.append(f"{param_name}: Optional[Any] = None")
        
        if endpoint.request_body:
            params.append("data: Optional[Dict[str, Any]] = None")
        
        params_str = ", ".join(params)
        if params_str:
            params_str = ", " + params_str
        
        # Build path formatting
        path = endpoint.path
        for param_name in path_params:
            path = path.replace(f"{{{param_name}}}", f"{{f{param_name}}}")
        
        deprecation_warning = ""
        if endpoint.deprecated:
            deprecation_warning = '''
        import warnings
        warnings.warn(
            f"Method {method_name} is deprecated",
            DeprecationWarning,
            stacklevel=2
        )'''
        
        return f'''
    def {method_name}(self{params_str}) -> Dict[str, Any]:
        """
        {endpoint.summary or f"{endpoint.method.upper()} {endpoint.path}"}
        
        {endpoint.description or ""}
        """
        {deprecation_warning}
        
        endpoint = f"{path}"
        
        # Build query parameters
        query_params = {{}}
        {chr(10).join(f'        if {param} is not None: query_params["{param}"] = {param}' for param in query_params)}
        
        return self._make_request(
            method="{endpoint.method.upper()}",
            endpoint=endpoint,
            params=query_params if query_params else None,
            data=data if "{endpoint.request_body}" else None
        )'''
    
    def _generate_models(self) -> str:
        """Generate Pydantic models."""
        models_code = '''"""
Data models for API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


'''
        
        for model_name, schema in self.models.items():
            models_code += self._generate_pydantic_model(model_name, schema)
            models_code += "\n\n"
        
        return models_code
    
    def _generate_pydantic_model(self, name: str, schema: Dict[str, Any]) -> str:
        """Generate a Pydantic model from schema."""
        fields = []
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for field_name, field_schema in properties.items():
            field_type = self._get_python_type(field_schema)
            is_required = field_name in required
            
            if is_required:
                fields.append(f"    {field_name}: {field_type}")
            else:
                fields.append(f"    {field_name}: Optional[{field_type}] = None")
        
        return f'''class {name}(BaseModel):
    """{schema.get("description", f"{name} model")}"""
    
{chr(10).join(fields) if fields else "    pass"}'''
    
    def _get_python_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema type to Python type."""
        schema_type = schema.get("type", "string")
        
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": f"List[{self._get_python_type(schema.get('items', {'type': 'string'}))}]",
            "object": "Dict[str, Any]"
        }
        
        return type_mapping.get(schema_type, "Any")
    
    def _generate_exceptions(self) -> str:
        """Generate exception classes."""
        return '''"""
API exception classes.
"""


class APIError(Exception):
    """Base API exception."""
    
    def __init__(self, message: str, response=None):
        super().__init__(message)
        self.response = response


class AuthenticationError(APIError):
    """Authentication failed."""
    pass


class ValidationError(APIError):
    """Request validation failed."""
    
    def __init__(self, message: str, errors=None):
        super().__init__(message)
        self.errors = errors or {}
'''
    
    def _generate_config(self) -> str:
        """Generate configuration class."""
        return f'''"""
Configuration for API client.
"""

from typing import Optional


class Config:
    """API client configuration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "{self.config.api_base_url}",
        timeout: int = {self.config.timeout}
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
'''
    
    def _generate_init(self) -> str:
        """Generate package __init__.py file."""
        return f'''"""
{self.config.package_name} Python SDK

API Version: {self.config.version}
"""

from .client import {self._to_pascal_case(self.config.package_name)}Client
from .exceptions import APIError, AuthenticationError, ValidationError

__version__ = "{self.config.version}"
__all__ = ["{self._to_pascal_case(self.config.package_name)}Client", "APIError", "AuthenticationError", "ValidationError"]
'''
    
    def _generate_setup(self) -> str:
        """Generate setup.py file."""
        return f'''"""
Setup configuration for {self.config.package_name} Python SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{self.config.package_name}",
    version="{self.config.version}",
    author="API Team",
    description="Python SDK for {self.config.package_name} API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">={self.config.python_min_version}",
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    extras_require={{
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "mypy>=0.800",
        ]
    }}
)
'''
    
    def _generate_requirements(self) -> str:
        """Generate requirements.txt file."""
        return f'''requests>=2.25.0
pydantic>=1.8.0
'''
    
    def _generate_readme(self) -> str:
        """Generate README.md file."""
        return f'''# {self.config.package_name} Python SDK

Python client library for the {self.config.package_name} API.

## Installation

```bash
pip install {self.config.package_name}
```

## Quick Start

```python
from {self.config.package_name} import {self._to_pascal_case(self.config.package_name)}Client

# Initialize client
client = {self._to_pascal_case(self.config.package_name)}Client(api_key="your-api-key")

# Make API calls
# result = client.some_method()
```

## Authentication

This SDK supports Bearer token authentication. Set your API key when initializing the client:

```python
client = {self._to_pascal_case(self.config.package_name)}Client(api_key="your-api-key")
```

## API Version

This SDK is compatible with API version {self.config.version}.

## Error Handling

```python
from {self.config.package_name} import APIError, AuthenticationError, ValidationError

try:
    result = client.some_method()
except AuthenticationError:
    print("Authentication failed")
except ValidationError as e:
    print(f"Validation error: {{e.errors}}")
except APIError as e:
    print(f"API error: {{e}}")
```

## Documentation

For detailed API documentation, visit: [API Documentation]({self.config.api_base_url}/docs)

## Support

For support and questions, please contact the API team.
'''
    
    def _generate_tests(self) -> str:
        """Generate basic test file."""
        return f'''"""
Tests for {self.config.package_name} SDK.
"""

import pytest
from unittest.mock import Mock, patch
from {self.config.package_name} import {self._to_pascal_case(self.config.package_name)}Client, APIError


class Test{self._to_pascal_case(self.config.package_name)}Client:
    """Test cases for API client."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = {self._to_pascal_case(self.config.package_name)}Client(api_key="test-key")
    
    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.config.api_key == "test-key"
        assert self.client.config.base_url == "{self.config.api_base_url}"
    
    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"success": True}}
        mock_request.return_value = mock_response
        
        result = self.client._make_request("GET", "/test")
        assert result == {{"success": True}}
    
    @patch('requests.Session.request')
    def test_authentication_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with pytest.raises(APIError):
            self.client._make_request("GET", "/test")
'''
    
    def _to_snake_case(self, name: str) -> str:
        """Convert string to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert string to PascalCase."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


class TypeScriptSDKGenerator(BaseSDKGenerator):
    """TypeScript SDK generator."""
    
    def get_file_extension(self) -> str:
        return ".ts"
    
    def generate(self) -> Dict[str, str]:
        """Generate TypeScript SDK files."""
        files = {}
        
        # Main client file
        files["src/client.ts"] = self._generate_client()
        
        # Types file
        files["src/types.ts"] = self._generate_types()
        
        # Configuration file
        files["src/config.ts"] = self._generate_config()
        
        # Index file
        files["src/index.ts"] = self._generate_index()
        
        # Package.json
        files["package.json"] = self._generate_package_json()
        
        # TypeScript config
        files["tsconfig.json"] = self._generate_tsconfig()
        
        # README
        files["README.md"] = self._generate_readme()
        
        return files
    
    def _generate_client(self) -> str:
        """Generate TypeScript client."""
        methods = []
        
        for endpoint in self.endpoints:
            methods.append(self._generate_method(endpoint))
        
        return f'''/**
 * {self.config.package_name} API Client
 * 
 * Generated on: {datetime.utcnow().isoformat()}
 * API Version: {self.config.version}
 */

import {{ Config }} from './config';
import {{ APIError, AuthenticationError, ValidationError }} from './errors';
import * as Types from './types';

export class {self._to_pascal_case(self.config.package_name)}Client {{
  private config: Config;
  
  constructor(options: {{
    apiKey?: string;
    baseUrl?: string;
    timeout?: number;
  }} = {{}}) {{
    this.config = new Config({{
      apiKey: options.apiKey,
      baseUrl: options.baseUrl || '{self.config.api_base_url}',
      timeout: options.timeout || {self.config.timeout}
    }});
  }}
  
  private async makeRequest<T>(
    method: string,
    endpoint: string,
    options: {{
      params?: Record<string, any>;
      data?: any;
      headers?: Record<string, string>;
    }} = {{}}
  ): Promise<T> {{
    const url = `${{this.config.baseUrl}}${{endpoint}}`;
    const headers = {{
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${{this.config.apiKey}}`,
      'User-Agent': `{self.config.package_name}-typescript-sdk/{self.config.version}`,
      ...options.headers
    }};
    
    try {{
      const response = await fetch(url, {{
        method,
        headers,
        body: options.data ? JSON.stringify(options.data) : undefined,
        signal: AbortSignal.timeout(this.config.timeout * 1000)
      }});
      
      if (response.status === 401) {{
        throw new AuthenticationError('Invalid authentication credentials');
      }}
      
      if (response.status === 422) {{
        const errorData = await response.json();
        throw new ValidationError('Request validation failed', errorData);
      }}
      
      if (response.status >= 400) {{
        throw new APIError(`API request failed with status ${{response.status}}`);
      }}
      
      return response.json();
    }} catch (error) {{
      if (error instanceof APIError) {{
        throw error;
      }}
      throw new APIError(`Request failed: ${{error.message}}`);
    }}
  }}

{chr(10).join(methods)}
}}
'''
    
    def _generate_method(self, endpoint: APIEndpoint) -> str:
        """Generate TypeScript method."""
        method_name = self._to_camel_case(endpoint.operation_id or f"{endpoint.method}_{endpoint.path}")
        
        # Build parameters
        params = []
        path_params = []
        
        for param in endpoint.parameters:
            param_name = param["name"]
            param_type = self._get_typescript_type(param.get("schema", {"type": "string"}))
            
            if param.get("in") == "path":
                path_params.append(param_name)
                params.append(f"{param_name}: {param_type}")
            elif param.get("in") == "query":
                params.append(f"{param_name}?: {param_type}")
        
        if endpoint.request_body:
            params.append("data?: any")
        
        params_str = params[0] if len(params) == 1 else f"options: {{ {'; '.join(params)} }}"
        
        # Build path
        path = endpoint.path
        for param_name in path_params:
            path = path.replace(f"{{{param_name}}}", f"${{options.{param_name}}}")
        
        return_type = "Promise<any>"  # Could be more specific based on response schema
        
        return f'''
  /**
   * {endpoint.summary or f"{endpoint.method.upper()} {endpoint.path}"}
   * {endpoint.description or ""}
   */
  async {method_name}({params_str if params else ""}): {return_type} {{
    const endpoint = `{path}`;
    
    return this.makeRequest(
      '{endpoint.method.upper()}',
      endpoint,
      {{
        data: {params and 'data' in [p.split(':')[0] for p in params] and 'data' or 'undefined'}
      }}
    );
  }}'''
    
    def _generate_types(self) -> str:
        """Generate TypeScript type definitions."""
        types_code = f'''/**
 * Type definitions for {self.config.package_name} API
 */

'''
        
        for model_name, schema in self.models.items():
            types_code += self._generate_typescript_interface(model_name, schema)
            types_code += "\n\n"
        
        return types_code
    
    def _generate_typescript_interface(self, name: str, schema: Dict[str, Any]) -> str:
        """Generate TypeScript interface."""
        fields = []
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for field_name, field_schema in properties.items():
            field_type = self._get_typescript_type(field_schema)
            is_required = field_name in required
            optional_marker = "" if is_required else "?"
            
            fields.append(f"  {field_name}{optional_marker}: {field_type};")
        
        return f'''export interface {name} {{
  /** {schema.get("description", f"{name} interface")} */
{chr(10).join(fields) if fields else "  // No properties defined"}
}}'''
    
    def _get_typescript_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema type to TypeScript type."""
        schema_type = schema.get("type", "string")
        
        type_mapping = {
            "string": "string",
            "integer": "number",
            "number": "number",
            "boolean": "boolean",
            "array": f"Array<{self._get_typescript_type(schema.get('items', {'type': 'string'}))}>",
            "object": "Record<string, any>"
        }
        
        return type_mapping.get(schema_type, "any")
    
    def _generate_config(self) -> str:
        """Generate TypeScript config class."""
        return f'''/**
 * Configuration for API client
 */

export class Config {{
  public readonly apiKey?: string;
  public readonly baseUrl: string;
  public readonly timeout: number;
  
  constructor(options: {{
    apiKey?: string;
    baseUrl?: string;
    timeout?: number;
  }}) {{
    this.apiKey = options.apiKey;
    this.baseUrl = options.baseUrl?.replace(/\/$/, '') || '{self.config.api_base_url}';
    this.timeout = options.timeout || {self.config.timeout};
  }}
}}
'''
    
    def _generate_index(self) -> str:
        """Generate index.ts file."""
        return f'''/**
 * {self.config.package_name} TypeScript SDK
 * 
 * API Version: {self.config.version}
 */

export {{ {self._to_pascal_case(self.config.package_name)}Client }} from './client';
export * as Types from './types';
export {{ Config }} from './config';
export {{ APIError, AuthenticationError, ValidationError }} from './errors';
'''
    
    def _generate_package_json(self) -> str:
        """Generate package.json file."""
        package_data = {
            "name": self.config.package_name,
            "version": self.config.version,
            "description": f"TypeScript SDK for {self.config.package_name} API",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "lint": "eslint src/**/*.ts",
                "format": "prettier --write src/**/*.ts"
            },
            "keywords": ["api", "sdk", "typescript"],
            "author": "API Team",
            "license": "MIT",
            "devDependencies": {
                "typescript": "^4.5.0",
                "@types/node": "^16.0.0",
                "jest": "^27.0.0",
                "@types/jest": "^27.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.5.0"
            },
            "dependencies": {
                "node-fetch": "^3.0.0"
            },
            "engines": {
                "node": f">={self.config.node_min_version}"
            }
        }
        
        return json.dumps(package_data, indent=2)
    
    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json file."""
        config = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "lib": ["ES2020"],
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "**/*.test.ts"]
        }
        
        return json.dumps(config, indent=2)
    
    def _generate_readme(self) -> str:
        """Generate README.md file."""
        return f'''# {self.config.package_name} TypeScript SDK

TypeScript/JavaScript client library for the {self.config.package_name} API.

## Installation

```bash
npm install {self.config.package_name}
# or
yarn add {self.config.package_name}
```

## Quick Start

```typescript
import {{ {self._to_pascal_case(self.config.package_name)}Client }} from '{self.config.package_name}';

// Initialize client
const client = new {self._to_pascal_case(self.config.package_name)}Client({{
  apiKey: 'your-api-key'
}});

// Make API calls
// const result = await client.someMethod();
```

## Authentication

This SDK supports Bearer token authentication:

```typescript
const client = new {self._to_pascal_case(self.config.package_name)}Client({{
  apiKey: 'your-api-key'
}});
```

## API Version

This SDK is compatible with API version {self.config.version}.

## Error Handling

```typescript
import {{ APIError, AuthenticationError, ValidationError }} from '{self.config.package_name}';

try {{
  const result = await client.someMethod();
}} catch (error) {{
  if (error instanceof AuthenticationError) {{
    console.log('Authentication failed');
  }} else if (error instanceof ValidationError) {{
    console.log('Validation error:', error.errors);
  }} else if (error instanceof APIError) {{
    console.log('API error:', error.message);
  }}
}}
```

## Building

```bash
npm run build
```

## Testing

```bash
npm test
```

## Documentation

For detailed API documentation, visit: [API Documentation]({self.config.api_base_url}/docs)
'''
    
    def _to_camel_case(self, name: str) -> str:
        """Convert string to camelCase."""
        components = name.replace('-', '_').split('_')
        return components[0].lower() + ''.join(word.capitalize() for word in components[1:])
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert string to PascalCase."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


class SDKGeneratorFactory:
    """Factory for creating SDK generators."""
    
    _generators = {
        SDKLanguage.PYTHON: PythonSDKGenerator,
        SDKLanguage.TYPESCRIPT: TypeScriptSDKGenerator,
        # Add more generators as needed
    }
    
    @classmethod
    def create_generator(
        self,
        language: str,
        config: SDKConfiguration
    ) -> BaseSDKGenerator:
        """Create SDK generator for specified language."""
        generator_class = self._generators.get(language)
        
        if not generator_class:
            raise ValueError(f"Unsupported SDK language: {language}")
        
        return generator_class(config)
    
    @classmethod
    def supported_languages(cls) -> List[str]:
        """Get list of supported languages."""
        return list(cls._generators.keys())


def generate_sdk_for_api(
    openapi_spec: Dict[str, Any],
    language: str,
    config: SDKConfiguration
) -> List[str]:
    """Generate SDK from OpenAPI specification."""
    generator = SDKGeneratorFactory.create_generator(language, config)
    
    # Parse OpenAPI spec and add endpoints
    paths = openapi_spec.get("paths", {})
    components = openapi_spec.get("components", {})
    
    # Add models from components
    schemas = components.get("schemas", {})
    for schema_name, schema_def in schemas.items():
        generator.add_model(schema_name, schema_def)
    
    # Add endpoints from paths
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                endpoint = APIEndpoint(
                    path=path,
                    method=method.lower(),
                    operation_id=operation.get("operationId", f"{method}_{path}"),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    parameters=operation.get("parameters", []),
                    request_body=operation.get("requestBody"),
                    responses=operation.get("responses", {}),
                    tags=operation.get("tags", []),
                    deprecated=operation.get("deprecated", False)
                )
                generator.add_endpoint(endpoint)
    
    # Generate and write files
    return generator.write_files()