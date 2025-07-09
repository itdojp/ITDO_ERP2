"""Organization Service Interface for Department Service integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.models.organization import Organization
from app.types import OrganizationId


class OrganizationServiceInterface(ABC):
    """Interface for Organization Service used by Department Service."""

    @abstractmethod
    def get_organization(self, organization_id: OrganizationId) -> Optional[Organization]:
        """Get organization by ID."""
        pass

    @abstractmethod
    def validate_organization_exists(self, organization_id: OrganizationId) -> bool:
        """Validate that organization exists and is active."""
        pass

    @abstractmethod
    def get_organization_settings(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Get organization settings for department configuration."""
        pass

    @abstractmethod
    def can_user_access_organization(
        self, user_id: int, organization_id: OrganizationId
    ) -> bool:
        """Check if user has access to organization."""
        pass

    @abstractmethod
    def get_organization_hierarchy(
        self, organization_id: OrganizationId
    ) -> List[Organization]:
        """Get full hierarchy path for organization."""
        pass

    @abstractmethod
    def is_subsidiary_of(
        self, child_id: OrganizationId, parent_id: OrganizationId
    ) -> bool:
        """Check if child organization is a subsidiary of parent."""
        pass

    @abstractmethod
    def get_organization_statistics(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Get organization statistics including department counts."""
        pass


class DepartmentIntegrationMixin:
    """Mixin providing department-specific organization methods."""

    # Type hint to indicate this mixin expects to be mixed with OrganizationServiceInterface
    def get_organization(self, organization_id: OrganizationId) -> Optional[Organization]:
        """This method should be provided by the class using this mixin."""
        raise NotImplementedError("This method must be implemented by the class using this mixin")

    def get_department_code_prefix(self, organization_id: OrganizationId) -> str:
        """Get department code prefix from organization settings."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return "DEPT-"

        prefix = org.settings.get("department_code_prefix", "DEPT-")
        return str(prefix)

    def get_organization_currency(self, organization_id: OrganizationId) -> str:
        """Get default currency from organization settings."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return "JPY"

        currency = org.settings.get("default_currency", "JPY")
        return str(currency)

    def get_fiscal_year_start(self, organization_id: OrganizationId) -> str:
        """Get fiscal year start from organization settings."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return "04-01"

        fiscal_start = org.settings.get("fiscal_year_start", "04-01")
        return str(fiscal_start)

    def should_auto_approve_departments(self, organization_id: OrganizationId) -> bool:
        """Check if departments should be auto-approved in this organization."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return False

        auto_approve = org.settings.get("auto_approve_departments", False)
        return bool(auto_approve)

    def get_max_department_hierarchy_depth(self, organization_id: OrganizationId) -> int:
        """Get maximum allowed department hierarchy depth."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return 5  # Default depth limit

        max_depth = org.settings.get("max_department_depth", 5)
        return int(max_depth)

    def validate_department_budget_limit(
        self, organization_id: OrganizationId, budget: Optional[int]
    ) -> bool:
        """Validate department budget against organization limits."""
        if not budget:
            return True

        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return True

        max_budget = org.settings.get("max_department_budget")
        if max_budget is None:
            return True

        return budget <= int(max_budget)

    def get_organization_timezone(self, organization_id: OrganizationId) -> str:
        """Get organization timezone."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return "Asia/Tokyo"

        timezone = org.settings.get("time_zone", "Asia/Tokyo")
        return str(timezone)

    def can_create_department(
        self, organization_id: OrganizationId, current_depth: int = 0
    ) -> bool:
        """Check if departments can be created in this organization."""
        max_depth = self.get_max_department_hierarchy_depth(organization_id)
        return current_depth < max_depth

    def get_department_approval_workflow(self, organization_id: OrganizationId) -> str:
        """Get department approval workflow type."""
        org = self.get_organization(organization_id)
        if not org or not org.settings:
            return "manual"

        workflow = org.settings.get("department_approval_workflow", "manual")
        return str(workflow)

    def notify_department_created(
        self, organization_id: OrganizationId, department_data: Dict[str, Any]
    ) -> None:
        """Notify organization about department creation."""
        # This would trigger organization-level events/notifications
        # For now, this is a placeholder for future implementation
        pass

    def notify_department_updated(
        self, organization_id: OrganizationId, department_id: int, changes: Dict[str, Any]
    ) -> None:
        """Notify organization about department updates."""
        # This would trigger organization-level events/notifications
        # For now, this is a placeholder for future implementation
        pass

    def notify_department_deleted(
        self, organization_id: OrganizationId, department_id: int
    ) -> None:
        """Notify organization about department deletion."""
        # This would trigger organization-level events/notifications
        # For now, this is a placeholder for future implementation
        pass


# Data Transfer Objects for Department Service integration

class OrganizationInfo:
    """Organization information for department operations."""

    def __init__(
        self,
        id: OrganizationId,
        code: str,
        name: str,
        name_en: Optional[str],
        is_active: bool,
        settings: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.code = code
        self.name = name
        self.name_en = name_en
        self.is_active = is_active
        self.settings = settings or {}

    @property
    def department_code_prefix(self) -> str:
        """Get department code prefix."""
        prefix = self.settings.get("department_code_prefix", "DEPT-")
        return str(prefix)

    @property
    def default_currency(self) -> str:
        """Get default currency."""
        currency = self.settings.get("default_currency", "JPY")
        return str(currency)

    @property
    def fiscal_year_start(self) -> str:
        """Get fiscal year start."""
        start = self.settings.get("fiscal_year_start", "04-01")
        return str(start)

    @property
    def auto_approve_departments(self) -> bool:
        """Check if departments are auto-approved."""
        auto_approve = self.settings.get("auto_approve_departments", False)
        return bool(auto_approve)


class OrganizationConstraints:
    """Organization constraints for department validation."""

    def __init__(
        self,
        max_department_depth: int = 5,
        max_department_budget: Optional[int] = None,
        require_department_manager: bool = False,
        allow_cross_organization_transfers: bool = False
    ):
        self.max_department_depth = max_department_depth
        self.max_department_budget = max_department_budget
        self.require_department_manager = require_department_manager
        self.allow_cross_organization_transfers = allow_cross_organization_transfers

    @classmethod
    def from_organization_settings(
        cls, settings: Dict[str, Any]
    ) -> "OrganizationConstraints":
        """Create constraints from organization settings."""
        return cls(
            max_department_depth=settings.get("max_department_depth", 5),
            max_department_budget=settings.get("max_department_budget"),
            require_department_manager=settings.get("require_department_manager", False),
            allow_cross_organization_transfers=settings.get(
                "allow_cross_organization_transfers", False
            )
        )


# Integration events for Department Service

class OrganizationEvent:
    """Base class for organization events."""

    def __init__(self, organization_id: OrganizationId, event_type: str):
        self.organization_id = organization_id
        self.event_type = event_type


class OrganizationActivatedEvent(OrganizationEvent):
    """Event fired when organization is activated."""

    def __init__(self, organization_id: OrganizationId):
        super().__init__(organization_id, "organization_activated")


class OrganizationDeactivatedEvent(OrganizationEvent):
    """Event fired when organization is deactivated."""

    def __init__(self, organization_id: OrganizationId):
        super().__init__(organization_id, "organization_deactivated")


class OrganizationSettingsUpdatedEvent(OrganizationEvent):
    """Event fired when organization settings are updated."""

    def __init__(
        self,
        organization_id: OrganizationId,
        old_settings: Dict[str, Any],
        new_settings: Dict[str, Any]
    ):
        super().__init__(organization_id, "organization_settings_updated")
        self.old_settings = old_settings
        self.new_settings = new_settings


class OrganizationDeletedEvent(OrganizationEvent):
    """Event fired when organization is deleted."""

    def __init__(self, organization_id: OrganizationId):
        super().__init__(organization_id, "organization_deleted")


class DepartmentCreatedEvent(OrganizationEvent):
    """Event fired when a department is created in the organization."""

    def __init__(self, organization_id: OrganizationId, department_id: int):
        super().__init__(organization_id, "department_created")
        self.department_id = department_id


class DepartmentDeletedEvent(OrganizationEvent):
    """Event fired when a department is deleted from the organization."""

    def __init__(self, organization_id: OrganizationId, department_id: int):
        super().__init__(organization_id, "department_deleted")
        self.department_id = department_id


class OrganizationStructureChangedEvent(OrganizationEvent):
    """Event fired when organization structure changes affect departments."""

    def __init__(
        self,
        organization_id: OrganizationId,
        change_type: str,
        affected_departments: Optional[List[int]] = None
    ):
        super().__init__(organization_id, "organization_structure_changed")
        self.change_type = change_type  # "parent_changed", "activated", "deactivated"
        self.affected_departments = affected_departments or []
