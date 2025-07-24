#!/usr/bin/env python3
"""
CC02 v33.0 API テスト生成ツール  
Automated API Test Generator for Quality Improvement
"""

import os
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json
import re


class APITestGenerator:
    """FastAPI エンドポイントから自動的にテストケースを生成するツール"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.api_path = self.backend_path / "app" / "api"
        self.models_path = self.backend_path / "app" / "models"
        self.schemas_path = self.backend_path / "app" / "schemas"
        self.tests_path = self.backend_path / "tests"
        
    def discover_api_endpoints(self) -> Dict[str, List[Dict[str, Any]]]:
        """API エンドポイントを発見・解析"""
        print("🔍 API エンドポイント発見中...")
        
        endpoints = {}
        
        # Scan API files
        api_files = list(self.api_path.glob("**/*.py"))
        
        for api_file in api_files:
            if api_file.name.startswith("__"):
                continue
                
            try:
                endpoints[api_file.stem] = self._analyze_api_file(api_file)
            except Exception as e:
                print(f"⚠️  Warning: Could not analyze {api_file}: {e}")
                
        return endpoints
    
    def _analyze_api_file(self, api_file: Path) -> List[Dict[str, Any]]:
        """個別のAPIファイルを解析してエンドポイント情報を抽出"""
        endpoints = []
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {api_file}: {e}")
            return endpoints
        
        # Find FastAPI route decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                endpoint_info = self._extract_endpoint_info(node, content)
                if endpoint_info:
                    endpoints.append(endpoint_info)
        
        return endpoints
    
    def _extract_endpoint_info(self, func_node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """関数ノードからエンドポイント情報を抽出"""
        endpoint_info = {
            "function_name": func_node.name,
            "methods": [],
            "path": None,
            "parameters": [],
            "return_type": None,
            "docstring": ast.get_docstring(func_node),
            "line_number": func_node.lineno
        }
        
        # Check decorators for FastAPI routes
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr'):
                    method = decorator.func.attr.upper()
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoint_info["methods"].append(method)
                        
                        # Extract path from decorator arguments
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            endpoint_info["path"] = decorator.args[0].value
        
        # Extract function parameters
        for arg in func_node.args.args:
            if arg.arg not in ['self', 'db', 'current_user']:  # Skip common parameters
                param_info = {
                    "name": arg.arg,
                    "type": self._get_type_annotation(arg),
                    "required": True
                }
                endpoint_info["parameters"].append(param_info)
        
        # Extract return type annotation
        if func_node.returns:
            endpoint_info["return_type"] = self._get_type_annotation_from_node(func_node.returns)
        
        # Only return if this looks like an API endpoint
        if endpoint_info["methods"] and endpoint_info["path"]:
            return endpoint_info
        
        return None
    
    def _get_type_annotation(self, arg: ast.arg) -> str:
        """引数の型アノテーションを取得"""
        if arg.annotation:
            return self._get_type_annotation_from_node(arg.annotation)
        return "Any"
    
    def _get_type_annotation_from_node(self, node: ast.AST) -> str:
        """ASTノードから型アノテーション文字列を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_type_annotation_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            base = self._get_type_annotation_from_node(node.value)
            slice_val = self._get_type_annotation_from_node(node.slice)
            return f"{base}[{slice_val}]"
        else:
            return "Any"
    
    def generate_test_cases(self, endpoints: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """エンドポイント情報からテストケースを生成"""
        print("🧪 テストケース生成中...")
        
        test_files = {}
        
        for module_name, endpoint_list in endpoints.items():
            if not endpoint_list:
                continue
                
            test_content = self._generate_test_file_content(module_name, endpoint_list)
            test_files[f"test_{module_name}_generated.py"] = test_content
        
        return test_files
    
    def _generate_test_file_content(self, module_name: str, endpoints: List[Dict[str, Any]]) -> str:
        """個別のテストファイル内容を生成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        test_content = f'''"""
Generated API Tests for {module_name}
Auto-generated by CC02 v33.0 API Test Generator
Created: {timestamp}
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
import json
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4


# Test client setup
client = TestClient(app)


# Mock dependencies
def override_get_db():
    \"\"\"Override database dependency for testing\"\"\"
    try:
        # Use test database session here
        yield None
    finally:
        pass


def override_get_current_user():
    \"\"\"Override auth dependency for testing\"\"\"
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_active=True
    )


# Apply overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


class Test{module_name.title().replace('_', '')}API:
    \"\"\"Generated test class for {module_name} API endpoints\"\"\"
    
    def setup_method(self):
        \"\"\"Setup method run before each test\"\"\"
        self.base_url = "http://testserver"
        self.headers = {{"Content-Type": "application/json"}}
        
    def teardown_method(self):
        \"\"\"Cleanup method run after each test\"\"\"
        pass

'''
        
        # Generate test methods for each endpoint
        for endpoint in endpoints:
            test_content += self._generate_endpoint_test_methods(endpoint)
        
        # Add utility methods
        test_content += '''
    # Utility methods
    def _create_test_data(self, **kwargs):
        """Create test data with default values"""
        defaults = {
            "name": "Test Item",
            "description": "Test Description", 
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        defaults.update(kwargs)
        return defaults
    
    def _assert_response_structure(self, response_data, expected_fields):
        """Assert response has expected structure"""
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"
    
    def _assert_error_response(self, response, expected_status=400):
        """Assert error response format"""
        assert response.status_code == expected_status
        assert "detail" in response.json()


# Performance and Load Tests
class Test{module_name.title().replace('_', '')}Performance:
    """Performance tests for {module_name} API"""
    
    def test_endpoint_response_time(self):
        """Test endpoint response time is within acceptable limits"""
        import time
        
        start_time = time.time()
        response = client.get("/")  # Adjust endpoint
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0, f"Response time too slow: {{response_time:.2f}}s"
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get("/")  # Adjust endpoint
            results.put(response.status_code)
        
        # Create and start threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code < 500, f"Server error in concurrent test: {{status_code}}"


# Security Tests  
class Test{module_name.title().replace('_', '')}Security:
    """Security tests for {module_name} API"""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        malicious_input = "'; DROP TABLE users; --"
        
        # Test in various parameters
        response = client.get(f"/api/v1/items?search={{malicious_input}}")
        assert response.status_code != 500, "SQL injection vulnerability detected"
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        xss_payload = "<script>alert('xss')</script>"
        
        test_data = {{"name": xss_payload, "description": "test"}}
        response = client.post("/api/v1/items", json=test_data)
        
        if response.status_code == 200:
            # Check response doesn't contain unescaped script
            assert "<script>" not in response.text
    
    def test_unauthorized_access(self):
        """Test endpoints require proper authentication"""
        # Remove auth override temporarily
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        response = client.get("/api/v1/protected-endpoint")
        assert response.status_code in [401, 403], "Endpoint should require authentication"
        
        # Restore auth override
        app.dependency_overrides[get_current_user] = override_get_current_user
'''
        
        return test_content
    
    def _generate_endpoint_test_methods(self, endpoint: Dict[str, Any]) -> str:
        """個別エンドポイントのテストメソッドを生成"""
        function_name = endpoint["function_name"]
        methods = endpoint["methods"]
        path = endpoint["path"] or "/api/v1/test"
        
        test_methods = f'''
    # Tests for {function_name} ({", ".join(methods)})
    
'''
        
        for method in methods:
            method_lower = method.lower()
            
            if method == "GET":
                test_methods += f'''    def test_{function_name}_{method_lower}_success(self):
        """Test successful {method} request"""
        response = client.{method_lower}("{path}")
        assert response.status_code == 200
        
        # Validate response structure
        data = response.json()
        assert isinstance(data, (dict, list))
    
    def test_{function_name}_{method_lower}_not_found(self):
        """Test {method} request with non-existent resource"""
        response = client.{method_lower}("{path.replace('{', '999')}") 
        assert response.status_code == 404
        
'''
            
            elif method == "POST":
                test_methods += f'''    def test_{function_name}_{method_lower}_success(self):
        """Test successful {method} request"""
        test_data = self._create_test_data()
        
        response = client.{method_lower}("{path}", json=test_data)
        assert response.status_code in [200, 201]
        
        # Validate response structure
        data = response.json()
        assert isinstance(data, dict)
        
    def test_{function_name}_{method_lower}_validation_error(self):
        """Test {method} request with invalid data"""
        invalid_data = {{"invalid_field": "invalid_value"}}
        
        response = client.{method_lower}("{path}", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_{function_name}_{method_lower}_empty_data(self):
        """Test {method} request with empty data"""
        response = client.{method_lower}("{path}", json={{}})
        assert response.status_code in [400, 422]
        
'''
            
            elif method in ["PUT", "PATCH"]:
                test_methods += f'''    def test_{function_name}_{method_lower}_success(self):
        """Test successful {method} request"""
        test_data = self._create_test_data()
        
        response = client.{method_lower}("{path}", json=test_data)
        assert response.status_code == 200
        
        # Validate response structure
        data = response.json()
        assert isinstance(data, dict)
        
    def test_{function_name}_{method_lower}_not_found(self):
        """Test {method} request with non-existent resource"""
        test_data = self._create_test_data()
        
        response = client.{method_lower}("{path.replace('{', '999')}", json=test_data)
        assert response.status_code == 404
        
'''
            
            elif method == "DELETE":
                test_methods += f'''    def test_{function_name}_{method_lower}_success(self):
        """Test successful {method} request"""
        response = client.{method_lower}("{path}")
        assert response.status_code in [200, 204]
        
    def test_{function_name}_{method_lower}_not_found(self):
        """Test {method} request with non-existent resource"""
        response = client.{method_lower}("{path.replace('{', '999')}")
        assert response.status_code == 404
        
'''
        
        return test_methods
    
    def save_test_files(self, test_files: Dict[str, str], output_dir: Path):
        """生成されたテストファイルを保存"""
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for filename, content in test_files.items():
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files.append(file_path)
            print(f"📝 Generated test file: {file_path}")
        
        return saved_files
    
    def run_generation_process(self) -> Dict[str, Any]:
        """完全なテスト生成プロセスを実行"""
        print("🚀 CC02 v33.0 API Test Generator Starting")
        print("=" * 50)
        
        # Discover endpoints
        endpoints = self.discover_api_endpoints()
        
        total_endpoints = sum(len(ep_list) for ep_list in endpoints.values())
        print(f"📊 Discovered {total_endpoints} endpoints across {len(endpoints)} modules")
        
        # Generate test cases
        test_files = self.generate_test_cases(endpoints)
        
        # Save test files
        output_dir = self.tests_path / "generated"
        saved_files = self.save_test_files(test_files, output_dir)
        
        # Generate summary
        return {
            "discovered_endpoints": endpoints,
            "generated_files": [str(f) for f in saved_files],
            "total_endpoints": total_endpoints,
            "total_test_files": len(test_files),
            "generation_timestamp": datetime.now().isoformat(),
            "recommendations": [
                "Review generated tests for accuracy",
                "Customize test data for specific business logic",
                "Add integration with existing test fixtures",
                "Implement proper database setup/teardown",
                "Add edge case tests for critical endpoints"
            ]
        }


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🧪 CC02 v33.0 API Test Generator")
    print("=" * 50)
    print(f"Project root: {project_root}")
    
    generator = APITestGenerator(project_root)
    results = generator.run_generation_process()
    
    # Save generation report
    report_file = project_root / f"api_test_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Generation report saved: {report_file}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎯 生成完了サマリー:")
    print(f"Total endpoints analyzed: {results['total_endpoints']}")
    print(f"Test files generated: {results['total_test_files']}")
    print(f"Output directory: {Path.cwd() / 'backend' / 'tests' / 'generated'}")
    
    print("\n📋 推奨アクション:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
    
    return results


if __name__ == "__main__":
    main()