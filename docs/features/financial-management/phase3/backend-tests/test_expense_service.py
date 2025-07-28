"""
経費管理サービスのユニットテスト
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException

from app.services.financial.expense_service import ExpenseService
from app.models.financial.expense import (
    Expense,
    ExpenseItem,
    ExpenseReceipt,
    ExpenseApproval,
)
from app.schemas.financial.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseItemCreate,
    ApprovalAction,
    SettlementCreate,
)
from app.core.exceptions import BusinessLogicError, NotFoundError


class TestExpenseService:
    """経費管理サービスのテストクラス"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return Mock()

    @pytest.fixture
    def mock_ocr_service(self):
        """モックOCRサービス"""
        return Mock()

    @pytest.fixture
    def mock_workflow_service(self):
        """モックワークフローサービス"""
        return Mock()

    @pytest.fixture
    def expense_service(self, mock_db, mock_ocr_service, mock_workflow_service):
        """テスト用の経費サービスインスタンス"""
        return ExpenseService(
            db=mock_db,
            ocr_service=mock_ocr_service,
            workflow_service=mock_workflow_service
        )

    @pytest.fixture
    def sample_expense_data(self):
        """サンプル経費申請データ"""
        return ExpenseCreate(
            expense_date=date(2024, 7, 15),
            department_id=1,
            project_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="transport",
                    description="東京→大阪 新幹線代",
                    amount=Decimal("28500"),
                    tax_rate=Decimal("10"),
                    account_code="7001",
                ),
                ExpenseItemCreate(
                    expense_type="meeting",
                    description="顧客との会食",
                    amount=Decimal("15000"),
                    tax_rate=Decimal("10"),
                    account_code="7002",
                    vendor="レストラン山田",
                    attendees="顧客A社 山田様、田中様",
                ),
            ],
        )

    @pytest.fixture
    def sample_expense(self):
        """サンプル経費エンティティ"""
        expense = Expense(
            id=1,
            expense_number="EXP-2024-0715-001",
            employee_id=1,
            expense_date=date(2024, 7, 15),
            department_id=1,
            project_id=1,
            total_amount=Decimal("47850"),
            status="pending",
            payment_method="cash",
            current_approval_level=1,
            submitted_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        expense.items = [
            ExpenseItem(
                id=1,
                expense_id=1,
                expense_type="transport",
                description="東京→大阪 新幹線代",
                amount=Decimal("28500"),
                tax_rate=Decimal("10"),
                tax_amount=Decimal("2850"),
                account_code="7001",
            ),
            ExpenseItem(
                id=2,
                expense_id=1,
                expense_type="meeting",
                description="顧客との会食",
                amount=Decimal("15000"),
                tax_rate=Decimal("10"),
                tax_amount=Decimal("1500"),
                account_code="7002",
                vendor="レストラン山田",
                attendees="顧客A社 山田様、田中様",
            ),
        ]
        return expense

    def test_create_expense_success(self, expense_service, mock_db, sample_expense_data):
        """経費申請作成の正常系テスト"""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        employee_id = 1

        # Act
        with patch.object(expense_service, '_generate_expense_number', return_value="EXP-2024-0715-001"):
            result = expense_service.create_expense(
                expense_data=sample_expense_data,
                employee_id=employee_id
            )

        # Assert
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # 作成された経費オブジェクトの検証
        added_expense = mock_db.add.call_args[0][0]
        assert added_expense.employee_id == employee_id
        assert added_expense.expense_date == sample_expense_data.expense_date
        assert added_expense.status == "draft"

    def test_create_expense_with_policy_violation(self, expense_service, mock_db):
        """経費規定違反チェックのテスト"""
        # Arrange
        expense_data = ExpenseCreate(
            expense_date=date(2024, 7, 15),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="transport",
                    description="タクシー代（20:00利用）",
                    amount=Decimal("3500"),
                    tax_rate=Decimal("10"),
                    account_code="7001",
                ),
            ],
        )
        
        # タクシー利用規定のモック
        mock_policy = Mock()
        mock_policy.night_time_start = datetime.strptime("23:00", "%H:%M").time()
        mock_db.query().filter().first.return_value = mock_policy

        # Act
        with patch.object(expense_service, '_check_policy_violation', return_value=True):
            result = expense_service.create_expense(expense_data, 1)

        # Assert
        # 警告フラグが設定されることを確認
        added_expense = mock_db.add.call_args[0][0]
        assert hasattr(added_expense, 'has_policy_warning')

    def test_submit_expense_success(self, expense_service, mock_db, mock_workflow_service, sample_expense):
        """経費申請提出の正常系テスト"""
        # Arrange
        sample_expense.status = "draft"
        mock_db.query().filter().first.return_value = sample_expense
        mock_db.commit = Mock()
        
        mock_workflow_service.start_approval_workflow.return_value = {
            "workflow_id": "WF-001",
            "next_approver_id": 2
        }

        # Act
        result = expense_service.submit_expense(1)

        # Assert
        assert sample_expense.status == "pending"
        assert sample_expense.submitted_at is not None
        assert mock_workflow_service.start_approval_workflow.called
        assert mock_db.commit.called

    def test_approve_expense_success(self, expense_service, mock_db, mock_workflow_service, sample_expense):
        """経費承認の正常系テスト"""
        # Arrange
        sample_expense.status = "pending"
        sample_expense.current_approval_level = 1
        mock_db.query().filter().first.return_value = sample_expense
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        mock_workflow_service.process_approval.return_value = {
            "status": "approved",
            "next_level": None
        }

        # Act
        result = expense_service.approve_expense(
            expense_id=1,
            approver_id=2,
            comment="承認します"
        )

        # Assert
        assert sample_expense.status == "approved"
        assert mock_db.add.called
        
        # 承認履歴の記録を確認
        approval_record = mock_db.add.call_args[0][0]
        assert isinstance(approval_record, ExpenseApproval)
        assert approval_record.action == "approved"
        assert approval_record.approver_id == 2

    def test_approve_expense_multi_level(self, expense_service, mock_db, mock_workflow_service, sample_expense):
        """多段階承認のテスト"""
        # Arrange
        sample_expense.status = "pending"
        sample_expense.current_approval_level = 1
        sample_expense.total_amount = Decimal("150000")  # 10万円超
        mock_db.query().filter().first.return_value = sample_expense
        
        mock_workflow_service.process_approval.return_value = {
            "status": "pending",
            "next_level": 2,
            "next_approver_id": 3
        }

        # Act
        result = expense_service.approve_expense(1, 2, "一次承認")

        # Assert
        assert sample_expense.status == "pending"  # まだ承認待ち
        assert sample_expense.current_approval_level == 2  # 次のレベルへ

    def test_reject_expense_success(self, expense_service, mock_db, sample_expense):
        """経費却下の正常系テスト"""
        # Arrange
        sample_expense.status = "pending"
        mock_db.query().filter().first.return_value = sample_expense
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        result = expense_service.reject_expense(
            expense_id=1,
            approver_id=2,
            reason="領収書が不明瞭です"
        )

        # Assert
        assert sample_expense.status == "rejected"
        assert mock_db.add.called
        
        # 却下履歴の記録を確認
        rejection_record = mock_db.add.call_args[0][0]
        assert rejection_record.action == "rejected"
        assert rejection_record.comment == "領収書が不明瞭です"

    @pytest.mark.asyncio
    async def test_process_ocr_success(self, expense_service, mock_ocr_service):
        """OCR処理の正常系テスト"""
        # Arrange
        mock_file = Mock()
        mock_file.read = AsyncMock(return_value=b"image_data")
        
        mock_ocr_service.extract_receipt_data.return_value = {
            "date": "2024-07-15",
            "vendor": "コンビニA",
            "amount": 1500,
            "items": [
                {"description": "弁当", "amount": 500},
                {"description": "飲み物", "amount": 200},
                {"description": "文房具", "amount": 800},
            ]
        }

        # Act
        result = await expense_service.process_ocr(mock_file)

        # Assert
        assert result["success"] is True
        assert result["data"]["vendor"] == "コンビニA"
        assert result["data"]["amount"] == 1500
        assert len(result["data"]["items"]) == 3

    def test_create_monthly_settlement_success(self, expense_service, mock_db):
        """月次精算作成の正常系テスト"""
        # Arrange
        settlement_data = SettlementCreate(
            settlement_period="2024-07",
            settlement_date=date(2024, 8, 10),
            employee_ids=[1, 2, 3]
        )
        
        # 承認済み経費のモック
        approved_expenses = [
            Mock(id=1, employee_id=1, total_amount=Decimal("50000")),
            Mock(id=2, employee_id=1, total_amount=Decimal("30000")),
            Mock(id=3, employee_id=2, total_amount=Decimal("45000")),
        ]
        
        mock_db.query().filter().all.return_value = approved_expenses
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Act
        with patch.object(expense_service, '_generate_settlement_number', return_value="SET-2024-07-001"):
            result = expense_service.create_monthly_settlement(settlement_data, created_by=1)

        # Assert
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # 精算オブジェクトの検証
        settlement = mock_db.add.call_args[0][0]
        assert settlement.settlement_period == "2024-07"
        assert settlement.total_amount == Decimal("125000")
        assert settlement.employee_count == 2  # 実際の経費がある従業員数

    def test_generate_payment_file(self, expense_service, mock_db):
        """支払ファイル生成のテスト"""
        # Arrange
        settlement = Mock(
            id=1,
            settlement_number="SET-2024-07-001",
            details=[
                Mock(
                    employee_id=1,
                    amount=Decimal("80000"),
                    employee=Mock(
                        bank_account_number="1234567",
                        bank_account_name="ヤマダタロウ",
                        bank_name="みずほ銀行",
                        branch_name="東京支店"
                    )
                ),
                Mock(
                    employee_id=2,
                    amount=Decimal("45000"),
                    employee=Mock(
                        bank_account_number="7654321",
                        bank_account_name="スズキハナコ",
                        bank_name="三菱UFJ銀行",
                        branch_name="新宿支店"
                    )
                ),
            ]
        )
        
        mock_db.query().filter().first.return_value = settlement

        # Act
        result = expense_service.generate_payment_file(1)

        # Assert
        assert "payment_file_path" in result
        assert result["total_amount"] == Decimal("125000")
        assert result["payment_count"] == 2

    def test_check_budget_integration(self, expense_service, mock_db):
        """予算チェック統合のテスト"""
        # Arrange
        expense_data = ExpenseCreate(
            expense_date=date(2024, 7, 15),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="entertainment",
                    description="接待交際費",
                    amount=Decimal("60000"),
                    tax_rate=Decimal("10"),
                    account_code="7003",
                ),
            ],
        )
        
        # 予算消化状況のモック
        mock_budget_consumption = Mock(
            consumed_amount=Decimal("450000"),
            remaining_amount=Decimal("50000"),
            consumption_rate=Decimal("90")
        )
        
        with patch.object(expense_service, '_check_budget_availability', return_value=mock_budget_consumption):
            # Act & Assert
            with pytest.raises(BusinessLogicError) as exc_info:
                expense_service.create_expense(expense_data, 1)
            
            assert "予算超過" in str(exc_info.value)

    def test_validate_receipt_required(self, expense_service, mock_db):
        """領収書必須チェックのテスト"""
        # Arrange
        expense = Mock(
            items=[
                Mock(expense_type="meeting", amount=Decimal("5000")),
                Mock(expense_type="entertainment", amount=Decimal("50000")),
            ],
            receipts=[]
        )
        
        # 経費ポリシーのモック
        mock_policy = Mock(receipt_required=True)
        mock_db.query().filter().first.return_value = mock_policy

        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            expense_service._validate_receipts(expense)
        
        assert "領収書が必要です" in str(exc_info.value)