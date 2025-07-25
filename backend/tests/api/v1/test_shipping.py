"""Tests for shipping management API endpoints - CC02 v61.0 Day 6."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_management import (
    Address,
    CarrierConfiguration,
    DeliveryPriority,
    PackageType,
    Shipment,
    ShipmentStatus,
    ShippingCarrier,
    ShippingMethod,
)
from app.models.user import User
from app.models.organization import Organization


class TestShippingAPI:
    """Test suite for shipping management API endpoints."""

    @pytest.fixture
    async def test_organization(self, db: AsyncSession) -> Organization:
        """Create test organization."""
        org = Organization(
            id="test-shipping-org",
            name="Test Shipping Organization",
            domain="shipping.test.com",
            is_active=True
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org

    @pytest.fixture
    async def test_user(
        self, 
        db: AsyncSession, 
        test_organization: Organization
    ) -> User:
        """Create test user."""
        user = User(
            id="test-shipping-user",
            email="shipping@test.com",
            username="shippinguser",
            full_name="Shipping Test User",
            organization_id=test_organization.id,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @pytest.fixture
    async def test_carrier(
        self, 
        db: AsyncSession, 
        test_organization: Organization
    ) -> CarrierConfiguration:
        """Create test carrier configuration."""
        carrier = CarrierConfiguration(
            organization_id=test_organization.id,
            carrier=ShippingCarrier.YAMATO,
            api_endpoint="https://api.yamato.test",
            api_key="test-key",
            carrier_name="Test Yamato",
            is_active=True,
            is_default=True,
            supported_methods=["standard", "express"],
            base_rate=500.0,
            weight_rate=100.0,
            distance_rate=10.0
        )
        db.add(carrier)
        await db.commit()
        await db.refresh(carrier)
        return carrier

    @pytest.fixture
    async def test_addresses(
        self, 
        db: AsyncSession, 
        test_organization: Organization
    ) -> tuple[Address, Address]:
        """Create test addresses."""
        from_address = Address(
            organization_id=test_organization.id,
            address_type="shipping",
            contact_name="Sender Name",
            address_line_1="123 Sender Street",
            city="Tokyo",
            postal_code="100-0001",
            country_code="JP",
            phone="03-1234-5678",
            email="sender@test.com"
        )
        
        to_address = Address(
            organization_id=test_organization.id,
            address_type="delivery",
            contact_name="Recipient Name",
            address_line_1="456 Recipient Avenue",
            city="Osaka",
            postal_code="530-0001",
            country_code="JP",
            phone="06-8765-4321",
            email="recipient@test.com"
        )
        
        db.add_all([from_address, to_address])
        await db.commit()
        await db.refresh(from_address)
        await db.refresh(to_address)
        
        return from_address, to_address

    @pytest.fixture
    async def test_shipment(
        self, 
        db: AsyncSession, 
        test_organization: Organization,
        test_carrier: CarrierConfiguration,
        test_addresses: tuple[Address, Address]
    ) -> Shipment:
        """Create test shipment."""
        from_address, to_address = test_addresses
        
        shipment = Shipment(
            shipment_id="TEST-SHIP-001",
            organization_id=test_organization.id,
            order_id="ORDER-001",
            carrier_config_id=test_carrier.id,
            from_address_id=from_address.id,
            to_address_id=to_address.id,
            shipping_method=ShippingMethod.STANDARD,
            package_type=PackageType.BOX,
            delivery_priority=DeliveryPriority.NORMAL,
            weight_kg=2.5,
            dimensions_cm={"length": 30, "width": 20, "height": 10},
            declared_value=5000.0,
            currency="JPY",
            current_status=ShipmentStatus.DRAFT
        )
        
        db.add(shipment)
        await db.commit()
        await db.refresh(shipment)
        return shipment

    async def test_create_carrier_configuration(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test creating a carrier configuration."""
        carrier_data = {
            "carrier": "sagawa",
            "api_endpoint": "https://api.sagawa.test",
            "api_key": "test-api-key",
            "carrier_name": "Test Sagawa Express",
            "is_active": True,
            "is_default": False,
            "supported_methods": ["standard", "express", "overnight"],
            "base_rate": 600.0,
            "weight_rate": 120.0,
            "distance_rate": 15.0,
            "max_weight_kg": 30.0,
            "service_areas": ["100", "530", "600"]
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/carriers",
            json=carrier_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["carrier"] == "sagawa"
        assert data["carrier_name"] == "Test Sagawa Express"
        assert data["is_active"] is True
        assert data["base_rate"] == 600.0
        assert data["organization_id"] == test_user.organization_id

    async def test_get_carrier_configurations(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_carrier: CarrierConfiguration
    ):
        """Test getting carrier configurations."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            "/api/v1/shipping/carriers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        carrier_data = next((c for c in data if c["id"] == test_carrier.id), None)
        assert carrier_data is not None
        assert carrier_data["carrier"] == "yamato"
        assert carrier_data["is_default"] is True

    async def test_get_shipping_rates(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_carrier: CarrierConfiguration
    ):
        """Test getting shipping rates."""
        rate_request = {
            "from_postal_code": "100-0001",
            "to_postal_code": "530-0001",
            "weight_kg": 2.5,
            "dimensions_cm": {"length": 30, "width": 20, "height": 10},
            "shipping_method": "standard",
            "package_type": "box",
            "declared_value": 5000.0
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/rates",
            json=rate_request,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        rate = data[0]
        assert "carrier" in rate
        assert "total_rate" in rate
        assert "estimated_delivery" in rate
        assert rate["total_rate"] > 0

    async def test_create_shipment(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_carrier: CarrierConfiguration
    ):
        """Test creating a shipment."""
        shipment_data = {
            "order_id": "ORDER-NEW-001",
            "from_address": {
                "contact_name": "New Sender",
                "address_line_1": "789 New Sender St",
                "city": "Tokyo",
                "postal_code": "100-0002",
                "phone": "03-9999-8888"
            },
            "to_address": {
                "contact_name": "New Recipient",
                "address_line_1": "321 New Recipient Ave",
                "city": "Kyoto",
                "postal_code": "600-0001",
                "phone": "075-1111-2222"
            },
            "items": [
                {
                    "item_name": "Test Product",
                    "weight_kg": 1.5,
                    "unit_value": 3000.0,
                    "total_value": 3000.0,
                    "quantity": 1
                }
            ],
            "shipping_method": "standard",
            "package_type": "box",
            "delivery_priority": "normal",
            "dimensions_cm": {"length": 25, "width": 15, "height": 8},
            "requires_signature": True,
            "delivery_instructions": "Leave at front door if no one home"
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/shipments",
            json=shipment_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["order_id"] == "ORDER-NEW-001"
        assert data["current_status"] == "draft"
        assert data["shipping_method"] == "standard"
        assert data["requires_signature"] is True
        assert data["delivery_instructions"] == "Leave at front door if no one home"
        assert len(data["items"]) == 1
        assert data["items"][0]["item_name"] == "Test Product"

    async def test_get_shipment(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test getting a shipment by ID."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            f"/api/v1/shipping/shipments/{test_shipment.shipment_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["shipment_id"] == test_shipment.shipment_id
        assert data["order_id"] == test_shipment.order_id
        assert data["current_status"] == test_shipment.current_status.value
        assert data["weight_kg"] == test_shipment.weight_kg
        assert "from_address" in data
        assert "to_address" in data
        assert "carrier_config" in data

    async def test_search_shipments(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test searching shipments."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        # Search by status
        response = await client.get(
            "/api/v1/shipping/shipments",
            params={"status": ["draft"]},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        shipment_data = next((s for s in data if s["id"] == test_shipment.id), None)
        assert shipment_data is not None

        # Search by order ID
        response = await client.get(
            "/api/v1/shipping/shipments",
            params={"order_id": test_shipment.order_id},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert data[0]["order_id"] == test_shipment.order_id

    async def test_track_shipment(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test shipment tracking."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            f"/api/v1/shipping/shipments/{test_shipment.shipment_id}/tracking",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["shipment_id"] == test_shipment.shipment_id
        assert data["current_status"] == test_shipment.current_status.value
        assert "events" in data
        assert "delivery_attempts" in data
        assert "is_delivered" in data

    async def test_update_shipment_status(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test updating shipment status."""
        status_update = {
            "status": "in_transit",
            "location": "Tokyo Distribution Center",
            "notes": "Package has left origin facility"
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.put(
            f"/api/v1/shipping/shipments/{test_shipment.shipment_id}/status",
            json=status_update,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "in_transit" in data["message"]
        assert data["updated_by"] == str(test_user.id)

    async def test_cancel_shipment(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test cancelling a shipment."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.delete(
            f"/api/v1/shipping/shipments/{test_shipment.shipment_id}/cancel",
            params={"reason": "Customer requested cancellation"},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Shipment cancelled successfully"
        assert data["reason"] == "Customer requested cancellation"
        assert data["cancelled_by"] == str(test_user.id)

    async def test_get_shipments_by_status(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test getting shipments by status."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            f"/api/v1/shipping/shipments/status/{test_shipment.current_status.value}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        assert all(s["current_status"] == test_shipment.current_status.value for s in data)

    async def test_get_shipping_analytics(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test getting shipping analytics."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            "/api/v1/shipping/analytics",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert "total_shipments" in data
        assert "status_distribution" in data
        assert "carrier_distribution" in data
        assert "shipping_costs" in data
        assert "delivery_performance" in data
        
        assert data["total_shipments"] >= 1
        assert test_shipment.current_status.value in data["status_distribution"]

    async def test_get_available_carriers(self, client: AsyncClient):
        """Test getting available carriers."""
        response = await client.get("/api/v1/shipping/carriers/available")

        assert response.status_code == 200
        data = response.json()
        
        expected_carriers = ["yamato", "sagawa", "japan_post", "fedex", "ups", "dhl", "custom"]
        assert all(carrier in expected_carriers for carrier in data)

    async def test_get_available_shipping_methods(self, client: AsyncClient):
        """Test getting available shipping methods."""
        response = await client.get("/api/v1/shipping/methods/available")

        assert response.status_code == 200
        data = response.json()
        
        expected_methods = ["standard", "express", "overnight", "same_day", "pickup", "international"]
        assert all(method in expected_methods for method in data)

    async def test_get_available_shipment_statuses(self, client: AsyncClient):
        """Test getting available shipment statuses."""
        response = await client.get("/api/v1/shipping/statuses/available")

        assert response.status_code == 200
        data = response.json()
        
        expected_statuses = [
            "draft", "pending", "label_created", "picked_up", "in_transit",
            "out_for_delivery", "delivered", "failed_delivery", "returned",
            "cancelled", "lost"
        ]
        assert all(status in expected_statuses for status in data)

    async def test_generate_shipping_label(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test generating shipping label."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            f"/api/v1/shipping/labels/{test_shipment.shipment_id}/generate",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "label_url" in data
        assert "tracking_number" in data
        assert data["message"] == "Shipping label generated successfully"

    async def test_handle_tracking_webhook(self, client: AsyncClient):
        """Test handling tracking webhook."""
        webhook_data = {
            "tracking_number": "TEST123456",
            "status": "in_transit",
            "location": "Distribution Center",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        response = await client.post(
            "/api/v1/shipping/webhook/tracking",
            json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Webhook processed successfully"
        assert data["tracking_number"] == "TEST123456"

    async def test_shipment_not_found(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test accessing non-existent shipment."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.get(
            "/api/v1/shipping/shipments/NONEXISTENT-001",
            headers=headers
        )

        assert response.status_code == 404
        assert "Shipment not found" in response.json()["detail"]

    async def test_invalid_status_update(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_shipment: Shipment
    ):
        """Test invalid status update."""
        status_update = {
            "status": "invalid_status",
            "notes": "This should fail"
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.put(
            f"/api/v1/shipping/shipments/{test_shipment.shipment_id}/status",
            json=status_update,
            headers=headers
        )

        assert response.status_code == 422  # Validation error

    async def test_webhook_missing_tracking_number(self, client: AsyncClient):
        """Test webhook with missing tracking number."""
        webhook_data = {
            "status": "in_transit",
            "location": "Distribution Center"
        }
        
        response = await client.post(
            "/api/v1/shipping/webhook/tracking",
            json=webhook_data
        )

        assert response.status_code == 400
        assert "Tracking number is required" in response.json()["detail"]


class TestShippingValidation:
    """Test suite for shipping data validation."""

    async def test_invalid_carrier_configuration(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test creating carrier configuration with invalid data."""
        carrier_data = {
            "carrier": "invalid_carrier",
            "api_endpoint": "not-a-url",
            "carrier_name": "",  # Empty name
            "base_rate": -100.0,  # Negative rate
            "weight_rate": -50.0  # Negative rate
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/carriers",
            json=carrier_data,
            headers=headers
        )

        assert response.status_code == 422  # Validation error

    async def test_invalid_shipment_data(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test creating shipment with invalid data."""
        shipment_data = {
            "from_address": {
                "contact_name": "",  # Empty name
                "address_line_1": "",  # Empty address
                "city": "",  # Empty city
                "postal_code": ""  # Empty postal code
            },
            "to_address": {
                "contact_name": "Valid Name",
                "address_line_1": "123 Valid St",
                "city": "Valid City",
                "postal_code": "123-4567"
            },
            "items": [],  # Empty items
            "dimensions_cm": {"length": -10}  # Negative dimension
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/shipments",
            json=shipment_data,
            headers=headers
        )

        assert response.status_code == 422  # Validation error

    async def test_invalid_rate_request(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test rate request with invalid data."""
        rate_request = {
            "from_postal_code": "",  # Empty postal code
            "to_postal_code": "123-4567",
            "weight_kg": -1.0,  # Negative weight
            "dimensions_cm": {}  # Empty dimensions
        }

        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}
        
        response = await client.post(
            "/api/v1/shipping/rates",
            json=rate_request,
            headers=headers
        )

        assert response.status_code == 422  # Validation error


class TestShippingIntegration:
    """Integration tests for shipping workflow."""

    async def test_complete_shipping_workflow(
        self, 
        client: AsyncClient, 
        test_user: User,
        test_carrier: CarrierConfiguration,
        db: AsyncSession
    ):
        """Test complete shipping workflow from creation to delivery."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}

        # 1. Create shipment
        shipment_data = {
            "order_id": "WORKFLOW-001",
            "from_address": {
                "contact_name": "Workflow Sender",
                "address_line_1": "123 Workflow St",
                "city": "Tokyo",
                "postal_code": "100-0001"
            },
            "to_address": {
                "contact_name": "Workflow Recipient",
                "address_line_1": "456 Workflow Ave",
                "city": "Osaka",
                "postal_code": "530-0001"
            },
            "items": [
                {
                    "item_name": "Workflow Item",
                    "weight_kg": 2.0,
                    "unit_value": 4000.0,
                    "total_value": 4000.0,
                    "quantity": 1
                }
            ],
            "shipping_method": "express",
            "package_type": "box"
        }
        
        response = await client.post(
            "/api/v1/shipping/shipments",
            json=shipment_data,
            headers=headers
        )
        
        assert response.status_code == 200
        shipment = response.json()
        shipment_id = shipment["shipment_id"]

        # 2. Generate shipping label
        response = await client.post(
            f"/api/v1/shipping/labels/{shipment_id}/generate",
            headers=headers
        )
        
        assert response.status_code == 200
        label_data = response.json()
        assert label_data["success"] is True

        # 3. Update to picked up
        response = await client.put(
            f"/api/v1/shipping/shipments/{shipment_id}/status",
            json={
                "status": "picked_up",
                "location": "Origin Facility",
                "notes": "Package picked up by driver"
            },
            headers=headers
        )
        
        assert response.status_code == 200

        # 4. Update to in transit
        response = await client.put(
            f"/api/v1/shipping/shipments/{shipment_id}/status",
            json={
                "status": "in_transit",
                "location": "Distribution Center",
                "notes": "Package in transit"
            },
            headers=headers
        )
        
        assert response.status_code == 200

        # 5. Update to delivered
        response = await client.put(
            f"/api/v1/shipping/shipments/{shipment_id}/status",
            json={
                "status": "delivered",
                "location": "Recipient Address",
                "notes": "Package delivered successfully"
            },
            headers=headers
        )
        
        assert response.status_code == 200

        # 6. Verify final tracking
        response = await client.get(
            f"/api/v1/shipping/shipments/{shipment_id}/tracking",
            headers=headers
        )
        
        assert response.status_code == 200
        tracking = response.json()
        assert tracking["current_status"] == "delivered"
        assert tracking["is_delivered"] is True
        assert len(tracking["events"]) >= 3  # At least 3 status updates

        # 7. Verify analytics updated
        response = await client.get(
            "/api/v1/shipping/analytics",
            headers=headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["total_shipments"] >= 1
        assert "delivered" in analytics["status_distribution"]

    async def test_bulk_shipment_operations(
        self, 
        client: AsyncClient, 
        test_user: User,
        test_carrier: CarrierConfiguration
    ):
        """Test bulk shipment operations."""
        headers = {"Authorization": f"Bearer mock-token-{test_user.id}"}

        # Create multiple shipments
        shipment_ids = []
        for i in range(3):
            shipment_data = {
                "order_id": f"BULK-{i+1:03d}",
                "from_address": {
                    "contact_name": f"Bulk Sender {i+1}",
                    "address_line_1": f"{100+i} Bulk St",
                    "city": "Tokyo",
                    "postal_code": "100-0001"
                },
                "to_address": {
                    "contact_name": f"Bulk Recipient {i+1}",
                    "address_line_1": f"{200+i} Bulk Ave",
                    "city": "Osaka",
                    "postal_code": "530-0001"
                },
                "items": [
                    {
                        "item_name": f"Bulk Item {i+1}",
                        "weight_kg": 1.0 + i,
                        "unit_value": 1000.0 * (i+1),
                        "total_value": 1000.0 * (i+1),
                        "quantity": 1
                    }
                ]
            }
            
            response = await client.post(
                "/api/v1/shipping/shipments",
                json=shipment_data,
                headers=headers
            )
            
            assert response.status_code == 200
            shipment = response.json()
            shipment_ids.append(shipment["shipment_id"])

        # Search for all bulk shipments
        response = await client.get(
            "/api/v1/shipping/shipments",
            params={"limit": 10},
            headers=headers
        )
        
        assert response.status_code == 200
        shipments = response.json()
        bulk_shipments = [s for s in shipments if s["order_id"].startswith("BULK-")]
        assert len(bulk_shipments) >= 3

        # Update all to same status
        for shipment_id in shipment_ids:
            response = await client.put(
                f"/api/v1/shipping/shipments/{shipment_id}/status",
                json={
                    "status": "in_transit",
                    "notes": "Bulk update to in transit"
                },
                headers=headers
            )
            assert response.status_code == 200

        # Verify all updated
        response = await client.get(
            "/api/v1/shipping/shipments/status/in_transit",
            headers=headers
        )
        
        assert response.status_code == 200
        in_transit_shipments = response.json()
        bulk_in_transit = [s for s in in_transit_shipments if s["order_id"].startswith("BULK-")]
        assert len(bulk_in_transit) >= 3