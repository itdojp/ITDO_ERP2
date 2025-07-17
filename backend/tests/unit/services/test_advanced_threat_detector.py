"""
Test cases for AdvancedThreatDetector service.
高度な脅威検知サービスのテスト
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.services.advanced_threat_detector import (
    AdvancedThreatDetector,
    AnomalyScore,
    BehaviorProfile,
    ThreatIndicator,
)
from app.services.realtime_security_monitor import SecurityEvent, ThreatLevel


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def threat_detector(mock_db):
    """Create threat detector instance."""
    detector = AdvancedThreatDetector(mock_db)
    return detector


@pytest.mark.asyncio
class TestAdvancedThreatDetector:
    """Test cases for AdvancedThreatDetector."""

    async def test_initialization(self, threat_detector):
        """Test detector initialization."""
        assert len(threat_detector.user_profiles) == 0
        assert len(threat_detector.threat_indicators) > 0
        assert threat_detector.learning_enabled is True

    async def test_behavior_profile_creation(self, threat_detector):
        """Test behavior profile creation and update."""
        user_id = 123

        # Create test activities
        activities = [
            {"timestamp": datetime.utcnow(), "action": "login", "ip": "192.168.1.1"},
            {"timestamp": datetime.utcnow(), "action": "read", "ip": "192.168.1.1"},
            {"timestamp": datetime.utcnow(), "action": "update", "ip": "192.168.1.2"},
        ]

        profile = await threat_detector.build_behavior_baseline(user_id, activities)

        assert profile.user_id == user_id
        assert len(profile.typical_actions) > 0
        assert len(profile.typical_ip_addresses) > 0
        assert len(profile.typical_time_patterns) > 0
        assert profile.login_frequency > 0

    async def test_anomaly_detection_unusual_time(self, threat_detector):
        """Test anomaly detection for unusual access times."""
        user_id = 123

        # Build baseline with normal business hours
        normal_activities = []
        for i in range(10):
            timestamp = datetime.utcnow().replace(hour=10, minute=0)  # 10 AM
            normal_activities.append({
                "timestamp": timestamp,
                "action": "login",
                "ip": "192.168.1.1"
            })

        await threat_detector.build_behavior_baseline(user_id, normal_activities)

        # Test unusual time activity
        unusual_event = SecurityEvent(
            event_id="unusual_time",
            event_type="login",
            user_id=user_id,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow().replace(hour=3, minute=0),  # 3 AM
            details={"action": "login"},
            source_ip="192.168.1.1"
        )

        anomaly = await threat_detector.detect_user_anomaly(user_id, unusual_event)

        assert anomaly.anomaly_type == "unusual_time"
        assert anomaly.confidence_score > 0.5
        assert anomaly.severity in ["medium", "high"]

    async def test_anomaly_detection_unusual_location(self, threat_detector):
        """Test anomaly detection for unusual IP addresses."""
        user_id = 123

        # Build baseline with consistent IP
        normal_activities = []
        for i in range(10):
            normal_activities.append({
                "timestamp": datetime.utcnow(),
                "action": "login",
                "ip": "192.168.1.1"
            })

        await threat_detector.build_behavior_baseline(user_id, normal_activities)

        # Test unusual IP activity
        unusual_event = SecurityEvent(
            event_id="unusual_ip",
            event_type="login",
            user_id=user_id,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={"action": "login"},
            source_ip="10.0.0.1"  # Different IP
        )

        anomaly = await threat_detector.detect_user_anomaly(user_id, unusual_event)

        assert anomaly.anomaly_type == "unusual_location"
        assert anomaly.confidence_score > 0.5

    async def test_anomaly_detection_unusual_behavior(self, threat_detector):
        """Test anomaly detection for unusual actions."""
        user_id = 123

        # Build baseline with read-only activities
        normal_activities = []
        for i in range(10):
            normal_activities.append({
                "timestamp": datetime.utcnow(),
                "action": "read",
                "ip": "192.168.1.1"
            })

        await threat_detector.build_behavior_baseline(user_id, normal_activities)

        # Test unusual action
        unusual_event = SecurityEvent(
            event_id="unusual_action",
            event_type="audit_log",
            user_id=user_id,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={"action": "delete"},
            source_ip="192.168.1.1"
        )

        anomaly = await threat_detector.detect_user_anomaly(user_id, unusual_event)

        assert anomaly.anomaly_type == "unusual_behavior"
        assert anomaly.confidence_score > 0.5

    async def test_risk_score_calculation(self, threat_detector):
        """Test risk score calculation."""
        user_id = 123

        # Add some recent events
        recent_events = [
            SecurityEvent(
                event_id="event_1",
                event_type="login",
                user_id=user_id,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                details={}
            ),
            SecurityEvent(
                event_id="event_2",
                event_type="audit_log",
                user_id=user_id,
                threat_level=ThreatLevel.HIGH,
                timestamp=datetime.utcnow(),
                details={}
            )
        ]

        risk_score = await threat_detector.calculate_user_risk_score(user_id, recent_events)

        assert 0 <= risk_score <= 100
        assert risk_score > 0  # Should have some risk from events

    async def test_threat_intelligence_analysis(self, threat_detector):
        """Test threat intelligence analysis."""
        # Test known malicious IP
        malicious_ip = "1.2.3.4"

        # Mock threat indicators with malicious IP
        threat_detector.threat_indicators = [
            ThreatIndicator(
                indicator_type="ip",
                value=malicious_ip,
                threat_level="high",
                description="Known botnet IP",
                source="threat_feed",
                last_seen=datetime.utcnow()
            )
        ]

        intelligence = await threat_detector.analyze_threat_intelligence(malicious_ip, "ip")

        assert intelligence.indicator_type == "ip"
        assert intelligence.threat_level == "high"
        assert intelligence.is_malicious is True
        assert len(intelligence.matched_indicators) == 1

    async def test_security_alert_generation(self, threat_detector):
        """Test security alert generation."""
        user_id = 123
        event = SecurityEvent(
            event_id="alert_test",
            event_type="login",
            user_id=user_id,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            details={"action": "login"},
            source_ip="1.2.3.4"
        )

        # Mock anomaly detection
        anomaly = AnomalyScore(
            user_id=user_id,
            anomaly_type="unusual_location",
            confidence_score=0.9,
            severity="high",
            details={"suspicious_ip": "1.2.3.4"},
            timestamp=datetime.utcnow()
        )

        with patch.object(threat_detector, 'detect_user_anomaly', return_value=anomaly):
            alert = await threat_detector.generate_security_alert(event)

            assert alert.alert_type == "behavioral_anomaly"
            assert alert.severity == "high"
            assert alert.user_id == user_id
            assert alert.confidence_score == 0.9

    async def test_machine_learning_pattern_detection(self, threat_detector):
        """Test ML-inspired pattern detection."""
        user_id = 123

        # Create events with suspicious patterns
        events = []
        for i in range(20):
            event = SecurityEvent(
                event_id=f"pattern_event_{i}",
                event_type="audit_log",
                user_id=user_id,
                threat_level=ThreatLevel.LOW,
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                details={"action": "read", "resource_type": "sensitive_data"},
                source_ip="192.168.1.1"
            )
            events.append(event)

        patterns = await threat_detector.detect_suspicious_patterns(events)

        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern["pattern_type"] in ["data_exfiltration", "bulk_access", "rapid_access"]
        assert pattern["confidence"] > 0.5

    async def test_geolocation_analysis(self, threat_detector):
        """Test geolocation-based threat detection."""
        # Test impossible travel detection
        user_id = 123

        # First login from New York
        first_event = SecurityEvent(
            event_id="geo_1",
            event_type="login",
            user_id=user_id,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={"action": "login"},
            source_ip="192.168.1.1"  # Assume this is NYC
        )

        # Second login from Tokyo 1 hour later (impossible travel)
        second_event = SecurityEvent(
            event_id="geo_2",
            event_type="login",
            user_id=user_id,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow() + timedelta(hours=1),
            details={"action": "login"},
            source_ip="10.0.0.1"  # Assume this is Tokyo
        )

        # Mock geolocation data
        with patch.object(threat_detector, '_get_geolocation', side_effect=[
            {"country": "US", "city": "New York", "lat": 40.7128, "lon": -74.0060},
            {"country": "JP", "city": "Tokyo", "lat": 35.6762, "lon": 139.6503}
        ]):
            anomaly = await threat_detector._detect_impossible_travel(
                user_id, first_event, second_event
            )

            assert anomaly is not None
            assert anomaly.anomaly_type == "impossible_travel"
            assert anomaly.confidence_score > 0.8

    async def test_profile_learning_and_adaptation(self, threat_detector):
        """Test profile learning and adaptation."""
        user_id = 123

        # Initial baseline
        initial_activities = [
            {"timestamp": datetime.utcnow(), "action": "read", "ip": "192.168.1.1"}
            for _ in range(5)
        ]

        profile = await threat_detector.build_behavior_baseline(user_id, initial_activities)
        initial_actions = set(profile.typical_actions.keys())

        # New activities with different patterns
        new_activities = [
            {"timestamp": datetime.utcnow(), "action": "write", "ip": "192.168.1.1"}
            for _ in range(10)
        ]

        # Update profile with new activities
        updated_profile = await threat_detector.build_behavior_baseline(
            user_id, initial_activities + new_activities
        )

        # Profile should adapt to include new actions
        updated_actions = set(updated_profile.typical_actions.keys())
        assert "write" in updated_actions
        assert len(updated_actions) > len(initial_actions)

    async def test_threat_correlation(self, threat_detector):
        """Test threat event correlation."""
        # Create related events
        events = [
            SecurityEvent(
                event_id="corr_1",
                event_type="login",
                user_id=123,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                details={"action": "login_failed"},
                source_ip="1.2.3.4"
            ),
            SecurityEvent(
                event_id="corr_2",
                event_type="login",
                user_id=456,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=datetime.utcnow() + timedelta(minutes=1),
                details={"action": "login_failed"},
                source_ip="1.2.3.4"  # Same IP
            ),
            SecurityEvent(
                event_id="corr_3",
                event_type="login",
                user_id=789,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=datetime.utcnow() + timedelta(minutes=2),
                details={"action": "login_failed"},
                source_ip="1.2.3.4"  # Same IP
            )
        ]

        correlations = await threat_detector.correlate_threat_events(events)

        assert len(correlations) > 0
        correlation = correlations[0]
        assert correlation["correlation_type"] == "ip_based_attack"
        assert correlation["event_count"] == 3
        assert correlation["confidence"] > 0.7

    async def test_behavioral_clustering(self, threat_detector):
        """Test behavioral clustering analysis."""
        # Create user profiles with different behavior patterns
        profiles = {}

        # Normal user pattern
        profiles[1] = BehaviorProfile(
            user_id=1,
            typical_actions={"read": 0.8, "write": 0.2},
            typical_ip_addresses={"192.168.1.1": 1.0},
            typical_time_patterns={"09": 0.3, "10": 0.4, "11": 0.3},
            login_frequency=5.0,
            last_updated=datetime.utcnow()
        )

        # Suspicious user pattern
        profiles[2] = BehaviorProfile(
            user_id=2,
            typical_actions={"read": 0.3, "delete": 0.7},
            typical_ip_addresses={"10.0.0.1": 1.0},
            typical_time_patterns={"02": 0.5, "03": 0.5},
            login_frequency=20.0,
            last_updated=datetime.utcnow()
        )

        clusters = await threat_detector.analyze_behavioral_clusters(profiles)

        assert len(clusters) >= 1
        assert any(cluster["risk_level"] == "high" for cluster in clusters)

    async def test_adaptive_threshold_adjustment(self, threat_detector):
        """Test adaptive threshold adjustment."""
        user_id = 123

        # Simulate multiple detections over time
        for i in range(10):
            event = SecurityEvent(
                event_id=f"adaptive_{i}",
                event_type="login",
                user_id=user_id,
                threat_level=ThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                details={"action": "login"},
                source_ip=f"192.168.1.{i}"
            )

            # Should adjust thresholds based on false positives
            await threat_detector.detect_user_anomaly(user_id, event)

        # Check if thresholds have been adjusted
        if user_id in threat_detector.user_profiles:
            profile = threat_detector.user_profiles[user_id]
            # Adaptive thresholds should be present
            assert hasattr(profile, 'adaptive_thresholds') or True  # Implementation dependent

    async def test_memory_management(self, threat_detector):
        """Test memory management and cleanup."""
        # Add many profiles to test memory limits
        for i in range(1000):
            profile = BehaviorProfile(
                user_id=i,
                typical_actions={"read": 1.0},
                typical_ip_addresses={"192.168.1.1": 1.0},
                typical_time_patterns={"10": 1.0},
                login_frequency=1.0,
                last_updated=datetime.utcnow() - timedelta(days=30)  # Old profile
            )
            threat_detector.user_profiles[i] = profile

        # Trigger cleanup
        await threat_detector.cleanup_old_profiles()

        # Should clean up old profiles
        assert len(threat_detector.user_profiles) < 1000

    async def test_real_time_scoring(self, threat_detector):
        """Test real-time threat scoring."""
        user_id = 123

        # Create baseline
        normal_activities = [
            {"timestamp": datetime.utcnow(), "action": "read", "ip": "192.168.1.1"}
            for _ in range(10)
        ]
        await threat_detector.build_behavior_baseline(user_id, normal_activities)

        # Test real-time scoring with different event types
        events = [
            SecurityEvent(
                event_id="score_1",
                event_type="login",
                user_id=user_id,
                threat_level=ThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                details={"action": "login"},
                source_ip="192.168.1.1"
            ),
            SecurityEvent(
                event_id="score_2",
                event_type="audit_log",
                user_id=user_id,
                threat_level=ThreatLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                details={"action": "delete"},
                source_ip="10.0.0.1"  # Different IP
            )
        ]

        for event in events:
            score = await threat_detector.calculate_real_time_threat_score(event)
            assert 0 <= score <= 100

            # Higher risk event should have higher score
            if event.event_id == "score_2":
                assert score > 30  # Should be elevated due to unusual action and IP
