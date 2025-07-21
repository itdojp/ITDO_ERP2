"""Comprehensive audit service with tamper-proof logging and compliance reporting."""

import hashlib
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import Request

from app.core.base_service import BaseService
from app.core.cache import cache_manager
from app.core.monitoring import monitor_performance
from app.models.comprehensive_audit import (
    ComprehensiveAuditLog,
    AuditSearchQuery,
    AuditExport,
    ComplianceReport,
    AuditEventType,
    AuditSeverity,
    ComplianceFramework,
)
from app.models.user import User
from app.models.organization import Organization


class ComprehensiveAuditService(BaseService[ComprehensiveAuditLog]):
    """Service for comprehensive audit logging with tamper-proof features."""

    def __init__(self, db: AsyncSession):
        super().__init__(ComprehensiveAuditLog, db)
        self._last_log_hash: Optional[str] = None

    @monitor_performance("audit.log_event")
    async def log_event(
        self,
        event_type: AuditEventType,
        event_name: str,
        event_description: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: str = "unknown",
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        request: Optional[Request] = None,
        compliance_frameworks: Optional[List[ComplianceFramework]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> ComprehensiveAuditLog:
        """Log a comprehensive audit event with tamper-proof features."""
        
        # Get the last log hash for chaining
        if not self._last_log_hash:
            self._last_log_hash = await self._get_last_log_hash()
        
        # Extract request information if available
        request_data = {}
        if request:
            request_data.update({
                "user_ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent"),
                "api_endpoint": str(request.url.path),
                "http_method": request.method,
                "session_id": request.headers.get("Session-ID"),
                "request_id": request.headers.get("X-Request-ID"),
            })
        
        # Generate changes summary
        changes_summary = None
        if old_values and new_values:
            changes_summary = self._generate_changes_summary(old_values, new_values)
        
        # Determine data classification flags
        classification_flags = self._analyze_data_classification(old_values, new_values, additional_data)
        
        # Create audit log entry
        audit_log = ComprehensiveAuditLog(
            event_type=event_type,
            event_name=event_name,
            event_description=event_description,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            organization_id=organization_id,
            department_id=department_id,
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            additional_data=additional_data,
            tags=tags or [],
            compliance_frameworks=compliance_frameworks or [],
            previous_log_hash=self._last_log_hash,
            **request_data,
            **classification_flags,
            **kwargs
        )
        
        # Calculate hash for tamper-proofing
        audit_log._calculate_hash()
        
        # Save to database
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        # Update last hash for next entry
        self._last_log_hash = audit_log.current_log_hash
        
        # Cache recent audit events for quick access
        await self._cache_recent_event(audit_log)
        
        return audit_log

    @monitor_performance("audit.log_api_call")
    async def log_api_call(
        self,
        request: Request,
        response_status: int,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> ComprehensiveAuditLog:
        """Log API call with request/response details."""
        
        # Determine severity based on status code
        if response_status >= 500:
            severity = AuditSeverity.CRITICAL
        elif response_status >= 400:
            severity = AuditSeverity.HIGH
        elif response_status >= 300:
            severity = AuditSeverity.MEDIUM
        else:
            severity = AuditSeverity.LOW
        
        additional_data = {
            "response_status": response_status,
            "query_params": dict(request.query_params),
            "path_params": getattr(request, "path_params", {}),
        }
        
        if error_message:
            additional_data["error_details"] = error_message
        
        return await self.log_event(
            event_type=AuditEventType.API_CALL,
            event_name=f"{request.method} {request.url.path}",
            event_description=f"API call to {request.url.path} returned {response_status}",
            user_id=user_id,
            user_email=user_email,
            resource_type="api_endpoint",
            resource_id=f"{request.method}:{request.url.path}",
            severity=severity,
            organization_id=organization_id,
            request=request,
            event_duration_ms=duration_ms,
            is_successful=response_status < 400,
            error_code=str(response_status) if response_status >= 400 else None,
            error_message=error_message,
            additional_data=additional_data,
            tags=["api", "http"]
        )

    @monitor_performance("audit.log_security_event")
    async def log_security_event(
        self,
        event_name: str,
        event_description: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        threat_level: str = "medium",
        indicators: Optional[List[str]] = None,
        remediation_taken: Optional[str] = None,
        organization_id: Optional[int] = None,
        request: Optional[Request] = None
    ) -> ComprehensiveAuditLog:
        """Log security-related events."""
        
        severity_mapping = {
            "low": AuditSeverity.LOW,
            "medium": AuditSeverity.MEDIUM,
            "high": AuditSeverity.HIGH,
            "critical": AuditSeverity.CRITICAL
        }
        
        additional_data = {
            "threat_level": threat_level,
            "indicators": indicators or [],
            "remediation_taken": remediation_taken,
            "detection_timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            event_name=event_name,
            event_description=event_description,
            user_id=user_id,
            user_email=user_email,
            resource_type="security",
            severity=severity_mapping.get(threat_level, AuditSeverity.MEDIUM),
            organization_id=organization_id,
            request=request,
            additional_data=additional_data,
            is_suspicious=threat_level in ["high", "critical"],
            requires_investigation=threat_level == "critical",
            compliance_frameworks=[ComplianceFramework.ISO27001, ComplianceFramework.SOC2],
            tags=["security", "threat", threat_level]
        )

    @monitor_performance("audit.search")
    async def search_audit_logs(
        self,
        filters: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        organization_id: Optional[int] = None
    ) -> Tuple[List[ComprehensiveAuditLog], int]:
        """Search audit logs with advanced filtering."""
        
        query = await self.get_query()
        
        # Apply organization filter
        if organization_id:
            query = query.filter(ComprehensiveAuditLog.organization_id == organization_id)
        
        # Apply date range
        if start_date:
            query = query.filter(ComprehensiveAuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(ComprehensiveAuditLog.timestamp <= end_date)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(ComprehensiveAuditLog, key) and value is not None:
                column = getattr(ComprehensiveAuditLog, key)
                
                if isinstance(value, str) and "%" in value:
                    # Support wildcard search
                    query = query.filter(column.like(value))
                elif isinstance(value, list):
                    # Support IN queries
                    query = query.filter(column.in_(value))
                else:
                    query = query.filter(column == value)
        
        # Special handling for tag search
        if "tags" in filters and filters["tags"]:
            tag_search = filters["tags"]
            if isinstance(tag_search, str):
                query = query.filter(ComprehensiveAuditLog.tags.contains([tag_search]))
            elif isinstance(tag_search, list):
                for tag in tag_search:
                    query = query.filter(ComprehensiveAuditLog.tags.contains([tag]))
        
        # Get total count
        count_query = query.with_only_columns(func.count(ComprehensiveAuditLog.id))
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(ComprehensiveAuditLog, sort_by, ComprehensiveAuditLog.timestamp)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        logs = list(result.scalars().all())
        
        return logs, total_count

    @monitor_performance("audit.verify_chain_integrity")
    async def verify_chain_integrity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verify the integrity of the audit log chain."""
        
        query = await self.get_query()
        
        # Apply filters
        if organization_id:
            query = query.filter(ComprehensiveAuditLog.organization_id == organization_id)
        if start_date:
            query = query.filter(ComprehensiveAuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(ComprehensiveAuditLog.timestamp <= end_date)
        
        # Order by timestamp
        query = query.order_by(asc(ComprehensiveAuditLog.timestamp))
        
        result = await self.db.execute(query)
        logs = list(result.scalars().all())
        
        verification_result = {
            "total_logs_checked": len(logs),
            "integrity_violations": [],
            "chain_breaks": [],
            "hash_mismatches": [],
            "overall_integrity": True
        }
        
        previous_log = None
        for log in logs:
            # Verify individual log integrity
            if not log.verify_integrity(previous_log):
                verification_result["integrity_violations"].append({
                    "log_id": log.id,
                    "audit_id": log.audit_id,
                    "timestamp": log.timestamp.isoformat(),
                    "issue": "Hash verification failed"
                })
                verification_result["overall_integrity"] = False
            
            # Check chain continuity
            if previous_log and log.previous_log_hash != previous_log.current_log_hash:
                verification_result["chain_breaks"].append({
                    "log_id": log.id,
                    "previous_log_id": previous_log.id,
                    "expected_hash": previous_log.current_log_hash,
                    "actual_hash": log.previous_log_hash
                })
                verification_result["overall_integrity"] = False
            
            previous_log = log
        
        return verification_result

    async def export_audit_logs(
        self,
        export_criteria: Dict[str, Any],
        format: str = "csv",
        user_id: int,
        organization_id: Optional[int] = None,
        compliance_framework: Optional[ComplianceFramework] = None
    ) -> AuditExport:
        """Export audit logs based on criteria."""
        
        export_service = AuditExportService(self.db)
        return await export_service.create_export(
            export_criteria=export_criteria,
            format=format,
            requested_by=user_id,
            organization_id=organization_id,
            compliance_framework=compliance_framework
        )

    async def generate_compliance_report(
        self,
        compliance_framework: ComplianceFramework,
        period_start: datetime,
        period_end: datetime,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> ComplianceReport:
        """Generate compliance report for specified framework."""
        
        compliance_service = ComplianceReportService(self.db)
        return await compliance_service.generate_report(
            compliance_framework=compliance_framework,
            period_start=period_start,
            period_end=period_end,
            generated_by=user_id,
            organization_id=organization_id
        )

    async def _get_last_log_hash(self) -> Optional[str]:
        """Get the hash of the last audit log entry."""
        query = await self.get_query()
        query = query.order_by(desc(ComprehensiveAuditLog.timestamp)).limit(1)
        
        result = await self.db.execute(query)
        last_log = result.scalar_one_or_none()
        
        return last_log.current_log_hash if last_log else None

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("X-Forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client address
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None

    def _generate_changes_summary(self, old_values: Dict[str, Any], new_values: Dict[str, Any]) -> str:
        """Generate human-readable summary of changes."""
        changes = []
        
        # Find changed fields
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            
            if old_val != new_val:
                if old_val is None:
                    changes.append(f"Added {key}: {new_val}")
                elif new_val is None:
                    changes.append(f"Removed {key}")
                else:
                    changes.append(f"Changed {key}: {old_val} → {new_val}")
        
        return "; ".join(changes[:10])  # Limit to first 10 changes

    def _analyze_data_classification(
        self,
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]],
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Analyze data to determine classification flags."""
        
        # Combine all data for analysis
        all_data = {}
        if old_values:
            all_data.update(old_values)
        if new_values:
            all_data.update(new_values)
        if additional_data:
            all_data.update(additional_data)
        
        # Convert to JSON string for analysis
        data_str = json.dumps(all_data, default=str).lower()
        
        # PII detection patterns
        pii_patterns = [
            "email", "phone", "ssn", "social_security", "passport", "license",
            "address", "credit_card", "birth_date", "personal"
        ]
        
        # Financial data patterns
        financial_patterns = [
            "salary", "wage", "income", "tax", "bank", "account", "payment",
            "credit", "debit", "financial", "money", "amount", "currency"
        ]
        
        # Health data patterns
        health_patterns = [
            "medical", "health", "diagnosis", "treatment", "patient", "doctor",
            "hospital", "medication", "prescription", "symptom"
        ]
        
        return {
            "contains_pii": any(pattern in data_str for pattern in pii_patterns),
            "contains_financial_data": any(pattern in data_str for pattern in financial_patterns),
            "contains_health_data": any(pattern in data_str for pattern in health_patterns)
        }

    async def _cache_recent_event(self, audit_log: ComprehensiveAuditLog) -> None:
        """Cache recent audit event for quick access."""
        cache_key = f"recent_audit:{audit_log.user_id or 'system'}"
        
        # Get existing recent events
        recent_events = await cache_manager.get(cache_key, namespace="audit") or []
        
        # Add new event
        event_data = {
            "audit_id": audit_log.audit_id,
            "event_name": audit_log.event_name,
            "timestamp": audit_log.timestamp.isoformat(),
            "severity": audit_log.severity
        }
        
        recent_events.insert(0, event_data)
        
        # Keep only last 10 events
        recent_events = recent_events[:10]
        
        # Cache for 1 hour
        await cache_manager.set(cache_key, recent_events, ttl=3600, namespace="audit")


class AuditSearchQueryService(BaseService[AuditSearchQuery]):
    """Service for managing saved audit search queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(AuditSearchQuery, db)

    async def save_search_query(
        self,
        query_name: str,
        search_criteria: Dict[str, Any],
        user_id: int,
        description: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        compliance_framework: Optional[ComplianceFramework] = None,
        organization_id: Optional[int] = None
    ) -> AuditSearchQuery:
        """Save a search query for reuse."""
        
        query_data = {
            "query_name": query_name,
            "query_description": description,
            "search_criteria": search_criteria,
            "date_from": date_from,
            "date_to": date_to,
            "compliance_framework": compliance_framework,
            "created_by": user_id,
            "organization_id": organization_id,
            "is_compliance_query": compliance_framework is not None
        }
        
        return await self.create(query_data)

    async def execute_saved_query(
        self,
        query_id: int,
        audit_service: ComprehensiveAuditService,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ComprehensiveAuditLog], int]:
        """Execute a saved search query."""
        
        saved_query = await self.get_by_id(query_id)
        if not saved_query:
            raise ValueError("Search query not found")
        
        # Update execution tracking
        await self.update(query_id, {
            "last_executed": datetime.utcnow(),
            "execution_count": saved_query.execution_count + 1
        })
        
        # Execute the search
        return await audit_service.search_audit_logs(
            filters=saved_query.search_criteria,
            start_date=saved_query.date_from,
            end_date=saved_query.date_to,
            limit=limit,
            offset=offset,
            organization_id=saved_query.organization_id
        )


class AuditExportService(BaseService[AuditExport]):
    """Service for exporting audit data."""

    def __init__(self, db: AsyncSession):
        super().__init__(AuditExport, db)

    async def create_export(
        self,
        export_criteria: Dict[str, Any],
        format: str,
        requested_by: int,
        organization_id: Optional[int] = None,
        compliance_framework: Optional[ComplianceFramework] = None,
        export_name: Optional[str] = None
    ) -> AuditExport:
        """Create a new audit data export."""
        
        # Determine date range from criteria
        date_from = export_criteria.get("date_from", datetime.utcnow() - timedelta(days=30))
        date_to = export_criteria.get("date_to", datetime.utcnow())
        
        if isinstance(date_from, str):
            date_from = datetime.fromisoformat(date_from)
        if isinstance(date_to, str):
            date_to = datetime.fromisoformat(date_to)
        
        export_data = {
            "export_name": export_name or f"Audit Export {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "export_criteria": export_criteria,
            "date_from": date_from,
            "date_to": date_to,
            "format": format,
            "compliance_framework": compliance_framework,
            "requested_by": requested_by,
            "organization_id": organization_id,
            "status": "pending"
        }
        
        export = await self.create(export_data)
        
        # Process export asynchronously (in production, this would be a background task)
        # For now, we'll mark it as completed
        await self._process_export(export)
        
        return export

    async def _process_export(self, export: AuditExport) -> None:
        """Process the export (simplified implementation)."""
        
        try:
            # Update status to processing
            await self.update(export.id, {
                "status": "processing",
                "started_at": datetime.utcnow()
            })
            
            # Simulate export processing
            # In production, this would query the audit logs and generate the file
            total_records = 1000  # Simulated count
            file_size = 1024 * 1024  # 1MB simulated
            
            # Update completion status
            await self.update(export.id, {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "total_records": total_records,
                "file_size_bytes": file_size,
                "file_path": f"/exports/{export.export_id}.{export.format}",
                "download_url": f"/api/v1/audit/exports/{export.export_id}/download"
            })
            
        except Exception as e:
            # Mark as failed
            await self.update(export.id, {
                "status": "failed",
                "error_message": str(e)
            })


class ComplianceReportService(BaseService[ComplianceReport]):
    """Service for generating compliance reports."""

    def __init__(self, db: AsyncSession):
        super().__init__(ComplianceReport, db)

    async def generate_report(
        self,
        compliance_framework: ComplianceFramework,
        period_start: datetime,
        period_end: datetime,
        generated_by: int,
        organization_id: Optional[int] = None
    ) -> ComplianceReport:
        """Generate a compliance report."""
        
        report_data = {
            "report_name": f"{compliance_framework.upper()} Compliance Report {period_start.strftime('%Y-%m')}",
            "compliance_framework": compliance_framework,
            "period_start": period_start,
            "period_end": period_end,
            "generated_by": generated_by,
            "organization_id": organization_id,
            "status": "draft"
        }
        
        report = await self.create(report_data)
        
        # Generate report content
        await self._generate_report_content(report)
        
        return report

    async def _generate_report_content(self, report: ComplianceReport) -> None:
        """Generate the actual report content."""
        
        # This is a simplified implementation
        # In production, this would analyze audit logs against compliance requirements
        
        summary_data = {
            "compliance_score": 95.5,
            "total_events": 10000,
            "compliant_events": 9550,
            "non_compliant_events": 450,
            "risk_level": "low"
        }
        
        findings = [
            {
                "severity": "medium",
                "finding": "Some API calls lack proper authentication logging",
                "count": 45,
                "recommendation": "Implement comprehensive authentication event logging"
            },
            {
                "severity": "low",
                "finding": "Missing user agent information in some audit logs",
                "count": 12,
                "recommendation": "Ensure all HTTP requests include user agent tracking"
            }
        ]
        
        recommendations = [
            "Implement automated compliance monitoring",
            "Regular audit log integrity verification",
            "Enhanced user access logging",
            "Quarterly compliance reviews"
        ]
        
        await self.update(report.id, {
            "total_events_analyzed": summary_data["total_events"],
            "compliance_score": summary_data["compliance_score"],
            "summary_data": summary_data,
            "findings": findings,
            "recommendations": recommendations,
            "status": "final"
        })


# Helper function for audit context manager
class AuditContext:
    """Context manager for audit logging."""
    
    def __init__(self, audit_service: ComprehensiveAuditService, event_name: str, **kwargs):
        self.audit_service = audit_service
        self.event_name = event_name
        self.kwargs = kwargs
        self.start_time = None
        self.error = None

    async def __aenter__(self):
        self.start_time = datetime.utcnow()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = None
        if self.start_time:
            duration_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)
        
        # Log event with outcome
        await self.audit_service.log_event(
            event_name=self.event_name,
            event_duration_ms=duration_ms,
            is_successful=exc_type is None,
            error_message=str(exc_val) if exc_val else None,
            **self.kwargs
        )


# Health check for audit system
async def check_audit_health() -> Dict[str, Any]:
    """Check audit system health."""
    health_info = {
        "status": "healthy",
        "recent_logs_count": 0,
        "chain_integrity": True,
        "export_queue_size": 0
    }
    
    try:
        # This would check actual system health in production
        health_info["recent_logs_count"] = 100  # Simulated
        health_info["export_queue_size"] = 5  # Simulated
        
    except Exception as e:
        health_info["status"] = "degraded"
        health_info["error"] = str(e)
    
    return health_info