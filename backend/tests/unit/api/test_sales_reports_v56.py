"""
Tests for CC02 v56.0 Sales Reports API
Unit tests for sales analytics and reporting functionality
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.sales_reports_v56 import (
    ReportPeriod, ReportType, SalesAnalyticsService,
    SalesReportRequest, ProductPerformanceItem, CustomerSegmentItem
)
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product, ProductCategory
from app.models.user import User

# Test Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def analytics_service(mock_db_session):
    """Create analytics service with mocked database"""
    return SalesAnalyticsService(mock_db_session)

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return [
        {
            'id': uuid4(),
            'customer_id': uuid4(),
            'order_date': date(2024, 1, 15),
            'total_amount': Decimal('1250.00'),
            'status': 'completed'
        },
        {
            'id': uuid4(),
            'customer_id': uuid4(),
            'order_date': date(2024, 1, 20),
            'total_amount': Decimal('890.50'),
            'status': 'completed'
        }
    ]

@pytest.fixture
def sample_product_data():
    """Sample product performance data"""
    return [
        {
            'id': uuid4(),
            'name': 'Premium Widget',
            'sku': 'PWD-001',
            'category_name': 'Electronics',
            'revenue': Decimal('15000.00'),
            'quantity_sold': 150,
            'orders_count': 45,
            'average_price': Decimal('100.00')
        },
        {
            'id': uuid4(),
            'name': 'Standard Widget',
            'sku': 'SWD-002',
            'category_name': 'Electronics',
            'revenue': Decimal('8500.00'),
            'quantity_sold': 200,
            'orders_count': 60,
            'average_price': Decimal('42.50')
        }
    ]

# Unit Tests for SalesAnalyticsService
class TestSalesAnalyticsService:
    
    @pytest.mark.asyncio
    async def test_generate_revenue_summary_success(self, analytics_service, mock_db_session):
        """Test successful revenue summary generation"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_revenue=Decimal('25000.00'),
            total_orders=150,
            total_quantity=500,
            average_order_value=Decimal('166.67')
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service.generate_revenue_summary(start_date, end_date)
        
        # Assertions
        assert result['total_revenue'] == Decimal('25000.00')
        assert result['total_orders'] == 150
        assert result['total_quantity'] == 500
        assert result['average_order_value'] == Decimal('166.67')
        assert 'conversion_rate' in result
        
        # Verify database was called
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_revenue_summary_with_filters(self, analytics_service, mock_db_session):
        """Test revenue summary with filters applied"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_revenue=Decimal('15000.00'),
            total_orders=75,
            total_quantity=250,
            average_order_value=Decimal('200.00')
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute test with filters
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        filters = {
            'customer_ids': [uuid4(), uuid4()],
            'product_categories': [uuid4()]
        }
        
        result = await analytics_service.generate_revenue_summary(start_date, end_date, filters)
        
        # Assertions
        assert result['total_revenue'] == Decimal('15000.00')
        assert result['total_orders'] == 75
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_performance_success(self, analytics_service, mock_db_session, sample_product_data):
        """Test successful product performance retrieval"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_products = []
        for product_data in sample_product_data:
            mock_product = MagicMock()
            for key, value in product_data.items():
                setattr(mock_product, key, value)
            mock_products.append(mock_product)
        
        mock_result.all.return_value = mock_products
        mock_db_session.execute.return_value = mock_result
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service.get_product_performance(start_date, end_date, top_n=10)
        
        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], ProductPerformanceItem)
        assert result[0].product_name == 'Premium Widget'
        assert result[0].revenue == Decimal('15000.00')
        assert result[1].product_name == 'Standard Widget'
        
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_customer_analysis_success(self, analytics_service, mock_db_session):
        """Test successful customer analysis"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_segments = [
            MagicMock(
                segment='High Value',
                customer_count=25,
                total_revenue=Decimal('50000.00'),
                total_orders=150
            ),
            MagicMock(
                segment='Medium Value', 
                customer_count=75,
                total_revenue=Decimal('30000.00'),
                total_orders=200
            )
        ]
        mock_result.all.return_value = mock_segments
        mock_db_session.execute.return_value = mock_result
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service.get_customer_analysis(start_date, end_date)
        
        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], CustomerSegmentItem)
        assert result[0].segment == 'High Value'
        assert result[0].customer_count == 25
        assert result[0].total_revenue == Decimal('50000.00')
        
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trend_analysis_monthly(self, analytics_service, mock_db_session):
        """Test trend analysis with monthly aggregation"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_trends = [
            MagicMock(
                period_start=date(2024, 1, 1),
                revenue=Decimal('20000.00'),
                orders_count=100,
                avg_order_value=Decimal('200.00')
            ),
            MagicMock(
                period_start=date(2024, 2, 1),
                revenue=Decimal('22000.00'),
                orders_count=110,
                avg_order_value=Decimal('200.00')
            )
        ]
        mock_result.all.return_value = mock_trends
        mock_db_session.execute.return_value = mock_result
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 2, 28)
        
        result = await analytics_service.get_trend_analysis(start_date, end_date, ReportPeriod.MONTHLY)
        
        # Assertions
        assert len(result) == 2
        assert result[0]['revenue'] == 20000.00
        assert result[1]['revenue'] == 22000.00
        assert result[1]['growth_rate'] == 10.0  # (22000-20000)/20000 * 100
        
        mock_db_session.execute.assert_called_once()

# Integration-style tests for API endpoints
class TestSalesReportsAPI:
    
    def test_sales_report_request_validation(self):
        """Test sales report request validation"""
        
        # Valid request
        valid_request = SalesReportRequest(
            report_type=ReportType.REVENUE_SUMMARY,
            period=ReportPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert valid_request.report_type == ReportType.REVENUE_SUMMARY
        assert valid_request.period == ReportPeriod.MONTHLY
        
        # Test date validation - end_date before start_date should fail
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            SalesReportRequest(
                report_type=ReportType.REVENUE_SUMMARY,
                period=ReportPeriod.MONTHLY,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)  # Invalid: before start_date
            )
        
        # Test date range too large
        with pytest.raises(ValueError, match="date range cannot exceed 365 days"):
            SalesReportRequest(
                report_type=ReportType.REVENUE_SUMMARY,
                period=ReportPeriod.MONTHLY,
                start_date=date(2023, 1, 1),
                end_date=date(2024, 12, 31)  # Invalid: > 365 days
            )

    def test_product_performance_item_creation(self):
        """Test ProductPerformanceItem model creation"""
        
        product_id = uuid4()
        item = ProductPerformanceItem(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-001",
            category_name="Test Category",
            revenue=Decimal('1500.00'),
            quantity_sold=50,
            orders_count=25,
            average_price=Decimal('30.00')
        )
        
        assert item.product_id == product_id
        assert item.product_name == "Test Product"
        assert item.revenue == Decimal('1500.00')
        assert item.quantity_sold == 50

    def test_customer_segment_item_creation(self):
        """Test CustomerSegmentItem model creation"""
        
        segment = CustomerSegmentItem(
            segment="High Value",
            customer_count=100,
            total_revenue=Decimal('50000.00'),
            average_revenue_per_customer=Decimal('500.00'),
            average_order_frequency=2.5
        )
        
        assert segment.segment == "High Value"
        assert segment.customer_count == 100
        assert segment.total_revenue == Decimal('50000.00')
        assert segment.average_order_frequency == 2.5

    def test_report_period_enum(self):
        """Test ReportPeriod enum values"""
        
        assert ReportPeriod.DAILY == "daily"
        assert ReportPeriod.WEEKLY == "weekly"
        assert ReportPeriod.MONTHLY == "monthly"
        assert ReportPeriod.QUARTERLY == "quarterly"
        assert ReportPeriod.YEARLY == "yearly"
        assert ReportPeriod.CUSTOM == "custom"

    def test_report_type_enum(self):
        """Test ReportType enum values"""
        
        assert ReportType.REVENUE_SUMMARY == "revenue_summary"
        assert ReportType.PRODUCT_PERFORMANCE == "product_performance"
        assert ReportType.CUSTOMER_ANALYSIS == "customer_analysis"
        assert ReportType.REGIONAL_COMPARISON == "regional_comparison"
        assert ReportType.TREND_ANALYSIS == "trend_analysis"
        assert ReportType.SALES_FUNNEL == "sales_funnel"

# Performance Tests
class TestSalesReportsPerformance:
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, analytics_service, mock_db_session):
        """Test handling of large datasets"""
        
        # Mock large dataset result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_revenue=Decimal('1000000.00'),
            total_orders=10000,
            total_quantity=50000,
            average_order_value=Decimal('100.00')
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute test with wide date range
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = await analytics_service.generate_revenue_summary(start_date, end_date)
        
        # Assertions
        assert result['total_revenue'] == Decimal('1000000.00')
        assert result['total_orders'] == 10000
        
        # Verify single database call (performance optimization)
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio 
    async def test_concurrent_report_generation(self, analytics_service, mock_db_session):
        """Test concurrent report generation"""
        
        # Mock database result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_revenue=Decimal('5000.00'),
            total_orders=50,
            total_quantity=150,
            average_order_value=Decimal('100.00')
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute multiple concurrent requests
        import asyncio
        
        tasks = []
        for i in range(5):
            start_date = date(2024, i+1, 1)
            end_date = date(2024, i+1, 28)
            task = analytics_service.generate_revenue_summary(start_date, end_date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Assertions
        assert len(results) == 5
        for result in results:
            assert 'total_revenue' in result
            assert 'total_orders' in result
        
        # Verify all database calls were made
        assert mock_db_session.execute.call_count == 5

# Error Handling Tests
class TestSalesReportsErrorHandling:
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, analytics_service, mock_db_session):
        """Test handling of database errors"""
        
        # Mock database exception
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        with pytest.raises(Exception, match="Database connection failed"):
            await analytics_service.generate_revenue_summary(start_date, end_date)

    @pytest.mark.asyncio
    async def test_empty_result_handling(self, analytics_service, mock_db_session):
        """Test handling of empty results"""
        
        # Mock empty database result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_revenue=None,
            total_orders=None,
            total_quantity=None,
            average_order_value=None
        )
        mock_db_session.execute.return_value = mock_result
        
        # Execute test
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = await analytics_service.generate_revenue_summary(start_date, end_date)
        
        # Assertions - should handle None values gracefully
        assert result['total_revenue'] == Decimal('0')
        assert result['total_orders'] == 0
        assert result['total_quantity'] == 0
        assert result['average_order_value'] == Decimal('0')

if __name__ == "__main__":
    pytest.main([__file__])