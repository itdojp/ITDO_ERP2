"""Tests for the notification system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    NotificationPreference,
    Notification,
)
from app.services.notification_service import (
    NotificationService,
    NotificationTemplateService,
    NotificationPreferenceService,
)


class TestNotificationTemplateService:
    """Tests for notification template service."""

    @pytest.mark.asyncio
    async def test_create_template(self, async_db, test_user, test_organization):
        """Test creating a notification template."""
        service = NotificationTemplateService(async_db)
        
        template = await service.create_template(
            name="Welcome Email",
            template_key="welcome_email",
            channel=NotificationChannel.EMAIL,
            content_template="Welcome to our platform, {{user_name}}!",
            category="onboarding",
            subject_template="Welcome {{user_name}}",
            html_template="<h1>Welcome {{user_name}}</h1>",
            variables={"user_name": "string"},
            organization_id=test_organization.id,
            created_by=test_user.id
        )
        
        assert template.name == "Welcome Email"
        assert template.template_key == "welcome_email"
        assert template.channel == NotificationChannel.EMAIL
        assert template.category == "onboarding"
        assert template.is_active is True

    @pytest.mark.asyncio
    async def test_get_template_by_key(self, async_db, notification_template):
        """Test getting template by key."""
        service = NotificationTemplateService(async_db)
        
        # Test cache miss and database fetch
        template = await service.get_by_key("test_template")
        assert template is not None
        assert template.template_key == "test_template"

    @pytest.mark.asyncio
    async def test_render_template(self, async_db, notification_template):
        """Test template rendering with variables."""
        service = NotificationTemplateService(async_db)
        
        variables = {"user_name": "John Doe", "company": "ACME Corp"}
        rendered = await service.render_template(notification_template, variables)
        
        assert "John Doe" in rendered["content"]
        assert "ACME Corp" in rendered["content"]
        if "subject" in rendered:
            assert "John Doe" in rendered["subject"]

    @pytest.mark.asyncio
    async def test_render_template_missing_variables(self, async_db, notification_template):
        """Test template rendering with missing variables."""
        service = NotificationTemplateService(async_db)
        
        # This should raise an error for missing variables
        with pytest.raises(ValueError, match="Template rendering failed"):
            await service.render_template(notification_template, {})

    @pytest.mark.asyncio
    async def test_list_by_category(self, async_db, test_organization):
        """Test listing templates by category."""
        service = NotificationTemplateService(async_db)
        
        # Create templates in different categories
        await service.create_template(
            name="Template 1",
            template_key="cat1_template1",
            channel=NotificationChannel.EMAIL,
            content_template="Content 1",
            category="category1",
            organization_id=test_organization.id
        )
        
        await service.create_template(
            name="Template 2",
            template_key="cat1_template2",
            channel=NotificationChannel.SMS,
            content_template="Content 2",
            category="category1",
            organization_id=test_organization.id
        )
        
        await service.create_template(
            name="Template 3",
            template_key="cat2_template1",
            channel=NotificationChannel.EMAIL,
            content_template="Content 3",
            category="category2",
            organization_id=test_organization.id
        )
        
        # Test category filtering
        cat1_templates = await service.list_by_category("category1", test_organization.id)
        assert len(cat1_templates) == 2
        
        # Test category and channel filtering
        cat1_email_templates = await service.list_by_category(
            "category1", test_organization.id, NotificationChannel.EMAIL
        )
        assert len(cat1_email_templates) == 1


class TestNotificationPreferenceService:
    """Tests for notification preference service."""

    @pytest.mark.asyncio
    async def test_get_user_preferences(self, async_db, test_user, test_organization):
        """Test getting user preferences."""
        service = NotificationPreferenceService(async_db)
        
        # Create a preference
        await service.create({
            "user_id": test_user.id,
            "category": "security",
            "channel": NotificationChannel.EMAIL,
            "enabled": True,
            "frequency": "immediate",
            "organization_id": test_organization.id
        })
        
        preferences = await service.get_user_preferences(test_user.id, test_organization.id)
        assert len(preferences) == 1
        assert preferences[0].category == "security"
        assert preferences[0].enabled is True

    @pytest.mark.asyncio
    async def test_check_permission(self, async_db, test_user, test_organization):
        """Test checking notification permissions."""
        service = NotificationPreferenceService(async_db)
        
        # Create a disabled preference
        await service.create({
            "user_id": test_user.id,
            "category": "marketing",
            "channel": NotificationChannel.EMAIL,
            "enabled": False,
            "organization_id": test_organization.id
        })
        
        # Test disabled permission
        can_send = await service.check_permission(
            test_user.id, "marketing", NotificationChannel.EMAIL, test_organization.id
        )
        assert can_send is False
        
        # Test default permission (no preference set)
        can_send_default = await service.check_permission(
            test_user.id, "security", NotificationChannel.EMAIL, test_organization.id
        )
        assert can_send_default is True

    @pytest.mark.asyncio
    async def test_update_preference(self, async_db, test_user, test_organization):
        """Test updating notification preferences."""
        service = NotificationPreferenceService(async_db)
        
        # Create new preference
        preference = await service.update_preference(
            user_id=test_user.id,
            category="updates",
            channel=NotificationChannel.PUSH,
            enabled=True,
            frequency="daily",
            contact_info={"device_token": "abc123"},
            organization_id=test_organization.id
        )
        
        assert preference.enabled is True
        assert preference.frequency == "daily"
        assert preference.contact_info["device_token"] == "abc123"
        
        # Update existing preference
        updated_preference = await service.update_preference(
            user_id=test_user.id,
            category="updates",
            channel=NotificationChannel.PUSH,
            enabled=False,
            frequency="weekly",
            organization_id=test_organization.id
        )
        
        assert updated_preference.id == preference.id
        assert updated_preference.enabled is False
        assert updated_preference.frequency == "weekly"


class TestNotificationService:
    """Tests for main notification service."""

    @pytest.mark.asyncio
    async def test_send_notification(self, async_db, test_user, notification_template):
        """Test sending a single notification."""
        service = NotificationService(async_db)
        
        with patch.object(service, '_deliver_notification') as mock_deliver:
            mock_deliver.return_value = None
            
            notification = await service.send_notification(
                template_key="test_template",
                recipient_user_id=test_user.id,
                recipient_email="test@example.com",
                variables={"user_name": "Test User", "company": "Test Corp"},
                priority=NotificationPriority.HIGH
            )
            
            assert notification.template_id == notification_template.id
            assert notification.recipient_user_id == test_user.id
            assert notification.recipient_email == "test@example.com"
            assert notification.priority == NotificationPriority.HIGH
            assert "Test User" in notification.content
            
            # Verify delivery was attempted
            mock_deliver.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_invalid_template(self, async_db, test_user):
        """Test sending notification with invalid template."""
        service = NotificationService(async_db)
        
        with pytest.raises(ValueError, match="Template not found"):
            await service.send_notification(
                template_key="nonexistent_template",
                recipient_user_id=test_user.id
            )

    @pytest.mark.asyncio
    async def test_send_notification_user_disabled(self, async_db, test_user, notification_template):
        """Test sending notification to user who disabled it."""
        service = NotificationService(async_db)
        
        # Create disabled preference
        await service.preference_service.create({
            "user_id": test_user.id,
            "category": "test",
            "channel": NotificationChannel.EMAIL,
            "enabled": False
        })
        
        with pytest.raises(ValueError, match="User has disabled this type of notification"):
            await service.send_notification(
                template_key="test_template",
                recipient_user_id=test_user.id
            )

    @pytest.mark.asyncio
    async def test_send_batch_notification(self, async_db, test_user, notification_template):
        """Test sending batch notifications."""
        service = NotificationService(async_db)
        
        recipients = [
            {"user_id": test_user.id, "email": "user1@example.com"},
            {"email": "user2@example.com"},
            {"phone": "+1234567890"}
        ]
        
        batch_id = await service.send_batch_notification(
            template_key="test_template",
            recipients=recipients,
            variables={"company": "Test Corp"},
            priority=NotificationPriority.MEDIUM
        )
        
        assert batch_id is not None
        assert len(batch_id) > 0

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, async_db, test_user, test_organization):
        """Test getting user notifications."""
        service = NotificationService(async_db)
        
        # Create test notifications
        notification1 = await service.create({
            "recipient_user_id": test_user.id,
            "channel": NotificationChannel.EMAIL,
            "content": "Test notification 1",
            "organization_id": test_organization.id
        })
        
        notification2 = await service.create({
            "recipient_user_id": test_user.id,
            "channel": NotificationChannel.SMS,
            "content": "Test notification 2",
            "organization_id": test_organization.id,
            "opened_at": datetime.utcnow()
        })
        
        # Test getting all notifications
        all_notifications = await service.get_user_notifications(
            test_user.id, organization_id=test_organization.id
        )
        assert len(all_notifications) == 2
        
        # Test getting unread only
        unread_notifications = await service.get_user_notifications(
            test_user.id, unread_only=True, organization_id=test_organization.id
        )
        assert len(unread_notifications) == 1
        assert unread_notifications[0].id == notification1.id

    @pytest.mark.asyncio
    async def test_mark_as_opened(self, async_db, test_user):
        """Test marking notification as opened."""
        service = NotificationService(async_db)
        
        # Create test notification
        notification = await service.create({
            "recipient_user_id": test_user.id,
            "channel": NotificationChannel.EMAIL,
            "content": "Test notification"
        })
        
        # Mark as opened
        success = await service.mark_as_opened(notification.id, test_user.id)
        assert success is True
        
        # Verify it was marked as opened
        updated_notification = await service.get_by_id(notification.id)
        assert updated_notification.opened_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_opened_wrong_user(self, async_db, test_user, test_user2):
        """Test marking notification as opened by wrong user."""
        service = NotificationService(async_db)
        
        # Create test notification for user1
        notification = await service.create({
            "recipient_user_id": test_user.id,
            "channel": NotificationChannel.EMAIL,
            "content": "Test notification"
        })
        
        # Try to mark as opened by user2
        success = await service.mark_as_opened(notification.id, test_user2.id)
        assert success is False

    @pytest.mark.asyncio
    async def test_delivery_retry_logic(self, async_db, test_user, notification_template):
        """Test notification delivery retry logic."""
        service = NotificationService(async_db)
        
        # Mock delivery failure
        with patch.object(service, '_send_email') as mock_send:
            mock_send.side_effect = Exception("Delivery failed")
            
            notification = await service.create({
                "template_id": notification_template.id,
                "recipient_user_id": test_user.id,
                "recipient_email": "test@example.com",
                "channel": NotificationChannel.EMAIL,
                "content": "Test content",
                "status": NotificationStatus.PENDING
            })
            
            # Attempt delivery
            await service._deliver_notification(notification)
            
            # Check that notification was marked as failed and retry scheduled
            updated_notification = await service.get_by_id(notification.id)
            assert updated_notification.status == NotificationStatus.FAILED
            assert updated_notification.retry_count == 1
            assert updated_notification.error_message == "Delivery failed"


class TestNotificationHealthCheck:
    """Tests for notification system health check."""

    @pytest.mark.asyncio
    async def test_notification_health_check(self):
        """Test notification system health check."""
        from app.services.notification_service import check_notification_health
        
        health_info = await check_notification_health()
        
        assert "status" in health_info
        assert "template_count" in health_info
        assert "pending_notifications" in health_info
        assert "provider_status" in health_info
        
        # In test environment, this should be healthy
        assert health_info["status"] in ["healthy", "degraded"]


# Test fixtures
@pytest.fixture
async def notification_template(async_db, test_organization, test_user):
    """Create a test notification template."""
    service = NotificationTemplateService(async_db)
    
    template = await service.create_template(
        name="Test Template",
        template_key="test_template",
        channel=NotificationChannel.EMAIL,
        content_template="Hello {{user_name}} from {{company}}!",
        category="test",
        subject_template="Welcome {{user_name}}",
        html_template="<h1>Hello {{user_name}}</h1>",
        variables={"user_name": "string", "company": "string"},
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    return template


@pytest.fixture
async def test_user2(async_db, test_organization):
    """Create a second test user."""
    from app.models.user import User
    
    user = User(
        email="test2@example.com",
        hashed_password="hashed_password",
        full_name="Test User 2",
        is_active=True,
        organization_id=test_organization.id
    )
    
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    
    return user