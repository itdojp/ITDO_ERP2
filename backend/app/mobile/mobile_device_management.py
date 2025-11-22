"""Mobile Device Management & Security System - CC02 v73.0 Day 18."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from .enterprise_auth_system import EnterpriseAuthenticationSystem


class DeviceStatus(str, Enum):
    """Device status in MDM system."""

    ENROLLED = "enrolled"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    COMPROMISED = "compromised"
    WIPED = "wiped"
    RETIRED = "retired"


class ComplianceStatus(str, Enum):
    """Device compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"


class SecurityThreat(str, Enum):
    """Security threat types."""

    MALWARE = "malware"
    JAILBREAK = "jailbreak"
    ROOT = "root"
    DEBUG_MODE = "debug_mode"
    SUSPICIOUS_APP = "suspicious_app"
    NETWORK_THREAT = "network_threat"
    DATA_LEAKAGE = "data_leakage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class MDMCommand(str, Enum):
    """MDM command types."""

    LOCK_DEVICE = "lock_device"
    UNLOCK_DEVICE = "unlock_device"
    WIPE_DEVICE = "wipe_device"
    LOCATE_DEVICE = "locate_device"
    INSTALL_APP = "install_app"
    UNINSTALL_APP = "uninstall_app"
    UPDATE_POLICY = "update_policy"
    SYNC_DATA = "sync_data"
    BACKUP_DATA = "backup_data"
    RESET_PASSCODE = "reset_passcode"


class DeviceProfile(BaseModel):
    """Mobile device profile in MDM system."""

    device_id: str
    user_id: str

    # Device information
    device_name: str
    device_type: str  # phone, tablet, laptop
    platform: str  # ios, android, windows
    platform_version: str
    model: str
    manufacturer: str
    serial_number: Optional[str] = None

    # Hardware information
    imei: Optional[str] = None
    mac_address: Optional[str] = None
    cpu_architecture: Optional[str] = None
    total_storage: Optional[int] = None  # in GB
    available_storage: Optional[int] = None  # in GB
    ram_size: Optional[int] = None  # in GB
    battery_level: Optional[int] = None  # percentage

    # Network information
    carrier: Optional[str] = None
    phone_number: Optional[str] = None
    wifi_mac: Optional[str] = None
    bluetooth_mac: Optional[str] = None
    ip_address: Optional[str] = None

    # Security status
    status: DeviceStatus = DeviceStatus.ENROLLED
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    jailbroken: bool = False
    rooted: bool = False
    debug_enabled: bool = False
    screen_lock_enabled: bool = False
    encryption_enabled: bool = False

    # Location information
    last_location: Optional[Dict[str, Any]] = None
    location_enabled: bool = False

    # App information
    installed_apps: List[Dict[str, Any]] = Field(default_factory=list)
    managed_apps: List[str] = Field(default_factory=list)

    # Certificate information
    certificates: List[Dict[str, Any]] = Field(default_factory=list)

    # Management information
    enrollment_date: datetime = Field(default_factory=datetime.now)
    last_checkin: Optional[datetime] = None
    last_backup: Optional[datetime] = None
    managed_by: str

    # Security policies
    applied_policies: Set[str] = Field(default_factory=set)
    policy_violations: List[Dict[str, Any]] = Field(default_factory=list)

    # Threat information
    security_threats: List[Dict[str, Any]] = Field(default_factory=list)
    threat_score: float = 0.0


class SecurityPolicy(BaseModel):
    """Mobile device security policy."""

    policy_id: str
    name: str
    description: str
    version: str = "1.0"

    # Password/PIN requirements
    require_passcode: bool = True
    min_passcode_length: int = 6
    require_complex_passcode: bool = True
    max_failed_attempts: int = 5
    passcode_expiry_days: Optional[int] = None

    # Device restrictions
    allow_camera: bool = True
    allow_screenshot: bool = True
    allow_app_installation: bool = True
    allow_backup: bool = True
    allow_cloud_sync: bool = True
    allow_bluetooth: bool = True
    allow_wifi: bool = True
    allow_cellular_data: bool = True

    # App restrictions
    blacklisted_apps: Set[str] = Field(default_factory=set)
    whitelisted_apps: Set[str] = Field(default_factory=set)
    require_app_approval: bool = False

    # Security requirements
    require_encryption: bool = True
    require_screen_lock: bool = True
    max_inactivity_minutes: int = 15
    require_vpn: bool = False
    vpn_configuration: Optional[Dict[str, Any]] = None

    # Network restrictions
    allowed_wifi_networks: Set[str] = Field(default_factory=set)
    blocked_domains: Set[str] = Field(default_factory=set)
    require_certificate_authentication: bool = False

    # Compliance requirements
    max_os_age_days: int = 90
    require_antivirus: bool = True
    allow_jailbreak: bool = False
    allow_debugging: bool = False

    # Data protection
    require_remote_wipe: bool = True
    auto_wipe_on_compliance_violation: bool = False
    data_loss_prevention_enabled: bool = True

    # Monitoring
    location_tracking_enabled: bool = False
    app_usage_monitoring: bool = True
    network_monitoring: bool = True

    # Target devices
    target_platforms: Set[str] = Field(default_factory=set)
    target_device_types: Set[str] = Field(default_factory=set)
    target_user_groups: Set[str] = Field(default_factory=set)

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    active: bool = True


class MDMCommandRequest(BaseModel):
    """MDM command request."""

    command_id: str
    device_id: str
    command_type: MDMCommand
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Request information
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.now)
    reason: Optional[str] = None
    urgent: bool = False

    # Execution information
    status: str = "pending"  # pending, sent, executed, failed, expired
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Expiration
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(hours=24)
    )


class ThreatDetection(BaseModel):
    """Security threat detection."""

    threat_id: str
    device_id: str
    threat_type: SecurityThreat
    severity: str  # low, medium, high, critical

    # Threat details
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    indicators: List[str] = Field(default_factory=list)

    # Detection information
    detected_at: datetime = Field(default_factory=datetime.now)
    detection_method: str  # signature, behavior, heuristic, ml
    confidence_score: float = 0.0

    # Response information
    status: str = "new"  # new, investigating, confirmed, false_positive, resolved
    response_actions: List[str] = Field(default_factory=list)
    mitigation_steps: List[str] = Field(default_factory=list)

    # Investigation
    investigated_by: Optional[str] = None
    investigation_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class MobileApplication(BaseModel):
    """Mobile application information."""

    app_id: str
    name: str
    version: str
    bundle_identifier: str

    # App details
    developer: str
    category: str
    size_mb: int = 0
    install_date: Optional[datetime] = None
    last_used: Optional[datetime] = None

    # Management information
    managed: bool = False
    enterprise_app: bool = False
    sideloaded: bool = False

    # Security information
    permissions: List[str] = Field(default_factory=list)
    security_score: float = 0.0
    known_vulnerabilities: List[str] = Field(default_factory=list)

    # Usage statistics
    usage_time_minutes: int = 0
    launch_count: int = 0
    data_usage_mb: int = 0
    battery_usage_percent: float = 0.0


class DeviceComplianceChecker:
    """Device compliance checking engine."""

    def __init__(self) -> dict:
        self.compliance_rules: Dict[str, Any] = {}
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default compliance rules."""
        self.compliance_rules = {
            "passcode_required": {
                "check": "screen_lock_enabled",
                "severity": "high",
                "message": "Device must have screen lock enabled",
            },
            "encryption_required": {
                "check": "encryption_enabled",
                "severity": "high",
                "message": "Device storage must be encrypted",
            },
            "jailbreak_detection": {
                "check": "not jailbroken",
                "severity": "critical",
                "message": "Jailbroken devices are not allowed",
            },
            "root_detection": {
                "check": "not rooted",
                "severity": "critical",
                "message": "Rooted devices are not allowed",
            },
            "debug_detection": {
                "check": "not debug_enabled",
                "severity": "medium",
                "message": "Debug mode should be disabled",
            },
            "os_version": {
                "check": "platform_version_current",
                "severity": "medium",
                "message": "Operating system must be up to date",
            },
        }

    async def check_compliance(
        self, device: DeviceProfile, policy: SecurityPolicy
    ) -> Tuple[ComplianceStatus, List[Dict[str, Any]]]:
        """Check device compliance against policy."""
        violations = []
        critical_count = 0
        high_count = 0

        # Check passcode requirement
        if policy.require_passcode and not device.screen_lock_enabled:
            violations.append(
                {
                    "rule": "passcode_required",
                    "severity": "high",
                    "message": "Screen lock is required but not enabled",
                    "timestamp": datetime.now(),
                }
            )
            high_count += 1

        # Check encryption requirement
        if policy.require_encryption and not device.encryption_enabled:
            violations.append(
                {
                    "rule": "encryption_required",
                    "severity": "high",
                    "message": "Device encryption is required but not enabled",
                    "timestamp": datetime.now(),
                }
            )
            high_count += 1

        # Check jailbreak/root status
        if not policy.allow_jailbreak and device.jailbroken:
            violations.append(
                {
                    "rule": "jailbreak_detection",
                    "severity": "critical",
                    "message": "Jailbroken devices are not permitted",
                    "timestamp": datetime.now(),
                }
            )
            critical_count += 1

        if not policy.allow_jailbreak and device.rooted:
            violations.append(
                {
                    "rule": "root_detection",
                    "severity": "critical",
                    "message": "Rooted devices are not permitted",
                    "timestamp": datetime.now(),
                }
            )
            critical_count += 1

        # Check debug mode
        if not policy.allow_debugging and device.debug_enabled:
            violations.append(
                {
                    "rule": "debug_detection",
                    "severity": "medium",
                    "message": "Debug mode should be disabled",
                    "timestamp": datetime.now(),
                }
            )

        # Check OS version (simplified)
        if policy.max_os_age_days:
            # Mock OS age check
            os_age_days = 30  # Mock value
            if os_age_days > policy.max_os_age_days:
                violations.append(
                    {
                        "rule": "os_version",
                        "severity": "medium",
                        "message": f"OS version is {os_age_days} days old, maximum allowed is {policy.max_os_age_days}",
                        "timestamp": datetime.now(),
                    }
                )

        # Check installed apps against blacklist
        for app in device.installed_apps:
            app_id = app.get("bundle_identifier", "")
            if app_id in policy.blacklisted_apps:
                violations.append(
                    {
                        "rule": "blacklisted_app",
                        "severity": "high",
                        "message": f"Blacklisted app detected: {app.get('name', app_id)}",
                        "timestamp": datetime.now(),
                    }
                )
                high_count += 1

        # Determine overall compliance status
        if critical_count > 0:
            status = ComplianceStatus.NON_COMPLIANT
        elif high_count > 0:
            status = ComplianceStatus.WARNING
        elif len(violations) > 0:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.COMPLIANT

        return status, violations


class ThreatDetectionEngine:
    """Mobile device threat detection engine."""

    def __init__(self) -> dict:
        self.threat_signatures: Dict[str, Any] = {}
        self.ml_models: Dict[str, Any] = {}
        self._setup_threat_signatures()

    def _setup_threat_signatures(self) -> None:
        """Setup threat detection signatures."""
        self.threat_signatures = {
            "malware_apps": [
                "com.malicious.app",
                "org.suspicious.tool",
                "net.harmful.service",
            ],
            "jailbreak_indicators": [
                "/Applications/Cydia.app",
                "/usr/sbin/sshd",
                "/etc/ssh/sshd_config",
                "/var/mobile/Library/SBSettings",
            ],
            "root_indicators": [
                "/system/app/Superuser.apk",
                "/system/xbin/su",
                "/data/local/tmp",
                "/data/local/bin/su",
            ],
            "suspicious_networks": ["FreeWiFi", "PublicWiFi", "HackerNet"],
        }

    async def scan_device(self, device: DeviceProfile) -> List[ThreatDetection]:
        """Scan device for security threats."""
        threats = []

        # Check for malware apps
        malware_threats = await self._detect_malware(device)
        threats.extend(malware_threats)

        # Check for jailbreak/root
        jailbreak_threats = await self._detect_jailbreak_root(device)
        threats.extend(jailbreak_threats)

        # Check for suspicious network activity
        network_threats = await self._detect_network_threats(device)
        threats.extend(network_threats)

        # Check for data leakage
        data_threats = await self._detect_data_leakage(device)
        threats.extend(data_threats)

        # Update device threat score
        device.threat_score = self._calculate_threat_score(threats)

        return threats

    async def _detect_malware(self, device: DeviceProfile) -> List[ThreatDetection]:
        """Detect malware on device."""
        threats = []

        for app in device.installed_apps:
            app_id = app.get("bundle_identifier", "")
            if app_id in self.threat_signatures["malware_apps"]:
                threat = ThreatDetection(
                    threat_id=f"malware_{device.device_id}_{len(threats)}",
                    device_id=device.device_id,
                    threat_type=SecurityThreat.MALWARE,
                    severity="critical",
                    description=f"Malicious app detected: {app.get('name', app_id)}",
                    evidence={
                        "app_name": app.get("name"),
                        "bundle_id": app_id,
                        "install_date": app.get("install_date"),
                    },
                    detection_method="signature",
                    confidence_score=0.95,
                )
                threats.append(threat)

        return threats

    async def _detect_jailbreak_root(
        self, device: DeviceProfile
    ) -> List[ThreatDetection]:
        """Detect jailbreak/root status."""
        threats = []

        if device.jailbroken:
            threat = ThreatDetection(
                threat_id=f"jailbreak_{device.device_id}",
                device_id=device.device_id,
                threat_type=SecurityThreat.JAILBREAK,
                severity="critical",
                description="Device is jailbroken",
                evidence={"jailbreak_detected": True},
                indicators=self.threat_signatures["jailbreak_indicators"],
                detection_method="signature",
                confidence_score=0.98,
            )
            threats.append(threat)

        if device.rooted:
            threat = ThreatDetection(
                threat_id=f"root_{device.device_id}",
                device_id=device.device_id,
                threat_type=SecurityThreat.ROOT,
                severity="critical",
                description="Device is rooted",
                evidence={"root_detected": True},
                indicators=self.threat_signatures["root_indicators"],
                detection_method="signature",
                confidence_score=0.98,
            )
            threats.append(threat)

        return threats

    async def _detect_network_threats(
        self, device: DeviceProfile
    ) -> List[ThreatDetection]:
        """Detect network-based threats."""
        threats = []

        # Check for suspicious WiFi networks (mock)
        if device.last_location:
            connected_networks = device.last_location.get("wifi_networks", [])
            for network in connected_networks:
                if network in self.threat_signatures["suspicious_networks"]:
                    threat = ThreatDetection(
                        threat_id=f"network_{device.device_id}_{network}",
                        device_id=device.device_id,
                        threat_type=SecurityThreat.NETWORK_THREAT,
                        severity="medium",
                        description=f"Connected to suspicious network: {network}",
                        evidence={"network_name": network},
                        detection_method="signature",
                        confidence_score=0.75,
                    )
                    threats.append(threat)

        return threats

    async def _detect_data_leakage(
        self, device: DeviceProfile
    ) -> List[ThreatDetection]:
        """Detect potential data leakage."""
        threats = []

        # Check for apps with excessive permissions
        for app in device.installed_apps:
            dangerous_permissions = [
                "android.permission.READ_CONTACTS",
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.CAMERA",
                "android.permission.RECORD_AUDIO",
            ]

            app_permissions = app.get("permissions", [])
            excessive_permissions = [
                p for p in app_permissions if p in dangerous_permissions
            ]

            if len(excessive_permissions) >= 3:  # Threshold for suspicious
                threat = ThreatDetection(
                    threat_id=f"data_leak_{device.device_id}_{app.get('bundle_identifier')}",
                    device_id=device.device_id,
                    threat_type=SecurityThreat.DATA_LEAKAGE,
                    severity="medium",
                    description=f"App has excessive permissions: {app.get('name')}",
                    evidence={
                        "app_name": app.get("name"),
                        "excessive_permissions": excessive_permissions,
                    },
                    detection_method="heuristic",
                    confidence_score=0.65,
                )
                threats.append(threat)

        return threats

    def _calculate_threat_score(self, threats: List[ThreatDetection]) -> float:
        """Calculate overall threat score for device."""
        if not threats:
            return 0.0

        total_score = 0.0
        for threat in threats:
            severity_weight = {
                "low": 0.25,
                "medium": 0.5,
                "high": 0.75,
                "critical": 1.0,
            }.get(threat.severity, 0.5)

            total_score += severity_weight * threat.confidence_score

        # Normalize to 0-1 range
        return min(1.0, total_score / len(threats))


class MDMCommandProcessor:
    """MDM command processing engine."""

    def __init__(self, auth_system: EnterpriseAuthenticationSystem) -> dict:
        self.auth_system = auth_system
        self.pending_commands: Dict[str, MDMCommandRequest] = {}
        self.command_history: List[MDMCommandRequest] = []

    async def send_command(
        self,
        device_id: str,
        command_type: MDMCommand,
        parameters: Dict[str, Any],
        requested_by: str,
        reason: Optional[str] = None,
    ) -> MDMCommandRequest:
        """Send MDM command to device."""
        command = MDMCommandRequest(
            command_id=f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{device_id}",
            device_id=device_id,
            command_type=command_type,
            parameters=parameters,
            requested_by=requested_by,
            reason=reason,
        )

        # Validate command
        if not await self._validate_command(command):
            command.status = "failed"
            command.error_message = "Command validation failed"
            return command

        # Queue command for delivery
        self.pending_commands[command.command_id] = command
        command.status = "sent"
        command.sent_at = datetime.now()

        # Mock command delivery
        await self._deliver_command(command)

        return command

    async def _validate_command(self, command: MDMCommandRequest) -> bool:
        """Validate MDM command."""
        # Check if user has permission to send command
        user_info = self.auth_system.get_user_info(command.requested_by)
        if not user_info:
            return False

        # Check role-based permissions
        user_roles = set(user_info["roles"])
        required_roles = {
            MDMCommand.WIPE_DEVICE: {"system_admin", "security_admin"},
            MDMCommand.LOCK_DEVICE: {"system_admin", "security_admin", "mdm_admin"},
            MDMCommand.INSTALL_APP: {"system_admin", "mdm_admin"},
            MDMCommand.UNINSTALL_APP: {"system_admin", "mdm_admin"},
        }

        if command.command_type in required_roles:
            if not required_roles[command.command_type].intersection(user_roles):
                return False

        return True

    async def _deliver_command(self, command: MDMCommandRequest) -> None:
        """Deliver command to device (mock implementation)."""
        # In real implementation, this would use push notifications
        # or device check-in mechanism to deliver commands

        # Simulate command execution delay
        await asyncio.sleep(0.1)

        # Mock successful execution
        command.status = "executed"
        command.executed_at = datetime.now()
        command.result = {
            "status": "success",
            "message": "Command executed successfully",
        }

        # Move to history
        if command.command_id in self.pending_commands:
            del self.pending_commands[command.command_id]

        self.command_history.append(command)

    async def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of MDM command."""
        # Check pending commands
        if command_id in self.pending_commands:
            command = self.pending_commands[command_id]
        else:
            # Check history
            command = next(
                (cmd for cmd in self.command_history if cmd.command_id == command_id),
                None,
            )

        if not command:
            return None

        return {
            "command_id": command.command_id,
            "device_id": command.device_id,
            "command_type": command.command_type,
            "status": command.status,
            "requested_at": command.requested_at.isoformat(),
            "sent_at": command.sent_at.isoformat() if command.sent_at else None,
            "executed_at": command.executed_at.isoformat()
            if command.executed_at
            else None,
            "result": command.result,
            "error_message": command.error_message,
        }

    def get_device_commands(
        self, device_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get command history for device."""
        device_commands = [
            cmd for cmd in self.command_history if cmd.device_id == device_id
        ]

        # Sort by request time, most recent first
        device_commands.sort(key=lambda x: x.requested_at, reverse=True)

        return [
            {
                "command_id": cmd.command_id,
                "command_type": cmd.command_type,
                "status": cmd.status,
                "requested_by": cmd.requested_by,
                "requested_at": cmd.requested_at.isoformat(),
                "executed_at": cmd.executed_at.isoformat() if cmd.executed_at else None,
                "reason": cmd.reason,
            }
            for cmd in device_commands[:limit]
        ]


class MobileDeviceManagement:
    """Main Mobile Device Management system."""

    def __init__(
        self, sdk: MobileERPSDK, auth_system: EnterpriseAuthenticationSystem
    ) -> dict:
        self.sdk = sdk
        self.auth_system = auth_system

        # Core components
        self.devices: Dict[str, DeviceProfile] = {}
        self.policies: Dict[str, SecurityPolicy] = {}
        self.applications: Dict[str, MobileApplication] = {}

        # Engines
        self.compliance_checker = DeviceComplianceChecker()
        self.threat_detector = ThreatDetectionEngine()
        self.command_processor = MDMCommandProcessor(auth_system)

        # Active threats
        self.active_threats: Dict[str, ThreatDetection] = {}

        # Setup default policies
        self._setup_default_policies()

        # Setup mock devices for testing
        self._setup_mock_devices()

    def _setup_default_policies(self) -> None:
        """Setup default security policies."""
        # Corporate device policy
        corporate_policy = SecurityPolicy(
            policy_id="corporate_standard",
            name="Corporate Standard Policy",
            description="Standard security policy for corporate devices",
            require_passcode=True,
            min_passcode_length=8,
            require_complex_passcode=True,
            max_failed_attempts=3,
            require_encryption=True,
            require_screen_lock=True,
            max_inactivity_minutes=10,
            allow_jailbreak=False,
            allow_debugging=False,
            require_antivirus=True,
            blacklisted_apps={
                "com.social.insecure",
                "org.gaming.suspicious",
                "net.file.sharing",
            },
            target_platforms={"ios", "android"},
            created_by="system",
        )

        self.policies[corporate_policy.policy_id] = corporate_policy

        # Executive device policy (stricter)
        executive_policy = SecurityPolicy(
            policy_id="executive_secure",
            name="Executive Secure Policy",
            description="High-security policy for executive devices",
            require_passcode=True,
            min_passcode_length=12,
            require_complex_passcode=True,
            max_failed_attempts=2,
            passcode_expiry_days=30,
            require_encryption=True,
            require_screen_lock=True,
            max_inactivity_minutes=5,
            require_vpn=True,
            allow_jailbreak=False,
            allow_debugging=False,
            allow_camera=False,
            allow_screenshot=False,
            require_certificate_authentication=True,
            location_tracking_enabled=True,
            auto_wipe_on_compliance_violation=True,
            target_user_groups={"executives"},
            created_by="system",
        )

        self.policies[executive_policy.policy_id] = executive_policy

    def _setup_mock_devices(self) -> None:
        """Setup mock devices for testing."""
        # Mock iPhone device
        iphone_device = DeviceProfile(
            device_id="iphone_001",
            user_id="user_001",
            device_name="John's iPhone",
            device_type="phone",
            platform="ios",
            platform_version="17.2",
            model="iPhone 15 Pro",
            manufacturer="Apple",
            serial_number="ABC123456789",
            imei="123456789012345",
            total_storage=256,
            available_storage=128,
            ram_size=8,
            battery_level=85,
            status=DeviceStatus.ACTIVE,
            screen_lock_enabled=True,
            encryption_enabled=True,
            jailbroken=False,
            installed_apps=[
                {
                    "name": "Mobile ERP",
                    "bundle_identifier": "com.company.erp",
                    "version": "2.1.0",
                    "managed": True,
                },
                {
                    "name": "Safari",
                    "bundle_identifier": "com.apple.safari",
                    "version": "17.2",
                    "managed": False,
                },
            ],
            managed_by="system",
            applied_policies={"corporate_standard"},
        )

        self.devices[iphone_device.device_id] = iphone_device

        # Mock Android device with compliance issues
        android_device = DeviceProfile(
            device_id="android_001",
            user_id="user_002",
            device_name="Jane's Samsung",
            device_type="phone",
            platform="android",
            platform_version="13.0",
            model="Galaxy S23",
            manufacturer="Samsung",
            total_storage=128,
            available_storage=64,
            ram_size=8,
            battery_level=45,
            status=DeviceStatus.ACTIVE,
            screen_lock_enabled=False,  # Compliance issue
            encryption_enabled=True,
            rooted=True,  # Compliance issue
            debug_enabled=True,  # Compliance issue
            installed_apps=[
                {
                    "name": "Mobile ERP",
                    "bundle_identifier": "com.company.erp",
                    "version": "2.1.0",
                    "managed": True,
                },
                {
                    "name": "Suspicious App",
                    "bundle_identifier": "com.malicious.app",
                    "version": "1.0",
                    "managed": False,
                },
            ],
            managed_by="system",
            applied_policies={"corporate_standard"},
        )

        self.devices[android_device.device_id] = android_device

    async def enroll_device(
        self,
        device_info: Dict[str, Any],
        user_id: str,
        policy_id: str = "corporate_standard",
    ) -> DeviceProfile:
        """Enroll new device in MDM system."""
        device = DeviceProfile(
            **device_info,
            user_id=user_id,
            status=DeviceStatus.ENROLLED,
            managed_by="system",
            applied_policies={policy_id},
        )

        self.devices[device.device_id] = device

        # Apply initial compliance check
        await self.check_device_compliance(device.device_id)

        return device

    async def check_device_compliance(self, device_id: str) -> Dict[str, Any]:
        """Check device compliance against applied policies."""
        device = self.devices.get(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Get applicable policies
        compliance_results = {}
        overall_status = ComplianceStatus.COMPLIANT
        all_violations = []

        for policy_id in device.applied_policies:
            policy = self.policies.get(policy_id)
            if not policy:
                continue

            status, violations = await self.compliance_checker.check_compliance(
                device, policy
            )

            compliance_results[policy_id] = {"status": status, "violations": violations}

            # Update overall status
            if status == ComplianceStatus.NON_COMPLIANT:
                overall_status = ComplianceStatus.NON_COMPLIANT
            elif (
                status == ComplianceStatus.WARNING
                and overall_status == ComplianceStatus.COMPLIANT
            ):
                overall_status = ComplianceStatus.WARNING

            all_violations.extend(violations)

        # Update device compliance status
        device.compliance_status = overall_status
        device.policy_violations = all_violations

        return {
            "device_id": device_id,
            "overall_status": overall_status,
            "policy_results": compliance_results,
            "total_violations": len(all_violations),
            "last_checked": datetime.now().isoformat(),
        }

    async def scan_device_threats(self, device_id: str) -> List[Dict[str, Any]]:
        """Scan device for security threats."""
        device = self.devices.get(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Run threat detection
        threats = await self.threat_detector.scan_device(device)

        # Store active threats
        for threat in threats:
            if threat.status == "new":
                self.active_threats[threat.threat_id] = threat
                device.security_threats.append(
                    {
                        "threat_id": threat.threat_id,
                        "type": threat.threat_type,
                        "severity": threat.severity,
                        "detected_at": threat.detected_at.isoformat(),
                    }
                )

        return [
            {
                "threat_id": threat.threat_id,
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "confidence_score": threat.confidence_score,
                "detected_at": threat.detected_at.isoformat(),
            }
            for threat in threats
        ]

    async def send_device_command(
        self,
        device_id: str,
        command_type: MDMCommand,
        parameters: Dict[str, Any],
        user_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send command to device."""
        device = self.devices.get(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Send command through processor
        command = await self.command_processor.send_command(
            device_id, command_type, parameters, user_id, reason
        )

        # Update device status if needed
        if command.status == "executed":
            if command_type == MDMCommand.WIPE_DEVICE:
                device.status = DeviceStatus.WIPED
            elif command_type == MDMCommand.LOCK_DEVICE:
                device.status = DeviceStatus.SUSPENDED

        return {
            "command_id": command.command_id,
            "status": command.status,
            "sent_at": command.sent_at.isoformat() if command.sent_at else None,
            "error_message": command.error_message,
        }

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed device information."""
        device = self.devices.get(device_id)
        if not device:
            return None

        return {
            "device_id": device.device_id,
            "user_id": device.user_id,
            "device_name": device.device_name,
            "platform": f"{device.platform} {device.platform_version}",
            "model": f"{device.manufacturer} {device.model}",
            "status": device.status,
            "compliance_status": device.compliance_status,
            "threat_score": device.threat_score,
            "last_checkin": device.last_checkin.isoformat()
            if device.last_checkin
            else None,
            "enrollment_date": device.enrollment_date.isoformat(),
            "applied_policies": list(device.applied_policies),
            "violation_count": len(device.policy_violations),
            "threat_count": len(device.security_threats),
            "managed_apps": len(device.managed_apps),
            "battery_level": device.battery_level,
            "storage_usage": {
                "total": device.total_storage,
                "available": device.available_storage,
                "used_percent": round(
                    ((device.total_storage or 1) - (device.available_storage or 0))
                    / (device.total_storage or 1)
                    * 100,
                    1,
                )
                if device.total_storage
                else 0,
            },
        }

    def list_devices(
        self,
        user_id: Optional[str] = None,
        status: Optional[DeviceStatus] = None,
        compliance_status: Optional[ComplianceStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List devices with optional filters."""
        devices = []

        for device in self.devices.values():
            # Apply filters
            if user_id and device.user_id != user_id:
                continue
            if status and device.status != status:
                continue
            if compliance_status and device.compliance_status != compliance_status:
                continue

            devices.append(
                {
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "user_id": device.user_id,
                    "platform": device.platform,
                    "model": device.model,
                    "status": device.status,
                    "compliance_status": device.compliance_status,
                    "threat_score": device.threat_score,
                    "last_checkin": device.last_checkin.isoformat()
                    if device.last_checkin
                    else None,
                }
            )

        return sorted(devices, key=lambda x: x["device_name"])

    def get_system_overview(self) -> Dict[str, Any]:
        """Get MDM system overview."""
        total_devices = len(self.devices)
        active_devices = len(
            [d for d in self.devices.values() if d.status == DeviceStatus.ACTIVE]
        )
        compliant_devices = len(
            [
                d
                for d in self.devices.values()
                if d.compliance_status == ComplianceStatus.COMPLIANT
            ]
        )
        total_threats = len(self.active_threats)

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "compliance_rate": round(compliant_devices / total_devices * 100, 1)
            if total_devices > 0
            else 0,
            "total_threats": total_threats,
            "critical_threats": len(
                [t for t in self.active_threats.values() if t.severity == "critical"]
            ),
            "total_policies": len(self.policies),
            "pending_commands": len(self.command_processor.pending_commands),
            "enrollment_trend": {"today": 2, "this_week": 8, "this_month": 25},
            "platform_distribution": {
                "ios": len([d for d in self.devices.values() if d.platform == "ios"]),
                "android": len(
                    [d for d in self.devices.values() if d.platform == "android"]
                ),
                "windows": len(
                    [d for d in self.devices.values() if d.platform == "windows"]
                ),
            },
        }
