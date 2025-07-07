"""Security tests for task management."""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestTaskSecurity:
    """Security test cases for task management."""

    def test_sql_injection(self, client: TestClient, auth_headers: Dict[str, str]) -> None:
        """Test ST-001: SQLインジェクション"""
        # Try SQL injection in search parameter
        malicious_input = "'; DROP TABLE tasks; --"
        response = client.get(
            f"/api/v1/tasks?search={malicious_input}",
            headers=auth_headers
        )
        
        # Should handle the input safely
        assert response.status_code in [200, 400]
        
        # Verify tables still exist
        response = client.get("/api/v1/tasks", headers=auth_headers)
        assert response.status_code == 200

    def test_xss_attack(self, client: TestClient, auth_headers: Dict[str, str]) -> None:
        """Test ST-002: XSS攻撃"""
        # Try XSS in task title
        xss_payload = "<script>alert('XSS')</script>"
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": xss_payload,
                "project_id": 1
            },
            headers=auth_headers
        )
        
        if response.status_code == 201:
            task = response.json()
            # HTML should be escaped
            assert "<script>" not in task["title"]
            assert task["title"] == xss_payload  # Stored as-is but escaped on render

    def test_privilege_escalation(self, client: TestClient, regular_user_headers: Dict[str, str]) -> None:
        """Test ST-003: 権限昇格試行"""
        # Try to access admin-only endpoint as regular user
        response = client.post(
            "/api/v1/tasks/1/force-complete",  # Admin-only action
            headers=regular_user_headers
        )
        
        assert response.status_code == 403

    def test_cross_org_data_access(self, client: TestClient, auth_headers: Dict[str, str]) -> None:
        """Test ST-004: 他組織データアクセス"""
        # Try to access task from different organization
        response = client.get(
            "/api/v1/tasks/9999",  # Task from different org
            headers=auth_headers
        )
        
        assert response.status_code == 404  # Should appear as not found

    def test_file_upload_virus(self, client: TestClient, auth_headers: Dict[str, str]) -> None:
        """Test ST-005: ファイルアップロード（ウイルス）"""
        # Simulate virus-infected file upload
        # EICAR test signature
        eicar_test = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        
        files = {"file": ("virus.exe", eicar_test, "application/octet-stream")}
        response = client.post(
            "/api/v1/tasks/1/attachments",
            files=files,
            headers=auth_headers
        )
        
        # Should reject virus file
        assert response.status_code in [400, 415, 422]

    def test_file_upload_large(self, client: TestClient, auth_headers: dict):
        """Test ST-006: ファイルアップロード（大容量）"""
        # Create file larger than 10MB limit
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {"file": ("large.bin", large_content, "application/octet-stream")}
        response = client.post(
            "/api/v1/tasks/1/attachments",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 413  # Payload Too Large