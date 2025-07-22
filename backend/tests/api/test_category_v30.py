import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal
import uuid

from app.main import app
from app.core.database import get_db
from app.core.auth import get_current_user

# Mock database and auth dependencies
def override_get_db():
    return Mock(spec=Session)

def override_get_current_user():
    return {"sub": "test-user-123", "username": "testuser"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


class TestCategoryAPI:
    """カテゴリ管理APIのテスト"""

    @pytest.fixture
    def sample_category_data(self):
        return {
            "category_code": "ELECTRONICS",
            "category_name": "電子機器",
            "category_name_en": "Electronics",
            "description": "電子機器カテゴリ",
            "category_type": "product",
            "industry_vertical": "technology",
            "business_unit": "consumer",
            "display_name": "エレクトロニクス",
            "display_order": 1,
            "sort_order": 1,
            "tax_category": "standard",
            "measurement_unit": "pcs",
            "allow_sales": True,
            "allow_purchase": True,
            "allow_inventory": True,
            "default_income_account": "4000-001",
            "suggested_markup_percentage": 25.0,
            "standard_cost_method": "average",
            "safety_stock_percentage": 10.0,
            "abc_analysis_class": "A",
            "seasonality_pattern": "none",
            "demand_pattern": "stable",
            "lifecycle_stage": "growth",
            "profitability_rating": "high",
            "approval_required": False,
            "attributes": {"brand_required": True},
            "tags": ["electronics", "consumer"],
            "custom_fields": {"warranty_period": "12 months"},
            "seo_title": "電子機器・エレクトロニクス",
            "seo_description": "最新の電子機器を豊富に取り揃え",
            "url_slug": "electronics",
            "low_stock_alert_enabled": True
        }

    @pytest.fixture
    def sample_category_response(self):
        return {
            "id": "cat-123",
            "parent_id": None,
            "category_code": "ELECTRONICS",
            "category_name": "電子機器",
            "category_name_en": "Electronics",
            "description": "電子機器カテゴリ",
            "level": 1,
            "sort_order": 1,
            "path": "電子機器",
            "path_ids": "",
            "category_type": "product",
            "industry_vertical": "technology",
            "business_unit": "consumer",
            "is_active": True,
            "is_leaf": True,
            "display_name": "エレクトロニクス",
            "display_order": 1,
            "tax_category": "standard",
            "measurement_unit": "pcs",
            "weight_unit": None,
            "dimension_unit": None,
            "allow_sales": True,
            "allow_purchase": True,
            "allow_inventory": True,
            "requires_serial_number": False,
            "requires_lot_tracking": False,
            "requires_expiry_tracking": False,
            "quality_control_required": False,
            "default_income_account": "4000-001",
            "default_expense_account": None,
            "default_asset_account": None,
            "suggested_markup_percentage": 25.0,
            "standard_cost_method": "average",
            "valuation_method": None,
            "safety_stock_percentage": 10.0,
            "abc_analysis_class": "A",
            "vendor_managed_inventory": False,
            "seasonality_pattern": "none",
            "demand_pattern": "stable",
            "lifecycle_stage": "growth",
            "profitability_rating": "high",
            "approval_required": False,
            "approved_by": None,
            "approved_at": None,
            "approval_status": "approved",
            "attributes": {"brand_required": True},
            "tags": ["electronics", "consumer"],
            "custom_fields": {"warranty_period": "12 months"},
            "translations": {},
            "product_count": 0,
            "total_sales_amount": 0.0,
            "avg_margin_percentage": None,
            "last_activity_date": None,
            "seo_title": "電子機器・エレクトロニクス",
            "seo_description": "最新の電子機器を豊富に取り揃え",
            "seo_keywords": None,
            "url_slug": "electronics",
            "low_stock_alert_enabled": True,
            "price_change_alert_enabled": False,
            "new_product_alert_enabled": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None,
            "created_by": "test-user-123",
            "updated_by": None
        }

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_create_category_success(self, mock_crud_class, sample_category_data, sample_category_response):
        """カテゴリ作成成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.create.return_value = Mock(**sample_category_response)

        response = client.post("/categories/", json=sample_category_data)

        assert response.status_code == 201
        mock_crud.create.assert_called_once()
        
        data = response.json()
        assert data["category_code"] == sample_category_data["category_code"]
        assert data["category_name"] == sample_category_data["category_name"]
        assert data["category_type"] == sample_category_data["category_type"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_create_category_duplicate_error(self, mock_crud_class, sample_category_data):
        """カテゴリ作成重複エラーテスト"""
        from app.crud.category_v30 import DuplicateError
        mock_crud = mock_crud_class.return_value
        mock_crud.create.side_effect = DuplicateError("Category code already exists")

        response = client.post("/categories/", json=sample_category_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_success(self, mock_crud_class, sample_category_response):
        """カテゴリ詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_category_response)

        category_id = "cat-123"
        response = client.get(f"/categories/{category_id}")

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(category_id)
        
        data = response.json()
        assert data["id"] == category_id
        assert data["category_name"] == sample_category_response["category_name"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_not_found(self, mock_crud_class):
        """カテゴリ詳細取得未発見テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = None

        category_id = "nonexistent-cat"
        response = client.get(f"/categories/{category_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_list_categories_success(self, mock_crud_class, sample_category_response):
        """カテゴリ一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_categories = [Mock(**sample_category_response)]
        mock_crud.get_multi.return_value = (mock_categories, 1)

        response = client.get("/categories/")

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()
        
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert len(data["items"]) == 1

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_list_categories_with_filters(self, mock_crud_class, sample_category_response):
        """フィルター付きカテゴリ一覧取得テスト"""
        mock_crud = mock_crud_class.return_value
        mock_categories = [Mock(**sample_category_response)]
        mock_crud.get_multi.return_value = (mock_categories, 1)

        params = {
            "category_type": "product",
            "is_active": True,
            "level": 1,
            "industry_vertical": "technology",
            "search": "electronics",
            "page": 1,
            "per_page": 10
        }
        response = client.get("/categories/", params=params)

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()
        
        # Check that filters were passed to the CRUD method
        call_args = mock_crud.get_multi.call_args
        filters = call_args.kwargs['filters']
        assert filters["category_type"] == "product"
        assert filters["is_active"] is True
        assert filters["level"] == 1

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_update_category_success(self, mock_crud_class, sample_category_response):
        """カテゴリ更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_category_response.copy()
        updated_response["category_name"] = "更新された電子機器"
        mock_crud.update.return_value = Mock(**updated_response)

        category_id = "cat-123"
        update_data = {"category_name": "更新された電子機器", "description": "更新された説明"}
        response = client.put(f"/categories/{category_id}", json=update_data)

        assert response.status_code == 200
        mock_crud.update.assert_called_once()
        
        data = response.json()
        assert data["category_name"] == "更新された電子機器"

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_activate_category_success(self, mock_crud_class, sample_category_response):
        """カテゴリアクティブ化成功テスト"""
        mock_crud = mock_crud_class.return_value
        activated_response = sample_category_response.copy()
        activated_response["is_active"] = True
        mock_crud.activate.return_value = Mock(**activated_response)

        category_id = "cat-123"
        response = client.post(f"/categories/{category_id}/activate")

        assert response.status_code == 200
        mock_crud.activate.assert_called_once_with(category_id, "test-user-123")
        
        data = response.json()
        assert data["is_active"] is True

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_deactivate_category_success(self, mock_crud_class, sample_category_response):
        """カテゴリ非アクティブ化成功テスト"""
        mock_crud = mock_crud_class.return_value
        deactivated_response = sample_category_response.copy()
        deactivated_response["is_active"] = False
        mock_crud.deactivate.return_value = Mock(**deactivated_response)

        category_id = "cat-123"
        response = client.post(f"/categories/{category_id}/deactivate")

        assert response.status_code == 200
        mock_crud.deactivate.assert_called_once_with(category_id, "test-user-123")
        
        data = response.json()
        assert data["is_active"] is False

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_move_category_success(self, mock_crud_class, sample_category_response):
        """カテゴリ移動成功テスト"""
        mock_crud = mock_crud_class.return_value
        moved_response = sample_category_response.copy()
        moved_response["parent_id"] = "parent-456"
        moved_response["level"] = 2
        mock_crud.move_category.return_value = Mock(**moved_response)

        category_id = "cat-123"
        move_data = {"category_id": category_id, "new_parent_id": "parent-456"}
        response = client.post(f"/categories/{category_id}/move", json=move_data)

        assert response.status_code == 200
        mock_crud.move_category.assert_called_once_with("cat-123", "parent-456", "test-user-123")
        
        data = response.json()
        assert data["parent_id"] == "parent-456"
        assert data["level"] == 2

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_delete_category_success(self, mock_crud_class):
        """カテゴリ削除成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.delete.return_value = True

        category_id = "cat-123"
        response = client.delete(f"/categories/{category_id}")

        assert response.status_code == 200
        mock_crud.delete.assert_called_once_with(category_id, "test-user-123")
        
        data = response.json()
        assert "successfully" in data["message"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_children_success(self, mock_crud_class, sample_category_response):
        """子カテゴリ取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        # 親カテゴリの存在確認
        mock_crud.get_by_id.return_value = Mock(**sample_category_response)
        # 子カテゴリ取得
        child_response = sample_category_response.copy()
        child_response["id"] = "child-456"
        child_response["parent_id"] = "cat-123"
        child_response["level"] = 2
        mock_crud.get_by_parent.return_value = [Mock(**child_response)]

        parent_id = "cat-123"
        response = client.get(f"/categories/{parent_id}/children")

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(parent_id)
        mock_crud.get_by_parent.assert_called_once_with(parent_id)
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "child-456"
        assert data[0]["parent_id"] == parent_id

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_descendants_success(self, mock_crud_class, sample_category_response):
        """子孫カテゴリ取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        descendant_response = sample_category_response.copy()
        descendant_response["id"] = "descendant-789"
        descendant_response["parent_id"] = "cat-123"
        descendant_response["level"] = 3
        mock_crud.get_descendants.return_value = [Mock(**descendant_response)]

        category_id = "cat-123"
        response = client.get(f"/categories/{category_id}/descendants")

        assert response.status_code == 200
        mock_crud.get_descendants.assert_called_once_with(category_id, False)
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "descendant-789"

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_hierarchy_path_success(self, mock_crud_class, sample_category_response):
        """カテゴリ階層パス取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        # ルートから現在までのパス
        root_response = sample_category_response.copy()
        root_response["id"] = "root-000"
        root_response["level"] = 1
        current_response = sample_category_response.copy()
        current_response["id"] = "cat-123"
        current_response["parent_id"] = "root-000"
        current_response["level"] = 2
        mock_crud.get_hierarchy_path.return_value = [Mock(**root_response), Mock(**current_response)]

        category_id = "cat-123"
        response = client.get(f"/categories/{category_id}/hierarchy-path")

        assert response.status_code == 200
        mock_crud.get_hierarchy_path.assert_called_once_with(category_id)
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "root-000"
        assert data[1]["id"] == "cat-123"

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_by_code_success(self, mock_crud_class, sample_category_response):
        """カテゴリコード検索成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_code.return_value = Mock(**sample_category_response)

        category_code = "ELECTRONICS"
        response = client.get(f"/categories/by-code/{category_code}")

        assert response.status_code == 200
        mock_crud.get_by_code.assert_called_once_with(category_code)
        
        data = response.json()
        assert data["category_code"] == category_code


class TestCategoryAttributeAPI:
    """カテゴリ属性APIのテスト"""

    @pytest.fixture
    def sample_attribute_data(self):
        return {
            "attribute_name": "ブランド",
            "attribute_name_en": "Brand",
            "attribute_code": "brand",
            "display_name": "ブランド名",
            "data_type": "select",
            "is_required": True,
            "is_searchable": True,
            "is_filterable": True,
            "display_order": 1,
            "group_name": "基本情報",
            "help_text": "商品のブランド名を選択してください",
            "option_values": [
                {"value": "apple", "label": "Apple", "label_en": "Apple"},
                {"value": "samsung", "label": "Samsung", "label_en": "Samsung"}
            ],
            "validation_rules": {"required": True},
            "translations": {
                "ja": {"name": "ブランド", "help": "ブランドを選択"},
                "en": {"name": "Brand", "help": "Select brand"}
            }
        }

    @pytest.fixture
    def sample_attribute_response(self):
        return {
            "id": "attr-123",
            "category_id": "cat-123",
            "attribute_name": "ブランド",
            "attribute_name_en": "Brand",
            "attribute_code": "brand",
            "display_name": "ブランド名",
            "data_type": "select",
            "is_required": True,
            "is_unique": False,
            "is_searchable": True,
            "is_filterable": True,
            "is_visible_in_list": True,
            "display_order": 1,
            "group_name": "基本情報",
            "help_text": "商品のブランド名を選択してください",
            "placeholder_text": None,
            "min_value": None,
            "max_value": None,
            "min_length": None,
            "max_length": None,
            "regex_pattern": None,
            "default_value": None,
            "option_values": [
                {"value": "apple", "label": "Apple", "label_en": "Apple"},
                {"value": "samsung", "label": "Samsung", "label_en": "Samsung"}
            ],
            "unit": None,
            "unit_type": None,
            "validation_rules": {"required": True},
            "business_rules": {},
            "translations": {
                "ja": {"name": "ブランド", "help": "ブランドを選択"},
                "en": {"name": "Brand", "help": "Select brand"}
            },
            "inherit_from_parent": False,
            "shared_across_categories": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None,
            "created_by": "test-user-123"
        }

    @patch('app.api.v1.category_v30.CategoryCRUD')
    @patch('app.api.v1.category_v30.CategoryAttributeCRUD')
    def test_create_category_attribute_success(self, mock_attr_crud_class, mock_cat_crud_class, 
                                              sample_attribute_data, sample_attribute_response):
        """カテゴリ属性作成成功テスト"""
        # カテゴリ存在確認
        mock_cat_crud = mock_cat_crud_class.return_value
        mock_cat_crud.get_by_id.return_value = Mock(id="cat-123")
        
        # 属性作成
        mock_attr_crud = mock_attr_crud_class.return_value
        mock_attr_crud.create.return_value = Mock(**sample_attribute_response)

        category_id = "cat-123"
        response = client.post(f"/categories/{category_id}/attributes", json=sample_attribute_data)

        assert response.status_code == 201
        mock_cat_crud.get_by_id.assert_called_once_with(category_id)
        mock_attr_crud.create.assert_called_once()
        
        data = response.json()
        assert data["attribute_name"] == sample_attribute_data["attribute_name"]
        assert data["attribute_code"] == sample_attribute_data["attribute_code"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    @patch('app.api.v1.category_v30.CategoryAttributeCRUD')
    def test_list_category_attributes_success(self, mock_attr_crud_class, mock_cat_crud_class, 
                                            sample_attribute_response):
        """カテゴリ属性一覧取得成功テスト"""
        # カテゴリ存在確認
        mock_cat_crud = mock_cat_crud_class.return_value
        mock_cat_crud.get_by_id.return_value = Mock(id="cat-123")
        
        # 属性一覧取得
        mock_attr_crud = mock_attr_crud_class.return_value
        mock_attr_crud.get_by_category.return_value = [Mock(**sample_attribute_response)]

        category_id = "cat-123"
        response = client.get(f"/categories/{category_id}/attributes")

        assert response.status_code == 200
        mock_cat_crud.get_by_id.assert_called_once_with(category_id)
        mock_attr_crud.get_by_category.assert_called_once_with(category_id)
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "attr-123"

    @patch('app.api.v1.category_v30.CategoryAttributeCRUD')
    def test_get_category_attribute_success(self, mock_crud_class, sample_attribute_response):
        """カテゴリ属性詳細取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.get_by_id.return_value = Mock(**sample_attribute_response)

        attribute_id = "attr-123"
        response = client.get(f"/categories/attributes/{attribute_id}")

        assert response.status_code == 200
        mock_crud.get_by_id.assert_called_once_with(attribute_id)
        
        data = response.json()
        assert data["id"] == attribute_id

    @patch('app.api.v1.category_v30.CategoryAttributeCRUD')
    def test_update_category_attribute_success(self, mock_crud_class, sample_attribute_response):
        """カテゴリ属性更新成功テスト"""
        mock_crud = mock_crud_class.return_value
        updated_response = sample_attribute_response.copy()
        updated_response["attribute_name"] = "更新されたブランド"
        mock_crud.update.return_value = Mock(**updated_response)

        attribute_id = "attr-123"
        update_data = {"attribute_name": "更新されたブランド", "help_text": "更新されたヘルプ"}
        response = client.put(f"/categories/attributes/{attribute_id}", json=update_data)

        assert response.status_code == 200
        mock_crud.update.assert_called_once()
        
        data = response.json()
        assert data["attribute_name"] == "更新されたブランド"

    @patch('app.api.v1.category_v30.CategoryAttributeCRUD')
    def test_delete_category_attribute_success(self, mock_crud_class):
        """カテゴリ属性削除成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.delete.return_value = True

        attribute_id = "attr-123"
        response = client.delete(f"/categories/attributes/{attribute_id}")

        assert response.status_code == 200
        mock_crud.delete.assert_called_once_with(attribute_id)
        
        data = response.json()
        assert "successfully" in data["message"]


class TestCategoryPricingRuleAPI:
    """カテゴリ価格ルールAPIのテスト"""

    @pytest.fixture
    def sample_pricing_rule_data(self):
        return {
            "rule_name": "エレクトロニクス標準マークアップ",
            "rule_code": "ELEC_MARKUP_STD",
            "description": "エレクトロニクス製品の標準マークアップルール",
            "rule_type": "markup",
            "priority": 10,
            "is_active": True,
            "effective_date": "2024-01-01T00:00:00",
            "expiry_date": "2024-12-31T23:59:59",
            "customer_segments": ["retail", "wholesale"],
            "minimum_quantity": 1.0,
            "maximum_quantity": 1000.0,
            "minimum_amount": 100.0,
            "markup_percentage": 25.0,
            "currency": "JPY",
            "region_codes": ["JP", "APAC"],
            "market_position": "standard",
            "approval_required": False
        }

    @pytest.fixture
    def sample_pricing_rule_response(self):
        return {
            "id": "rule-123",
            "category_id": "cat-123",
            "rule_name": "エレクトロニクス標準マークアップ",
            "rule_code": "ELEC_MARKUP_STD",
            "description": "エレクトロニクス製品の標準マークアップルール",
            "rule_type": "markup",
            "priority": 10,
            "is_active": True,
            "effective_date": "2024-01-01T00:00:00",
            "expiry_date": "2024-12-31T23:59:59",
            "customer_segments": ["retail", "wholesale"],
            "minimum_quantity": 1.0,
            "maximum_quantity": 1000.0,
            "minimum_amount": 100.0,
            "markup_percentage": 25.0,
            "discount_percentage": None,
            "fixed_amount": None,
            "cost_multiplier": None,
            "price_tiers": [],
            "volume_discounts": [],
            "currency": "JPY",
            "region_codes": ["JP", "APAC"],
            "exchange_rate_factor": None,
            "competitor_price_factor": None,
            "market_position": "standard",
            "price_elasticity": None,
            "approval_required": False,
            "approved_by": None,
            "approved_at": None,
            "usage_count": 0,
            "last_applied_date": None,
            "effectiveness_rating": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None,
            "created_by": "test-user-123"
        }

    @patch('app.api.v1.category_v30.CategoryCRUD')
    @patch('app.api.v1.category_v30.CategoryPricingRuleCRUD')
    def test_create_pricing_rule_success(self, mock_rule_crud_class, mock_cat_crud_class, 
                                        sample_pricing_rule_data, sample_pricing_rule_response):
        """価格ルール作成成功テスト"""
        # カテゴリ存在確認
        mock_cat_crud = mock_cat_crud_class.return_value
        mock_cat_crud.get_by_id.return_value = Mock(id="cat-123")
        
        # ルール作成
        mock_rule_crud = mock_rule_crud_class.return_value
        mock_rule_crud.create.return_value = Mock(**sample_pricing_rule_response)

        category_id = "cat-123"
        response = client.post(f"/categories/{category_id}/pricing-rules", json=sample_pricing_rule_data)

        assert response.status_code == 201
        mock_cat_crud.get_by_id.assert_called_once_with(category_id)
        mock_rule_crud.create.assert_called_once()
        
        data = response.json()
        assert data["rule_name"] == sample_pricing_rule_data["rule_name"]
        assert data["rule_type"] == sample_pricing_rule_data["rule_type"]

    @patch('app.api.v1.category_v30.CategoryCRUD')
    @patch('app.api.v1.category_v30.CategoryPricingRuleCRUD')
    def test_list_category_pricing_rules_success(self, mock_rule_crud_class, mock_cat_crud_class, 
                                                sample_pricing_rule_response):
        """カテゴリ価格ルール一覧取得成功テスト"""
        # カテゴリ存在確認
        mock_cat_crud = mock_cat_crud_class.return_value
        mock_cat_crud.get_by_id.return_value = Mock(id="cat-123")
        
        # ルール一覧取得
        mock_rule_crud = mock_rule_crud_class.return_value
        mock_rule_crud.get_by_category.return_value = [Mock(**sample_pricing_rule_response)]

        category_id = "cat-123"
        response = client.get(f"/categories/{category_id}/pricing-rules")

        assert response.status_code == 200
        mock_cat_crud.get_by_id.assert_called_once_with(category_id)
        mock_rule_crud.get_by_category.assert_called_once_with(category_id, True)
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "rule-123"

    @patch('app.api.v1.category_v30.CategoryPricingRuleCRUD')
    def test_list_all_pricing_rules_success(self, mock_crud_class, sample_pricing_rule_response):
        """全価格ルール一覧取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_rules = [Mock(**sample_pricing_rule_response)]
        mock_crud.get_multi.return_value = (mock_rules, 1)

        response = client.get("/categories/pricing-rules")

        assert response.status_code == 200
        mock_crud.get_multi.assert_called_once()
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch('app.api.v1.category_v30.CategoryPricingRuleCRUD')
    def test_activate_pricing_rule_success(self, mock_crud_class, sample_pricing_rule_response):
        """価格ルールアクティブ化成功テスト"""
        mock_crud = mock_crud_class.return_value
        activated_response = sample_pricing_rule_response.copy()
        activated_response["is_active"] = True
        mock_crud.activate.return_value = Mock(**activated_response)

        rule_id = "rule-123"
        response = client.post(f"/categories/pricing-rules/{rule_id}/activate")

        assert response.status_code == 200
        mock_crud.activate.assert_called_once_with(rule_id)
        
        data = response.json()
        assert data["is_active"] is True


class TestCategoryAnalyticsAPI:
    """カテゴリ分析APIのテスト"""

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_analytics_success(self, mock_crud_class):
        """カテゴリ分析データ取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_analytics = {
            "total_categories": 150,
            "active_categories": 120,
            "inactive_categories": 30,
            "leaf_categories": 80,
            "avg_hierarchy_depth": 2.5,
            "max_hierarchy_depth": 5,
            "categories_by_type": {
                "product": 100,
                "service": 30,
                "expense": 20
            },
            "categories_by_level": {
                1: 20,
                2: 50,
                3: 60,
                4: 20
            },
            "top_categories_by_product_count": [
                {"id": "cat-1", "name": "Electronics", "product_count": 150, "level": 1}
            ],
            "top_categories_by_sales": [
                {"id": "cat-1", "name": "Electronics", "total_sales": 5000000.0, "margin_percentage": 25.0}
            ],
            "categories_needing_attention": [
                {"id": "cat-2", "name": "Old Category", "issues": ["no_recent_activity"], "product_count": 0}
            ],
            "taxonomy_completeness": {
                "categories_with_description": 100,
                "categories_with_attributes": 80,
                "categories_with_seo": 60,
                "categories_with_translations": 40
            }
        }
        mock_crud.get_analytics.return_value = mock_analytics

        response = client.get("/categories/analytics")

        assert response.status_code == 200
        mock_crud.get_analytics.assert_called_once()
        
        data = response.json()
        assert data["total_categories"] == 150
        assert data["active_categories"] == 120
        assert data["avg_hierarchy_depth"] == 2.5

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_get_category_tree_success(self, mock_crud_class):
        """カテゴリツリー構造取得成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_tree = [
            {
                "id": "cat-1",
                "category_code": "ELECTRONICS",
                "category_name": "Electronics",
                "level": 1,
                "is_active": True,
                "is_leaf": False,
                "product_count": 0,
                "children": [
                    {
                        "id": "cat-2",
                        "category_code": "SMARTPHONES",
                        "category_name": "Smartphones",
                        "level": 2,
                        "is_active": True,
                        "is_leaf": True,
                        "product_count": 25,
                        "children": []
                    }
                ]
            }
        ]
        mock_crud.get_tree_structure.return_value = mock_tree

        response = client.get("/categories/tree")

        assert response.status_code == 200
        mock_crud.get_tree_structure.assert_called_once_with(None, False)
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "cat-1"
        assert len(data[0]["children"]) == 1


class TestCategoryValidation:
    """カテゴリAPIバリデーションテスト"""

    def test_create_category_invalid_data(self):
        """カテゴリ作成無効データテスト"""
        invalid_data = {
            "category_code": "",  # Empty code
            "category_name": "",  # Empty name
            "category_type": "invalid_type",  # Invalid enum
            "suggested_markup_percentage": -10.0,  # Negative percentage
            "display_order": -1  # Negative order
        }

        response = client.post("/categories/", json=invalid_data)

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0

    def test_create_category_invalid_code_format(self):
        """カテゴリコード形式無効テスト"""
        invalid_data = {
            "category_code": "invalid-code!",  # Contains invalid characters
            "category_name": "Valid Name",
            "category_type": "product"
        }

        response = client.post("/categories/", json=invalid_data)

        assert response.status_code == 422

    def test_create_attribute_invalid_data(self):
        """属性作成無効データテスト"""
        invalid_data = {
            "attribute_name": "",  # Empty name
            "attribute_code": "",  # Empty code
            "data_type": "invalid_type",  # Invalid enum
            "min_length": 10,
            "max_length": 5  # max_length < min_length
        }

        response = client.post("/categories/cat-123/attributes", json=invalid_data)

        assert response.status_code == 422

    def test_create_pricing_rule_invalid_dates(self):
        """価格ルール無効日付テスト"""
        invalid_data = {
            "rule_name": "Test Rule",
            "rule_type": "markup",
            "effective_date": "2024-12-01T00:00:00",
            "expiry_date": "2024-01-01T00:00:00",  # Earlier than effective_date
            "markup_percentage": 150.0  # Over 100% is valid for markup
        }

        response = client.post("/categories/cat-123/pricing-rules", json=invalid_data)

        assert response.status_code == 422

    def test_list_categories_invalid_pagination(self):
        """カテゴリ一覧無効ページネーションテスト"""
        params = {
            "page": 0,  # Invalid page (minimum 1)
            "per_page": 150  # Over maximum (100)
        }

        response = client.get("/categories/", params=params)

        assert response.status_code == 422


class TestCategoryBulkOperations:
    """カテゴリ一括操作テスト"""

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_bulk_operations_success(self, mock_crud_class):
        """一括操作成功テスト"""
        mock_crud = mock_crud_class.return_value
        mock_crud.activate.return_value = Mock()

        bulk_data = {
            "category_ids": ["cat-1", "cat-2", "cat-3"],
            "operation": "activate",
            "operation_data": {}
        }

        response = client.post("/categories/bulk-operations", json=bulk_data)

        assert response.status_code == 200
        assert mock_crud.activate.call_count == 3
        
        data = response.json()
        assert "completed" in data["message"]
        assert len(data["results"]["successful"]) == 3
        assert len(data["results"]["failed"]) == 0

    @patch('app.api.v1.category_v30.CategoryCRUD')
    def test_bulk_operations_partial_failure(self, mock_crud_class):
        """一括操作部分失敗テスト"""
        from app.crud.category_v30 import NotFoundError
        
        mock_crud = mock_crud_class.return_value
        mock_crud.activate.side_effect = [Mock(), NotFoundError("Category not found"), Mock()]

        bulk_data = {
            "category_ids": ["cat-1", "cat-2", "cat-3"],
            "operation": "activate"
        }

        response = client.post("/categories/bulk-operations", json=bulk_data)

        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]["successful"]) == 2
        assert len(data["results"]["failed"]) == 1
        assert data["results"]["failed"][0]["category_id"] == "cat-2"