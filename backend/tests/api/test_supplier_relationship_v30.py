from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app


# Mock database and auth dependencies
def override_get_db():
    return Mock(spec=Session)


def override_get_current_user():
    return {"sub": "test-user-123", "username": "testuser"}


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


class TestSupplierRelationshipAPI:
    """サプライヤー関係管理APIのテスト"""

    @pytest.fixture
    def sample_relationship_data(self):
        return {
            "supplier_id": "supplier-123",
            "relationship_type": "strategic",
            "partnership_level": "strategic",
            "contract_type": "master_agreement",
            "contract_start_date": "2024-01-01",
            "contract_end_date": "2025-12-31",
            "auto_renewal": True,
            "renewal_notice_days": 30,
            "overall_score": 4.5,
            "quality_score": 4.3,
            "delivery_score": 4.7,
            "service_score": 4.2,
            "cost_competitiveness": 4.0,
            "innovation_score": 3.8,
            "annual_spend": 5000000.00,
            "spend_percentage": 15.5,
            "cost_savings_achieved": 250000.00,
            "risk_level": "low",
            "business_continuity_risk": "low",
            "financial_risk": "medium",
            "compliance_risk": "low",
            "geographic_risk": "low",
            "strategic_importance": "high",
            "business_impact": "high",
            "substitutability": "low",
            "next_review_date": "2024-06-01",
            "review_frequency_months": 6,
            "notes": "Strategic supplier with excellent performance",
            "strengths": ["High quality", "Reliable delivery", "Innovation"],
            "weaknesses": ["Premium pricing"],
            "improvement_areas": ["Cost optimization"],
            "action_items": ["Negotiate better pricing", "Explore new technologies"],
        }

    @pytest.fixture
    def sample_relationship_response(self):
        return {
            "id": "rel-123",
            "supplier_id": "supplier-123",
            "relationship_manager_id": "test-user-123",
            "relationship_type": "strategic",
            "partnership_level": "strategic",
            "contract_type": "master_agreement",
            "contract_start_date": "2024-01-01",
            "contract_end_date": "2025-12-31",
            "auto_renewal": True,
            "renewal_notice_days": 30,
            "overall_score": 4.5,
            "quality_score": 4.3,
            "delivery_score": 4.7,
            "service_score": 4.2,
            "cost_competitiveness": 4.0,
            "innovation_score": 3.8,
            "annual_spend": 5000000.00,
            "spend_percentage": 15.5,
            "cost_savings_achieved": 250000.00,
            "risk_level": "low",
            "business_continuity_risk": "low",
            "financial_risk": "medium",
            "compliance_risk": "low",
            "geographic_risk": "low",
            "strategic_importance": "high",
            "business_impact": "high",
            "substitutability": "low",
            "status": "active",
            "approval_status": "approved",
            "approved_by": "manager-456",
            "approved_at": "2024-01-01T00:00:00",
            "next_review_date": "2024-06-01",
            "review_frequency_months": 6,
            "notes": "Strategic supplier with excellent performance",
            "strengths": ["High quality", "Reliable delivery", "Innovation"],
            "weaknesses": ["Premium pricing"],
            "improvement_areas": ["Cost optimization"],
            "action_items": ["Negotiate better pricing", "Explore new technologies"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "last_reviewed_at": "2024-01-01T00:00:00",
        }

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_create_supplier_relationship_success(
        self, mock_crud_class, sample_relationship_data, sample_relationship_response
    ):
        """サプライヤー関係作成成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_relationship_response)

        response = client.post(
            "/supplier-relationships/relationships", json=sample_relationship_data
        )

        assert response.status_code == 201
        mock_crud.create.assert_called_once()

        # Verify the response structure
        data = response.json()
        assert data["supplier_id"] == sample_relationship_data["supplier_id"]
        assert (
            data["relationship_type"] == sample_relationship_data["relationship_type"]
        )
        assert (
            data["partnership_level"] == sample_relationship_data["partnership_level"]
        )

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_create_supplier_relationship_duplicate_error(
        self, mock_crud_class, sample_relationship_data
    ):
        """サプライヤー関係作成重複エラーテスト"""
        from app.crud.supplier_relationship_v30 import DuplicateError

        mock_crud = mock_crud_class.return_value
        mock_crud.create.side_effect = DuplicateError(
            "Supplier relationship already exists"
        )

        response = client.post(
            "/supplier-relationships/relationships", json=sample_relationship_data
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_get_supplier_relationship_success(
        self, mock_crud_class, sample_relationship_response
    ):
        """サプライヤー関係詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_relationship_response)

        relationship_id = "rel-123"
        response = client.get(
            f"/supplier-relationships/relationships/{relationship_id}"
        )

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(relationship_id)

        data = response.json()
        assert data["id"] == relationship_id

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_get_supplier_relationship_not_found(self, mock_crud_class):
        """サプライヤー関係詳細取得未発見テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = None

        relationship_id = "nonexistent-rel"
        response = client.get(
            f"/supplier-relationships/relationships/{relationship_id}"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_list_supplier_relationships_success(
        self, mock_crud_class, sample_relationship_response
    ):
        """サプライヤー関係一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_relationships = [Mock(**sample_relationship_response)]
        mock_crud.get_multi.return_value = (mock_relationships, 1)

        response = client.get("/supplier-relationships/relationships")

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()

        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert len(data["items"]) == 1

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_list_supplier_relationships_with_filters(
        self, mock_crud_class, sample_relationship_response
    ):
        """フィルター付きサプライヤー関係一覧取得テスト"""
        mock_crud = mock_crud_class.return_value
        mock_relationships = [Mock(**sample_relationship_response)]
        mock_crud.get_multi.return_value = (mock_relationships, 1)

        params = {
            "supplier_id": "supplier-123",
            "relationship_type": "strategic",
            "partnership_level": "strategic",
            "risk_level": "low",
            "page": 1,
            "per_page": 10,
        }
        response = client.get("/supplier-relationships/relationships", params=params)

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()

        # Check that filters were passed to the CRUD method
        call_args = mock_crud.get_multi.call_args
        filters = call_args.kwargs["filters"]
        assert filters["supplier_id"] == "supplier-123"
        assert filters["relationship_type"] == "strategic"

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_update_supplier_relationship_success(
        self, mock_crud_class, sample_relationship_response
    ):
        """サプライヤー関係更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_relationship_response.copy()
        updated_response["overall_score"] = 4.8
        mock_crud.update.return_value = Mock(**updated_response)

        relationship_id = "rel-123"
        update_data = {"overall_score": 4.8, "notes": "Updated performance"}
        response = client.put(
            f"/supplier-relationships/relationships/{relationship_id}", json=update_data
        )

        assert response.status_code == 200
        mock_crud.update.assert_called_once_with(relationship_id, Mock())

        data = response.json()
        assert data["overall_score"] == 4.8

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_update_supplier_relationship_not_found(self, mock_crud_class):
        """サプライヤー関係更新未発見テスト"""
        from app.crud.supplier_relationship_v30 import NotFoundError

        mock_crud = mock_crud_class.return_value
        mock_crud.update.side_effect = NotFoundError("Relationship not found")

        relationship_id = "nonexistent-rel"
        update_data = {"overall_score": 4.8}
        response = client.put(
            f"/supplier-relationships/relationships/{relationship_id}", json=update_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_approve_supplier_relationship_success(
        self, mock_crud_class, sample_relationship_response
    ):
        """サプライヤー関係承認成功テスト"""
        mock_crud = mock_crud_class.return_value
        approved_response = sample_relationship_response.copy()
        approved_response["approval_status"] = "approved"
        mock_crud.approve.return_value = Mock(**approved_response)

        relationship_id = "rel-123"
        response = client.post(
            f"/supplier-relationships/relationships/{relationship_id}/approve"
        )

        assert response.status_code == 200
        mock_crud.approve.assert_called_once_with(relationship_id, "test-user-123")

        data = response.json()
        assert data["approval_status"] == "approved"

    @patch("app.api.v1.supplier_relationship_v30.SupplierRelationshipCRUD")
    def test_schedule_supplier_review_success(self, mock_crud_class):
        """サプライヤーレビュー日程設定成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.schedule_review.return_value = None

        relationship_id = "rel-123"
        review_date = "2024-06-01"
        response = client.post(
            f"/supplier-relationships/relationships/{relationship_id}/schedule-review?review_date={review_date}"
        )

        assert response.status_code == 200
        mock_crud.schedule_review.assert_called_once()

        data = response.json()
        assert "successfully" in data["message"]


class TestSupplierPerformanceReviewAPI:
    """サプライヤーパフォーマンスレビューAPIのテスト"""

    @pytest.fixture
    def sample_review_data(self):
        return {
            "supplier_relationship_id": "rel-123",
            "review_period_start": "2024-01-01",
            "review_period_end": "2024-03-31",
            "review_type": "quarterly",
            "quality_rating": 4.5,
            "delivery_rating": 4.3,
            "service_rating": 4.2,
            "cost_rating": 3.8,
            "innovation_rating": 4.0,
            "compliance_rating": 4.7,
            "communication_rating": 4.1,
            "responsiveness_rating": 4.4,
            "on_time_delivery_rate": 95.5,
            "quality_defect_rate": 0.8,
            "cost_variance": -2.3,
            "invoice_accuracy_rate": 98.2,
            "response_time_hours": 2.5,
            "strengths_identified": ["Excellent quality", "Fast response"],
            "weaknesses_identified": ["Higher costs"],
            "improvement_recommendations": ["Cost optimization"],
            "action_items": ["Review pricing model"],
            "quality_comments": "Consistently high quality products",
            "delivery_comments": "On-time delivery performance excellent",
            "service_comments": "Responsive customer service",
            "cost_comments": "Pricing slightly above market",
            "general_comments": "Strong overall performance",
            "next_period_goals": ["Reduce costs by 5%"],
            "improvement_plan": "Work with supplier on cost reduction initiatives",
        }

    @pytest.fixture
    def sample_review_response(self):
        return {
            "id": "review-123",
            "supplier_relationship_id": "rel-123",
            "reviewer_id": "test-user-123",
            "review_period_start": "2024-01-01",
            "review_period_end": "2024-03-31",
            "review_type": "quarterly",
            "review_status": "draft",
            "quality_rating": 4.5,
            "delivery_rating": 4.3,
            "service_rating": 4.2,
            "cost_rating": 3.8,
            "innovation_rating": 4.0,
            "compliance_rating": 4.7,
            "communication_rating": 4.1,
            "responsiveness_rating": 4.4,
            "overall_rating": 4.25,
            "overall_grade": "A",
            "on_time_delivery_rate": 95.5,
            "quality_defect_rate": 0.8,
            "cost_variance": -2.3,
            "invoice_accuracy_rate": 98.2,
            "response_time_hours": 2.5,
            "strengths_identified": ["Excellent quality", "Fast response"],
            "weaknesses_identified": ["Higher costs"],
            "improvement_recommendations": ["Cost optimization"],
            "action_items": ["Review pricing model"],
            "quality_comments": "Consistently high quality products",
            "delivery_comments": "On-time delivery performance excellent",
            "service_comments": "Responsive customer service",
            "cost_comments": "Pricing slightly above market",
            "general_comments": "Strong overall performance",
            "next_period_goals": ["Reduce costs by 5%"],
            "improvement_plan": "Work with supplier on cost reduction initiatives",
            "approved_by": None,
            "approved_at": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "completed_at": None,
        }

    @patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReviewCRUD")
    def test_create_performance_review_success(
        self, mock_crud_class, sample_review_data, sample_review_response
    ):
        """パフォーマンスレビュー作成成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_review_response)

        response = client.post(
            "/supplier-relationships/performance-reviews", json=sample_review_data
        )

        assert response.status_code == 201
        mock_crud.create.assert_called_once()

        data = response.json()
        assert (
            data["supplier_relationship_id"]
            == sample_review_data["supplier_relationship_id"]
        )
        assert data["review_type"] == sample_review_data["review_type"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReviewCRUD")
    def test_get_performance_review_success(
        self, mock_crud_class, sample_review_response
    ):
        """パフォーマンスレビュー詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_review_response)

        review_id = "review-123"
        response = client.get(
            f"/supplier-relationships/performance-reviews/{review_id}"
        )

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(review_id)

        data = response.json()
        assert data["id"] == review_id

    @patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReviewCRUD")
    def test_list_relationship_performance_reviews_success(
        self, mock_crud_class, sample_review_response
    ):
        """関係別パフォーマンスレビュー一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_reviews = [Mock(**sample_review_response)]
        mock_crud.get_multi_by_relationship.return_value = (mock_reviews, 1)

        relationship_id = "rel-123"
        response = client.get(
            f"/supplier-relationships/relationships/{relationship_id}/performance-reviews"
        )

        assert response.status_code == 200
        mock_crud.get_multi_by_relationship.assert_called_once()

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReviewCRUD")
    def test_update_performance_review_success(
        self, mock_crud_class, sample_review_response
    ):
        """パフォーマンスレビュー更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_review_response.copy()
        updated_response["review_status"] = "completed"
        mock_crud.update.return_value = Mock(**updated_response)

        review_id = "review-123"
        update_data = {
            "review_status": "completed",
            "general_comments": "Review completed",
        }
        response = client.put(
            f"/supplier-relationships/performance-reviews/{review_id}", json=update_data
        )

        assert response.status_code == 200
        mock_crud.update.assert_called_once()

        data = response.json()
        assert data["review_status"] == "completed"

    @patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReviewCRUD")
    def test_approve_performance_review_success(
        self, mock_crud_class, sample_review_response
    ):
        """パフォーマンスレビュー承認成功テスト"""
        mock_crud = mock_crud_class.return_value
        approved_response = sample_review_response.copy()
        approved_response["review_status"] = "approved"
        mock_crud.approve.return_value = Mock(**approved_response)

        review_id = "review-123"
        response = client.post(
            f"/supplier-relationships/performance-reviews/{review_id}/approve"
        )

        assert response.status_code == 200
        mock_crud.approve.assert_called_once_with(review_id, "test-user-123")

        data = response.json()
        assert data["review_status"] == "approved"


class TestSupplierNegotiationAPI:
    """サプライヤー交渉APIのテスト"""

    @pytest.fixture
    def sample_negotiation_data(self):
        return {
            "supplier_relationship_id": "rel-123",
            "negotiation_title": "Annual Contract Renewal 2024",
            "negotiation_type": "contract_renewal",
            "description": "Renewal negotiation for main supply contract",
            "start_date": "2024-01-15",
            "target_completion_date": "2024-03-01",
            "primary_objectives": ["Reduce costs by 5%", "Improve delivery terms"],
            "secondary_objectives": ["Extended payment terms"],
            "minimum_acceptable_terms": ["Cost reduction minimum 2%"],
            "current_annual_value": 5000000.00,
            "target_annual_value": 4750000.00,
            "estimated_savings": 250000.00,
            "payment_terms": "Net 30 days",
            "delivery_terms": "FOB destination",
            "quality_requirements": "ISO 9001 certification required",
            "service_level_agreements": [
                {
                    "metric": "Response time",
                    "target": "24 hours",
                    "penalty": "1% reduction",
                }
            ],
            "penalty_clauses": [
                {"condition": "Late delivery", "penalty": "2% of order value"}
            ],
            "identified_risks": ["Supplier may reject cost reduction"],
            "mitigation_strategies": ["Offer longer-term contract"],
            "escalation_points": ["If cost reduction below 3%"],
            "negotiation_team": ["user-123", "user-456"],
            "supplier_representatives": [
                "John Smith - Procurement Manager",
                "Jane Doe - Sales Director",
            ],
        }

    @pytest.fixture
    def sample_negotiation_response(self):
        return {
            "id": "neg-123",
            "supplier_relationship_id": "rel-123",
            "lead_negotiator_id": "test-user-123",
            "negotiation_title": "Annual Contract Renewal 2024",
            "negotiation_type": "contract_renewal",
            "description": "Renewal negotiation for main supply contract",
            "status": "preparation",
            "current_phase": "planning",
            "start_date": "2024-01-15",
            "target_completion_date": "2024-03-01",
            "actual_completion_date": None,
            "next_meeting_date": None,
            "primary_objectives": ["Reduce costs by 5%", "Improve delivery terms"],
            "secondary_objectives": ["Extended payment terms"],
            "minimum_acceptable_terms": ["Cost reduction minimum 2%"],
            "achieved_outcomes": [],
            "current_annual_value": 5000000.00,
            "target_annual_value": 4750000.00,
            "achieved_annual_value": None,
            "estimated_savings": 250000.00,
            "actual_savings": None,
            "payment_terms": "Net 30 days",
            "delivery_terms": "FOB destination",
            "quality_requirements": "ISO 9001 certification required",
            "service_level_agreements": [
                {
                    "metric": "Response time",
                    "target": "24 hours",
                    "penalty": "1% reduction",
                }
            ],
            "penalty_clauses": [
                {"condition": "Late delivery", "penalty": "2% of order value"}
            ],
            "identified_risks": ["Supplier may reject cost reduction"],
            "mitigation_strategies": ["Offer longer-term contract"],
            "escalation_points": ["If cost reduction below 3%"],
            "negotiation_team": ["user-123", "user-456"],
            "supplier_representatives": [
                "John Smith - Procurement Manager",
                "Jane Doe - Sales Director",
            ],
            "success_rating": None,
            "objectives_achieved_percentage": None,
            "relationship_impact": None,
            "meeting_notes": [],
            "documents_exchanged": [],
            "final_agreement_document": None,
            "requires_approval": True,
            "approved_by": None,
            "approved_at": None,
            "approval_notes": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    @patch("app.api.v1.supplier_relationship_v30.SupplierNegotiationCRUD")
    def test_create_supplier_negotiation_success(
        self, mock_crud_class, sample_negotiation_data, sample_negotiation_response
    ):
        """サプライヤー交渉作成成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_negotiation_response)

        response = client.post(
            "/supplier-relationships/negotiations", json=sample_negotiation_data
        )

        assert response.status_code == 201
        mock_crud.create.assert_called_once()

        data = response.json()
        assert data["negotiation_title"] == sample_negotiation_data["negotiation_title"]
        assert data["negotiation_type"] == sample_negotiation_data["negotiation_type"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierNegotiationCRUD")
    def test_get_supplier_negotiation_success(
        self, mock_crud_class, sample_negotiation_response
    ):
        """サプライヤー交渉詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_negotiation_response)

        negotiation_id = "neg-123"
        response = client.get(f"/supplier-relationships/negotiations/{negotiation_id}")

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(negotiation_id)

        data = response.json()
        assert data["id"] == negotiation_id

    @patch("app.api.v1.supplier_relationship_v30.SupplierNegotiationCRUD")
    def test_list_supplier_negotiations_success(
        self, mock_crud_class, sample_negotiation_response
    ):
        """サプライヤー交渉一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_negotiations = [Mock(**sample_negotiation_response)]
        mock_crud.get_multi.return_value = (mock_negotiations, 1)

        response = client.get("/supplier-relationships/negotiations")

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch("app.api.v1.supplier_relationship_v30.SupplierNegotiationCRUD")
    def test_update_supplier_negotiation_success(
        self, mock_crud_class, sample_negotiation_response
    ):
        """サプライヤー交渉更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_negotiation_response.copy()
        updated_response["status"] = "active"
        mock_crud.update.return_value = Mock(**updated_response)

        negotiation_id = "neg-123"
        update_data = {"status": "active", "current_phase": "negotiation"}
        response = client.put(
            f"/supplier-relationships/negotiations/{negotiation_id}", json=update_data
        )

        assert response.status_code == 200
        mock_crud.update.assert_called_once()

        data = response.json()
        assert data["status"] == "active"

    @patch("app.api.v1.supplier_relationship_v30.SupplierNegotiationCRUD")
    def test_complete_supplier_negotiation_success(
        self, mock_crud_class, sample_negotiation_response
    ):
        """サプライヤー交渉完了成功テスト"""
        mock_crud = mock_crud_class.return_value
        completed_response = sample_negotiation_response.copy()
        completed_response["status"] = "completed"
        mock_crud.complete.return_value = Mock(**completed_response)

        negotiation_id = "neg-123"
        final_document = "final_agreement.pdf"
        response = client.post(
            f"/supplier-relationships/negotiations/{negotiation_id}/complete?final_agreement_document={final_document}"
        )

        assert response.status_code == 200
        mock_crud.complete.assert_called_once_with(negotiation_id, final_document)

        data = response.json()
        assert data["status"] == "completed"


class TestSupplierContractAPI:
    """サプライヤー契約APIのテスト"""

    @pytest.fixture
    def sample_contract_data(self):
        return {
            "supplier_id": "supplier-123",
            "contract_title": "Master Supply Agreement 2024",
            "contract_type": "purchase_agreement",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-12-31",
            "contract_duration_months": 24,
            "auto_renewal": True,
            "renewal_notice_days": 60,
            "contract_value": 10000000.00,
            "currency": "JPY",
            "pricing_model": "fixed",
            "payment_terms": "Net 30 days",
            "payment_schedule": [
                {
                    "milestone": "Contract signing",
                    "percentage": 20,
                    "due_date": "2024-01-01",
                }
            ],
            "early_payment_discount": 2.0,
            "late_payment_penalty": 1.5,
            "delivery_terms": "FOB destination",
            "delivery_location": "Tokyo Warehouse",
            "lead_time_days": 14,
            "minimum_order_quantity": 1000.00,
            "quality_standards": ["ISO 9001", "JIS standards"],
            "compliance_requirements": [
                "Environmental regulations",
                "Safety standards",
            ],
            "audit_rights": True,
            "certifications_required": ["ISO 9001", "ISO 14001"],
            "service_level_agreements": [
                {
                    "metric": "On-time delivery",
                    "target": "95%",
                    "measurement": "monthly",
                }
            ],
            "key_performance_indicators": [
                {"kpi": "Quality defect rate", "target": "<1%", "frequency": "monthly"}
            ],
            "performance_bonuses": [
                {"condition": "Zero defects", "bonus": "1% of order value"}
            ],
            "performance_penalties": [
                {"condition": "Late delivery", "penalty": "2% of order value"}
            ],
            "liability_cap": 50000000.00,
            "insurance_requirements": [
                "Product liability $10M",
                "General liability $5M",
            ],
            "force_majeure_clauses": ["Natural disasters", "Government regulations"],
            "termination_conditions": [
                "Material breach",
                "Insolvency",
                "Change of control",
            ],
            "contract_document_path": "/contracts/supplier-123/master-agreement-2024.pdf",
            "related_documents": ["specifications.pdf", "quality-manual.pdf"],
            "confidentiality_level": "confidential",
            "tags": ["strategic", "long-term", "high-value"],
            "notes": "Critical supply agreement for main product line",
        }

    @pytest.fixture
    def sample_contract_response(self):
        return {
            "id": "contract-123",
            "contract_number": "SC-202401-0001",
            "supplier_id": "supplier-123",
            "contract_manager_id": "test-user-123",
            "contract_title": "Master Supply Agreement 2024",
            "contract_type": "purchase_agreement",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-12-31",
            "contract_duration_months": 24,
            "auto_renewal": True,
            "renewal_notice_days": 60,
            "contract_value": 10000000.00,
            "currency": "JPY",
            "pricing_model": "fixed",
            "payment_terms": "Net 30 days",
            "payment_schedule": [
                {
                    "milestone": "Contract signing",
                    "percentage": 20,
                    "due_date": "2024-01-01",
                }
            ],
            "early_payment_discount": 2.0,
            "late_payment_penalty": 1.5,
            "delivery_terms": "FOB destination",
            "delivery_location": "Tokyo Warehouse",
            "lead_time_days": 14,
            "minimum_order_quantity": 1000.00,
            "quality_standards": ["ISO 9001", "JIS standards"],
            "compliance_requirements": [
                "Environmental regulations",
                "Safety standards",
            ],
            "audit_rights": True,
            "certifications_required": ["ISO 9001", "ISO 14001"],
            "service_level_agreements": [
                {
                    "metric": "On-time delivery",
                    "target": "95%",
                    "measurement": "monthly",
                }
            ],
            "key_performance_indicators": [
                {"kpi": "Quality defect rate", "target": "<1%", "frequency": "monthly"}
            ],
            "performance_bonuses": [
                {"condition": "Zero defects", "bonus": "1% of order value"}
            ],
            "performance_penalties": [
                {"condition": "Late delivery", "penalty": "2% of order value"}
            ],
            "liability_cap": 50000000.00,
            "insurance_requirements": [
                "Product liability $10M",
                "General liability $5M",
            ],
            "force_majeure_clauses": ["Natural disasters", "Government regulations"],
            "termination_conditions": [
                "Material breach",
                "Insolvency",
                "Change of control",
            ],
            "status": "draft",
            "approval_workflow": [],
            "signed_by_supplier": False,
            "signed_by_company": False,
            "company_signatory": None,
            "signing_date": None,
            "contract_document_path": "/contracts/supplier-123/master-agreement-2024.pdf",
            "amendment_documents": [],
            "related_documents": ["specifications.pdf", "quality-manual.pdf"],
            "renewal_alert_sent": False,
            "expiry_alert_sent": False,
            "performance_alert_sent": False,
            "confidentiality_level": "confidential",
            "tags": ["strategic", "long-term", "high-value"],
            "notes": "Critical supply agreement for main product line",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_create_supplier_contract_success(
        self, mock_crud_class, sample_contract_data, sample_contract_response
    ):
        """サプライヤー契約作成成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_contract_response)

        response = client.post(
            "/supplier-relationships/contracts", json=sample_contract_data
        )

        assert response.status_code == 201
        mock_crud.create.assert_called_once()

        data = response.json()
        assert data["contract_title"] == sample_contract_data["contract_title"]
        assert data["contract_type"] == sample_contract_data["contract_type"]

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_get_supplier_contract_success(
        self, mock_crud_class, sample_contract_response
    ):
        """サプライヤー契約詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_contract_response)

        contract_id = "contract-123"
        response = client.get(f"/supplier-relationships/contracts/{contract_id}")

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(contract_id)

        data = response.json()
        assert data["id"] == contract_id

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_list_supplier_contracts_success(
        self, mock_crud_class, sample_contract_response
    ):
        """サプライヤー契約一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_contracts = [Mock(**sample_contract_response)]
        mock_crud.get_multi.return_value = (mock_contracts, 1)

        response = client.get("/supplier-relationships/contracts")

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_update_supplier_contract_success(
        self, mock_crud_class, sample_contract_response
    ):
        """サプライヤー契約更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_contract_response.copy()
        updated_response["status"] = "active"
        mock_crud.update.return_value = Mock(**updated_response)

        contract_id = "contract-123"
        update_data = {"status": "active", "signed_by_company": True}
        response = client.put(
            f"/supplier-relationships/contracts/{contract_id}", json=update_data
        )

        assert response.status_code == 200
        mock_crud.update.assert_called_once()

        data = response.json()
        assert data["status"] == "active"


class TestSupplierAnalyticsAPI:
    """サプライヤー分析APIのテスト"""

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_get_supplier_relationship_stats_success(self, mock_crud_class):
        """サプライヤー関係統計取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_stats = {
            "total_relationships": 150,
            "active_relationships": 120,
            "strategic_partnerships": 25,
            "avg_relationship_score": Decimal("4.2"),
            "total_annual_spend": Decimal("50000000.00"),
            "cost_savings_achieved": Decimal("2500000.00"),
            "contracts_expiring_soon": 8,
            "reviews_overdue": 5,
            "by_partnership_level": {
                "strategic": 25,
                "preferred": 45,
                "standard": 60,
                "conditional": 20,
            },
            "by_risk_level": {"critical": 3, "high": 12, "medium": 45, "low": 90},
            "top_suppliers_by_spend": [
                {
                    "supplier_id": "supplier-001",
                    "annual_spend": Decimal("5000000.00"),
                    "overall_score": Decimal("4.5"),
                    "partnership_level": "strategic",
                }
            ],
            "relationship_distribution": {
                "vendor": 80,
                "partner": 45,
                "strategic": 25,
                "preferred": 0,
            },
        }
        mock_crud.get_relationship_analytics.return_value = mock_stats

        response = client.get("/supplier-relationships/stats")

        assert response.status_code == 200
        mock_crud.get_relationship_analytics.assert_called_once()

        data = response.json()
        assert data["total_relationships"] == 150
        assert data["active_relationships"] == 120
        assert data["strategic_partnerships"] == 25

    def test_get_supplier_performance_analytics_success(self):
        """サプライヤーパフォーマンス分析データ取得成功テスト"""
        date_from = "2024-01-01T00:00:00"
        date_to = "2024-03-31T23:59:59"

        with patch("app.api.v1.supplier_relationship_v30.SupplierPerformanceReview"):
            with patch("app.api.v1.supplier_relationship_v30.func"):
                # Mock database query results
                mock_reviews = []  # Empty list for simplicity

                # Mock the database session and query chain
                mock_db = Mock()
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = mock_reviews
                mock_db.query.return_value = mock_query

                with patch(
                    "app.api.v1.supplier_relationship_v30.get_db", return_value=mock_db
                ):
                    response = client.get(
                        f"/supplier-relationships/performance-analytics?date_from={date_from}&date_to={date_to}"
                    )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "period_start" in data
        assert "period_end" in data
        assert "total_suppliers_reviewed" in data
        assert "avg_overall_rating" in data
        assert "top_performing_suppliers" in data
        assert "improvement_needed_suppliers" in data
        assert "performance_trends" in data
        assert "category_performance" in data

    @patch("app.api.v1.supplier_relationship_v30.SupplierContractCRUD")
    def test_get_expiring_contracts_success(self, mock_crud_class):
        """期限が近い契約取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_contracts = [
            Mock(
                id="contract-123",
                contract_number="SC-202401-0001",
                supplier_id="supplier-123",
                contract_title="Master Agreement",
                expiration_date=date.today() + timedelta(days=20),
                contract_value=Decimal("1000000.00"),
                auto_renewal=True,
            )
        ]
        mock_crud.get_expiring_contracts.return_value = mock_contracts

        days = 30
        response = client.get(f"/supplier-relationships/contracts/expiring?days={days}")

        assert response.status_code == 200
        mock_crud.get_expiring_contracts.assert_called_once_with(days)

        data = response.json()
        assert data["contracts_count"] == 1
        assert len(data["contracts"]) == 1

        contract = data["contracts"][0]
        assert contract["contract_id"] == "contract-123"
        assert contract["contract_number"] == "SC-202401-0001"
        assert contract["days_until_expiry"] == 20


class TestSupplierRelationshipValidation:
    """サプライヤー関係管理APIバリデーションテスト"""

    def test_create_relationship_invalid_data(self):
        """サプライヤー関係作成無効データテスト"""
        invalid_data = {
            "supplier_id": "",  # Empty supplier_id
            "relationship_type": "invalid_type",  # Invalid enum
            "overall_score": 6.0,  # Out of range (max 5.0)
            "annual_spend": -1000,  # Negative value
        }

        response = client.post(
            "/supplier-relationships/relationships", json=invalid_data
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0

    def test_create_review_missing_required_fields(self):
        """パフォーマンスレビュー作成必須フィールド不足テスト"""
        invalid_data = {
            "review_period_start": "2024-01-01",
            # Missing supplier_relationship_id and review_period_end
            "quality_rating": 4.5,
        }

        response = client.post(
            "/supplier-relationships/performance-reviews", json=invalid_data
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]
        assert "supplier_relationship_id" in error_fields
        assert "review_period_end" in error_fields

    def test_create_negotiation_invalid_dates(self):
        """サプライヤー交渉作成無効日付テスト"""
        invalid_data = {
            "supplier_relationship_id": "rel-123",
            "negotiation_title": "Test Negotiation",
            "start_date": "2024-03-01",
            "target_completion_date": "2024-01-01",  # Earlier than start_date
            "current_annual_value": -1000,  # Negative value
        }

        response = client.post(
            "/supplier-relationships/negotiations", json=invalid_data
        )

        assert response.status_code == 422

    def test_create_contract_invalid_pricing(self):
        """サプライヤー契約作成無効価格テスト"""
        invalid_data = {
            "supplier_id": "supplier-123",
            "contract_title": "Test Contract",
            "contract_type": "invalid_type",  # Invalid enum
            "effective_date": "2024-01-01",
            "contract_value": -1000,  # Negative value
            "early_payment_discount": 150,  # Over 100%
        }

        response = client.post("/supplier-relationships/contracts", json=invalid_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0

    def test_list_relationships_invalid_pagination(self):
        """サプライヤー関係一覧無効ページネーションテスト"""
        params = {
            "page": 0,  # Invalid page (minimum 1)
            "per_page": 150,  # Over maximum (100)
        }

        response = client.get("/supplier-relationships/relationships", params=params)

        assert response.status_code == 422

    def test_performance_analytics_missing_dates(self):
        """パフォーマンス分析日付不足テスト"""
        response = client.get("/supplier-relationships/performance-analytics")

        assert response.status_code == 422
        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]
        assert "date_from" in error_fields
        assert "date_to" in error_fields
