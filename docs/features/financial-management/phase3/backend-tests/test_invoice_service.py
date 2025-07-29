"""
請求管理サービスのユニットテスト
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from app.services.financial.invoice_service import InvoiceService
from app.models.financial.invoice import (
    Quote,
    QuoteItem,
    Invoice,
    InvoiceItem,
    InvoiceTaxDetail,
)
from app.schemas.financial.invoice import (
    QuoteCreate,
    InvoiceCreate,
    InvoiceUpdate,
    LineItemCreate,
    InvoiceSendRequest,
)
from app.core.exceptions import BusinessLogicError, NotFoundError


class TestInvoiceService:
    """請求管理サービスのテストクラス"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return Mock()

    @pytest.fixture
    def mock_pdf_service(self):
        """モックPDFサービス"""
        return Mock()

    @pytest.fixture
    def mock_mail_service(self):
        """モックメールサービス"""
        return Mock()

    @pytest.fixture
    def invoice_service(self, mock_db, mock_pdf_service, mock_mail_service):
        """テスト用の請求サービスインスタンス"""
        return InvoiceService(
            db=mock_db,
            pdf_service=mock_pdf_service,
            mail_service=mock_mail_service
        )

    @pytest.fixture
    def sample_quote_data(self):
        """サンプル見積データ"""
        return QuoteCreate(
            customer_id=1,
            quote_date=date(2024, 7, 15),
            valid_until=date(2024, 8, 31),
            items=[
                LineItemCreate(
                    description="コンサルティングサービス（月額）",
                    quantity=Decimal("2"),
                    unit_price=Decimal("500000"),
                    tax_rate=Decimal("10"),
                ),
                LineItemCreate(
                    product_id=1,
                    description="システム開発（人月）",
                    quantity=Decimal("1.5"),
                    unit_price=Decimal("800000"),
                    tax_rate=Decimal("10"),
                ),
            ],
            discount={"type": "percentage", "value": 5},
            terms="納品後30日以内にお支払いください",
            notes="初回取引につき5%割引適用",
        )

    @pytest.fixture
    def sample_invoice_data(self):
        """サンプル請求書データ"""
        return InvoiceCreate(
            customer_id=1,
            invoice_date=date(2024, 7, 31),
            due_date=date(2024, 8, 31),
            items=[
                LineItemCreate(
                    description="7月分コンサルティング料",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000000"),
                    tax_rate=Decimal("10"),
                ),
                LineItemCreate(
                    description="会議費（軽減税率）",
                    quantity=Decimal("1"),
                    unit_price=Decimal("10000"),
                    tax_rate=Decimal("8"),
                ),
            ],
            payment_terms="月末締め翌月末払い",
        )

    @pytest.fixture
    def sample_invoice(self):
        """サンプル請求書エンティティ"""
        invoice = Invoice(
            id=1,
            invoice_number="INV-2024-0731-001",
            customer_id=1,
            invoice_date=date(2024, 7, 31),
            due_date=date(2024, 8, 31),
            subtotal_amount=Decimal("1010000"),
            tax_amount_8=Decimal("800"),
            tax_amount_10=Decimal("100000"),
            total_amount=Decimal("1110800"),
            paid_amount=Decimal("0"),
            status="sent",
            payment_terms="月末締め翌月末払い",
            is_qualified_invoice=True,
            created_by=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return invoice

    def test_create_quote_success(self, invoice_service, mock_db, sample_quote_data):
        """見積作成の正常系テスト"""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # 顧客情報のモック
        mock_customer = Mock(
            id=1,
            customer_name="ABC商事",
            credit_limit=Decimal("10000000")
        )
        mock_db.query().filter().first.return_value = mock_customer

        # Act
        with patch.object(invoice_service, '_generate_quote_number', return_value="QT-2024-0715-001"):
            result = invoice_service.create_quote(
                quote_data=sample_quote_data,
                created_by=1
            )

        # Assert
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # 作成された見積オブジェクトの検証
        added_quote = mock_db.add.call_args[0][0]
        assert added_quote.customer_id == 1
        assert added_quote.quote_date == date(2024, 7, 15)
        assert added_quote.status == "draft"

    def test_create_quote_with_discount_calculation(self, invoice_service, mock_db, sample_quote_data):
        """割引計算を含む見積作成のテスト"""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_customer = Mock(id=1)
        mock_db.query().filter().first.return_value = mock_customer

        # Act
        with patch.object(invoice_service, '_calculate_totals') as mock_calculate:
            mock_calculate.return_value = {
                "subtotal": Decimal("2200000"),  # (500000*2 + 800000*1.5)
                "discount_amount": Decimal("110000"),  # 5%
                "tax_amount": Decimal("209000"),  # (2200000-110000)*0.1
                "total": Decimal("2299000")
            }
            
            result = invoice_service.create_quote(sample_quote_data, 1)

        # Assert
        added_quote = mock_db.add.call_args[0][0]
        assert added_quote.subtotal_amount == Decimal("2200000")
        assert added_quote.discount_amount == Decimal("110000")
        assert added_quote.total_amount == Decimal("2299000")

    def test_convert_quote_to_invoice_success(self, invoice_service, mock_db):
        """見積から請求書への変換の正常系テスト"""
        # Arrange
        mock_quote = Mock(
            id=1,
            customer_id=1,
            status="accepted",
            items=[
                Mock(
                    description="コンサルティング",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000000"),
                    tax_rate=Decimal("10")
                )
            ],
            discount=None
        )
        mock_db.query().filter().first.return_value = mock_quote
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        with patch.object(invoice_service, '_generate_invoice_number', return_value="INV-2024-0731-001"):
            result = invoice_service.convert_quote_to_invoice(
                quote_id=1,
                invoice_date=date(2024, 7, 31),
                due_date=date(2024, 8, 31)
            )

        # Assert
        assert mock_db.add.called
        added_invoice = mock_db.add.call_args[0][0]
        assert added_invoice.quote_id == 1
        assert added_invoice.customer_id == 1
        assert added_invoice.invoice_number == "INV-2024-0731-001"

    def test_create_invoice_with_qualified_invoice(self, invoice_service, mock_db, sample_invoice_data):
        """適格請求書作成のテスト"""
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # 顧客情報のモック（適格請求書発行事業者）
        mock_customer = Mock(
            id=1,
            customer_name="ABC商事",
            tax_registration_number="T1234567890123"
        )
        mock_db.query().filter().first.return_value = mock_customer

        # Act
        with patch.object(invoice_service, '_generate_invoice_number', return_value="INV-2024-0731-001"):
            result = invoice_service.create_invoice(
                invoice_data=sample_invoice_data,
                created_by=1
            )

        # Assert
        added_invoice = mock_db.add.call_args[0][0]
        assert added_invoice.is_qualified_invoice is True
        
        # 税率別の集計確認
        assert added_invoice.tax_amount_8 == Decimal("800")  # 10000 * 0.08
        assert added_invoice.tax_amount_10 == Decimal("100000")  # 1000000 * 0.1

    def test_create_recurring_invoice(self, invoice_service, mock_db):
        """定期請求書作成のテスト"""
        # Arrange
        recurring_config = {
            "customer_id": 1,
            "frequency": "monthly",
            "start_date": date(2024, 4, 1),
            "end_date": date(2025, 3, 31),
            "template_items": [
                {
                    "description": "月額保守料",
                    "quantity": 1,
                    "unit_price": 50000,
                    "tax_rate": 10
                }
            ]
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        result = invoice_service.create_recurring_invoice(recurring_config)

        # Assert
        assert mock_db.add.called
        added_recurring = mock_db.add.call_args[0][0]
        assert added_recurring.frequency == "monthly"
        assert added_recurring.next_invoice_date == date(2024, 4, 1)

    def test_generate_recurring_invoices_batch(self, invoice_service, mock_db):
        """定期請求書バッチ生成のテスト"""
        # Arrange
        today = date(2024, 7, 31)
        
        # アクティブな定期請求設定のモック
        recurring_invoices = [
            Mock(
                id=1,
                customer_id=1,
                frequency="monthly",
                next_invoice_date=today,
                amount=Decimal("50000"),
                template_items=[
                    {"description": "月額保守料", "quantity": 1, "unit_price": 50000, "tax_rate": 10}
                ]
            ),
            Mock(
                id=2,
                customer_id=2,
                frequency="monthly",
                next_invoice_date=today,
                amount=Decimal("100000"),
                template_items=[
                    {"description": "月額利用料", "quantity": 1, "unit_price": 100000, "tax_rate": 10}
                ]
            ),
        ]
        
        mock_db.query().filter().all.return_value = recurring_invoices
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        with patch.object(invoice_service, '_generate_invoice_number', side_effect=["INV-001", "INV-002"]):
            result = invoice_service.generate_recurring_invoices_batch(today)

        # Assert
        assert result["generated_count"] == 2
        assert result["total_amount"] == Decimal("150000")
        assert mock_db.add.call_count == 2  # 2つの請求書が作成される

    def test_generate_invoice_pdf(self, invoice_service, mock_db, mock_pdf_service, sample_invoice):
        """請求書PDF生成のテスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_invoice
        
        # 顧客情報のモック
        sample_invoice.customer = Mock(
            customer_name="ABC商事",
            address="東京都千代田区...",
            tax_registration_number="T1234567890123"
        )
        
        # 組織情報のモック  
        mock_org = Mock(
            name="株式会社ITDO",
            address="東京都港区...",
            tax_registration_number="T0987654321098"
        )
        
        mock_pdf_service.generate_invoice_pdf.return_value = b"PDF_CONTENT"

        # Act
        with patch.object(invoice_service, '_get_organization_info', return_value=mock_org):
            result = invoice_service.generate_invoice_pdf(1)

        # Assert
        assert mock_pdf_service.generate_invoice_pdf.called
        assert result == b"PDF_CONTENT"
        
        # PDF生成に渡されたデータの検証
        pdf_data = mock_pdf_service.generate_invoice_pdf.call_args[0][0]
        assert pdf_data["invoice_number"] == "INV-2024-0731-001"
        assert pdf_data["is_qualified_invoice"] is True

    def test_send_invoice_email(self, invoice_service, mock_db, mock_mail_service, sample_invoice):
        """請求書メール送信のテスト"""
        # Arrange
        mock_db.query().filter().first.return_value = sample_invoice
        
        send_request = InvoiceSendRequest(
            recipients=["accounting@abc-corp.jp"],
            cc=["manager@abc-corp.jp"],
            subject="7月分ご請求書送付の件",
            message="いつもお世話になっております。7月分のご請求書をお送りします。",
        )
        
        mock_mail_service.send_invoice.return_value = {
            "success": True,
            "message_id": "MSG-123456"
        }

        # Act
        with patch.object(invoice_service, 'generate_invoice_pdf', return_value=b"PDF"):
            result = invoice_service.send_invoice_email(1, send_request)

        # Assert
        assert mock_mail_service.send_invoice.called
        assert result["sent_at"] is not None
        assert sample_invoice.status == "sent"

    def test_create_split_invoice(self, invoice_service, mock_db):
        """分割請求書作成のテスト"""
        # Arrange
        split_config = {
            "total_amount": Decimal("6000000"),
            "installments": [
                {"due_date": date(2024, 4, 30), "percentage": 33.33, "description": "着手金"},
                {"due_date": date(2024, 7, 31), "percentage": 33.33, "description": "中間金"},
                {"due_date": date(2024, 10, 31), "percentage": 33.34, "description": "最終金"},
            ]
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Act
        result = invoice_service.create_split_invoices(
            customer_id=1,
            project_id=1,
            split_config=split_config
        )

        # Assert
        assert len(result) == 3
        assert mock_db.add.call_count == 3
        
        # 金額の検証
        total = sum(inv["amount"] for inv in result)
        assert total == Decimal("6000000")

    def test_check_overdue_invoices(self, invoice_service, mock_db):
        """請求書期限超過チェックのテスト"""
        # Arrange
        today = date(2024, 8, 1)
        
        overdue_invoices = [
            Mock(
                id=1,
                invoice_number="INV-001",
                customer_id=1,
                due_date=date(2024, 6, 30),
                total_amount=Decimal("100000"),
                paid_amount=Decimal("0"),
                status="sent"
            ),
            Mock(
                id=2,
                invoice_number="INV-002",
                customer_id=2,
                due_date=date(2024, 7, 15),
                total_amount=Decimal("200000"),
                paid_amount=Decimal("50000"),
                status="partial"
            ),
        ]
        
        mock_db.query().filter().all.return_value = overdue_invoices
        mock_db.commit = Mock()

        # Act
        result = invoice_service.check_overdue_invoices(today)

        # Assert
        assert len(result) == 2
        assert overdue_invoices[0].status == "overdue"
        assert overdue_invoices[1].status == "overdue"
        assert mock_db.commit.called

    def test_validate_credit_limit(self, invoice_service, mock_db):
        """与信限度額チェックのテスト"""
        # Arrange
        customer = Mock(
            id=1,
            credit_limit=Decimal("5000000")
        )
        
        # 既存の売掛金
        existing_receivables = Mock(
            total_balance=Decimal("4500000")
        )
        
        mock_db.query().filter().first.side_effect = [customer, existing_receivables]
        
        invoice_amount = Decimal("1000000")

        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            invoice_service._validate_credit_limit(1, invoice_amount)
        
        assert "与信限度額を超過" in str(exc_info.value)