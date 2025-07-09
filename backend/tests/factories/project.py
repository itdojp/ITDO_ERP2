"""Project test factories."""

from datetime import date, datetime, timedelta
from typing import Dict, Optional, List, Any

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus, ProjectPriority, ProjectType
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone, MilestoneStatus
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from . import BaseFactory


class ProjectFactory(BaseFactory):
    """Factory for creating test projects."""

    @staticmethod
    def create(
        db: Session,
        organization: Organization,
        owner: User,
        **kwargs: Any,
    ) -> Project:
        """Create a test project."""
        defaults = {
            "code": f"PROJ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": "Test Project",
            "description": "A test project for unit testing",
            "organization_id": organization.id,
            "owner_id": owner.id,
            "manager_id": owner.id,
            "status": ProjectStatus.PLANNING,
            "priority": ProjectPriority.MEDIUM,
            "project_type": ProjectType.INTERNAL,
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=90),
            "budget": 1000000.0,
            "is_template": False,
            "is_public": False,
            "tags": ["test", "development"],
            "settings": {"notifications": True},
        }
        defaults.update(kwargs)

        project = Project(**defaults)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def create_with_department(
        db: Session,
        organization: Organization,
        department: Department,
        owner: User,
        **kwargs: Any,
    ) -> Project:
        """Create a test project with department assignment."""
        kwargs["department_id"] = department.id
        return ProjectFactory.create(db, organization, owner, **kwargs)

    @staticmethod
    def create_project_hierarchy(
        db: Session,
        organization: Organization,
        owner: User,
        levels: int = 3,
        children_per_level: int = 2,
    ) -> Dict[str, Any]:
        """Create a project hierarchy."""
        root_project = ProjectFactory.create(
            db, organization, owner, name="Root Project", code="ROOT-PROJ"
        )

        def create_children(parent: Project, level: int) -> List[Project]:
            if level >= levels:
                return []

            children = []
            for i in range(children_per_level):
                child = ProjectFactory.create(
                    db,
                    organization,
                    owner,
                    name=f"Level {level} Project {i+1}",
                    code=f"L{level}-P{i+1}",
                    parent_id=parent.id,
                )
                children.append(child)
                # Recursively create children
                child.children = create_children(child, level + 1)

            return children

        root_project.children = create_children(root_project, 1)

        return {
            "root": root_project,
            "total_projects": 1 + sum(children_per_level**i for i in range(1, levels)),
        }

    @staticmethod
    def create_with_members(
        db: Session,
        organization: Organization,
        owner: User,
        members: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Project:
        """Create a project with members."""
        project = ProjectFactory.create(db, organization, owner, **kwargs)

        for member_data in members:
            member = ProjectMember(
                project_id=project.id,
                user_id=member_data["user_id"],
                role=member_data.get("role", "member"),
                permissions=member_data.get("permissions", []),
                joined_at=datetime.utcnow(),
                is_active=member_data.get("is_active", True),
            )
            db.add(member)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def create_with_milestones(
        db: Session,
        organization: Organization,
        owner: User,
        milestone_count: int = 3,
        **kwargs: Any,
    ) -> Project:
        """Create a project with milestones."""
        project = ProjectFactory.create(db, organization, owner, **kwargs)

        for i in range(milestone_count):
            milestone = ProjectMilestone(
                project_id=project.id,
                name=f"Milestone {i+1}",
                description=f"Description for milestone {i+1}",
                due_date=project.start_date + timedelta(days=30 * (i + 1)),
                status=MilestoneStatus.PENDING if i > 0 else MilestoneStatus.IN_PROGRESS,
                completion_percentage=0 if i > 0 else 25,
                deliverables=[f"Deliverable {j+1}" for j in range(3)],
                created_by=owner.id,
                assigned_to=owner.id,
            )
            db.add(milestone)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def create_project_set(
        db: Session,
        organization: Organization,
        owner: User,
        department: Optional[Department] = None,
    ) -> Dict[str, Project]:
        """Create a set of projects in different states."""
        projects = {}

        # Planning project
        projects["planning"] = ProjectFactory.create(
            db,
            organization,
            owner,
            name="Planning Project",
            code="PLAN-001",
            status=ProjectStatus.PLANNING,
            department_id=department.id if department else None,
        )

        # Active project with milestones
        projects["active"] = ProjectFactory.create_with_milestones(
            db,
            organization,
            owner,
            name="Active Project",
            code="ACT-001",
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.HIGH,
            department_id=department.id if department else None,
        )

        # On hold project
        projects["on_hold"] = ProjectFactory.create(
            db,
            organization,
            owner,
            name="On Hold Project",
            code="HOLD-001",
            status=ProjectStatus.ON_HOLD,
            priority=ProjectPriority.LOW,
            department_id=department.id if department else None,
        )

        # Completed project
        projects["completed"] = ProjectFactory.create(
            db,
            organization,
            owner,
            name="Completed Project",
            code="COMP-001",
            status=ProjectStatus.COMPLETED,
            end_date=date.today() - timedelta(days=30),
            completion_date=date.today() - timedelta(days=30),
            actual_cost=950000.0,
            department_id=department.id if department else None,
        )

        # Cancelled project
        projects["cancelled"] = ProjectFactory.create(
            db,
            organization,
            owner,
            name="Cancelled Project",
            code="CANC-001",
            status=ProjectStatus.CANCELLED,
            cancellation_reason="Budget constraints",
            department_id=department.id if department else None,
        )

        # Archived project
        projects["archived"] = ProjectFactory.create(
            db,
            organization,
            owner,
            name="Archived Project",
            code="ARCH-001",
            status=ProjectStatus.ARCHIVED,
            is_archived=True,
            archived_at=datetime.utcnow(),
            archived_by=owner.id,
            department_id=department.id if department else None,
        )

        return projects

    @staticmethod
    def create_cross_department_project(
        db: Session,
        organization: Organization,
        primary_department: Department,
        participating_departments: List[Department],
        owner: User,
        **kwargs: Any,
    ) -> Project:
        """Create a project spanning multiple departments."""
        project = ProjectFactory.create_with_department(
            db,
            organization,
            primary_department,
            owner,
            name="Cross-Department Project",
            code="CROSS-001",
            **kwargs,
        )

        # Add metadata for participating departments
        project.settings["participating_departments"] = [
            dept.id for dept in participating_departments
        ]
        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def create_template_project(
        db: Session,
        organization: Organization,
        owner: User,
        **kwargs: Any,
    ) -> Project:
        """Create a template project."""
        defaults = {
            "name": "Project Template",
            "code": "TMPL-001",
            "is_template": True,
            "template_config": {
                "phases": ["Planning", "Development", "Testing", "Deployment"],
                "default_duration": 90,
                "required_roles": ["manager", "developer", "tester"],
            },
        }
        defaults.update(kwargs)

        return ProjectFactory.create(db, organization, owner, **defaults)


class ProjectMemberFactory(BaseFactory):
    """Factory for creating project members."""

    @staticmethod
    def add_member(
        db: Session,
        project: Project,
        user: User,
        role: str = "member",
        permissions: Optional[List[str]] = None,
    ) -> ProjectMember:
        """Add a member to a project."""
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=role,
            permissions=permissions or [],
            joined_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def create_project_team(
        db: Session,
        project: Project,
        users: Dict[str, User],
    ) -> List[ProjectMember]:
        """Create a complete project team."""
        members = []

        # Add owner as admin
        if "owner" in users:
            members.append(
                ProjectMemberFactory.add_member(
                    db,
                    project,
                    users["owner"],
                    role="admin",
                    permissions=["project.manage", "members.manage", "settings.manage"],
                )
            )

        # Add manager
        if "manager" in users:
            members.append(
                ProjectMemberFactory.add_member(
                    db,
                    project,
                    users["manager"],
                    role="manager",
                    permissions=["project.update", "members.add", "tasks.manage"],
                )
            )

        # Add developers
        for key, user in users.items():
            if key.startswith("developer"):
                members.append(
                    ProjectMemberFactory.add_member(
                        db,
                        project,
                        user,
                        role="developer",
                        permissions=["project.read", "tasks.update"],
                    )
                )

        # Add viewers
        for key, user in users.items():
            if key.startswith("viewer"):
                members.append(
                    ProjectMemberFactory.add_member(
                        db, project, user, role="viewer", permissions=["project.read"]
                    )
                )

        return members


class ProjectMilestoneFactory(BaseFactory):
    """Factory for creating project milestones."""

    @staticmethod
    def create(
        db: Session,
        project: Project,
        created_by: int,
        **kwargs: Any,
    ) -> ProjectMilestone:
        """Create a project milestone."""
        defaults = {
            "name": "Test Milestone",
            "description": "A test milestone",
            "due_date": project.start_date + timedelta(days=30),
            "status": MilestoneStatus.PENDING,
            "completion_percentage": 0,
            "deliverables": ["Deliverable 1", "Deliverable 2"],
            "created_by": created_by,
        }
        defaults.update(kwargs)

        milestone = ProjectMilestone(project_id=project.id, **defaults)
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def create_milestone_chain(
        db: Session,
        project: Project,
        created_by: int,
        count: int = 4,
    ) -> List[ProjectMilestone]:
        """Create a chain of dependent milestones."""
        milestones = []
        statuses = [
            MilestoneStatus.COMPLETED,
            MilestoneStatus.IN_PROGRESS,
            MilestoneStatus.PENDING,
            MilestoneStatus.PENDING,
        ]

        for i in range(min(count, len(statuses))):
            milestone = ProjectMilestoneFactory.create(
                db,
                project,
                created_by,
                name=f"Phase {i+1}",
                due_date=project.start_date + timedelta(days=30 * (i + 1)),
                status=statuses[i],
                completion_percentage=100 if i == 0 else (50 if i == 1 else 0),
                dependencies=[milestones[-1].id] if milestones else [],
            )
            milestones.append(milestone)

        return milestones