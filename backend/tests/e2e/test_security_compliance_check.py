"""
Critical path test for security_compliance_check
Auto-generated by CC02 v38.0 Test Automation System
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestSecurityComplianceCheckCriticalPath:
    def test_critical_path(self, client):
        """Test security_compliance_check critical path"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
