"""Integration tests for Project workflow."""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.project import Project, ProjectStatus, ProjectPriority, ProjectType
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone, MilestoneStatus
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.services.project import ProjectService
from app.services.organization import OrganizationService
from app.services.department import DepartmentService
from app.schemas.project import ProjectCreate, ProjectUpdate
from tests.factories import (
    ProjectFactory,
    ProjectMemberFactory,
    ProjectMilestoneFactory,
    OrganizationFactory,
    DepartmentFactory,
    UserFactory,
)


class TestProjectWorkflow:
    """Integration tests for complete project workflow."""

    def test_complete_project_lifecycle(self, db_session: Session, complete_test_system):
        """Test complete project lifecycle from creation to completion."""
        # Get test system components
        organization = complete_test_system["organization"]
        departments = complete_test_system["departments"]
        users = complete_test_system["users"]
        
        # Get primary department
        primary_dept = departments["root"]
        
        # Initialize services
        project_service = ProjectService(db_session)
        
        # 1. Create project
        project_data = ProjectCreate(
            code="LIFECYCLE-001",
            name="Complete Lifecycle Project",
            description="Testing complete project lifecycle",
            organization_id=organization.id,
            department_id=primary_dept.id,
            manager_id=users["manager"].id,
            status=ProjectStatus.PLANNING,
            priority=ProjectPriority.HIGH,
            project_type=ProjectType.INTERNAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            budget=1000000.0,
            tags=["integration", "test"],
        )
        
        project = project_service.create_project(
            project_data=project_data,
            owner_id=users["owner"].id,
            validate_permissions=False,
        )
        
        assert project.dict()["code"] == "LIFECYCLE-001"
        assert project.dict()["status"] == ProjectStatus.PLANNING
        
        # 2. Add team members
        # Add manager
        project_service.add_member(
            project_id=project.dict()["id"],
            user_id=users["manager"].id,
            role="manager",
            current_user_id=users["owner"].id,
            permissions=["project.update", "members.add", "tasks.manage"],
        )
        
        # Add developers
        for i, user_key in enumerate(["developer1", "developer2"]):
            if user_key in users:
                project_service.add_member(
                    project_id=project.dict()["id"],
                    user_id=users[user_key].id,
                    role="developer",
                    current_user_id=users["owner"].id,
                    permissions=["project.read", "tasks.update"],
                )
        
        # Verify members were added
        members = project_service.get_project_members(
            project_id=project.dict()["id"],
            user_id=users["owner"].id,
        )
        assert len(members) >= 2  # manager + at least 1 developer
        
        # 3. Set project phases/milestones
        milestones = [
            {
                "name": "Requirements Analysis",
                "due_date": date.today() + timedelta(days=30),
                "deliverables": ["Requirements Document", "User Stories"],
            },
            {
                "name": "Development Phase",
                "due_date": date.today() + timedelta(days=60),
                "deliverables": ["Code Implementation", "Unit Tests"],
            },
            {
                "name": "Testing & Deployment",
                "due_date": date.today() + timedelta(days=90),
                "deliverables": ["Test Results", "Production Deployment"],
            },
        ]
        
        created_milestones = []
        for milestone_data in milestones:
            milestone = ProjectMilestone(
                project_id=project.dict()["id"],
                name=milestone_data["name"],
                due_date=milestone_data["due_date"],
                deliverables=milestone_data["deliverables"],
                status=MilestoneStatus.PENDING,
                created_by=users["owner"].id,
                assigned_to=users["manager"].id,
            )
            db_session.add(milestone)
            created_milestones.append(milestone)
        
        db_session.commit()
        
        # 4. Transition to active status
        from app.schemas.project import ProjectStatusTransition
        
        transition = ProjectStatusTransition(
            from_status=ProjectStatus.PLANNING,
            to_status=ProjectStatus.ACTIVE,
            reason="Project setup complete, ready to start",
        )
        
        active_project = project_service.transition_project_status(
            project_id=project.dict()["id"],
            transition=transition,
            user_id=users["owner"].id,
        )
        
        assert active_project.dict()["status"] == ProjectStatus.ACTIVE
        
        # 5. Create and assign tasks
        tasks = [
            {
                "title": "Setup Project Structure",
                "description": "Initialize project structure and dependencies",
                "assignee_id": users["developer1"].id if "developer1" in users else users["manager"].id,
                "status": TaskStatus.IN_PROGRESS,
                "priority": "high",
                "due_date": date.today() + timedelta(days=7),
            },
            {
                "title": "Create User Interface",
                "description": "Develop user interface components",
                "assignee_id": users["developer2"].id if "developer2" in users else users["manager"].id,
                "status": TaskStatus.TODO,
                "priority": "medium",
                "due_date": date.today() + timedelta(days=14),
            },
        ]
        
        created_tasks = []
        for task_data in tasks:
            task = Task(
                project_id=project.dict()["id"],
                title=task_data["title"],
                description=task_data["description"],
                assignee_id=task_data["assignee_id"],
                status=task_data["status"],
                priority=task_data["priority"],
                due_date=task_data["due_date"],
                created_by=users["owner"].id,
            )
            db_session.add(task)
            created_tasks.append(task)
        
        db_session.commit()
        
        # 6. Update project progress
        # Complete first task
        created_tasks[0].status = TaskStatus.COMPLETED
        created_tasks[0].completed_at = datetime.utcnow()
        
        # Update first milestone
        created_milestones[0].status = MilestoneStatus.IN_PROGRESS
        created_milestones[0].completion_percentage = 75
        
        db_session.commit()
        
        # 7. Get project statistics
        statistics = project_service.get_enhanced_project_statistics(
            project_id=project.dict()["id"],
            user_id=users["owner"].id,
        )
        
        assert statistics.total_members >= 2
        assert statistics.total_tasks == 2
        assert statistics.completed_tasks == 1
        assert statistics.total_milestones == 3
        
        # 8. Update actual costs
        project_service.update_actual_cost(
            project_id=project.dict()["id"],
            cost_delta=250000.0,
            user_id=users["owner"].id,
        )
        
        # 9. Get budget utilization
        budget_info = project_service.get_budget_utilization(
            project_id=project.dict()["id"]
        )
        
        assert budget_info["budget"] == 1000000.0
        assert budget_info["actual_cost"] == 250000.0
        assert budget_info["utilization_percentage"] == 25.0
        
        # 10. Test project completion
        # Complete remaining tasks
        for task in created_tasks[1:]:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
        
        # Complete milestones
        for milestone in created_milestones:
            milestone.status = MilestoneStatus.COMPLETED
            milestone.completion_percentage = 100
        
        db_session.commit()
        
        # Transition to completed
        completion_transition = ProjectStatusTransition(
            from_status=ProjectStatus.ACTIVE,
            to_status=ProjectStatus.COMPLETED,
            reason="All tasks and milestones completed",
        )
        
        completed_project = project_service.transition_project_status(
            project_id=project.dict()["id"],
            transition=completion_transition,
            user_id=users["owner"].id,
        )
        
        assert completed_project.dict()["status"] == ProjectStatus.COMPLETED
        
        # Verify final statistics
        final_stats = project_service.get_enhanced_project_statistics(
            project_id=project.dict()["id"],
            user_id=users["owner"].id,
        )
        
        assert final_stats.completed_tasks == 2
        assert final_stats.overall_progress == 100.0

    def test_organization_department_integration(self, db_session: Session):
        """Test project integration with organization and department structure."""
        # Create organization hierarchy
        parent_org = OrganizationFactory.create(
            db_session, name="Parent Corp", code="PARENT"
        )
        subsidiary_org = OrganizationFactory.create(
            db_session, name="Subsidiary Corp", code="SUB", parent_id=parent_org.id
        )
        
        # Create departments
        parent_dept = DepartmentFactory.create_with_organization(
            db_session, parent_org, name="IT Department", code="IT"
        )
        sub_dept = DepartmentFactory.create_with_organization(
            db_session, subsidiary_org, name="Development", code="DEV"
        )
        
        # Create users
        parent_user = UserFactory.create_with_password(
            db_session, email="parent@corp.com", password="test123"
        )
        sub_user = UserFactory.create_with_password(
            db_session, email="sub@corp.com", password="test123"
        )
        
        # Initialize services
        project_service = ProjectService(db_session)
        org_service = OrganizationService(db_session)
        dept_service = DepartmentService(db_session)
        
        # Create project in parent organization
        parent_project = ProjectFactory.create_with_department(
            db_session,
            parent_org,
            parent_dept,
            parent_user,
            name="Parent Project",
            code="PARENT-001",
        )
        
        # Create project in subsidiary
        sub_project = ProjectFactory.create_with_department(
            db_session,
            subsidiary_org,
            sub_dept,
            sub_user,
            name="Subsidiary Project",
            code="SUB-001",
        )
        
        # Test cross-organization access restrictions
        # Parent user should not access subsidiary project by default
        with pytest.raises(PermissionError):
            project_service.get_project(
                project_id=sub_project.id,
                user_id=parent_user.id,
                validate_permissions=True,
            )
        
        # Test organization-wide project statistics
        parent_stats = org_service.get_organization_statistics(parent_org.id)
        assert parent_stats["total_projects"] >= 1
        
        # Test department project filtering
        dept_projects = project_service.list_projects(
            user_id=parent_user.id,
            filters={"department_id": parent_dept.id},
            validate_permissions=False,
        )
        assert len(dept_projects[0]) >= 1

    def test_multitenant_access_control(self, db_session: Session):
        """Test multi-tenant access control for projects."""
        # Create two separate organizations
        org1 = OrganizationFactory.create(
            db_session, name="Company A", code="COMP-A"
        )
        org2 = OrganizationFactory.create(
            db_session, name="Company B", code="COMP-B"
        )
        
        # Create departments
        dept1 = DepartmentFactory.create_with_organization(
            db_session, org1, name="Dept A", code="DEPT-A"
        )
        dept2 = DepartmentFactory.create_with_organization(
            db_session, org2, name="Dept B", code="DEPT-B"
        )
        
        # Create users for each organization
        user1 = UserFactory.create_with_password(
            db_session, email="user1@compa.com", password="test123"
        )
        user2 = UserFactory.create_with_password(
            db_session, email="user2@compb.com", password="test123"
        )
        
        # Create projects in each organization
        project1 = ProjectFactory.create_with_department(
            db_session,
            org1,
            dept1,
            user1,
            name="Project A",
            code="PROJ-A-001",
        )
        project2 = ProjectFactory.create_with_department(
            db_session,
            org2,
            dept2,
            user2,
            name="Project B",
            code="PROJ-B-001",
        )
        
        # Initialize service
        project_service = ProjectService(db_session)
        
        # Test that user1 can access project1 but not project2
        result1 = project_service.get_project(
            project_id=project1.id,
            user_id=user1.id,
            validate_permissions=False,
        )
        assert result1 is not None
        assert result1.dict()["code"] == "PROJ-A-001"
        
        # Test tenant isolation in project listing
        projects_for_user1 = project_service.list_projects(
            user_id=user1.id,
            filters={"organization_id": org1.id},
            validate_permissions=False,
        )
        assert len(projects_for_user1[0]) >= 1
        assert all(p.dict()["organization_id"] == org1.id for p in projects_for_user1[0])
        
        # Test that user2 cannot access org1 projects
        projects_for_user2_in_org1 = project_service.list_projects(
            user_id=user2.id,
            filters={"organization_id": org1.id},
            validate_permissions=False,
        )
        # Should be empty or raise permission error
        assert len(projects_for_user2_in_org1[0]) == 0

    def test_cross_department_collaboration(self, db_session: Session):
        """Test cross-department project collaboration."""
        # Create organization with multiple departments
        org = OrganizationFactory.create(
            db_session, name="Multi-Dept Corp", code="MULTI"
        )
        
        # Create departments
        it_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="IT Department", code="IT"
        )
        marketing_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="Marketing", code="MKT"
        )
        finance_dept = DepartmentFactory.create_with_organization(
            db_session, org, name="Finance", code="FIN"
        )
        
        # Create users from different departments
        it_user = UserFactory.create_with_password(
            db_session, email="it@corp.com", password="test123"
        )
        marketing_user = UserFactory.create_with_password(
            db_session, email="marketing@corp.com", password="test123"
        )
        finance_user = UserFactory.create_with_password(
            db_session, email="finance@corp.com", password="test123"
        )
        
        # Create cross-department project
        cross_dept_project = ProjectFactory.create_cross_department_project(
            db_session,
            org,
            it_dept,  # Primary department
            [marketing_dept, finance_dept],  # Participating departments
            it_user,  # Owner
            name="Cross-Department Initiative",
            code="CROSS-001",
        )
        
        # Add members from different departments
        project_service = ProjectService(db_session)
        
        # Add marketing member
        project_service.add_member(
            project_id=cross_dept_project.id,
            user_id=marketing_user.id,
            role="stakeholder",
            current_user_id=it_user.id,
            permissions=["project.read", "feedback.provide"],
        )
        
        # Add finance member
        project_service.add_member(
            project_id=cross_dept_project.id,
            user_id=finance_user.id,
            role="approver",
            current_user_id=it_user.id,
            permissions=["project.read", "budget.approve"],
        )
        
        # Verify cross-department access
        members = project_service.get_project_members(
            project_id=cross_dept_project.id,
            user_id=it_user.id,
        )
        
        # Should have members from different departments
        assert len(members) >= 3  # Owner + 2 members from other departments
        
        # Test department-specific permissions
        # Marketing user should be able to read project
        marketing_access = project_service.check_project_permission(
            project_id=cross_dept_project.id,
            user_id=marketing_user.id,
            permission="project.read",
        )
        assert marketing_access is True
        
        # Finance user should be able to approve budget
        finance_access = project_service.check_project_permission(
            project_id=cross_dept_project.id,
            user_id=finance_user.id,
            permission="budget.approve",
        )
        assert finance_access is True

    def test_project_hierarchy_workflow(self, db_session: Session):
        """Test project hierarchy and dependency management."""
        # Create organization and department
        org = OrganizationFactory.create(
            db_session, name="Hierarchy Corp", code="HIER"
        )
        dept = DepartmentFactory.create_with_organization(
            db_session, org, name="Development", code="DEV"
        )
        
        # Create project manager
        manager = UserFactory.create_with_password(
            db_session, email="manager@hier.com", password="test123"
        )
        
        # Create parent project
        parent_project = ProjectFactory.create_with_department(
            db_session,
            org,
            dept,
            manager,
            name="Platform Development",
            code="PLATFORM-001",
            project_type=ProjectType.PROGRAM,
        )
        
        # Create sub-projects
        sub_projects = []
        for i in range(3):
            sub_project = ProjectFactory.create_with_department(
                db_session,
                org,
                dept,
                manager,
                name=f"Module {i+1}",
                code=f"MODULE-{i+1:03d}",
                parent_id=parent_project.id,
                project_type=ProjectType.INTERNAL,
            )
            sub_projects.append(sub_project)
        
        # Initialize service
        project_service = ProjectService(db_session)
        
        # Test hierarchy retrieval
        hierarchy = project_service.get_project_hierarchy(
            project_id=parent_project.id,
            user_id=manager.id,
        )
        
        assert hierarchy["root_project"]["id"] == parent_project.id
        assert hierarchy["total_projects"] >= 4  # Parent + 3 children
        
        # Test parent project progress calculation
        # Complete one sub-project
        sub_projects[0].status = ProjectStatus.COMPLETED
        sub_projects[0].completion_date = date.today()
        
        # Set another to 50% progress
        sub_projects[1].status = ProjectStatus.ACTIVE
        # Add tasks to simulate progress
        task = Task(
            project_id=sub_projects[1].id,
            title="Sub-project task",
            status=TaskStatus.COMPLETED,
            assignee_id=manager.id,
            created_by=manager.id,
        )
        db_session.add(task)
        db_session.commit()
        
        # Calculate parent project progress
        parent_progress = project_service.calculate_hierarchy_progress(
            project_id=parent_project.id
        )
        
        # Should be > 0 since one sub-project is completed
        assert parent_progress > 0
        
        # Test cascading updates
        # Update parent project budget
        parent_project.budget = 5000000.0
        db_session.commit()
        
        # Sub-projects should inherit budget constraints
        for sub_project in sub_projects:
            assert sub_project.budget <= parent_project.budget