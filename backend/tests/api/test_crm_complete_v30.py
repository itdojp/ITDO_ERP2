import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid

from app.main import app
from app.schemas.crm_complete_v30 import (
    CRMCustomerCreate, CRMCustomerUpdate, CustomerInteractionCreate, CustomerInteractionUpdate,
    SalesOpportunityCreate, SalesOpportunityUpdate, OpportunityActivityCreate,
    CustomerActivityCreate, CustomerSegmentCreate, CustomerSegmentUpdate,
    MarketingCampaignCreate, MarketingCampaignUpdate
)

client = TestClient(app)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_current_user():
    return {"sub": str(uuid.uuid4()), "username": "testuser"}

class TestCRMCustomerAPI:
    def test_create_crm_customer(self, mock_db, mock_current_user):
        """CRM顧客作成テスト"""
        customer_data = CRMCustomerCreate(
            customer_code="CRM001",
            full_name="田中太郎",
            primary_email="tanaka@example.com",
            company_name="テスト株式会社",
            job_title="営業部長",
            customer_type="business",
            lead_status="new",
            customer_stage="prospect",
            industry="manufacturing"
        )
        
        mock_customer = Mock()
        mock_customer.id = str(uuid.uuid4())
        mock_customer.customer_code = customer_data.customer_code
        mock_customer.full_name = customer_data.full_name
        mock_customer.created_at = datetime.utcnow()
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CRMCustomerCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_customer
            
            response = client.post("/api/v1/crm/customers", json=customer_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once()

    def test_get_crm_customer(self, mock_db, mock_current_user):
        """CRM顧客詳細取得テスト"""
        customer_id = str(uuid.uuid4())
        
        mock_customer = Mock()
        mock_customer.id = customer_id
        mock_customer.full_name = "田中太郎"
        mock_customer.customer_code = "CRM001"
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CRMCustomerCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_customer
            
            response = client.get(f"/api/v1/crm/customers/{customer_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(customer_id)

    def test_list_crm_customers(self, mock_db, mock_current_user):
        """CRM顧客一覧取得テスト"""
        mock_customers = [Mock() for _ in range(5)]
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CRMCustomerCRUD") as mock_crud:
            
            mock_crud.return_value.get_multi.return_value = (mock_customers, 5)
            
            response = client.get("/api/v1/crm/customers?page=1&per_page=20&lead_status=new")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 5
            assert data["page"] == 1

    def test_update_crm_customer(self, mock_db, mock_current_user):
        """CRM顧客情報更新テスト"""
        customer_id = str(uuid.uuid4())
        update_data = CRMCustomerUpdate(
            lead_status="qualified",
            is_vip=True,
            lead_score=85
        )
        
        mock_customer = Mock()
        mock_customer.id = customer_id
        mock_customer.lead_status = update_data.lead_status
        mock_customer.is_vip = update_data.is_vip
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CRMCustomerCRUD") as mock_crud:
            
            mock_crud.return_value.update.return_value = mock_customer
            
            response = client.put(
                f"/api/v1/crm/customers/{customer_id}",
                json=update_data.dict(exclude_unset=True)
            )
            
            assert response.status_code == 200
            mock_crud.return_value.update.assert_called_once()

    def test_add_customer_to_segment(self, mock_db, mock_current_user):
        """顧客をセグメントに追加テスト"""
        customer_id = str(uuid.uuid4())
        segment_id = str(uuid.uuid4())
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CRMCustomerCRUD") as mock_crud:
            
            response = client.post(f"/api/v1/crm/customers/{customer_id}/segments/{segment_id}/add")
            
            assert response.status_code == 200
            mock_crud.return_value.add_to_segment.assert_called_once_with(
                customer_id, segment_id, mock_current_user["sub"]
            )

class TestCustomerInteractionAPI:
    def test_create_customer_interaction(self, mock_db, mock_current_user):
        """顧客インタラクション作成テスト"""
        interaction_data = CustomerInteractionCreate(
            customer_id=str(uuid.uuid4()),
            interaction_type="call",
            subject="フォローアップ電話",
            description="商品説明とデモの日程調整",
            outcome="meeting_scheduled",
            duration_minutes=30,
            satisfaction_rating=4
        )
        
        mock_interaction = Mock()
        mock_interaction.id = str(uuid.uuid4())
        mock_interaction.subject = interaction_data.subject
        mock_interaction.outcome = interaction_data.outcome
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CustomerInteractionCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_interaction
            
            response = client.post("/api/v1/crm/interactions", json=interaction_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(interaction_data, mock_current_user["sub"])

    def test_get_customer_interactions(self, mock_db, mock_current_user):
        """顧客インタラクション一覧取得テスト"""
        customer_id = str(uuid.uuid4())
        mock_interactions = [Mock() for _ in range(10)]
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CustomerInteractionCRUD") as mock_crud:
            
            mock_crud.return_value.get_multi_by_customer.return_value = (mock_interactions, 10)
            
            response = client.get(f"/api/v1/crm/customers/{customer_id}/interactions?page=1&per_page=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 10
            mock_crud.return_value.get_multi_by_customer.assert_called_once()

class TestSalesOpportunityAPI:
    def test_create_sales_opportunity(self, mock_db, mock_current_user):
        """営業機会作成テスト"""
        opportunity_data = SalesOpportunityCreate(
            customer_id=str(uuid.uuid4()),
            name="新システム導入プロジェクト",
            amount=Decimal("5000000"),
            probability=75,
            stage="qualification",
            expected_close_date=date.today() + timedelta(days=30),
            product_category="software",
            solution_type="enterprise",
            competitors=["競合A", "競合B"],
            budget_confirmed=True
        )
        
        mock_opportunity = Mock()
        mock_opportunity.id = str(uuid.uuid4())
        mock_opportunity.opportunity_number = "OPP-202401-0001"
        mock_opportunity.name = opportunity_data.name
        mock_opportunity.amount = opportunity_data.amount
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.SalesOpportunityCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_opportunity
            
            response = client.post("/api/v1/crm/opportunities", json=opportunity_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(opportunity_data, mock_current_user["sub"])

    def test_get_sales_opportunity(self, mock_db, mock_current_user):
        """営業機会詳細取得テスト"""
        opportunity_id = str(uuid.uuid4())
        
        mock_opportunity = Mock()
        mock_opportunity.id = opportunity_id
        mock_opportunity.name = "新システム導入プロジェクト"
        mock_opportunity.stage = "qualification"
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.SalesOpportunityCRUD") as mock_crud:
            
            mock_crud.return_value.get_by_id.return_value = mock_opportunity
            
            response = client.get(f"/api/v1/crm/opportunities/{opportunity_id}")
            
            assert response.status_code == 200
            mock_crud.return_value.get_by_id.assert_called_once_with(opportunity_id)

    def test_list_sales_opportunities(self, mock_db, mock_current_user):
        """営業機会一覧取得テスト"""
        mock_opportunities = [Mock() for _ in range(15)]
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.SalesOpportunityCRUD") as mock_crud:
            
            mock_crud.return_value.get_multi.return_value = (mock_opportunities, 15)
            
            response = client.get("/api/v1/crm/opportunities?page=1&per_page=20&stage=qualification")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 15
            assert data["page"] == 1

    def test_update_sales_opportunity(self, mock_db, mock_current_user):
        """営業機会更新テスト"""
        opportunity_id = str(uuid.uuid4())
        update_data = SalesOpportunityUpdate(
            stage="proposal",
            probability=85,
            next_action="提案書作成",
            next_action_date=date.today() + timedelta(days=3)
        )
        
        mock_opportunity = Mock()
        mock_opportunity.id = opportunity_id
        mock_opportunity.stage = update_data.stage
        mock_opportunity.probability = update_data.probability
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.SalesOpportunityCRUD") as mock_crud:
            
            mock_crud.return_value.update.return_value = mock_opportunity
            
            response = client.put(
                f"/api/v1/crm/opportunities/{opportunity_id}",
                json=update_data.dict(exclude_unset=True)
            )
            
            assert response.status_code == 200
            mock_crud.return_value.update.assert_called_once()

class TestSegmentAPI:
    def test_create_customer_segment(self, mock_db, mock_current_user):
        """顧客セグメント作成テスト"""
        segment_data = CustomerSegmentCreate(
            name="高価値顧客",
            description="年間売上500万円以上の企業顧客",
            segment_type="dynamic",
            criteria={
                "lifetime_value_min": 5000000,
                "customer_type": "business",
                "is_active": True
            },
            color="#ff6b6b"
        )
        
        mock_segment = Mock()
        mock_segment.id = str(uuid.uuid4())
        mock_segment.name = segment_data.name
        mock_segment.description = segment_data.description
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CustomerSegmentCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_segment
            
            response = client.post("/api/v1/crm/segments", json=segment_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(segment_data, mock_current_user["sub"])

    def test_calculate_segment_metrics(self, mock_db, mock_current_user):
        """セグメントメトリクス計算テスト"""
        segment_id = str(uuid.uuid4())
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CustomerSegmentCRUD") as mock_crud:
            
            response = client.post(f"/api/v1/crm/segments/{segment_id}/calculate")
            
            assert response.status_code == 200
            mock_crud.return_value.calculate_segment_metrics.assert_called_once_with(segment_id)

class TestMarketingCampaignAPI:
    def test_create_marketing_campaign(self, mock_db, mock_current_user):
        """マーケティングキャンペーン作成テスト"""
        campaign_data = MarketingCampaignCreate(
            campaign_code="CAMP2024-001",
            name="春の新製品キャンペーン",
            description="新製品の認知度向上とリード獲得",
            campaign_type="email",
            channel="email",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            budget=Decimal("500000"),
            target_audience="既存顧客および見込み客",
            tags=["春キャンペーン", "新製品", "リード獲得"]
        )
        
        mock_campaign = Mock()
        mock_campaign.id = str(uuid.uuid4())
        mock_campaign.campaign_code = campaign_data.campaign_code
        mock_campaign.name = campaign_data.name
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.MarketingCampaignCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_campaign
            
            response = client.post("/api/v1/crm/campaigns", json=campaign_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(campaign_data, mock_current_user["sub"])

    def test_update_marketing_campaign(self, mock_db, mock_current_user):
        """マーケティングキャンペーン更新テスト"""
        campaign_id = str(uuid.uuid4())
        update_data = MarketingCampaignUpdate(
            status="active",
            impressions=50000,
            clicks=2500,
            leads_generated=125,
            customers_acquired=15,
            revenue_generated=Decimal("3000000")
        )
        
        mock_campaign = Mock()
        mock_campaign.id = campaign_id
        mock_campaign.status = update_data.status
        mock_campaign.impressions = update_data.impressions
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.MarketingCampaignCRUD") as mock_crud:
            
            mock_crud.return_value.update.return_value = mock_campaign
            
            response = client.put(
                f"/api/v1/crm/campaigns/{campaign_id}",
                json=update_data.dict(exclude_unset=True)
            )
            
            assert response.status_code == 200
            mock_crud.return_value.update.assert_called_once()

class TestActivityAPI:
    def test_create_opportunity_activity(self, mock_db, mock_current_user):
        """営業機会活動作成テスト"""
        activity_data = OpportunityActivityCreate(
            opportunity_id=str(uuid.uuid4()),
            activity_type="meeting",
            subject="提案プレゼンテーション",
            description="役員向けソリューション提案",
            outcome="interested",
            outcome_notes="技術的詳細について追加質問あり"
        )
        
        mock_activity = Mock()
        mock_activity.id = str(uuid.uuid4())
        mock_activity.subject = activity_data.subject
        mock_activity.outcome = activity_data.outcome
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.OpportunityActivityCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_activity
            
            response = client.post("/api/v1/crm/activities/opportunities", json=activity_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(activity_data, mock_current_user["sub"])

    def test_create_customer_activity(self, mock_db, mock_current_user):
        """顧客活動記録作成テスト"""
        activity_data = CustomerActivityCreate(
            customer_id=str(uuid.uuid4()),
            activity_type="webpage_visit",
            activity_category="marketing",
            subject="製品ページ閲覧",
            description="新製品の詳細ページを30分間閲覧",
            page_url="https://example.com/products/new-system",
            source="google_ads",
            custom_fields={
                "utm_source": "google",
                "utm_campaign": "spring_campaign"
            }
        )
        
        mock_activity = Mock()
        mock_activity.id = str(uuid.uuid4())
        mock_activity.activity_type = activity_data.activity_type
        mock_activity.subject = activity_data.subject
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.CustomerActivityCRUD") as mock_crud:
            
            mock_crud.return_value.create.return_value = mock_activity
            
            response = client.post("/api/v1/crm/activities/customers", json=activity_data.dict())
            
            assert response.status_code == 201
            mock_crud.return_value.create.assert_called_once_with(activity_data, mock_current_user["sub"])

class TestAnalyticsAPI:
    def test_get_pipeline_analytics(self, mock_db, mock_current_user):
        """パイプライン分析データ取得テスト"""
        mock_analytics = {
            "total_opportunities": 50,
            "total_pipeline_value": Decimal("25000000"),
            "weighted_pipeline_value": Decimal("18750000"),
            "avg_deal_size": Decimal("500000"),
            "stage_breakdown": {
                "prospecting": {"count": 15, "value": Decimal("7500000"), "weighted_value": Decimal("3750000")},
                "qualification": {"count": 20, "value": Decimal("10000000"), "weighted_value": Decimal("7500000")},
                "proposal": {"count": 10, "value": Decimal("5000000"), "weighted_value": Decimal("4000000")},
                "negotiation": {"count": 5, "value": Decimal("2500000"), "weighted_value": Decimal("2250000")}
            }
        }
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user), \
             patch("app.api.v1.crm_complete_v30.SalesOpportunityCRUD") as mock_crud:
            
            mock_crud.return_value.get_pipeline_analytics.return_value = mock_analytics
            
            response = client.get("/api/v1/crm/pipeline/analytics")
            
            assert response.status_code == 200
            mock_crud.return_value.get_pipeline_analytics.assert_called_once()

    def test_get_crm_stats(self, mock_db, mock_current_user):
        """CRM統計取得テスト"""
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user):
            
            mock_db.query.return_value.count.return_value = 100
            mock_db.query.return_value.filter.return_value.count.return_value = 80
            mock_db.query.return_value.with_entities.return_value.scalar.return_value = Decimal("50000000")
            mock_db.query.return_value.group_by.return_value.all.return_value = [("prospecting", 25), ("qualification", 30)]
            mock_db.query.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/crm/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_customers" in data
            assert "total_opportunities" in data
            assert "total_pipeline_value" in data

    def test_get_crm_analytics(self, mock_db, mock_current_user):
        """CRM分析データ取得テスト"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()
        
        with patch("app.api.v1.crm_complete_v30.get_db", return_value=mock_db), \
             patch("app.api.v1.crm_complete_v30.get_current_user", return_value=mock_current_user):
            
            mock_db.query.return_value.filter.return_value.count.return_value = 25
            mock_db.query.return_value.filter.return_value.with_entities.return_value.scalar.return_value = Decimal("5000000")
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.query.return_value.group_by.return_value.all.return_value = []
            
            response = client.get(
                f"/api/v1/crm/analytics?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "new_customers" in data
            assert "opportunities_created" in data
            assert "revenue_generated" in data