"""Cross-tenant permissions service."""

from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.cross_tenant_permissions import (
    CrossTenantAuditLog,
    CrossTenantPermissionRule,
)
from app.models.organization import Organization
from app.models.user import User
from app.models.user_organization import UserOrganization
from app.schemas.cross_tenant_permissions import (
    BatchCrossTenantPermissionResult,
    CrossTenantPermissionResult,
    CrossTenantPermissionRuleCreate,
    CrossTenantPermissionRuleUpdate,
    OrganizationCrossTenantSummary,
    UserCrossTenantAccess,
)


class CrossTenantPermissionService:
    """Service for managing cross-tenant permissions."""

    def __init__(self, db: Session):
        self.db = db

    def create_permission_rule(
        self,
        rule_data: CrossTenantPermissionRuleCreate,
        created_by: User,
    ) -> CrossTenantPermissionRule:
        """Create a new cross-tenant permission rule."""
        # Validate organizations exist
        source_org = (
            self.db.query(Organization)
            .filter(Organization.id == rule_data.source_organization_id)
            .first()
        )
        target_org = (
            self.db.query(Organization)
            .filter(Organization.id == rule_data.target_organization_id)
            .first()
        )

        if not source_org:
            raise NotFound("Source organization not found")
        if not target_org:
            raise NotFound("Target organization not found")

        # Check permissions - user must be admin of source organization
        if not self._can_manage_cross_tenant_rules(created_by, source_org):
            raise PermissionDenied(
                "Insufficient permissions to create cross-tenant rules"
            )

        # Validate rule type
        if rule_data.rule_type not in ["allow", "deny"]:
            raise BusinessLogicError("Rule type must be 'allow' or 'deny'")

        # Check for conflicting rules with same priority
        existing_rule = (
            self.db.query(CrossTenantPermissionRule)
            .filter(
                and_(
                    CrossTenantPermissionRule.source_organization_id
                    == rule_data.source_organization_id,
                    CrossTenantPermissionRule.target_organization_id
                    == rule_data.target_organization_id,
                    CrossTenantPermissionRule.permission_pattern
                    == rule_data.permission_pattern,
                    CrossTenantPermissionRule.priority == rule_data.priority,
                    CrossTenantPermissionRule.is_active,
                )
            )
            .first()
        )

        if existing_rule:
            raise BusinessLogicError(
                "A rule with the same pattern and priority already exists"
            )

        # Create the rule
        rule = CrossTenantPermissionRule(
            source_organization_id=rule_data.source_organization_id,
            target_organization_id=rule_data.target_organization_id,
            permission_pattern=rule_data.permission_pattern,
            rule_type=rule_data.rule_type,
            priority=rule_data.priority,
            created_by=created_by.id,
            expires_at=rule_data.expires_at,
            notes=rule_data.notes,
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def update_permission_rule(
        self,
        rule_id: int,
        update_data: CrossTenantPermissionRuleUpdate,
        updated_by: User,
    ) -> CrossTenantPermissionRule:
        """Update an existing cross-tenant permission rule."""
        rule = (
            self.db.query(CrossTenantPermissionRule)
            .filter(CrossTenantPermissionRule.id == rule_id)
            .first()
        )

        if not rule:
            raise NotFound("Permission rule not found")

        # Check permissions
        source_org = (
            self.db.query(Organization)
            .filter(Organization.id == rule.source_organization_id)
            .first()
        )

        if not self._can_manage_cross_tenant_rules(updated_by, source_org):
            raise PermissionDenied(
                "Insufficient permissions to update cross-tenant rules"
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(rule, field, value)

        rule.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def delete_permission_rule(
        self,
        rule_id: int,
        deleted_by: User,
    ) -> bool:
        """Delete a cross-tenant permission rule."""
        rule = (
            self.db.query(CrossTenantPermissionRule)
            .filter(CrossTenantPermissionRule.id == rule_id)
            .first()
        )

        if not rule:
            raise NotFound("Permission rule not found")

        # Check permissions
        source_org = (
            self.db.query(Organization)
            .filter(Organization.id == rule.source_organization_id)
            .first()
        )

        if not self._can_manage_cross_tenant_rules(deleted_by, source_org):
            raise PermissionDenied(
                "Insufficient permissions to delete cross-tenant rules"
            )

        self.db.delete(rule)
        self.db.commit()

        return True

    def check_cross_tenant_permission(
        self,
        user_id: int,
        source_organization_id: int,
        target_organization_id: int,
        permission: str,
        log_check: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CrossTenantPermissionResult:
        """Check if a user has cross-tenant permission."""
        # Validate user and organizations
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Check if user is member of source organization
        source_membership = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == source_organization_id,
                    UserOrganization.is_active,
                )
            )
            .first()
        )

        if not source_membership:
            result = CrossTenantPermissionResult(
                user_id=user_id,
                source_organization_id=source_organization_id,
                target_organization_id=target_organization_id,
                permission=permission,
                allowed=False,
                reason="User is not a member of the source organization",
                matching_rules=[],
            )

            if log_check:
                self._log_permission_check(result, ip_address, user_agent)

            return result

        # Get applicable rules
        rules = self._get_applicable_rules(
            source_organization_id, target_organization_id, permission
        )

        # Apply rules in priority order (highest priority first)
        rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        allowed = False
        reason = "No applicable rules found - default deny"
        matching_rules = []

        for rule in rules:
            if rule.matches_permission(permission):
                matching_rules.append(rule)
                if rule.rule_type == "allow":
                    allowed = True
                    reason = f"Allowed by rule {rule.id}: {rule.permission_pattern}"
                    break
                elif rule.rule_type == "deny":
                    allowed = False
                    reason = f"Denied by rule {rule.id}: {rule.permission_pattern}"
                    break

        result = CrossTenantPermissionResult(
            user_id=user_id,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
            permission=permission,
            allowed=allowed,
            reason=reason,
            matching_rules=matching_rules,
        )

        if log_check:
            self._log_permission_check(result, ip_address, user_agent)

        return result

    def batch_check_permissions(
        self,
        user_id: int,
        source_organization_id: int,
        target_organization_id: int,
        permissions: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BatchCrossTenantPermissionResult:
        """Check multiple permissions in batch."""
        results = []
        allowed_count = 0
        denied_count = 0

        for permission in permissions:
            result = self.check_cross_tenant_permission(
                user_id=user_id,
                source_organization_id=source_organization_id,
                target_organization_id=target_organization_id,
                permission=permission,
                log_check=False,  # Don't log individual checks in batch
                ip_address=ip_address,
                user_agent=user_agent,
            )

            results.append(result)
            if result.allowed:
                allowed_count += 1
            else:
                denied_count += 1

        # Log batch check
        self._log_batch_permission_check(
            user_id,
            source_organization_id,
            target_organization_id,
            permissions,
            allowed_count,
            denied_count,
            ip_address,
            user_agent,
        )

        summary = {
            "total_permissions": len(permissions),
            "allowed": allowed_count,
            "denied": denied_count,
            "success_rate": allowed_count / len(permissions) if permissions else 0,
        }

        return BatchCrossTenantPermissionResult(
            user_id=user_id,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
            results=results,
            summary=summary,
        )

    def get_user_cross_tenant_access(
        self,
        user_id: int,
        source_organization_id: int,
        target_organization_id: int,
    ) -> UserCrossTenantAccess:
        """Get comprehensive cross-tenant access information for a user."""
        # Get all applicable rules
        rules = self._get_applicable_rules(
            source_organization_id, target_organization_id
        )

        allowed_permissions = set()
        denied_permissions = set()

        # Process rules to determine allowed/denied permissions
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            if rule.rule_type == "allow":
                allowed_permissions.add(rule.permission_pattern)
            elif rule.rule_type == "deny":
                denied_permissions.add(rule.permission_pattern)

        # Determine access level
        access_level = self._determine_access_level(
            allowed_permissions, denied_permissions
        )

        # Get last access time from audit logs
        last_access_log = (
            self.db.query(CrossTenantAuditLog)
            .filter(
                and_(
                    CrossTenantAuditLog.user_id == user_id,
                    CrossTenantAuditLog.source_organization_id
                    == source_organization_id,
                    CrossTenantAuditLog.target_organization_id
                    == target_organization_id,
                    CrossTenantAuditLog.result == "allowed",
                )
            )
            .order_by(desc(CrossTenantAuditLog.created_at))
            .first()
        )

        return UserCrossTenantAccess(
            user_id=user_id,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
            allowed_permissions=list(allowed_permissions),
            denied_permissions=list(denied_permissions),
            effective_permissions=list(allowed_permissions - denied_permissions),
            access_level=access_level,
            last_accessed=last_access_log.created_at if last_access_log else None,
        )

    def get_organization_cross_tenant_summary(
        self,
        organization_id: int,
    ) -> OrganizationCrossTenantSummary:
        """Get cross-tenant permission summary for an organization."""
        org = (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )
        if not org:
            raise NotFound("Organization not found")

        # Count outbound rules (this org granting access to others)
        outbound_rules = (
            self.db.query(CrossTenantPermissionRule)
            .filter(
                and_(
                    CrossTenantPermissionRule.source_organization_id == organization_id,
                    CrossTenantPermissionRule.is_active,
                )
            )
            .count()
        )

        # Count inbound rules (other orgs granting access to this org)
        inbound_rules = (
            self.db.query(CrossTenantPermissionRule)
            .filter(
                and_(
                    CrossTenantPermissionRule.target_organization_id == organization_id,
                    CrossTenantPermissionRule.is_active,
                )
            )
            .count()
        )

        # Count active cross-tenant users
        active_users = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.organization_id == organization_id,
                    UserOrganization.is_active,
                )
            )
            .count()
        )

        # Get last update time
        last_rule = (
            self.db.query(CrossTenantPermissionRule)
            .filter(
                or_(
                    CrossTenantPermissionRule.source_organization_id == organization_id,
                    CrossTenantPermissionRule.target_organization_id == organization_id,
                )
            )
            .order_by(desc(CrossTenantPermissionRule.updated_at))
            .first()
        )

        return OrganizationCrossTenantSummary(
            organization_id=organization_id,
            organization_name=org.name,
            outbound_rules=outbound_rules,
            inbound_rules=inbound_rules,
            active_cross_tenant_users=active_users,
            total_shared_permissions=outbound_rules + inbound_rules,
            last_updated=last_rule.updated_at if last_rule else None,
        )

    def cleanup_expired_rules(self) -> int:
        """Clean up expired cross-tenant permission rules."""
        now = datetime.now()

        expired_rules = (
            self.db.query(CrossTenantPermissionRule)
            .filter(
                and_(
                    CrossTenantPermissionRule.expires_at <= now,
                    CrossTenantPermissionRule.is_active,
                )
            )
            .all()
        )

        for rule in expired_rules:
            rule.is_active = False
            rule.updated_at = now

        self.db.commit()

        return len(expired_rules)

    def _get_applicable_rules(
        self,
        source_organization_id: int,
        target_organization_id: int,
        permission: Optional[str] = None,
    ) -> List[CrossTenantPermissionRule]:
        """Get applicable cross-tenant permission rules."""
        query = self.db.query(CrossTenantPermissionRule).filter(
            and_(
                CrossTenantPermissionRule.source_organization_id
                == source_organization_id,
                CrossTenantPermissionRule.target_organization_id
                == target_organization_id,
                CrossTenantPermissionRule.is_active,
            )
        )

        # Filter out expired rules
        now = datetime.now()
        query = query.filter(
            or_(
                CrossTenantPermissionRule.expires_at.is_(None),
                CrossTenantPermissionRule.expires_at > now,
            )
        )

        rules = query.all()

        # If permission is specified, filter by matching patterns
        if permission:
            rules = [rule for rule in rules if rule.matches_permission(permission)]

        return rules

    def _determine_access_level(
        self,
        allowed_permissions: Set[str],
        denied_permissions: Set[str],
    ) -> str:
        """Determine access level based on permissions."""
        if not allowed_permissions:
            return "none"

        # Check for full access patterns
        full_access_patterns = ["*", "admin:*", "full:*"]
        if any(pattern in allowed_permissions for pattern in full_access_patterns):
            return "full"

        # Check for read-only patterns
        read_patterns = ["read:*", "view:*"]
        write_patterns = ["write:*", "edit:*", "create:*", "delete:*"]

        has_read = any(pattern in allowed_permissions for pattern in read_patterns)
        has_write = any(pattern in allowed_permissions for pattern in write_patterns)

        if has_read and not has_write:
            return "read_only"
        elif has_read and has_write:
            return "full"
        else:
            return "restricted"

    def _can_manage_cross_tenant_rules(
        self,
        user: User,
        organization: Organization,
    ) -> bool:
        """Check if user can manage cross-tenant rules for organization."""
        if user.is_superuser:
            return True

        # Check if user is admin of the organization
        # This would typically check user roles within the organization
        # For now, simplified to superuser check
        return False

    def _log_permission_check(
        self,
        result: CrossTenantPermissionResult,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log a permission check to audit trail."""
        rule_id = result.matching_rules[0].id if result.matching_rules else None

        log_entry = CrossTenantAuditLog(
            user_id=result.user_id,
            source_organization_id=result.source_organization_id,
            target_organization_id=result.target_organization_id,
            permission=result.permission,
            action="check",
            result="allowed" if result.allowed else "denied",
            rule_id=rule_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log_entry)
        self.db.commit()

    def _log_batch_permission_check(
        self,
        user_id: int,
        source_organization_id: int,
        target_organization_id: int,
        permissions: List[str],
        allowed_count: int,
        denied_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log a batch permission check."""
        log_entry = CrossTenantAuditLog(
            user_id=user_id,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
            permission=f"BATCH:{len(permissions)} permissions",
            action="batch_check",
            result=f"allowed:{allowed_count}, denied:{denied_count}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log_entry)
        self.db.commit()
