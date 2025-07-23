"""
Notification System CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for notification system including:
- Multi-Channel Notifications (Email, SMS, Push, In-App)
- Real-Time Notifications & WebSocket Support
- Template-Based Messaging
- Notification Preferences & Settings
- Delivery Tracking & Analytics
- Subscription Management
- Event-Driven Notifications
- Notification History & Audit
- Rich Content & Attachments
- Integration & Webhook Support
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.notification_extended import (
    DeliveryStatus,
    NotificationAnalytics,
    NotificationChannel,
    NotificationDelivery,
    NotificationEvent,
    NotificationExtended,
    NotificationInteraction,
    NotificationPreference,
    NotificationPriority,
    NotificationQueue,
    NotificationRule,
    NotificationStatus,
    NotificationSubscription,
    NotificationTemplate,
    NotificationType,
    SubscriptionStatus,
)


class NotificationService:
    """Service class for notification system operations."""

    # =============================================================================
    # Notification Management
    # =============================================================================

    async def create_notification(
        self, db: Session, notification_data: dict
    ) -> NotificationExtended:
        """Create a new notification with comprehensive content and targeting."""

        # Generate unique notification number
        notification_number = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"

        # Process rich content if provided
        if "rich_content" not in notification_data:
            notification_data["rich_content"] = {}

        # Set default channels if not provided
        if "channels" not in notification_data:
            notification_data["channels"] = ["in_app"]

        # Create notification record
        notification = NotificationExtended(
            notification_number=notification_number,
            title=notification_data["title"],
            message=notification_data["message"],
            summary=notification_data.get("summary"),
            notification_type=notification_data["notification_type"],
            category=notification_data.get("category"),
            subcategory=notification_data.get("subcategory"),
            priority=notification_data.get("priority", NotificationPriority.NORMAL),
            organization_id=notification_data["organization_id"],
            recipient_user_id=notification_data.get("recipient_user_id"),
            recipient_email=notification_data.get("recipient_email"),
            recipient_phone=notification_data.get("recipient_phone"),
            recipient_groups=notification_data.get("recipient_groups", []),
            recipient_roles=notification_data.get("recipient_roles", []),
            target_audience=notification_data.get("target_audience", {}),
            content_html=notification_data.get("content_html"),
            content_plain=notification_data.get("content_plain"),
            content_markdown=notification_data.get("content_markdown"),
            rich_content=notification_data["rich_content"],
            attachments=notification_data.get("attachments", []),
            channels=notification_data["channels"],
            primary_channel=notification_data.get(
                "primary_channel", NotificationChannel.IN_APP
            ),
            fallback_channels=notification_data.get("fallback_channels", []),
            send_at=notification_data.get("send_at"),
            scheduled_at=notification_data.get("scheduled_at"),
            expires_at=notification_data.get("expires_at"),
            timezone=notification_data.get("timezone"),
            template_id=notification_data.get("template_id"),
            template_variables=notification_data.get("template_variables", {}),
            personalization_data=notification_data.get("personalization_data", {}),
            source_system=notification_data.get("source_system"),
            source_event=notification_data.get("source_event"),
            source_entity_type=notification_data.get("source_entity_type"),
            source_entity_id=notification_data.get("source_entity_id"),
            context_data=notification_data.get("context_data", {}),
            action_buttons=notification_data.get("action_buttons", []),
            deep_link_url=notification_data.get("deep_link_url"),
            tracking_params=notification_data.get("tracking_params", {}),
            tags=notification_data.get("tags", []),
            metadata=notification_data.get("metadata", {}),
            custom_fields=notification_data.get("custom_fields", {}),
            created_by=notification_data.get("created_by"),
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Queue for delivery if scheduled or immediate
        if notification.send_at and notification.send_at <= datetime.utcnow():
            await self._queue_notification(db, notification.id)
        elif not notification.send_at:
            await self._queue_notification(db, notification.id)

        return notification

    async def get_notification_by_id(
        self, db: Session, notification_id: str
    ) -> Optional[NotificationExtended]:
        """Get notification by ID with full details."""
        return (
            db.query(NotificationExtended)
            .options(
                joinedload(NotificationExtended.recipient_user),
                joinedload(NotificationExtended.template),
                joinedload(NotificationExtended.deliveries),
                joinedload(NotificationExtended.interactions),
            )
            .filter(NotificationExtended.id == notification_id)
            .first()
        )

    async def get_notifications(
        self,
        db: Session,
        organization_id: str,
        recipient_user_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
        priority: Optional[NotificationPriority] = None,
        channel: Optional[NotificationChannel] = None,
        category: Optional[str] = None,
        is_read: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[NotificationExtended]:
        """Get notifications with comprehensive filtering options."""

        query = db.query(NotificationExtended).filter(
            NotificationExtended.organization_id == organization_id
        )

        if recipient_user_id:
            query = query.filter(
                NotificationExtended.recipient_user_id == recipient_user_id
            )

        if notification_type:
            query = query.filter(
                NotificationExtended.notification_type == notification_type
            )

        if status:
            query = query.filter(NotificationExtended.status == status)

        if priority:
            query = query.filter(NotificationExtended.priority == priority)

        if channel:
            query = query.filter(
                NotificationExtended.channels.contains([channel.value])
            )

        if category:
            query = query.filter(NotificationExtended.category == category)

        if is_read is not None:
            query = query.filter(NotificationExtended.is_read == is_read)

        if created_after:
            query = query.filter(NotificationExtended.created_at >= created_after)

        if created_before:
            query = query.filter(NotificationExtended.created_at <= created_before)

        return (
            query.order_by(desc(NotificationExtended.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def mark_notification_as_read(
        self, db: Session, notification_id: str, user_id: str
    ) -> Optional[NotificationExtended]:
        """Mark notification as read and track interaction."""

        notification = (
            db.query(NotificationExtended)
            .filter(NotificationExtended.id == notification_id)
            .first()
        )

        if not notification:
            return None

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        notification.view_count += 1

        # Log interaction
        await self._log_notification_interaction(
            db,
            notification_id,
            user_id,
            "read",
            {"channel": "in_app", "timestamp": datetime.utcnow().isoformat()},
        )

        db.commit()
        db.refresh(notification)

        return notification

    async def archive_notification(
        self, db: Session, notification_id: str, user_id: str
    ) -> Optional[NotificationExtended]:
        """Archive notification for user."""

        notification = (
            db.query(NotificationExtended)
            .filter(NotificationExtended.id == notification_id)
            .first()
        )

        if not notification:
            return None

        notification.is_archived = True
        notification.archived_at = datetime.utcnow()

        # Log interaction
        await self._log_notification_interaction(
            db, notification_id, user_id, "archive"
        )

        db.commit()
        return notification

    # =============================================================================
    # Template Management
    # =============================================================================

    async def create_notification_template(
        self, db: Session, template_data: dict
    ) -> NotificationTemplate:
        """Create a new notification template."""

        template = NotificationTemplate(
            name=template_data["name"],
            code=template_data["code"],
            description=template_data.get("description"),
            category=template_data.get("category"),
            subject_template=template_data.get("subject_template"),
            title_template=template_data.get("title_template"),
            message_template=template_data["message_template"],
            html_template=template_data.get("html_template"),
            plain_template=template_data.get("plain_template"),
            notification_type=template_data["notification_type"],
            default_priority=template_data.get(
                "default_priority", NotificationPriority.NORMAL
            ),
            default_channels=template_data.get("default_channels", ["in_app"]),
            variables=template_data.get("variables", []),
            required_variables=template_data.get("required_variables", []),
            default_values=template_data.get("default_values", {}),
            validation_rules=template_data.get("validation_rules", {}),
            styling=template_data.get("styling", {}),
            layout=template_data.get("layout"),
            theme=template_data.get("theme"),
            language=template_data.get("language", "en"),
            localized_versions=template_data.get("localized_versions", {}),
            organization_id=template_data["organization_id"],
            owner_id=template_data["owner_id"],
            is_public=template_data.get("is_public", False),
            tags=template_data.get("tags", []),
            metadata=template_data.get("metadata", {}),
            created_by=template_data["created_by"],
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        return template

    async def generate_notification_from_template(
        self,
        db: Session,
        template_id: str,
        variables: Dict[str, Any],
        notification_data: dict,
    ) -> NotificationExtended:
        """Generate notification from template with variable substitution."""

        template = (
            db.query(NotificationTemplate)
            .filter(NotificationTemplate.id == template_id)
            .first()
        )

        if not template:
            raise ValueError("Template not found")

        # Process template variables
        processed_title = self._process_template_variables(
            template.title_template or template.name, variables
        )
        processed_message = self._process_template_variables(
            template.message_template, variables
        )
        processed_html = None
        if template.html_template:
            processed_html = self._process_template_variables(
                template.html_template, variables
            )

        # Create notification with processed content
        notification_data.update(
            {
                "title": processed_title,
                "message": processed_message,
                "content_html": processed_html,
                "notification_type": template.notification_type,
                "channels": template.default_channels,
                "priority": template.default_priority,
                "template_id": template_id,
                "template_variables": variables,
            }
        )

        notification = await self.create_notification(db, notification_data)

        # Update template usage statistics
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        db.commit()

        return notification

    def _process_template_variables(
        self, template_text: str, variables: Dict[str, Any]
    ) -> str:
        """Process template variables in text."""
        if not template_text:
            return ""

        result = template_text
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    # =============================================================================
    # Delivery Management
    # =============================================================================

    async def create_delivery_record(
        self,
        db: Session,
        notification_id: str,
        channel: NotificationChannel,
        recipient_address: str,
        delivery_data: Optional[dict] = None,
    ) -> NotificationDelivery:
        """Create delivery record for notification channel."""

        notification = await self.get_notification_by_id(db, notification_id)
        if not notification:
            raise ValueError("Notification not found")

        delivery = NotificationDelivery(
            notification_id=notification_id,
            organization_id=notification.organization_id,
            channel=channel,
            recipient_address=recipient_address,
            recipient_name=delivery_data.get("recipient_name")
            if delivery_data
            else None,
            recipient_type=delivery_data.get("recipient_type", "user")
            if delivery_data
            else "user",
            subject=notification.title,
            content=notification.message,
            formatted_content=notification.content_html or notification.message,
            scheduled_at=notification.send_at or datetime.utcnow(),
            provider=delivery_data.get("provider") if delivery_data else None,
            metadata=delivery_data.get("metadata", {}) if delivery_data else {},
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        return delivery

    async def update_delivery_status(
        self,
        db: Session,
        delivery_id: str,
        status: DeliveryStatus,
        provider_data: Optional[dict] = None,
    ) -> Optional[NotificationDelivery]:
        """Update delivery status with provider response."""

        delivery = (
            db.query(NotificationDelivery)
            .filter(NotificationDelivery.id == delivery_id)
            .first()
        )

        if not delivery:
            return None

        delivery.status = status
        delivery.updated_at = datetime.utcnow()

        if status == DeliveryStatus.SENT:
            delivery.sent_at = datetime.utcnow()
        elif status == DeliveryStatus.DELIVERED:
            delivery.delivered_at = datetime.utcnow()
        elif status == DeliveryStatus.FAILED:
            delivery.failed_at = datetime.utcnow()
            delivery.retry_count += 1

        if provider_data:
            delivery.provider_message_id = provider_data.get("message_id")
            delivery.delivery_response = provider_data.get("response")
            delivery.error_code = provider_data.get("error_code")
            delivery.error_message = provider_data.get("error_message")
            delivery.tracking_id = provider_data.get("tracking_id")
            delivery.delivery_cost = provider_data.get("cost")

        db.commit()
        return delivery

    # =============================================================================
    # Preference Management
    # =============================================================================

    async def get_user_notification_preferences(
        self, db: Session, user_id: str, organization_id: str
    ) -> Optional[NotificationPreference]:
        """Get user notification preferences."""

        preferences = (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.organization_id == organization_id,
            )
            .first()
        )

        # Create default preferences if none exist
        if not preferences:
            preferences = await self._create_default_preferences(
                db, user_id, organization_id
            )

        return preferences

    async def update_user_notification_preferences(
        self, db: Session, user_id: str, organization_id: str, preferences_data: dict
    ) -> NotificationPreference:
        """Update user notification preferences."""

        preferences = await self.get_user_notification_preferences(
            db, user_id, organization_id
        )

        # Update preference fields
        for field, value in preferences_data.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)

        return preferences

    async def _create_default_preferences(
        self, db: Session, user_id: str, organization_id: str
    ) -> NotificationPreference:
        """Create default notification preferences for user."""

        preferences = NotificationPreference(
            user_id=user_id,
            organization_id=organization_id,
            is_enabled=True,
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True,
            in_app_enabled=True,
            system_notifications=True,
            alert_notifications=True,
            warning_notifications=True,
            info_notifications=True,
            reminder_notifications=True,
            task_notifications=True,
            message_notifications=True,
            announcement_notifications=True,
            quiet_hours_enabled=False,
            max_emails_per_day=50,
            max_sms_per_day=10,
            digest_frequency="daily",
            language_preference="en",
            content_format="html",
            grouping_enabled=True,
        )

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

        return preferences

    # =============================================================================
    # Subscription Management
    # =============================================================================

    async def create_notification_subscription(
        self, db: Session, subscription_data: dict
    ) -> NotificationSubscription:
        """Create notification subscription for user."""

        subscription = NotificationSubscription(
            user_id=subscription_data["user_id"],
            organization_id=subscription_data["organization_id"],
            topic=subscription_data["topic"],
            event_type=subscription_data.get("event_type"),
            entity_type=subscription_data.get("entity_type"),
            entity_id=subscription_data.get("entity_id"),
            status=subscription_data.get("status", SubscriptionStatus.ACTIVE),
            channels=subscription_data.get("channels", ["in_app"]),
            priority=subscription_data.get("priority", NotificationPriority.NORMAL),
            filters=subscription_data.get("filters", {}),
            conditions=subscription_data.get("conditions", {}),
            keywords=subscription_data.get("keywords", []),
            frequency=subscription_data.get("frequency", "instant"),
            delivery_time=subscription_data.get("delivery_time"),
            timezone=subscription_data.get("timezone"),
            name=subscription_data.get("name"),
            description=subscription_data.get("description"),
            auto_created=subscription_data.get("auto_created", False),
            expires_at=subscription_data.get("expires_at"),
            metadata=subscription_data.get("metadata", {}),
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        return subscription

    async def get_user_subscriptions(
        self,
        db: Session,
        user_id: str,
        organization_id: str,
        status: Optional[SubscriptionStatus] = None,
    ) -> List[NotificationSubscription]:
        """Get user notification subscriptions."""

        query = db.query(NotificationSubscription).filter(
            NotificationSubscription.user_id == user_id,
            NotificationSubscription.organization_id == organization_id,
        )

        if status:
            query = query.filter(NotificationSubscription.status == status)

        return query.order_by(NotificationSubscription.created_at).all()

    async def unsubscribe_user(
        self, db: Session, subscription_id: str, user_id: str
    ) -> bool:
        """Unsubscribe user from notification topic."""

        subscription = (
            db.query(NotificationSubscription)
            .filter(
                NotificationSubscription.id == subscription_id,
                NotificationSubscription.user_id == user_id,
            )
            .first()
        )

        if not subscription:
            return False

        subscription.status = SubscriptionStatus.INACTIVE
        subscription.updated_at = datetime.utcnow()

        db.commit()
        return True

    # =============================================================================
    # Event Processing
    # =============================================================================

    async def process_notification_event(
        self, db: Session, event_data: dict
    ) -> List[NotificationExtended]:
        """Process notification event and trigger rules."""

        # Create event record
        event = NotificationEvent(
            organization_id=event_data["organization_id"],
            event_name=event_data["event_name"],
            event_type=event_data["event_type"],
            source_system=event_data.get("source_system"),
            event_data=event_data.get("event_data", {}),
            entity_type=event_data.get("entity_type"),
            entity_id=event_data.get("entity_id"),
            priority=event_data.get("priority", NotificationPriority.NORMAL),
            batch_id=event_data.get("batch_id"),
            correlation_id=event_data.get("correlation_id"),
            event_timestamp=event_data.get("event_timestamp", datetime.utcnow()),
        )

        db.add(event)
        db.commit()

        # Find matching notification rules
        matching_rules = await self._find_matching_rules(db, event)

        # Generate notifications from rules
        generated_notifications = []
        for rule in matching_rules:
            notifications = await self._generate_notifications_from_rule(
                db, rule, event
            )
            generated_notifications.extend(notifications)

        # Mark event as processed
        event.is_processed = True
        event.processed_at = datetime.utcnow()
        db.commit()

        return generated_notifications

    async def _find_matching_rules(
        self, db: Session, event: NotificationEvent
    ) -> List[NotificationRule]:
        """Find notification rules that match the event."""

        rules = (
            db.query(NotificationRule)
            .filter(
                NotificationRule.organization_id == event.organization_id,
                NotificationRule.is_active,
            )
            .all()
        )

        matching_rules = []
        for rule in rules:
            if self._rule_matches_event(rule, event):
                matching_rules.append(rule)

        return matching_rules

    def _rule_matches_event(
        self, rule: NotificationRule, event: NotificationEvent
    ) -> bool:
        """Check if rule matches event criteria."""

        # Check trigger events
        if rule.trigger_events and event.event_name not in rule.trigger_events:
            return False

        # Check entity type filter
        if (
            rule.filters.get("entity_type")
            and event.entity_type != rule.filters["entity_type"]
        ):
            return False

        # Add more sophisticated matching logic here
        return True

    async def _generate_notifications_from_rule(
        self, db: Session, rule: NotificationRule, event: NotificationEvent
    ) -> List[NotificationExtended]:
        """Generate notifications based on rule configuration."""

        notifications = []

        # Determine recipients based on rule
        recipients = await self._determine_rule_recipients(db, rule, event)

        for recipient in recipients:
            # Create notification data
            notification_data = {
                "organization_id": rule.organization_id,
                "title": f"Event: {event.event_name}",
                "message": f"Event {event.event_name} occurred",
                "notification_type": rule.notification_type or NotificationType.INFO,
                "priority": rule.priority_override or NotificationPriority.NORMAL,
                "channels": rule.channels,
                "recipient_user_id": recipient.get("user_id"),
                "recipient_email": recipient.get("email"),
                "template_id": rule.template_id,
                "template_variables": self._build_template_variables(rule, event),
                "source_system": event.source_system,
                "source_event": event.event_name,
                "source_entity_type": event.entity_type,
                "source_entity_id": event.entity_id,
                "context_data": event.event_data,
            }

            # Apply delay if configured
            if rule.delay_seconds:
                notification_data["send_at"] = datetime.utcnow() + timedelta(
                    seconds=rule.delay_seconds
                )

            notification = await self.create_notification(db, notification_data)
            notifications.append(notification)

        # Update rule execution statistics
        rule.execution_count += 1
        rule.last_executed_at = datetime.utcnow()
        if notifications:
            rule.success_count += len(notifications)

        db.commit()

        return notifications

    async def _determine_rule_recipients(
        self, db: Session, rule: NotificationRule, event: NotificationEvent
    ) -> List[Dict[str, Any]]:
        """Determine recipients for rule-based notification."""

        recipients = []

        # Add target users
        for user_id in rule.target_users:
            recipients.append({"user_id": user_id})

        # Add users from target groups and roles
        # Implementation would query users by group/role membership

        return recipients

    def _build_template_variables(
        self, rule: NotificationRule, event: NotificationEvent
    ) -> Dict[str, Any]:
        """Build template variables from rule and event data."""

        variables = {}

        # Add event data
        variables.update(event.event_data)

        # Add rule-specific mappings
        for key, mapping in rule.variable_mappings.items():
            if mapping in event.event_data:
                variables[key] = event.event_data[mapping]

        # Add standard variables
        variables.update(
            {
                "event_name": event.event_name,
                "event_type": event.event_type,
                "event_timestamp": event.event_timestamp.isoformat(),
                "organization_id": event.organization_id,
            }
        )

        return variables

    # =============================================================================
    # Analytics and Reporting
    # =============================================================================

    async def get_notification_analytics(
        self, db: Session, organization_id: str, period_start: date, period_end: date
    ) -> NotificationAnalytics:
        """Generate comprehensive notification analytics."""

        # Basic notification metrics
        total_notifications = (
            db.query(NotificationExtended)
            .filter(
                NotificationExtended.organization_id == organization_id,
                NotificationExtended.created_at >= period_start,
                NotificationExtended.created_at <= period_end,
            )
            .count()
        )

        notifications_sent = (
            db.query(NotificationExtended)
            .filter(
                NotificationExtended.organization_id == organization_id,
                NotificationExtended.status == NotificationStatus.SENT,
                NotificationExtended.sent_at >= period_start,
                NotificationExtended.sent_at <= period_end,
            )
            .count()
        )

        notifications_read = (
            db.query(NotificationExtended)
            .filter(
                NotificationExtended.organization_id == organization_id,
                NotificationExtended.is_read,
                NotificationExtended.read_at >= period_start,
                NotificationExtended.read_at <= period_end,
            )
            .count()
        )

        # Channel-specific metrics
        email_deliveries = db.query(NotificationDelivery).filter(
            NotificationDelivery.organization_id == organization_id,
            NotificationDelivery.channel == NotificationChannel.EMAIL,
            NotificationDelivery.created_at >= period_start,
            NotificationDelivery.created_at <= period_end,
        )

        email_sent = email_deliveries.count()
        email_delivered = email_deliveries.filter(
            NotificationDelivery.status == DeliveryStatus.DELIVERED
        ).count()
        email_opened = email_deliveries.filter(
            NotificationDelivery.opened_at.isnot(None)
        ).count()
        email_clicked = email_deliveries.filter(
            NotificationDelivery.clicked_at.isnot(None)
        ).count()

        # Calculate rates
        delivery_rate = (
            (notifications_sent / total_notifications * 100)
            if total_notifications > 0
            else 0
        )
        read_rate = (
            (notifications_read / notifications_sent * 100)
            if notifications_sent > 0
            else 0
        )
        (email_opened / email_delivered * 100) if email_delivered > 0 else 0
        email_click_rate = (
            (email_clicked / email_opened * 100) if email_opened > 0 else 0
        )

        # Engagement metrics
        total_views = (
            db.query(func.sum(NotificationExtended.view_count))
            .filter(
                NotificationExtended.organization_id == organization_id,
                NotificationExtended.created_at >= period_start,
                NotificationExtended.created_at <= period_end,
            )
            .scalar()
            or 0
        )

        total_clicks = (
            db.query(func.sum(NotificationExtended.click_count))
            .filter(
                NotificationExtended.organization_id == organization_id,
                NotificationExtended.created_at >= period_start,
                NotificationExtended.created_at <= period_end,
            )
            .scalar()
            or 0
        )

        # Create analytics record
        analytics = NotificationAnalytics(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            total_notifications=total_notifications,
            notifications_sent=notifications_sent,
            notifications_delivered=notifications_sent,  # Simplified
            notifications_read=notifications_read,
            email_sent=email_sent,
            email_delivered=email_delivered,
            email_opened=email_opened,
            email_clicked=email_clicked,
            total_views=total_views,
            total_clicks=total_clicks,
            delivery_success_rate=delivery_rate,
            open_rate=read_rate,
            click_rate=email_click_rate,
            calculated_date=datetime.utcnow(),
        )

        db.add(analytics)
        db.commit()
        db.refresh(analytics)

        return analytics

    # =============================================================================
    # Queue and Delivery Management
    # =============================================================================

    async def _queue_notification(
        self, db: Session, notification_id: str, priority: int = 100
    ):
        """Queue notification for processing."""

        notification = await self.get_notification_by_id(db, notification_id)
        if not notification:
            return

        queue_item = NotificationQueue(
            notification_id=notification_id,
            organization_id=notification.organization_id,
            priority=priority,
            scheduled_at=notification.send_at or datetime.utcnow(),
            process_after=notification.send_at or datetime.utcnow(),
        )

        db.add(queue_item)
        db.commit()

    async def process_notification_queue(
        self, db: Session, queue_name: str = "default", batch_size: int = 100
    ) -> List[NotificationExtended]:
        """Process queued notifications for delivery."""

        # Get pending queue items
        queue_items = (
            db.query(NotificationQueue)
            .filter(
                NotificationQueue.queue_name == queue_name,
                NotificationQueue.status == "pending",
                NotificationQueue.process_after <= datetime.utcnow(),
            )
            .order_by(NotificationQueue.priority.desc(), NotificationQueue.created_at)
            .limit(batch_size)
            .all()
        )

        processed_notifications = []

        for item in queue_items:
            try:
                # Mark as processing
                item.status = "processing"
                db.commit()

                # Process notification
                notification = await self.get_notification_by_id(
                    db, item.notification_id
                )
                if notification:
                    await self._deliver_notification(db, notification)
                    processed_notifications.append(notification)

                # Mark as completed
                item.status = "completed"
                item.processed_at = datetime.utcnow()

            except Exception as e:
                # Mark as failed
                item.status = "failed"
                item.error_message = str(e)
                item.attempts += 1

                # Retry if not exceeded max attempts
                if item.attempts < item.max_attempts:
                    item.status = "pending"
                    item.process_after = datetime.utcnow() + timedelta(
                        minutes=5 * item.attempts
                    )

            db.commit()

        return processed_notifications

    async def _deliver_notification(
        self, db: Session, notification: NotificationExtended
    ):
        """Deliver notification through configured channels."""

        for channel_name in notification.channels:
            channel = NotificationChannel(channel_name)

            # Determine recipient address for channel
            recipient_address = self._get_recipient_address_for_channel(
                notification, channel
            )
            if not recipient_address:
                continue

            # Create delivery record
            delivery = await self.create_delivery_record(
                db, notification.id, channel, recipient_address
            )

            # Process delivery based on channel
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._deliver_email(db, delivery)
                elif channel == NotificationChannel.SMS:
                    await self._deliver_sms(db, delivery)
                elif channel == NotificationChannel.PUSH:
                    await self._deliver_push(db, delivery)
                elif channel == NotificationChannel.IN_APP:
                    await self._deliver_in_app(db, delivery)

                await self.update_delivery_status(db, delivery.id, DeliveryStatus.SENT)

            except Exception as e:
                await self.update_delivery_status(
                    db, delivery.id, DeliveryStatus.FAILED, {"error_message": str(e)}
                )

        # Update notification status
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()
        db.commit()

    def _get_recipient_address_for_channel(
        self, notification: NotificationExtended, channel: NotificationChannel
    ) -> Optional[str]:
        """Get recipient address for specific channel."""

        if channel == NotificationChannel.EMAIL:
            return notification.recipient_email
        elif channel == NotificationChannel.SMS:
            return notification.recipient_phone
        elif channel == NotificationChannel.IN_APP:
            return notification.recipient_user_id
        elif channel == NotificationChannel.PUSH:
            return notification.recipient_user_id

        return None

    async def _deliver_email(self, db: Session, delivery: NotificationDelivery) -> dict:
        """Deliver notification via email."""
        # Implementation would integrate with email service (AWS SES, SendGrid, etc.)
        pass

    async def _deliver_sms(self, db: Session, delivery: NotificationDelivery) -> dict:
        """Deliver notification via SMS."""
        # Implementation would integrate with SMS service (Twilio, AWS SNS, etc.)
        pass

    async def _deliver_push(self, db: Session, delivery: NotificationDelivery) -> dict:
        """Deliver notification via push notification."""
        # Implementation would integrate with push service (Firebase, APNs, etc.)
        pass

    async def _deliver_in_app(self, db: Session, delivery: NotificationDelivery) -> dict:
        """Deliver in-app notification."""
        # In-app notifications are already created in database
        await self.update_delivery_status(db, delivery.id, DeliveryStatus.DELIVERED)

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _log_notification_interaction(
        self,
        db: Session,
        notification_id: str,
        user_id: str,
        interaction_type: str,
        interaction_data: Optional[Dict[str, Any]] = None,
    ):
        """Log notification interaction for analytics."""

        notification = await self.get_notification_by_id(db, notification_id)
        if not notification:
            return

        interaction = NotificationInteraction(
            notification_id=notification_id,
            organization_id=notification.organization_id,
            user_id=user_id,
            interaction_type=interaction_type,
            interaction_data=interaction_data or {},
            channel=NotificationChannel.IN_APP,  # Default to in-app
        )

        db.add(interaction)
        db.commit()

    async def get_system_health(self, db: Session) -> Dict[str, Any]:
        """Get notification system health status."""

        try:
            # Test database connectivity
            db.execute("SELECT 1")

            # Get basic statistics
            total_notifications = db.query(NotificationExtended).count()
            pending_queue = (
                db.query(NotificationQueue)
                .filter(NotificationQueue.status == "pending")
                .count()
            )

            return {
                "status": "healthy",
                "database_connection": "OK",
                "services_available": True,
                "statistics": {
                    "total_notifications": total_notifications,
                    "pending_queue_items": pending_queue,
                },
                "version": "31.0",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
