"""
User Assignment Service for Issue #42.
ユーザー割り当てサービス（Issue #42 - 組織・部門管理API実装と階層構造サポート）
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.department import Department
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user_assignment import (
    AssignmentValidationResult,
    BulkUserAssignmentRequest,
    DepartmentUsersResponse,
    OrganizationUsersResponse,
    UserAssignmentCreate,
    UserAssignmentResponse,
    UserAssignmentUpdate,
    UserSummary,
)


class UserAssignmentService:
    """Service for managing user assignments to organizations and departments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_organization_users(
        self,
        organization_id: int,
        include_departments: bool = True,
        include_inactive: bool = False,
        role_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[OrganizationUsersResponse]:
        """
        Get all users assigned to an organization.
        組織に割り当てられたユーザー一覧を取得
        """
        try:
            # Check if organization exists
            org_query = select(Organization).where(Organization.id == organization_id)
            result = await self.db.execute(org_query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                return None
            
            # Build user query
            user_query = select(User).where(User.organization_id == organization_id)
            
            if not include_inactive:
                user_query = user_query.where(User.is_active == True)
            
            # Apply role filter if specified
            if role_filter:
                # This would need proper role relationship join
                pass  # Placeholder for role filtering
            
            # Get total count
            count_query = select(func.count()).select_from(user_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            
            # Apply pagination and execute
            paginated_query = user_query.offset(offset).limit(limit).order_by(User.full_name)
            result = await self.db.execute(paginated_query)
            users = result.scalars().all()
            
            # Convert to UserSummary
            user_summaries = [
                UserSummary(
                    id=user.id,
                    full_name=user.full_name or f"{user.first_name} {user.last_name}",
                    email=user.email,
                    is_active=user.is_active,
                    employee_id=getattr(user, 'employee_id', None),
                    hire_date=getattr(user, 'hire_date', None),
                    job_title=getattr(user, 'job_title', None),
                    current_organization_id=user.organization_id,
                    current_department_id=getattr(user, 'department_id', None)
                )
                for user in users
            ]
            
            # Get department breakdown if requested
            departments = None
            if include_departments:
                dept_query = select(
                    Department.id,
                    Department.name,
                    Department.code,
                    func.count(User.id).label("user_count")
                ).select_from(
                    Department
                ).outerjoin(
                    User, and_(
                        User.department_id == Department.id,
                        User.organization_id == organization_id,
                        User.is_active == True if not include_inactive else True
                    )
                ).where(
                    Department.organization_id == organization_id,
                    Department.is_active == True
                ).group_by(Department.id, Department.name, Department.code)
                
                dept_result = await self.db.execute(dept_query)
                departments = [
                    {
                        "id": row.id,
                        "name": row.name,
                        "code": row.code,
                        "user_count": row.user_count
                    }
                    for row in dept_result
                ]
            
            # Calculate statistics
            active_count = sum(1 for u in user_summaries if u.is_active)
            inactive_count = len(user_summaries) - active_count
            
            return OrganizationUsersResponse(
                organization_id=organization.id,
                organization_name=organization.name,
                organization_code=organization.code,
                total_users=total_count,
                active_users=active_count,
                inactive_users=inactive_count,
                users=user_summaries,
                departments=departments,
                limit=limit,
                offset=offset,
                has_more=(offset + len(user_summaries)) < total_count
            )
            
        except Exception as e:
            raise ValueError(f"Failed to get organization users: {str(e)}")

    async def get_department_users(
        self,
        department_id: int,
        include_sub_departments: bool = False,
        include_inactive: bool = False,
        role_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[DepartmentUsersResponse]:
        """
        Get all users assigned to a department.
        部門に割り当てられたユーザー一覧を取得
        """
        try:
            # Check if department exists
            dept_query = select(Department).where(Department.id == department_id)
            dept_query = dept_query.options(joinedload(Department.organization))
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()
            
            if not department:
                return None
            
            # Build department filter
            dept_filter = [User.department_id == department_id]
            
            if include_sub_departments:
                # Get all sub-department IDs
                sub_dept_ids = await self._get_all_sub_department_ids(department_id)
                if sub_dept_ids:
                    dept_filter.append(User.department_id.in_(sub_dept_ids))
            
            # Build user query
            user_query = select(User).where(or_(*dept_filter))
            
            if not include_inactive:
                user_query = user_query.where(User.is_active == True)
            
            # Apply role filter if specified
            if role_filter:
                # This would need proper role relationship join
                pass  # Placeholder for role filtering
            
            # Get total count
            count_query = select(func.count()).select_from(user_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            
            # Apply pagination and execute
            paginated_query = user_query.offset(offset).limit(limit).order_by(User.full_name)
            result = await self.db.execute(paginated_query)
            users = result.scalars().all()
            
            # Convert to UserSummary
            user_summaries = [
                UserSummary(
                    id=user.id,
                    full_name=user.full_name or f"{user.first_name} {user.last_name}",
                    email=user.email,
                    is_active=user.is_active,
                    employee_id=getattr(user, 'employee_id', None),
                    hire_date=getattr(user, 'hire_date', None),
                    job_title=getattr(user, 'job_title', None),
                    current_organization_id=user.organization_id,
                    current_department_id=getattr(user, 'department_id', None)
                )
                for user in users
            ]
            
            # Get sub-department breakdown if requested
            sub_departments = None
            if include_sub_departments:
                subdept_query = select(
                    Department.id,
                    Department.name,
                    Department.code,
                    func.count(User.id).label("user_count")
                ).select_from(
                    Department
                ).outerjoin(
                    User, and_(
                        User.department_id == Department.id,
                        User.is_active == True if not include_inactive else True
                    )
                ).where(
                    Department.parent_id == department_id,
                    Department.is_active == True
                ).group_by(Department.id, Department.name, Department.code)
                
                subdept_result = await self.db.execute(subdept_query)
                sub_departments = [
                    {
                        "id": row.id,
                        "name": row.name,
                        "code": row.code,
                        "user_count": row.user_count
                    }
                    for row in subdept_result
                ]
            
            # Calculate statistics
            active_count = sum(1 for u in user_summaries if u.is_active)
            inactive_count = len(user_summaries) - active_count
            
            return DepartmentUsersResponse(
                department_id=department.id,
                department_name=department.name,
                department_code=department.code,
                organization_id=department.organization_id,
                organization_name=department.organization.name,
                total_users=total_count,
                active_users=active_count,
                inactive_users=inactive_count,
                users=user_summaries,
                sub_departments=sub_departments,
                limit=limit,
                offset=offset,
                has_more=(offset + len(user_summaries)) < total_count
            )
            
        except Exception as e:
            raise ValueError(f"Failed to get department users: {str(e)}")

    async def _get_all_sub_department_ids(self, department_id: int) -> List[int]:
        """Get all sub-department IDs recursively using CTE."""
        
        cte_query = text("""
            WITH RECURSIVE department_tree AS (
                SELECT id, parent_id, 1 as level
                FROM departments
                WHERE parent_id = :dept_id
                
                UNION ALL
                
                SELECT d.id, d.parent_id, dt.level + 1
                FROM departments d
                INNER JOIN department_tree dt ON d.parent_id = dt.id
                WHERE dt.level < 10  -- Prevent infinite recursion
            )
            SELECT id FROM department_tree
        """)
        
        result = await self.db.execute(cte_query, {"dept_id": department_id})
        return [row[0] for row in result]

    async def assign_user(
        self, assignment: UserAssignmentCreate, assigned_by: int
    ) -> UserAssignmentResponse:
        """
        Assign user to organization and department.
        ユーザーを組織・部門に割り当て
        """
        try:
            # Validate user exists
            user_query = select(User).where(User.id == assignment.user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Validate organization exists
            org_query = select(Organization).where(Organization.id == assignment.organization_id)
            result = await self.db.execute(org_query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                raise ValueError("Organization not found")
            
            # Validate department if specified
            department = None
            if assignment.department_id:
                dept_query = select(Department).where(
                    Department.id == assignment.department_id,
                    Department.organization_id == assignment.organization_id
                )
                result = await self.db.execute(dept_query)
                department = result.scalar_one_or_none()
                
                if not department:
                    raise ValueError("Department not found or not in specified organization")
            
            # Update user's organization and department
            user.organization_id = assignment.organization_id
            if assignment.department_id:
                user.department_id = assignment.department_id
            user.updated_by = assigned_by
            
            # Handle role assignments if specified
            if assignment.role_assignments:
                # This would need proper role management implementation
                pass  # Placeholder for role assignment
            
            await self.db.commit()
            
            return UserAssignmentResponse(
                id=user.id,  # Using user ID as assignment ID for simplicity
                user_id=user.id,
                organization_id=assignment.organization_id,
                department_id=assignment.department_id,
                is_primary=assignment.is_primary,
                is_active=True,
                effective_date=assignment.effective_date or datetime.utcnow(),
                assignment_reason=assignment.assignment_reason,
                assigned_by=assigned_by,
                assigned_at=datetime.utcnow(),
                updated_by=None,
                updated_at=None,
                user_name=user.full_name,
                user_email=user.email,
                organization_name=organization.name,
                organization_code=organization.code,
                department_name=department.name if department else None,
                department_code=department.code if department else None,
                role_names=assignment.role_assignments
            )
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to assign user: {str(e)}")

    async def update_assignment(
        self, assignment_id: int, assignment_update: UserAssignmentUpdate, updated_by: int
    ) -> Optional[UserAssignmentResponse]:
        """
        Update user assignment.
        ユーザー割り当て情報の更新
        """
        try:
            # Get user (using assignment_id as user_id for simplicity)
            user_query = select(User).where(User.id == assignment_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Update organization if specified
            if assignment_update.organization_id:
                org_query = select(Organization).where(Organization.id == assignment_update.organization_id)
                result = await self.db.execute(org_query)
                organization = result.scalar_one_or_none()
                
                if not organization:
                    raise ValueError("Organization not found")
                
                user.organization_id = assignment_update.organization_id
            
            # Update department if specified
            if assignment_update.department_id:
                dept_query = select(Department).where(
                    Department.id == assignment_update.department_id,
                    Department.organization_id == user.organization_id
                )
                result = await self.db.execute(dept_query)
                department = result.scalar_one_or_none()
                
                if not department:
                    raise ValueError("Department not found or not in user's organization")
                
                user.department_id = assignment_update.department_id
            
            # Update user status if specified
            if assignment_update.is_active is not None:
                user.is_active = assignment_update.is_active
            
            user.updated_by = updated_by
            
            await self.db.commit()
            
            # Return updated assignment
            return await self._get_user_assignment_response(user)
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update assignment: {str(e)}")

    async def _get_user_assignment_response(self, user: User) -> UserAssignmentResponse:
        """Convert User model to UserAssignmentResponse."""
        
        # Get organization info
        org_query = select(Organization).where(Organization.id == user.organization_id)
        result = await self.db.execute(org_query)
        organization = result.scalar_one_or_none()
        
        # Get department info if assigned
        department = None
        if hasattr(user, 'department_id') and user.department_id:
            dept_query = select(Department).where(Department.id == user.department_id)
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()
        
        return UserAssignmentResponse(
            id=user.id,
            user_id=user.id,
            organization_id=user.organization_id,
            department_id=getattr(user, 'department_id', None),
            is_primary=True,  # Assuming primary assignment
            is_active=user.is_active,
            effective_date=user.created_at,
            assignment_reason=None,
            assigned_by=user.created_by,
            assigned_at=user.created_at,
            updated_by=user.updated_by,
            updated_at=user.updated_at,
            user_name=user.full_name,
            user_email=user.email,
            organization_name=organization.name if organization else None,
            organization_code=organization.code if organization else None,
            department_name=department.name if department else None,
            department_code=department.code if department else None,
            role_names=None  # Would need role relationship
        )

    async def remove_assignment(self, assignment_id: int, removed_by: int) -> bool:
        """
        Remove user assignment.
        ユーザー割り当ての削除
        """
        try:
            # Get user (using assignment_id as user_id)
            user_query = select(User).where(User.id == assignment_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Remove assignment by clearing organization/department
            user.organization_id = None
            user.department_id = None
            user.updated_by = removed_by
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to remove assignment: {str(e)}")

    async def bulk_assign_users(
        self, bulk_request: BulkUserAssignmentRequest, assigned_by: int
    ) -> Dict[str, Any]:
        """
        Bulk assign multiple users to organizations and departments.
        複数ユーザーの組織・部門一括割り当て
        """
        successful_count = 0
        failed_count = 0
        errors = []
        
        try:
            for assignment in bulk_request.assignments:
                try:
                    # Check for duplicates if requested
                    if bulk_request.skip_duplicates:
                        user_query = select(User).where(
                            User.id == assignment.user_id,
                            User.organization_id == assignment.organization_id
                        )
                        result = await self.db.execute(user_query)
                        existing_user = result.scalar_one_or_none()
                        
                        if existing_user:
                            continue  # Skip duplicate
                    
                    # Perform assignment
                    await self.assign_user(assignment, assigned_by)
                    successful_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        "user_id": assignment.user_id,
                        "error": str(e)
                    })
            
            return {
                "successful_count": successful_count,
                "failed_count": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Bulk assignment failed: {str(e)}")

    async def get_user_assignments(
        self, user_id: int, include_history: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get all assignments for a specific user.
        特定ユーザーの割り当て情報を取得
        """
        try:
            # Check if user exists
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Get current assignment
            current_assignment = None
            if user.organization_id:
                current_assignment = await self._get_user_assignment_response(user)
            
            # Get assignment history if requested
            history = []
            if include_history:
                # This would require a proper assignment history table
                # For now, just return the current assignment as history
                if current_assignment:
                    history = [current_assignment]
            
            return {
                "user_id": user_id,
                "user_name": user.full_name,
                "user_email": user.email,
                "current_assignment": current_assignment,
                "assignment_history": history,
                "total_assignments": 1 if current_assignment else 0,
                "active_assignments": 1 if current_assignment and current_assignment.is_active else 0
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get user assignments: {str(e)}")

    async def transfer_user(
        self,
        user_id: int,
        new_organization_id: Optional[int],
        new_department_id: Optional[int],
        transfer_reason: Optional[str],
        effective_date: Optional[str],
        transferred_by: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Transfer user to different organization or department.
        ユーザーの組織・部門転籍
        """
        try:
            # Get user
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Store previous assignment info
            previous_org_id = user.organization_id
            previous_dept_id = getattr(user, 'department_id', None)
            
            # Validate new organization if specified
            if new_organization_id:
                org_query = select(Organization).where(Organization.id == new_organization_id)
                result = await self.db.execute(org_query)
                organization = result.scalar_one_or_none()
                
                if not organization:
                    raise ValueError("New organization not found")
                
                user.organization_id = new_organization_id
            
            # Validate new department if specified
            if new_department_id:
                target_org_id = new_organization_id or user.organization_id
                dept_query = select(Department).where(
                    Department.id == new_department_id,
                    Department.organization_id == target_org_id
                )
                result = await self.db.execute(dept_query)
                department = result.scalar_one_or_none()
                
                if not department:
                    raise ValueError("New department not found or not in target organization")
                
                user.department_id = new_department_id
            
            user.updated_by = transferred_by
            
            await self.db.commit()
            
            return {
                "transfer_id": user_id,  # Using user_id as transfer_id
                "user_id": user_id,
                "user_name": user.full_name,
                "previous_organization_id": previous_org_id,
                "previous_department_id": previous_dept_id,
                "new_organization_id": new_organization_id,
                "new_department_id": new_department_id,
                "transfer_reason": transfer_reason,
                "effective_date": effective_date or datetime.utcnow().isoformat(),
                "transferred_by": transferred_by,
                "transferred_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to transfer user: {str(e)}")

    async def get_organization_assignment_stats(
        self, organization_id: int, include_departments: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get organization assignment statistics.
        組織の割り当て統計情報を取得
        """
        try:
            # Check if organization exists
            org_query = select(Organization).where(Organization.id == organization_id)
            result = await self.db.execute(org_query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                return None
            
            # Get user statistics
            user_stats_query = select(
                func.count(User.id).label("total_users"),
                func.count(User.id).filter(User.is_active == True).label("active_users")
            ).where(User.organization_id == organization_id)
            
            result = await self.db.execute(user_stats_query)
            user_stats = result.first()
            
            # Get department count
            dept_count_query = select(func.count(Department.id)).where(
                Department.organization_id == organization_id,
                Department.is_active == True
            )
            result = await self.db.execute(dept_count_query)
            departments_count = result.scalar()
            
            stats = {
                "organization_id": organization_id,
                "organization_name": organization.name,
                "total_assignments": user_stats.total_users or 0,
                "active_assignments": user_stats.active_users or 0,
                "inactive_assignments": (user_stats.total_users or 0) - (user_stats.active_users or 0),
                "total_users": user_stats.total_users or 0,
                "active_users": user_stats.active_users or 0,
                "departments_count": departments_count or 0,
                "department_stats": [],
                "role_distribution": {},
                "monthly_changes": {}
            }
            
            # Get department breakdown if requested
            if include_departments:
                dept_stats_query = select(
                    Department.id,
                    Department.name,
                    Department.code,
                    func.count(User.id).label("user_count"),
                    func.count(User.id).filter(User.is_active == True).label("active_count")
                ).select_from(
                    Department
                ).outerjoin(
                    User, User.department_id == Department.id
                ).where(
                    Department.organization_id == organization_id,
                    Department.is_active == True
                ).group_by(Department.id, Department.name, Department.code)
                
                result = await self.db.execute(dept_stats_query)
                stats["department_stats"] = [
                    {
                        "department_id": row.id,
                        "department_name": row.name,
                        "department_code": row.code,
                        "total_users": row.user_count,
                        "active_users": row.active_count
                    }
                    for row in result
                ]
            
            return stats
            
        except Exception as e:
            raise ValueError(f"Failed to get organization assignment statistics: {str(e)}")

    async def get_department_assignment_stats(
        self, department_id: int, include_sub_departments: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get department assignment statistics.
        部門の割り当て統計情報を取得
        """
        try:
            # Check if department exists
            dept_query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()
            
            if not department:
                return None
            
            # Build department filter
            dept_filter = [User.department_id == department_id]
            
            if include_sub_departments:
                sub_dept_ids = await self._get_all_sub_department_ids(department_id)
                if sub_dept_ids:
                    dept_filter.append(User.department_id.in_(sub_dept_ids))
            
            # Get user statistics
            user_stats_query = select(
                func.count(User.id).label("total_users"),
                func.count(User.id).filter(User.is_active == True).label("active_users")
            ).where(or_(*dept_filter))
            
            result = await self.db.execute(user_stats_query)
            user_stats = result.first()
            
            # Calculate headcount utilization
            headcount_utilization = None
            if department.headcount_limit and department.headcount_limit > 0:
                headcount_utilization = ((user_stats.active_users or 0) / department.headcount_limit) * 100
            
            stats = {
                "department_id": department_id,
                "department_name": department.name,
                "organization_id": department.organization_id,
                "total_assignments": user_stats.total_users or 0,
                "active_assignments": user_stats.active_users or 0,
                "inactive_assignments": (user_stats.total_users or 0) - (user_stats.active_users or 0),
                "total_users": user_stats.total_users or 0,
                "active_users": user_stats.active_users or 0,
                "headcount_limit": department.headcount_limit,
                "headcount_utilization": round(headcount_utilization, 2) if headcount_utilization else None,
                "sub_department_stats": [],
                "role_distribution": {}
            }
            
            # Get sub-department breakdown if requested
            if include_sub_departments:
                subdept_stats_query = select(
                    Department.id,
                    Department.name,
                    Department.code,
                    func.count(User.id).label("user_count"),
                    func.count(User.id).filter(User.is_active == True).label("active_count")
                ).select_from(
                    Department
                ).outerjoin(
                    User, User.department_id == Department.id
                ).where(
                    Department.parent_id == department_id,
                    Department.is_active == True
                ).group_by(Department.id, Department.name, Department.code)
                
                result = await self.db.execute(subdept_stats_query)
                stats["sub_department_stats"] = [
                    {
                        "department_id": row.id,
                        "department_name": row.name,
                        "department_code": row.code,
                        "total_users": row.user_count,
                        "active_users": row.active_count
                    }
                    for row in result
                ]
            
            return stats
            
        except Exception as e:
            raise ValueError(f"Failed to get department assignment statistics: {str(e)}")

    async def validate_assignments(
        self, organization_id: Optional[int] = None, fix_issues: bool = False
    ) -> Dict[str, Any]:
        """
        Validate all user assignments for consistency.
        ユーザー割り当ての整合性検証
        """
        issues = []
        fixed_count = 0
        
        try:
            # Check for users without organization
            orphan_users_query = select(User.id, User.full_name, User.email).where(
                User.organization_id.is_(None),
                User.is_active == True
            )
            
            if organization_id:
                # If specific organization, check users with invalid org references
                orphan_users_query = select(User.id, User.full_name, User.email).where(
                    User.organization_id == organization_id,
                    User.is_active == True
                ).outerjoin(
                    Organization, Organization.id == User.organization_id
                ).where(Organization.id.is_(None))
            
            result = await self.db.execute(orphan_users_query)
            orphan_users = result.fetchall()
            
            for user in orphan_users:
                issues.append({
                    "issue_type": "orphaned_user",
                    "severity": "error",
                    "description": f"User {user.full_name} ({user.email}) has no valid organization",
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "organization_id": None,
                    "department_id": None,
                    "suggested_fix": "Assign user to a valid organization",
                    "auto_fixable": False
                })
            
            # Check for users with invalid department assignments
            invalid_dept_query = text("""
                SELECT u.id, u.full_name, u.email, u.organization_id, u.department_id
                FROM users u
                LEFT JOIN departments d ON d.id = u.department_id
                WHERE u.department_id IS NOT NULL
                AND u.is_active = true
                AND (d.id IS NULL OR d.organization_id != u.organization_id)
            """)
            
            if organization_id:
                invalid_dept_query = text("""
                    SELECT u.id, u.full_name, u.email, u.organization_id, u.department_id
                    FROM users u
                    LEFT JOIN departments d ON d.id = u.department_id
                    WHERE u.organization_id = :org_id
                    AND u.department_id IS NOT NULL
                    AND u.is_active = true
                    AND (d.id IS NULL OR d.organization_id != u.organization_id)
                """)
                result = await self.db.execute(invalid_dept_query, {"org_id": organization_id})
            else:
                result = await self.db.execute(invalid_dept_query)
            
            invalid_dept_users = result.fetchall()
            
            for user in invalid_dept_users:
                issues.append({
                    "issue_type": "invalid_department",
                    "severity": "error",
                    "description": f"User {user.full_name} assigned to invalid department",
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "organization_id": user.organization_id,
                    "department_id": user.department_id,
                    "suggested_fix": "Remove invalid department assignment or assign to valid department",
                    "auto_fixable": True
                })
                
                # Auto-fix if requested
                if fix_issues:
                    user_update_query = select(User).where(User.id == user.id)
                    user_result = await self.db.execute(user_update_query)
                    user_obj = user_result.scalar_one_or_none()
                    
                    if user_obj:
                        user_obj.department_id = None
                        fixed_count += 1
            
            if fix_issues and fixed_count > 0:
                await self.db.commit()
            
            return {
                "issues_count": len(issues),
                "fixed_count": fixed_count,
                "issues": issues,
                "recommendations": [
                    "Review orphaned users and assign to appropriate organizations",
                    "Verify department assignments match organization structure",
                    "Consider implementing automated assignment validation"
                ]
            }
            
        except Exception as e:
            if fix_issues:
                await self.db.rollback()
            raise ValueError(f"Assignment validation failed: {str(e)}")