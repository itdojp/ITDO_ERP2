"""Organization service implementation."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, ValidationError
from app.interfaces.organization_interface import (
    DepartmentIntegrationMixin,
    OrganizationServiceInterface,
)
from app.models.organization import Organization
from app.models.role import UserRole
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationPolicy,
    OrganizationResponse,
    OrganizationSettings,
    OrganizationSettingsResponse,
    OrganizationSettingsUpdate,
    OrganizationSummary,
    OrganizationTree,
    OrganizationUpdate,
    PermissionTemplate,
)
from app.types import OrganizationId, UserId


class OrganizationService(OrganizationServiceInterface, DepartmentIntegrationMixin):
    """Service for organization business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = OrganizationRepository(Organization, db)

    def get_organization(
        self, organization_id: OrganizationId
    ) -> Optional[Organization]:
        """Get organization by ID."""
        return self.repository.get(organization_id)

    def list_organizations(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Organization], int]:
        """List organizations with pagination."""
        organizations = self.repository.get_multi(
            skip=skip, limit=limit, filters=filters
        )
        total = self.repository.get_count(filters=filters)
        return organizations, total

    def get_organization_hierarchy_tree(
        self, organization_id: OrganizationId
    ) -> OrganizationTree:
        """Get organization hierarchy tree."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound("Organization not found")

        # Build hierarchy tree
        def build_tree(org: Organization) -> OrganizationTree:
            children = []
            for subsidiary in org.subsidiaries:
                if subsidiary.is_active:
                    children.append(build_tree(subsidiary))

            return OrganizationTree(
                id=org.id,
                code=org.code,
                name=org.name,
                parent_id=org.parent_id,
                is_active=org.is_active,
                children=children,
                level=len(org.get_hierarchy_path()) - 1
            )

        return build_tree(org)

    def merge_organizations(
        self,
        source_org_id: OrganizationId,
        target_org_id: OrganizationId,
        merge_settings: Dict[str, Any],
        user_id: UserId
    ) -> Organization:
        """Merge source organization into target organization."""
        source_org = self.get_organization(source_org_id)
        target_org = self.get_organization(target_org_id)

        if not source_org or not target_org:
            raise NotFound("Organization not found")

        if source_org_id == target_org_id:
            raise ValidationError("Cannot merge organization with itself")

        # Move all departments to target organization
        for dept in source_org.departments:
            dept.organization_id = target_org_id

        # Move all users to target organization
        user_roles = self.db.query(UserRole).filter(
            UserRole.organization_id == source_org_id
        ).all()

        for user_role in user_roles:
            # Check if user already has role in target org
            existing_role = self.db.query(UserRole).filter(
                UserRole.user_id == user_role.user_id,
                UserRole.organization_id == target_org_id,
                UserRole.role_id == user_role.role_id
            ).first()

            if not existing_role:
                user_role.organization_id = target_org_id
            else:
                # If role exists, deactivate the source role
                user_role.is_active = False

        # Move subsidiaries to target organization
        for subsidiary in source_org.subsidiaries:
            subsidiary.parent_id = target_org_id

        # Merge settings if requested
        if merge_settings.get("merge_settings", False):
            target_settings = target_org.settings or {}
            source_settings = source_org.settings or {}
            merged_settings = {**target_settings, **source_settings}
            target_org.settings = merged_settings

        # Deactivate source organization
        source_org.is_active = False
        source_org.soft_delete(deleted_by=user_id)

        self.db.commit()
        self.db.refresh(target_org)

        return target_org

    def split_organization(
        self,
        parent_org_id: OrganizationId,
        new_org_data: OrganizationCreate,
        department_ids: List[int],
        user_id: UserId
    ) -> Organization:
        """Split organization by creating new subsidiary and moving departments."""
        parent_org = self.get_organization(parent_org_id)
        if not parent_org:
            raise NotFound("Parent organization not found")

        # Create new subsidiary organization
        new_org_dict = new_org_data.model_dump()
        new_org_dict["parent_id"] = parent_org_id
        new_org = Organization(**new_org_dict)
        self.db.add(new_org)
        self.db.flush()

        # Move specified departments to new organization
        from app.models.department import Department
        departments = self.db.query(Department).filter(
            Department.id.in_(department_ids),
            Department.organization_id == parent_org_id
        ).all()

        for dept in departments:
            dept.organization_id = new_org.id

            # Move department users to new organization
            dept_user_roles = self.db.query(UserRole).filter(
                UserRole.department_id == dept.id,
                UserRole.organization_id == parent_org_id
            ).all()

            for user_role in dept_user_roles:
                user_role.organization_id = new_org.id

        self.db.commit()
        self.db.refresh(new_org)

        return new_org

    def delegate_permissions(
        self,
        from_org_id: OrganizationId,
        to_org_id: OrganizationId,
        permission_codes: List[str],
        user_id: UserId
    ) -> bool:
        """Delegate permissions from parent org to subsidiary."""
        from_org = self.get_organization(from_org_id)
        to_org = self.get_organization(to_org_id)

        if not from_org or not to_org:
            raise NotFound("Organization not found")

        # Verify hierarchy relationship
        if to_org.parent_id != from_org_id:
            raise ValidationError("Can only delegate permissions to direct subsidiaries")

        # Create delegation record in settings
        to_org_settings = to_org.settings or {}
        delegated_permissions = to_org_settings.get("delegated_permissions", {})
        delegated_permissions[str(from_org_id)] = {
            "permissions": permission_codes,
            "delegated_by": user_id,
            "delegated_at": datetime.utcnow().isoformat()
        }
        to_org_settings["delegated_permissions"] = delegated_permissions
        to_org.settings = to_org_settings

        self.db.commit()

        return True

    def search_organizations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Organization], int]:
        """Search organizations by name."""
        # Get all matching organizations
        all_results = self.repository.search_by_name(query)

        # Apply additional filters if provided
        if filters:
            filtered_results = []
            for org in all_results:
                match = True
                for key, value in filters.items():
                    if hasattr(org, key) and getattr(org, key) != value:
                        match = False
                        break
                if match:
                    filtered_results.append(org)
            all_results = filtered_results

        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip : skip + limit]

        return paginated_results, total

    def create_organization(
        self, organization_data: OrganizationCreate, created_by: Optional[UserId] = None
    ) -> Organization:
        """Create a new organization."""
        # Validate unique code
        if not self.repository.validate_unique_code(organization_data.code):
            raise ValueError(
                f"Organization code '{organization_data.code}' already exists"
            )

        # Add audit fields
        data = organization_data.model_dump()
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by

        # Create organization
        return self.repository.create(OrganizationCreate(**data))

    def update_organization(
        self,
        organization_id: OrganizationId,
        organization_data: OrganizationUpdate,
        updated_by: Optional[UserId] = None,
    ) -> Optional[Organization]:
        """Update organization details."""
        # Check if organization exists
        organization = self.repository.get(organization_id)
        if not organization:
            return None

        # Validate unique code if being changed
        if organization_data.code and organization_data.code != organization.code:
            if not self.repository.validate_unique_code(
                organization_data.code, exclude_id=organization_id
            ):
                raise ValueError(
                    f"Organization code '{organization_data.code}' already exists"
                )

        # Add audit fields
        data = organization_data.model_dump(exclude_unset=True)
        if updated_by:
            data["updated_by"] = updated_by

        # Update organization
        return self.repository.update(organization_id, OrganizationUpdate(**data))

    def delete_organization(
        self, organization_id: OrganizationId, deleted_by: Optional[UserId] = None
    ) -> bool:
        """Soft delete an organization."""
        organization = self.repository.get(organization_id)
        if not organization:
            return False

        # Perform soft delete
        organization.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True

    def activate_organization(
        self, organization_id: OrganizationId, updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Activate an inactive organization."""
        org = self.repository.update(
            organization_id, OrganizationUpdate(is_active=True)
        )
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org

    def deactivate_organization(
        self, organization_id: OrganizationId, updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Deactivate an active organization."""
        org = self.repository.update(
            organization_id, OrganizationUpdate(is_active=False)
        )
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org

    def get_direct_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get direct subsidiaries of an organization."""
        return self.repository.get_subsidiaries(parent_id)

    def get_all_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get all subsidiaries recursively."""
        return self.repository.get_all_subsidiaries(parent_id)

    def has_active_subsidiaries(self, organization_id: OrganizationId) -> bool:
        """Check if organization has active subsidiaries."""
        subsidiaries = self.repository.get_subsidiaries(organization_id)
        return any(sub.is_active for sub in subsidiaries)

    def get_organization_summary(
        self, organization: Organization
    ) -> OrganizationSummary:
        """Get organization summary with counts."""
        parent_name = organization.parent.name if organization.parent else None
        department_count = self.repository.get_department_count(organization.id)
        user_count = self.repository.get_user_count(organization.id)

        return OrganizationSummary(
            id=organization.id,
            code=organization.code,
            name=organization.name,
            name_en=organization.name_en,
            is_active=organization.is_active,
            parent_id=organization.parent_id,
            parent_name=parent_name,
            department_count=department_count,
            user_count=user_count,
        )

    def get_organization_response(
        self, organization: Organization
    ) -> OrganizationResponse:
        """Get full organization response."""
        # Load parent if needed
        if organization.parent_id and not organization.parent:
            org_with_parent = self.repository.get_with_parent(organization.id)
            if org_with_parent:
                organization = org_with_parent

        # Get counts
        subsidiary_count = len(self.repository.get_subsidiaries(organization.id))

        # Build response
        data = organization.to_dict()
        data["parent"] = organization.parent.to_dict() if organization.parent else None
        data["full_address"] = organization.full_address
        data["is_subsidiary"] = organization.is_subsidiary
        data["is_parent"] = organization.is_parent
        data["subsidiary_count"] = subsidiary_count

        return OrganizationResponse.model_validate(data)

    def get_organization_tree(self) -> List[OrganizationTree]:
        """Get organization hierarchy tree."""
        # Get root organizations
        roots = self.repository.get_root_organizations()

        def build_tree(org: Organization, level: int = 0) -> OrganizationTree:
            """Build tree recursively."""
            children = []
            for sub in self.repository.get_subsidiaries(org.id):
                children.append(build_tree(sub, level + 1))

            return OrganizationTree(
                id=org.id,
                code=org.code,
                name=org.name,
                is_active=org.is_active,
                level=level,
                parent_id=org.parent_id,
                children=children,
            )

        return [build_tree(root) for root in roots]

    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: Optional[OrganizationId] = None,
    ) -> bool:
        """Check if user has permission for organizations."""
        # Simplified permission check for testing
        # In a real implementation, this would check actual permissions
        try:
            user = self.db.get(User, user_id)
            return user is not None and user.is_superuser
        except Exception:
            return False

    def update_settings(
        self,
        organization_id: OrganizationId,
        settings: Dict[str, Any],
        updated_by: Optional[UserId] = None,
    ) -> Optional[Organization]:
        """Update organization settings."""
        org = self.repository.update_settings(organization_id, settings)
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org

    def get_organization_by_code(self, code: str) -> Optional[Organization]:
        """Get organization by unique code."""
        return self.repository.get_by_code(code)

    def validate_parent_assignment(
        self, organization_id: OrganizationId, parent_id: OrganizationId
    ) -> bool:
        """Validate parent assignment to prevent circular references."""
        if organization_id == parent_id:
            raise ValidationError("Organization cannot be its own parent")

        # Check for circular reference
        current = self.repository.get(parent_id)
        while current:
            if current.id == organization_id:
                raise ValidationError("Circular reference detected in organization hierarchy")
            current = self.repository.get(current.parent_id) if current.parent_id else None

        return True

    def get_organization_statistics(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Get detailed statistics for an organization."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")  # noqa: N818

        stats = {
            "department_count": self.repository.get_department_count(organization_id),
            "user_count": self.repository.get_user_count(organization_id),
            "active_subsidiaries": len([s for s in self.get_direct_subsidiaries(organization_id) if s.is_active]),
            "total_subsidiaries": len(self.get_all_subsidiaries(organization_id)),
            "hierarchy_depth": len(org.get_hierarchy_path()),
        }

        return stats

    # OrganizationServiceInterface implementation

    def validate_organization_exists(self, organization_id: OrganizationId) -> bool:
        """Validate that organization exists and is active."""
        org = self.get_organization(organization_id)
        return org is not None and org.is_active

    def get_organization_settings_dict(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Get organization settings for department configuration."""
        org = self.get_organization(organization_id)
        if not org:
            return {}
        return org.settings or {}

    def can_user_access_organization(
        self, user_id: int, organization_id: OrganizationId
    ) -> bool:
        """Check if user has access to organization."""
        # Simplified implementation - check if user is superuser or has permissions
        return self.user_has_permission(user_id, "organizations.read", organization_id)

    def get_organization_hierarchy(
        self, organization_id: OrganizationId
    ) -> List[Organization]:
        """Get full hierarchy path for organization."""
        org = self.get_organization(organization_id)
        if not org:
            return []
        return org.get_hierarchy_path()

    def is_subsidiary_of(
        self, child_id: OrganizationId, parent_id: OrganizationId
    ) -> bool:
        """Check if child organization is a subsidiary of parent."""
        child = self.get_organization(child_id)
        if not child:
            return False

        # Check direct parent
        if child.parent_id == parent_id:
            return True

        # Check hierarchy recursively
        hierarchy = child.get_hierarchy_path()
        return any(org.id == parent_id for org in hierarchy[:-1])  # Exclude self

    def analyze_organization_impact(
        self, organization_id: OrganizationId
    ) -> Dict[str, Any]:
        """Analyze the impact of changes to an organization."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Get all subsidiaries
        all_subsidiaries = self.get_all_subsidiaries(organization_id)
        active_subsidiaries = [sub for sub in all_subsidiaries if sub.is_active]

        # Get department and user counts
        dept_count = self.repository.get_department_count(organization_id)
        user_count = self.repository.get_user_count(organization_id)

        # Calculate total counts including subsidiaries
        total_dept_count = dept_count
        total_user_count = user_count

        for sub in all_subsidiaries:
            total_dept_count += self.repository.get_department_count(sub.id)
            total_user_count += self.repository.get_user_count(sub.id)

        return {
            "organization_id": organization_id,
            "organization_name": org.name,
            "is_active": org.is_active,
            "direct_subsidiaries": len(self.get_direct_subsidiaries(organization_id)),
            "total_subsidiaries": len(all_subsidiaries),
            "active_subsidiaries": len(active_subsidiaries),
            "direct_departments": dept_count,
            "total_departments": total_dept_count,
            "direct_users": user_count,
            "total_users": total_user_count,
            "hierarchy_depth": self.repository.get_organization_depth(organization_id),
            "requires_attention": not org.is_active and len(active_subsidiaries) > 0,
        }

    def validate_organization_constraints(
        self, organization_data: OrganizationCreate, parent_id: Optional[OrganizationId] = None
    ) -> Dict[str, List[str]]:
        """Validate organization data against business constraints."""
        errors: Dict[str, List[str]] = {}

        # Validate code uniqueness
        if not self.repository.validate_unique_code(organization_data.code):
            errors.setdefault("code", []).append("Organization code already exists")

        # Validate parent assignment if provided
        if parent_id:
            parent = self.get_organization(parent_id)
            if not parent:
                errors.setdefault("parent_id", []).append("Parent organization not found")
            elif not parent.is_active:
                errors.setdefault("parent_id", []).append("Parent organization is inactive")

        # Validate industry if provided
        if hasattr(organization_data, 'industry') and organization_data.industry:
            valid_industries = [
                "Technology", "Finance", "Healthcare", "Manufacturing",
                "Education", "Government", "Retail", "Other"
            ]
            if organization_data.industry not in valid_industries:
                errors.setdefault("industry", []).append(f"Invalid industry. Must be one of: {', '.join(valid_industries)}")

        # Validate settings if provided
        if hasattr(organization_data, 'settings') and organization_data.settings:
            settings_errors = self._validate_organization_settings(organization_data.settings)
            if settings_errors:
                errors["settings"] = settings_errors

        return errors

    def _validate_organization_settings(self, settings: Dict[str, Any]) -> List[str]:
        """Validate organization settings."""
        errors = []

        # Validate fiscal year start format
        if "fiscal_year_start" in settings:
            fiscal_start = settings["fiscal_year_start"]
            if not isinstance(fiscal_start, str) or len(fiscal_start) != 5 or fiscal_start[2] != "-":
                errors.append("fiscal_year_start must be in MM-DD format")

        # Validate currency code
        if "default_currency" in settings:
            currency = settings["default_currency"]
            valid_currencies = ["JPY", "USD", "EUR", "GBP", "CNY"]
            if currency not in valid_currencies:
                errors.append(f"Invalid currency. Must be one of: {', '.join(valid_currencies)}")

        # Validate department constraints
        if "max_department_depth" in settings:
            max_depth = settings["max_department_depth"]
            if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
                errors.append("max_department_depth must be an integer between 1 and 10")

        if "max_department_budget" in settings:
            max_budget = settings["max_department_budget"]
            if not isinstance(max_budget, (int, float)) or max_budget < 0:
                errors.append("max_department_budget must be a positive number")

        return errors

    def get_organization_health_check(
        self, organization_id: OrganizationId
    ) -> Dict[str, Any]:
        """Perform health check for an organization."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        health_score = 100
        issues = []
        warnings = []

        # Check if organization is active
        if not org.is_active:
            health_score -= 30
            issues.append("Organization is inactive")

        # Check for active subsidiaries with inactive parent
        if not org.is_active:
            active_subs = [sub for sub in self.get_direct_subsidiaries(organization_id) if sub.is_active]
            if active_subs:
                health_score -= 20
                issues.append(f"Inactive organization has {len(active_subs)} active subsidiaries")

        # Check hierarchy depth
        depth = self.repository.get_organization_depth(organization_id)
        if depth > 5:
            health_score -= 10
            warnings.append(f"Organization hierarchy is very deep (depth: {depth})")

        # Check department count
        dept_count = self.repository.get_department_count(organization_id)
        if dept_count == 0:
            health_score -= 15
            warnings.append("Organization has no departments")
        elif dept_count > 50:
            health_score -= 5
            warnings.append(f"Organization has many departments ({dept_count})")

        # Check user count
        user_count = self.repository.get_user_count(organization_id)
        if user_count == 0:
            health_score -= 10
            warnings.append("Organization has no users")

        # Determine health status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 70:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        else:
            status = "poor"

        return {
            "organization_id": organization_id,
            "organization_name": org.name,
            "health_score": max(0, health_score),
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "recommendations": self._get_health_recommendations(issues, warnings),
        }

    def _get_health_recommendations(
        self, issues: List[str], warnings: List[str]
    ) -> List[str]:
        """Get health improvement recommendations."""
        recommendations = []

        if "Organization is inactive" in issues:
            recommendations.append("Consider activating the organization if it should be operational")

        if any("active subsidiaries" in issue for issue in issues):
            recommendations.append("Review subsidiary organization structure and activate parent if needed")

        if any("no departments" in warning for warning in warnings):
            recommendations.append("Create departments to organize the organization structure")

        if any("no users" in warning for warning in warnings):
            recommendations.append("Assign users to the organization")

        if any("very deep" in warning for warning in warnings):
            recommendations.append("Consider flattening the organization hierarchy")

        return recommendations

    def bulk_organization_operations(
        self, operation: str, organization_ids: List[OrganizationId], **kwargs: Any
    ) -> Dict[str, Any]:
        """Perform bulk operations on organizations."""
        results: Dict[str, Any] = {
            "operation": operation,
            "total_requested": len(organization_ids),
            "successful": [],
            "failed": [],
            "errors": {},
        }

        for org_id in organization_ids:
            try:
                if operation == "activate":
                    org = self.activate_organization(org_id, kwargs.get("updated_by"))
                    if org:
                        results["successful"].append(org_id)
                    else:
                        results["failed"].append(org_id)
                        results["errors"][org_id] = "Organization not found"

                elif operation == "deactivate":
                    org = self.deactivate_organization(org_id, kwargs.get("updated_by"))
                    if org:
                        results["successful"].append(org_id)
                    else:
                        results["failed"].append(org_id)
                        results["errors"][org_id] = "Organization not found"

                elif operation == "delete":
                    success = self.delete_organization(org_id, kwargs.get("deleted_by"))
                    if success:
                        results["successful"].append(org_id)
                    else:
                        results["failed"].append(org_id)
                        results["errors"][org_id] = "Organization not found or has dependencies"

                else:
                    results["failed"].append(org_id)
                    results["errors"][org_id] = f"Unknown operation: {operation}"

            except Exception as e:
                results["failed"].append(org_id)
                results["errors"][org_id] = str(e)

        results["success_rate"] = len(results["successful"]) / results["total_requested"] * 100

        return results

    def get_organization_settings(
        self, organization_id: OrganizationId, include_inherited: bool = True
    ) -> OrganizationSettingsResponse:
        """Get organization settings with inheritance support."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Get current settings or create default
        current_settings = org.settings or {}
        org_settings = OrganizationSettings(**current_settings)

        # Get inherited settings if requested and has parent
        inherited_settings = {}
        if include_inherited and org.parent_id:
            parent_settings = self.get_organization_settings(
                org.parent_id, include_inherited=False
            )
            inherited_settings = parent_settings.settings.model_dump()

        # Merge settings with inheritance
        effective_settings = {**inherited_settings, **org_settings.model_dump()}

        # Get permission templates
        permission_templates = self._get_permission_templates(organization_id)

        # Get active policies
        policies = self._get_organization_policies(organization_id)

        return OrganizationSettingsResponse(
            organization_id=organization_id,
            settings=org_settings,
            permission_templates=permission_templates,
            policies=policies,
            inherited_settings=inherited_settings if include_inherited else None,
            effective_settings=effective_settings,
        )

    def update_organization_settings(
        self,
        organization_id: OrganizationId,
        settings_update: OrganizationSettingsUpdate,
        updated_by: Optional[UserId] = None,
    ) -> OrganizationSettingsResponse:
        """Update organization settings."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Get current settings
        current_settings = org.settings or {}
        current_org_settings = OrganizationSettings(**current_settings)

        # Apply updates
        update_data = settings_update.model_dump(exclude_unset=True)
        updated_settings_dict = current_org_settings.model_dump()
        updated_settings_dict.update(update_data)

        # Validate updated settings
        updated_settings = OrganizationSettings(**updated_settings_dict)

        # Update organization
        org.settings = updated_settings.model_dump()
        if updated_by:
            org.updated_by = updated_by

        self.db.commit()
        self.db.refresh(org)

        return self.get_organization_settings(organization_id)

    def create_permission_template(
        self,
        organization_id: OrganizationId,
        template: PermissionTemplate,
        created_by: Optional[UserId] = None,
    ) -> PermissionTemplate:
        """Create a permission template for the organization."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Store template in organization settings
        current_settings = org.settings or {}
        templates = current_settings.get("permission_templates", [])

        # Generate ID for new template
        max_id = max([t.get("id", 0) for t in templates], default=0)
        template_dict = template.model_dump()
        template_dict["id"] = max_id + 1
        template_dict["created_at"] = datetime.utcnow().isoformat()
        template_dict["updated_at"] = datetime.utcnow().isoformat()

        # Check if making this default
        if template.is_default:
            # Remove default from other templates of same type
            for t in templates:
                if t.get("role_type") == template.role_type:
                    t["is_default"] = False

        templates.append(template_dict)
        current_settings["permission_templates"] = templates
        org.settings = current_settings

        if created_by:
            org.updated_by = created_by

        self.db.commit()

        return PermissionTemplate(**template_dict)

    def get_permission_templates(
        self, organization_id: OrganizationId, role_type: Optional[str] = None
    ) -> List[PermissionTemplate]:
        """Get permission templates for the organization."""
        templates = self._get_permission_templates(organization_id)

        if role_type:
            templates = [t for t in templates if t.role_type == role_type]

        return templates

    def _get_permission_templates(
        self, organization_id: OrganizationId
    ) -> List[PermissionTemplate]:
        """Internal method to get permission templates."""
        org = self.get_organization(organization_id)
        if not org:
            return []

        current_settings = org.settings or {}
        template_dicts = current_settings.get("permission_templates", [])

        # If no templates, create defaults
        if not template_dicts:
            template_dicts = self._create_default_permission_templates()
            current_settings["permission_templates"] = template_dicts
            org.settings = current_settings
            self.db.commit()

        return [PermissionTemplate(**t) for t in template_dicts if t.get("is_active", True)]

    def _create_default_permission_templates(self) -> List[Dict[str, Any]]:
        """Create default permission templates."""
        return [
            {
                "id": 1,
                "name": "Organization Admin",
                "description": "Full administrative access to organization",
                "role_type": "admin",
                "permissions": [
                    "organization.*",
                    "department.*",
                    "project.*",
                    "user.*",
                    "role.*",
                ],
                "is_default": True,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
            {
                "id": 2,
                "name": "Department Manager",
                "description": "Manage departments and projects",
                "role_type": "manager",
                "permissions": [
                    "department.read",
                    "department.update",
                    "project.*",
                    "user.read",
                    "user.invite",
                ],
                "is_default": True,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
            {
                "id": 3,
                "name": "Project Member",
                "description": "Participate in projects",
                "role_type": "member",
                "permissions": [
                    "organization.read",
                    "department.read",
                    "project.read",
                    "project.update_own",
                    "user.read",
                ],
                "is_default": True,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
            {
                "id": 4,
                "name": "Organization Viewer",
                "description": "Read-only access to organization",
                "role_type": "viewer",
                "permissions": [
                    "organization.read",
                    "department.read",
                    "project.read",
                    "user.read",
                ],
                "is_default": True,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        ]

    def create_organization_policy(
        self,
        organization_id: OrganizationId,
        policy: OrganizationPolicy,
        created_by: Optional[UserId] = None,
    ) -> OrganizationPolicy:
        """Create an organization policy."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Store policy in organization settings
        current_settings = org.settings or {}
        policies = current_settings.get("policies", [])

        # Generate ID for new policy
        max_id = max([p.get("id", 0) for p in policies], default=0)
        policy_dict = policy.model_dump()
        policy_dict["id"] = max_id + 1
        policy_dict["created_at"] = datetime.utcnow().isoformat()
        policy_dict["updated_at"] = datetime.utcnow().isoformat()

        # Convert date fields to ISO format
        if policy_dict.get("effective_from"):
            policy_dict["effective_from"] = policy_dict["effective_from"].isoformat()
        if policy_dict.get("expires_at"):
            policy_dict["expires_at"] = policy_dict["expires_at"].isoformat()

        policies.append(policy_dict)
        current_settings["policies"] = policies
        org.settings = current_settings

        if created_by:
            org.updated_by = created_by

        self.db.commit()

        return OrganizationPolicy(**policy_dict)

    def get_organization_policies(
        self,
        organization_id: OrganizationId,
        policy_type: Optional[str] = None,
        include_inherited: bool = True,
    ) -> List[OrganizationPolicy]:
        """Get organization policies."""
        policies = self._get_organization_policies(organization_id)

        # Include inherited policies
        org = self.get_organization(organization_id)
        if include_inherited and org and org.parent_id:
            parent_policies = self.get_organization_policies(
                org.parent_id,
                policy_type=policy_type,
                include_inherited=True,
            )
            # Merge with local policies (local takes precedence)
            policy_map = {p.name: p for p in parent_policies}
            for p in policies:
                policy_map[p.name] = p
            policies = list(policy_map.values())

        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]

        return policies

    def _get_organization_policies(
        self, organization_id: OrganizationId
    ) -> List[OrganizationPolicy]:
        """Internal method to get organization policies."""
        org = self.get_organization(organization_id)
        if not org:
            return []

        current_settings = org.settings or {}
        policy_dicts = current_settings.get("policies", [])

        # Filter active and non-expired policies
        active_policies = []
        for p in policy_dicts:
            if not p.get("is_active", True):
                continue

            # Check expiration
            if p.get("expires_at"):
                expires_at = datetime.fromisoformat(p["expires_at"].replace("Z", "+00:00"))
                if expires_at < datetime.utcnow():
                    continue

            # Check effective date
            if p.get("effective_from"):
                effective_from = datetime.fromisoformat(p["effective_from"].replace("Z", "+00:00"))
                if effective_from > datetime.utcnow():
                    continue

            active_policies.append(OrganizationPolicy(**p))

        return active_policies

    def apply_permission_template(
        self,
        organization_id: OrganizationId,
        user_id: UserId,
        template_id: int,
        updated_by: Optional[UserId] = None,
    ) -> bool:
        """Apply a permission template to a user."""
        org = self.get_organization(organization_id)
        if not org:
            raise NotFound(f"Organization {organization_id} not found")

        # Get template
        templates = self._get_permission_templates(organization_id)
        template = next((t for t in templates if t.id == template_id), None)

        if not template:
            raise NotFound(f"Permission template {template_id} not found")

        # Apply permissions to user
        # This would integrate with the permission service
        # For now, we'll store in user_roles or similar structure

        # Log the application
        current_settings = org.settings or {}
        template_applications = current_settings.get("template_applications", [])
        template_applications.append({
            "user_id": user_id,
            "template_id": template_id,
            "applied_by": updated_by,
            "applied_at": datetime.utcnow().isoformat(),
        })
        current_settings["template_applications"] = template_applications
        org.settings = current_settings

        if updated_by:
            org.updated_by = updated_by

        self.db.commit()

        return True

    def get_effective_settings(
        self, organization_id: OrganizationId, setting_path: str
    ) -> Any:
        """Get effective setting value considering inheritance."""
        settings_response = self.get_organization_settings(organization_id)

        # Navigate through setting path
        value: Any = settings_response.effective_settings
        for part in setting_path.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            if value is None:
                return None

        return value

    def add_subsidiary(
        self,
        parent_id: OrganizationId,
        subsidiary_data: OrganizationCreate,
        created_by: Optional[UserId] = None,
    ) -> Organization:
        """Add a subsidiary to an organization."""
        # Validate parent organization exists
        parent_org = self.get_organization(parent_id)
        if not parent_org:
            raise NotFound(f"Parent organization {parent_id} not found")

        if not parent_org.is_active:
            raise ValidationError("Cannot add subsidiary to inactive organization")

        # Create subsidiary with parent_id set
        subsidiary_dict = subsidiary_data.model_dump()
        subsidiary_dict["parent_id"] = parent_id
        
        # Inherit some settings from parent if not specified
        if not subsidiary_dict.get("settings"):
            parent_settings = parent_org.settings or {}
            subsidiary_dict["settings"] = {
                "fiscal_year_start": parent_settings.get("fiscal_year_start", "04-01"),
                "default_currency": parent_settings.get("default_currency", "JPY"),
                "timezone": parent_settings.get("timezone", "Asia/Tokyo"),
            }

        # Create the subsidiary
        subsidiary = self.repository.create(OrganizationCreate(**subsidiary_dict))
        
        # Copy permission templates from parent
        parent_templates = self._get_permission_templates(parent_id)
        for template in parent_templates:
            template_dict = template.model_dump()
            if template_dict.get("inheritable", True):
                new_template = template_dict.copy()
                new_template["organization_id"] = subsidiary.id
                new_template["id"] = None  # Generate new ID
                self._save_permission_template(subsidiary.id, new_template)

        if created_by:
            subsidiary.created_by = created_by
            self.db.commit()

        return subsidiary

    def _save_permission_template(
        self, organization_id: OrganizationId, template: Dict[str, Any]
    ) -> None:
        """Save a permission template to organization settings."""
        org = self.get_organization(organization_id)
        if not org:
            return

        current_settings = org.settings or {}
        templates = current_settings.get("permission_templates", [])
        
        # Generate ID if not present
        if not template.get("id"):
            max_id = max([t.get("id", 0) for t in templates], default=0)
            template["id"] = max_id + 1

        templates.append(template)
        current_settings["permission_templates"] = templates
        org.settings = current_settings
        self.db.commit()
