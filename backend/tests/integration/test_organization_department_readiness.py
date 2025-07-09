"""Department Service integration readiness tests for Organization Service."""

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User
from app.services.organization import OrganizationService
from app.interfaces.organization_interface import (
    OrganizationInfo,
    OrganizationConstraints,
    OrganizationActivatedEvent,
    OrganizationDeactivatedEvent,
    OrganizationSettingsUpdatedEvent,
    OrganizationDeletedEvent,
)
from tests.factories import OrganizationFactory


class TestOrganizationDepartmentReadiness:
    """Test Organization Service readiness for Department Service integration."""

    def test_organization_service_interface_implementation(
        self,
        db_session: Session,
        test_organization: Organization,
    ):
        """Test that OrganizationService implements the required interface."""
        service = OrganizationService(db_session)
        
        # Verify interface methods are implemented
        assert hasattr(service, "get_organization")
        assert hasattr(service, "validate_organization_exists")
        assert hasattr(service, "get_organization_settings")
        assert hasattr(service, "can_user_access_organization")
        assert hasattr(service, "get_organization_hierarchy")
        assert hasattr(service, "is_subsidiary_of")
        
        # Test interface method implementations
        org = service.get_organization(test_organization.id)
        assert org is not None
        assert org.id == test_organization.id
        
        # Test validation
        assert service.validate_organization_exists(test_organization.id)
        assert not service.validate_organization_exists(99999)
        
        # Test settings access
        settings = service.get_organization_settings(test_organization.id)
        assert isinstance(settings, dict)

    def test_department_integration_mixin_methods(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test Department Service integration mixin methods."""
        service = OrganizationService(db_session)
        
        # Update organization with department-specific settings
        dept_settings = {
            "department_code_prefix": "DEPT-",
            "default_currency": "JPY",
            "fiscal_year_start": "04-01",
            "auto_approve_departments": True,
            "max_department_depth": 5,
            "max_department_budget": 1000000,
            "time_zone": "Asia/Tokyo",
        }
        
        updated_org = service.update_settings(
            test_organization.id, dept_settings, updated_by=test_user.id
        )
        assert updated_org is not None
        
        # Test mixin methods
        assert service.get_department_code_prefix(test_organization.id) == "DEPT-"
        assert service.get_organization_currency(test_organization.id) == "JPY"
        assert service.get_fiscal_year_start(test_organization.id) == "04-01"
        assert service.should_auto_approve_departments(test_organization.id) is True
        assert service.get_max_department_hierarchy_depth(test_organization.id) == 5
        assert service.get_organization_timezone(test_organization.id) == "Asia/Tokyo"
        
        # Test budget validation
        assert service.validate_department_budget_limit(test_organization.id, 500000)
        assert not service.validate_department_budget_limit(test_organization.id, 2000000)
        assert service.validate_department_budget_limit(test_organization.id, None)

    def test_organization_info_dto(
        self,
        db_session: Session,
        test_organization: Organization,
    ):
        """Test OrganizationInfo data transfer object."""
        # Create OrganizationInfo from test organization
        org_info = OrganizationInfo(
            id=test_organization.id,
            code=test_organization.code,
            name=test_organization.name,
            name_en=test_organization.name_en,
            is_active=test_organization.is_active,
            settings={
                "department_code_prefix": "TEST-",
                "default_currency": "USD",
                "fiscal_year_start": "01-01",
                "auto_approve_departments": False,
            }
        )
        
        # Test properties
        assert org_info.id == test_organization.id
        assert org_info.code == test_organization.code
        assert org_info.name == test_organization.name
        assert org_info.is_active == test_organization.is_active
        
        # Test setting properties
        assert org_info.department_code_prefix == "TEST-"
        assert org_info.default_currency == "USD"
        assert org_info.fiscal_year_start == "01-01"
        assert org_info.auto_approve_departments is False

    def test_organization_constraints_dto(self):
        """Test OrganizationConstraints data transfer object."""
        # Test default constraints
        constraints = OrganizationConstraints()
        assert constraints.max_department_depth == 5
        assert constraints.max_department_budget is None
        assert constraints.require_department_manager is False
        assert constraints.allow_cross_organization_transfers is False
        
        # Test custom constraints
        custom_constraints = OrganizationConstraints(
            max_department_depth=10,
            max_department_budget=5000000,
            require_department_manager=True,
            allow_cross_organization_transfers=True,
        )
        assert custom_constraints.max_department_depth == 10
        assert custom_constraints.max_department_budget == 5000000
        assert custom_constraints.require_department_manager is True
        assert custom_constraints.allow_cross_organization_transfers is True
        
        # Test from settings
        settings_dict = {
            "max_department_depth": 8,
            "max_department_budget": 2000000,
            "require_department_manager": True,
        }
        constraints_from_settings = OrganizationConstraints.from_organization_settings(settings_dict)
        assert constraints_from_settings.max_department_depth == 8
        assert constraints_from_settings.max_department_budget == 2000000
        assert constraints_from_settings.require_department_manager is True

    def test_organization_events(
        self,
        test_organization: Organization,
    ):
        """Test organization integration events."""
        # Test activation event
        activation_event = OrganizationActivatedEvent(test_organization.id)
        assert activation_event.organization_id == test_organization.id
        assert activation_event.event_type == "organization_activated"
        
        # Test deactivation event
        deactivation_event = OrganizationDeactivatedEvent(test_organization.id)
        assert deactivation_event.organization_id == test_organization.id
        assert deactivation_event.event_type == "organization_deactivated"
        
        # Test settings update event
        old_settings = {"department_prefix": "OLD-"}
        new_settings = {"department_prefix": "NEW-"}
        settings_event = OrganizationSettingsUpdatedEvent(
            test_organization.id, old_settings, new_settings
        )
        assert settings_event.organization_id == test_organization.id
        assert settings_event.event_type == "organization_settings_updated"
        assert settings_event.old_settings == old_settings
        assert settings_event.new_settings == new_settings
        
        # Test deletion event
        deletion_event = OrganizationDeletedEvent(test_organization.id)
        assert deletion_event.organization_id == test_organization.id
        assert deletion_event.event_type == "organization_deleted"

    def test_department_service_integration_scenarios(
        self,
        db_session: Session,
        test_user: User,
    ):
        """Test typical Department Service integration scenarios."""
        service = OrganizationService(db_session)
        
        # Scenario 1: Create organization with department settings
        org_with_dept_settings = OrganizationFactory.create(
            db_session,
            code="DEPT-READY-001",
            name="Department Ready Organization",
            settings={
                "department_code_prefix": "DR-",
                "max_department_depth": 3,
                "auto_approve_departments": False,
                "default_currency": "JPY",
                "fiscal_year_start": "04-01",
                "require_department_manager": True,
            },
            created_by=test_user.id,
        )
        
        # Verify department service can get needed information
        assert service.validate_organization_exists(org_with_dept_settings.id)
        assert service.get_department_code_prefix(org_with_dept_settings.id) == "DR-"
        assert service.get_max_department_hierarchy_depth(org_with_dept_settings.id) == 3
        assert not service.should_auto_approve_departments(org_with_dept_settings.id)
        
        # Scenario 2: Create organization hierarchy for departments
        parent_org = OrganizationFactory.create(
            db_session,
            code="PARENT-DEPT-001",
            name="Parent for Departments",
            created_by=test_user.id,
        )
        
        subsidiary_org = OrganizationFactory.create(
            db_session,
            code="SUB-DEPT-001",
            name="Subsidiary for Departments",
            parent_id=parent_org.id,
            created_by=test_user.id,
        )
        
        # Test hierarchy methods needed by Department Service
        assert service.is_subsidiary_of(subsidiary_org.id, parent_org.id)
        hierarchy = service.get_organization_hierarchy(subsidiary_org.id)
        assert len(hierarchy) >= 2
        
        # Scenario 3: Update settings that affect departments
        new_dept_settings = {
            "department_code_prefix": "UPDATED-",
            "max_department_budget": 500000,
            "auto_approve_departments": True,
        }
        
        updated = service.update_settings(
            org_with_dept_settings.id, new_dept_settings, updated_by=test_user.id
        )
        assert updated is not None
        
        # Verify changes are reflected in mixin methods
        assert service.get_department_code_prefix(org_with_dept_settings.id) == "UPDATED-"
        assert service.validate_department_budget_limit(org_with_dept_settings.id, 400000)
        assert not service.validate_department_budget_limit(org_with_dept_settings.id, 600000)
        assert service.should_auto_approve_departments(org_with_dept_settings.id)

    def test_organization_access_for_department_operations(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test organization access methods needed for department operations."""
        service = OrganizationService(db_session)
        
        # Test user access validation (needed for department CRUD)
        can_access = service.can_user_access_organization(
            test_user.id, test_organization.id
        )
        # In current simplified implementation, this checks superuser status
        assert can_access == test_user.is_superuser
        
        # Test organization existence validation (needed before creating departments)
        assert service.validate_organization_exists(test_organization.id)
        
        # Test organization retrieval (needed for department context)
        org = service.get_organization(test_organization.id)
        assert org is not None
        assert org.id == test_organization.id
        
        # Test settings retrieval (needed for department configuration)
        settings = service.get_organization_settings(test_organization.id)
        assert isinstance(settings, dict)

    def test_department_constraint_validation(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test constraint validation methods needed by Department Service."""
        service = OrganizationService(db_session)
        
        # Set up constraints via settings
        constraint_settings = {
            "max_department_depth": 4,
            "max_department_budget": 1000000,
            "require_department_manager": True,
            "allow_cross_organization_transfers": False,
        }
        
        updated_org = service.update_settings(
            test_organization.id, constraint_settings, updated_by=test_user.id
        )
        assert updated_org is not None
        
        # Test depth constraint
        max_depth = service.get_max_department_hierarchy_depth(test_organization.id)
        assert max_depth == 4
        
        # Test budget constraint
        assert service.validate_department_budget_limit(test_organization.id, 500000)
        assert service.validate_department_budget_limit(test_organization.id, 1000000)
        assert not service.validate_department_budget_limit(test_organization.id, 1500000)
        
        # Test null budget (should be valid)
        assert service.validate_department_budget_limit(test_organization.id, None)

    def test_default_settings_fallback(
        self,
        db_session: Session,
    ):
        """Test default settings fallback for organizations without explicit settings."""
        service = OrganizationService(db_session)
        
        # Create organization without settings
        org_without_settings = OrganizationFactory.create(
            db_session,
            code="NO-SETTINGS-001",
            name="Organization Without Settings",
            settings=None,
        )
        
        # Test that default values are returned
        assert service.get_department_code_prefix(org_without_settings.id) == "DEPT-"
        assert service.get_organization_currency(org_without_settings.id) == "JPY"
        assert service.get_fiscal_year_start(org_without_settings.id) == "04-01"
        assert service.should_auto_approve_departments(org_without_settings.id) is False
        assert service.get_max_department_hierarchy_depth(org_without_settings.id) == 5
        assert service.get_organization_timezone(org_without_settings.id) == "Asia/Tokyo"
        
        # Test budget validation with no limits
        assert service.validate_department_budget_limit(org_without_settings.id, 99999999)

    def test_organization_service_error_handling(
        self,
        db_session: Session,
    ):
        """Test error handling in organization service methods."""
        service = OrganizationService(db_session)
        
        # Test with non-existent organization
        assert not service.validate_organization_exists(99999)
        assert service.get_organization(99999) is None
        assert service.get_organization_settings(99999) == {}
        
        # Test mixin methods with non-existent organization
        assert service.get_department_code_prefix(99999) == "DEPT-"  # Default
        assert service.get_organization_currency(99999) == "JPY"  # Default
        assert service.get_fiscal_year_start(99999) == "04-01"  # Default
        assert service.should_auto_approve_departments(99999) is False  # Default
        assert service.get_max_department_hierarchy_depth(99999) == 5  # Default
        assert service.validate_department_budget_limit(99999, 1000000) is True  # Default (no limit)

    def test_integration_readiness_checklist(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Comprehensive readiness check for Department Service integration."""
        service = OrganizationService(db_session)
        
        # ✅ Interface implementation check
        from app.interfaces.organization_interface import OrganizationServiceInterface
        assert isinstance(service, OrganizationServiceInterface)
        
        # ✅ Required methods available
        required_methods = [
            "get_organization",
            "validate_organization_exists", 
            "get_organization_settings",
            "can_user_access_organization",
            "get_organization_hierarchy",
            "is_subsidiary_of",
        ]
        
        for method in required_methods:
            assert hasattr(service, method)
            assert callable(getattr(service, method))
        
        # ✅ Mixin methods available
        mixin_methods = [
            "get_department_code_prefix",
            "get_organization_currency",
            "get_fiscal_year_start",
            "should_auto_approve_departments",
            "get_max_department_hierarchy_depth",
            "validate_department_budget_limit",
            "get_organization_timezone",
        ]
        
        for method in mixin_methods:
            assert hasattr(service, method)
            assert callable(getattr(service, method))
        
        # ✅ Data transfer objects available
        from app.interfaces.organization_interface import (
            OrganizationInfo,
            OrganizationConstraints,
        )
        
        # Test DTO creation
        org_info = OrganizationInfo(
            id=test_organization.id,
            code=test_organization.code,
            name=test_organization.name,
            name_en=test_organization.name_en,
            is_active=test_organization.is_active,
        )
        assert org_info.id == test_organization.id
        
        constraints = OrganizationConstraints()
        assert constraints.max_department_depth == 5
        
        # ✅ Event classes available
        events_available = [
            OrganizationActivatedEvent,
            OrganizationDeactivatedEvent,
            OrganizationSettingsUpdatedEvent,
            OrganizationDeletedEvent,
        ]
        
        for event_class in events_available:
            # Test event creation
            if event_class == OrganizationSettingsUpdatedEvent:
                event = event_class(test_organization.id, {}, {})
            else:
                event = event_class(test_organization.id)
            assert event.organization_id == test_organization.id
        
        # ✅ All integration tests pass
        print("✅ Organization Service is ready for Department Service integration")
        print(f"✅ Interface methods: {len(required_methods)} implemented")
        print(f"✅ Mixin methods: {len(mixin_methods)} implemented")
        print(f"✅ Event classes: {len(events_available)} available")
        print("✅ All integration readiness tests passed")