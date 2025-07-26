"""
ITDO ERP Backend - Product Management v66 Tests
Comprehensive test suite for product management functionality
Day 8: Product Management Test Implementation
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.v1.product_management_v66 import ProductManagementService
from app.api.v1.product_media_v66 import MediaManagementService
from app.api.v1.product_pricing_v66 import PricingEngine
from app.api.v1.product_search_v66 import ElasticsearchService
from app.main import app


class TestProductManagement:
    """Test product management core functionality"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_db(self):
        with patch("app.core.database.get_db") as mock:
            yield mock

    @pytest.fixture
    def mock_redis(self):
        with patch("aioredis.from_url") as mock:
            redis_client = AsyncMock()
            mock.return_value = redis_client
            yield redis_client

    async def test_create_product_category(self, async_client, mock_db, mock_redis):
        """Test product category creation"""
        category_data = {
            "name": "Electronics",
            "description": "Electronic products",
            "parent_id": None,
            "sort_order": 1,
            "is_active": True,
        }

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_category"
        ) as mock_create:
            mock_create.return_value = Mock(
                id=uuid.uuid4(),
                name="Electronics",
                slug="electronics",
                description="Electronic products",
                is_active=True,
            )

            response = await async_client.post(
                "/api/v1/products/categories", json=category_data
            )
            assert response.status_code == 200

            result = response.json()
            assert result["name"] == "Electronics"
            assert result["slug"] == "electronics"
            assert result["is_active"] is True

    async def test_create_brand(self, async_client, mock_db, mock_redis):
        """Test brand creation"""
        brand_data = {
            "name": "Apple",
            "description": "Apple Inc. products",
            "website": "https://apple.com",
            "is_active": True,
        }

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_brand"
        ) as mock_create:
            mock_create.return_value = Mock(
                id=uuid.uuid4(),
                name="Apple",
                slug="apple",
                description="Apple Inc. products",
                is_active=True,
            )

            response = await async_client.post(
                "/api/v1/products/brands", json=brand_data
            )
            assert response.status_code == 200

            result = response.json()
            assert result["name"] == "Apple"
            assert result["slug"] == "apple"

    async def test_create_product(self, async_client, mock_db, mock_redis):
        """Test product creation"""
        product_data = {
            "sku": "IPHONE-13-PRO",
            "name": "iPhone 13 Pro",
            "description": "Latest iPhone with Pro features",
            "base_price": 999.99,
            "inventory_quantity": 100,
            "status": "active",
            "is_visible": True,
        }

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_product"
        ) as mock_create:
            mock_create.return_value = Mock(
                id=uuid.uuid4(),
                sku="IPHONE-13-PRO",
                name="iPhone 13 Pro",
                slug="iphone-13-pro",
                base_price=Decimal("999.99"),
                status="active",
            )

            response = await async_client.post("/api/v1/products/", json=product_data)
            assert response.status_code == 200

            result = response.json()
            assert result["sku"] == "IPHONE-13-PRO"
            assert result["name"] == "iPhone 13 Pro"

    async def test_search_products(self, async_client, mock_db, mock_redis):
        """Test product search functionality"""
        search_params = {"query": "iPhone", "category_id": None, "page": 1, "size": 20}

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.search_products"
        ) as mock_search:
            mock_search.return_value = {
                "products": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "iPhone 13 Pro",
                        "price": 999.99,
                        "category": {"name": "Smartphones"},
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1,
            }

            response = await async_client.get(
                "/api/v1/products/search", params=search_params
            )
            assert response.status_code == 200

            result = response.json()
            assert result["total"] == 1
            assert len(result["products"]) == 1
            assert "iPhone" in result["products"][0]["name"]

    async def test_update_inventory(self, async_client, mock_db, mock_redis):
        """Test inventory update functionality"""
        product_id = uuid.uuid4()
        inventory_data = {
            "quantity_change": -5,
            "change_type": "sale",
            "reason": "Product sold",
        }

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.update_inventory"
        ) as mock_update:
            mock_update.return_value = {
                "product_id": product_id,
                "old_quantity": 100,
                "quantity_change": -5,
                "new_quantity": 95,
                "low_stock_alert": False,
            }

            response = await async_client.post(
                f"/api/v1/products/{product_id}/inventory", params=inventory_data
            )
            assert response.status_code == 200

            result = response.json()
            assert result["old_quantity"] == 100
            assert result["new_quantity"] == 95
            assert result["quantity_change"] == -5


class TestProductPricing:
    """Test product pricing functionality"""

    @pytest.fixture
    def pricing_engine(self, mock_db, mock_redis):
        return PricingEngine(mock_db, mock_redis)

    async def test_calculate_product_price(self, pricing_engine):
        """Test product price calculation"""
        product_id = uuid.uuid4()
        customer_id = uuid.uuid4()

        with patch.object(pricing_engine.db, "execute") as mock_execute:
            # Mock base price query
            mock_execute.return_value.fetchone.return_value = Mock(
                base_price=Decimal("100.00"),
                compare_at_price=None,
                cost_price=Decimal("60.00"),
            )

            result = await pricing_engine.calculate_product_price(
                product_id=product_id, customer_id=customer_id, quantity=2
            )

            assert result.product_id == product_id
            assert result.base_price == Decimal("100.00")
            assert result.final_price <= result.base_price

    async def test_bulk_pricing_calculation(self, pricing_engine):
        """Test bulk pricing calculation"""
        items = [
            Mock(product_id=uuid.uuid4(), quantity=5, customer_id=None),
            Mock(product_id=uuid.uuid4(), quantity=3, customer_id=None),
        ]

        with patch.object(pricing_engine, "calculate_product_price") as mock_calc:
            mock_calc.return_value = Mock(
                final_price=Decimal("95.00"), total_discount=Decimal("5.00")
            )

            result = await pricing_engine.calculate_bulk_pricing(items)

            assert len(result.products) == len(items)
            assert result.total_amount > 0
            assert result.total_discount >= 0

    async def test_discount_application(self, pricing_engine):
        """Test discount application logic"""
        discount = {
            "discount_type": "percentage",
            "discount_value": "10",
            "max_discount_amount": None,
        }

        current_price = Decimal("100.00")
        quantity = 1

        discount_amount = await pricing_engine._calculate_discount_amount(
            discount, current_price, quantity
        )

        assert discount_amount == Decimal("10.00")

    async def test_pricing_rule_evaluation(self, pricing_engine):
        """Test pricing rule evaluation"""
        rule = Mock(
            conditions={
                "quantity": {"min": 2},
                "products": {"include": ["product-123"]},
            }
        )

        product_id = uuid.uuid4()
        customer_id = None
        quantity = 3

        result = await pricing_engine._evaluate_rule_conditions(
            rule, product_id, customer_id, quantity
        )

        # Should evaluate conditions properly
        assert isinstance(result, bool)


class TestProductMedia:
    """Test product media management"""

    @pytest.fixture
    def media_service(self, mock_db, mock_redis):
        return MediaManagementService(mock_db, mock_redis)

    async def test_file_upload_validation(self, media_service):
        """Test file upload validation"""
        # Mock file that's too large
        large_file = Mock()
        large_file.filename = "large_image.jpg"
        large_file.content_type = "image/jpeg"
        large_file.read = AsyncMock(return_value=b"x" * (200 * 1024 * 1024))  # 200MB

        with pytest.raises(Exception):  # Should raise file too large error
            await media_service._validate_upload(large_file)

    async def test_media_type_determination(self, media_service):
        """Test media type determination from MIME type"""
        assert media_service._determine_media_type("image/jpeg") == "image"
        assert media_service._determine_media_type("video/mp4") == "video"
        assert media_service._determine_media_type("application/pdf") == "document"

    async def test_image_processing(self, media_service):
        """Test image processing functionality"""
        media_file = Mock(
            id=uuid.uuid4(),
            filename="test_image.jpg",
            file_path="uploads/test_image.jpg",
            media_type="image",
        )

        with patch("PIL.Image.open") as mock_image:
            mock_img = Mock()
            mock_img.size = (1920, 1080)
            mock_img.format = "JPEG"
            mock_img.mode = "RGB"
            mock_image.return_value.__enter__.return_value = mock_img

            result = await media_service.processing_service.process_image(media_file)

            assert result["status"] == "success"
            assert "variants_created" in result

    async def test_media_search(self, media_service):
        """Test media search functionality"""
        filters = Mock(
            media_type="image", processing_status="completed", access_level="public"
        )

        with patch.object(media_service.db, "execute") as mock_execute:
            mock_execute.return_value.scalar.return_value = 10  # Total count
            mock_execute.return_value.scalars.return_value.all.return_value = [
                Mock(
                    id=uuid.uuid4(),
                    filename="image1.jpg",
                    media_type="image",
                    variants=[],
                )
            ]

            result = await media_service.search_media(filters, page=1, size=20)

            assert result["total"] == 10
            assert len(result["media_files"]) == 1


class TestProductSearch:
    """Test product search functionality"""

    @pytest.fixture
    def search_service(self, mock_db, mock_redis):
        with patch("elasticsearch.AsyncElasticsearch") as mock_es:
            service = ElasticsearchService(mock_db, mock_redis)
            service.es = mock_es.return_value
            return service

    async def test_elasticsearch_query_building(self, search_service):
        """Test Elasticsearch query building"""
        request = Mock(
            query="iPhone",
            scope="all",
            filters={"category_id": "electronics"},
            sort="relevance",
            include_facets=True,
            highlight=True,
        )

        query = await search_service._build_search_query(request)

        assert "query" in query
        assert "bool" in query["query"]
        assert "must" in query["query"]["bool"]
        assert "filter" in query["query"]["bool"]

    async def test_search_execution(self, search_service):
        """Test search execution"""
        request = Mock(
            query="iPhone",
            page=1,
            size=20,
            include_facets=True,
            include_suggestions=True,
            highlight=True,
        )

        # Mock Elasticsearch response
        mock_response = {
            "hits": {
                "total": {"value": 5},
                "hits": [
                    {
                        "_source": {
                            "id": str(uuid.uuid4()),
                            "name": "iPhone 13",
                            "price": 999.99,
                        },
                        "_score": 1.5,
                    }
                ],
            },
            "aggregations": {},
        }

        search_service.es.search = AsyncMock(return_value=mock_response)

        result = await search_service.search_products(request)

        assert result.total == 5
        assert len(result.products) == 1
        assert result.products[0]["name"] == "iPhone 13"

    async def test_autocomplete_functionality(self, search_service):
        """Test autocomplete functionality"""
        request = Mock(query="iPh", size=5, categories=None)

        mock_response = {
            "suggest": {
                "product_suggest": [
                    {
                        "options": [
                            {
                                "_source": {
                                    "id": str(uuid.uuid4()),
                                    "name": "iPhone 13",
                                    "suggest": {"input": ["iPhone 13", "iPhone"]},
                                },
                                "_score": 1.0,
                            }
                        ]
                    }
                ]
            }
        }

        search_service.es.search = AsyncMock(return_value=mock_response)

        result = await search_service.autocomplete(request)

        assert result.query == "iPh"
        assert len(result.suggestions) > 0

    async def test_facet_processing(self, search_service):
        """Test facet processing"""
        aggregations = {
            "categories": {
                "buckets": [
                    {"key": "Electronics", "doc_count": 15},
                    {"key": "Clothing", "doc_count": 8},
                ]
            },
            "brands": {
                "values": {
                    "buckets": [
                        {"key": "Apple", "doc_count": 12},
                        {"key": "Samsung", "doc_count": 7},
                    ]
                }
            },
        }

        facets = await search_service._process_facets(aggregations)

        assert "categories" in facets
        assert "brands" in facets
        assert len(facets["categories"]) == 2
        assert facets["categories"][0]["value"] == "Electronics"
        assert facets["categories"][0]["count"] == 15

    async def test_product_recommendations(self, search_service):
        """Test product recommendations"""
        request = Mock(
            product_id=uuid.uuid4(),
            recommendation_type="related",
            size=5,
            exclude_ids=[],
        )

        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "id": str(uuid.uuid4()),
                            "name": "Related Product",
                            "price": 799.99,
                        },
                        "_score": 1.2,
                    }
                ]
            }
        }

        search_service.es.search = AsyncMock(return_value=mock_response)

        with patch.object(search_service.db, "execute") as mock_execute:
            mock_execute.return_value.fetchone.return_value = Mock(
                category_id=uuid.uuid4(),
                brand_id=uuid.uuid4(),
                tags=["smartphone", "apple"],
            )

            recommendations = await search_service.get_recommendations(request)

            assert len(recommendations) == 1
            assert recommendations[0]["name"] == "Related Product"


class TestProductInventory:
    """Test product inventory management"""

    async def test_inventory_tracking(self, async_client, mock_db):
        """Test inventory level tracking"""
        product_id = uuid.uuid4()

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.update_inventory"
        ) as mock_update:
            mock_update.return_value = {
                "product_id": product_id,
                "old_quantity": 50,
                "quantity_change": -10,
                "new_quantity": 40,
                "low_stock_alert": False,
            }

            response = await async_client.post(
                f"/api/v1/products/{product_id}/inventory",
                params={
                    "quantity_change": -10,
                    "change_type": "sale",
                    "reason": "Order fulfillment",
                },
            )

            assert response.status_code == 200
            result = response.json()
            assert result["new_quantity"] == 40

    async def test_low_stock_alert(self, mock_db, mock_redis):
        """Test low stock alert generation"""
        service = ProductManagementService(mock_db, mock_redis)

        with patch.object(service.db, "execute") as mock_execute:
            # Mock product with low stock threshold
            mock_product = Mock(
                id=uuid.uuid4(),
                inventory_quantity=5,
                low_stock_threshold=10,
                track_inventory=True,
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_product

            result = await service.update_inventory(
                product_id=mock_product.id,
                quantity_change=-2,
                change_type="sale",
                reason="Order fulfillment",
            )

            assert result["low_stock_alert"] is True
            assert result["new_quantity"] == 3  # 5 - 2


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""

    async def test_complete_product_workflow(self, async_client, mock_db, mock_redis):
        """Test complete product creation to search workflow"""
        # 1. Create category
        category_data = {"name": "Smartphones", "description": "Mobile phones"}

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_category"
        ) as mock_create_cat:
            mock_category = Mock(
                id=uuid.uuid4(), name="Smartphones", slug="smartphones"
            )
            mock_create_cat.return_value = mock_category

            cat_response = await async_client.post(
                "/api/v1/products/categories", json=category_data
            )
            assert cat_response.status_code == 200
            category_id = mock_category.id

        # 2. Create brand
        brand_data = {"name": "Apple", "description": "Apple Inc."}

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_brand"
        ) as mock_create_brand:
            mock_brand = Mock(id=uuid.uuid4(), name="Apple", slug="apple")
            mock_create_brand.return_value = mock_brand

            brand_response = await async_client.post(
                "/api/v1/products/brands", json=brand_data
            )
            assert brand_response.status_code == 200
            brand_id = mock_brand.id

        # 3. Create product
        product_data = {
            "sku": "IPHONE-14-PRO",
            "name": "iPhone 14 Pro",
            "category_id": str(category_id),
            "brand_id": str(brand_id),
            "base_price": 1099.99,
            "inventory_quantity": 50,
        }

        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.create_product"
        ) as mock_create_prod:
            mock_product = Mock(
                id=uuid.uuid4(),
                sku="IPHONE-14-PRO",
                name="iPhone 14 Pro",
                base_price=Decimal("1099.99"),
            )
            mock_create_prod.return_value = mock_product

            prod_response = await async_client.post(
                "/api/v1/products/", json=product_data
            )
            assert prod_response.status_code == 200

        # 4. Search for product
        with patch(
            "app.api.v1.product_management_v66.ProductManagementService.search_products"
        ) as mock_search:
            mock_search.return_value = {
                "products": [{"id": str(mock_product.id), "name": "iPhone 14 Pro"}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1,
            }

            search_response = await async_client.get(
                "/api/v1/products/search", params={"query": "iPhone"}
            )
            assert search_response.status_code == 200

            search_result = search_response.json()
            assert search_result["total"] == 1
            assert "iPhone" in search_result["products"][0]["name"]

    async def test_pricing_with_discounts_workflow(self, async_client, mock_db):
        """Test pricing calculation with discounts"""
        # Create discount
        discount_data = {
            "code": "SAVE10",
            "name": "10% Off Everything",
            "discount_type": "percentage",
            "discount_scope": "global",
            "discount_value": 10.0,
            "valid_from": datetime.utcnow().isoformat(),
            "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }

        with patch("app.api.v1.product_pricing_v66.Discount") as mock_discount_model:
            mock_discount_model.return_value = Mock(id=uuid.uuid4(), code="SAVE10")

            discount_response = await async_client.post(
                "/api/v1/pricing/discounts", json=discount_data
            )
            assert discount_response.status_code == 200

        # Calculate price with discount
        price_request = {
            "product_id": str(uuid.uuid4()),
            "quantity": 2,
            "discount_codes": ["SAVE10"],
        }

        with patch(
            "app.api.v1.product_pricing_v66.PricingEngine.calculate_product_price"
        ) as mock_calc:
            mock_calc.return_value = Mock(
                product_id=uuid.uuid4(),
                base_price=Decimal("100.00"),
                final_price=Decimal("90.00"),
                total_discount=Decimal("10.00"),
                discount_percentage=Decimal("10.00"),
                applied_discounts=[
                    {
                        "type": "coupon",
                        "name": "10% Off Everything",
                        "discount_amount": 10.0,
                    }
                ],
            )

            price_response = await async_client.post(
                "/api/v1/pricing/calculate", json=price_request
            )
            assert price_response.status_code == 200

            price_result = price_response.json()
            assert price_result["final_price"] < price_result["base_price"]
            assert len(price_result["applied_discounts"]) > 0


# Performance and Load Tests
class TestPerformance:
    """Test performance characteristics"""

    async def test_search_performance(self, async_client):
        """Test search response time under load"""
        import time

        search_params = {"query": "test", "size": 20}

        with patch(
            "app.api.v1.product_search_v66.ElasticsearchService.search_products"
        ) as mock_search:
            mock_search.return_value = Mock(
                total=100,
                products=[
                    {"id": str(uuid.uuid4()), "name": f"Product {i}"} for i in range(20)
                ],
                execution_time_ms=45,
            )

            start_time = time.time()
            response = await async_client.post("/api/v1/search/", json=search_params)
            end_time = time.time()

            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Should respond within 1 second

    async def test_bulk_operations_performance(self, async_client):
        """Test bulk operations performance"""
        # Test bulk price calculation
        items = [
            {"product_id": str(uuid.uuid4()), "quantity": i}
            for i in range(1, 51)  # 50 items
        ]

        with patch(
            "app.api.v1.product_pricing_v66.PricingEngine.calculate_bulk_pricing"
        ) as mock_bulk:
            mock_bulk.return_value = Mock(
                products=[Mock(final_price=Decimal("10.00")) for _ in items],
                total_amount=Decimal("500.00"),
                total_discount=Decimal("50.00"),
            )

            response = await async_client.post(
                "/api/v1/pricing/calculate-bulk", json=items
            )
            assert response.status_code == 200

            result = response.json()
            assert len(result["products"]) == 50


# Test execution and coverage reporting
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app.api.v1.product_management_v66",
            "--cov=app.api.v1.product_pricing_v66",
            "--cov=app.api.v1.product_media_v66",
            "--cov=app.api.v1.product_search_v66",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ]
    )
