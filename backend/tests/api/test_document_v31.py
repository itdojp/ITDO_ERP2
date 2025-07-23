"""
Test Suite for Document Management API v31.0

Comprehensive test coverage for all 10 document management endpoints:
1. Document Storage & Management
2. Folder & Category Organization
3. Document Sharing & Permissions
4. Workflow & Approval Processes
5. Document Templates & Generation
6. Advanced Search & Discovery
7. Collaboration & Comments
8. Document Analytics & Insights
9. Digital Signatures & E-signing
10. Bulk Operations & Management
"""

import base64
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document_extended import (
    AccessLevel,
    ApprovalStatus,
    DocumentApproval,
    DocumentComment,
    DocumentExtended,
    DocumentFolder,
    DocumentShare,
    DocumentSignature,
    DocumentStatus,
    DocumentTemplate,
    DocumentWorkflow,
    ShareType,
    SignatureStatus,
)

client = TestClient(app)


# Test data fixtures
@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "organization_id": "org-123",
        "title": "Test Document",
        "description": "Test document description",
        "document_type": "pdf",
        "category": "contracts",
        "subcategory": "vendor_contracts",
        "filename": "test_document.pdf",
        "owner_id": "user-123",
        "created_by_id": "user-123",
        "folder_id": "folder-456",
        "tags": ["important", "contract"],
        "metadata": {"client": "Test Client"},
        "is_confidential": True,
        "requires_approval": True,
    }


@pytest.fixture
def sample_folder_data():
    """Sample folder data for testing."""
    return {
        "organization_id": "org-123",
        "name": "Test Folder",
        "description": "Test folder description",
        "parent_folder_id": None,
        "owner_id": "user-123",
        "created_by_id": "user-123",
        "default_access_level": "view",
        "storage_quota_bytes": 1073741824,  # 1GB
        "allowed_file_types": ["pdf", "docx", "xlsx"],
        "tags": ["documents", "contracts"],
    }


@pytest.fixture
def sample_share_data():
    """Sample share data for testing."""
    return {
        "organization_id": "org-123",
        "share_type": "user",
        "shared_with_user_id": "user-456",
        "access_level": "view",
        "can_download": True,
        "can_print": False,
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "max_views": 10,
        "share_message": "Please review this document",
    }


@pytest.fixture
def sample_comment_data():
    """Sample comment data for testing."""
    return {
        "organization_id": "org-123",
        "content": "This needs to be reviewed",
        "comment_type": "review",
        "page_number": 1,
        "position_x": "100.5",
        "position_y": "200.75",
        "mentioned_users": ["user-789"],
        "requires_response": True,
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "organization_id": "org-123",
        "name": "Contract Approval Workflow",
        "description": "Standard contract approval process",
        "workflow_type": "approval",
        "created_by_id": "user-123",
        "steps": [
            {"step": 1, "name": "Legal Review", "required": True},
            {"step": 2, "name": "Financial Review", "required": True},
            {"step": 3, "name": "Executive Approval", "required": False},
        ],
        "default_deadline_days": 5,
        "send_notifications": True,
    }


@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "organization_id": "org-123",
        "name": "Contract Template",
        "description": "Standard contract template",
        "document_type": "pdf",
        "category": "contracts",
        "template_format": "html",
        "template_content": "<h1>{{contract_title}}</h1><p>Party: {{party_name}}</p>",
        "placeholder_fields": [
            {"name": "contract_title", "type": "text", "required": True},
            {"name": "party_name", "type": "text", "required": True},
        ],
        "required_fields": ["contract_title", "party_name"],
        "owner_id": "user-123",
        "created_by_id": "user-123",
    }


class TestDocumentManagement:
    """Test suite for Document Storage & Management endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_document")
    def test_create_document_success(self, mock_create, sample_document_data):
        """Test successful document creation."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-123"
        mock_document.document_number = "DOC-12345678"
        mock_document.title = sample_document_data["title"]
        mock_document.status = DocumentStatus.DRAFT
        mock_document.created_at = datetime.utcnow()

        mock_create.return_value = mock_document

        response = client.post("/api/v1/documents", json=sample_document_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_document_data["title"]
        assert "document_number" in data
        mock_create.assert_called_once()

    def test_create_document_validation_error(self):
        """Test document creation with validation errors."""
        invalid_data = {
            "organization_id": "org-123",
            # Missing required fields
            "document_type": "invalid_type",
        }

        response = client.post("/api/v1/documents", json=invalid_data)
        assert response.status_code == 422

    @patch("app.crud.document_v31.DocumentService.get_documents")
    def test_list_documents_with_filters(self, mock_get_documents):
        """Test document listing with comprehensive filters."""
        mock_documents = [
            DocumentExtended(id="doc-1", title="Document 1"),
            DocumentExtended(id="doc-2", title="Document 2"),
        ]
        mock_get_documents.return_value = mock_documents

        response = client.get(
            "/api/v1/documents",
            params={
                "organization_id": "org-123",
                "document_type": "pdf",
                "category": "contracts",
                "search_text": "test",
                "tags": "important,contract",
                "limit": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        mock_get_documents.assert_called_once()

    @patch("app.crud.document_v31.DocumentService.get_document_by_id")
    def test_get_document_by_id_success(self, mock_get_document):
        """Test successful document retrieval by ID."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-123"
        mock_document.title = "Test Document"
        mock_document.view_count = 5
        mock_get_document.return_value = mock_document

        response = client.get("/api/v1/documents/doc-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "doc-123"
        mock_get_document.assert_called_once()

    @patch("app.crud.document_v31.DocumentService.update_document")
    def test_update_document_success(self, mock_update):
        """Test successful document update."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-123"
        mock_document.title = "Updated Document"
        mock_update.return_value = mock_document

        update_data = {
            "title": "Updated Document",
            "description": "Updated description",
            "tags": ["updated", "contract"],
        }

        response = client.put(
            "/api/v1/documents/doc-123?user_id=user-123", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Document"
        mock_update.assert_called_once()

    @patch("app.crud.document_v31.DocumentService.create_document_version")
    def test_create_document_version(self, mock_create_version):
        """Test document version creation."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-456"
        mock_document.version = "2.0"
        mock_document.parent_document_id = "doc-123"
        mock_create_version.return_value = mock_document

        version_data = {
            "filename": "test_v2.pdf",
            "description": "Version 2 with updates",
            "major_update": True,
        }

        response = client.post(
            "/api/v1/documents/doc-123/versions?user_id=user-123", json=version_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0"
        assert data["parent_document_id"] == "doc-123"

    @patch("app.crud.document_v31.DocumentService.move_document")
    def test_move_document(self, mock_move):
        """Test document move operation."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-123"
        mock_document.folder_id = "folder-789"
        mock_move.return_value = mock_document

        move_data = {"new_folder_id": "folder-789"}

        response = client.post(
            "/api/v1/documents/doc-123/move?user_id=user-123", json=move_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["folder_id"] == "folder-789"

    @patch("app.crud.document_v31.DocumentService.delete_document")
    def test_delete_document(self, mock_delete):
        """Test document deletion."""
        mock_delete.return_value = True

        response = client.delete("/api/v1/documents/doc-123?user_id=user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document deleted successfully"


class TestFolderManagement:
    """Test suite for Folder & Category Organization endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_folder")
    def test_create_folder_success(self, mock_create, sample_folder_data):
        """Test successful folder creation."""
        mock_folder = DocumentFolder()
        mock_folder.id = "folder-123"
        mock_folder.name = sample_folder_data["name"]
        mock_folder.full_path = sample_folder_data["name"]
        mock_folder.level = 0

        mock_create.return_value = mock_folder

        response = client.post("/api/v1/folders", json=sample_folder_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_folder_data["name"]
        assert data["level"] == 0

    @patch("app.crud.document_v31.DocumentService.get_folder_contents")
    def test_get_folder_contents(self, mock_get_contents):
        """Test folder contents retrieval."""
        mock_contents = {
            "subfolders": [
                DocumentFolder(id="sub-1", name="Subfolder 1"),
                DocumentFolder(id="sub-2", name="Subfolder 2"),
            ],
            "documents": [
                DocumentExtended(id="doc-1", title="Document 1"),
                DocumentExtended(id="doc-2", title="Document 2"),
            ],
        }
        mock_get_contents.return_value = mock_contents

        response = client.get("/api/v1/folders/folder-123/contents")

        assert response.status_code == 200
        data = response.json()
        assert len(data["subfolders"]) == 2
        assert len(data["documents"]) == 2


class TestDocumentSharing:
    """Test suite for Document Sharing & Permissions endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_document_share")
    def test_create_document_share(self, mock_create_share, sample_share_data):
        """Test document share creation."""
        mock_share = DocumentShare()
        mock_share.id = "share-123"
        mock_share.document_id = "doc-123"
        mock_share.share_type = ShareType.USER
        mock_share.access_level = AccessLevel.VIEW
        mock_share.is_active = True

        mock_create_share.return_value = mock_share

        response = client.post(
            "/api/v1/documents/doc-123/shares?shared_by_id=user-123",
            json=sample_share_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "doc-123"
        assert data["access_level"] == "view"

    @patch("app.crud.document_v31.DocumentService.get_document_shares")
    def test_get_document_shares(self, mock_get_shares):
        """Test document shares retrieval."""
        mock_shares = [
            DocumentShare(id="share-1", access_level=AccessLevel.VIEW),
            DocumentShare(id="share-2", access_level=AccessLevel.EDIT),
        ]
        mock_get_shares.return_value = mock_shares

        response = client.get("/api/v1/documents/doc-123/shares")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("app.crud.document_v31.DocumentService.revoke_document_share")
    def test_revoke_document_share(self, mock_revoke):
        """Test document share revocation."""
        mock_revoke.return_value = True

        response = client.delete("/api/v1/shares/share-123?revoked_by_id=user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document share revoked successfully"


class TestWorkflowManagement:
    """Test suite for Workflow & Approval Processes endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_approval_workflow")
    def test_create_workflow(self, mock_create_workflow, sample_workflow_data):
        """Test workflow creation."""
        mock_workflow = DocumentWorkflow()
        mock_workflow.id = "workflow-123"
        mock_workflow.name = sample_workflow_data["name"]
        mock_workflow.is_active = True

        mock_create_workflow.return_value = mock_workflow

        response = client.post("/api/v1/workflows", json=sample_workflow_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_workflow_data["name"]

    @patch("app.crud.document_v31.DocumentService.submit_document_for_approval")
    def test_submit_for_approval(self, mock_submit):
        """Test document approval submission."""
        mock_approvals = [
            DocumentApproval(id="approval-1", step_number=1),
            DocumentApproval(id="approval-2", step_number=2),
        ]
        mock_submit.return_value = mock_approvals

        approval_data = {
            "workflow_id": "workflow-123",
            "approvers": [
                {"approver_id": "user-456", "step_name": "Legal Review"},
                {"approver_id": "user-789", "step_name": "Financial Review"},
            ],
        }

        response = client.post(
            "/api/v1/documents/doc-123/submit-approval?requested_by_id=user-123",
            json=approval_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("app.crud.document_v31.DocumentService.process_approval_decision")
    def test_process_approval_decision(self, mock_process):
        """Test approval decision processing."""
        mock_approval = DocumentApproval()
        mock_approval.id = "approval-123"
        mock_approval.status = ApprovalStatus.APPROVED
        mock_approval.decision_date = datetime.utcnow()

        mock_process.return_value = mock_approval

        decision_data = {
            "decision": "approved",
            "comments": "Looks good to proceed",
            "conditions": "Ensure final review by legal",
        }

        response = client.post(
            "/api/v1/approvals/approval-123/decision", json=decision_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"


class TestTemplateManagement:
    """Test suite for Document Templates & Generation endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_document_template")
    def test_create_template(self, mock_create_template, sample_template_data):
        """Test template creation."""
        mock_template = DocumentTemplate()
        mock_template.id = "template-123"
        mock_template.name = sample_template_data["name"]
        mock_template.is_active = True

        mock_create_template.return_value = mock_template

        response = client.post("/api/v1/templates", json=sample_template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_template_data["name"]

    @patch("app.crud.document_v31.DocumentService.generate_document_from_template")
    def test_generate_from_template(self, mock_generate):
        """Test document generation from template."""
        mock_document = DocumentExtended()
        mock_document.id = "doc-456"
        mock_document.filename = "generated_contract.pdf"

        mock_generate.return_value = mock_document

        generation_data = {
            "template_id": "template-123",
            "field_values": {
                "contract_title": "Service Agreement",
                "party_name": "ABC Corporation",
            },
        }

        response = client.post(
            "/api/v1/templates/template-123/generate?generated_by_id=user-123",
            json=generation_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-456"
        assert data["generation_success"] is True


class TestDocumentSearch:
    """Test suite for Advanced Search & Discovery endpoints."""

    @patch("app.crud.document_v31.DocumentService.search_documents")
    def test_search_documents(self, mock_search):
        """Test advanced document search."""
        mock_documents = [
            DocumentExtended(id="doc-1", title="Contract ABC"),
            DocumentExtended(id="doc-2", title="Agreement XYZ"),
        ]
        mock_search.return_value = mock_documents

        search_data = {
            "query": "contract agreement",
            "document_type": "pdf",
            "category": "contracts",
            "tags": ["important"],
        }

        response = client.post(
            "/api/v1/documents/search?organization_id=org-123", json=search_data
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total_count"] == 2
        assert "search_time_ms" in data

    def test_get_search_suggestions(self):
        """Test search suggestions endpoint."""
        response = client.get(
            "/api/v1/documents/search/suggestions",
            params={"query": "contract", "organization_id": "org-123", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
        assert all("contract" in suggestion for suggestion in data)


class TestCollaboration:
    """Test suite for Collaboration & Comments endpoints."""

    @patch("app.crud.document_v31.DocumentService.create_document_comment")
    def test_create_comment(self, mock_create_comment, sample_comment_data):
        """Test comment creation."""
        mock_comment = DocumentComment()
        mock_comment.id = "comment-123"
        mock_comment.content = sample_comment_data["content"]
        mock_comment.author_id = "user-123"
        mock_comment.is_resolved = False

        mock_create_comment.return_value = mock_comment

        response = client.post(
            "/api/v1/documents/doc-123/comments?author_id=user-123",
            json=sample_comment_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == sample_comment_data["content"]

    @patch("app.crud.document_v31.DocumentService.resolve_comment")
    def test_resolve_comment(self, mock_resolve):
        """Test comment resolution."""
        mock_comment = DocumentComment()
        mock_comment.id = "comment-123"
        mock_comment.is_resolved = True
        mock_comment.resolved_at = datetime.utcnow()

        mock_resolve.return_value = mock_comment

        response = client.post(
            "/api/v1/comments/comment-123/resolve?resolved_by_id=user-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True


class TestDocumentAnalytics:
    """Test suite for Document Analytics & Insights endpoints."""

    @patch("app.crud.document_v31.DocumentService.get_document_analytics")
    def test_get_analytics(self, mock_get_analytics):
        """Test document analytics generation."""
        from app.models.document_extended import DocumentAnalytics

        mock_analytics = DocumentAnalytics()
        mock_analytics.organization_id = "org-123"
        mock_analytics.total_documents = 150
        mock_analytics.total_storage_bytes = 1073741824
        mock_analytics.total_views = 500
        mock_analytics.total_downloads = 100
        mock_analytics.calculated_date = datetime.utcnow()

        mock_get_analytics.return_value = mock_analytics

        analytics_data = {
            "organization_id": "org-123",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "period_type": "monthly",
        }

        response = client.post("/api/v1/analytics", json=analytics_data)

        assert response.status_code == 200
        data = response.json()
        assert data["storage_metrics"]["total_documents"] == 150
        assert data["usage_metrics"]["total_views"] == 500


class TestDigitalSignatures:
    """Test suite for Digital Signatures & E-signing endpoints."""

    @patch("app.crud.document_v31.DocumentService.request_document_signature")
    def test_request_signature(self, mock_request_signature):
        """Test signature request creation."""
        mock_signatures = [
            DocumentSignature(id="sig-1", signer_email="signer1@test.com"),
            DocumentSignature(id="sig-2", signer_email="signer2@test.com"),
        ]
        mock_request_signature.return_value = mock_signatures

        signature_data = {
            "organization_id": "org-123",
            "signer_name": "John Doe",
            "signer_email": "john.doe@test.com",
            "page_number": 1,
            "position_x": "100.0",
            "position_y": "200.0",
        }

        response = client.post(
            "/api/v1/documents/doc-123/signatures/request?requested_by_id=user-123",
            json=signature_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @patch("app.crud.document_v31.DocumentService.process_document_signature")
    def test_process_signature(self, mock_process_signature):
        """Test signature processing."""
        mock_signature = DocumentSignature()
        mock_signature.id = "sig-123"
        mock_signature.status = SignatureStatus.SIGNED
        mock_signature.signed_at = datetime.utcnow()

        mock_process_signature.return_value = mock_signature

        # Create a simple signature image (1x1 pixel PNG)
        signature_bytes = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        ).decode()

        signature_data = {
            "signature_data": signature_bytes,
            "consent_given": True,
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test Browser",
        }

        response = client.post("/api/v1/signatures/sig-123/sign", json=signature_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "signed"


class TestBulkOperations:
    """Test suite for Bulk Operations & Management endpoints."""

    def test_bulk_document_operation(self):
        """Test bulk document operations."""
        operation_data = {
            "document_ids": ["doc-1", "doc-2", "doc-3"],
            "operation": "move",
            "parameters": {"target_folder_id": "folder-456"},
        }

        with patch("app.crud.document_v31.DocumentService.move_document") as mock_move:
            mock_move.return_value = DocumentExtended(id="doc-1")

            response = client.post(
                "/api/v1/documents/bulk-operation?user_id=user-123", json=operation_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["operation"] == "move"
            assert data["total_requested"] == 3

    def test_bulk_tag_operation(self):
        """Test bulk tag operations."""
        tag_data = {
            "document_ids": ["doc-1", "doc-2"],
            "tags_to_add": ["urgent", "reviewed"],
            "tags_to_remove": ["draft"],
        }

        response = client.post(
            "/api/v1/documents/bulk-tag?user_id=user-123", json=tag_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "bulk_tag"
        assert data["success_rate"] == 100.0

    def test_bulk_share_operation(self):
        """Test bulk share operations."""
        share_data = {
            "document_ids": ["doc-1", "doc-2"],
            "share_settings": {
                "share_type": "user",
                "shared_with_user_id": "user-456",
                "access_level": "view",
            },
        }

        response = client.post(
            "/api/v1/documents/bulk-share?shared_by_id=user-123", json=share_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "bulk_share"

    def test_export_documents(self):
        """Test document export functionality."""
        export_data = {
            "document_ids": ["doc-1", "doc-2"],
            "export_format": "zip",
            "include_metadata": True,
            "include_versions": False,
        }

        response = client.post("/api/v1/export?user_id=user-123", json=export_data)

        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "processing"

    def test_import_documents(self):
        """Test document import functionality."""
        import_data = {
            "source_type": "file_upload",
            "source_location": "/tmp/documents.zip",
            "target_folder_id": "folder-123",
            "preserve_structure": True,
        }

        response = client.post("/api/v1/import?user_id=user-123", json=import_data)

        assert response.status_code == 200
        data = response.json()
        assert "import_id" in data
        assert data["status"] == "processing"


class TestSystemHealth:
    """Test suite for system health and status endpoints."""

    @patch("app.crud.document_v31.DocumentService.get_system_health")
    def test_system_health_success(self, mock_get_health):
        """Test successful system health check."""
        mock_health = {
            "status": "healthy",
            "database_connection": "OK",
            "services_available": True,
            "statistics": {
                "total_documents": 1000,
                "total_storage_bytes": 10737418240,
                "total_folders": 50,
            },
            "version": "31.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_get_health.return_value = mock_health

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services_available"] is True

    @patch("app.crud.document_v31.DocumentService.get_system_health")
    def test_system_health_failure(self, mock_get_health):
        """Test system health check failure handling."""
        mock_get_health.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services_available"] is False


# Integration test scenarios
class TestDocumentIntegrationScenarios:
    """Integration test scenarios for complete document workflows."""

    @patch("app.crud.document_v31.DocumentService")
    def test_complete_document_lifecycle(self, mock_service):
        """Test complete document lifecycle from creation to deletion."""
        mock_service_instance = mock_service.return_value

        # Setup mocks for the entire lifecycle
        mock_document = DocumentExtended(id="doc-123", title="Test Document")
        mock_folder = DocumentFolder(id="folder-456", name="Test Folder")
        mock_share = DocumentShare(id="share-789", document_id="doc-123")
        mock_comment = DocumentComment(id="comment-012", document_id="doc-123")

        mock_service_instance.create_folder.return_value = mock_folder
        mock_service_instance.create_document.return_value = mock_document
        mock_service_instance.create_document_share.return_value = mock_share
        mock_service_instance.create_document_comment.return_value = mock_comment
        mock_service_instance.delete_document.return_value = True

        # Execute the lifecycle
        # 1. Create folder
        folder_data = {
            "organization_id": "org-123",
            "name": "Test Folder",
            "owner_id": "user-123",
            "created_by_id": "user-123",
        }

        folder_response = client.post("/api/v1/folders", json=folder_data)
        assert folder_response.status_code == 201

        # 2. Create document
        document_data = {
            "organization_id": "org-123",
            "title": "Test Document",
            "document_type": "pdf",
            "filename": "test.pdf",
            "owner_id": "user-123",
            "created_by_id": "user-123",
            "folder_id": "folder-456",
        }

        document_response = client.post("/api/v1/documents", json=document_data)
        assert document_response.status_code == 201

        # 3. Share document
        share_data = {
            "organization_id": "org-123",
            "share_type": "user",
            "shared_with_user_id": "user-456",
            "access_level": "view",
        }

        share_response = client.post(
            "/api/v1/documents/doc-123/shares?shared_by_id=user-123", json=share_data
        )
        assert share_response.status_code == 201

        # 4. Add comment
        comment_data = {
            "organization_id": "org-123",
            "content": "Please review this document",
        }

        comment_response = client.post(
            "/api/v1/documents/doc-123/comments?author_id=user-123", json=comment_data
        )
        assert comment_response.status_code == 201

        # 5. Delete document
        delete_response = client.delete("/api/v1/documents/doc-123?user_id=user-123")
        assert delete_response.status_code == 200

    @patch("app.crud.document_v31.DocumentService")
    def test_approval_workflow_process(self, mock_service):
        """Test complete approval workflow process."""
        mock_service_instance = mock_service.return_value

        # Mock workflow and approval entities
        mock_workflow = DocumentWorkflow(id="workflow-123", name="Test Workflow")
        mock_approvals = [
            DocumentApproval(
                id="approval-1", step_number=1, status=ApprovalStatus.PENDING
            ),
            DocumentApproval(
                id="approval-2", step_number=2, status=ApprovalStatus.PENDING
            ),
        ]

        mock_service_instance.create_approval_workflow.return_value = mock_workflow
        mock_service_instance.submit_document_for_approval.return_value = mock_approvals
        mock_service_instance.process_approval_decision.return_value = mock_approvals[0]

        # Create workflow
        workflow_data = {
            "organization_id": "org-123",
            "name": "Test Workflow",
            "created_by_id": "user-123",
            "steps": [
                {"step": 1, "name": "Legal Review"},
                {"step": 2, "name": "Executive Approval"},
            ],
        }

        workflow_response = client.post("/api/v1/workflows", json=workflow_data)
        assert workflow_response.status_code == 201

        # Submit document for approval
        approval_data = {
            "workflow_id": "workflow-123",
            "approvers": [
                {"approver_id": "user-456", "step_name": "Legal Review"},
                {"approver_id": "user-789", "step_name": "Executive Approval"},
            ],
        }

        submission_response = client.post(
            "/api/v1/documents/doc-123/submit-approval?requested_by_id=user-123",
            json=approval_data,
        )
        assert submission_response.status_code == 200

        # Process approval decision
        decision_data = {
            "decision": "approved",
            "comments": "Approved with minor revisions",
        }

        decision_response = client.post(
            "/api/v1/approvals/approval-1/decision", json=decision_data
        )
        assert decision_response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
