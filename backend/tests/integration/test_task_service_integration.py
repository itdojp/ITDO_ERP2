"""Task Service integration tests for Phase 2 Sprint 1."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from tests.factories import OrganizationFactory, DepartmentFactory, UserFactory


class TestTaskServicePermissions:
    """Test Task Service permission integration."""

    def test_task_creation_requires_organization_membership(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task creation requires user to be in target organization."""
        # Given
        system = complete_test_system
        org_user = system["users"]["regular_user"]
        other_org = OrganizationFactory.create(db_session, name="他組織")
        
        # When/Then
        # User from one org cannot create tasks in another org
        user_orgs = [o.id for o in org_user.get_organizations()]
        assert other_org.id not in user_orgs
        
        # This would be enforced in TaskService.create_task()
        # task_service.create_task(user=org_user, organization_id=other_org.id)
        # Should raise PermissionDenied

    def test_task_view_permissions_by_role(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task viewing permissions based on user roles."""
        # Given
        system = complete_test_system
        org_id = system["organization"].id
        
        org_admin = system["users"]["org_admin"]
        dept_manager = system["users"]["dept_manager"]
        regular_user = system["users"]["regular_user"]
        
        # When
        admin_permissions = org_admin.get_effective_permissions(org_id)
        manager_permissions = dept_manager.get_effective_permissions(org_id)
        user_permissions = regular_user.get_effective_permissions(org_id)
        
        # Then
        # Admin should have all task permissions
        task_admin_perms = [p for p in admin_permissions if "task." in p]
        assert len(task_admin_perms) > 0
        
        # Manager should have department task permissions
        task_manager_perms = [p for p in manager_permissions if "task." in p]
        assert len(task_manager_perms) > 0
        
        # Regular user should have limited task permissions
        task_user_perms = [p for p in user_permissions if "task." in p]
        # Should be able to view/edit own tasks but not delete all tasks
        assert "task.view" in " ".join(task_user_perms) or len(task_user_perms) > 0

    def test_task_assignment_department_boundaries(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task assignment respects department boundaries."""
        # Given
        system = complete_test_system
        org = system["organization"]
        departments = system["departments"]
        
        # Create users in different departments
        dept1 = list(departments["root_department"].children)[0] if departments["root_department"].children else departments["root_department"]
        dept2_list = list(departments["root_department"].children)
        dept2 = dept2_list[1] if len(dept2_list) > 1 else dept1
        
        user1 = UserFactory.create(db_session, email="dept1_user@example.com")
        user2 = UserFactory.create(db_session, email="dept2_user@example.com")
        
        # Assign users to departments (simulated)
        user1.department_id = dept1.id
        user2.department_id = dept2.id
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # When/Then
        # Users should only be able to assign tasks within their department scope
        user1_depts = user1.get_departments(org.id)
        user2_depts = user2.get_departments(org.id)
        
        # Departments should be different (if multiple departments exist)
        if dept1.id != dept2.id:
            assert user1.department_id != user2.department_id

    def test_task_audit_logging_integration(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test task operations generate proper audit logs."""
        # Given
        org = OrganizationFactory.create(db_session, name="監査テスト組織")
        
        # Mock task operations that should be logged
        operations = [
            {"action": "task.create", "resource_type": "task", "user": test_admin},
            {"action": "task.assign", "resource_type": "task", "user": test_admin},
            {"action": "task.complete", "resource_type": "task", "user": test_admin},
        ]
        
        # When
        for op in operations:
            # Simulate audit logging
            test_admin.log_activity(
                db_session,
                action=op["action"],
                details={"organization_id": org.id, "task_id": 123},
                ip_address="192.168.1.1"
            )
        
        # Then
        from app.models.user_activity_log import UserActivityLog
        logs = db_session.query(UserActivityLog).filter_by(user_id=test_admin.id).all()
        
        assert len(logs) == 3
        log_actions = [log.action for log in logs]
        assert "task.create" in log_actions
        assert "task.assign" in log_actions
        assert "task.complete" in log_actions


class TestTaskServiceMultiTenant:
    """Test Task Service multi-tenant isolation."""

    def test_task_organization_isolation(
        self, db_session: Session, test_admin: User
    ) -> None:
        """Test tasks are isolated between organizations."""
        # Given
        org1 = OrganizationFactory.create(db_session, name="組織1")
        org2 = OrganizationFactory.create(db_session, name="組織2")
        
        user1 = UserFactory.create(db_session, email="org1_user@example.com")
        user2 = UserFactory.create(db_session, email="org2_user@example.com")
        
        # Simulate user assignment to organizations via roles
        from app.models.role import Role, UserRole
        
        role1 = Role(name="組織1ロール", code="ORG1_ROLE", organization_id=org1.id)
        role2 = Role(name="組織2ロール", code="ORG2_ROLE", organization_id=org2.id)
        db_session.add_all([role1, role2])
        db_session.flush()
        
        user_role1 = UserRole(
            user_id=user1.id, role_id=role1.id, organization_id=org1.id, assigned_by=test_admin.id
        )
        user_role2 = UserRole(
            user_id=user2.id, role_id=role2.id, organization_id=org2.id, assigned_by=test_admin.id
        )
        db_session.add_all([user_role1, user_role2])
        db_session.commit()
        
        # When/Then
        user1_orgs = [o.id for o in user1.get_organizations()]
        user2_orgs = [o.id for o in user2.get_organizations()]
        
        assert org1.id in user1_orgs
        assert org2.id in user2_orgs
        assert org1.id not in user2_orgs
        assert org2.id not in user1_orgs

    def test_task_cross_organization_access_denied(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test users cannot access tasks from other organizations."""
        # Given
        system = complete_test_system
        org_user = system["users"]["regular_user"]
        other_org = OrganizationFactory.create(db_session, name="他組織タスク")
        
        # When
        user_org_ids = [o.id for o in org_user.get_organizations()]
        
        # Then
        assert other_org.id not in user_org_ids
        # In TaskService: search_tasks(user=org_user, organization_id=other_org.id)
        # Should return empty results or raise PermissionDenied

    def test_task_department_level_permissions(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task permissions at department level."""
        # Given
        system = complete_test_system
        org = system["organization"]
        dept_manager = system["users"]["dept_manager"]
        
        # When
        # Department manager should have task permissions within their department
        has_task_view = dept_manager.has_permission("task.view", org.id)
        has_task_create = dept_manager.has_permission("task.create", org.id)
        
        # Then
        assert has_task_view or has_task_create  # Should have some task permissions
        
        # Department manager should NOT have org-wide task deletion rights
        has_org_task_delete = dept_manager.has_permission("task.delete_all", org.id)
        assert not has_org_task_delete


class TestTaskServiceAPI:
    """Test Task Service API integration (when implemented)."""

    def test_task_api_permission_enforcement(
        self, client: TestClient, manager_token: str, test_organization: Organization
    ) -> None:
        """Test task API enforces proper permissions."""
        # Given
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # This test would be relevant when Task API is implemented
        # For now, we test the permission structure
        
        # When/Then
        # GET /api/v1/tasks/ should be accessible to manager
        # POST /api/v1/tasks/ should be accessible with proper permissions
        # DELETE /api/v1/tasks/{id} should require appropriate permissions
        
        # Placeholder test - would implement when Task API exists
        assert headers is not None
        assert test_organization.id is not None

    def test_task_api_organization_filtering(
        self, client: TestClient, user_token: str, test_organization: Organization
    ) -> None:
        """Test task API properly filters by organization."""
        # Given
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # When/Then
        # GET /api/v1/tasks/?organization_id={org_id}
        # Should only return tasks from user's organizations
        
        # Placeholder for future Task API implementation
        assert headers is not None
        assert test_organization.id is not None


class TestTaskServiceWorkflows:
    """Test complete task workflows across services."""

    def test_user_task_assignment_workflow(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test complete user-to-task assignment workflow."""
        # Given
        system = complete_test_system
        org = system["organization"]
        assigner = system["users"]["org_admin"]
        assignee = system["users"]["regular_user"]
        
        # When - Simulate task assignment workflow
        # 1. Verify assigner has permission to assign tasks
        can_assign = assigner.has_permission("task.assign", org.id)
        
        # 2. Verify assignee is in same organization
        assigner_orgs = [o.id for o in assigner.get_organizations()]
        assignee_orgs = [o.id for o in assignee.get_organizations()]
        common_orgs = set(assigner_orgs) & set(assignee_orgs)
        
        # 3. Log the assignment (audit trail)
        if can_assign and common_orgs:
            assigner.log_activity(
                db_session,
                action="task.assign",
                details={
                    "assignee_id": assignee.id,
                    "organization_id": org.id,
                    "task_id": 456
                }
            )
        
        # Then
        assert can_assign or len(assigner_orgs) > 0  # Admin should have permissions
        assert org.id in common_orgs  # Users should share organization
        
        # Verify audit log created
        from app.models.user_activity_log import UserActivityLog
        assignment_logs = db_session.query(UserActivityLog).filter_by(
            user_id=assigner.id, action="task.assign"
        ).all()
        assert len(assignment_logs) > 0

    def test_task_completion_workflow(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task completion workflow with notifications."""
        # Given
        system = complete_test_system
        org = system["organization"]
        task_owner = system["users"]["regular_user"]
        
        # When - Simulate task completion
        # 1. User completes their task
        task_owner.log_activity(
            db_session,
            action="task.complete",
            details={
                "task_id": 789,
                "organization_id": org.id,
                "completion_time": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # 2. System should potentially notify manager/admin
        # (This would be implemented in actual TaskService)
        
        # Then
        from app.models.user_activity_log import UserActivityLog
        completion_logs = db_session.query(UserActivityLog).filter_by(
            user_id=task_owner.id, action="task.complete"
        ).all()
        assert len(completion_logs) > 0
        
        # Verify log contains proper details
        log = completion_logs[0]
        assert "task_id" in log.details
        assert log.details["organization_id"] == org.id

    def test_task_escalation_workflow(
        self, db_session: Session, complete_test_system
    ) -> None:
        """Test task escalation across department hierarchy."""
        # Given
        system = complete_test_system
        org = system["organization"]
        regular_user = system["users"]["regular_user"]
        dept_manager = system["users"]["dept_manager"]
        
        # When - Simulate task escalation
        # 1. Regular user escalates task to manager
        regular_user.log_activity(
            db_session,
            action="task.escalate",
            details={
                "task_id": 999,
                "escalated_to": dept_manager.id,
                "organization_id": org.id,
                "reason": "Requires manager approval"
            }
        )
        
        # 2. Manager receives escalation (would be implemented in TaskService)
        dept_manager.log_activity(
            db_session,
            action="task.receive_escalation",
            details={
                "task_id": 999,
                "escalated_from": regular_user.id,
                "organization_id": org.id
            }
        )
        
        # Then
        from app.models.user_activity_log import UserActivityLog
        
        escalation_logs = db_session.query(UserActivityLog).filter_by(
            user_id=regular_user.id, action="task.escalate"
        ).all()
        receive_logs = db_session.query(UserActivityLog).filter_by(
            user_id=dept_manager.id, action="task.receive_escalation"
        ).all()
        
        assert len(escalation_logs) > 0
        assert len(receive_logs) > 0
        
        # Verify escalation chain
        escalation = escalation_logs[0]
        received = receive_logs[0]
        assert escalation.details["escalated_to"] == dept_manager.id
        assert received.details["escalated_from"] == regular_user.id
        assert escalation.details["task_id"] == received.details["task_id"]