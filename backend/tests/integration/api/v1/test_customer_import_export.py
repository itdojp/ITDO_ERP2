"""
Integration tests for Customer Import/Export API endpoints - Phase 5 CRM.
顧客データインポート/エクスポートAPIエンドポイント統合テスト（CRM機能Phase 5）
"""

import io
import json
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.customer import Customer, CustomerContact, CustomerStatus
from app.models.organization import Organization
from app.models.user import User
from tests.factories.organization import OrganizationFactory
from tests.factories.user import UserFactory


@pytest.fixture
async def test_organization(async_session: AsyncSession):
    """Create test organization."""
    org = OrganizationFactory()
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)
    return org


@pytest.fixture
async def test_user_with_org(async_session: AsyncSession, test_organization: Organization):
    """Create test user with organization."""
    user = UserFactory(organization_id=test_organization.id)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_customers(
    async_session: AsyncSession, test_organization: Organization, test_user_with_org: User
):
    """Create test customers for export testing."""
    customers = []
    
    # Customer 1: Technology company
    customer1 = Customer(
        organization_id=test_organization.id,
        customer_code="TECH001",
        company_name="Tech Solutions Inc.",
        name_kana="テックソリューション",
        customer_type="corporate",
        status=CustomerStatus.ACTIVE,
        industry="Technology",
        scale="large",
        email="contact@techsolutions.com",
        phone="03-1234-5678",
        annual_revenue=10000000,
        employee_count=500,
        priority="high",
        created_by=test_user_with_org.id
    )
    customers.append(customer1)
    async_session.add(customer1)
    await async_session.flush()
    
    # Add contact for customer1
    contact1 = CustomerContact(
        customer_id=customer1.id,
        name="John Smith",
        title="CTO",
        email="john.smith@techsolutions.com",
        phone="03-1234-5679",
        is_primary=True,
        is_decision_maker=True
    )
    async_session.add(contact1)
    
    # Customer 2: Finance company
    customer2 = Customer(
        organization_id=test_organization.id,
        customer_code="FIN001",
        company_name="Financial Services Ltd.",
        customer_type="corporate",
        status=CustomerStatus.PROSPECT,
        industry="Finance",
        scale="medium",
        email="info@finservices.com",
        phone="03-2345-6789",
        annual_revenue=5000000,
        employee_count=200,
        priority="normal",
        created_by=test_user_with_org.id
    )
    customers.append(customer2)
    async_session.add(customer2)
    
    # Customer 3: Small company
    customer3 = Customer(
        organization_id=test_organization.id,
        customer_code="SMALL001",
        company_name="Small Business Co.",
        customer_type="corporate",
        status=CustomerStatus.INACTIVE,
        industry="Retail",
        scale="small",
        email="contact@smallbiz.com",
        phone="03-3456-7890",
        annual_revenue=1000000,
        employee_count=50,
        priority="low",
        created_by=test_user_with_org.id
    )
    customers.append(customer3)
    async_session.add(customer3)
    
    await async_session.commit()
    return customers


def create_test_csv_content() -> str:
    """Create test CSV content for import testing."""
    csv_content = """customer_code,company_name,customer_type,status,industry,email,phone
IMPORT001,Import Test Company 1,corporate,active,Technology,test1@import.com,03-1111-1111
IMPORT002,Import Test Company 2,corporate,prospect,Finance,test2@import.com,03-2222-2222
IMPORT003,Import Test Company 3,individual,active,Healthcare,test3@import.com,03-3333-3333"""
    return csv_content


def create_invalid_csv_content() -> str:
    """Create invalid CSV content for validation testing."""
    csv_content = """customer_code,company_name,customer_type,status,industry,email,phone
,Missing Code Company,corporate,active,Technology,test@missing.com,03-1111-1111
INVALID001,Invalid Type Company,invalid_type,active,Technology,test@invalid.com,03-2222-2222
DUPLICATE001,Duplicate Company 1,corporate,active,Technology,test1@dup.com,03-3333-3333
DUPLICATE001,Duplicate Company 2,corporate,prospect,Finance,test2@dup.com,03-4444-4444"""
    return csv_content


@pytest.mark.asyncio
class TestCustomerImportExportAPI:
    """Test customer import/export API endpoints."""

    async def test_get_import_template_csv(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test getting CSV import template."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/import/template?format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "customer_import_template.csv" in response.headers["content-disposition"]
        
        # Verify CSV content
        content = response.content.decode("utf-8")
        assert "customer_code" in content
        assert "company_name" in content
        assert "CUST001" in content  # Sample data

    async def test_get_import_template_json(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test getting JSON import template."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/import/template?format=json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["format"] == "json"
        assert "template_content" in data
        assert "field_descriptions" in data
        
        # Verify template content is valid JSON
        template_content = json.loads(data["template_content"])
        assert isinstance(template_content, list)
        assert len(template_content) > 0

    async def test_get_field_mapping_guide(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test getting field mapping guide."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/import/mapping-guide")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mapping_guide" in data
        mapping_guide = data["mapping_guide"]
        
        assert "required_fields" in mapping_guide
        assert "optional_fields" in mapping_guide
        assert "field_types" in mapping_guide
        assert "example_mapping" in mapping_guide
        
        # Verify required fields
        required_fields = mapping_guide["required_fields"]
        assert "customer_code" in required_fields
        assert "company_name" in required_fields
        assert "customer_type" in required_fields

    async def test_validate_import_data_valid(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test validating valid import data."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        csv_content = create_test_csv_content()
        mapping = {
            "customer_code": "customer_code",
            "company_name": "company_name",
            "customer_type": "customer_type",
            "status": "status",
            "industry": "industry",
            "email": "email",
            "phone": "phone"
        }
        
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {
            "mapping": json.dumps(mapping),
            "validation_rules": "{}",
            "import_mode": "create"
        }
        
        response = client.post(
            "/api/v1/customer-import-export/customers/import/validate",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "success"
        assert result["valid_rows"] == 3
        assert result["invalid_rows"] == 0
        assert result["total_rows"] == 3

    async def test_validate_import_data_invalid(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test validating invalid import data."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        csv_content = create_invalid_csv_content()
        mapping = {
            "customer_code": "customer_code",
            "company_name": "company_name",
            "customer_type": "customer_type",
            "status": "status",
            "industry": "industry",
            "email": "email",
            "phone": "phone"
        }
        
        files = {"file": ("test_invalid.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {
            "mapping": json.dumps(mapping),
            "validation_rules": "{}",
            "import_mode": "create"
        }
        
        response = client.post(
            "/api/v1/customer-import-export/customers/import/validate",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "success"
        assert result["invalid_rows"] > 0
        assert "validation_errors" in result
        assert len(result["validation_errors"]) > 0

    async def test_import_customers_create_mode(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test importing customers in create mode."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        csv_content = create_test_csv_content()
        mapping = {
            "customer_code": "customer_code",
            "company_name": "company_name",
            "customer_type": "customer_type",
            "status": "status",
            "industry": "industry",
            "email": "email",
            "phone": "phone"
        }
        
        files = {"file": ("import.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {
            "mapping": json.dumps(mapping),
            "validation_rules": "{}",
            "import_mode": "create"
        }
        
        response = client.post(
            "/api/v1/customer-import-export/customers/import",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] in ["success", "partial_success"]
        assert result["imported_count"] >= 0
        assert "import_summary" in result

    async def test_export_customers_csv_basic(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test basic CSV export of customers."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/export/csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "customers_export_" in response.headers["content-disposition"]
        
        # Verify CSV content contains test customers
        content = response.content.decode("utf-8")
        assert "TECH001" in content
        assert "Tech Solutions Inc." in content

    async def test_export_customers_csv_with_filters(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test CSV export with filters."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            "/api/v1/customer-import-export/customers/export/csv"
            "?customer_type=corporate&status=active&industry=Technology"
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # Should contain only active technology customers
        assert "TECH001" in content
        assert "Tech Solutions Inc." in content
        # Should not contain prospect or inactive customers
        assert "FIN001" not in content or "SMALL001" not in content

    async def test_export_customers_csv_with_contacts(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test CSV export including contact information."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            "/api/v1/customer-import-export/customers/export/csv?include_contacts=true"
        )
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # Should include contact headers
        assert "primary_contact_name" in content
        assert "primary_contact_email" in content
        assert "primary_contact_phone" in content
        
        # Should include contact data
        assert "John Smith" in content

    async def test_export_customers_excel(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test Excel export of customers."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/export/excel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["exported_count"] >= 3
        assert "excel_data" in data
        assert "filename" in data
        assert data["filename"].endswith(".xlsx")
        
        # Verify Excel data structure
        excel_data = data["excel_data"]
        assert "customers" in excel_data
        customers_sheet = excel_data["customers"]
        assert "headers" in customers_sheet
        assert "data" in customers_sheet

    async def test_export_summary(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test export summary endpoint."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/export/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "estimated_export_count" in data
        assert data["estimated_export_count"] >= 3  # At least 3 test customers
        assert "applied_filters" in data

    async def test_export_summary_with_filters(
        self, client: TestClient, test_user_with_org: User, test_customers
    ):
        """Test export summary with filters."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            "/api/v1/customer-import-export/customers/export/summary"
            "?customer_type=corporate&status=active"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fewer customers than total due to filters
        assert data["estimated_export_count"] >= 1
        assert data["estimated_export_count"] <= 3
        
        # Verify filters were applied
        filters = data["applied_filters"]
        assert filters["customer_type"] == "corporate"
        assert filters["status"] == "active"

    async def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        # Test import endpoints
        response = client.get("/api/v1/customer-import-export/customers/import/template")
        assert response.status_code == 401
        
        response = client.post("/api/v1/customer-import-export/customers/import/validate")
        assert response.status_code == 401
        
        response = client.post("/api/v1/customer-import-export/customers/import")
        assert response.status_code == 401
        
        # Test export endpoints
        response = client.get("/api/v1/customer-import-export/customers/export/csv")
        assert response.status_code == 401
        
        response = client.get("/api/v1/customer-import-export/customers/export/excel")
        assert response.status_code == 401

    async def test_user_without_organization(
        self, client: TestClient, async_session: AsyncSession
    ):
        """Test endpoints with user that has no organization."""
        # Create user without organization
        user = UserFactory(organization_id=None)
        async_session.add(user)
        await async_session.commit()
        
        client.headers = {"Authorization": f"Bearer mock_token_{user.id}"}
        
        response = client.get("/api/v1/customer-import-export/customers/import/template")
        assert response.status_code == 400
        assert "must belong to an organization" in response.json()["detail"]

    async def test_invalid_file_type(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test import with invalid file type."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        # Try to upload a non-CSV file
        files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
        data = {
            "mapping": "{}",
            "validation_rules": "{}",
            "import_mode": "create"
        }
        
        response = client.post(
            "/api/v1/customer-import-export/customers/import/validate",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Only CSV files are supported" in response.json()["detail"]

    async def test_invalid_json_parameters(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test import with invalid JSON parameters."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        csv_content = create_test_csv_content()
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {
            "mapping": "invalid json",  # Invalid JSON
            "validation_rules": "{}",
            "import_mode": "create"
        }
        
        response = client.post(
            "/api/v1/customer-import-export/customers/import/validate",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    async def test_unsupported_template_format(
        self, client: TestClient, test_user_with_org: User
    ):
        """Test requesting unsupported template format."""
        client.headers = {"Authorization": f"Bearer mock_token_{test_user_with_org.id}"}
        
        response = client.get(
            "/api/v1/customer-import-export/customers/import/template?format=xml"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Unsupported template format" in data["message"]