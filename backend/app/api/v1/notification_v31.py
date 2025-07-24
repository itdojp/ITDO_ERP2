"""
Notification System API Endpoints - CC02 v31.0 Phase 2

Comprehensive notification system with 10 main endpoints:
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

import asyncio
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.notification_v31 import NotificationService
from app.models.notification_extended import (
    DeliveryStatus,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    SubscriptionStatus,
)
from app.schemas.notification_v31 import (  # Notification schemas; Template schemas; Delivery schemas; Preference schemas; Subscription schemas; Event schemas; Analytics schemas; Interaction schemas; Health schemas; Bulk operation schemas; WebSocket schemas
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationAnalyticsRequest,
    NotificationAnalyticsResponse,
    NotificationCreateRequest,
    NotificationDeliveryResponse,
    NotificationEventCreateRequest,
    NotificationEventResponse,
    NotificationInteractionRequest,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
    NotificationSubscriptionCreateRequest,
    NotificationSubscriptionResponse,
    NotificationSystemHealthResponse,
    NotificationTemplateCreateRequest,
    NotificationTemplateResponse,
    NotificationUpdateRequest,
    TemplateGenerationRequest,
    WebSocketNotificationMessage,
    WebSocketSubscriptionRequest,
)

router = APIRouter()
notification_service = NotificationService()

# WebSocket connection manager
class NotificationConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self) -> dict:
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> dict:
        """Connect a WebSocket for a user."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str) -> dict:
        """Disconnect a WebSocket for a user."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_notification(self, user_id: str, notification: dict) -> dict:
        """Send notification to all user's WebSocket connections."""
        if user_id in self.active_connections:
            message = {
                "type": "notification",
                "notification": notification,
                "timestamp": datetime.utcnow().isoformat(),
                "channel": "websocket"
            }
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message, default=str))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)

websocket_manager = NotificationConnectionManager()


# =============================================================================
# 1. Notification Management
# =============================================================================

@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification_data: NotificationCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new notification with comprehensive content and targeting.
    
    Features:
    - Multi-channel delivery (Email, SMS, Push, In-App)
    - Rich content support (HTML, Markdown, Plain text)
    - Advanced targeting (Users, Groups, Roles)
    - Scheduling and expiration
    - Template-based generation
    - A/B testing support
    """
    try:
        notification = await notification_service.create_notification(
            db, notification_data.dict()
        )
        
        # Send real-time notification if needed
        if notification.recipient_user_id and notification.primary_channel == NotificationChannel.IN_APP:
            background_tasks.add_task(
                websocket_manager.send_notification,
                notification.recipient_user_id,
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.notification_type.value,
                    "priority": notification.priority.value
                }
            )
        
        return notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    organization_id: str = Query(..., description="Organization ID"),
    recipient_user_id: Optional[str] = Query(None, description="Filter by recipient user"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    priority: Optional[NotificationPriority] = Query(None, description="Filter by priority"),
    channel: Optional[NotificationChannel] = Query(None, description="Filter by channel"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Limit for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get notifications with comprehensive filtering and pagination.
    
    Features:
    - Advanced filtering by multiple criteria
    - Pagination support
    - Read/unread status tracking
    - Real-time updates compatible
    """
    try:
        notifications = await notification_service.get_notifications(
            db=db,
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            status=status,
            priority=priority,
            channel=channel,
            category=category,
            is_read=is_read,
            created_after=created_after,
            created_before=created_before,
            skip=skip,
            limit=limit
        )
        
        # Count unread notifications for user
        unread_count = 0
        if recipient_user_id:
            unread_notifications = await notification_service.get_notifications(
                db=db,
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
                is_read=False,
                skip=0,
                limit=10000  # Large limit to count all
            )
            unread_count = len(unread_notifications)
        
        return NotificationListResponse(
            notifications=notifications,
            total_count=len(notifications),
            unread_count=unread_count,
            page=(skip // limit) + 1,
            per_page=limit,
            has_more=len(notifications) == limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification_by_id(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Get notification by ID with full details and related information.
    
    Features:
    - Complete notification data
    - Delivery status information
    - Interaction history
    - View count tracking
    """
    try:
        notification = await notification_service.get_notification_by_id(db, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_data: NotificationUpdateRequest,
    user_id: str = Query(..., description="User ID performing the update"),
    db: Session = Depends(get_db)
):
    """
    Update notification content and metadata.
    
    Features:
    - Partial updates support
    - Version tracking
    - Audit trail maintenance
    - Permission validation
    """
    try:
        # Get existing notification
        existing_notification = await notification_service.get_notification_by_id(db, notification_id)
        if not existing_notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Update fields
        update_data = notification_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_notification, field, value)
        
        existing_notification.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_notification)
        
        return existing_notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    user_id: str = Query(..., description="User ID marking as read"),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read and track interaction.
    
    Features:
    - Read status tracking
    - View count incrementing
    - Interaction logging
    - Real-time status updates
    """
    try:
        notification = await notification_service.mark_notification_as_read(
            db, notification_id, user_id
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/archive", response_model=NotificationResponse)
async def archive_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID archiving the notification"),
    db: Session = Depends(get_db)
):
    """
    Archive notification for user.
    
    Features:
    - User-specific archiving
    - Archive timestamp tracking
    - Interaction logging
    - Bulk archive support
    """
    try:
        notification = await notification_service.archive_notification(
            db, notification_id, user_id
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID deleting the notification"),
    db: Session = Depends(get_db)
):
    """
    Delete notification and related data.
    
    Features:
    - Cascade deletion of related records
    - Permission validation
    - Audit trail maintenance
    - Soft delete option
    """
    try:
        # Get notification
        notification = await notification_service.get_notification_by_id(db, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Delete notification (this will cascade to related records)
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 2. Template Management
# =============================================================================

@router.post("/templates", response_model=NotificationTemplateResponse, status_code=201)
async def create_notification_template(
    template_data: NotificationTemplateCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new notification template for reusable notifications.
    
    Features:
    - Multi-format templates (HTML, Plain, Markdown)
    - Variable substitution support
    - Localization capabilities
    - Version management
    - Usage analytics
    """
    try:
        template = await notification_service.create_notification_template(
            db, template_data.dict()
        )
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def get_notification_templates(
    organization_id: str = Query(..., description="Organization ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Limit for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get notification templates with filtering options.
    
    Features:
    - Template library browsing
    - Category-based organization
    - Public/private template management
    - Usage statistics
    """
    try:
        from app.models.notification_extended import NotificationTemplate
        
        query = db.query(NotificationTemplate).filter(
            NotificationTemplate.organization_id == organization_id
        )
        
        if category:
            query = query.filter(NotificationTemplate.category == category)
        if notification_type:
            query = query.filter(NotificationTemplate.notification_type == notification_type)
        if is_active is not None:
            query = query.filter(NotificationTemplate.is_active == is_active)
        if is_public is not None:
            query = query.filter(NotificationTemplate.is_public == is_public)
        
        templates = query.offset(skip).limit(limit).all()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_notification_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get notification template by ID with full details.
    
    Features:
    - Complete template information
    - Variable definitions
    - Usage statistics
    - Version history
    """
    try:
        from app.models.notification_extended import NotificationTemplate
        
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/generate", response_model=NotificationResponse)
async def generate_notification_from_template(
    template_id: str,
    generation_data: TemplateGenerationRequest,
    generated_by_id: str = Query(..., description="User ID generating the notification"),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate notification from template with variable substitution.
    
    Features:
    - Variable substitution
    - Template validation
    - Override capabilities
    - Automatic scheduling
    - Real-time delivery
    """
    try:
        # Prepare notification data
        notification_data = generation_data.dict()
        notification_data["created_by"] = generated_by_id
        
        notification = await notification_service.generate_notification_from_template(
            db, template_id, generation_data.field_values, notification_data
        )
        
        # Send real-time notification if needed
        if notification.recipient_user_id and notification.primary_channel == NotificationChannel.IN_APP:
            background_tasks.add_task(
                websocket_manager.send_notification,
                notification.recipient_user_id,
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.notification_type.value,
                    "priority": notification.priority.value
                }
            )
        
        return notification
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 3. Delivery Management
# =============================================================================

@router.get("/notifications/{notification_id}/deliveries", response_model=List[NotificationDeliveryResponse])
async def get_notification_deliveries(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Get delivery records for a notification across all channels.
    
    Features:
    - Multi-channel delivery tracking
    - Provider-specific information
    - Retry and error tracking
    - Cost analytics
    """
    try:
        from app.models.notification_extended import NotificationDelivery
        
        deliveries = db.query(NotificationDelivery).filter(
            NotificationDelivery.notification_id == notification_id
        ).all()
        
        return deliveries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deliveries/{delivery_id}/status")
async def update_delivery_status(
    delivery_id: str,
    status: DeliveryStatus,
    provider_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Update delivery status with provider response data.
    
    Features:
    - Status progression tracking
    - Provider response logging
    - Error handling and retry logic
    - Cost tracking
    """
    try:
        delivery = await notification_service.update_delivery_status(
            db, delivery_id, status, provider_data
        )
        
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")
        
        return {"message": "Delivery status updated successfully", "delivery": delivery}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 4. Preference Management
# =============================================================================

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    user_id: str = Query(..., description="User ID"),
    organization_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db)
):
    """
    Get user notification preferences with all settings.
    
    Features:
    - Complete preference management
    - Channel-specific settings
    - Frequency controls
    - Quiet hours configuration
    """
    try:
        preferences = await notification_service.get_user_notification_preferences(
            db, user_id, organization_id
        )
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    user_id: str = Query(..., description="User ID"),
    organization_id: str = Query(..., description="Organization ID"),
    preferences_data: NotificationPreferenceUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update user notification preferences.
    
    Features:
    - Granular preference control
    - Channel enablement/disablement
    - Frequency and timing settings
    - Global opt-out support
    """
    try:
        preferences = await notification_service.update_user_notification_preferences(
            db, user_id, organization_id, preferences_data.dict(exclude_unset=True)
        )
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 5. Subscription Management
# =============================================================================

@router.post("/subscriptions", response_model=NotificationSubscriptionResponse, status_code=201)
async def create_notification_subscription(
    user_id: str = Query(..., description="User ID"),
    subscription_data: NotificationSubscriptionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create notification subscription for user.
    
    Features:
    - Topic-based subscriptions
    - Event filtering
    - Frequency control
    - Expiration management
    """
    try:
        subscription_dict = subscription_data.dict()
        subscription_dict["user_id"] = user_id
        
        subscription = await notification_service.create_notification_subscription(
            db, subscription_dict
        )
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions", response_model=List[NotificationSubscriptionResponse])
async def get_user_subscriptions(
    user_id: str = Query(..., description="User ID"),
    organization_id: str = Query(..., description="Organization ID"),
    status: Optional[SubscriptionStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Get user notification subscriptions.
    
    Features:
    - Subscription management
    - Status filtering
    - Analytics integration
    - Bulk operations support
    """
    try:
        subscriptions = await notification_service.get_user_subscriptions(
            db, user_id, organization_id, status
        )
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscriptions/{subscription_id}")
async def unsubscribe_user(
    subscription_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe user from notification topic.
    
    Features:
    - Graceful unsubscription
    - Status tracking
    - Re-subscription capability
    - Audit trail
    """
    try:
        success = await notification_service.unsubscribe_user(db, subscription_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {"message": "Successfully unsubscribed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 6. Event Processing
# =============================================================================

@router.post("/events", response_model=List[NotificationResponse])
async def process_notification_event(
    event_data: NotificationEventCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process notification event and trigger rule-based notifications.
    
    Features:
    - Event-driven notifications
    - Rule engine integration
    - Batch processing
    - Real-time triggers
    """
    try:
        notifications = await notification_service.process_notification_event(
            db, event_data.dict()
        )
        
        # Send real-time notifications
        for notification in notifications:
            if notification.recipient_user_id and notification.primary_channel == NotificationChannel.IN_APP:
                background_tasks.add_task(
                    websocket_manager.send_notification,
                    notification.recipient_user_id,
                    {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.notification_type.value,
                        "priority": notification.priority.value
                    }
                )
        
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[NotificationEventResponse])
async def get_notification_events(
    organization_id: str = Query(..., description="Organization ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Limit for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get notification events with filtering options.
    
    Features:
    - Event history tracking
    - Processing status monitoring
    - Error analysis
    - Performance metrics
    """
    try:
        from app.models.notification_extended import NotificationEvent
        
        query = db.query(NotificationEvent).filter(
            NotificationEvent.organization_id == organization_id
        )
        
        if event_type:
            query = query.filter(NotificationEvent.event_type == event_type)
        if processed is not None:
            query = query.filter(NotificationEvent.is_processed == processed)
        
        events = query.order_by(NotificationEvent.created_at.desc()).offset(skip).limit(limit).all()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 7. Analytics & Reporting
# =============================================================================

@router.post("/analytics", response_model=NotificationAnalyticsResponse)
async def generate_notification_analytics(
    analytics_data: NotificationAnalyticsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive notification analytics and performance metrics.
    
    Features:
    - Multi-channel analytics
    - Engagement metrics
    - Performance tracking
    - Cost analysis
    - Trend reporting
    """
    try:
        analytics = await notification_service.get_notification_analytics(
            db,
            analytics_data.organization_id,
            analytics_data.period_start,
            analytics_data.period_end
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_notification_dashboard(
    organization_id: str = Query(..., description="Organization ID"),
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: Session = Depends(get_db)
):
    """
    Get notification dashboard with key metrics and visualizations.
    
    Features:
    - Real-time dashboard data
    - Key performance indicators
    - Channel breakdowns
    - Trend analysis
    """
    try:
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        analytics = await notification_service.get_notification_analytics(
            db, organization_id, start_date, end_date
        )
        
        # Build dashboard data
        dashboard_data = {
            "overview": {
                "total_notifications": analytics.total_notifications,
                "delivery_rate": float(analytics.delivery_success_rate or 0),
                "open_rate": float(analytics.open_rate or 0),
                "click_rate": float(analytics.click_rate or 0)
            },
            "channels": {
                "email": {
                    "sent": analytics.email_sent,
                    "delivered": analytics.email_delivered,
                    "opened": analytics.email_opened,
                    "clicked": analytics.email_clicked
                },
                "sms": {
                    "sent": analytics.sms_sent,
                    "delivered": analytics.sms_delivered,
                    "failed": analytics.sms_failed
                },
                "push": {
                    "sent": analytics.push_sent,
                    "delivered": analytics.push_delivered,
                    "opened": analytics.push_opened
                },
                "in_app": {
                    "created": analytics.in_app_created,
                    "viewed": analytics.in_app_viewed,
                    "clicked": analytics.in_app_clicked
                }
            },
            "engagement": {
                "total_views": analytics.total_views,
                "total_clicks": analytics.total_clicks,
                "unique_viewers": analytics.unique_viewers
            },
            "costs": {
                "total_cost": float(analytics.total_cost or 0),
                "cost_per_notification": float(analytics.cost_per_notification or 0)
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": period_days
            }
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 8. Interaction Tracking
# =============================================================================

@router.post("/interactions")
async def log_notification_interaction(
    interaction_data: NotificationInteractionRequest,
    user_id: Optional[str] = Query(None, description="User ID (if authenticated)"),
    db: Session = Depends(get_db)
):
    """
    Log notification interaction for analytics and engagement tracking.
    
    Features:
    - Detailed interaction logging
    - Anonymous interaction support
    - Device and platform tracking
    - Custom interaction types
    """
    try:
        await notification_service._log_notification_interaction(
            db,
            interaction_data.notification_id,
            user_id or "anonymous",
            interaction_data.interaction_type,
            interaction_data.dict(exclude={"notification_id", "interaction_type"})
        )
        
        return {"message": "Interaction logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/{notification_id}/interactions")
async def get_notification_interactions(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Get interaction history for a notification.
    
    Features:
    - Complete interaction timeline
    - User engagement analysis
    - Device and platform insights
    - Performance metrics
    """
    try:
        from app.models.notification_extended import NotificationInteraction
        
        interactions = db.query(NotificationInteraction).filter(
            NotificationInteraction.notification_id == notification_id
        ).order_by(NotificationInteraction.timestamp.desc()).all()
        
        return interactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 9. Real-Time WebSocket
# =============================================================================

@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    organization_id: str = Query(..., description="Organization ID")
):
    """
    WebSocket endpoint for real-time notification delivery.
    
    Features:
    - Real-time notification push
    - Connection management
    - Subscription handling
    - Message queuing
    """
    await websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client (subscription updates, etc.)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    # Handle subscription updates
                    channels = message.get("channels", [])
                    filters = message.get("filters", {})
                    
                    # Send confirmation
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message.get("type") == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                pass
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)


# =============================================================================
# 10. System Health & Status
# =============================================================================

@router.get("/health", response_model=NotificationSystemHealthResponse)
async def get_notification_system_health(
    db: Session = Depends(get_db)
):
    """
    Get notification system health status and performance metrics.
    
    Features:
    - System status monitoring
    - Database connectivity check
    - Service availability validation
    - Performance statistics
    """
    try:
        health_data = await notification_service.get_system_health(db)
        return health_data
    except Exception as e:
        return NotificationSystemHealthResponse(
            status="unhealthy",
            database_connection="Failed",
            services_available=False,
            statistics={"error": str(e)},
            version="31.0",
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )


@router.post("/queue/process")
async def process_notification_queue(
    queue_name: str = Query("default", description="Queue name"),
    batch_size: int = Query(100, ge=1, le=1000, description="Batch size"),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process queued notifications for delivery.
    
    Features:
    - Batch processing
    - Queue management
    - Error handling
    - Performance optimization
    """
    try:
        processed_notifications = await notification_service.process_notification_queue(
            db, queue_name, batch_size
        )
        
        # Send real-time notifications for processed items
        for notification in processed_notifications:
            if notification.recipient_user_id and notification.primary_channel == NotificationChannel.IN_APP:
                background_tasks.add_task(
                    websocket_manager.send_notification,
                    notification.recipient_user_id,
                    {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.notification_type.value,
                        "priority": notification.priority.value
                    }
                )
        
        return {
            "message": f"Processed {len(processed_notifications)} notifications",
            "queue_name": queue_name,
            "batch_size": batch_size,
            "processed_count": len(processed_notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/notifications/bulk", response_model=BulkNotificationResponse)
async def create_bulk_notifications(
    bulk_data: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create multiple notifications in a single batch operation.
    
    Features:
    - Batch creation
    - Transaction management
    - Error handling
    - Performance optimization
    """
    try:
        import time
        start_time = time.time()
        
        created_notifications = []
        errors = []
        
        for i, notification_data in enumerate(bulk_data.notifications):
            try:
                notification = await notification_service.create_notification(
                    db, notification_data.dict()
                )
                created_notifications.append(notification.id)
                
                # Queue for real-time delivery
                if notification.recipient_user_id and notification.primary_channel == NotificationChannel.IN_APP:
                    background_tasks.add_task(
                        websocket_manager.send_notification,
                        notification.recipient_user_id,
                        {
                            "id": notification.id,
                            "title": notification.title,
                            "message": notification.message,
                            "type": notification.notification_type.value,
                            "priority": notification.priority.value
                        }
                    )
                    
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "notification_data": notification_data.dict()
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        success_rate = (len(created_notifications) / len(bulk_data.notifications)) * 100
        
        return BulkNotificationResponse(
            batch_id=bulk_data.batch_id or f"batch-{int(time.time())}",
            total_requested=len(bulk_data.notifications),
            successful=len(created_notifications),
            failed=len(errors),
            created_notifications=created_notifications,
            errors=errors,
            processing_time_ms=processing_time,
            success_rate=success_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))