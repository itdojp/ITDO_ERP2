"""Payment Processing API Tests

Comprehensive test suite for payment processing functionality including
multi-provider support, fraud detection, and analytics.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.payment_processing import (
    PaymentMethod,
    PaymentProvider,
    PaymentStatus,
    PaymentTransaction,
)


class TestPaymentProcessing:
    """Test payment processing API endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment_success(self, client: AsyncClient):
        """Test successful payment creation"""
        payment_data = {
            "amount": "10000.00",
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "customer_id": str(uuid.uuid4()),
            "order_id": "ORD-12345",
            "description": "Test payment for order",
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
            "customer_info": {
                "email": "customer@example.com",
                "ip_address": "192.168.1.1",
                "billing_address_line1": "123 Test Street",
                "billing_city": "Tokyo",
                "billing_postal_code": "100-0001",
                "billing_country": "JP",
            },
            "metadata": {"campaign": "summer_sale", "source": "mobile_app"},
        }

        response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "transaction_id" in data
        assert data["status"] == "completed"
        assert data["risk_score"] is not None
        assert data["risk_score"] <= 100
        assert data["message"] == "Payment successful"

    @pytest.mark.asyncio
    async def test_create_payment_high_risk_blocked(self, client: AsyncClient):
        """Test payment blocked due to high fraud risk"""
        payment_data = {
            "amount": "1000000.00",  # High amount increases risk
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "customer_info": {
                "email": "suspicious@example.com",
                "ip_address": "10.0.0.1",  # Mock suspicious IP
            },
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
        }

        # Mock high risk score
        with patch(
            "app.services.payment_processing_service.PaymentProcessingService._assess_fraud_risk"
        ) as mock_risk:
            mock_risk.return_value = 85  # High risk score

            response = await client.post(
                "/api/v1/payment-processing/payments", json=payment_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is False
            assert data["status"] == "failed"
            assert data["risk_score"] == 85
            assert "security concerns" in data["message"]

    @pytest.mark.asyncio
    async def test_create_payment_card_declined(self, client: AsyncClient):
        """Test payment with declined card"""
        payment_data = {
            "amount": "5000.00",
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "payment_method_info": {
                "card_number": "4000000000000000",  # Mock declined card
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
        }

        response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["status"] == "failed"
        assert data["error_code"] == "card_declined"
        assert "declined" in data["message"]

    @pytest.mark.asyncio
    async def test_create_payment_validation_error(self, client: AsyncClient):
        """Test payment creation with validation errors"""
        payment_data = {
            "amount": "-100.00",  # Invalid negative amount
            "currency": "INVALID",  # Invalid currency
            "payment_method": "credit_card",
        }

        response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_payment_success(self, client: AsyncClient, db_session):
        """Test retrieving payment transaction details"""
        # Create a test transaction
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_test123",
            amount=Decimal("10000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.COMPLETED,
            customer_id=uuid.uuid4(),
            order_id="ORD-12345",
            description="Test payment",
            risk_score=25,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        db_session.add(transaction)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["transaction_id"] == "pay_test123"
        assert data["amount"] == "10000.00"
        assert data["currency"] == "JPY"
        assert data["status"] == "completed"
        assert data["risk_score"] == 25
        assert data["order_id"] == "ORD-12345"

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, client: AsyncClient):
        """Test retrieving non-existent payment"""
        response = await client.get("/api/v1/payment-processing/payments/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refund_payment_full(self, client: AsyncClient, db_session):
        """Test full payment refund"""
        # Create a completed transaction
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_refund_test",
            amount=Decimal("15000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.COMPLETED,
            provider_payment_id="stripe_payment_123",
            completed_at=datetime.now(timezone.utc),
        )

        db_session.add(transaction)
        await db_session.commit()

        refund_data = {
            "reason": "customer_request",
            "reason_details": "Customer requested full refund",
            "notify_customer": True,
        }

        response = await client.post(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}/refund",
            json=refund_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["status"] == "completed"
        assert "refund processed successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_refund_payment_partial(self, client: AsyncClient, db_session):
        """Test partial payment refund"""
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_partial_refund",
            amount=Decimal("20000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.COMPLETED,
            provider_payment_id="stripe_payment_456",
        )

        db_session.add(transaction)
        await db_session.commit()

        refund_data = {
            "amount": "5000.00",
            "reason": "product_defective",
            "reason_details": "Partial refund for defective item",
        }

        response = await client.post(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}/refund",
            json=refund_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_refund_payment_invalid_status(self, client: AsyncClient, db_session):
        """Test refund on non-completed payment"""
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_pending_refund",
            amount=Decimal("10000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.PENDING,  # Not completed
        )

        db_session.add(transaction)
        await db_session.commit()

        refund_data = {"reason": "customer_request"}

        response = await client.post(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}/refund",
            json=refund_data,
        )

        assert response.status_code == 400
        assert "completed transactions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_search_payments_basic(self, client: AsyncClient, db_session):
        """Test basic payment search"""
        customer_id = uuid.uuid4()

        # Create test transactions
        transactions = [
            PaymentTransaction(
                id=uuid.uuid4(),
                transaction_id=f"pay_search_{i}",
                amount=Decimal(f"{1000 * (i + 1)}.00"),
                currency="JPY",
                payment_method=PaymentMethod.CREDIT_CARD,
                payment_provider=PaymentProvider.STRIPE,
                status=PaymentStatus.COMPLETED if i % 2 == 0 else PaymentStatus.FAILED,
                customer_id=customer_id if i < 3 else uuid.uuid4(),
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            for i in range(5)
        ]

        for tx in transactions:
            db_session.add(tx)
        await db_session.commit()

        # Search by customer
        search_data = {"customer_id": str(customer_id), "limit": 10, "offset": 0}

        response = await client.post(
            "/api/v1/payment-processing/payments/search", json=search_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 3  # Only 3 transactions for this customer
        assert len(data["transactions"]) == 3
        assert all(tx["customer_id"] == str(customer_id) for tx in data["transactions"])

    @pytest.mark.asyncio
    async def test_search_payments_with_filters(self, client: AsyncClient, db_session):
        """Test payment search with multiple filters"""
        # Create transactions with various attributes
        base_date = datetime.now(timezone.utc) - timedelta(days=10)

        transactions = [
            PaymentTransaction(
                id=uuid.uuid4(),
                transaction_id=f"pay_filter_{i}",
                amount=Decimal(f"{5000 + i * 1000}.00"),
                currency="JPY",
                payment_method=PaymentMethod.CREDIT_CARD
                if i % 2 == 0
                else PaymentMethod.PAYPAL,
                payment_provider=PaymentProvider.STRIPE,
                status=PaymentStatus.COMPLETED,
                created_at=base_date + timedelta(days=i),
            )
            for i in range(5)
        ]

        for tx in transactions:
            db_session.add(tx)
        await db_session.commit()

        search_data = {
            "status": "completed",
            "payment_method": "credit_card",
            "min_amount": "6000.00",
            "max_amount": "8000.00",
            "limit": 10,
        }

        response = await client.post(
            "/api/v1/payment-processing/payments/search", json=search_data
        )

        assert response.status_code == 200
        data = response.json()

        # Should return transactions with amounts 6000 and 7000 (credit card, completed)
        assert data["total_count"] == 2
        for tx in data["transactions"]:
            assert tx["status"] == "completed"
            assert tx["payment_method"] == "credit_card"
            assert 6000 <= float(tx["amount"]) <= 8000

    @pytest.mark.asyncio
    async def test_get_payment_analytics(self, client: AsyncClient, db_session):
        """Test payment analytics endpoint"""
        # Create test data for analytics
        base_date = datetime.now(timezone.utc) - timedelta(days=7)

        transactions = [
            PaymentTransaction(
                id=uuid.uuid4(),
                transaction_id=f"pay_analytics_{i}",
                amount=Decimal(f"{1000 * (i + 1)}.00"),
                currency="JPY",
                payment_method=PaymentMethod.CREDIT_CARD
                if i % 2 == 0
                else PaymentMethod.PAYPAL,
                payment_provider=PaymentProvider.STRIPE
                if i % 3 == 0
                else PaymentProvider.PAYPAL,
                status=PaymentStatus.COMPLETED if i < 7 else PaymentStatus.FAILED,
                risk_score=10 + i * 5,
                created_at=base_date + timedelta(hours=i),
            )
            for i in range(10)
        ]

        for tx in transactions:
            db_session.add(tx)
        await db_session.commit()

        # Get analytics for the past week
        response = await client.get(
            "/api/v1/payment-processing/analytics",
            params={
                "date_from": (base_date - timedelta(days=1)).isoformat(),
                "date_to": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify analytics structure
        assert "period" in data
        assert "totals" in data
        assert "breakdown" in data

        # Verify totals
        totals = data["totals"]
        assert totals["transactions"] == 10
        assert totals["successful_transactions"] == 7
        assert totals["failed_transactions"] == 3
        assert totals["success_rate"] == 70.0
        assert totals["average_transaction_amount"] > 0

        # Verify breakdowns exist
        breakdown = data["breakdown"]
        assert "by_status" in breakdown
        assert "by_provider" in breakdown
        assert "by_payment_method" in breakdown

    @pytest.mark.asyncio
    async def test_get_payment_trends(self, client: AsyncClient):
        """Test payment trends endpoint"""
        response = await client.get(
            "/api/v1/payment-processing/analytics/trends", params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period"] == "30 days"
        assert "daily_average_transactions" in data
        assert "daily_average_revenue" in data
        assert "growth_rate" in data
        assert "forecast" in data

        forecast = data["forecast"]
        assert "next_month_transactions" in forecast
        assert "next_month_revenue" in forecast

    @pytest.mark.asyncio
    async def test_payment_webhook_handling(self, client: AsyncClient, db_session):
        """Test payment webhook processing"""
        # Create a test transaction
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_webhook_test",
            amount=Decimal("10000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.AUTHORIZED,
            provider_payment_id="stripe_payment_webhook",
        )

        db_session.add(transaction)
        await db_session.commit()

        # Mock webhook data
        webhook_data = {
            "type": "payment.completed",
            "transaction_id": transaction.transaction_id,
            "external_id": "stripe_payment_webhook",
            "amount": "10000.00",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        response = await client.post(
            "/api/v1/payment-processing/webhooks/stripe", json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "received"
        assert data["processed"] is True

    @pytest.mark.asyncio
    async def test_webhook_missing_transaction_id(self, client: AsyncClient):
        """Test webhook with missing transaction ID"""
        webhook_data = {
            "type": "payment.completed",
            "amount": "10000.00",
            # Missing transaction_id
        }

        response = await client.post(
            "/api/v1/payment-processing/webhooks/stripe", json=webhook_data
        )

        assert response.status_code == 400
        assert "Missing transaction_id" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_payment_providers(self, client: AsyncClient):
        """Test listing payment providers"""
        response = await client.get("/api/v1/payment-processing/providers")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check provider structure
        provider = data[0]
        assert "id" in provider
        assert "provider" in provider
        assert "is_active" in provider
        assert "supported_currencies" in provider
        assert "supported_payment_methods" in provider

    @pytest.mark.asyncio
    async def test_payment_health_check(self, client: AsyncClient):
        """Test payment system health check"""
        response = await client.get("/api/v1/payment-processing/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "providers" in data
        assert "database" in data
        assert "version" in data

        # Check provider health
        providers = data["providers"]
        assert len(providers) > 0

        for provider_status in providers.values():
            assert "status" in provider_status
            if provider_status["status"] == "healthy":
                assert "response_time_ms" in provider_status


class TestPaymentProcessingEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_payment_processing(self, client: AsyncClient):
        """Test concurrent payment processing"""
        import asyncio

        payment_data = {
            "amount": "5000.00",
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
        }

        # Send multiple concurrent requests
        tasks = [
            client.post("/api/v1/payment-processing/payments", json=payment_data)
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transaction_id" in data

    @pytest.mark.asyncio
    async def test_large_amount_payment(self, client: AsyncClient):
        """Test payment with very large amount"""
        payment_data = {
            "amount": "9999999.99",  # Very large amount
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
        }

        response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )

        assert response.status_code == 200
        data = response.json()

        # Large amounts should have higher risk scores
        assert data["risk_score"] > 30

    @pytest.mark.asyncio
    async def test_payment_with_special_characters(self, client: AsyncClient):
        """Test payment with special characters in description"""
        payment_data = {
            "amount": "1000.00",
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "description": "Test payment with 特殊文字 and émojis 🎉",
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
        }

        response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_refunds_exceed_amount(
        self, client: AsyncClient, db_session
    ):
        """Test multiple refunds that would exceed original amount"""
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id="pay_multi_refund",
            amount=Decimal("10000.00"),
            currency="JPY",
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_provider=PaymentProvider.STRIPE,
            status=PaymentStatus.COMPLETED,
            provider_payment_id="stripe_multi_refund",
        )

        db_session.add(transaction)
        await db_session.commit()

        # First refund - partial
        refund_data = {"amount": "7000.00", "reason": "customer_request"}
        response1 = await client.post(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}/refund",
            json=refund_data,
        )
        assert response1.status_code == 200

        # Second refund - would exceed remaining amount
        refund_data = {"amount": "5000.00", "reason": "customer_request"}
        response2 = await client.post(
            f"/api/v1/payment-processing/payments/{transaction.transaction_id}/refund",
            json=refund_data,
        )

        assert response2.status_code == 400
        assert "exceeds available amount" in response2.json()["detail"]


class TestPaymentProcessingIntegration:
    """Integration tests for payment processing"""

    @pytest.mark.asyncio
    async def test_end_to_end_payment_flow(self, client: AsyncClient):
        """Test complete payment processing flow"""
        customer_id = str(uuid.uuid4())
        order_id = "ORD-E2E-12345"

        # 1. Create payment
        payment_data = {
            "amount": "15000.00",
            "currency": "JPY",
            "payment_method": "credit_card",
            "payment_provider": "stripe",
            "customer_id": customer_id,
            "order_id": order_id,
            "description": "End-to-end test payment",
            "payment_method_info": {
                "card_number": "4111111111111111",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "card_cvv": "123",
            },
            "customer_info": {
                "email": "e2e@example.com",
                "ip_address": "192.168.1.100",
            },
        }

        create_response = await client.post(
            "/api/v1/payment-processing/payments", json=payment_data
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["success"] is True

        transaction_id = create_data["transaction_id"]

        # 2. Retrieve payment details
        get_response = await client.get(
            f"/api/v1/payment-processing/payments/{transaction_id}"
        )
        assert get_response.status_code == 200
        get_data = get_response.json()

        assert get_data["transaction_id"] == transaction_id
        assert get_data["amount"] == "15000.00"
        assert get_data["status"] == "completed"
        assert get_data["customer_id"] == customer_id
        assert get_data["order_id"] == order_id

        # 3. Search for the payment
        search_data = {"customer_id": customer_id, "order_id": order_id, "limit": 10}

        search_response = await client.post(
            "/api/v1/payment-processing/payments/search", json=search_data
        )
        assert search_response.status_code == 200
        search_results = search_response.json()

        assert search_results["total_count"] == 1
        found_payment = search_results["transactions"][0]
        assert found_payment["transaction_id"] == transaction_id

        # 4. Process partial refund
        refund_data = {
            "amount": "5000.00",
            "reason": "customer_request",
            "reason_details": "Partial refund for order adjustment",
        }

        refund_response = await client.post(
            f"/api/v1/payment-processing/payments/{transaction_id}/refund",
            json=refund_data,
        )
        assert refund_response.status_code == 200
        refund_data_response = refund_response.json()
        assert refund_data_response["success"] is True

        # 5. Verify refund reflected in payment details
        final_get_response = await client.get(
            f"/api/v1/payment-processing/payments/{transaction_id}"
        )
        assert final_get_response.status_code == 200
        final_data = final_get_response.json()

        assert final_data["status"] == "partially_refunded"
        assert len(final_data["refunds"]) == 1
        assert final_data["refunds"][0]["amount"] == "5000.00"
        assert final_data["refunds"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_analytics_accuracy(self, client: AsyncClient, db_session):
        """Test analytics calculation accuracy"""
        # Create known test data
        test_amounts = [1000, 2000, 3000, 4000, 5000]  # Total: 15000
        successful_count = 4  # First 4 successful, last one failed

        base_date = datetime.now(timezone.utc) - timedelta(days=1)

        for i, amount in enumerate(test_amounts):
            transaction = PaymentTransaction(
                id=uuid.uuid4(),
                transaction_id=f"pay_analytics_accuracy_{i}",
                amount=Decimal(str(amount)),
                currency="JPY",
                payment_method=PaymentMethod.CREDIT_CARD,
                payment_provider=PaymentProvider.STRIPE,
                status=PaymentStatus.COMPLETED
                if i < successful_count
                else PaymentStatus.FAILED,
                risk_score=20 + i * 10,
                created_at=base_date + timedelta(minutes=i * 10),
            )

            db_session.add(transaction)

        await db_session.commit()

        # Get analytics
        response = await client.get(
            "/api/v1/payment-processing/analytics",
            params={
                "date_from": (base_date - timedelta(hours=1)).isoformat(),
                "date_to": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()

        totals = data["totals"]

        # Verify calculations
        assert totals["transactions"] == 5
        assert totals["successful_transactions"] == 4
        assert totals["failed_transactions"] == 1
        assert totals["success_rate"] == 80.0  # 4/5 * 100

        # Verify amounts (successful transactions: 1000+2000+3000+4000 = 10000)
        assert totals["successful_amount"] == 10000.0
        assert totals["total_amount"] == 15000.0

        # Verify average transaction amount (15000/5 = 3000)
        assert totals["average_transaction_amount"] == 3000.0

        # Verify average risk score ((20+30+40+50+60)/5 = 40)
        assert totals["average_risk_score"] == 40.0
