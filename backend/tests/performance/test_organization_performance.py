"""Performance tests for Organization Service."""

import time
import pytest
from typing import List
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.services.organization import OrganizationService
from tests.factories import OrganizationFactory, DepartmentFactory, UserFactory


class TestOrganizationPerformance:
    """Performance tests for Organization Service operations."""

    @pytest.fixture
    def organization_service(self, db_session: Session):
        """Organization service fixture."""
        return OrganizationService(db_session)

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Test user for audit fields."""
        return UserFactory.create(db_session, email="perf_test@example.com")

    @pytest.fixture
    def sample_organizations(self, db_session: Session) -> List[Organization]:
        """Create multiple organizations for performance testing."""
        organizations = []
        for i in range(100):
            org = OrganizationFactory.create(
                db_session,
                code=f"PERF-ORG-{i:03d}",
                name=f"Performance Test Organization {i+1}",
                industry="IT" if i % 2 == 0 else "Finance"
            )
            organizations.append(org)
        return organizations

    def test_list_organizations_performance(
        self,
        organization_service: OrganizationService,
        sample_organizations: List[Organization]
    ):
        """Test performance of listing organizations with pagination."""
        # Test various page sizes
        page_sizes = [10, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            organizations, total = organization_service.list_organizations(
                skip=0,
                limit=page_size
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 0.5  # Should complete within 500ms
            assert len(organizations) <= page_size
            assert total >= len(sample_organizations)
            
            print(f"List {page_size} organizations: {execution_time:.3f}s")

    def test_search_organizations_performance(
        self,
        organization_service: OrganizationService,
        sample_organizations: List[Organization]
    ):
        """Test performance of organization search."""
        search_queries = ["Performance", "IT", "001", "Finance"]
        
        for query in search_queries:
            start_time = time.time()
            
            results, total = organization_service.search_organizations(
                query=query,
                skip=0,
                limit=50
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 0.3  # Should complete within 300ms
            assert total >= 0
            
            print(f"Search '{query}': {execution_time:.3f}s, {total} results")

    def test_organization_tree_performance(
        self,
        db_session: Session,
        organization_service: OrganizationService
    ):
        """Test performance of organization tree generation."""
        # Create hierarchical structure
        root_orgs = []
        for i in range(5):  # 5 root organizations
            root = OrganizationFactory.create(
                db_session,
                code=f"ROOT-{i:02d}",
                name=f"Root Organization {i+1}"
            )
            root_orgs.append(root)
            
            # Create 3 levels of subsidiaries
            for j in range(3):  # 3 subsidiaries per root
                level1 = OrganizationFactory.create(
                    db_session,
                    code=f"L1-{i:02d}-{j:02d}",
                    name=f"Level 1 Subsidiary {i+1}-{j+1}",
                    parent_id=root.id
                )
                
                for k in range(2):  # 2 subsidiaries per level 1
                    OrganizationFactory.create(
                        db_session,
                        code=f"L2-{i:02d}-{j:02d}-{k:02d}",
                        name=f"Level 2 Subsidiary {i+1}-{j+1}-{k+1}",
                        parent_id=level1.id
                    )
        
        start_time = time.time()
        
        tree = organization_service.get_organization_tree()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 1.0  # Should complete within 1 second
        assert len(tree) == 5  # 5 root organizations
        
        # Verify tree structure
        for root_node in tree:
            assert len(root_node.children) == 3
            for child in root_node.children:
                assert len(child.children) == 2
        
        print(f"Organization tree generation: {execution_time:.3f}s")

    def test_bulk_organization_creation_performance(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        test_user
    ):
        """Test performance of bulk organization creation."""
        organization_count = 50
        
        start_time = time.time()
        
        created_organizations = []
        for i in range(organization_count):
            org_data = OrganizationFactory.build_create_schema(
                code=f"BULK-{i:03d}",
                name=f"Bulk Created Organization {i+1}"
            )
            
            org = organization_service.create_organization(
                org_data,
                created_by=test_user.id
            )
            created_organizations.append(org)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(created_organizations) == organization_count
        
        avg_time_per_org = execution_time / organization_count
        assert avg_time_per_org < 0.1  # Average < 100ms per organization
        
        print(f"Bulk creation of {organization_count} organizations: {execution_time:.3f}s")
        print(f"Average time per organization: {avg_time_per_org:.3f}s")

    def test_organization_statistics_performance(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        sample_organizations: List[Organization]
    ):
        """Test performance of organization statistics calculation."""
        # Add departments and users to some organizations
        for i, org in enumerate(sample_organizations[:10]):
            # Add departments
            for j in range(5):
                DepartmentFactory.create(
                    db_session,
                    organization_id=org.id,
                    code=f"DEPT-{i:02d}-{j:02d}",
                    name=f"Department {j+1}"
                )
        
        # Test statistics calculation performance
        test_orgs = sample_organizations[:5]
        
        start_time = time.time()
        
        for org in test_orgs:
            stats = organization_service.get_organization_statistics(org.id)
            assert "department_count" in stats
            assert "user_count" in stats
            assert "active_subsidiaries" in stats
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 2.0  # Should complete within 2 seconds
        
        avg_time_per_stat = execution_time / len(test_orgs)
        assert avg_time_per_stat < 0.4  # Average < 400ms per statistics calculation
        
        print(f"Statistics for {len(test_orgs)} organizations: {execution_time:.3f}s")
        print(f"Average time per statistics: {avg_time_per_stat:.3f}s")

    def test_concurrent_organization_operations(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        test_user
    ):
        """Test performance under rapid sequential operations (simulating concurrent load)."""
        start_time = time.time()
        
        # Simulate rapid operations
        total_operations = 15
        created_organizations = []
        errors = []
        
        for i in range(total_operations):
            try:
                org_data = OrganizationFactory.build_create_schema(
                    code=f"RAPID-{i:03d}",
                    name=f"Rapid Test Org {i + 1}"
                )
                
                org = organization_service.create_organization(
                    org_data,
                    created_by=test_user.id
                )
                created_organizations.append(org)
            except Exception as e:
                errors.append(f"Error: {e}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 10.0  # Should complete within 10 seconds
        
        success_count = len(created_organizations)
        success_rate = success_count / total_operations
        assert success_rate >= 0.8  # At least 80% success rate
        
        print(f"Rapid sequential operations ({total_operations} total): {execution_time:.3f}s")
        print(f"Success rate: {success_rate:.2%}")
        if errors:
            print(f"Errors: {errors[:3]}...")  # Show first 3 errors only

    def test_memory_usage_large_dataset(
        self,
        organization_service: OrganizationService,
        sample_organizations: List[Organization]
    ):
        """Test memory efficiency with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform operations that might consume memory
        start_time = time.time()
        
        # Large pagination test
        for skip in range(0, len(sample_organizations), 20):
            organizations, total = organization_service.list_organizations(
                skip=skip,
                limit=20
            )
        
        # Search operations
        for i in range(10):
            results, total = organization_service.search_organizations(
                query="Test",
                skip=0,
                limit=50
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Measure final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Performance assertions
        assert execution_time < 3.0  # Should complete within 3 seconds
        assert memory_increase < 50  # Memory increase should be < 50MB
        
        print(f"Large dataset operations: {execution_time:.3f}s")
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")

    def test_database_query_efficiency(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        sample_organizations: List[Organization]
    ):
        """Test database query efficiency and N+1 problem detection."""
        # Enable SQL query logging for this test
        import logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        
        query_count = 0
        original_execute = db_session.execute
        
        def counting_execute(*args, **kwargs):
            nonlocal query_count
            query_count += 1
            return original_execute(*args, **kwargs)
        
        db_session.execute = counting_execute
        
        try:
            start_time = time.time()
            
            # Test operations that might cause N+1 queries
            organizations, total = organization_service.list_organizations(
                skip=0,
                limit=50
            )
            
            # Get organization summaries (should not cause N+1)
            for org in organizations[:10]:
                summary = organization_service.get_organization_summary(org)
                assert summary.id == org.id
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 1.0  # Should complete within 1 second
            # Allow for reasonable number of queries, but prevent N+1
            assert query_count < 50  # Should not exceed 50 queries for this operation
            
            print(f"Database efficiency test: {execution_time:.3f}s, {query_count} queries")
            
        finally:
            # Restore original execute method
            db_session.execute = original_execute
            logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)