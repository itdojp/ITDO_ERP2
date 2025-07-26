"""Payment Processing Service

Comprehensive payment processing service with multi-provider support,
fraud detection, automated workflows, and compliance features.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment_processing import (
    PaymentMethod,
    PaymentMethodInfo,
    PaymentProcessingLog,
    PaymentProvider,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    RefundReason,
)

logger = logging.getLogger(__name__)


@dataclass
class PaymentRequest:
    """Payment request data structure"""

    amount: Decimal
    currency: str = "JPY"
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    customer_id: Optional[uuid.UUID] = None
    order_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    # Payment method specific data
    card_token: Optional[str] = None
    card_number: Optional[str] = None  # For testing only
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    card_cvv: Optional[str] = None

    # Customer data for fraud detection
    customer_email: Optional[str] = None
    customer_ip: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None


@dataclass
class PaymentResponse:
    """Payment processing response"""

    success: bool
    transaction_id: str
    external_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: Optional[str] = None
    error_code: Optional[str] = None
    risk_score: Optional[int] = None
    requires_action: bool = False
    action_url: Optional[str] = None


class PaymentProcessingService:
    """Core payment processing service"""

    def __init__(self, db: AsyncSession) -> dict:
        self.db = db
        self.providers: Dict[PaymentProvider, "BasePaymentProvider"] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> dict:
        """Initialize payment providers"""
        # Initialize mock providers for testing
        # In production, these would be actual provider integrations
        self.providers[PaymentProvider.STRIPE] = MockStripeProvider()
        self.providers[PaymentProvider.PAYPAL] = MockPayPalProvider()
        self.providers[PaymentProvider.GMO_PAYMENT] = MockGMOProvider()

    async def process_payment(
        self,
        request: PaymentRequest,
        provider: PaymentProvider = PaymentProvider.STRIPE,
    ) -> PaymentResponse:
        """Process a payment transaction"""
        try:
            # Create transaction record
            transaction = await self._create_transaction(request, provider)

            # Fraud detection
            risk_score = await self._assess_fraud_risk(request, transaction)
            transaction.risk_score = risk_score

            if risk_score > 80:
                transaction.is_fraud_flagged = True
                transaction.fraud_reason = "High risk score detected"
                transaction.status = PaymentStatus.FAILED
                await self._log_processing_step(
                    transaction,
                    "fraud_check",
                    PaymentStatus.FAILED,
                    "Transaction blocked due to high fraud risk",
                )
                await self.db.commit()
                return PaymentResponse(
                    success=False,
                    transaction_id=transaction.transaction_id,
                    status=PaymentStatus.FAILED,
                    message="Transaction blocked due to security concerns",
                    risk_score=risk_score,
                )

            # Process with provider
            provider_client = self.providers.get(provider)
            if not provider_client:
                raise ValueError(f"Unsupported payment provider: {provider}")

            # Authorization phase
            auth_result = await provider_client.authorize_payment(request)
            transaction.provider_payment_id = auth_result.get("payment_id")
            transaction.provider_response = auth_result

            if auth_result.get("success", False):
                transaction.status = PaymentStatus.AUTHORIZED
                transaction.authorized_at = datetime.now(timezone.utc)

                # Auto-capture for most transactions
                if request.amount < Decimal("100000"):  # Auto-capture under 100,000 JPY
                    capture_result = await provider_client.capture_payment(
                        auth_result.get("payment_id"), request.amount
                    )

                    if capture_result.get("success", False):
                        transaction.status = PaymentStatus.CAPTURED
                        transaction.captured_at = datetime.now(timezone.utc)

                        # Complete the transaction
                        transaction.status = PaymentStatus.COMPLETED
                        transaction.completed_at = datetime.now(timezone.utc)
                    else:
                        transaction.status = PaymentStatus.FAILED
                        transaction.failure_code = capture_result.get("error_code")
                        transaction.failure_message = capture_result.get(
                            "error_message"
                        )
            else:
                transaction.status = PaymentStatus.FAILED
                transaction.failed_at = datetime.now(timezone.utc)
                transaction.failure_code = auth_result.get("error_code")
                transaction.failure_message = auth_result.get("error_message")

            # Save payment method info
            if request.card_token or request.card_number:
                await self._save_payment_method_info(transaction, request, auth_result)

            # Log processing step
            await self._log_processing_step(
                transaction,
                "payment_processing",
                transaction.status,
                f"Payment processed with {provider}",
            )

            await self.db.commit()

            return PaymentResponse(
                success=transaction.status == PaymentStatus.COMPLETED,
                transaction_id=transaction.transaction_id,
                external_id=transaction.provider_payment_id,
                status=transaction.status,
                message=transaction.failure_message
                if transaction.status == PaymentStatus.FAILED
                else "Payment successful",
                error_code=transaction.failure_code,
                risk_score=risk_score,
            )

        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            await self.db.rollback()
            raise

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: RefundReason = RefundReason.CUSTOMER_REQUEST,
        reason_details: Optional[str] = None,
    ) -> PaymentResponse:
        """Process a payment refund"""
        try:
            # Get original transaction
            result = await self.db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.transaction_id == transaction_id)
                .options(selectinload(PaymentTransaction.refunds))
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            if transaction.status != PaymentStatus.COMPLETED:
                raise ValueError("Can only refund completed transactions")

            # Calculate refund amount
            if amount is None:
                amount = transaction.amount

            # Check available refund amount
            total_refunded = sum(
                refund.amount
                for refund in transaction.refunds
                if refund.status == PaymentStatus.COMPLETED
            )

            if total_refunded + amount > transaction.amount:
                raise ValueError("Refund amount exceeds available amount")

            # Create refund record
            refund = PaymentRefund(
                id=uuid.uuid4(),
                transaction_id=transaction.id,
                refund_id=f"ref_{uuid.uuid4().hex[:12]}",
                amount=amount,
                currency=transaction.currency,
                reason=reason,
                reason_details=reason_details,
                status=PaymentStatus.PENDING,
            )

            self.db.add(refund)

            # Process refund with provider
            provider_client = self.providers.get(transaction.payment_provider)
            if provider_client:
                refund_result = await provider_client.refund_payment(
                    transaction.provider_payment_id, amount
                )

                refund.external_refund_id = refund_result.get("refund_id")
                refund.provider_response = refund_result

                if refund_result.get("success", False):
                    refund.status = PaymentStatus.COMPLETED
                    refund.processed_at = datetime.now(timezone.utc)

                    # Update transaction status
                    if total_refunded + amount >= transaction.amount:
                        transaction.status = PaymentStatus.REFUNDED
                    else:
                        transaction.status = PaymentStatus.PARTIALLY_REFUNDED
                else:
                    refund.status = PaymentStatus.FAILED

            await self.db.commit()

            return PaymentResponse(
                success=refund.status == PaymentStatus.COMPLETED,
                transaction_id=refund.refund_id,
                external_id=refund.external_refund_id,
                status=refund.status,
                message="Refund processed successfully"
                if refund.status == PaymentStatus.COMPLETED
                else "Refund failed",
            )

        except Exception as e:
            logger.error(f"Refund processing error: {str(e)}")
            await self.db.rollback()
            raise

    async def get_payment_status(
        self, transaction_id: str
    ) -> Optional[PaymentTransaction]:
        """Get payment transaction status"""
        result = await self.db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_id == transaction_id)
            .options(
                selectinload(PaymentTransaction.payment_method_info),
                selectinload(PaymentTransaction.refunds),
                selectinload(PaymentTransaction.processing_logs),
            )
        )
        return result.scalar_one_or_none()

    async def search_transactions(
        self,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        provider: Optional[PaymentProvider] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[PaymentTransaction], int]:
        """Search payment transactions with filters"""
        query = select(PaymentTransaction).options(
            selectinload(PaymentTransaction.payment_method_info),
            selectinload(PaymentTransaction.refunds),
        )
        count_query = select(func.count(PaymentTransaction.id))

        # Apply filters
        conditions = []

        if customer_id:
            conditions.append(PaymentTransaction.customer_id == customer_id)

        if status:
            conditions.append(PaymentTransaction.status == status)

        if payment_method:
            conditions.append(PaymentTransaction.payment_method == payment_method)

        if provider:
            conditions.append(PaymentTransaction.payment_provider == provider)

        if date_from:
            conditions.append(PaymentTransaction.created_at >= date_from)

        if date_to:
            conditions.append(PaymentTransaction.created_at <= date_to)

        if min_amount:
            conditions.append(PaymentTransaction.amount >= min_amount)

        if max_amount:
            conditions.append(PaymentTransaction.amount <= max_amount)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(PaymentTransaction.created_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total_count

    async def get_payment_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        provider: Optional[PaymentProvider] = None,
    ) -> Dict[str, Any]:
        """Get payment analytics and metrics"""
        # Default to last 30 days if no dates provided
        if not date_from:
            date_from = datetime.now(timezone.utc) - timedelta(days=30)
        if not date_to:
            date_to = datetime.now(timezone.utc)

        conditions = [
            PaymentTransaction.created_at >= date_from,
            PaymentTransaction.created_at <= date_to,
        ]

        if provider:
            conditions.append(PaymentTransaction.payment_provider == provider)

        # Basic metrics
        metrics_query = select(
            func.count(PaymentTransaction.id).label("total_transactions"),
            func.count()
            .filter(PaymentTransaction.status == PaymentStatus.COMPLETED)
            .label("successful_transactions"),
            func.count()
            .filter(PaymentTransaction.status == PaymentStatus.FAILED)
            .label("failed_transactions"),
            func.sum(PaymentTransaction.amount).label("total_amount"),
            func.sum(PaymentTransaction.amount)
            .filter(PaymentTransaction.status == PaymentStatus.COMPLETED)
            .label("successful_amount"),
            func.avg(PaymentTransaction.risk_score).label("avg_risk_score"),
        ).where(and_(*conditions))

        result = await self.db.execute(metrics_query)
        metrics = result.first()

        # Status breakdown
        status_query = (
            select(
                PaymentTransaction.status,
                func.count(PaymentTransaction.id).label("count"),
                func.sum(PaymentTransaction.amount).label("amount"),
            )
            .where(and_(*conditions))
            .group_by(PaymentTransaction.status)
        )

        status_result = await self.db.execute(status_query)
        status_breakdown = {
            row.status: {"count": row.count, "amount": float(row.amount or 0)}
            for row in status_result
        }

        # Provider breakdown
        provider_query = (
            select(
                PaymentTransaction.payment_provider,
                func.count(PaymentTransaction.id).label("count"),
                func.sum(PaymentTransaction.amount).label("amount"),
            )
            .where(and_(*conditions))
            .group_by(PaymentTransaction.payment_provider)
        )

        provider_result = await self.db.execute(provider_query)
        provider_breakdown = {
            row.payment_provider: {"count": row.count, "amount": float(row.amount or 0)}
            for row in provider_result
        }

        # Payment method breakdown
        method_query = (
            select(
                PaymentTransaction.payment_method,
                func.count(PaymentTransaction.id).label("count"),
                func.sum(PaymentTransaction.amount).label("amount"),
            )
            .where(and_(*conditions))
            .group_by(PaymentTransaction.payment_method)
        )

        method_result = await self.db.execute(method_query)
        method_breakdown = {
            row.payment_method: {"count": row.count, "amount": float(row.amount or 0)}
            for row in method_result
        }

        return {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "totals": {
                "transactions": metrics.total_transactions or 0,
                "successful_transactions": metrics.successful_transactions or 0,
                "failed_transactions": metrics.failed_transactions or 0,
                "total_amount": float(metrics.total_amount or 0),
                "successful_amount": float(metrics.successful_amount or 0),
                "success_rate": float(
                    (metrics.successful_transactions or 0)
                    / max(metrics.total_transactions or 1, 1)
                    * 100
                ),
                "average_risk_score": float(metrics.avg_risk_score or 0),
            },
            "breakdown": {
                "by_status": status_breakdown,
                "by_provider": provider_breakdown,
                "by_payment_method": method_breakdown,
            },
        }

    async def _create_transaction(
        self, request: PaymentRequest, provider: PaymentProvider
    ) -> PaymentTransaction:
        """Create a new payment transaction record"""
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            transaction_id=f"pay_{uuid.uuid4().hex[:12]}",
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            payment_provider=provider,
            customer_id=request.customer_id,
            order_id=request.order_id,
            description=request.description,
            extra_data=request.metadata or {},
            status=PaymentStatus.PENDING,
        )

        self.db.add(transaction)
        await self.db.flush()  # Get the ID

        return transaction

    async def _assess_fraud_risk(
        self, request: PaymentRequest, transaction: PaymentTransaction
    ) -> int:
        """Assess fraud risk for a payment (0-100 scale)"""
        risk_score = 0

        # Amount-based risk
        if request.amount > Decimal("500000"):  # > 500,000 JPY
            risk_score += 30
        elif request.amount > Decimal("100000"):  # > 100,000 JPY
            risk_score += 15

        # Check for suspicious patterns (mock implementation)
        if request.customer_id:
            # Check recent failed transactions
            recent_failures = await self.db.execute(
                select(func.count(PaymentTransaction.id)).where(
                    and_(
                        PaymentTransaction.customer_id == request.customer_id,
                        PaymentTransaction.status == PaymentStatus.FAILED,
                        PaymentTransaction.created_at
                        >= datetime.now(timezone.utc) - timedelta(hours=1),
                    )
                )
            )

            failure_count = recent_failures.scalar() or 0
            if failure_count > 3:
                risk_score += 40
            elif failure_count > 1:
                risk_score += 20

        # IP-based risk (mock)
        if request.customer_ip:
            if request.customer_ip.startswith("10.0.0"):  # Mock suspicious IP range
                risk_score += 25

        # Random risk for testing
        import random

        risk_score += random.randint(0, 10)

        return min(risk_score, 100)

    async def _save_payment_method_info(
        self,
        transaction: PaymentTransaction,
        request: PaymentRequest,
        provider_response: Dict[str, Any],
    ):
        """Save secure payment method information"""
        payment_method_info = PaymentMethodInfo(
            id=uuid.uuid4(),
            transaction_id=transaction.id,
            payment_token=provider_response.get("payment_token"),
            three_d_secure_used=provider_response.get("3ds_used", False),
            cvv_verified=provider_response.get("cvv_verified", False),
            address_verified=provider_response.get("address_verified", False),
        )

        # Save card info securely (last 4 digits only)
        if request.card_number:
            payment_method_info.card_last_four = request.card_number[-4:]
            payment_method_info.card_exp_month = request.card_exp_month
            payment_method_info.card_exp_year = request.card_exp_year
            payment_method_info.card_brand = provider_response.get(
                "card_brand", "unknown"
            )
            payment_method_info.card_type = provider_response.get("card_type", "credit")

        self.db.add(payment_method_info)

    async def _log_processing_step(
        self,
        transaction: PaymentTransaction,
        action: str,
        status: PaymentStatus,
        message: Optional[str] = None,
        provider_request: Optional[Dict] = None,
        provider_response: Optional[Dict] = None,
    ):
        """Log a payment processing step"""
        log_entry = PaymentProcessingLog(
            id=uuid.uuid4(),
            transaction_id=transaction.id,
            action=action,
            status=status.value,
            message=message,
            provider_request=provider_request,
            provider_response=provider_response,
        )

        self.db.add(log_entry)


# Mock payment provider implementations for testing
class BasePaymentProvider:
    """Base payment provider interface"""

    async def authorize_payment(self, request: PaymentRequest) -> Dict[str, Any]:
        """Authorize a payment"""
        raise NotImplementedError

    async def capture_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        """Capture an authorized payment"""
        raise NotImplementedError

    async def refund_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        """Refund a payment"""
        raise NotImplementedError


class MockStripeProvider(BasePaymentProvider):
    """Mock Stripe provider for testing"""

    async def authorize_payment(self, request: PaymentRequest) -> Dict[str, Any]:
        # Simulate processing delay
        await asyncio.sleep(0.1)

        # Mock success/failure based on card number
        if request.card_number and request.card_number.endswith("0000"):
            return {
                "success": False,
                "error_code": "card_declined",
                "error_message": "Your card was declined.",
            }

        return {
            "success": True,
            "payment_id": f"stripe_{uuid.uuid4().hex[:16]}",
            "payment_token": f"tok_{uuid.uuid4().hex[:24]}",
            "card_brand": "visa"
            if request.card_number and request.card_number.startswith("4")
            else "mastercard",
            "card_type": "credit",
            "3ds_used": True,
            "cvv_verified": True,
            "address_verified": False,
        }

    async def capture_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "success": True,
            "capture_id": f"cap_{uuid.uuid4().hex[:16]}",
            "captured_amount": float(amount),
        }

    async def refund_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "refund_id": f"ref_{uuid.uuid4().hex[:16]}",
            "refunded_amount": float(amount),
        }


class MockPayPalProvider(BasePaymentProvider):
    """Mock PayPal provider for testing"""

    async def authorize_payment(self, request: PaymentRequest) -> Dict[str, Any]:
        await asyncio.sleep(0.15)
        return {
            "success": True,
            "payment_id": f"paypal_{uuid.uuid4().hex[:16]}",
            "payment_token": f"EC-{uuid.uuid4().hex[:20].upper()}",
            "payer_email": request.customer_email or "customer@example.com",
        }

    async def capture_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "capture_id": f"cap_{uuid.uuid4().hex[:16]}",
            "captured_amount": float(amount),
        }

    async def refund_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.12)
        return {
            "success": True,
            "refund_id": f"ref_{uuid.uuid4().hex[:16]}",
            "refunded_amount": float(amount),
        }


class MockGMOProvider(BasePaymentProvider):
    """Mock GMO Payment provider for testing"""

    async def authorize_payment(self, request: PaymentRequest) -> Dict[str, Any]:
        await asyncio.sleep(0.08)
        return {
            "success": True,
            "payment_id": f"gmo_{uuid.uuid4().hex[:16]}",
            "payment_token": f"GMO{uuid.uuid4().hex[:20].upper()}",
            "card_brand": "jcb"
            if request.card_number and request.card_number.startswith("35")
            else "visa",
            "card_type": "credit",
        }

    async def capture_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.06)
        return {
            "success": True,
            "capture_id": f"cap_{uuid.uuid4().hex[:16]}",
            "captured_amount": float(amount),
        }

    async def refund_payment(self, payment_id: str, amount: Decimal) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "refund_id": f"ref_{uuid.uuid4().hex[:16]}",
            "refunded_amount": float(amount),
        }
