"""
ITDO ERP Backend - Customer Management v70 Tests
Comprehensive test suite for customer relationship management functionality
Day 12: Customer Management Test Implementation
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.v1.customer_management_v70 import (
    CustomerManagementService,
    CustomerSegment,
    CustomerStatus,
    CustomerType,
    TicketPriority,
    TicketStatus,
)
from app.main import app


class TestCustomerManagement:
    """Test customer management functionality"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_db(self):
        with patch("app.core.database.get_db") as mock:
            yield mock

    @pytest.fixture
    def mock_redis(self):
        with patch("aioredis.from_url") as mock:
            redis_client = AsyncMock()
            mock.return_value = redis_client
            yield redis_client

    async def test_create_customer_individual(self, async_client, mock_db, mock_redis):
        """Test individual customer creation"""
        customer_data = {
            "name": "John Smith",
            "customer_type": "individual",
            "status": "active",
            "segment": "standard",
            "preferred_language": "en",
            "preferred_communication": "email",
            "acquisition_source": "website",
            "contacts": [
                {
                    "contact_type": "primary",
                    "first_name": "John",
                    "last_name": "Smith",
                    "email": "john.smith@example.com",
                    "phone": "+1-555-123-4567",
                    "is_primary": True,
                    "preferred_contact_method": "email",
                }
            ],
            "addresses": [
                {
                    "address_type": "billing",
                    "address_line1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                    "is_primary": True,
                }
            ],
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.create_customer"
        ) as mock_create:
            mock_customer = Mock(
                id=uuid.uuid4(),
                customer_number="CUST-20241126-000001",
                name="John Smith",
                customer_type=CustomerType.INDIVIDUAL,
                status=CustomerStatus.ACTIVE,
                segment=CustomerSegment.STANDARD,
                total_orders=Decimal("0"),
                total_revenue=Decimal("0"),
                average_order_value=Decimal("0"),
                lifetime_value=Decimal("0"),
                last_order_date=None,
                acquisition_date=datetime.utcnow(),
                risk_score=Decimal("0"),
                compliance_status="compliant",
                kyc_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            mock_create.return_value = mock_customer

            response = await async_client.post("/api/v1/customers/", json=customer_data)

            assert response.status_code == 200
            result = response.json()
            assert result["name"] == "John Smith"
            assert result["customer_type"] == "individual"
            assert result["status"] == "active"

    async def test_create_customer_business(self, async_client, mock_db, mock_redis):
        """Test business customer creation"""
        customer_data = {
            "name": "Acme Corporation",
            "legal_name": "Acme Corporation Ltd.",
            "customer_type": "business",
            "status": "active",
            "segment": "enterprise",
            "tax_id": "TAX123456789",
            "business_registration": "REG987654321",
            "industry": "Manufacturing",
            "website": "https://acme.com",
            "credit_limit": 50000.00,
            "payment_terms": "net_30",
            "contacts": [
                {
                    "contact_type": "primary",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "title": "Purchasing Manager",
                    "department": "Procurement",
                    "email": "jane.doe@acme.com",
                    "phone": "+1-555-987-6543",
                    "is_primary": True,
                }
            ],
            "addresses": [
                {
                    "address_type": "billing",
                    "address_line1": "456 Business Ave",
                    "address_line2": "Suite 100",
                    "city": "Chicago",
                    "state": "IL",
                    "postal_code": "60601",
                    "country": "USA",
                    "is_primary": True,
                }
            ],
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.create_customer"
        ) as mock_create:
            mock_customer = Mock(
                id=uuid.uuid4(),
                customer_number="CUST-20241126-000002",
                name="Acme Corporation",
                customer_type=CustomerType.BUSINESS,
                status=CustomerStatus.ACTIVE,
                segment=CustomerSegment.ENTERPRISE,
                total_orders=Decimal("0"),
                total_revenue=Decimal("0"),
                average_order_value=Decimal("0"),
                lifetime_value=Decimal("0"),
                last_order_date=None,
                acquisition_date=datetime.utcnow(),
                risk_score=Decimal("0"),
                compliance_status="compliant",
                kyc_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            mock_create.return_value = mock_customer

            response = await async_client.post("/api/v1/customers/", json=customer_data)

            assert response.status_code == 200
            result = response.json()
            assert result["name"] == "Acme Corporation"
            assert result["customer_type"] == "business"
            assert result["segment"] == "enterprise"

    async def test_get_customers_with_filters(self, async_client, mock_db, mock_redis):
        """Test customer retrieval with filtering"""
        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.get_customers"
        ) as mock_get:
            mock_customers = [
                Mock(
                    id=uuid.uuid4(),
                    customer_number="CUST-001",
                    name="Premium Customer 1",
                    status=CustomerStatus.ACTIVE,
                    segment=CustomerSegment.PREMIUM,
                    customer_type=CustomerType.BUSINESS,
                    total_revenue=Decimal("15000.00"),
                ),
                Mock(
                    id=uuid.uuid4(),
                    customer_number="CUST-002",
                    name="Premium Customer 2",
                    status=CustomerStatus.ACTIVE,
                    segment=CustomerSegment.PREMIUM,
                    customer_type=CustomerType.INDIVIDUAL,
                    total_revenue=Decimal("8000.00"),
                ),
            ]

            mock_get.return_value = {
                "customers": mock_customers,
                "total": 2,
                "skip": 0,
                "limit": 100,
            }

            response = await async_client.get(
                "/api/v1/customers/",
                params={"status": "active", "segment": "premium", "search": "Premium"},
            )

            assert response.status_code == 200
            result = response.json()
            assert result["total"] == 2
            assert len(result["customers"]) == 2
            assert all(
                "Premium" in customer["name"] for customer in result["customers"]
            )

    async def test_update_customer(self, async_client, mock_db, mock_redis):
        """Test customer information update"""
        customer_id = uuid.uuid4()
        update_data = {
            "name": "Updated Customer Name",
            "status": "inactive",
            "segment": "vip",
            "credit_limit": 75000.00,
            "notes": "Updated customer notes",
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.update_customer"
        ) as mock_update:
            mock_customer = Mock(
                id=customer_id,
                name="Updated Customer Name",
                status=CustomerStatus.INACTIVE,
                segment=CustomerSegment.VIP,
                credit_limit=Decimal("75000.00"),
                notes="Updated customer notes",
            )
            mock_update.return_value = mock_customer

            response = await async_client.put(
                f"/api/v1/customers/{customer_id}", json=update_data
            )

            assert response.status_code == 200
            result = response.json()
            assert result["name"] == "Updated Customer Name"
            assert result["status"] == "inactive"
            assert result["segment"] == "vip"


class TestSupportTicketManagement:
    """Test customer support ticket management"""

    @pytest.fixture
    def customer_service(self, mock_db, mock_redis):
        return CustomerManagementService(mock_db, mock_redis)

    async def test_create_support_ticket(self, customer_service):
        """Test support ticket creation"""
        customer_id = uuid.uuid4()
        ticket_data = Mock(
            customer_id=customer_id,
            subject="Unable to login to account",
            description="Customer is experiencing login issues after password reset",
            category="technical",
            subcategory="authentication",
            priority=TicketPriority.HIGH,
            reported_by="customer_service@company.com",
        )

        # Mock customer validation
        with patch.object(customer_service.db, "get") as mock_get:
            mock_customer = Mock(id=customer_id, name="Test Customer")
            mock_get.return_value = mock_customer

            # Mock Redis counter
            customer_service.redis.incr = AsyncMock(return_value=1)
            customer_service.redis.expire = AsyncMock()

            with patch.object(customer_service.db, "add") as mock_add:
                with patch.object(customer_service.db, "commit") as mock_commit:
                    with patch.object(customer_service.db, "refresh") as mock_refresh:
                        await customer_service.create_support_ticket(ticket_data)

                        assert mock_add.call_count >= 2  # Ticket + initial interaction
                        assert mock_commit.call_count == 2
                        assert mock_refresh.called

    async def test_update_ticket_status(self, customer_service):
        """Test support ticket status update"""
        ticket_id = uuid.uuid4()
        new_status = TicketStatus.RESOLVED
        updated_by = "support_agent@company.com"
        notes = "Issue resolved by resetting user password"

        with patch.object(customer_service.db, "get") as mock_get:
            mock_ticket = Mock(
                id=ticket_id,
                status=TicketStatus.IN_PROGRESS,
                created_at=datetime.utcnow() - timedelta(hours=2),
            )
            mock_get.return_value = mock_ticket

            with patch.object(customer_service.db, "add") as mock_add:
                with patch.object(customer_service.db, "commit") as mock_commit:
                    with patch.object(customer_service.db, "refresh"):
                        await customer_service.update_ticket_status(
                            ticket_id, new_status, updated_by, notes
                        )

                        assert mock_ticket.status == TicketStatus.RESOLVED
                        assert mock_ticket.resolved_at is not None
                        assert mock_ticket.resolution_time is not None
                        assert mock_add.called  # For status change interaction
                        assert mock_commit.called

    async def test_add_ticket_interaction(self, customer_service):
        """Test adding interaction to support ticket"""
        ticket_id = uuid.uuid4()
        interaction_data = Mock(
            interaction_type="note",
            content="Customer confirmed the issue is resolved",
            is_internal=False,
            created_by="customer@example.com",
            created_by_type="customer",
        )

        with patch.object(customer_service.db, "get") as mock_get:
            mock_ticket = Mock(id=ticket_id)
            mock_get.return_value = mock_ticket

            with patch.object(customer_service.db, "add") as mock_add:
                with patch.object(customer_service.db, "commit") as mock_commit:
                    with patch.object(customer_service.db, "refresh") as mock_refresh:
                        await customer_service.add_ticket_interaction(
                            ticket_id, interaction_data
                        )

                        assert mock_add.called
                        assert mock_commit.called
                        assert mock_refresh.called
                        assert mock_ticket.updated_at is not None

    async def test_create_ticket_invalid_customer(self, customer_service):
        """Test ticket creation with invalid customer"""
        ticket_data = Mock(customer_id=uuid.uuid4())

        with patch.object(customer_service.db, "get") as mock_get:
            mock_get.return_value = None  # Customer not found

            with pytest.raises(Exception):  # Should raise HTTPException
                await customer_service.create_support_ticket(ticket_data)


class TestLoyaltyProgramManagement:
    """Test loyalty program management"""

    @pytest.fixture
    def customer_service(self, mock_db, mock_redis):
        return CustomerManagementService(mock_db, mock_redis)

    async def test_create_loyalty_tier(self, customer_service):
        """Test loyalty tier creation"""
        tier_data = Mock(
            name="Gold Tier",
            description="Premium tier for valued customers",
            minimum_points=Decimal("1000"),
            minimum_spending=Decimal("5000.00"),
            minimum_orders=Decimal("10"),
            points_multiplier=Decimal("1.5"),
            discount_percentage=Decimal("10.0"),
            free_shipping=True,
            priority_support=True,
            is_active=True,
            sort_order=Decimal("2"),
        )

        # Mock tier name uniqueness check
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = None

            with patch.object(customer_service.db, "add") as mock_add:
                with patch.object(customer_service.db, "commit") as mock_commit:
                    with patch.object(customer_service.db, "refresh") as mock_refresh:
                        await customer_service.create_loyalty_tier(tier_data)

                        assert mock_add.called
                        assert mock_commit.called
                        assert mock_refresh.called

    async def test_create_duplicate_loyalty_tier(self, customer_service):
        """Test creating loyalty tier with duplicate name"""
        tier_data = Mock(name="Existing Tier")

        with patch.object(customer_service.db, "execute") as mock_execute:
            # Mock existing tier found
            mock_execute.return_value.scalar_one_or_none.return_value = Mock(
                name="Existing Tier"
            )

            with pytest.raises(Exception):  # Should raise HTTPException
                await customer_service.create_loyalty_tier(tier_data)

    async def test_process_loyalty_transaction_earn(self, customer_service):
        """Test processing loyalty points earning transaction"""
        customer_id = uuid.uuid4()
        transaction_data = Mock(
            customer_id=customer_id,
            transaction_type="earned",
            points=Decimal("100"),
            reference_type="order",
            reference_id="ORDER-001",
            description="Points earned from purchase",
            processed_by="system",
        )

        # Mock existing loyalty account
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_account = Mock(
                id=uuid.uuid4(),
                customer_id=customer_id,
                current_points=Decimal("500"),
                lifetime_points_earned=Decimal("2000"),
                lifetime_points_redeemed=Decimal("300"),
                tier_points=Decimal("700"),
                tier=Mock(name="Silver"),
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_account

            with patch.object(
                customer_service, "_check_tier_upgrade"
            ) as mock_tier_check:
                with patch.object(customer_service.db, "add") as mock_add:
                    with patch.object(customer_service.db, "commit") as mock_commit:
                        with patch.object(customer_service.db, "refresh"):
                            result = await customer_service.process_loyalty_transaction(
                                transaction_data
                            )

                            assert result["new_balance"] == Decimal("600")  # 500 + 100
                            assert result["account_tier"] == "Silver"
                            assert mock_account.current_points == Decimal("600")
                            assert mock_account.lifetime_points_earned == Decimal(
                                "2100"
                            )
                            assert mock_tier_check.called
                            assert mock_add.called
                            assert mock_commit.called

    async def test_process_loyalty_transaction_redeem(self, customer_service):
        """Test processing loyalty points redemption transaction"""
        customer_id = uuid.uuid4()
        transaction_data = Mock(
            customer_id=customer_id,
            transaction_type="redeemed",
            points=Decimal("-200"),  # Negative for redemption
            reference_type="discount",
            reference_id="DISC-001",
            description="Points redeemed for discount",
            processed_by="customer_service",
        )

        # Mock existing loyalty account with sufficient points
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_account = Mock(
                id=uuid.uuid4(),
                customer_id=customer_id,
                current_points=Decimal("500"),
                lifetime_points_earned=Decimal("2000"),
                lifetime_points_redeemed=Decimal("300"),
                tier_points=Decimal("700"),
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_account

            with patch.object(customer_service, "_check_tier_upgrade"):
                with patch.object(customer_service.db, "add"):
                    with patch.object(customer_service.db, "commit"):
                        result = await customer_service.process_loyalty_transaction(
                            transaction_data
                        )

                        assert result["new_balance"] == Decimal("300")  # 500 - 200
                        assert mock_account.current_points == Decimal("300")
                        assert mock_account.lifetime_points_redeemed == Decimal(
                            "500"
                        )  # 300 + 200

    async def test_process_loyalty_transaction_insufficient_points(
        self, customer_service
    ):
        """Test redemption with insufficient points"""
        customer_id = uuid.uuid4()
        transaction_data = Mock(
            customer_id=customer_id,
            transaction_type="redeemed",
            points=Decimal("-1000"),  # More than available
        )

        # Mock account with insufficient points
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_account = Mock(current_points=Decimal("100"))
            mock_execute.return_value.scalar_one_or_none.return_value = mock_account

            with pytest.raises(Exception):  # Should raise HTTPException
                await customer_service.process_loyalty_transaction(transaction_data)

    async def test_initialize_loyalty_account(self, customer_service):
        """Test loyalty account initialization"""
        customer_id = uuid.uuid4()

        # Mock default tier selection
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_tier = Mock(id=uuid.uuid4(), name="Bronze")
            mock_execute.return_value.scalars.return_value.first.return_value = (
                mock_tier
            )

            with patch.object(customer_service.db, "add") as mock_add:
                with patch.object(customer_service.db, "commit") as mock_commit:
                    with patch.object(customer_service.db, "refresh") as mock_refresh:
                        await customer_service._initialize_loyalty_account(customer_id)

                        assert mock_add.called
                        assert mock_commit.called
                        assert mock_refresh.called


class TestCustomerAnalytics:
    """Test customer analytics functionality"""

    @pytest.fixture
    def customer_service(self, mock_db, mock_redis):
        return CustomerManagementService(mock_db, mock_redis)

    async def test_generate_rfm_analysis(self, customer_service):
        """Test RFM (Recency, Frequency, Monetary) analysis"""
        request = Mock(
            customer_ids=None,
            segments=[CustomerSegment.PREMIUM, CustomerSegment.VIP],
            analytics_type="rfm",
            include_predictions=True,
        )

        # Mock customer data
        mock_customers = [
            Mock(
                id=uuid.uuid4(),
                name="High Value Customer",
                total_revenue=Decimal("10000.00"),
                total_orders=Decimal("15"),
                last_order_date=datetime.utcnow() - timedelta(days=10),
            ),
            Mock(
                id=uuid.uuid4(),
                name="Medium Value Customer",
                total_revenue=Decimal("3000.00"),
                total_orders=Decimal("8"),
                last_order_date=datetime.utcnow() - timedelta(days=45),
            ),
            Mock(
                id=uuid.uuid4(),
                name="At Risk Customer",
                total_revenue=Decimal("1500.00"),
                total_orders=Decimal("3"),
                last_order_date=datetime.utcnow() - timedelta(days=200),
            ),
        ]

        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_execute.return_value.scalars.return_value.all.return_value = (
                mock_customers
            )

            analytics = await customer_service.generate_customer_analytics(request)

            assert analytics["analytics_type"] == "rfm"
            assert analytics["total_customers"] == 3
            assert "summary" in analytics
            assert "segments" in analytics
            assert "recommendations" in analytics
            assert analytics["summary"]["high_value_customers"] > 0

    async def test_generate_churn_analysis(self, customer_service):
        """Test customer churn analysis"""
        request = Mock(analytics_type="churn", include_predictions=True)

        mock_customers = [
            Mock(
                last_order_date=datetime.utcnow() - timedelta(days=200)  # High risk
            ),
            Mock(
                last_order_date=datetime.utcnow() - timedelta(days=100)  # Medium risk
            ),
            Mock(
                last_order_date=datetime.utcnow() - timedelta(days=30)  # Low risk
            ),
        ]

        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_execute.return_value.scalars.return_value.all.return_value = (
                mock_customers
            )

            analytics = await customer_service.generate_customer_analytics(request)

            assert analytics["analytics_type"] == "churn"
            assert analytics["summary"]["high_risk"] == 1
            assert analytics["summary"]["medium_risk"] == 1
            assert analytics["summary"]["low_risk"] == 1
            assert len(analytics["recommendations"]) > 0

    async def test_generate_ltv_analysis(self, customer_service):
        """Test lifetime value analysis"""
        request = Mock(analytics_type="ltv", include_predictions=True)

        mock_customers = [
            Mock(lifetime_value=Decimal("15000.00")),  # High LTV
            Mock(lifetime_value=Decimal("5000.00")),  # Medium LTV
            Mock(lifetime_value=Decimal("1000.00")),  # Low LTV
            Mock(lifetime_value=Decimal("8000.00")),  # Medium LTV
        ]

        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_execute.return_value.scalars.return_value.all.return_value = (
                mock_customers
            )

            analytics = await customer_service.generate_customer_analytics(request)

            assert analytics["analytics_type"] == "ltv"
            assert analytics["summary"]["total_ltv"] == Decimal("29000.00")
            assert analytics["summary"]["average_ltv"] == Decimal("7250.00")
            assert "segments" in analytics
            assert len(analytics["recommendations"]) > 0

    async def test_update_customer_analytics(self, customer_service):
        """Test customer analytics update"""
        customer_id = uuid.uuid4()

        with patch.object(customer_service.db, "get") as mock_get:
            mock_customer = Mock(
                id=customer_id,
                total_orders=Decimal("0"),
                total_revenue=Decimal("0"),
                segment=CustomerSegment.STANDARD,
            )
            mock_get.return_value = mock_customer

            with patch.object(
                customer_service, "_get_customer_order_count"
            ) as mock_orders:
                with patch.object(
                    customer_service, "_get_customer_total_revenue"
                ) as mock_revenue:
                    with patch.object(
                        customer_service, "_get_customer_last_order_date"
                    ) as mock_date:
                        with patch.object(
                            customer_service, "_update_customer_segment"
                        ) as mock_segment:
                            mock_orders.return_value = Decimal("5")
                            mock_revenue.return_value = Decimal("2500.00")
                            mock_date.return_value = datetime.utcnow() - timedelta(
                                days=30
                            )

                            with patch.object(
                                customer_service.db, "commit"
                            ) as mock_commit:
                                await customer_service.update_customer_analytics(
                                    customer_id
                                )

                                assert mock_customer.total_orders == Decimal("5")
                                assert mock_customer.total_revenue == Decimal("2500.00")
                                assert mock_customer.average_order_value == Decimal(
                                    "500.00"
                                )
                                assert mock_customer.lifetime_value == Decimal(
                                    "3000.00"
                                )  # 2500 * 1.2
                                assert mock_segment.called
                                assert mock_commit.called


class TestHelperMethods:
    """Test helper methods and utilities"""

    @pytest.fixture
    def customer_service(self, mock_db, mock_redis):
        return CustomerManagementService(mock_db, mock_redis)

    async def test_generate_customer_number(self, customer_service):
        """Test customer number generation"""
        customer_service.redis.incr = AsyncMock(return_value=5)
        customer_service.redis.expire = AsyncMock()

        customer_number = await customer_service._generate_customer_number()

        today = datetime.utcnow().strftime("%Y%m%d")
        expected = f"CUST-{today}-000005"
        assert customer_number == expected

    async def test_generate_ticket_number(self, customer_service):
        """Test ticket number generation"""
        customer_service.redis.incr = AsyncMock(return_value=3)
        customer_service.redis.expire = AsyncMock()

        ticket_number = await customer_service._generate_ticket_number()

        today = datetime.utcnow().strftime("%Y%m%d")
        expected = f"TKT-{today}-000003"
        assert ticket_number == expected

    async def test_cache_customer(self, customer_service):
        """Test customer caching"""
        customer = Mock(
            id=uuid.uuid4(),
            customer_number="CUST-001",
            name="Test Customer",
            status=CustomerStatus.ACTIVE,
            segment=CustomerSegment.PREMIUM,
        )

        customer_service.redis.setex = AsyncMock()

        await customer_service._cache_customer(customer)

        customer_service.redis.setex.assert_called_once()
        call_args = customer_service.redis.setex.call_args
        assert call_args[0][0] == f"customer:{customer.id}"
        assert call_args[0][1] == 3600  # 1 hour

    async def test_check_tier_upgrade(self, customer_service):
        """Test loyalty tier upgrade check"""
        account_id = uuid.uuid4()
        account = Mock(id=account_id, tier_points=Decimal("1500"), tier_id=None)

        # Mock tiers query
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_tiers = [
                Mock(
                    id=uuid.uuid4(), minimum_points=Decimal("2000")
                ),  # Gold - not qualified
                Mock(
                    id=uuid.uuid4(), minimum_points=Decimal("1000")
                ),  # Silver - qualified
                Mock(
                    id=uuid.uuid4(), minimum_points=Decimal("0")
                ),  # Bronze - qualified
            ]
            mock_execute.return_value.scalars.return_value.all.return_value = mock_tiers

            await customer_service._check_tier_upgrade(account)

            # Should upgrade to Silver tier (first qualifying tier)
            assert account.tier_id == mock_tiers[1].id
            assert account.tier_achieved_date is not None
            assert account.tier_expiry_date is not None

    async def test_update_customer_segment(self, customer_service):
        """Test customer segmentation update"""
        # Test VIP segment assignment
        customer_vip = Mock(total_revenue=Decimal("15000.00"))
        await customer_service._update_customer_segment(customer_vip)
        assert customer_vip.segment == CustomerSegment.VIP

        # Test Premium segment assignment
        customer_premium = Mock(total_revenue=Decimal("7500.00"))
        await customer_service._update_customer_segment(customer_premium)
        assert customer_premium.segment == CustomerSegment.PREMIUM

        # Test Standard segment assignment
        customer_standard = Mock(total_revenue=Decimal("2500.00"))
        await customer_service._update_customer_segment(customer_standard)
        assert customer_standard.segment == CustomerSegment.STANDARD

        # Test Basic segment assignment
        customer_basic = Mock(total_revenue=Decimal("500.00"))
        await customer_service._update_customer_segment(customer_basic)
        assert customer_basic.segment == CustomerSegment.BASIC


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""

    async def test_complete_customer_lifecycle(self, async_client, mock_db, mock_redis):
        """Test complete customer lifecycle workflow"""
        # 1. Create customer
        customer_data = {
            "name": "Integration Test Customer",
            "customer_type": "individual",
            "status": "active",
            "contacts": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@test.com",
                    "is_primary": True,
                }
            ],
            "addresses": [
                {
                    "address_line1": "123 Test St",
                    "city": "Test City",
                    "country": "USA",
                    "is_primary": True,
                }
            ],
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.create_customer"
        ) as mock_create:
            customer_id = uuid.uuid4()
            mock_customer = Mock(
                id=customer_id,
                customer_number="CUST-TEST-001",
                name="Integration Test Customer",
            )
            mock_create.return_value = mock_customer

            customer_response = await async_client.post(
                "/api/v1/customers/", json=customer_data
            )
            assert customer_response.status_code == 200

        # 2. Create support ticket
        ticket_data = {
            "customer_id": str(customer_id),
            "subject": "Product inquiry",
            "description": "Customer asking about product features",
            "category": "general",
            "priority": "medium",
            "reported_by": "customer_service",
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.create_support_ticket"
        ) as mock_create_ticket:
            ticket_id = uuid.uuid4()
            mock_ticket = Mock(
                id=ticket_id, ticket_number="TKT-TEST-001", subject="Product inquiry"
            )
            mock_create_ticket.return_value = mock_ticket

            ticket_response = await async_client.post(
                "/api/v1/customers/tickets", json=ticket_data
            )
            assert ticket_response.status_code == 200

        # 3. Process loyalty transaction
        loyalty_data = {
            "customer_id": str(customer_id),
            "transaction_type": "earned",
            "points": 100,
            "reference_type": "purchase",
            "description": "Points earned from purchase",
            "processed_by": "system",
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.process_loyalty_transaction"
        ) as mock_loyalty:
            mock_loyalty.return_value = {
                "transaction_id": uuid.uuid4(),
                "new_balance": Decimal("100"),
                "message": "Transaction processed successfully",
            }

            loyalty_response = await async_client.post(
                "/api/v1/customers/loyalty/transactions", json=loyalty_data
            )
            assert loyalty_response.status_code == 200

    async def test_customer_analytics_workflow(self, async_client, mock_db, mock_redis):
        """Test customer analytics generation workflow"""
        analytics_request = {
            "segments": ["premium", "vip"],
            "analytics_type": "rfm",
            "include_predictions": True,
        }

        with patch(
            "app.api.v1.customer_management_v70.CustomerManagementService.generate_customer_analytics"
        ) as mock_analytics:
            mock_analytics.return_value = {
                "analytics_type": "rfm",
                "total_customers": 150,
                "analysis_date": datetime.utcnow(),
                "summary": {"high_value_customers": 45, "at_risk_customers": 12},
                "segments": {
                    "champions": 25,
                    "loyal_customers": 20,
                    "potential_loyalists": 35,
                    "at_risk": 8,
                    "lost": 4,
                },
                "recommendations": [
                    "Focus retention efforts on Champions",
                    "Re-engage At Risk customers",
                ],
            }

            response = await async_client.post(
                "/api/v1/customers/analytics", json=analytics_request
            )
            assert response.status_code == 200
            result = response.json()
            assert result["analytics_type"] == "rfm"
            assert result["total_customers"] == 150
            assert len(result["recommendations"]) > 0


class TestPerformanceAndEdgeCases:
    """Test performance scenarios and edge cases"""

    @pytest.fixture
    def customer_service(self, mock_db, mock_redis):
        return CustomerManagementService(mock_db, mock_redis)

    async def test_bulk_customer_operations(self, customer_service):
        """Test bulk customer operations performance"""
        # Simulate bulk customer retrieval
        with patch.object(customer_service.db, "execute") as mock_execute:
            # Mock large number of customers
            mock_customers = [
                Mock(
                    id=uuid.uuid4(),
                    customer_number=f"CUST{i:05d}",
                    name=f"Customer {i}",
                    status=CustomerStatus.ACTIVE,
                )
                for i in range(1000)
            ]

            mock_execute.return_value.scalar.return_value = 1000  # Total count
            mock_execute.return_value.scalars.return_value.all.return_value = (
                mock_customers
            )

            result = await customer_service.get_customers(limit=1000)

            assert result["total"] == 1000
            assert len(result["customers"]) == 1000

    async def test_concurrent_loyalty_transactions(self, customer_service):
        """Test concurrent loyalty transactions"""
        customer_id = uuid.uuid4()

        # Mock loyalty account
        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_account = Mock(
                id=uuid.uuid4(),
                current_points=Decimal("1000"),
                lifetime_points_earned=Decimal("5000"),
                lifetime_points_redeemed=Decimal("2000"),
                tier_points=Decimal("3000"),
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_account

            with patch.object(customer_service, "_check_tier_upgrade"):
                with patch.object(customer_service.db, "add"):
                    with patch.object(customer_service.db, "commit"):
                        # Create multiple concurrent transactions
                        tasks = []
                        for i in range(10):
                            transaction_data = Mock(
                                customer_id=customer_id,
                                transaction_type="earned",
                                points=Decimal("10"),
                                processed_by=f"system_{i}",
                            )
                            tasks.append(
                                customer_service.process_loyalty_transaction(
                                    transaction_data
                                )
                            )

                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # All should succeed
                        successful_results = [
                            r for r in results if not isinstance(r, Exception)
                        ]
                        assert len(successful_results) == 10

    async def test_edge_case_zero_points_transaction(self, customer_service):
        """Test edge case with zero points transaction"""
        customer_id = uuid.uuid4()
        transaction_data = Mock(
            customer_id=customer_id,
            transaction_type="earned",
            points=Decimal("0"),  # Zero points
        )

        with patch.object(customer_service.db, "execute") as mock_execute:
            mock_account = Mock(current_points=Decimal("100"))
            mock_execute.return_value.scalar_one_or_none.return_value = mock_account

            with patch.object(customer_service, "_check_tier_upgrade"):
                with patch.object(customer_service.db, "add"):
                    with patch.object(customer_service.db, "commit"):
                        result = await customer_service.process_loyalty_transaction(
                            transaction_data
                        )

                        assert result["new_balance"] == Decimal("100")  # No change

    async def test_edge_case_negative_revenue_customer(self, customer_service):
        """Test customer with negative total revenue"""
        customer = Mock(total_revenue=Decimal("-500.00"))  # Negative revenue

        await customer_service._update_customer_segment(customer)

        # Should default to BASIC segment
        assert customer.segment == CustomerSegment.BASIC


# Test execution and coverage reporting
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app.api.v1.customer_management_v70",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ]
    )
