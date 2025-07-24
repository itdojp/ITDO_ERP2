"""
Test Suite for Notification System API v31.0

Comprehensive test coverage for all 10 notification system endpoints:
1. Notification Management
2. Template Management
3. Delivery Management
4. Preference Management
5. Subscription Management
6. Event Processing
7. Analytics & Reporting
8. Interaction Tracking
9. Real-Time WebSocket
10. System Health & Status
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.notification_extended import (
    DeliveryStatus,
    NotificationAnalytics,
    NotificationChannel,
    NotificationDelivery,
    NotificationEvent,
    NotificationExtended,
    NotificationInteraction,
    NotificationPreference,
    NotificationStatus,
    NotificationSubscription,
    NotificationTemplate,
    NotificationType,
    SubscriptionStatus,
)

client = TestClient(app)


# Test data fixtures
@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        "organization_id": "org-123",
        "title": "Test Notification",
        "message": "This is a test notification message",
        "summary": "Test notification summary",
        "notification_type": "info",
        "category": "system",
        "priority": "normal",
        "recipient_user_id": "user-123",
        "recipient_email": "user@test.com",
        "channels": ["in_app", "email"],
        "primary_channel": "in_app",
        "tags": ["test", "notification"],
        "metadata": {"source": "test_suite"},
    }


@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "organization_id": "org-123",
        "name": "Test Template",
        "code": "TEST_TEMPLATE",
        "description": "Test notification template",
        "message_template": "Hello {{user_name}}, you have a new {{item_type}}!",
        "notification_type": "info",
        "default_priority": "normal",
        "variables": ["user_name", "item_type"],
        "required_variables": ["user_name"],
        "owner_id": "user-123",
        "created_by": "user-123",
    }


@pytest.fixture
def sample_preference_data():
    """Sample preference data for testing."""
    return {
        "email_enabled": True,
        "sms_enabled": False,
        "push_enabled": True,
        "in_app_enabled": True,
        "system_notifications": True,
        "quiet_hours_enabled": True,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "max_emails_per_day": 25,
        "digest_frequency": "daily",
    }


@pytest.fixture
def sample_subscription_data():
    """Sample subscription data for testing."""
    return {
        "organization_id": "org-123",
        "topic": "project_updates",
        "event_type": "task_completed",
        "entity_type": "project",
        "entity_id": "project-456",
        "channels": ["in_app", "email"],
        "priority": "normal",
        "frequency": "instant",
        "name": "Project Updates Subscription",
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "organization_id": "org-123",
        "event_name": "task_completed",
        "event_type": "project_event",
        "source_system": "project_management",
        "event_data": {
            "task_id": "task-789",
            "task_name": "Complete documentation",
            "project_id": "project-456",
            "completed_by": "user-123",
        },
        "entity_type": "task",
        "entity_id": "task-789",
        "priority": "normal",
        "event_timestamp": datetime.utcnow().isoformat(),
    }


class TestNotificationManagement:
    """Test suite for Notification Management endpoints."""

    @patch("app.crud.notification_v31.NotificationService.create_notification")
    def test_create_notification_success(self, mock_create, sample_notification_data):
        """Test successful notification creation."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_notification.notification_number = "NOTIF-12345678"
        mock_notification.title = sample_notification_data["title"]
        mock_notification.message = sample_notification_data["message"]
        mock_notification.notification_type = NotificationType.INFO
        mock_notification.status = NotificationStatus.PENDING
        mock_notification.primary_channel = NotificationChannel.IN_APP
        mock_notification.recipient_user_id = "user-123"
        mock_notification.created_at = datetime.utcnow()

        mock_create.return_value = mock_notification

        response = client.post("/api/v1/notifications", json=sample_notification_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_notification_data["title"]
        assert "notification_number" in data
        mock_create.assert_called_once()

    def test_create_notification_validation_error(self):
        """Test notification creation with validation errors."""
        invalid_data = {
            "organization_id": "org-123",
            # Missing required fields
            "notification_type": "invalid_type",
        }

        response = client.post("/api/v1/notifications", json=invalid_data)
        assert response.status_code == 422

    @patch("app.crud.notification_v31.NotificationService.get_notifications")
    def test_get_notifications_with_filters(self, mock_get_notifications):
        """Test notification listing with comprehensive filters."""
        mock_notifications = [
            NotificationExtended(
                id="notif-1",
                title="Notification 1",
                notification_type=NotificationType.INFO,
                status=NotificationStatus.SENT,
                primary_channel=NotificationChannel.IN_APP,
            ),
            NotificationExtended(
                id="notif-2",
                title="Notification 2",
                notification_type=NotificationType.ALERT,
                status=NotificationStatus.PENDING,
                primary_channel=NotificationChannel.EMAIL,
            ),
        ]
        mock_get_notifications.return_value = mock_notifications

        response = client.get(
            "/api/v1/notifications",
            params={
                "organization_id": "org-123",
                "recipient_user_id": "user-123",
                "notification_type": "info",
                "status": "sent",
                "priority": "normal",
                "is_read": False,
                "limit": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert len(data["notifications"]) == 2
        assert data["total_count"] == 2
        mock_get_notifications.assert_called()

    @patch("app.crud.notification_v31.NotificationService.get_notification_by_id")
    def test_get_notification_by_id_success(self, mock_get_notification):
        """Test successful notification retrieval by ID."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_notification.title = "Test Notification"
        mock_notification.message = "Test message"
        mock_notification.notification_type = NotificationType.INFO
        mock_notification.status = NotificationStatus.SENT
        mock_notification.primary_channel = NotificationChannel.IN_APP
        mock_notification.view_count = 5
        mock_get_notification.return_value = mock_notification

        response = client.get("/api/v1/notifications/notif-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "notif-123"
        assert data["view_count"] == 5
        mock_get_notification.assert_called_once()

    @patch("app.crud.notification_v31.NotificationService.get_notification_by_id")
    def test_update_notification_success(self, mock_get_notification):
        """Test successful notification update."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_notification.title = "Original Title"
        mock_notification.message = "Original message"
        mock_notification.notification_type = NotificationType.INFO
        mock_notification.status = NotificationStatus.PENDING
        mock_notification.primary_channel = NotificationChannel.IN_APP
        mock_get_notification.return_value = mock_notification

        update_data = {
            "title": "Updated Title",
            "message": "Updated message",
            "tags": ["updated", "test"],
        }

        with patch.object(mock_notification, "__setattr__"):
            response = client.put(
                "/api/v1/notifications/notif-123?user_id=user-123", json=update_data
            )

            assert response.status_code == 200

    @patch("app.crud.notification_v31.NotificationService.mark_notification_as_read")
    def test_mark_notification_as_read(self, mock_mark_read):
        """Test marking notification as read."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_notification.is_read = True
        mock_notification.read_at = datetime.utcnow()
        mock_notification.view_count = 1
        mock_mark_read.return_value = mock_notification

        response = client.post("/api/v1/notifications/notif-123/read?user_id=user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        mock_mark_read.assert_called_once()

    @patch("app.crud.notification_v31.NotificationService.archive_notification")
    def test_archive_notification(self, mock_archive):
        """Test notification archiving."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_notification.is_archived = True
        mock_notification.archived_at = datetime.utcnow()
        mock_archive.return_value = mock_notification

        response = client.post(
            "/api/v1/notifications/notif-123/archive?user_id=user-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True

    @patch("app.crud.notification_v31.NotificationService.get_notification_by_id")
    def test_delete_notification(self, mock_get_notification):
        """Test notification deletion."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-123"
        mock_get_notification.return_value = mock_notification

        response = client.delete("/api/v1/notifications/notif-123?user_id=user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Notification deleted successfully"


class TestTemplateManagement:
    """Test suite for Template Management endpoints."""

    @patch("app.crud.notification_v31.NotificationService.create_notification_template")
    def test_create_template_success(self, mock_create_template, sample_template_data):
        """Test successful template creation."""
        mock_template = NotificationTemplate()
        mock_template.id = "template-123"
        mock_template.name = sample_template_data["name"]
        mock_template.code = sample_template_data["code"]
        mock_template.notification_type = NotificationType.INFO
        mock_template.is_active = True

        mock_create_template.return_value = mock_template

        response = client.post("/api/v1/templates", json=sample_template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_template_data["name"]
        assert data["code"] == sample_template_data["code"]

    def test_get_templates_with_filters(self):
        """Test template listing with filters."""
        with patch("app.api.v1.notification_v31.db.query") as mock_query:
            mock_templates = [
                NotificationTemplate(
                    id="template-1",
                    name="Template 1",
                    notification_type=NotificationType.INFO,
                ),
                NotificationTemplate(
                    id="template-2",
                    name="Template 2",
                    notification_type=NotificationType.ALERT,
                ),
            ]

            # Mock the query chain
            mock_query_obj = MagicMock()
            mock_query_obj.filter.return_value = mock_query_obj
            mock_query_obj.offset.return_value = mock_query_obj
            mock_query_obj.limit.return_value = mock_query_obj
            mock_query_obj.all.return_value = mock_templates
            mock_query.return_value = mock_query_obj

            response = client.get(
                "/api/v1/templates",
                params={
                    "organization_id": "org-123",
                    "category": "system",
                    "is_active": True,
                    "limit": 50,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    @patch(
        "app.crud.notification_v31.NotificationService.generate_notification_from_template"
    )
    def test_generate_from_template(self, mock_generate):
        """Test notification generation from template."""
        mock_notification = NotificationExtended()
        mock_notification.id = "notif-456"
        mock_notification.title = "Generated Notification"
        mock_notification.message = "Hello John, you have a new task!"
        mock_notification.notification_type = NotificationType.INFO
        mock_notification.status = NotificationStatus.PENDING
        mock_notification.primary_channel = NotificationChannel.IN_APP
        mock_notification.recipient_user_id = "user-123"

        mock_generate.return_value = mock_notification

        generation_data = {
            "template_id": "template-123",
            "field_values": {"user_name": "John", "item_type": "task"},
            "recipient_user_id": "user-123",
        }

        response = client.post(
            "/api/v1/templates/template-123/generate?generated_by_id=user-123",
            json=generation_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello John, you have a new task!"


class TestDeliveryManagement:
    """Test suite for Delivery Management endpoints."""

    def test_get_notification_deliveries(self):
        """Test notification deliveries retrieval."""
        with patch("app.api.v1.notification_v31.db.query") as mock_query:
            mock_deliveries = [
                NotificationDelivery(
                    id="delivery-1",
                    notification_id="notif-123",
                    channel=NotificationChannel.EMAIL,
                    status=DeliveryStatus.DELIVERED,
                ),
                NotificationDelivery(
                    id="delivery-2",
                    notification_id="notif-123",
                    channel=NotificationChannel.SMS,
                    status=DeliveryStatus.SENT,
                ),
            ]

            mock_query_obj = MagicMock()
            mock_query_obj.filter.return_value = mock_query_obj
            mock_query_obj.all.return_value = mock_deliveries
            mock_query.return_value = mock_query_obj

            response = client.get("/api/v1/notifications/notif-123/deliveries")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    @patch("app.crud.notification_v31.NotificationService.update_delivery_status")
    def test_update_delivery_status(self, mock_update_status):
        """Test delivery status update."""
        mock_delivery = NotificationDelivery()
        mock_delivery.id = "delivery-123"
        mock_delivery.status = DeliveryStatus.DELIVERED
        mock_delivery.delivered_at = datetime.utcnow()

        mock_update_status.return_value = mock_delivery

        response = client.post(
            "/api/v1/deliveries/delivery-123/status",
            params={"status": "delivered"},
            json={"message_id": "provider-123", "response": {"success": True}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Delivery status updated successfully"


class TestPreferenceManagement:
    """Test suite for Preference Management endpoints."""

    @patch(
        "app.crud.notification_v31.NotificationService.get_user_notification_preferences"
    )
    def test_get_notification_preferences(self, mock_get_preferences):
        """Test notification preferences retrieval."""
        mock_preferences = NotificationPreference()
        mock_preferences.id = "pref-123"
        mock_preferences.user_id = "user-123"
        mock_preferences.organization_id = "org-123"
        mock_preferences.email_enabled = True
        mock_preferences.sms_enabled = False
        mock_preferences.push_enabled = True
        mock_preferences.in_app_enabled = True

        mock_get_preferences.return_value = mock_preferences

        response = client.get(
            "/api/v1/preferences",
            params={"user_id": "user-123", "organization_id": "org-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] is True
        assert data["sms_enabled"] is False

    @patch(
        "app.crud.notification_v31.NotificationService.update_user_notification_preferences"
    )
    def test_update_notification_preferences(
        self, mock_update_preferences, sample_preference_data
    ):
        """Test notification preferences update."""
        mock_preferences = NotificationPreference()
        mock_preferences.id = "pref-123"
        mock_preferences.user_id = "user-123"
        mock_preferences.organization_id = "org-123"
        mock_preferences.email_enabled = sample_preference_data["email_enabled"]
        mock_preferences.quiet_hours_enabled = sample_preference_data[
            "quiet_hours_enabled"
        ]

        mock_update_preferences.return_value = mock_preferences

        response = client.put(
            "/api/v1/preferences",
            params={"user_id": "user-123", "organization_id": "org-123"},
            json=sample_preference_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] == sample_preference_data["email_enabled"]


class TestSubscriptionManagement:
    """Test suite for Subscription Management endpoints."""

    @patch(
        "app.crud.notification_v31.NotificationService.create_notification_subscription"
    )
    def test_create_subscription_success(
        self, mock_create_subscription, sample_subscription_data
    ):
        """Test successful subscription creation."""
        mock_subscription = NotificationSubscription()
        mock_subscription.id = "sub-123"
        mock_subscription.user_id = "user-123"
        mock_subscription.topic = sample_subscription_data["topic"]
        mock_subscription.status = SubscriptionStatus.ACTIVE

        mock_create_subscription.return_value = mock_subscription

        response = client.post(
            "/api/v1/subscriptions?user_id=user-123", json=sample_subscription_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == sample_subscription_data["topic"]

    @patch("app.crud.notification_v31.NotificationService.get_user_subscriptions")
    def test_get_user_subscriptions(self, mock_get_subscriptions):
        """Test user subscriptions retrieval."""
        mock_subscriptions = [
            NotificationSubscription(
                id="sub-1", topic="project_updates", status=SubscriptionStatus.ACTIVE
            ),
            NotificationSubscription(
                id="sub-2", topic="system_alerts", status=SubscriptionStatus.ACTIVE
            ),
        ]

        mock_get_subscriptions.return_value = mock_subscriptions

        response = client.get(
            "/api/v1/subscriptions",
            params={"user_id": "user-123", "organization_id": "org-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("app.crud.notification_v31.NotificationService.unsubscribe_user")
    def test_unsubscribe_user(self, mock_unsubscribe):
        """Test user unsubscription."""
        mock_unsubscribe.return_value = True

        response = client.delete("/api/v1/subscriptions/sub-123?user_id=user-123")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully unsubscribed"


class TestEventProcessing:
    """Test suite for Event Processing endpoints."""

    @patch("app.crud.notification_v31.NotificationService.process_notification_event")
    def test_process_notification_event(self, mock_process_event, sample_event_data):
        """Test event processing and notification generation."""
        mock_notifications = [
            NotificationExtended(
                id="notif-1",
                title="Task Completed",
                message="Task has been completed",
                notification_type=NotificationType.INFO,
                status=NotificationStatus.PENDING,
                primary_channel=NotificationChannel.IN_APP,
                recipient_user_id="user-456",
            )
        ]

        mock_process_event.return_value = mock_notifications

        response = client.post("/api/v1/events", json=sample_event_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Task Completed"

    def test_get_notification_events(self):
        """Test notification events retrieval."""
        with patch("app.api.v1.notification_v31.db.query") as mock_query:
            mock_events = [
                NotificationEvent(
                    id="event-1",
                    event_name="task_completed",
                    event_type="project_event",
                    is_processed=True,
                ),
                NotificationEvent(
                    id="event-2",
                    event_name="user_login",
                    event_type="auth_event",
                    is_processed=False,
                ),
            ]

            mock_query_obj = MagicMock()
            mock_query_obj.filter.return_value = mock_query_obj
            mock_query_obj.order_by.return_value = mock_query_obj
            mock_query_obj.offset.return_value = mock_query_obj
            mock_query_obj.limit.return_value = mock_query_obj
            mock_query_obj.all.return_value = mock_events
            mock_query.return_value = mock_query_obj

            response = client.get(
                "/api/v1/events",
                params={
                    "organization_id": "org-123",
                    "event_type": "project_event",
                    "processed": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


class TestAnalytics:
    """Test suite for Analytics & Reporting endpoints."""

    @patch("app.crud.notification_v31.NotificationService.get_notification_analytics")
    def test_generate_notification_analytics(self, mock_get_analytics):
        """Test notification analytics generation."""
        mock_analytics = NotificationAnalytics()
        mock_analytics.organization_id = "org-123"
        mock_analytics.total_notifications = 1000
        mock_analytics.notifications_sent = 950
        mock_analytics.notifications_read = 600
        mock_analytics.email_sent = 500
        mock_analytics.email_delivered = 480
        mock_analytics.email_opened = 240
        mock_analytics.delivery_success_rate = Decimal("95.0")
        mock_analytics.open_rate = Decimal("50.0")
        mock_analytics.calculated_date = datetime.utcnow()

        mock_get_analytics.return_value = mock_analytics

        analytics_data = {
            "organization_id": "org-123",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "period_type": "monthly",
        }

        response = client.post("/api/v1/analytics", json=analytics_data)

        assert response.status_code == 200
        data = response.json()
        assert data["total_notifications"] == 1000
        assert float(data["delivery_success_rate"]) == 95.0

    @patch("app.crud.notification_v31.NotificationService.get_notification_analytics")
    def test_get_notification_dashboard(self, mock_get_analytics):
        """Test notification dashboard data retrieval."""
        mock_analytics = NotificationAnalytics()
        mock_analytics.total_notifications = 500
        mock_analytics.delivery_success_rate = Decimal("92.5")
        mock_analytics.open_rate = Decimal("45.0")
        mock_analytics.click_rate = Decimal("15.0")
        mock_analytics.email_sent = 200
        mock_analytics.email_delivered = 185
        mock_analytics.email_opened = 90
        mock_analytics.email_clicked = 30
        mock_analytics.total_views = 1000
        mock_analytics.total_clicks = 150
        mock_analytics.unique_viewers = 300
        mock_analytics.total_cost = Decimal("50.25")
        mock_analytics.cost_per_notification = Decimal("0.10")

        mock_get_analytics.return_value = mock_analytics

        response = client.get(
            "/api/v1/analytics/dashboard",
            params={"organization_id": "org-123", "period_days": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "channels" in data
        assert "engagement" in data
        assert "costs" in data
        assert data["overview"]["total_notifications"] == 500


class TestInteractionTracking:
    """Test suite for Interaction Tracking endpoints."""

    @patch(
        "app.crud.notification_v31.NotificationService._log_notification_interaction"
    )
    def test_log_notification_interaction(self, mock_log_interaction):
        """Test notification interaction logging."""
        mock_log_interaction.return_value = None

        interaction_data = {
            "notification_id": "notif-123",
            "interaction_type": "click",
            "channel": "email",
            "device_type": "mobile",
            "platform": "ios",
            "interaction_data": {"button_id": "cta_button"},
        }

        response = client.post(
            "/api/v1/interactions?user_id=user-123", json=interaction_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Interaction logged successfully"

    def test_get_notification_interactions(self):
        """Test notification interactions retrieval."""
        with patch("app.api.v1.notification_v31.db.query") as mock_query:
            mock_interactions = [
                NotificationInteraction(
                    id="interaction-1",
                    notification_id="notif-123",
                    interaction_type="view",
                    timestamp=datetime.utcnow(),
                ),
                NotificationInteraction(
                    id="interaction-2",
                    notification_id="notif-123",
                    interaction_type="click",
                    timestamp=datetime.utcnow(),
                ),
            ]

            mock_query_obj = MagicMock()
            mock_query_obj.filter.return_value = mock_query_obj
            mock_query_obj.order_by.return_value = mock_query_obj
            mock_query_obj.all.return_value = mock_interactions
            mock_query.return_value = mock_query_obj

            response = client.get("/api/v1/notifications/notif-123/interactions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


class TestSystemHealth:
    """Test suite for System Health & Status endpoints."""

    @patch("app.crud.notification_v31.NotificationService.get_system_health")
    def test_system_health_success(self, mock_get_health):
        """Test successful system health check."""
        mock_health = {
            "status": "healthy",
            "database_connection": "OK",
            "services_available": True,
            "statistics": {"total_notifications": 5000, "pending_queue_items": 10},
            "version": "31.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

        mock_get_health.return_value = mock_health

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services_available"] is True

    @patch("app.crud.notification_v31.NotificationService.get_system_health")
    def test_system_health_failure(self, mock_get_health):
        """Test system health check failure handling."""
        mock_get_health.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services_available"] is False
        assert "error" in data

    @patch("app.crud.notification_v31.NotificationService.process_notification_queue")
    def test_process_notification_queue(self, mock_process_queue):
        """Test notification queue processing."""
        mock_notifications = [
            NotificationExtended(
                id="notif-1",
                title="Queued Notification 1",
                notification_type=NotificationType.INFO,
                status=NotificationStatus.SENT,
                primary_channel=NotificationChannel.IN_APP,
                recipient_user_id="user-123",
            ),
            NotificationExtended(
                id="notif-2",
                title="Queued Notification 2",
                notification_type=NotificationType.ALERT,
                status=NotificationStatus.SENT,
                primary_channel=NotificationChannel.EMAIL,
                recipient_user_id="user-456",
            ),
        ]

        mock_process_queue.return_value = mock_notifications

        response = client.post(
            "/api/v1/queue/process", params={"queue_name": "default", "batch_size": 100}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["processed_count"] == 2
        assert data["queue_name"] == "default"


class TestBulkOperations:
    """Test suite for Bulk Operations endpoints."""

    @patch("app.crud.notification_v31.NotificationService.create_notification")
    def test_create_bulk_notifications(self, mock_create):
        """Test bulk notification creation."""
        # Mock successful creation for all notifications
        mock_notifications = []
        for i in range(3):
            notification = NotificationExtended()
            notification.id = f"notif-{i}"
            notification.title = f"Bulk Notification {i}"
            notification.notification_type = NotificationType.INFO
            notification.status = NotificationStatus.PENDING
            notification.primary_channel = NotificationChannel.IN_APP
            notification.recipient_user_id = f"user-{i}"
            mock_notifications.append(notification)

        mock_create.side_effect = mock_notifications

        bulk_data = {
            "notifications": [
                {
                    "organization_id": "org-123",
                    "title": f"Bulk Notification {i}",
                    "message": f"Bulk message {i}",
                    "notification_type": "info",
                    "recipient_user_id": f"user-{i}",
                }
                for i in range(3)
            ],
            "batch_id": "bulk-batch-123",
        }

        response = client.post("/api/v1/notifications/bulk", json=bulk_data)

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "bulk-batch-123"
        assert data["total_requested"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert data["success_rate"] == 100.0


class TestWebSocketConnection:
    """Test suite for WebSocket connection functionality."""

    def test_websocket_connection_handling(self):
        """Test WebSocket connection management."""
        from app.api.v1.notification_v31 import NotificationConnectionManager

        manager = NotificationConnectionManager()

        # Mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        # Test connection
        user_id = "user-123"

        # Since connect is async, we need to test it properly
        import asyncio

        async def test_connection():
            await manager.connect(mock_websocket, user_id)
            assert user_id in manager.active_connections
            assert mock_websocket in manager.active_connections[user_id]

            # Test sending notification
            notification_data = {
                "id": "notif-123",
                "title": "Test",
                "message": "Test message",
            }

            await manager.send_notification(user_id, notification_data)
            mock_websocket.send_text.assert_called_once()

            # Test disconnection
            manager.disconnect(mock_websocket, user_id)
            assert user_id not in manager.active_connections

        # Run the async test
        asyncio.run(test_connection())


# Integration test scenarios
class TestNotificationIntegrationScenarios:
    """Integration test scenarios for complete notification workflows."""

    @patch("app.crud.notification_v31.NotificationService")
    def test_complete_notification_lifecycle(self, mock_service):
        """Test complete notification lifecycle from creation to interaction."""
        mock_service_instance = mock_service.return_value

        # Setup mocks for the entire lifecycle
        mock_notification = NotificationExtended(
            id="notif-123",
            title="Integration Test",
            notification_type=NotificationType.INFO,
            status=NotificationStatus.PENDING,
            primary_channel=NotificationChannel.IN_APP,
            recipient_user_id="user-123",
        )
        NotificationTemplate(id="template-123", name="Test Template")
        mock_preferences = NotificationPreference(id="pref-123", email_enabled=True)

        mock_service_instance.create_notification.return_value = mock_notification
        mock_service_instance.get_notification_by_id.return_value = mock_notification
        mock_service_instance.mark_notification_as_read.return_value = mock_notification
        mock_service_instance.get_user_notification_preferences.return_value = (
            mock_preferences
        )

        # Execute the lifecycle
        # 1. Create notification
        notification_data = {
            "organization_id": "org-123",
            "title": "Integration Test",
            "message": "Integration test message",
            "notification_type": "info",
            "recipient_user_id": "user-123",
        }

        create_response = client.post("/api/v1/notifications", json=notification_data)
        assert create_response.status_code == 201

        # 2. Get notification
        get_response = client.get("/api/v1/notifications/notif-123")
        assert get_response.status_code == 200

        # 3. Mark as read
        read_response = client.post(
            "/api/v1/notifications/notif-123/read?user_id=user-123"
        )
        assert read_response.status_code == 200

        # 4. Check preferences
        pref_response = client.get(
            "/api/v1/preferences?user_id=user-123&organization_id=org-123"
        )
        assert pref_response.status_code == 200

    @patch("app.crud.notification_v31.NotificationService")
    def test_template_generation_workflow(self, mock_service):
        """Test complete template-based notification generation workflow."""
        mock_service_instance = mock_service.return_value

        # Mock template and generated notification
        mock_template = NotificationTemplate(
            id="template-123",
            name="Welcome Template",
            notification_type=NotificationType.INFO,
        )
        mock_notification = NotificationExtended(
            id="notif-456",
            title="Welcome John!",
            message="Welcome to our platform, John!",
            notification_type=NotificationType.INFO,
            status=NotificationStatus.PENDING,
            primary_channel=NotificationChannel.EMAIL,
            recipient_user_id="user-123",
        )

        mock_service_instance.create_notification_template.return_value = mock_template
        mock_service_instance.generate_notification_from_template.return_value = (
            mock_notification
        )

        # Create template
        template_data = {
            "organization_id": "org-123",
            "name": "Welcome Template",
            "code": "WELCOME_USER",
            "message_template": "Welcome to our platform, {{user_name}}!",
            "notification_type": "info",
            "owner_id": "user-123",
            "created_by": "user-123",
        }

        template_response = client.post("/api/v1/templates", json=template_data)
        assert template_response.status_code == 201

        # Generate notification from template
        generation_data = {
            "template_id": "template-123",
            "field_values": {"user_name": "John"},
            "recipient_user_id": "user-123",
        }

        generate_response = client.post(
            "/api/v1/templates/template-123/generate?generated_by_id=user-123",
            json=generation_data,
        )
        assert generate_response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
