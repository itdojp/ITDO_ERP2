"""
ITDO ERP Backend - Resource Management API
Day 21: Resource Management Implementation (Requirements 2.3.2)
Complete resource allocation, utilization tracking, and optimization
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User


# Mock authentication dependency
async def get_current_user() -> User:
    """Mock current user for resource management APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/resources", tags=["resource-management"])


# Resource Types and Status Enums
class ResourceType(str, Enum):
    HUMAN = "human"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    FACILITY = "facility"
    MATERIAL = "material"
    BUDGET = "budget"


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    OVERALLOCATED = "overallocated"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class AllocationStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class UtilizationLevel(str, Enum):
    UNDERUTILIZED = "underutilized"  # < 60%
    OPTIMAL = "optimal"  # 60-85%
    OVERUTILIZED = "overutilized"  # > 85%
    CRITICAL = "critical"  # > 100%


# Pydantic Schemas
class ResourceBase(BaseModel):
    """Base resource schema"""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    resource_type: ResourceType
    status: ResourceStatus = ResourceStatus.AVAILABLE
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=200)
    cost_per_hour: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    capacity_hours_per_day: Optional[Decimal] = Field(None, ge=0, le=24)
    max_capacity: Optional[Decimal] = Field(None, ge=0)
    skills: Optional[List[str]] = Field(default_factory=list)
    certifications: Optional[List[str]] = Field(default_factory=list)
    availability_start: Optional[date] = None
    availability_end: Optional[date] = None

    @validator(
        "cost_per_hour",
        "cost_per_unit",
        "capacity_hours_per_day",
        "max_capacity",
        pre=True,
    )
    def validate_decimals(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class ResourceCreate(ResourceBase):
    """Schema for creating a new resource"""

    pass


class ResourceUpdate(BaseModel):
    """Schema for updating an existing resource"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ResourceStatus] = None
    location: Optional[str] = Field(None, max_length=200)
    cost_per_hour: Optional[Decimal] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    capacity_hours_per_day: Optional[Decimal] = Field(None, ge=0, le=24)
    max_capacity: Optional[Decimal] = Field(None, ge=0)
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    availability_start: Optional[date] = None
    availability_end: Optional[date] = None


class ResourceAllocationBase(BaseModel):
    """Base resource allocation schema"""

    resource_id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    allocated_by: int
    allocation_percentage: Decimal = Field(..., ge=0, le=100)
    allocated_hours: Optional[Decimal] = Field(None, ge=0)
    allocation_start: date
    allocation_end: date
    status: AllocationStatus = AllocationStatus.PLANNED
    priority: int = Field(1, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=500)

    @validator("allocation_percentage", "allocated_hours", pre=True)
    def validate_decimals(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class ResourceAllocationCreate(ResourceAllocationBase):
    """Schema for creating resource allocation"""

    pass


class ResourceAllocationUpdate(BaseModel):
    """Schema for updating resource allocation"""

    allocation_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    allocated_hours: Optional[Decimal] = Field(None, ge=0)
    allocation_start: Optional[date] = None
    allocation_end: Optional[date] = None
    status: Optional[AllocationStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=500)


class ResourceUtilizationEntry(BaseModel):
    """Resource utilization entry"""

    resource_id: int
    resource_name: str
    resource_type: str
    total_capacity: Decimal
    allocated_capacity: Decimal
    utilized_capacity: Decimal
    utilization_percentage: float
    utilization_level: UtilizationLevel
    efficiency_score: float
    cost_per_hour: Optional[Decimal] = None
    total_cost: Decimal
    active_allocations: int
    upcoming_allocations: int


class ResourceResponse(ResourceBase):
    """Schema for resource response"""

    id: int
    current_utilization: float = 0.0
    utilization_level: UtilizationLevel = UtilizationLevel.UNDERUTILIZED
    efficiency_score: float = 0.0
    active_allocations_count: int = 0
    total_allocated_hours: Decimal = Decimal("0")
    remaining_capacity: Decimal = Decimal("0")
    cost_this_month: Decimal = Decimal("0")
    next_available_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceAllocationResponse(ResourceAllocationBase):
    """Schema for resource allocation response"""

    id: int
    resource: Dict[str, Any]
    project_name: Optional[str] = None
    task_title: Optional[str] = None
    actual_hours_used: Decimal = Decimal("0")
    efficiency_percentage: float = 0.0
    cost_to_date: Decimal = Decimal("0")
    is_overallocated: bool = False
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


class ResourceCapacityPlanningRequest(BaseModel):
    """Request for resource capacity planning"""

    date_from: date
    date_to: date
    project_ids: Optional[List[int]] = None
    resource_types: Optional[List[ResourceType]] = None
    include_skills_analysis: bool = True
    include_cost_analysis: bool = True


class ResourceCapacityPlanningResponse(BaseModel):
    """Response for resource capacity planning"""

    planning_period: str
    total_capacity_hours: Decimal
    allocated_hours: Decimal
    available_hours: Decimal
    utilization_percentage: float
    capacity_gaps: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]
    cost_analysis: Dict[str, Decimal]
    resource_recommendations: List[str]
    optimized_allocations: List[Dict[str, Any]]


class ResourceOptimizationRequest(BaseModel):
    """Request for resource optimization"""

    project_id: Optional[int] = None
    optimization_goal: str = "efficiency"  # efficiency, cost, time, balance
    constraints: Dict[str, Any] = Field(default_factory=dict)
    include_external_resources: bool = False


class ResourceOptimizationResponse(BaseModel):
    """Response for resource optimization"""

    current_efficiency: float
    optimized_efficiency: float
    improvement_percentage: float
    cost_savings: Decimal
    time_savings: int  # days
    recommended_changes: List[Dict[str, Any]]
    resource_reallocation_plan: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]


# Resource Management Service
class ResourceManagementService:
    """Service for resource management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_resource(
        self, resource_data: ResourceCreate, user_id: int
    ) -> ResourceResponse:
        """Create a new resource"""

        # Check for duplicate resource code
        if resource_data.code:
            existing = await self._check_resource_code_exists(resource_data.code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resource with code '{resource_data.code}' already exists",
                )

        # Generate resource ID and store in Redis (mock implementation)
        resource_id = await self._generate_resource_id()

        resource_dict = {
            "id": resource_id,
            "code": resource_data.code,
            "name": resource_data.name,
            "description": resource_data.description,
            "resource_type": resource_data.resource_type.value,
            "status": resource_data.status.value,
            "organization_id": resource_data.organization_id or 1,
            "department_id": resource_data.department_id,
            "location": resource_data.location,
            "cost_per_hour": str(resource_data.cost_per_hour)
            if resource_data.cost_per_hour
            else None,
            "cost_per_unit": str(resource_data.cost_per_unit)
            if resource_data.cost_per_unit
            else None,
            "capacity_hours_per_day": str(resource_data.capacity_hours_per_day)
            if resource_data.capacity_hours_per_day
            else None,
            "max_capacity": str(resource_data.max_capacity)
            if resource_data.max_capacity
            else None,
            "skills": ",".join(resource_data.skills or []),
            "certifications": ",".join(resource_data.certifications or []),
            "availability_start": resource_data.availability_start.isoformat()
            if resource_data.availability_start
            else None,
            "availability_end": resource_data.availability_end.isoformat()
            if resource_data.availability_end
            else None,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store resource in Redis
        await self.redis.hset(
            f"resource:{resource_id}",
            mapping={
                k: str(v) if v is not None else "" for k, v in resource_dict.items()
            },
        )

        # Add to resource index
        await self.redis.sadd("resources:all", resource_id)
        await self.redis.sadd(
            f"resources:type:{resource_data.resource_type.value}", resource_id
        )

        # Initialize resource metrics
        await self._initialize_resource_metrics(resource_id)

        return await self._build_resource_response(resource_dict)

    async def get_resource(self, resource_id: int) -> Optional[ResourceResponse]:
        """Get resource by ID"""

        resource_dict = await self._get_resource_by_id(resource_id)
        if not resource_dict:
            return None

        return await self._build_resource_response(resource_dict)

    async def update_resource(
        self, resource_id: int, resource_data: ResourceUpdate, user_id: int
    ) -> Optional[ResourceResponse]:
        """Update existing resource"""

        resource_dict = await self._get_resource_by_id(resource_id)
        if not resource_dict:
            return None

        # Update fields
        update_data = resource_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if (
                field
                in [
                    "cost_per_hour",
                    "cost_per_unit",
                    "capacity_hours_per_day",
                    "max_capacity",
                ]
                and value is not None
            ):
                resource_dict[field] = str(value)
            elif field in ["skills", "certifications"] and value is not None:
                resource_dict[field] = ",".join(value)
            elif (
                field in ["availability_start", "availability_end"]
                and value is not None
            ):
                resource_dict[field] = value.isoformat()
            elif value is not None:
                resource_dict[field] = str(value)

        resource_dict["updated_at"] = datetime.utcnow().isoformat()
        resource_dict["updated_by"] = str(user_id)

        # Update in Redis
        await self.redis.hset(f"resource:{resource_id}", mapping=resource_dict)

        # Update resource metrics
        await self._update_resource_metrics(resource_id)

        return await self._build_resource_response(resource_dict)

    async def delete_resource(self, resource_id: int) -> bool:
        """Delete resource (soft delete)"""

        resource_dict = await self._get_resource_by_id(resource_id)
        if not resource_dict:
            return False

        # Check for active allocations
        active_allocations = await self._get_active_allocations_count(resource_id)
        if active_allocations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete resource with active allocations",
            )

        # Soft delete
        resource_dict["status"] = ResourceStatus.RETIRED.value
        resource_dict["deleted_at"] = datetime.utcnow().isoformat()

        await self.redis.hset(f"resource:{resource_id}", mapping=resource_dict)

        # Remove from active indexes
        await self.redis.srem("resources:all", resource_id)

        return True

    async def allocate_resource(
        self, allocation_data: ResourceAllocationCreate, user_id: int
    ) -> ResourceAllocationResponse:
        """Allocate resource to project/task"""

        # Validate resource exists
        resource_dict = await self._get_resource_by_id(allocation_data.resource_id)
        if not resource_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Resource not found"
            )

        # Check resource availability
        conflicts = await self._check_allocation_conflicts(
            allocation_data.resource_id,
            allocation_data.allocation_start,
            allocation_data.allocation_end,
            allocation_data.allocation_percentage,
        )

        # Generate allocation ID
        allocation_id = await self._generate_allocation_id()

        allocation_dict = {
            "id": allocation_id,
            "resource_id": allocation_data.resource_id,
            "project_id": allocation_data.project_id,
            "task_id": allocation_data.task_id,
            "allocated_by": allocation_data.allocated_by,
            "allocation_percentage": str(allocation_data.allocation_percentage),
            "allocated_hours": str(allocation_data.allocated_hours)
            if allocation_data.allocated_hours
            else None,
            "allocation_start": allocation_data.allocation_start.isoformat(),
            "allocation_end": allocation_data.allocation_end.isoformat(),
            "status": allocation_data.status.value,
            "priority": allocation_data.priority,
            "notes": allocation_data.notes,
            "actual_hours_used": "0",
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store allocation
        await self.redis.hset(
            f"allocation:{allocation_id}",
            mapping={
                k: str(v) if v is not None else "" for k, v in allocation_dict.items()
            },
        )

        # Add to resource allocations
        await self.redis.sadd(
            f"resource_allocations:{allocation_data.resource_id}", allocation_id
        )

        if allocation_data.project_id:
            await self.redis.sadd(
                f"project_allocations:{allocation_data.project_id}", allocation_id
            )

        # Update resource utilization
        await self._update_resource_utilization(allocation_data.resource_id)

        return await self._build_allocation_response(
            allocation_dict, resource_dict, conflicts
        )

    async def get_resource_utilization(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        resource_types: Optional[List[ResourceType]] = None,
        department_id: Optional[int] = None,
    ) -> List[ResourceUtilizationEntry]:
        """Get resource utilization report"""

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today() + timedelta(days=30)

        # Get all resources
        resource_ids = await self.redis.smembers("resources:all")
        utilization_entries = []

        for resource_id_bytes in resource_ids:
            resource_id = int(resource_id_bytes.decode())
            resource_dict = await self._get_resource_by_id(resource_id)

            if not resource_dict:
                continue

            # Filter by resource type
            if resource_types and resource_dict["resource_type"] not in [
                rt.value for rt in resource_types
            ]:
                continue

            # Filter by department
            if department_id and resource_dict.get("department_id") != str(
                department_id
            ):
                continue

            # Calculate utilization
            utilization = await self._calculate_resource_utilization(
                resource_id, date_from, date_to
            )

            utilization_entries.append(utilization)

        return sorted(
            utilization_entries, key=lambda x: x.utilization_percentage, reverse=True
        )

    async def plan_resource_capacity(
        self, request: ResourceCapacityPlanningRequest
    ) -> ResourceCapacityPlanningResponse:
        """Plan resource capacity for given period"""

        period_str = f"{request.date_from} to {request.date_to}"
        period_days = (request.date_to - request.date_from).days + 1

        # Get all resources
        resource_ids = await self.redis.smembers("resources:all")

        total_capacity = Decimal("0")
        allocated_hours = Decimal("0")
        capacity_gaps = []
        skill_gaps = []
        cost_analysis = {
            "total_cost_budget": Decimal("0"),
            "allocated_cost": Decimal("0"),
            "remaining_budget": Decimal("0"),
        }

        for resource_id_bytes in resource_ids:
            resource_id = int(resource_id_bytes.decode())
            resource_dict = await self._get_resource_by_id(resource_id)

            if not resource_dict:
                continue

            # Filter by resource types
            if request.resource_types and resource_dict["resource_type"] not in [
                rt.value for rt in request.resource_types
            ]:
                continue

            # Calculate capacity for period
            daily_capacity = Decimal(resource_dict.get("capacity_hours_per_day", "8"))
            resource_capacity = daily_capacity * period_days
            total_capacity += resource_capacity

            # Get allocations for this resource in the period
            resource_allocations = await self._get_resource_allocations_in_period(
                resource_id, request.date_from, request.date_to
            )

            resource_allocated = sum(
                Decimal(alloc.get("allocated_hours", "0"))
                for alloc in resource_allocations
            )
            allocated_hours += resource_allocated

            # Check for capacity gaps
            if resource_allocated > resource_capacity * Decimal("0.9"):  # 90% threshold
                capacity_gaps.append(
                    {
                        "resource_id": resource_id,
                        "resource_name": resource_dict["name"],
                        "capacity": float(resource_capacity),
                        "allocated": float(resource_allocated),
                        "overallocation": float(resource_allocated - resource_capacity),
                    }
                )

            # Cost analysis
            if resource_dict.get("cost_per_hour"):
                cost_per_hour = Decimal(resource_dict["cost_per_hour"])
                cost_analysis["total_cost_budget"] += cost_per_hour * resource_capacity
                cost_analysis["allocated_cost"] += cost_per_hour * resource_allocated

        available_hours = total_capacity - allocated_hours
        utilization_percentage = (
            float((allocated_hours / total_capacity * 100)) if total_capacity > 0 else 0
        )
        cost_analysis["remaining_budget"] = (
            cost_analysis["total_cost_budget"] - cost_analysis["allocated_cost"]
        )

        # Generate recommendations
        recommendations = []
        if utilization_percentage > 85:
            recommendations.append(
                "Consider hiring additional resources or extending project timelines"
            )
        elif utilization_percentage < 60:
            recommendations.append(
                "Resources are underutilized, consider taking on additional projects"
            )

        if len(capacity_gaps) > 0:
            recommendations.append(
                f"Address {len(capacity_gaps)} resource capacity gaps"
            )

        return ResourceCapacityPlanningResponse(
            planning_period=period_str,
            total_capacity_hours=total_capacity,
            allocated_hours=allocated_hours,
            available_hours=available_hours,
            utilization_percentage=utilization_percentage,
            capacity_gaps=capacity_gaps,
            skill_gaps=skill_gaps,  # Would be implemented with skills analysis
            cost_analysis=cost_analysis,
            resource_recommendations=recommendations,
            optimized_allocations=[],  # Would contain optimization suggestions
        )

    async def optimize_resource_allocation(
        self, request: ResourceOptimizationRequest
    ) -> ResourceOptimizationResponse:
        """Optimize resource allocation"""

        # Get current allocations
        if request.project_id:
            allocation_ids = await self.redis.smembers(
                f"project_allocations:{request.project_id}"
            )
        else:
            # Get all allocations (simplified)
            allocation_ids = []
            resource_ids = await self.redis.smembers("resources:all")
            for resource_id_bytes in resource_ids:
                resource_id = int(resource_id_bytes.decode())
                resource_allocation_ids = await self.redis.smembers(
                    f"resource_allocations:{resource_id}"
                )
                allocation_ids.extend(resource_allocation_ids)

        # Calculate current efficiency
        current_efficiency = await self._calculate_allocation_efficiency(allocation_ids)

        # Generate optimization recommendations
        recommendations = []
        resource_reallocation_plan = []

        # Example optimization logic
        if request.optimization_goal == "efficiency":
            recommendations.append(
                "Redistribute workload to balance resource utilization"
            )
            recommendations.append("Identify and eliminate resource conflicts")
        elif request.optimization_goal == "cost":
            recommendations.append(
                "Prioritize lower-cost resources for non-critical tasks"
            )
            recommendations.append(
                "Consider outsourcing high-cost, low-utilization resources"
            )
        elif request.optimization_goal == "time":
            recommendations.append("Parallelize tasks where possible")
            recommendations.append(
                "Allocate high-performance resources to critical path"
            )

        # Mock optimization results
        optimized_efficiency = current_efficiency * 1.15  # 15% improvement
        improvement_percentage = 15.0
        cost_savings = Decimal("25000.00")
        time_savings = 7  # days

        risk_assessment = {
            "overall_risk": "low",
            "risks": [
                {
                    "type": "resource_availability",
                    "level": "medium",
                    "mitigation": "Confirm resource availability before reallocation",
                }
            ],
        }

        return ResourceOptimizationResponse(
            current_efficiency=current_efficiency,
            optimized_efficiency=optimized_efficiency,
            improvement_percentage=improvement_percentage,
            cost_savings=cost_savings,
            time_savings=time_savings,
            recommended_changes=recommendations,
            resource_reallocation_plan=resource_reallocation_plan,
            risk_assessment=risk_assessment,
        )

    async def _get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource data by ID"""
        resource_data = await self.redis.hgetall(f"resource:{resource_id}")
        if resource_data:
            return {k.decode(): v.decode() for k, v in resource_data.items()}
        return None

    async def _check_resource_code_exists(self, code: str) -> bool:
        """Check if resource code already exists"""
        # Mock implementation - would search through all resources
        return False

    async def _generate_resource_id(self) -> int:
        """Generate unique resource ID"""
        return await self.redis.incr("resource_counter")

    async def _generate_allocation_id(self) -> int:
        """Generate unique allocation ID"""
        return await self.redis.incr("allocation_counter")

    async def _initialize_resource_metrics(self, resource_id: int):
        """Initialize resource metrics"""
        await self.redis.hset(
            f"resource_metrics:{resource_id}",
            mapping={
                "utilization_percentage": "0",
                "efficiency_score": "0",
                "total_allocated_hours": "0",
                "actual_hours_used": "0",
                "cost_this_month": "0",
            },
        )

    async def _update_resource_metrics(self, resource_id: int):
        """Update resource metrics"""
        # Calculate current utilization and efficiency
        utilization = await self._calculate_current_utilization(resource_id)
        efficiency = await self._calculate_efficiency_score(resource_id)

        await self.redis.hset(
            f"resource_metrics:{resource_id}",
            mapping={
                "utilization_percentage": str(utilization),
                "efficiency_score": str(efficiency),
                "last_updated": datetime.utcnow().isoformat(),
            },
        )

    async def _build_resource_response(
        self, resource_dict: Dict[str, Any]
    ) -> ResourceResponse:
        """Build resource response from data"""

        resource_id = int(resource_dict["id"])

        # Get current metrics
        metrics = await self.redis.hgetall(f"resource_metrics:{resource_id}")
        current_utilization = (
            float(metrics.get(b"utilization_percentage", b"0").decode())
            if metrics
            else 0.0
        )
        efficiency_score = (
            float(metrics.get(b"efficiency_score", b"0").decode()) if metrics else 0.0
        )

        # Determine utilization level
        if current_utilization < 60:
            utilization_level = UtilizationLevel.UNDERUTILIZED
        elif current_utilization <= 85:
            utilization_level = UtilizationLevel.OPTIMAL
        elif current_utilization <= 100:
            utilization_level = UtilizationLevel.OVERUTILIZED
        else:
            utilization_level = UtilizationLevel.CRITICAL

        # Get active allocations count
        allocation_ids = await self.redis.smembers(
            f"resource_allocations:{resource_id}"
        )
        active_allocations_count = len(allocation_ids)

        return ResourceResponse(
            id=resource_id,
            code=resource_dict["code"],
            name=resource_dict["name"],
            description=resource_dict.get("description"),
            resource_type=ResourceType(resource_dict["resource_type"]),
            status=ResourceStatus(resource_dict["status"]),
            organization_id=int(resource_dict.get("organization_id", 1)),
            department_id=int(resource_dict["department_id"])
            if resource_dict.get("department_id")
            else None,
            location=resource_dict.get("location"),
            cost_per_hour=Decimal(resource_dict["cost_per_hour"])
            if resource_dict.get("cost_per_hour")
            else None,
            cost_per_unit=Decimal(resource_dict["cost_per_unit"])
            if resource_dict.get("cost_per_unit")
            else None,
            capacity_hours_per_day=Decimal(resource_dict["capacity_hours_per_day"])
            if resource_dict.get("capacity_hours_per_day")
            else None,
            max_capacity=Decimal(resource_dict["max_capacity"])
            if resource_dict.get("max_capacity")
            else None,
            skills=resource_dict.get("skills", "").split(",")
            if resource_dict.get("skills")
            else [],
            certifications=resource_dict.get("certifications", "").split(",")
            if resource_dict.get("certifications")
            else [],
            availability_start=date.fromisoformat(resource_dict["availability_start"])
            if resource_dict.get("availability_start")
            else None,
            availability_end=date.fromisoformat(resource_dict["availability_end"])
            if resource_dict.get("availability_end")
            else None,
            current_utilization=current_utilization,
            utilization_level=utilization_level,
            efficiency_score=efficiency_score,
            active_allocations_count=active_allocations_count,
            total_allocated_hours=Decimal("120.5"),  # Mock data
            remaining_capacity=Decimal("47.5"),  # Mock data
            cost_this_month=Decimal("12500.00"),  # Mock data
            next_available_date=date.today() + timedelta(days=5),  # Mock data
            created_at=datetime.fromisoformat(resource_dict["created_at"]),
            updated_at=datetime.fromisoformat(resource_dict["updated_at"])
            if resource_dict.get("updated_at")
            else None,
        )

    async def _build_allocation_response(
        self,
        allocation_dict: Dict[str, Any],
        resource_dict: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
    ) -> ResourceAllocationResponse:
        """Build allocation response from data"""

        return ResourceAllocationResponse(
            id=int(allocation_dict["id"]),
            resource_id=int(allocation_dict["resource_id"]),
            project_id=int(allocation_dict["project_id"])
            if allocation_dict.get("project_id")
            else None,
            task_id=int(allocation_dict["task_id"])
            if allocation_dict.get("task_id")
            else None,
            allocated_by=int(allocation_dict["allocated_by"]),
            allocation_percentage=Decimal(allocation_dict["allocation_percentage"]),
            allocated_hours=Decimal(allocation_dict["allocated_hours"])
            if allocation_dict.get("allocated_hours")
            else None,
            allocation_start=date.fromisoformat(allocation_dict["allocation_start"]),
            allocation_end=date.fromisoformat(allocation_dict["allocation_end"]),
            status=AllocationStatus(allocation_dict["status"]),
            priority=int(allocation_dict["priority"]),
            notes=allocation_dict.get("notes"),
            resource={
                "id": int(resource_dict["id"]),
                "name": resource_dict["name"],
                "type": resource_dict["resource_type"],
            },
            project_name="Mock Project Name",  # Would fetch from project service
            task_title="Mock Task Title",  # Would fetch from task service
            actual_hours_used=Decimal(allocation_dict.get("actual_hours_used", "0")),
            efficiency_percentage=92.5,  # Mock efficiency
            cost_to_date=Decimal("8750.00"),  # Mock cost
            is_overallocated=len(conflicts) > 0,
            conflicts=conflicts,
            created_at=datetime.fromisoformat(allocation_dict["created_at"]),
            updated_at=datetime.fromisoformat(allocation_dict["updated_at"])
            if allocation_dict.get("updated_at")
            else None,
        )

    async def _check_allocation_conflicts(
        self,
        resource_id: int,
        start_date: date,
        end_date: date,
        allocation_percentage: Decimal,
    ) -> List[Dict[str, Any]]:
        """Check for allocation conflicts"""

        # Mock conflict detection
        conflicts = []

        # Get existing allocations for this resource
        allocation_ids = await self.redis.smembers(
            f"resource_allocations:{resource_id}"
        )

        total_allocation = Decimal("0")
        for allocation_id_bytes in allocation_ids:
            allocation_id = int(allocation_id_bytes.decode())
            allocation_data = await self.redis.hgetall(f"allocation:{allocation_id}")

            if allocation_data:
                existing_start = date.fromisoformat(
                    allocation_data[b"allocation_start"].decode()
                )
                existing_end = date.fromisoformat(
                    allocation_data[b"allocation_end"].decode()
                )
                existing_percentage = Decimal(
                    allocation_data[b"allocation_percentage"].decode()
                )

                # Check for date overlap
                if not (end_date < existing_start or start_date > existing_end):
                    total_allocation += existing_percentage

        total_allocation += allocation_percentage

        # Check if over 100% allocation
        if total_allocation > 100:
            conflicts.append(
                {
                    "type": "overallocation",
                    "severity": "high",
                    "message": f"Resource allocation would exceed 100% ({total_allocation}%)",
                    "suggested_action": "Reduce allocation percentage or adjust dates",
                }
            )

        return conflicts

    async def _get_active_allocations_count(self, resource_id: int) -> int:
        """Get count of active allocations for resource"""
        allocation_ids = await self.redis.smembers(
            f"resource_allocations:{resource_id}"
        )

        active_count = 0
        for allocation_id_bytes in allocation_ids:
            allocation_id = int(allocation_id_bytes.decode())
            allocation_data = await self.redis.hgetall(f"allocation:{allocation_id}")

            if allocation_data:
                status = allocation_data[b"status"].decode()
                if status in ["planned", "active"]:
                    active_count += 1

        return active_count

    async def _calculate_current_utilization(self, resource_id: int) -> float:
        """Calculate current resource utilization"""
        # Mock calculation
        return 73.5

    async def _calculate_efficiency_score(self, resource_id: int) -> float:
        """Calculate resource efficiency score"""
        # Mock calculation
        return 87.2

    async def _calculate_resource_utilization(
        self, resource_id: int, date_from: date, date_to: date
    ) -> ResourceUtilizationEntry:
        """Calculate resource utilization for period"""

        resource_dict = await self._get_resource_by_id(resource_id)

        # Mock calculations
        total_capacity = Decimal("160")  # hours for period
        allocated_capacity = Decimal("140")
        utilized_capacity = Decimal("125")
        utilization_percentage = float((utilized_capacity / total_capacity) * 100)

        if utilization_percentage < 60:
            utilization_level = UtilizationLevel.UNDERUTILIZED
        elif utilization_percentage <= 85:
            utilization_level = UtilizationLevel.OPTIMAL
        elif utilization_percentage <= 100:
            utilization_level = UtilizationLevel.OVERUTILIZED
        else:
            utilization_level = UtilizationLevel.CRITICAL

        efficiency_score = (
            float((utilized_capacity / allocated_capacity) * 100)
            if allocated_capacity > 0
            else 0
        )
        cost_per_hour = Decimal(resource_dict.get("cost_per_hour", "0"))
        total_cost = cost_per_hour * utilized_capacity

        return ResourceUtilizationEntry(
            resource_id=int(resource_dict["id"]),
            resource_name=resource_dict["name"],
            resource_type=resource_dict["resource_type"],
            total_capacity=total_capacity,
            allocated_capacity=allocated_capacity,
            utilized_capacity=utilized_capacity,
            utilization_percentage=utilization_percentage,
            utilization_level=utilization_level,
            efficiency_score=efficiency_score,
            cost_per_hour=cost_per_hour,
            total_cost=total_cost,
            active_allocations=3,  # Mock
            upcoming_allocations=2,  # Mock
        )

    async def _get_resource_allocations_in_period(
        self, resource_id: int, date_from: date, date_to: date
    ) -> List[Dict[str, Any]]:
        """Get resource allocations in given period"""

        allocation_ids = await self.redis.smembers(
            f"resource_allocations:{resource_id}"
        )
        allocations = []

        for allocation_id_bytes in allocation_ids:
            allocation_id = int(allocation_id_bytes.decode())
            allocation_data = await self.redis.hgetall(f"allocation:{allocation_id}")

            if allocation_data:
                allocation_start = date.fromisoformat(
                    allocation_data[b"allocation_start"].decode()
                )
                allocation_end = date.fromisoformat(
                    allocation_data[b"allocation_end"].decode()
                )

                # Check if allocation overlaps with period
                if not (date_to < allocation_start or date_from > allocation_end):
                    allocations.append(
                        {k.decode(): v.decode() for k, v in allocation_data.items()}
                    )

        return allocations

    async def _calculate_allocation_efficiency(
        self, allocation_ids: List[bytes]
    ) -> float:
        """Calculate efficiency of allocations"""
        # Mock calculation
        return 78.5

    async def _update_resource_utilization(self, resource_id: int):
        """Update resource utilization after allocation change"""
        await self._update_resource_metrics(resource_id)


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_resource_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> ResourceManagementService:
    """Get resource management service instance"""
    return ResourceManagementService(db, redis)


# API Endpoints - Resource Management
@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Create a new resource"""
    return await service.create_resource(resource_data, current_user.id)


@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    resource_type: Optional[ResourceType] = Query(None),
    status: Optional[ResourceStatus] = Query(None),
    department_id: Optional[int] = Query(None),
    service: ResourceManagementService = Depends(get_resource_service),
):
    """List resources with filtering"""
    # Mock implementation - would implement filtering
    return []


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Get resource by ID"""
    resource = await service.get_resource(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Update resource"""
    resource = await service.update_resource(
        resource_id, resource_data, current_user.id
    )
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Delete resource"""
    success = await service.delete_resource(resource_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )


@router.post(
    "/allocations",
    response_model=ResourceAllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allocate_resource(
    allocation_data: ResourceAllocationCreate,
    current_user: User = Depends(get_current_user),
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Allocate resource to project/task"""
    return await service.allocate_resource(allocation_data, current_user.id)


@router.get("/utilization/report", response_model=List[ResourceUtilizationEntry])
async def get_resource_utilization_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    resource_types: Optional[str] = Query(
        None, description="Comma-separated resource types"
    ),
    department_id: Optional[int] = Query(None),
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Get resource utilization report"""

    resource_type_list = None
    if resource_types:
        resource_type_list = [
            ResourceType(rt.strip()) for rt in resource_types.split(",")
        ]

    return await service.get_resource_utilization(
        date_from=date_from,
        date_to=date_to,
        resource_types=resource_type_list,
        department_id=department_id,
    )


@router.post("/capacity/plan", response_model=ResourceCapacityPlanningResponse)
async def plan_resource_capacity(
    request: ResourceCapacityPlanningRequest,
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Plan resource capacity for given period"""
    return await service.plan_resource_capacity(request)


@router.post("/optimize", response_model=ResourceOptimizationResponse)
async def optimize_resource_allocation(
    request: ResourceOptimizationRequest,
    service: ResourceManagementService = Depends(get_resource_service),
):
    """Optimize resource allocation"""
    return await service.optimize_resource_allocation(request)


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for resource management API"""
    return {
        "status": "healthy",
        "service": "resource-management-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
