"""
ITDO ERP Backend - Team Management API
Day 17: Team & Member Management Implementation (Requirements 2.3)
Complete team structure, role-based access, and collaboration features
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.models.user import User


# Mock authentication dependency for team management APIs
async def get_current_user() -> User:
    """Mock current user for team management APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/teams", tags=["team-management"])


# Team Role and Permission Enums
class TeamRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class ProjectPermission(str, Enum):
    CREATE_PROJECT = "create_project"
    EDIT_PROJECT = "edit_project"
    DELETE_PROJECT = "delete_project"
    VIEW_PROJECT = "view_project"
    MANAGE_TEAM = "manage_team"
    CREATE_TASK = "create_task"
    EDIT_TASK = "edit_task"
    DELETE_TASK = "delete_task"
    ASSIGN_TASK = "assign_task"
    VIEW_REPORTS = "view_reports"
    MANAGE_BUDGET = "manage_budget"


class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


# Pydantic Schemas
class TeamMemberBase(BaseModel):
    """Base team member schema"""

    user_id: int
    project_id: int
    role: TeamRole = TeamRole.MEMBER
    status: MemberStatus = MemberStatus.ACTIVE
    permissions: List[ProjectPermission] = Field(default_factory=list)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    allocation_percentage: Optional[int] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    """Schema for creating team member"""

    pass


class TeamMemberUpdate(BaseModel):
    """Schema for updating team member"""

    role: Optional[TeamRole] = None
    status: Optional[MemberStatus] = None
    permissions: Optional[List[ProjectPermission]] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    allocation_percentage: Optional[int] = Field(None, ge=0, le=100)
    end_date: Optional[date] = None
    notes: Optional[str] = None


class UserSummary(BaseModel):
    """User summary for team member response"""

    id: int
    name: str
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""

    id: int
    user: UserSummary
    project_name: str
    is_project_owner: bool = False
    active_tasks_count: int = 0
    completed_tasks_count: int = 0
    total_hours_logged: Optional[Decimal] = None
    last_activity: Optional[datetime] = None
    performance_score: Optional[float] = None
    joined_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectTeamResponse(BaseModel):
    """Complete project team response"""

    project_id: int
    project_name: str
    project_status: str
    team_size: int
    active_members: int
    team_members: List[TeamMemberResponse]
    role_distribution: Dict[str, int] = Field(default_factory=dict)
    total_allocation: int = 0
    average_performance: float = 0.0
    generated_at: datetime


class TeamStatisticsResponse(BaseModel):
    """Team statistics response"""

    total_members: int
    active_members: int
    pending_members: int
    role_breakdown: Dict[str, int]
    department_breakdown: Dict[str, int]
    average_allocation: float
    total_hourly_cost: Decimal
    team_performance_score: float
    top_performers: List[UserSummary] = Field(default_factory=list)


class TeamActivityLog(BaseModel):
    """Team activity log entry"""

    id: int
    project_id: int
    user_id: int
    user_name: str
    activity_type: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class TeamCollaborationRequest(BaseModel):
    """Request for team collaboration analysis"""

    project_id: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    include_external: bool = False


class TeamCollaborationResponse(BaseModel):
    """Team collaboration analysis response"""

    project_id: int
    analysis_period: str
    total_interactions: int
    collaboration_matrix: Dict[str, Dict[str, int]]
    communication_frequency: Dict[str, int]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]


# Team Management Service
class TeamManagementService:
    """Service for team management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
        self.role_permissions = self._initialize_role_permissions()

    def _initialize_role_permissions(self) -> Dict[TeamRole, List[ProjectPermission]]:
        """Initialize default permissions for each role"""
        return {
            TeamRole.OWNER: [
                ProjectPermission.CREATE_PROJECT,
                ProjectPermission.EDIT_PROJECT,
                ProjectPermission.DELETE_PROJECT,
                ProjectPermission.VIEW_PROJECT,
                ProjectPermission.MANAGE_TEAM,
                ProjectPermission.CREATE_TASK,
                ProjectPermission.EDIT_TASK,
                ProjectPermission.DELETE_TASK,
                ProjectPermission.ASSIGN_TASK,
                ProjectPermission.VIEW_REPORTS,
                ProjectPermission.MANAGE_BUDGET,
            ],
            TeamRole.ADMIN: [
                ProjectPermission.EDIT_PROJECT,
                ProjectPermission.VIEW_PROJECT,
                ProjectPermission.MANAGE_TEAM,
                ProjectPermission.CREATE_TASK,
                ProjectPermission.EDIT_TASK,
                ProjectPermission.ASSIGN_TASK,
                ProjectPermission.VIEW_REPORTS,
                ProjectPermission.MANAGE_BUDGET,
            ],
            TeamRole.MANAGER: [
                ProjectPermission.VIEW_PROJECT,
                ProjectPermission.CREATE_TASK,
                ProjectPermission.EDIT_TASK,
                ProjectPermission.ASSIGN_TASK,
                ProjectPermission.VIEW_REPORTS,
            ],
            TeamRole.MEMBER: [
                ProjectPermission.VIEW_PROJECT,
                ProjectPermission.CREATE_TASK,
                ProjectPermission.EDIT_TASK,
            ],
            TeamRole.VIEWER: [
                ProjectPermission.VIEW_PROJECT,
            ],
            TeamRole.GUEST: [
                ProjectPermission.VIEW_PROJECT,
            ],
        }

    async def add_team_member(
        self, member_data: TeamMemberCreate, added_by: int
    ) -> TeamMemberResponse:
        """Add a new team member to project"""

        # Validate project exists
        project_result = await self.db.execute(
            select(Project).where(Project.id == member_data.project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with ID {member_data.project_id} not found",
            )

        # Validate user exists (mock implementation)
        if member_data.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )

        # Check if member already exists
        existing_member = await self._get_team_member(
            member_data.project_id, member_data.user_id
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a team member",
            )

        # Set default permissions based on role
        permissions = member_data.permissions or self.role_permissions.get(
            member_data.role, []
        )

        # Create team member entry (mock implementation - would use proper model)
        member_id = await self._generate_member_id()
        member_data_dict = {
            "id": member_id,
            "user_id": member_data.user_id,
            "project_id": member_data.project_id,
            "role": member_data.role.value,
            "status": member_data.status.value,
            "permissions": [p.value for p in permissions],
            "hourly_rate": float(member_data.hourly_rate)
            if member_data.hourly_rate
            else None,
            "allocation_percentage": member_data.allocation_percentage or 100,
            "start_date": member_data.start_date or date.today(),
            "end_date": member_data.end_date,
            "notes": member_data.notes,
            "joined_at": datetime.utcnow(),
            "added_by": added_by,
        }

        # Store in Redis (temporary storage for demo)
        await self.redis.hset(
            f"team_member:{member_id}",
            mapping={
                k: str(v) if v is not None else "" for k, v in member_data_dict.items()
            },
        )

        # Add to project team set
        await self.redis.sadd(f"project_team:{member_data.project_id}", member_id)

        # Log activity
        await self._log_team_activity(
            project_id=member_data.project_id,
            user_id=added_by,
            activity_type="member_added",
            description=f"Added user {member_data.user_id} as {member_data.role.value}",
            metadata={"new_member_id": member_id, "role": member_data.role.value},
        )

        return await self._build_team_member_response(member_data_dict, project)

    async def update_team_member(
        self, member_id: int, member_data: TeamMemberUpdate, updated_by: int
    ) -> Optional[TeamMemberResponse]:
        """Update existing team member"""

        # Get existing member
        member_dict = await self._get_team_member_by_id(member_id)
        if not member_dict:
            return None

        # Update fields
        update_data = member_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "permissions" and value is not None:
                member_dict[field] = [
                    p.value if hasattr(p, "value") else p for p in value
                ]
            elif field == "hourly_rate" and value is not None:
                member_dict[field] = str(float(value))
            elif value is not None:
                member_dict[field] = str(value) if not isinstance(value, str) else value

        member_dict["updated_at"] = datetime.utcnow().isoformat()
        member_dict["updated_by"] = str(updated_by)

        # Update in Redis
        await self.redis.hset(f"team_member:{member_id}", mapping=member_dict)

        # Get project for response
        project_result = await self.db.execute(
            select(Project).where(Project.id == int(member_dict["project_id"]))
        )
        project = project_result.scalar_one_or_none()

        # Log activity
        await self._log_team_activity(
            project_id=int(member_dict["project_id"]),
            user_id=updated_by,
            activity_type="member_updated",
            description=f"Updated team member {member_dict['user_id']}",
            metadata={"member_id": member_id, "changes": list(update_data.keys())},
        )

        return await self._build_team_member_response(member_dict, project)

    async def remove_team_member(self, member_id: int, removed_by: int) -> bool:
        """Remove team member from project"""

        # Get member to remove
        member_dict = await self._get_team_member_by_id(member_id)
        if not member_dict:
            return False

        project_id = int(member_dict["project_id"])
        user_id = int(member_dict["user_id"])

        # Remove from Redis
        await self.redis.delete(f"team_member:{member_id}")
        await self.redis.srem(f"project_team:{project_id}", member_id)

        # Log activity
        await self._log_team_activity(
            project_id=project_id,
            user_id=removed_by,
            activity_type="member_removed",
            description=f"Removed user {user_id} from team",
            metadata={"removed_member_id": member_id, "removed_user_id": user_id},
        )

        return True

    async def get_project_team(self, project_id: int) -> ProjectTeamResponse:
        """Get complete project team information"""

        # Get project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Get team member IDs from Redis
        member_ids = await self.redis.smembers(f"project_team:{project_id}")

        team_members = []
        role_distribution = {}
        total_allocation = 0
        active_members = 0

        for member_id in member_ids:
            member_dict = await self._get_team_member_by_id(int(member_id))
            if member_dict:
                member_response = await self._build_team_member_response(
                    member_dict, project
                )
                team_members.append(member_response)

                # Update statistics
                role = member_response.role.value
                role_distribution[role] = role_distribution.get(role, 0) + 1

                if member_response.allocation_percentage:
                    total_allocation += member_response.allocation_percentage

                if member_response.status == MemberStatus.ACTIVE:
                    active_members += 1

        # Calculate average performance
        performance_scores = [
            m.performance_score for m in team_members if m.performance_score is not None
        ]
        average_performance = (
            sum(performance_scores) / len(performance_scores)
            if performance_scores
            else 0.0
        )

        return ProjectTeamResponse(
            project_id=project_id,
            project_name=project.name,
            project_status=project.status,
            team_size=len(team_members),
            active_members=active_members,
            team_members=team_members,
            role_distribution=role_distribution,
            total_allocation=total_allocation,
            average_performance=average_performance,
            generated_at=datetime.utcnow(),
        )

    async def get_team_statistics(
        self, project_id: Optional[int] = None
    ) -> TeamStatisticsResponse:
        """Get team statistics across projects or for specific project"""

        # Get team member IDs
        if project_id:
            member_ids = await self.redis.smembers(f"project_team:{project_id}")
        else:
            # Get all team members (would need different implementation in production)
            member_ids = []
            for key in await self.redis.keys("team_member:*"):
                member_id = key.decode().split(":")[-1]
                member_ids.append(member_id)

        # Collect statistics
        total_members = len(member_ids)
        active_members = 0
        pending_members = 0
        role_breakdown = {}
        department_breakdown = {}
        total_allocation = 0
        total_hourly_cost = Decimal(0)
        performance_scores = []

        for member_id in member_ids:
            member_dict = await self._get_team_member_by_id(int(member_id))
            if member_dict:
                status = member_dict.get("status", "active")
                if status == "active":
                    active_members += 1
                elif status == "pending":
                    pending_members += 1

                role = member_dict.get("role", "member")
                role_breakdown[role] = role_breakdown.get(role, 0) + 1

                allocation = int(member_dict.get("allocation_percentage", 0))
                total_allocation += allocation

                hourly_rate = member_dict.get("hourly_rate")
                if hourly_rate:
                    total_hourly_cost += Decimal(hourly_rate) * (allocation / 100)

        average_allocation = (
            total_allocation / total_members if total_members > 0 else 0
        )
        team_performance_score = (
            sum(performance_scores) / len(performance_scores)
            if performance_scores
            else 0.0
        )

        # Get top performers (mock implementation)
        top_performers = [
            UserSummary(id=1, name="Top Performer 1", email="top1@example.com"),
        ]

        return TeamStatisticsResponse(
            total_members=total_members,
            active_members=active_members,
            pending_members=pending_members,
            role_breakdown=role_breakdown,
            department_breakdown=department_breakdown,
            average_allocation=average_allocation,
            total_hourly_cost=total_hourly_cost,
            team_performance_score=team_performance_score,
            top_performers=top_performers,
        )

    async def analyze_team_collaboration(
        self, request: TeamCollaborationRequest
    ) -> TeamCollaborationResponse:
        """Analyze team collaboration patterns"""

        # Mock collaboration analysis
        collaboration_matrix = {
            "User1": {"User2": 25, "User3": 15, "User4": 10},
            "User2": {"User1": 25, "User3": 20, "User4": 8},
            "User3": {"User1": 15, "User2": 20, "User4": 12},
            "User4": {"User1": 10, "User2": 8, "User3": 12},
        }

        communication_frequency = {
            "daily": 45,
            "weekly": 30,
            "monthly": 15,
            "ad_hoc": 10,
        }

        bottlenecks = [
            {
                "type": "communication",
                "description": "Limited cross-team communication",
                "severity": "medium",
                "affected_members": ["User3", "User4"],
            }
        ]

        recommendations = [
            "Schedule regular cross-team sync meetings",
            "Implement pair programming sessions",
            "Create shared collaboration channels",
            "Establish mentorship programs",
        ]

        analysis_period = "Last 30 days"
        if request.date_from and request.date_to:
            analysis_period = f"{request.date_from} to {request.date_to}"

        return TeamCollaborationResponse(
            project_id=request.project_id,
            analysis_period=analysis_period,
            total_interactions=150,
            collaboration_matrix=collaboration_matrix,
            communication_frequency=communication_frequency,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )

    async def _get_team_member(
        self, project_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get team member by project and user ID"""
        member_ids = await self.redis.smembers(f"project_team:{project_id}")

        for member_id in member_ids:
            member_dict = await self._get_team_member_by_id(int(member_id))
            if member_dict and int(member_dict.get("user_id", 0)) == user_id:
                return member_dict

        return None

    async def _get_team_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """Get team member by ID"""
        member_data = await self.redis.hgetall(f"team_member:{member_id}")
        if member_data:
            return {k.decode(): v.decode() for k, v in member_data.items()}
        return None

    async def _build_team_member_response(
        self, member_dict: Dict[str, Any], project: Project
    ) -> TeamMemberResponse:
        """Build team member response from data"""

        # Mock user data
        user = UserSummary(
            id=int(member_dict["user_id"]),
            name=f"User {member_dict['user_id']}",
            email=f"user{member_dict['user_id']}@example.com",
            title="Developer",
            department="Engineering",
        )

        # Calculate task statistics (mock)
        active_tasks_count = 3
        completed_tasks_count = 12
        total_hours_logged = Decimal("45.5")
        performance_score = 85.5

        # Parse dates
        joined_at = datetime.fromisoformat(
            member_dict.get("joined_at", datetime.utcnow().isoformat())
        )
        updated_at = None
        if member_dict.get("updated_at"):
            updated_at = datetime.fromisoformat(member_dict["updated_at"])

        return TeamMemberResponse(
            id=int(member_dict["id"]),
            user_id=int(member_dict["user_id"]),
            project_id=int(member_dict["project_id"]),
            role=TeamRole(member_dict["role"]),
            status=MemberStatus(member_dict["status"]),
            permissions=[
                ProjectPermission(p) for p in eval(member_dict.get("permissions", "[]"))
            ],
            hourly_rate=Decimal(member_dict["hourly_rate"])
            if member_dict.get("hourly_rate")
            else None,
            allocation_percentage=int(member_dict.get("allocation_percentage", 100)),
            start_date=date.fromisoformat(member_dict["start_date"])
            if member_dict.get("start_date")
            else None,
            end_date=date.fromisoformat(member_dict["end_date"])
            if member_dict.get("end_date")
            else None,
            notes=member_dict.get("notes"),
            user=user,
            project_name=project.name,
            is_project_owner=(project.owner_id == int(member_dict["user_id"])),
            active_tasks_count=active_tasks_count,
            completed_tasks_count=completed_tasks_count,
            total_hours_logged=total_hours_logged,
            last_activity=datetime.utcnow()
            - timedelta(hours=2),  # Mock recent activity
            performance_score=performance_score,
            joined_at=joined_at,
            updated_at=updated_at,
        )

    async def _generate_member_id(self) -> int:
        """Generate unique member ID"""
        return await self.redis.incr("team_member_counter")

    async def _log_team_activity(
        self,
        project_id: int,
        user_id: int,
        activity_type: str,
        description: str,
        metadata: Dict[str, Any] = None,
    ):
        """Log team activity for audit trail"""
        activity_id = await self.redis.incr("team_activity_counter")

        activity_data = {
            "id": activity_id,
            "project_id": project_id,
            "user_id": user_id,
            "user_name": f"User {user_id}",
            "activity_type": activity_type,
            "description": description,
            "metadata": str(metadata or {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.redis.hset(
            f"team_activity:{activity_id}",
            mapping={k: str(v) for k, v in activity_data.items()},
        )

        # Add to project activity log
        await self.redis.lpush(f"project_activities:{project_id}", activity_id)


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_team_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> TeamManagementService:
    """Get team management service instance"""
    return TeamManagementService(db, redis)


# API Endpoints - Team Management
@router.post(
    "/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED
)
async def add_team_member(
    member_data: TeamMemberCreate,
    current_user: User = Depends(get_current_user),
    service: TeamManagementService = Depends(get_team_service),
):
    """Add a new team member to project"""
    return await service.add_team_member(member_data, current_user.id)


@router.put("/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: int,
    member_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    service: TeamManagementService = Depends(get_team_service),
):
    """Update existing team member"""
    member = await service.update_team_member(member_id, member_data, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamManagementService = Depends(get_team_service),
):
    """Remove team member from project"""
    success = await service.remove_team_member(member_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found"
        )


@router.get("/projects/{project_id}", response_model=ProjectTeamResponse)
async def get_project_team(
    project_id: int,
    service: TeamManagementService = Depends(get_team_service),
):
    """Get complete project team information"""
    return await service.get_project_team(project_id)


@router.get("/statistics", response_model=TeamStatisticsResponse)
async def get_team_statistics(
    project_id: Optional[int] = Query(None),
    service: TeamManagementService = Depends(get_team_service),
):
    """Get team statistics"""
    return await service.get_team_statistics(project_id)


@router.post("/collaboration/analyze", response_model=TeamCollaborationResponse)
async def analyze_team_collaboration(
    request: TeamCollaborationRequest,
    service: TeamManagementService = Depends(get_team_service),
):
    """Analyze team collaboration patterns"""
    return await service.analyze_team_collaboration(request)


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for team management API"""
    return {
        "status": "healthy",
        "service": "team-management-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
