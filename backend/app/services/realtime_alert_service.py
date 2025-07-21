"""Real-time alert and notification service for security monitoring."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.models.security_event import SecurityAlert, SecurityEvent, ThreatLevel
from app.models.user import User


class AlertSubscriber:
    """Represents an alert subscriber with delivery preferences."""

    def __init__(
        self,
        user_id: int,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        webhook_url: Optional[str] = None,
        severity_threshold: ThreatLevel = ThreatLevel.MEDIUM,
        alert_types: Optional[List[str]] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.phone = phone
        self.webhook_url = webhook_url
        self.severity_threshold = severity_threshold
        self.alert_types = alert_types or []
        self.is_active = True

    def should_receive_alert(self, alert: SecurityAlert) -> bool:
        """Check if subscriber should receive this alert."""
        if not self.is_active:
            return False
        
        # Check severity threshold
        severity_order = {
            ThreatLevel.LOW: 0,
            ThreatLevel.MEDIUM: 1,
            ThreatLevel.HIGH: 2,
            ThreatLevel.CRITICAL: 3,
        }
        
        alert_severity = severity_order.get(alert.severity, 0)
        threshold_severity = severity_order.get(self.severity_threshold, 1)
        
        if alert_severity < threshold_severity:
            return False
        
        # Check alert types if specified
        if self.alert_types and alert.alert_type not in self.alert_types:
            return False
        
        return True


class RealtimeAlertService:
    """Real-time alert and notification service."""

    def __init__(self):
        """Initialize the real-time alert service."""
        self.subscribers: Dict[int, AlertSubscriber] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.notification_handlers: Dict[str, callable] = {}
        self.is_running = False
        self.alert_history: List[SecurityAlert] = []
        self.max_history_size = 1000

    # ===== SUBSCRIBER MANAGEMENT =====

    def add_subscriber(
        self,
        user_id: int,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        webhook_url: Optional[str] = None,
        severity_threshold: ThreatLevel = ThreatLevel.MEDIUM,
        alert_types: Optional[List[str]] = None,
    ) -> str:
        """Add a new alert subscriber."""
        subscriber = AlertSubscriber(
            user_id=user_id,
            email=email,
            phone=phone,
            webhook_url=webhook_url,
            severity_threshold=severity_threshold,
            alert_types=alert_types,
        )
        
        self.subscribers[user_id] = subscriber
        return f"Subscriber {user_id} added successfully"

    def remove_subscriber(self, user_id: int) -> str:
        """Remove an alert subscriber."""
        if user_id in self.subscribers:
            del self.subscribers[user_id]
            return f"Subscriber {user_id} removed successfully"
        return f"Subscriber {user_id} not found"

    def update_subscriber_preferences(
        self,
        user_id: int,
        severity_threshold: Optional[ThreatLevel] = None,
        alert_types: Optional[List[str]] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> str:
        """Update subscriber preferences."""
        if user_id not in self.subscribers:
            return f"Subscriber {user_id} not found"
        
        subscriber = self.subscribers[user_id]
        
        if severity_threshold is not None:
            subscriber.severity_threshold = severity_threshold
        if alert_types is not None:
            subscriber.alert_types = alert_types
        if email is not None:
            subscriber.email = email
        if phone is not None:
            subscriber.phone = phone
        if webhook_url is not None:
            subscriber.webhook_url = webhook_url
        
        return f"Subscriber {user_id} preferences updated"

    def get_subscriber_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get subscriber preferences."""
        if user_id not in self.subscribers:
            return None
        
        subscriber = self.subscribers[user_id]
        return {
            "user_id": subscriber.user_id,
            "email": subscriber.email,
            "phone": subscriber.phone,
            "webhook_url": subscriber.webhook_url,
            "severity_threshold": subscriber.severity_threshold.value,
            "alert_types": subscriber.alert_types,
            "is_active": subscriber.is_active,
        }

    # ===== WEBSOCKET MANAGEMENT =====

    async def add_websocket_connection(self, websocket, user_id: int) -> str:
        """Add a WebSocket connection for real-time alerts."""
        connection_id = str(uuid.uuid4())
        self.websocket_connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
        }
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
        }))
        
        return connection_id

    async def remove_websocket_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        if connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]

    async def broadcast_to_websockets(self, alert: SecurityAlert) -> None:
        """Broadcast alert to all relevant WebSocket connections."""
        message = {
            "type": "security_alert",
            "alert": {
                "id": alert.id,
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value if alert.severity else None,
                "title": alert.title,
                "message": alert.message,
                "user_id": alert.user_id,
                "organization_id": alert.organization_id,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Send to relevant connections
        connections_to_remove = []
        for connection_id, connection in self.websocket_connections.items():
            try:
                user_id = connection["user_id"]
                
                # Check if user should receive this alert
                if user_id in self.subscribers:
                    subscriber = self.subscribers[user_id]
                    if subscriber.should_receive_alert(alert):
                        await connection["websocket"].send_text(json.dumps(message))
                else:
                    # Send to all if no specific subscription
                    await connection["websocket"].send_text(json.dumps(message))
                    
            except Exception as e:
                # Connection is broken, mark for removal
                connections_to_remove.append(connection_id)
                print(f"WebSocket error for connection {connection_id}: {e}")
        
        # Clean up broken connections
        for connection_id in connections_to_remove:
            await self.remove_websocket_connection(connection_id)

    # ===== ALERT PROCESSING =====

    async def queue_alert(self, alert: SecurityAlert) -> None:
        """Queue an alert for processing."""
        await self.alert_queue.put(alert)

    async def process_alerts(self) -> None:
        """Process alerts from the queue."""
        while self.is_running:
            try:
                # Wait for alert with timeout
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                await self._process_single_alert(alert)
                self.alert_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing alert: {e}")

    async def _process_single_alert(self, alert: SecurityAlert) -> None:
        """Process a single alert."""
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history_size:
            self.alert_history.pop(0)
        
        # Broadcast to WebSocket connections
        await self.broadcast_to_websockets(alert)
        
        # Send notifications through various channels
        await self._send_notifications(alert)

    async def _send_notifications(self, alert: SecurityAlert) -> None:
        """Send notifications through configured channels."""
        # Email notifications
        if "email" in alert.delivery_methods:
            await self._send_email_notifications(alert)
        
        # SMS notifications
        if "sms" in alert.delivery_methods:
            await self._send_sms_notifications(alert)
        
        # Webhook notifications
        if "webhook" in alert.delivery_methods:
            await self._send_webhook_notifications(alert)
        
        # In-app notifications (WebSocket handled separately)
        if "in_app" in alert.delivery_methods:
            # Already handled by WebSocket broadcast
            pass

    async def _send_email_notifications(self, alert: SecurityAlert) -> None:
        """Send email notifications to relevant subscribers."""
        recipients = []
        
        # Get recipients from alert
        if alert.recipients:
            for user_id in alert.recipients:
                if user_id in self.subscribers:
                    subscriber = self.subscribers[user_id]
                    if subscriber.should_receive_alert(alert) and subscriber.email:
                        recipients.append(subscriber.email)
        else:
            # Send to all email subscribers who should receive this alert
            for subscriber in self.subscribers.values():
                if subscriber.should_receive_alert(alert) and subscriber.email:
                    recipients.append(subscriber.email)
        
        if recipients and "email" in self.notification_handlers:
            await self.notification_handlers["email"](alert, recipients)

    async def _send_sms_notifications(self, alert: SecurityAlert) -> None:
        """Send SMS notifications to relevant subscribers."""
        recipients = []
        
        # Only send SMS for high and critical severity
        if alert.severity not in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            return
        
        # Get phone numbers from subscribers
        if alert.recipients:
            for user_id in alert.recipients:
                if user_id in self.subscribers:
                    subscriber = self.subscribers[user_id]
                    if subscriber.should_receive_alert(alert) and subscriber.phone:
                        recipients.append(subscriber.phone)
        else:
            # Send to all SMS subscribers who should receive this alert
            for subscriber in self.subscribers.values():
                if subscriber.should_receive_alert(alert) and subscriber.phone:
                    recipients.append(subscriber.phone)
        
        if recipients and "sms" in self.notification_handlers:
            await self.notification_handlers["sms"](alert, recipients)

    async def _send_webhook_notifications(self, alert: SecurityAlert) -> None:
        """Send webhook notifications to relevant subscribers."""
        webhooks = []
        
        # Get webhook URLs from subscribers
        if alert.recipients:
            for user_id in alert.recipients:
                if user_id in self.subscribers:
                    subscriber = self.subscribers[user_id]
                    if subscriber.should_receive_alert(alert) and subscriber.webhook_url:
                        webhooks.append(subscriber.webhook_url)
        else:
            # Send to all webhook subscribers who should receive this alert
            for subscriber in self.subscribers.values():
                if subscriber.should_receive_alert(alert) and subscriber.webhook_url:
                    webhooks.append(subscriber.webhook_url)
        
        if webhooks and "webhook" in self.notification_handlers:
            await self.notification_handlers["webhook"](alert, webhooks)

    # ===== NOTIFICATION HANDLERS =====

    def register_notification_handler(self, channel: str, handler: callable) -> None:
        """Register a notification handler for a specific channel."""
        self.notification_handlers[channel] = handler

    async def default_email_handler(self, alert: SecurityAlert, recipients: List[str]) -> None:
        """Default email notification handler."""
        print(f"EMAIL ALERT: Sending to {len(recipients)} recipients")
        print(f"Subject: {alert.title}")
        print(f"Message: {alert.message}")
        print(f"Severity: {alert.severity.value}")
        
        # In a real implementation, you would use an email service here
        # For example: await email_service.send_alert_email(alert, recipients)

    async def default_sms_handler(self, alert: SecurityAlert, recipients: List[str]) -> None:
        """Default SMS notification handler."""
        print(f"SMS ALERT: Sending to {len(recipients)} recipients")
        print(f"Message: {alert.title} - {alert.severity.value.upper()}")
        
        # In a real implementation, you would use an SMS service here
        # For example: await sms_service.send_alert_sms(alert, recipients)

    async def default_webhook_handler(self, alert: SecurityAlert, webhooks: List[str]) -> None:
        """Default webhook notification handler."""
        import aiohttp
        
        payload = {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity.value if alert.severity else None,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.created_at.isoformat() if alert.created_at else None,
        }
        
        async with aiohttp.ClientSession() as session:
            for webhook_url in webhooks:
                try:
                    async with session.post(
                        webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status != 200:
                            print(f"Webhook failed for {webhook_url}: {response.status}")
                except Exception as e:
                    print(f"Webhook error for {webhook_url}: {e}")

    # ===== SERVICE CONTROL =====

    async def start_service(self) -> None:
        """Start the real-time alert service."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Register default handlers
        self.register_notification_handler("email", self.default_email_handler)
        self.register_notification_handler("sms", self.default_sms_handler)
        self.register_notification_handler("webhook", self.default_webhook_handler)
        
        # Start alert processing task
        asyncio.create_task(self.process_alerts())
        
        print("Real-time alert service started")

    async def stop_service(self) -> None:
        """Stop the real-time alert service."""
        self.is_running = False
        
        # Wait for remaining alerts to be processed
        await self.alert_queue.join()
        
        # Close all WebSocket connections
        for connection_id in list(self.websocket_connections.keys()):
            await self.remove_websocket_connection(connection_id)
        
        print("Real-time alert service stopped")

    # ===== STATISTICS AND MONITORING =====

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "is_running": self.is_running,
            "total_subscribers": len(self.subscribers),
            "active_websocket_connections": len(self.websocket_connections),
            "queued_alerts": self.alert_queue.qsize(),
            "alert_history_size": len(self.alert_history),
            "notification_handlers": list(self.notification_handlers.keys()),
            "uptime": "running" if self.is_running else "stopped",
        }

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts from history."""
        recent_alerts = self.alert_history[-limit:] if self.alert_history else []
        return [
            {
                "id": alert.id,
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value if alert.severity else None,
                "title": alert.title,
                "message": alert.message,
                "acknowledged": alert.acknowledged,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert in recent_alerts
        ]

    def get_subscriber_list(self) -> List[Dict[str, Any]]:
        """Get list of all subscribers."""
        return [
            {
                "user_id": subscriber.user_id,
                "severity_threshold": subscriber.severity_threshold.value,
                "alert_types": subscriber.alert_types,
                "has_email": bool(subscriber.email),
                "has_phone": bool(subscriber.phone),
                "has_webhook": bool(subscriber.webhook_url),
                "is_active": subscriber.is_active,
            }
            for subscriber in self.subscribers.values()
        ]

    # ===== ALERT TESTING =====

    async def send_test_alert(
        self,
        user_id: int,
        severity: ThreatLevel = ThreatLevel.LOW,
        alert_type: str = "test_alert",
    ) -> str:
        """Send a test alert to verify notification systems."""
        test_alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title="Test Security Alert",
            message="This is a test alert to verify the notification system is working correctly.",
            user_id=user_id,
            recipients=[user_id],
            delivery_methods=["email", "in_app", "webhook"],
        )
        test_alert.created_at = datetime.utcnow()
        
        await self.queue_alert(test_alert)
        return f"Test alert queued for user {user_id}"


# Global instance
realtime_alert_service = RealtimeAlertService()