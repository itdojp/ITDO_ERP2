"""
財務管理システム統合テスト
サービス間の連携、データベーストランザクション、外部サービス統合をテスト
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.database import Base
from app.models.financial.budget import Budget, BudgetAllocation, BudgetConsumption
from app.models.financial.expense import Expense, ExpenseItem, ExpenseApproval
from app.models.financial.invoice import Invoice, InvoiceItem, InvoiceTaxDetail
from app.models.financial.payment import Payment, PaymentAllocation
from app.services.financial.budget_service import BudgetService
from app.services.financial.expense_service import ExpenseService
from app.services.financial.invoice_service import InvoiceService
from app.services.financial.revenue_service import RevenueService
from app.services.workflow_service import WorkflowService
from app.core.events import EventBus
from app.schemas.financial.budget import BudgetCreate
from app.schemas.financial.expense import ExpenseCreate, ExpenseItemCreate
from app.schemas.financial.invoice import InvoiceCreate, LineItemCreate
from app.schemas.financial.payment import PaymentCreate


class TestFinancialIntegration:
    """財務管理システムの統合テストクラス"""

    @pytest.fixture(scope="module")
    def postgres_container(self) -> Generator:
        """PostgreSQLテストコンテナ"""
        with PostgresContainer("postgres:15-alpine") as postgres:
            yield postgres

    @pytest.fixture(scope="module")
    def redis_container(self) -> Generator:
        """Redisテストコンテナ"""
        with RedisContainer("redis:7-alpine") as redis:
            yield redis

    @pytest.fixture
    def db_session(self, postgres_container) -> Generator[Session, None, None]:
        """データベースセッション"""
        engine = create_engine(postgres_container.get_connection_url())
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    @pytest.fixture
    def event_bus(self, redis_container):
        """イベントバス"""
        return EventBus(redis_url=redis_container.get_connection_url())

    @pytest.fixture
    def workflow_service(self, db_session):
        """ワークフローサービス"""
        return WorkflowService(db_session)

    @pytest.fixture
    def budget_service(self, db_session):
        """予算管理サービス"""
        return BudgetService(db_session)

    @pytest.fixture
    def expense_service(self, db_session, workflow_service):
        """経費管理サービス"""
        # OCRサービスはモック化
        ocr_service = None
        return ExpenseService(db_session, ocr_service, workflow_service)

    @pytest.fixture
    def invoice_service(self, db_session):
        """請求管理サービス"""
        # PDFとメールサービスはモック化
        pdf_service = None
        mail_service = None
        return InvoiceService(db_session, pdf_service, mail_service)

    @pytest.fixture
    def revenue_service(self, db_session):
        """売上・入金管理サービス"""
        return RevenueService(db_session)

    @pytest.fixture
    def sample_organization(self, db_session):
        """テスト用組織データ"""
        from app.models.core.organization import Organization
        org = Organization(
            id=1,
            name="テスト株式会社",
            tax_registration_number="T1234567890123",
            created_at=datetime.now()
        )
        db_session.add(org)
        db_session.commit()
        return org

    @pytest.fixture
    def sample_users(self, db_session, sample_organization):
        """テスト用ユーザーデータ"""
        from app.models.core.user import User
        users = [
            User(
                id=1,
                username="employee01",
                full_name="社員太郎",
                email="employee01@test.com",
                organization_id=sample_organization.id,
                department_id=1,
                role="employee"
            ),
            User(
                id=2,
                username="manager01",
                full_name="課長花子",
                email="manager01@test.com",
                organization_id=sample_organization.id,
                department_id=1,
                role="manager"
            ),
            User(
                id=3,
                username="director01",
                full_name="部長次郎",
                email="director01@test.com",
                organization_id=sample_organization.id,
                department_id=1,
                role="director"
            ),
        ]
        db_session.add_all(users)
        db_session.commit()
        return users

    def test_budget_expense_integration(
        self,
        db_session,
        budget_service,
        expense_service,
        event_bus,
        sample_organization,
        sample_users
    ):
        """予算管理と経費管理の統合テスト"""
        # 1. 予算作成
        budget_data = BudgetCreate(
            budget_code="BUD-2024-TEST-001",
            budget_name="テスト部門予算",
            fiscal_year=2024,
            period_start=date(2024, 4, 1),
            period_end=date(2025, 3, 31),
            budget_type="annual",
            department_id=1,
            expense_budget=Decimal("1000000"),  # 100万円
        )
        
        budget = budget_service.create_budget(
            budget_data=budget_data,
            user_id=sample_users[2].id,  # 部長が作成
            organization_id=sample_organization.id
        )
        
        assert budget.id is not None
        assert budget.status == "draft"
        
        # 2. 予算承認
        budget_service.approve_budget(
            budget_id=budget.id,
            approver_id=sample_users[2].id,
            comment="承認します"
        )
        
        db_session.refresh(budget)
        assert budget.status == "approved"
        
        # 3. 予算配分
        allocations = [
            {"account_code": "7001", "allocated_amount": Decimal("500000")},  # 交通費
            {"account_code": "7002", "allocated_amount": Decimal("300000")},  # 会議費
            {"account_code": "7003", "allocated_amount": Decimal("200000")},  # 交際費
        ]
        
        for alloc in allocations:
            allocation = BudgetAllocation(
                budget_id=budget.id,
                account_code=alloc["account_code"],
                allocated_amount=alloc["allocated_amount"],
                created_at=datetime.now()
            )
            db_session.add(allocation)
        db_session.commit()
        
        # 4. 経費申請作成
        expense_data = ExpenseCreate(
            expense_date=date(2024, 7, 15),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="transport",
                    description="東京-大阪出張",
                    amount=Decimal("50000"),
                    tax_rate=Decimal("10"),
                    account_code="7001",
                ),
                ExpenseItemCreate(
                    expense_type="meeting",
                    description="顧客会議費",
                    amount=Decimal("30000"),
                    tax_rate=Decimal("10"),
                    account_code="7002",
                ),
            ],
        )
        
        expense = expense_service.create_expense(
            expense_data=expense_data,
            employee_id=sample_users[0].id  # 社員が申請
        )
        
        assert expense.id is not None
        assert expense.total_amount == Decimal("88000")  # 税込み
        
        # 5. 経費申請提出・承認
        expense_service.submit_expense(expense.id)
        
        # マネージャー承認
        expense_service.approve_expense(
            expense_id=expense.id,
            approver_id=sample_users[1].id,
            comment="承認します"
        )
        
        db_session.refresh(expense)
        assert expense.status == "approved"
        
        # 6. 予算消化確認
        consumption = budget_service.get_budget_consumption(
            budget_id=budget.id,
            as_of_date=date(2024, 7, 31)
        )
        
        # 交通費: 50,000円、会議費: 30,000円の消化
        assert consumption.consumed_amount == Decimal("80000")
        assert consumption.remaining_amount == Decimal("920000")
        assert consumption.consumption_rate == pytest.approx(8.0, 0.1)

    def test_invoice_payment_integration(
        self,
        db_session,
        invoice_service,
        revenue_service,
        event_bus,
        sample_organization
    ):
        """請求管理と入金管理の統合テスト"""
        # 1. 顧客マスタ作成
        from app.models.master.customer import Customer
        customer = Customer(
            id=1,
            customer_code="CUST-001",
            customer_name="テスト商事株式会社",
            tax_registration_number="T9876543210987",
            payment_terms="月末締め翌月末払い",
            credit_limit=Decimal("10000000"),
            organization_id=sample_organization.id,
            created_at=datetime.now()
        )
        db_session.add(customer)
        db_session.commit()
        
        # 2. 請求書作成
        invoice_data = InvoiceCreate(
            customer_id=customer.id,
            invoice_date=date(2024, 7, 31),
            due_date=date(2024, 8, 31),
            items=[
                LineItemCreate(
                    description="コンサルティング料（7月分）",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000000"),
                    tax_rate=Decimal("10"),
                ),
                LineItemCreate(
                    description="システム保守料（7月分）",
                    quantity=Decimal("1"),
                    unit_price=Decimal("300000"),
                    tax_rate=Decimal("10"),
                ),
            ],
            payment_terms="月末締め翌月末払い",
        )
        
        invoice = invoice_service.create_invoice(
            invoice_data=invoice_data,
            created_by=1
        )
        
        assert invoice.id is not None
        assert invoice.total_amount == Decimal("1430000")  # 税込み
        assert invoice.status == "draft"
        
        # 3. 請求書送付
        invoice_service.update_invoice_status(
            invoice_id=invoice.id,
            status="sent",
            updated_by=1
        )
        
        # 4. 入金登録
        payment_data = PaymentCreate(
            payment_date=date(2024, 8, 30),
            customer_id=customer.id,
            amount=Decimal("1430000"),
            payment_method="bank_transfer",
            bank_name="みずほ銀行",
            reference_number="20240830-001",
        )
        
        payment = revenue_service.create_payment(
            payment_data=payment_data,
            created_by=1
        )
        
        assert payment.id is not None
        assert payment.status == "unallocated"
        
        # 5. 入金消込
        allocation_result = revenue_service.allocate_payment(
            payment_id=payment.id,
            invoice_ids=[invoice.id],
            auto_allocate=True
        )
        
        assert allocation_result["allocated_amount"] == Decimal("1430000")
        assert allocation_result["remaining_amount"] == Decimal("0")
        
        # 6. 請求書・入金ステータス確認
        db_session.refresh(invoice)
        db_session.refresh(payment)
        
        assert invoice.status == "paid"
        assert invoice.paid_amount == Decimal("1430000")
        assert payment.status == "allocated"
        assert payment.allocated_amount == Decimal("1430000")

    def test_expense_budget_alert_integration(
        self,
        db_session,
        budget_service,
        expense_service,
        event_bus,
        sample_organization,
        sample_users
    ):
        """経費申請による予算アラートの統合テスト"""
        # 1. 少額予算を作成（アラートテスト用）
        budget_data = BudgetCreate(
            budget_code="BUD-2024-ALERT-001",
            budget_name="アラートテスト予算",
            fiscal_year=2024,
            period_start=date(2024, 7, 1),
            period_end=date(2024, 7, 31),
            budget_type="monthly",
            department_id=1,
            expense_budget=Decimal("100000"),  # 10万円
        )
        
        budget = budget_service.create_budget(
            budget_data=budget_data,
            user_id=sample_users[2].id,
            organization_id=sample_organization.id
        )
        
        # 予算承認
        budget_service.approve_budget(budget.id, sample_users[2].id, "承認")
        
        # 予算配分
        allocation = BudgetAllocation(
            budget_id=budget.id,
            account_code="7003",  # 交際費
            allocated_amount=Decimal("100000"),
            created_at=datetime.now()
        )
        db_session.add(allocation)
        db_session.commit()
        
        # 2. 段階的に経費を申請
        alerts_triggered = []
        
        # 60%消化（アラートなし）
        expense1_data = ExpenseCreate(
            expense_date=date(2024, 7, 10),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="entertainment",
                    description="顧客接待",
                    amount=Decimal("60000"),
                    tax_rate=Decimal("10"),
                    account_code="7003",
                ),
            ],
        )
        
        expense1 = expense_service.create_expense(expense1_data, sample_users[0].id)
        expense_service.submit_expense(expense1.id)
        expense_service.approve_expense(expense1.id, sample_users[1].id, "承認")
        
        consumption1 = budget_service.get_budget_consumption(budget.id, date(2024, 7, 15))
        assert consumption1.consumption_rate == pytest.approx(60.0, 0.1)
        
        # 3. 85%消化（80%アラート発生）
        expense2_data = ExpenseCreate(
            expense_date=date(2024, 7, 20),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="entertainment",
                    description="重要顧客接待",
                    amount=Decimal("25000"),
                    tax_rate=Decimal("10"),
                    account_code="7003",
                ),
            ],
        )
        
        expense2 = expense_service.create_expense(expense2_data, sample_users[0].id)
        expense_service.submit_expense(expense2.id)
        expense_service.approve_expense(expense2.id, sample_users[1].id, "承認")
        
        # アラート確認
        alerts = db_session.query(BudgetAlert).filter(
            BudgetAlert.budget_id == budget.id
        ).all()
        
        assert len(alerts) >= 1
        assert any(alert.alert_type == "threshold_80" for alert in alerts)
        
        # 4. 予算超過申請（エラー発生）
        expense3_data = ExpenseCreate(
            expense_date=date(2024, 7, 25),
            department_id=1,
            items=[
                ExpenseItemCreate(
                    expense_type="entertainment",
                    description="追加接待",
                    amount=Decimal("20000"),
                    tax_rate=Decimal("10"),
                    account_code="7003",
                ),
            ],
        )
        
        with pytest.raises(BusinessLogicError) as exc_info:
            expense3 = expense_service.create_expense(expense3_data, sample_users[0].id)
            expense_service.submit_expense(expense3.id)
        
        assert "予算超過" in str(exc_info.value)

    def test_recurring_invoice_payment_cycle(
        self,
        db_session,
        invoice_service,
        revenue_service,
        sample_organization
    ):
        """定期請求と入金サイクルの統合テスト"""
        # 1. 定期請求設定作成
        from app.models.financial.invoice import RecurringInvoice
        
        customer = Customer(
            id=2,
            customer_code="CUST-002",
            customer_name="定期顧客株式会社",
            payment_terms="月末締め翌月末払い",
            organization_id=sample_organization.id,
            created_at=datetime.now()
        )
        db_session.add(customer)
        db_session.commit()
        
        recurring = RecurringInvoice(
            customer_id=customer.id,
            frequency="monthly",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            next_invoice_date=date(2024, 7, 31),
            template_items=[
                {
                    "description": "月額サービス利用料",
                    "quantity": 1,
                    "unit_price": 100000,
                    "tax_rate": 10
                }
            ],
            amount=Decimal("110000"),  # 税込み
            is_active=True,
            created_by=1,
            created_at=datetime.now()
        )
        db_session.add(recurring)
        db_session.commit()
        
        # 2. 定期請求バッチ実行
        batch_result = invoice_service.generate_recurring_invoices_batch(
            target_date=date(2024, 7, 31)
        )
        
        assert batch_result["generated_count"] == 1
        assert batch_result["total_amount"] == Decimal("110000")
        
        # 3. 生成された請求書確認
        invoices = db_session.query(Invoice).filter(
            Invoice.customer_id == customer.id,
            Invoice.invoice_date == date(2024, 7, 31)
        ).all()
        
        assert len(invoices) == 1
        invoice = invoices[0]
        assert invoice.total_amount == Decimal("110000")
        assert invoice.due_date == date(2024, 8, 31)
        
        # 4. 3ヶ月分の入金サイクルテスト
        for month_offset in range(3):
            payment_date = date(2024, 8 + month_offset, 25)
            
            # 入金登録
            payment_data = PaymentCreate(
                payment_date=payment_date,
                customer_id=customer.id,
                amount=Decimal("110000"),
                payment_method="bank_transfer",
                reference_number=f"REC-{payment_date.strftime('%Y%m%d')}"
            )
            
            payment = revenue_service.create_payment(payment_data, created_by=1)
            
            # 自動消込
            allocation_result = revenue_service.auto_allocate_payments(
                customer_id=customer.id
            )
            
            assert allocation_result["success_count"] == 1
            assert allocation_result["total_allocated"] == Decimal("110000")

    @pytest.mark.asyncio
    async def test_financial_report_generation(
        self,
        db_session,
        budget_service,
        expense_service,
        invoice_service,
        revenue_service,
        sample_organization
    ):
        """財務レポート生成の統合テスト"""
        # テストデータのセットアップは省略（実際の実装では必要）
        
        # レポートサービスのモック
        from app.services.financial.report_service import ReportService
        report_service = ReportService(db_session)
        
        # 1. 試算表生成
        trial_balance = await report_service.generate_trial_balance(
            organization_id=sample_organization.id,
            period_start=date(2024, 7, 1),
            period_end=date(2024, 7, 31)
        )
        
        assert trial_balance is not None
        assert "accounts" in trial_balance
        assert "total_debit" in trial_balance
        assert "total_credit" in trial_balance
        assert trial_balance["total_debit"] == trial_balance["total_credit"]
        
        # 2. 予実対比分析
        budget_actual = await report_service.generate_budget_actual_report(
            organization_id=sample_organization.id,
            fiscal_year=2024,
            period_end=date(2024, 7, 31)
        )
        
        assert budget_actual is not None
        assert "budget_items" in budget_actual
        assert all(
            item["achievement_rate"] >= 0 
            for item in budget_actual["budget_items"]
        )
        
        # 3. キャッシュフロー計算書
        cash_flow = await report_service.generate_cash_flow_statement(
            organization_id=sample_organization.id,
            period_start=date(2024, 7, 1),
            period_end=date(2024, 7, 31)
        )
        
        assert cash_flow is not None
        assert "operating_activities" in cash_flow
        assert "investing_activities" in cash_flow
        assert "financing_activities" in cash_flow
        assert cash_flow["net_cash_flow"] == (
            cash_flow["operating_activities"]["total"] +
            cash_flow["investing_activities"]["total"] +
            cash_flow["financing_activities"]["total"]
        )

    def test_multi_currency_transaction(
        self,
        db_session,
        invoice_service,
        revenue_service,
        sample_organization
    ):
        """多通貨取引の統合テスト"""
        # 1. 外貨建て請求書作成
        customer = Customer(
            id=3,
            customer_code="CUST-USD-001",
            customer_name="Global Tech Inc.",
            currency_code="USD",
            organization_id=sample_organization.id,
            created_at=datetime.now()
        )
        db_session.add(customer)
        db_session.commit()
        
        invoice_data = InvoiceCreate(
            customer_id=customer.id,
            invoice_date=date(2024, 7, 31),
            due_date=date(2024, 8, 31),
            currency_code="USD",
            exchange_rate=Decimal("145.50"),  # 1USD = 145.50JPY
            items=[
                LineItemCreate(
                    description="Consulting Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("10000"),  # USD
                    tax_rate=Decimal("0"),  # 外貨は非課税
                ),
            ],
            payment_terms="Net 30",
        )
        
        invoice = invoice_service.create_invoice(invoice_data, created_by=1)
        
        assert invoice.currency_code == "USD"
        assert invoice.total_amount == Decimal("10000")  # USD
        assert invoice.total_amount_jpy == Decimal("1455000")  # JPY換算
        
        # 2. 外貨入金と為替差損益
        payment_data = PaymentCreate(
            payment_date=date(2024, 8, 30),
            customer_id=customer.id,
            amount=Decimal("10000"),  # USD
            currency_code="USD",
            exchange_rate=Decimal("148.00"),  # 決済時レート
            payment_method="wire_transfer",
            reference_number="WT-20240830-001"
        )
        
        payment = revenue_service.create_payment(payment_data, created_by=1)
        
        assert payment.amount == Decimal("10000")  # USD
        assert payment.amount_jpy == Decimal("1480000")  # JPY換算
        
        # 3. 消込と為替差益計算
        allocation_result = revenue_service.allocate_payment(
            payment_id=payment.id,
            invoice_ids=[invoice.id],
            auto_allocate=True
        )
        
        # 為替差益: 1,480,000 - 1,455,000 = 25,000円
        assert allocation_result["forex_gain_loss"] == Decimal("25000")
        
        # 為替差損益の仕訳確認
        forex_entries = db_session.query(JournalEntry).filter(
            JournalEntry.reference_type == "payment_allocation",
            JournalEntry.reference_id == payment.id
        ).all()
        
        assert any(
            entry.account_code == "9101"  # 為替差益
            for entry in forex_entries
        )