"""
Integration tests for Organization and Department hierarchy management.
組織・部門階層管理の統合テスト
"""

import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User


@pytest.mark.asyncio
class TestOrganizationHierarchyIntegration:
    """Integration tests for organization hierarchy management."""

    async def test_complete_organization_hierarchy_workflow(self, db: AsyncSession):
        """Test complete workflow from organization creation to hierarchy management."""
        
        # Create root organization
        root_org = Organization(
            code="ROOT001",
            name="Root Organization",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(root_org)
        await db.commit()
        await db.refresh(root_org)
        
        # Create subsidiary organization
        subsidiary_org = Organization(
            code="SUB001",
            name="Subsidiary Organization",
            parent_id=root_org.id,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(subsidiary_org)
        await db.commit()
        await db.refresh(subsidiary_org)
        
        # Create departments in root organization
        dept1 = Department(
            code="DEPT001",
            name="Engineering Department",
            organization_id=root_org.id,
            parent_id=None,
            path=str(1),  # Will be updated
            depth=0,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(dept1)
        await db.commit()
        await db.refresh(dept1)
        
        # Update department path
        dept1.path = str(dept1.id)
        await db.commit()
        
        # Create sub-department
        sub_dept = Department(
            code="SUBDEPT001",
            name="Software Engineering",
            organization_id=root_org.id,
            parent_id=dept1.id,
            path=f"{dept1.id}.{dept1.id + 1}",  # Will be updated
            depth=1,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(sub_dept)
        await db.commit()
        await db.refresh(sub_dept)
        
        # Update sub-department path
        sub_dept.path = f"{dept1.path}.{sub_dept.id}"
        await db.commit()
        
        # Create users
        user1 = User(
            email="user1@example.com",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            organization_id=root_org.id,
            department_id=dept1.id,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(user1)
        
        user2 = User(
            email="user2@example.com",
            first_name="Jane",
            last_name="Smith",
            full_name="Jane Smith",
            organization_id=root_org.id,
            department_id=sub_dept.id,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(user2)
        await db.commit()
        
        # Test API endpoints
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test organization tree endpoint
            tree_response = await client.get(f"/api/v1/organizations/{root_org.id}/tree")
            assert tree_response.status_code == 200
            tree_data = tree_response.json()
            assert tree_data["id"] == root_org.id
            assert tree_data["code"] == "ROOT001"
            
            # Test organization statistics
            stats_response = await client.get(f"/api/v1/organizations/{root_org.id}/stats")
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            assert "statistics" in stats_data
            
            # Test department tree
            dept_tree_response = await client.get(f"/api/v1/departments/{dept1.id}/tree")
            assert dept_tree_response.status_code == 200
            dept_tree_data = dept_tree_response.json()
            assert dept_tree_data["id"] == dept1.id
            
            # Test organization users
            users_response = await client.get(f"/api/v1/user-assignments/organizations/{root_org.id}/users")
            assert users_response.status_code == 200
            users_data = users_response.json()
            assert users_data["organization_id"] == root_org.id
            assert users_data["total_users"] == 2
            
            # Test department users
            dept_users_response = await client.get(f"/api/v1/user-assignments/departments/{dept1.id}/users")
            assert dept_users_response.status_code == 200
            dept_users_data = dept_users_response.json()
            assert dept_users_data["department_id"] == dept1.id

    async def test_hierarchy_validation_and_constraints(self, db: AsyncSession):
        """Test hierarchy validation and constraint enforcement."""
        
        # Create organizations with potential issues
        org1 = Organization(
            code="ORG001",
            name="Organization 1",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org1)
        await db.commit()
        await db.refresh(org1)
        
        org2 = Organization(
            code="ORG002",
            name="Organization 2",
            parent_id=org1.id,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org2)
        await db.commit()
        await db.refresh(org2)
        
        # Test validation endpoint
        async with AsyncClient(app=app, base_url="http://test") as client:
            validation_response = await client.get(f"/api/v1/organizations/{org1.id}/validation")
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert "is_valid" in validation_data
            assert "errors" in validation_data
            assert "warnings" in validation_data

    async def test_user_assignment_workflow(self, db: AsyncSession):
        """Test complete user assignment workflow."""
        
        # Create test data
        org = Organization(
            code="TESTORG",
            name="Test Organization",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        dept = Department(
            code="TESTDEPT",
            name="Test Department",
            organization_id=org.id,
            parent_id=None,
            path=str(1),
            depth=0,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        
        dept.path = str(dept.id)
        await db.commit()
        
        user = User(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            full_name="Test User",
            organization_id=None,  # Initially unassigned
            department_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Test assignment API
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Assign user to organization and department
            assignment_data = {
                "user_id": user.id,
                "organization_id": org.id,
                "department_id": dept.id,
                "is_primary": True,
                "assignment_reason": "Initial assignment"
            }
            
            assign_response = await client.post(
                "/api/v1/user-assignments/assign",
                json=assignment_data
            )
            assert assign_response.status_code == 200
            assign_result = assign_response.json()
            assert assign_result["user_id"] == user.id
            assert assign_result["organization_id"] == org.id
            assert assign_result["department_id"] == dept.id
            
            # Verify assignment
            user_assignments_response = await client.get(f"/api/v1/user-assignments/users/{user.id}/assignments")
            assert user_assignments_response.status_code == 200
            assignments_data = user_assignments_response.json()
            assert assignments_data["user_id"] == user.id
            assert assignments_data["current_assignment"] is not None

    async def test_performance_with_large_hierarchy(self, db: AsyncSession):
        """Test performance with larger hierarchy structures."""
        
        # Create root organization
        root_org = Organization(
            code="PERF001",
            name="Performance Test Organization",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(root_org)
        await db.commit()
        await db.refresh(root_org)
        
        # Create multiple subsidiary organizations
        subsidiaries = []
        for i in range(5):
            sub_org = Organization(
                code=f"SUB{i:03d}",
                name=f"Subsidiary {i+1}",
                parent_id=root_org.id,
                is_active=True,
                created_by=1,
                created_at=datetime.utcnow()
            )
            db.add(sub_org)
            subsidiaries.append(sub_org)
        
        await db.commit()
        
        # Create departments in each organization
        departments = []
        for org in [root_org] + subsidiaries:
            await db.refresh(org)
            for j in range(3):
                dept = Department(
                    code=f"DEPT{org.id:03d}{j:02d}",
                    name=f"Department {j+1} - Org {org.id}",
                    organization_id=org.id,
                    parent_id=None,
                    path=str(len(departments) + 1),
                    depth=0,
                    is_active=True,
                    created_by=1,
                    created_at=datetime.utcnow()
                )
                db.add(dept)
                departments.append(dept)
        
        await db.commit()
        
        # Update department paths
        for dept in departments:
            await db.refresh(dept)
            dept.path = str(dept.id)
        await db.commit()
        
        # Create users
        users = []
        for i, dept in enumerate(departments[:10]):  # First 10 departments
            for k in range(5):  # 5 users per department
                user = User(
                    email=f"user{i:02d}{k:02d}@example.com",
                    first_name=f"User{i:02d}{k:02d}",
                    last_name="Test",
                    full_name=f"User{i:02d}{k:02d} Test",
                    organization_id=dept.organization_id,
                    department_id=dept.id,
                    is_active=True,
                    created_by=1,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                users.append(user)
        
        await db.commit()
        
        # Test performance of API endpoints
        async with AsyncClient(app=app, base_url="http://test") as client:
            import time
            
            # Test organization tree performance
            start_time = time.time()
            tree_response = await client.get(f"/api/v1/organizations/{root_org.id}/tree")
            tree_time = time.time() - start_time
            
            assert tree_response.status_code == 200
            assert tree_time < 2.0  # Should complete within 2 seconds
            
            # Test organization statistics performance
            start_time = time.time()
            stats_response = await client.get(f"/api/v1/organizations/{root_org.id}/stats")
            stats_time = time.time() - start_time
            
            assert stats_response.status_code == 200
            assert stats_time < 1.0  # Should complete within 1 second
            
            # Test user listing performance
            start_time = time.time()
            users_response = await client.get(
                f"/api/v1/user-assignments/organizations/{root_org.id}/users",
                params={"limit": 100}
            )
            users_time = time.time() - start_time
            
            assert users_response.status_code == 200
            assert users_time < 1.5  # Should complete within 1.5 seconds

    async def test_concurrent_hierarchy_operations(self, db: AsyncSession):
        """Test concurrent operations on hierarchy structures."""
        import asyncio
        
        # Create base organization
        org = Organization(
            code="CONCURRENT",
            name="Concurrent Test Organization",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        async def create_department(i):
            """Create a department concurrently."""
            dept = Department(
                code=f"CONC{i:03d}",
                name=f"Concurrent Department {i}",
                organization_id=org.id,
                parent_id=None,
                path=str(i),
                depth=0,
                is_active=True,
                created_by=1,
                created_at=datetime.utcnow()
            )
            db.add(dept)
            await db.commit()
            await db.refresh(dept)
            dept.path = str(dept.id)
            await db.commit()
            return dept
        
        # Create departments concurrently
        tasks = [create_department(i) for i in range(5)]
        departments = await asyncio.gather(*tasks)
        
        # Verify all departments were created successfully
        assert len(departments) == 5
        for dept in departments:
            assert dept.id is not None
            assert dept.organization_id == org.id
        
        # Test concurrent API calls
        async with AsyncClient(app=app, base_url="http://test") as client:
            async def get_stats():
                response = await client.get(f"/api/v1/organizations/{org.id}/stats")
                return response.status_code
            
            # Make concurrent API calls
            concurrent_tasks = [get_stats() for _ in range(10)]
            results = await asyncio.gather(*concurrent_tasks)
            
            # All calls should succeed
            assert all(status == 200 for status in results)

    async def test_data_consistency_after_operations(self, db: AsyncSession):
        """Test data consistency after various hierarchy operations."""
        
        # Create test hierarchy
        org = Organization(
            code="CONSISTENCY",
            name="Consistency Test Organization",
            parent_id=None,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        dept1 = Department(
            code="DEPT1",
            name="Department 1",
            organization_id=org.id,
            parent_id=None,
            path="1",
            depth=0,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(dept1)
        await db.commit()
        await db.refresh(dept1)
        dept1.path = str(dept1.id)
        await db.commit()
        
        dept2 = Department(
            code="DEPT2",
            name="Department 2",
            organization_id=org.id,
            parent_id=dept1.id,
            path=f"{dept1.id}.2",
            depth=1,
            is_active=True,
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(dept2)
        await db.commit()
        await db.refresh(dept2)
        dept2.path = f"{dept1.path}.{dept2.id}"
        await db.commit()
        
        # Test moving department
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Move dept2 to be a root department
            move_response = await client.post(
                f"/api/v1/departments/{dept2.id}/move",
                params={"new_parent_id": None}
            )
            assert move_response.status_code == 200
            
            # Verify the move was successful and data is consistent
            await db.refresh(dept2)
            assert dept2.parent_id is None
            assert dept2.depth == 0
            
            # Test hierarchy validation
            validation_response = await client.get(f"/api/v1/departments/{dept1.id}/validation")
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert validation_data["is_valid"] is True