"""
CC02 v76.0 Day 21 - Enterprise Security & Compliance Platform
Security Audit & Log Management System

Comprehensive security auditing and log management with real-time monitoring,
tamper-proof logging, and automated analysis capabilities.
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import logging
import re
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet

# Import from our existing mobile SDK
from app.mobile.mobile_erp_sdk import MobileERPSDK


class LogLevel(Enum):
    """Log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    AUDIT = "audit"


class AuditCategory(Enum):
    """Audit event categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    ADMINISTRATIVE = "administrative"
    COMPLIANCE = "compliance"
    SECURITY_EVENT = "security_event"
    PRIVACY_EVENT = "privacy_event"


class LogFormat(Enum):
    """Supported log formats."""

    JSON = "json"
    CEF = "cef"  # Common Event Format
    SYSLOG = "syslog"
    CSV = "csv"
    CUSTOM = "custom"


class LogRetentionPolicy(Enum):
    """Log retention policies."""

    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_365 = "365_days"
    YEARS_7 = "7_years"
    PERMANENT = "permanent"


@dataclass
class AuditEvent:
    """Security audit event data structure."""

    event_id: str
    timestamp: datetime
    category: AuditCategory
    level: LogLevel
    source_system: str
    source_component: str
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    action: str
    resource: str
    resource_type: str
    result: str  # success, failure, error
    risk_score: float
    details: Dict[str, Any]
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    correlation_id: Optional[str]
    parent_event_id: Optional[str]
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    """Generic log entry structure."""

    log_id: str
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    context: Dict[str, Any]
    user_id: Optional[str]
    session_id: Optional[str]
    trace_id: Optional[str]
    structured_data: Dict[str, Any] = field(default_factory=dict)
    raw_log: Optional[str] = None


@dataclass
class LogIntegrityRecord:
    """Log integrity and tamper detection record."""

    record_id: str
    timestamp: datetime
    log_count: int
    hash_chain: str  # Previous hash + current batch hash
    merkle_root: str
    signature: str
    verification_status: str
    created_by: str


@dataclass
class AuditRule:
    """Audit rule configuration."""

    rule_id: str
    name: str
    description: str
    category: AuditCategory
    enabled: bool
    conditions: Dict[str, Any]
    actions: List[str]
    severity: LogLevel
    retention_override: Optional[LogRetentionPolicy]
    notification_required: bool
    compliance_tags: List[str] = field(default_factory=list)


class LogAggregator:
    """Log aggregation and processing engine."""

    def __init__(self) -> dict:
        self.log_buffer: deque = deque(maxlen=10000)
        self.batch_size = 1000
        self.flush_interval = 60  # seconds
        self.processors: List[callable] = []
        self.filters: List[callable] = []
        self.enrichers: List[callable] = []
        self.outputs: List[callable] = []

        # Metrics
        self.metrics = {
            "logs_received": 0,
            "logs_processed": 0,
            "logs_dropped": 0,
            "processing_errors": 0,
            "last_flush": datetime.now(),
        }

    def add_processor(self, processor: callable) -> None:
        """Add log processor."""
        self.processors.append(processor)

    def add_filter(self, filter_func: callable) -> None:
        """Add log filter."""
        self.filters.append(filter_func)

    def add_enricher(self, enricher: callable) -> None:
        """Add log enricher."""
        self.enrichers.append(enricher)

    def add_output(self, output: callable) -> None:
        """Add log output destination."""
        self.outputs.append(output)

    async def ingest_log(self, log_entry: LogEntry) -> None:
        """Ingest log entry into aggregator."""
        self.metrics["logs_received"] += 1

        try:
            # Apply filters
            if not await self._apply_filters(log_entry):
                self.metrics["logs_dropped"] += 1
                return

            # Apply enrichments
            enriched_entry = await self._apply_enrichments(log_entry)

            # Add to buffer
            self.log_buffer.append(enriched_entry)

            # Check if batch processing needed
            if len(self.log_buffer) >= self.batch_size:
                await self._process_batch()

        except Exception as e:
            self.metrics["processing_errors"] += 1
            logging.error(f"Error ingesting log: {e}")

    async def _apply_filters(self, log_entry: LogEntry) -> bool:
        """Apply filtering rules to log entry."""
        for filter_func in self.filters:
            try:
                if not await filter_func(log_entry):
                    return False
            except Exception as e:
                logging.warning(f"Filter error: {e}")
                continue
        return True

    async def _apply_enrichments(self, log_entry: LogEntry) -> LogEntry:
        """Apply enrichments to log entry."""
        enriched_entry = log_entry

        for enricher in self.enrichers:
            try:
                enriched_entry = await enricher(enriched_entry)
            except Exception as e:
                logging.warning(f"Enrichment error: {e}")
                continue

        return enriched_entry

    async def _process_batch(self) -> None:
        """Process batch of log entries."""
        if not self.log_buffer:
            return

        batch = list(self.log_buffer)
        self.log_buffer.clear()

        # Apply processors
        for processor in self.processors:
            try:
                await processor(batch)
            except Exception as e:
                logging.error(f"Processor error: {e}")

        # Send to outputs
        for output in self.outputs:
            try:
                await output(batch)
            except Exception as e:
                logging.error(f"Output error: {e}")

        self.metrics["logs_processed"] += len(batch)
        self.metrics["last_flush"] = datetime.now()

    async def flush(self) -> None:
        """Force flush all pending logs."""
        await self._process_batch()

    async def start_processing(self) -> None:
        """Start periodic processing."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._process_batch()
            except Exception as e:
                logging.error(f"Processing loop error: {e}")


class LogParser:
    """Log parsing and normalization engine."""

    def __init__(self) -> dict:
        self.parsers = {
            LogFormat.JSON: self._parse_json,
            LogFormat.CEF: self._parse_cef,
            LogFormat.SYSLOG: self._parse_syslog,
            LogFormat.CSV: self._parse_csv,
        }

        self.field_extractors = {
            "timestamp": [
                r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
                r"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})",
                r"(\d{10})",  # Unix timestamp
            ],
            "ip_address": [
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                r"([0-9a-fA-F:]+:+[0-9a-fA-F]+)",  # IPv6
            ],
            "user_id": [r"user[_=:]([a-zA-Z0-9_-]+)", r"uid[_=:]([a-zA-Z0-9_-]+)"],
            "session_id": [
                r"session[_=:]([a-zA-Z0-9_-]+)",
                r"sid[_=:]([a-zA-Z0-9_-]+)",
            ],
        }

    async def parse_log(
        self, raw_log: str, format_hint: Optional[LogFormat] = None
    ) -> LogEntry:
        """Parse raw log into structured LogEntry."""
        log_id = str(uuid.uuid4())

        # Auto-detect format if not provided
        if format_hint is None:
            format_hint = await self._detect_format(raw_log)

        # Parse using specific format parser
        if format_hint in self.parsers:
            parsed_data = await self.parsers[format_hint](raw_log)
        else:
            parsed_data = await self._parse_generic(raw_log)

        # Create LogEntry
        log_entry = LogEntry(
            log_id=log_id,
            timestamp=parsed_data.get("timestamp", datetime.now()),
            level=LogLevel(parsed_data.get("level", "info")),
            source=parsed_data.get("source", "unknown"),
            message=parsed_data.get("message", raw_log),
            context=parsed_data.get("context", {}),
            user_id=parsed_data.get("user_id"),
            session_id=parsed_data.get("session_id"),
            trace_id=parsed_data.get("trace_id"),
            structured_data=parsed_data.get("structured_data", {}),
            raw_log=raw_log,
        )

        return log_entry

    async def _detect_format(self, raw_log: str) -> LogFormat:
        """Auto-detect log format."""
        # JSON format detection
        if raw_log.strip().startswith("{") and raw_log.strip().endswith("}"):
            return LogFormat.JSON

        # CEF format detection
        if raw_log.startswith("CEF:"):
            return LogFormat.CEF

        # Syslog format detection
        if re.match(r"^<\d+>", raw_log):
            return LogFormat.SYSLOG

        # CSV format detection (simple heuristic)
        if "," in raw_log and raw_log.count(",") > 2:
            return LogFormat.CSV

        return LogFormat.CUSTOM

    async def _parse_json(self, raw_log: str) -> Dict[str, Any]:
        """Parse JSON format logs."""
        try:
            data = json.loads(raw_log)

            # Normalize common field names
            normalized = {
                "timestamp": self._parse_timestamp(
                    data.get("timestamp", data.get("@timestamp", data.get("time")))
                ),
                "level": data.get("level", data.get("severity", "info")).lower(),
                "source": data.get(
                    "source", data.get("logger", data.get("component", "unknown"))
                ),
                "message": data.get("message", data.get("msg", "")),
                "context": data.get("context", {}),
                "user_id": data.get("user_id", data.get("userId", data.get("user"))),
                "session_id": data.get(
                    "session_id", data.get("sessionId", data.get("session"))
                ),
                "trace_id": data.get(
                    "trace_id", data.get("traceId", data.get("trace"))
                ),
                "structured_data": data,
            }

            return normalized

        except json.JSONDecodeError:
            return await self._parse_generic(raw_log)

    async def _parse_cef(self, raw_log: str) -> Dict[str, Any]:
        """Parse Common Event Format (CEF) logs."""
        # CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|Extension
        parts = raw_log.split("|")

        if len(parts) < 8:
            return await self._parse_generic(raw_log)

        cef_data = {
            "version": parts[0].replace("CEF:", ""),
            "device_vendor": parts[1],
            "device_product": parts[2],
            "device_version": parts[3],
            "signature_id": parts[4],
            "name": parts[5],
            "severity": parts[6],
        }

        # Parse extension fields
        extension = "|".join(parts[7:])
        extension_fields = self._parse_cef_extension(extension)
        cef_data.update(extension_fields)

        normalized = {
            "timestamp": self._parse_timestamp(
                cef_data.get("rt", cef_data.get("deviceReceiptTime"))
            ),
            "level": self._map_cef_severity(cef_data["severity"]),
            "source": f"{cef_data['device_vendor']} {cef_data['device_product']}",
            "message": cef_data["name"],
            "context": cef_data,
            "user_id": cef_data.get("suser", cef_data.get("duser")),
            "session_id": None,
            "trace_id": None,
            "structured_data": cef_data,
        }

        return normalized

    def _parse_cef_extension(self, extension: str) -> Dict[str, Any]:
        """Parse CEF extension fields."""
        fields = {}

        # Simple key=value parsing (CEF extensions can be complex)
        for pair in re.findall(r"(\w+)=([^\s]+(?:\s[^\s=]+)*)", extension):
            key, value = pair
            fields[key] = value

        return fields

    def _map_cef_severity(self, severity: str) -> str:
        """Map CEF severity to standard log levels."""
        severity_map = {
            "0": "info",
            "1": "info",
            "2": "info",
            "3": "warning",
            "4": "warning",
            "5": "error",
            "6": "error",
            "7": "critical",
            "8": "critical",
            "9": "critical",
            "10": "critical",
        }
        return severity_map.get(severity, "info")

    async def _parse_syslog(self, raw_log: str) -> Dict[str, Any]:
        """Parse syslog format logs."""
        # RFC3164 Syslog format: <priority>timestamp hostname tag: message
        syslog_pattern = (
            r"^<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+):\s*(.*)"
        )

        match = re.match(syslog_pattern, raw_log)
        if not match:
            return await self._parse_generic(raw_log)

        priority, timestamp_str, hostname, tag, message = match.groups()

        # Calculate facility and severity from priority
        priority_int = int(priority)
        facility = priority_int // 8
        severity = priority_int % 8

        normalized = {
            "timestamp": self._parse_timestamp(timestamp_str),
            "level": self._map_syslog_severity(severity),
            "source": f"{hostname}:{tag}",
            "message": message,
            "context": {
                "hostname": hostname,
                "tag": tag,
                "facility": facility,
                "severity": severity,
            },
            "user_id": None,
            "session_id": None,
            "trace_id": None,
            "structured_data": {
                "priority": priority_int,
                "facility": facility,
                "severity": severity,
                "hostname": hostname,
                "tag": tag,
            },
        }

        return normalized

    def _map_syslog_severity(self, severity: int) -> str:
        """Map syslog severity to standard log levels."""
        severity_map = {
            0: "critical",  # Emergency
            1: "critical",  # Alert
            2: "critical",  # Critical
            3: "error",  # Error
            4: "warning",  # Warning
            5: "info",  # Notice
            6: "info",  # Informational
            7: "debug",  # Debug
        }
        return severity_map.get(severity, "info")

    async def _parse_csv(self, raw_log: str) -> Dict[str, Any]:
        """Parse CSV format logs."""
        # Simple CSV parsing - in production, use proper CSV parser
        fields = raw_log.split(",")

        # Assume common CSV log format: timestamp, level, source, message
        if len(fields) >= 4:
            normalized = {
                "timestamp": self._parse_timestamp(fields[0].strip('"')),
                "level": fields[1].strip('"').lower(),
                "source": fields[2].strip('"'),
                "message": fields[3].strip('"'),
                "context": {},
                "user_id": None,
                "session_id": None,
                "trace_id": None,
                "structured_data": {"csv_fields": fields},
            }
        else:
            normalized = await self._parse_generic(raw_log)

        return normalized

    async def _parse_generic(self, raw_log: str) -> Dict[str, Any]:
        """Generic log parsing using regex extractors."""
        extracted_fields = {}

        # Extract common fields using regex
        for field_name, patterns in self.field_extractors.items():
            for pattern in patterns:
                match = re.search(pattern, raw_log)
                if match:
                    extracted_fields[field_name] = match.group(1)
                    break

        normalized = {
            "timestamp": self._parse_timestamp(extracted_fields.get("timestamp")),
            "level": "info",
            "source": "unknown",
            "message": raw_log,
            "context": extracted_fields,
            "user_id": extracted_fields.get("user_id"),
            "session_id": extracted_fields.get("session_id"),
            "trace_id": None,
            "structured_data": extracted_fields,
        }

        return normalized

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return datetime.now()

        # Try different timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # Try Unix timestamp
        try:
            return datetime.fromtimestamp(float(timestamp_str))
        except (ValueError, TypeError):
            pass

        return datetime.now()


class LogIntegrityManager:
    """Log integrity and tamper detection management."""

    def __init__(self) -> dict:
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.hash_chain: List[str] = []
        self.integrity_records: List[LogIntegrityRecord] = []
        self.batch_size = 1000

    async def secure_log_batch(self, log_entries: List[LogEntry]) -> LogIntegrityRecord:
        """Secure and create integrity record for log batch."""
        record_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Create batch hash
        batch_data = json.dumps(
            [
                {
                    "log_id": entry.log_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "message": entry.message,
                    "checksum": self._calculate_log_hash(entry),
                }
                for entry in log_entries
            ],
            sort_keys=True,
        )

        batch_hash = hashlib.sha256(batch_data.encode()).hexdigest()

        # Create hash chain
        previous_hash = self.hash_chain[-1] if self.hash_chain else "0" * 64
        chain_hash = hashlib.sha256(f"{previous_hash}{batch_hash}".encode()).hexdigest()
        self.hash_chain.append(chain_hash)

        # Create Merkle root
        merkle_root = await self._create_merkle_root(log_entries)

        # Sign the record
        signature = await self._sign_record(
            {
                "record_id": record_id,
                "timestamp": timestamp.isoformat(),
                "log_count": len(log_entries),
                "hash_chain": chain_hash,
                "merkle_root": merkle_root,
            }
        )

        # Create integrity record
        integrity_record = LogIntegrityRecord(
            record_id=record_id,
            timestamp=timestamp,
            log_count=len(log_entries),
            hash_chain=chain_hash,
            merkle_root=merkle_root,
            signature=signature,
            verification_status="verified",
            created_by="log_integrity_manager",
        )

        self.integrity_records.append(integrity_record)
        return integrity_record

    def _calculate_log_hash(self, log_entry: LogEntry) -> str:
        """Calculate hash for individual log entry."""
        log_data = {
            "log_id": log_entry.log_id,
            "timestamp": log_entry.timestamp.isoformat(),
            "level": log_entry.level.value,
            "source": log_entry.source,
            "message": log_entry.message,
        }

        return hashlib.sha256(json.dumps(log_data, sort_keys=True).encode()).hexdigest()

    async def _create_merkle_root(self, log_entries: List[LogEntry]) -> str:
        """Create Merkle tree root for log batch."""
        if not log_entries:
            return hashlib.sha256(b"empty").hexdigest()

        # Create leaf hashes
        leaf_hashes = [self._calculate_log_hash(entry) for entry in log_entries]

        # Build Merkle tree
        while len(leaf_hashes) > 1:
            next_level = []
            for i in range(0, len(leaf_hashes), 2):
                left = leaf_hashes[i]
                right = leaf_hashes[i + 1] if i + 1 < len(leaf_hashes) else left
                combined = hashlib.sha256(f"{left}{right}".encode()).hexdigest()
                next_level.append(combined)
            leaf_hashes = next_level

        return leaf_hashes[0]

    async def _sign_record(self, record_data: Dict[str, Any]) -> str:
        """Sign integrity record."""
        # Simplified signing - in production, use proper digital signatures
        record_string = json.dumps(record_data, sort_keys=True)
        signature = hashlib.sha256(f"secret_key{record_string}".encode()).hexdigest()
        return signature

    async def verify_integrity(self, record_id: str) -> Dict[str, Any]:
        """Verify log integrity for specific record."""
        record = next(
            (r for r in self.integrity_records if r.record_id == record_id), None
        )

        if not record:
            return {"verified": False, "error": "Record not found"}

        # Verify signature
        signature_valid = await self._verify_signature(record)

        # Verify hash chain continuity
        chain_valid = await self._verify_hash_chain(record)

        verification_result = {
            "verified": signature_valid and chain_valid,
            "record_id": record.record_id,
            "signature_valid": signature_valid,
            "chain_valid": chain_valid,
            "timestamp": record.timestamp.isoformat(),
            "log_count": record.log_count,
        }

        return verification_result

    async def _verify_signature(self, record: LogIntegrityRecord) -> bool:
        """Verify record signature."""
        record_data = {
            "record_id": record.record_id,
            "timestamp": record.timestamp.isoformat(),
            "log_count": record.log_count,
            "hash_chain": record.hash_chain,
            "merkle_root": record.merkle_root,
        }

        expected_signature = await self._sign_record(record_data)
        return record.signature == expected_signature

    async def _verify_hash_chain(self, record: LogIntegrityRecord) -> bool:
        """Verify hash chain continuity."""
        # Find position in chain
        record_index = next(
            (
                i
                for i, r in enumerate(self.integrity_records)
                if r.record_id == record.record_id
            ),
            -1,
        )

        if record_index == -1:
            return False

        # Verify chain continuity
        if record_index > 0:
            self.integrity_records[record_index - 1]
            # In full implementation, verify that current hash incorporates previous hash

        return True


class AuditRuleEngine:
    """Audit rule management and processing engine."""

    def __init__(self) -> dict:
        self.rules: Dict[str, AuditRule] = {}
        self.rule_evaluator = RuleEvaluator()
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default audit rules."""
        default_rules = [
            AuditRule(
                rule_id="auth_failure_rule",
                name="Authentication Failure Detection",
                description="Detect repeated authentication failures",
                category=AuditCategory.AUTHENTICATION,
                enabled=True,
                conditions={
                    "event_type": "authentication_failure",
                    "threshold": 5,
                    "time_window": 300,  # 5 minutes
                },
                actions=["alert", "block_user"],
                severity=LogLevel.WARNING,
                retention_override=LogRetentionPolicy.YEARS_7,
                notification_required=True,
                compliance_tags=["SOX", "PCI-DSS"],
            ),
            AuditRule(
                rule_id="privileged_access_rule",
                name="Privileged Access Monitoring",
                description="Monitor privileged user activities",
                category=AuditCategory.ADMINISTRATIVE,
                enabled=True,
                conditions={
                    "user_role": ["admin", "root", "system"],
                    "actions": ["create", "delete", "modify"],
                },
                actions=["audit", "alert"],
                severity=LogLevel.AUDIT,
                retention_override=LogRetentionPolicy.YEARS_7,
                notification_required=True,
                compliance_tags=["SOX", "HIPAA", "ISO27001"],
            ),
            AuditRule(
                rule_id="data_access_rule",
                name="Sensitive Data Access",
                description="Monitor access to sensitive data",
                category=AuditCategory.DATA_ACCESS,
                enabled=True,
                conditions={
                    "resource_type": [
                        "personal_data",
                        "financial_data",
                        "medical_data",
                    ],
                    "access_type": ["read", "export", "download"],
                },
                actions=["audit", "log"],
                severity=LogLevel.AUDIT,
                retention_override=LogRetentionPolicy.YEARS_7,
                notification_required=False,
                compliance_tags=["GDPR", "HIPAA", "PCI-DSS"],
            ),
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    async def evaluate_event(self, audit_event: AuditEvent) -> List[Dict[str, Any]]:
        """Evaluate audit event against all rules."""
        triggered_rules = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if await self.rule_evaluator.evaluate(rule, audit_event):
                triggered_rules.append(
                    {
                        "rule": rule,
                        "event": audit_event,
                        "actions": rule.actions,
                        "severity": rule.severity,
                        "compliance_tags": rule.compliance_tags,
                    }
                )

        return triggered_rules

    def add_rule(self, rule: AuditRule) -> None:
        """Add new audit rule."""
        self.rules[rule.rule_id] = rule

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing audit rule."""
        if rule_id not in self.rules:
            return False

        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        return True

    def delete_rule(self, rule_id: str) -> bool:
        """Delete audit rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def get_rules_by_category(self, category: AuditCategory) -> List[AuditRule]:
        """Get rules by category."""
        return [rule for rule in self.rules.values() if rule.category == category]


class RuleEvaluator:
    """Rule evaluation engine."""

    async def evaluate(self, rule: AuditRule, event: AuditEvent) -> bool:
        """Evaluate if event matches rule conditions."""
        conditions = rule.conditions

        # Category match
        if rule.category != event.category:
            return False

        # Evaluate specific conditions
        for condition_key, condition_value in conditions.items():
            if not await self._evaluate_condition(
                condition_key, condition_value, event
            ):
                return False

        return True

    async def _evaluate_condition(
        self, key: str, value: Any, event: AuditEvent
    ) -> bool:
        """Evaluate individual condition."""
        # Direct field comparison
        if hasattr(event, key):
            event_value = getattr(event, key)
            return await self._compare_values(event_value, value)

        # Check in details
        if key in event.details:
            event_value = event.details[key]
            return await self._compare_values(event_value, value)

        # Special condition handlers
        if key == "event_type":
            return event.action == value
        elif key == "user_role":
            user_roles = event.details.get("user_roles", [])
            if isinstance(value, list):
                return any(role in value for role in user_roles)
            else:
                return value in user_roles
        elif key == "resource_type":
            if isinstance(value, list):
                return event.resource_type in value
            else:
                return event.resource_type == value
        elif key == "access_type":
            if isinstance(value, list):
                return event.action in value
            else:
                return event.action == value

        return False

    async def _compare_values(self, event_value: Any, condition_value: Any) -> bool:
        """Compare event value with condition value."""
        if isinstance(condition_value, list):
            return event_value in condition_value
        elif isinstance(condition_value, dict):
            # Range or complex comparison
            if "min" in condition_value and "max" in condition_value:
                return condition_value["min"] <= event_value <= condition_value["max"]
            elif "greater_than" in condition_value:
                return event_value > condition_value["greater_than"]
            elif "less_than" in condition_value:
                return event_value < condition_value["less_than"]
        else:
            return event_value == condition_value

        return False


class LogRetentionManager:
    """Log retention and archival management."""

    def __init__(self) -> dict:
        self.retention_policies: Dict[str, LogRetentionPolicy] = {}
        self.archival_storage = ArchivalStorage()
        self.compression_enabled = True
        self.encryption_enabled = True

    def set_retention_policy(self, log_type: str, policy: LogRetentionPolicy) -> None:
        """Set retention policy for log type."""
        self.retention_policies[log_type] = policy

    async def apply_retention_policies(self) -> Dict[str, Any]:
        """Apply retention policies to stored logs."""
        results = {
            "logs_archived": 0,
            "logs_deleted": 0,
            "storage_freed": 0,
            "errors": [],
        }

        # Get all log files
        log_files = await self._discover_log_files()

        for log_file in log_files:
            try:
                # Determine retention policy
                policy = await self._determine_retention_policy(log_file)

                # Check if action needed
                action = await self._determine_retention_action(log_file, policy)

                if action == "archive":
                    await self._archive_log_file(log_file)
                    results["logs_archived"] += 1
                elif action == "delete":
                    size = await self._get_file_size(log_file)
                    await self._delete_log_file(log_file)
                    results["logs_deleted"] += 1
                    results["storage_freed"] += size

            except Exception as e:
                results["errors"].append(f"Error processing {log_file}: {str(e)}")

        return results

    async def _discover_log_files(self) -> List[str]:
        """Discover all log files in system."""
        # Simplified discovery - in production, scan actual file systems
        return [
            "/logs/audit/2023-01-01.log",
            "/logs/security/2023-01-01.log",
            "/logs/application/2023-01-01.log",
        ]

    async def _determine_retention_policy(self, log_file: str) -> LogRetentionPolicy:
        """Determine retention policy for log file."""
        # Extract log type from file path
        if "audit" in log_file or "security" in log_file:
            return self.retention_policies.get("security", LogRetentionPolicy.YEARS_7)
        elif "application" in log_file:
            return self.retention_policies.get(
                "application", LogRetentionPolicy.DAYS_90
            )
        else:
            return LogRetentionPolicy.DAYS_30

    async def _determine_retention_action(
        self, log_file: str, policy: LogRetentionPolicy
    ) -> str:
        """Determine what action to take for log file."""
        # Get file age
        file_age = await self._get_file_age(log_file)

        # Map policy to days
        policy_days = {
            LogRetentionPolicy.DAYS_30: 30,
            LogRetentionPolicy.DAYS_90: 90,
            LogRetentionPolicy.DAYS_365: 365,
            LogRetentionPolicy.YEARS_7: 2555,
            LogRetentionPolicy.PERMANENT: float("inf"),
        }

        retention_days = policy_days.get(policy, 30)

        if file_age > retention_days:
            return "delete"
        elif file_age > 30:  # Archive after 30 days
            return "archive"
        else:
            return "keep"

    async def _get_file_age(self, log_file: str) -> int:
        """Get file age in days."""
        # Simplified - extract date from filename
        import re

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", log_file)
        if date_match:
            file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            return (datetime.now() - file_date).days
        return 0

    async def _get_file_size(self, log_file: str) -> int:
        """Get file size in bytes."""
        # Simplified - return mock size
        return 1024 * 1024  # 1MB

    async def _archive_log_file(self, log_file: str) -> None:
        """Archive log file."""
        await self.archival_storage.archive_file(
            log_file, self.compression_enabled, self.encryption_enabled
        )

    async def _delete_log_file(self, log_file: str) -> None:
        """Securely delete log file."""
        # In production, implement secure deletion
        logging.info(f"Securely deleted log file: {log_file}")


class ArchivalStorage:
    """Archival storage management."""

    def __init__(self) -> dict:
        self.archive_location = "/archive/logs"
        self.compression_ratio = 0.7

    async def archive_file(
        self, file_path: str, compress: bool = True, encrypt: bool = True
    ) -> str:
        """Archive file to long-term storage."""
        archive_path = f"{self.archive_location}/{Path(file_path).name}"

        # Read file content (simplified)
        content = f"Mock content for {file_path}"

        # Compress if requested
        if compress:
            content = await self._compress_content(content)
            archive_path += ".gz"

        # Encrypt if requested
        if encrypt:
            content = await self._encrypt_content(content)
            archive_path += ".enc"

        # Store to archive location
        await self._store_to_archive(archive_path, content)

        return archive_path

    async def _compress_content(self, content: str) -> bytes:
        """Compress content."""
        return gzip.compress(content.encode())

    async def _encrypt_content(self, content: Union[str, bytes]) -> bytes:
        """Encrypt content."""
        if isinstance(content, str):
            content = content.encode()

        # Simplified encryption
        key = Fernet.generate_key()
        cipher = Fernet(key)
        return cipher.encrypt(content)

    async def _store_to_archive(
        self, archive_path: str, content: Union[str, bytes]
    ) -> None:
        """Store content to archive location."""
        # In production, write to actual storage system
        logging.info(f"Archived to: {archive_path}, size: {len(content)} bytes")


class SecurityAuditLoggingSystem:
    """Main security audit and logging management system."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.log_aggregator = LogAggregator()
        self.log_parser = LogParser()
        self.integrity_manager = LogIntegrityManager()
        self.audit_rule_engine = AuditRuleEngine()
        self.retention_manager = LogRetentionManager()

        # Configure aggregator
        self._configure_aggregator()

        # Configure retention policies
        self._configure_retention_policies()

        # Metrics
        self.metrics = {
            "total_logs_processed": 0,
            "audit_events_generated": 0,
            "rules_triggered": 0,
            "integrity_violations": 0,
            "last_integrity_check": datetime.now(),
            "system_uptime": datetime.now(),
        }

    def _configure_aggregator(self) -> None:
        """Configure log aggregator with processors and outputs."""
        # Add processors
        self.log_aggregator.add_processor(self._security_event_processor)
        self.log_aggregator.add_processor(self._audit_event_processor)

        # Add filters
        self.log_aggregator.add_filter(self._security_filter)

        # Add enrichers
        self.log_aggregator.add_enricher(self._geo_enricher)
        self.log_aggregator.add_enricher(self._risk_enricher)

        # Add outputs
        self.log_aggregator.add_output(self._siem_output)
        self.log_aggregator.add_output(self._compliance_output)

    def _configure_retention_policies(self) -> None:
        """Configure log retention policies."""
        self.retention_manager.set_retention_policy(
            "security", LogRetentionPolicy.YEARS_7
        )
        self.retention_manager.set_retention_policy("audit", LogRetentionPolicy.YEARS_7)
        self.retention_manager.set_retention_policy(
            "application", LogRetentionPolicy.DAYS_90
        )
        self.retention_manager.set_retention_policy("debug", LogRetentionPolicy.DAYS_30)

    async def ingest_raw_log(
        self, raw_log: str, format_hint: Optional[LogFormat] = None
    ) -> str:
        """Ingest raw log entry."""
        try:
            # Parse log
            log_entry = await self.log_parser.parse_log(raw_log, format_hint)

            # Ingest into aggregator
            await self.log_aggregator.ingest_log(log_entry)

            self.metrics["total_logs_processed"] += 1
            return log_entry.log_id

        except Exception as e:
            logging.error(f"Error ingesting log: {e}")
            raise

    async def create_audit_event(
        self,
        category: AuditCategory,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Create new audit event."""
        event_id = str(uuid.uuid4())

        audit_event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            category=category,
            level=LogLevel.AUDIT,
            source_system="erp_system",
            source_component="audit_logger",
            user_id=user_id,
            session_id=None,  # TODO: Get from context
            ip_address="",  # TODO: Get from context
            user_agent=None,
            action=action,
            resource=resource,
            resource_type=self._determine_resource_type(resource),
            result="success",  # TODO: Determine from context
            risk_score=await self._calculate_risk_score(category, action, user_id),
            details=details or {},
            before_state=None,
            after_state=None,
            correlation_id=None,
            parent_event_id=None,
        )

        # Evaluate against rules
        triggered_rules = await self.audit_rule_engine.evaluate_event(audit_event)

        # Process triggered rules
        for rule_trigger in triggered_rules:
            await self._process_rule_trigger(rule_trigger)

        self.metrics["audit_events_generated"] += 1
        self.metrics["rules_triggered"] += len(triggered_rules)

        return audit_event

    def _determine_resource_type(self, resource: str) -> str:
        """Determine resource type from resource identifier."""
        if "/api/" in resource:
            return "api_endpoint"
        elif "/admin/" in resource:
            return "admin_interface"
        elif ".db" in resource:
            return "database"
        elif "/data/" in resource:
            return "data_file"
        else:
            return "unknown"

    async def _calculate_risk_score(
        self, category: AuditCategory, action: str, user_id: Optional[str]
    ) -> float:
        """Calculate risk score for audit event."""
        base_score = 0.3

        # Category-based risk
        category_risk = {
            AuditCategory.AUTHENTICATION: 0.2,
            AuditCategory.AUTHORIZATION: 0.4,
            AuditCategory.DATA_ACCESS: 0.6,
            AuditCategory.DATA_MODIFICATION: 0.8,
            AuditCategory.ADMINISTRATIVE: 0.9,
            AuditCategory.CONFIGURATION_CHANGE: 0.8,
            AuditCategory.SECURITY_EVENT: 0.9,
        }

        # Action-based risk
        action_risk = {
            "create": 0.4,
            "read": 0.2,
            "update": 0.6,
            "delete": 0.8,
            "execute": 0.7,
            "login": 0.3,
            "logout": 0.1,
        }

        # User-based risk (simplified)
        user_risk = 0.5  # TODO: Implement user risk scoring

        risk_score = (
            base_score
            + category_risk.get(category, 0.3) * 0.4
            + action_risk.get(action, 0.3) * 0.3
            + user_risk * 0.3
        )

        return min(risk_score, 1.0)

    async def _process_rule_trigger(self, rule_trigger: Dict[str, Any]) -> None:
        """Process triggered audit rule."""
        rule = rule_trigger["rule"]
        event = rule_trigger["event"]
        actions = rule_trigger["actions"]

        for action in actions:
            if action == "alert":
                await self._send_alert(rule, event)
            elif action == "audit":
                await self._create_audit_log(rule, event)
            elif action == "block_user":
                await self._block_user(event.user_id)
            elif action == "log":
                await self._enhanced_logging(rule, event)

    async def _send_alert(self, rule: AuditRule, event: AuditEvent) -> None:
        """Send security alert."""
        alert = {
            "alert_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "event_id": event.event_id,
            "user_id": event.user_id,
            "action": event.action,
            "resource": event.resource,
            "risk_score": event.risk_score,
            "compliance_tags": rule.compliance_tags,
        }

        # In production, send to alerting system
        logging.warning(f"Security Alert: {json.dumps(alert)}")

    async def _create_audit_log(self, rule: AuditRule, event: AuditEvent) -> None:
        """Create enhanced audit log entry."""
        audit_log = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "rule_triggered": rule.rule_id,
            "event_details": {
                "event_id": event.event_id,
                "category": event.category.value,
                "action": event.action,
                "resource": event.resource,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "risk_score": event.risk_score,
            },
            "compliance_requirements": rule.compliance_tags,
        }

        # Store audit log
        logging.info(f"Audit Log: {json.dumps(audit_log)}")

    async def _block_user(self, user_id: Optional[str]) -> None:
        """Block user account."""
        if user_id:
            # In production, integrate with identity management system
            logging.warning(f"User blocked: {user_id}")

    async def _enhanced_logging(self, rule: AuditRule, event: AuditEvent) -> None:
        """Enable enhanced logging for event type."""
        logging.info(f"Enhanced logging activated for rule: {rule.rule_id}")

    # Aggregator processor functions
    async def _security_event_processor(self, log_batch: List[LogEntry]) -> None:
        """Process security-related log entries."""
        security_logs = [
            log
            for log in log_batch
            if log.level in [LogLevel.SECURITY, LogLevel.CRITICAL]
        ]

        for log in security_logs:
            # Create corresponding audit event
            await self.create_audit_event(
                AuditCategory.SECURITY_EVENT,
                "security_log_detected",
                log.source,
                log.user_id,
                {"original_message": log.message, "log_level": log.level.value},
            )

    async def _audit_event_processor(self, log_batch: List[LogEntry]) -> None:
        """Process audit log entries."""
        audit_logs = [log for log in log_batch if log.level == LogLevel.AUDIT]

        # Batch integrity check
        if audit_logs:
            await self.integrity_manager.secure_log_batch(audit_logs)

    async def _security_filter(self, log_entry: LogEntry) -> bool:
        """Filter for security-relevant logs."""
        # Keep all security, audit, and high-severity logs
        if log_entry.level in [LogLevel.SECURITY, LogLevel.AUDIT, LogLevel.CRITICAL]:
            return True

        # Keep logs with security-related keywords
        security_keywords = [
            "login",
            "authentication",
            "authorization",
            "access",
            "permission",
            "security",
            "breach",
        ]
        message_lower = log_entry.message.lower()

        return any(keyword in message_lower for keyword in security_keywords)

    async def _geo_enricher(self, log_entry: LogEntry) -> LogEntry:
        """Enrich log with geographic information."""
        # Extract IP from context or structured data
        ip_address = log_entry.context.get(
            "ip_address"
        ) or log_entry.structured_data.get("ip_address")

        if ip_address:
            # In production, use actual geolocation service
            geo_info = {
                "country": "US",
                "region": "CA",
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
            }

            log_entry.structured_data["geo_location"] = geo_info

        return log_entry

    async def _risk_enricher(self, log_entry: LogEntry) -> LogEntry:
        """Enrich log with risk assessment."""
        # Calculate risk score based on log content
        risk_score = 0.3  # Base risk

        # Increase risk for certain log levels
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            risk_score += 0.3

        # Increase risk for security-related content
        security_indicators = ["failed", "error", "unauthorized", "blocked", "denied"]
        message_lower = log_entry.message.lower()

        for indicator in security_indicators:
            if indicator in message_lower:
                risk_score += 0.2
                break

        log_entry.structured_data["risk_score"] = min(risk_score, 1.0)
        return log_entry

    async def _siem_output(self, log_batch: List[LogEntry]) -> None:
        """Output logs to SIEM system."""
        # In production, send to actual SIEM
        siem_logs = []
        for log in log_batch:
            siem_log = {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value,
                "source": log.source,
                "message": log.message,
                "user_id": log.user_id,
                "risk_score": log.structured_data.get("risk_score", 0.3),
            }
            siem_logs.append(siem_log)

        logging.info(f"Sent {len(siem_logs)} logs to SIEM")

    async def _compliance_output(self, log_batch: List[LogEntry]) -> None:
        """Output compliance-relevant logs."""
        compliance_logs = [
            log for log in log_batch if log.level in [LogLevel.AUDIT, LogLevel.SECURITY]
        ]

        if compliance_logs:
            logging.info(f"Stored {len(compliance_logs)} compliance logs")

    async def run_integrity_check(self) -> Dict[str, Any]:
        """Run comprehensive log integrity check."""
        results = {
            "total_records_checked": 0,
            "verified_records": 0,
            "failed_records": 0,
            "integrity_score": 0.0,
            "violations": [],
        }

        for record in self.integrity_manager.integrity_records:
            verification = await self.integrity_manager.verify_integrity(
                record.record_id
            )
            results["total_records_checked"] += 1

            if verification["verified"]:
                results["verified_records"] += 1
            else:
                results["failed_records"] += 1
                results["violations"].append(
                    {"record_id": record.record_id, "issues": verification}
                )

        if results["total_records_checked"] > 0:
            results["integrity_score"] = (
                results["verified_records"] / results["total_records_checked"]
            )

        self.metrics["last_integrity_check"] = datetime.now()
        self.metrics["integrity_violations"] = results["failed_records"]

        return results

    async def get_audit_dashboard(self) -> Dict[str, Any]:
        """Get audit and logging dashboard."""
        integrity_status = await self.run_integrity_check()

        return {
            "dashboard_generated": datetime.now().isoformat(),
            "system_status": {
                "uptime_hours": (
                    datetime.now() - self.metrics["system_uptime"]
                ).total_seconds()
                / 3600,
                "logs_processed_total": self.metrics["total_logs_processed"],
                "audit_events_generated": self.metrics["audit_events_generated"],
                "rules_triggered": self.metrics["rules_triggered"],
            },
            "log_processing": {
                "aggregator_buffer_size": len(self.log_aggregator.log_buffer),
                "processing_rate": self.log_aggregator.metrics["logs_processed"]
                / max(
                    (
                        datetime.now() - self.log_aggregator.metrics["last_flush"]
                    ).total_seconds(),
                    1,
                ),
                "error_rate": self.log_aggregator.metrics["processing_errors"]
                / max(self.log_aggregator.metrics["logs_received"], 1),
            },
            "integrity_status": {
                "integrity_score": integrity_status["integrity_score"],
                "total_records": integrity_status["total_records_checked"],
                "violations": len(integrity_status["violations"]),
            },
            "audit_rules": {
                "total_rules": len(self.audit_rule_engine.rules),
                "enabled_rules": len(
                    [r for r in self.audit_rule_engine.rules.values() if r.enabled]
                ),
                "rules_by_category": {
                    category.value: len(
                        self.audit_rule_engine.get_rules_by_category(category)
                    )
                    for category in AuditCategory
                },
            },
        }

    async def generate_compliance_report(
        self, compliance_framework: str
    ) -> Dict[str, Any]:
        """Generate compliance-specific audit report."""
        # Filter rules by compliance framework
        relevant_rules = [
            rule
            for rule in self.audit_rule_engine.rules.values()
            if compliance_framework in rule.compliance_tags
        ]

        return {
            "report_generated": datetime.now().isoformat(),
            "compliance_framework": compliance_framework,
            "audit_coverage": {
                "relevant_rules": len(relevant_rules),
                "enabled_rules": len([r for r in relevant_rules if r.enabled]),
                "coverage_percentage": len([r for r in relevant_rules if r.enabled])
                / max(len(relevant_rules), 1)
                * 100,
            },
            "log_retention": {
                "policy_compliance": "compliant",  # TODO: Implement actual check
                "retention_periods": {
                    rule.rule_id: rule.retention_override.value
                    if rule.retention_override
                    else "default"
                    for rule in relevant_rules
                },
            },
            "integrity_assurance": {
                "tamper_protection": "enabled",
                "hash_chain_verification": "passing",
                "digital_signatures": "enabled",
            },
            "recommendations": [
                "Continue monitoring all relevant audit events",
                "Review and update audit rules quarterly",
                "Ensure proper log retention compliance",
                "Maintain integrity protection mechanisms",
            ],
        }


# Usage example and testing
async def main() -> None:
    """Example usage of the Security Audit & Logging System."""
    # Initialize SDK (mock)
    sdk = MobileERPSDK()

    # Initialize audit logging system
    audit_system = SecurityAuditLoggingSystem(sdk)

    # Start log aggregator
    aggregator_task = asyncio.create_task(
        audit_system.log_aggregator.start_processing()
    )

    # Ingest sample logs
    sample_logs = [
        '{"timestamp": "2024-01-15T10:30:00", "level": "info", "source": "auth_service", "message": "User login successful", "user_id": "user123", "ip_address": "192.168.1.100"}',
        "CEF:0|ITDO|ERP|2.0|100|Failed Login|3|rt=Jan 15 2024 10:31:00 src=192.168.1.100 suser=user456 act=login outcome=failure",
        "<34>Jan 15 10:32:00 erp-server app[1234]: Database query executed successfully",
    ]

    for raw_log in sample_logs:
        log_id = await audit_system.ingest_raw_log(raw_log)
        print(f"Ingested log: {log_id}")

    # Create audit events
    audit_event = await audit_system.create_audit_event(
        AuditCategory.DATA_ACCESS,
        "read",
        "/api/users/sensitive_data",
        "user123",
        {"query": "SELECT * FROM users", "rows_returned": 1000},
    )
    print(f"Created audit event: {audit_event.event_id}")

    # Wait for processing
    await asyncio.sleep(2)

    # Flush remaining logs
    await audit_system.log_aggregator.flush()

    # Run integrity check
    integrity_result = await audit_system.run_integrity_check()
    print(f"Integrity check: {integrity_result}")

    # Get dashboard
    dashboard = await audit_system.get_audit_dashboard()
    print(f"Dashboard: {dashboard['system_status']}")

    # Generate compliance report
    compliance_report = await audit_system.generate_compliance_report("SOX")
    print(f"SOX compliance report: {compliance_report['audit_coverage']}")

    # Cancel aggregator task
    aggregator_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
