"""
予算管理サービスのユニットテスト
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from app.services.financial.budget_service import BudgetService
from app.models.financial.budget import Budget, BudgetAllocation, BudgetConsumption
from app.schemas.financial.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetAllocationCreate,
    BudgetConsumptionResponse,
)
from app.core.exceptions import BusinessLogicError, NotFoundError


class TestBudgetService:
    """予算管理サービスのテストクラス"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return Mock()

    @pytest.fixture
    def budget_service(self, mock_db):
        """テスト用の予算サービスインスタンス"""
        return BudgetService(mock_db)

    @pytest.fixture
    def sample_budget_data(self):
        """サンプル予算データ"""
        return BudgetCreate(
            budget_code="BUD-2024-001",
            budget_name="2024年度営業部予算",
            fiscal_year=2024,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            budget_type="annual",
            department_id=1,
            revenue_budget=Decimal("100000000"),
            cost_budget=Decimal("60000000"),
            expense_budget=Decimal("30000000"),
        )

    @pytest.fixture
    def sample_budget(self):
        """サンプル予算エンティティ"""
        budget = Budget(
            id=1,
            budget_code="BUD-2024-001",
            budget_name="2024年度営業部予算",
            fiscal_year=2024,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            budget_type="annual",
            department_id=1,
            revenue_budget=Decimal("100000000"),
            cost_budget=Decimal("60000000"),
            expense_budget=Decimal("30000000"),
            total_budget=Decimal("10000000"),
            status="approved",
            created_by=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return budget

    def test_create_budget_success(self, budget_service, mock_db, sample_budget_data):
        """予算作成の正常系テスト"""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        user_id = 1
        organization_id = 1

        # Act
        result = budget_service.create_budget(
            budget_data=sample_budget_data,
            user_id=user_id,
            organization_id=organization_id
        )

        # Assert
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        
        # 作成された予算オブジェクトの検証
        added_budget = mock_db.add.call_args[0][0]
        assert added_budget.budget_code == sample_budget_data.budget_code
        assert added_budget.budget_name == sample_budget_data.budget_name
        assert added_budget.fiscal_year == sample_budget_data.fiscal_year
        assert added_budget.created_by == user_id

    def test_create_budget_with_parent_hierarchy_check(self, budget_service, mock_db):
        """親予算の階層チェックテスト"""
        # Arrange
        parent_budget = Mock()
        parent_budget.id = 1
        parent_budget.parent_budget_id = None
        
        mock_db.query().filter().first.return_value = parent_budget
        
        budget_data = BudgetCreate(
            budget_code="BUD-2024-002",
            budget_name="営業1課予算",
            fiscal_year=2024,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            budget_type="annual",
            department_id=2,
            parent_budget_id=1,
            expense_budget=Decimal("10000000"),
        )

        # Act
        with patch.object(budget_service, 'get_budget_hierarchy_depth', return_value=3):
            result = budget_service.create_budget(budget_data, 1, 1)

        # Assert
        assert mock_db.add.called

    def test_create_budget_hierarchy_limit_exceeded(self, budget_service, mock_db):
        """予算階層制限超過のテスト"""
        # Arrange
        budget_data = BudgetCreate(
            budget_code="BUD-2024-003",
            budget_name="深い階層の予算",
            fiscal_year=2024,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            budget_type="annual",
            department_id=3,
            parent_budget_id=5,
            expense_budget=Decimal("5000000"),
        )

        # Act & Assert
        with patch.object(budget_service, 'get_budget_hierarchy_depth', return_value=5):
            with pytest.raises(BusinessLogicError) as exc_info:
                budget_service.create_budget(budget_data, 1, 1)
            
            assert "予算階層は最大5レベルまで" in str(exc_info.value)

    def test_get_budget_success(self, budget_service, mock_db, sample_budget):
        """予算取得の正常系テスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_budget

        # Act
        result = budget_service.get_budget(1)

        # Assert
        assert result == sample_budget
        assert result.id == 1
        assert result.budget_code == "BUD-2024-001"

    def test_get_budget_not_found(self, budget_service, mock_db):
        """存在しない予算取得のテスト"""
        # Arrange
        mock_db.query().filter().first.return_value = None

        # Act
        result = budget_service.get_budget(999)

        # Assert
        assert result is None

    def test_update_budget_success(self, budget_service, mock_db, sample_budget):
        """予算更新の正常系テスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_budget
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        update_data = BudgetUpdate(
            budget_name="2024年度営業部予算（改定）",
            expense_budget=Decimal("35000000"),
        )

        # Act
        result = budget_service.update_budget(1, update_data)

        # Assert
        assert mock_db.commit.called
        assert sample_budget.budget_name == "2024年度営業部予算（改定）"
        assert sample_budget.expense_budget == Decimal("35000000")

    def test_allocate_budget_success(self, budget_service, mock_db, sample_budget):
        """予算配分の正常系テスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_budget
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        allocations = [
            BudgetAllocationCreate(
                account_code="6001",
                allocated_amount=Decimal("15000000"),
                allocation_percentage=Decimal("50.0"),
            ),
            BudgetAllocationCreate(
                account_code="6002",
                allocated_amount=Decimal("10000000"),
                allocation_percentage=Decimal("33.3"),
            ),
            BudgetAllocationCreate(
                account_code="6003",
                allocated_amount=Decimal("5000000"),
                allocation_percentage=Decimal("16.7"),
            ),
        ]

        # Act
        result = budget_service.allocate_budget(1, allocations)

        # Assert
        assert mock_db.add.call_count == 3
        assert mock_db.commit.called
        assert result["total_allocated"] == Decimal("30000000")
        assert len(result["allocations"]) == 3

    def test_allocate_budget_exceeds_total(self, budget_service, mock_db, sample_budget):
        """予算配分が総額を超過するテスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_budget
        
        allocations = [
            BudgetAllocationCreate(
                account_code="6001",
                allocated_amount=Decimal("40000000"),  # 経費予算30Mを超過
            ),
        ]

        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            budget_service.allocate_budget(1, allocations)
        
        assert "配分額が予算総額を超過" in str(exc_info.value)

    def test_get_budget_consumption_success(self, budget_service, mock_db, sample_budget):
        """予算消化状況取得の正常系テスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_budget
        
        # 配分データのモック
        allocations = [
            Mock(
                id=1,
                account_code="6001",
                allocated_amount=Decimal("15000000"),
                consumptions=[
                    Mock(amount=Decimal("3000000")),
                    Mock(amount=Decimal("2000000")),
                ]
            ),
            Mock(
                id=2,
                account_code="6002",
                allocated_amount=Decimal("10000000"),
                consumptions=[
                    Mock(amount=Decimal("1500000")),
                ]
            ),
        ]
        
        mock_db.query().filter().all.return_value = allocations

        # Act
        result = budget_service.get_budget_consumption(1, as_of_date=date(2024, 7, 31))

        # Assert
        assert result.budget_id == 1
        assert result.total_budget == sample_budget.expense_budget
        assert result.consumed_amount == Decimal("6500000")  # 5M + 1.5M
        assert result.remaining_amount == Decimal("23500000")  # 30M - 6.5M
        assert result.consumption_rate == pytest.approx(21.67, 0.01)

    def test_check_budget_alert_threshold_exceeded(self, budget_service, mock_db):
        """予算アラート閾値超過のテスト"""
        # Arrange
        allocation = Mock(
            id=1,
            budget_id=1,
            account_code="6001",
            allocated_amount=Decimal("10000000"),
        )
        
        consumption_rate = Decimal("85.0")  # 85%消化
        
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        alert = budget_service.check_budget_alert(allocation, consumption_rate)

        # Assert
        assert mock_db.add.called
        added_alert = mock_db.add.call_args[0][0]
        assert added_alert.alert_type == "threshold_80"
        assert added_alert.threshold_percentage == 80
        assert added_alert.actual_percentage == 85

    def test_calculate_forecast_linear(self, budget_service):
        """線形予測計算のテスト"""
        # Arrange
        budget_start = date(2024, 4, 1)
        budget_end = date(2025, 3, 31)
        current_date = date(2024, 7, 31)
        consumed_amount = Decimal("10000000")
        total_budget = Decimal("30000000")

        # Act
        forecast = budget_service.calculate_forecast(
            budget_start,
            budget_end,
            current_date,
            consumed_amount,
            total_budget
        )

        # Assert
        # 4ヶ月で10M消化 → 年間30M予測
        assert forecast == Decimal("30000000")

    def test_list_budgets_with_filters(self, budget_service, mock_db):
        """予算一覧取得（フィルタ付き）のテスト"""
        # Arrange
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.all.return_value = [Mock() for _ in range(5)]

        # Act
        result, total = budget_service.list_budgets(
            organization_id=1,
            fiscal_year=2024,
            department_id=1,
            status="approved",
            skip=0,
            limit=20
        )

        # Assert
        assert len(result) == 5
        assert total == 5
        assert mock_query.filter.called

    def test_approve_budget_success(self, budget_service, mock_db, sample_budget):
        """予算承認の正常系テスト"""
        # Arrange
        sample_budget.status = "pending"
        mock_db.query().filter().first.return_value = sample_budget
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        result = budget_service.approve_budget(
            budget_id=1,
            approver_id=2,
            comment="承認します"
        )

        # Assert
        assert sample_budget.status == "approved"
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_reject_budget_success(self, budget_service, mock_db, sample_budget):
        """予算却下の正常系テスト"""
        # Arrange
        sample_budget.status = "pending"
        mock_db.query().filter().first.return_value = sample_budget
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        result = budget_service.reject_budget(
            budget_id=1,
            approver_id=2,
            comment="修正が必要です"
        )

        # Assert
        assert sample_budget.status == "rejected"
        assert mock_db.add.called
        assert mock_db.commit.called