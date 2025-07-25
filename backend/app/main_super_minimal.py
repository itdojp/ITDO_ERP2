"""
Super Minimal FastAPI App - Core ERP Business Logic
Product and inventory management with no database dependencies
"""

from fastapi import FastAPI
from app.api.v1.simple_products import router as products_router
from app.api.v1.simple_inventory import router as inventory_router

# Create ERP app with essential business functionality
app = FastAPI(
    title="ITDO ERP API - Core Business Logic",
    description="Core ERP functionality for product and inventory management",
    version="v21.0-core-business"
)

# Include core business routers
# app.include_router(products_router, prefix="/api/v1", tags=["products"])  # Temporarily disabled for TDD
# app.include_router(inventory_router, prefix="/api/v1", tags=["inventory"])  # Temporarily disabled for TDD

# Import and include advanced reporting
from app.api.v1.advanced_reports import router as reports_router
app.include_router(reports_router, prefix="/api/v1", tags=["reports"])

# Import and include advanced product management - CC02 v48.0
# from app.api.v1.advanced_product_management import router as advanced_products_router
# app.include_router(advanced_products_router, prefix="/api/v1", tags=["advanced-products"])  # Temporarily disabled for TDD

# Import and include product image management
from app.api.v1.product_image_management import router as image_router
app.include_router(image_router, prefix="/api/v1", tags=["product-images"])

# Import and include product catalog features
from app.api.v1.product_catalog_features import router as catalog_router
app.include_router(catalog_router, prefix="/api/v1", tags=["product-catalog"])

# Import and include inventory management core - CC02 v48.0 Phase 2
# from app.api.v1.inventory_management_core import router as inventory_core_router
# app.include_router(inventory_core_router, prefix="/api/v1", tags=["inventory-core"])  # Temporarily disabled for TDD

# Import and include products endpoints - CC02 v52.0 Business API Implementation
from app.api.v1.endpoints.products import router as products_endpoints_router
app.include_router(products_endpoints_router, prefix="/api/v1", tags=["products-endpoints"])

# Import and include inventory endpoints - CC02 v49.0 Phase 2 (temporarily disabled for v50.0)
# from app.api.v1.endpoints.inventory import router as inventory_endpoints_router
# app.include_router(inventory_endpoints_router, prefix="/api/v1", tags=["inventory-endpoints"])

# Import and include customer endpoints - CC02 v49.0 Phase 3
from app.api.v1.endpoints.customers import router as customers_endpoints_router
app.include_router(customers_endpoints_router, prefix="/api/v1", tags=["customers-endpoints"])

# Import and include order endpoints - CC02 v49.0 Phase 4
from app.api.v1.endpoints.orders import router as orders_endpoints_router
app.include_router(orders_endpoints_router, prefix="/api/v1", tags=["orders-endpoints"])

# Import and include core products endpoints - CC02 v50.0 Core Business API Sprint
from app.api.v1.endpoints.products_core import router as products_core_router
app.include_router(products_core_router, prefix="/api/v1", tags=["core-products"])

# Import and include core inventory endpoints - CC02 v50.0 Phase 2
from app.api.v1.endpoints.inventory_core import router as inventory_core_router
app.include_router(inventory_core_router, prefix="/api/v1", tags=["core-inventory"])

# Import and include core sales endpoints - CC02 v50.0 Phase 3
from app.api.v1.endpoints.sales_core import router as sales_core_router
app.include_router(sales_core_router, prefix="/api/v1", tags=["core-sales"])

# Import and include products v53.0 endpoints - CC02 v53.0 ERP Business API Sprint
from app.api.v1.endpoints.products_v53 import router as products_v53_router
app.include_router(products_v53_router, prefix="/api/v1", tags=["products-v53"])

# Import and include inventory v53.0 endpoints - CC02 v53.0 ERP Business API Sprint Day 3-4
from app.api.v1.endpoints.inventory_v53 import router as inventory_v53_router
app.include_router(inventory_v53_router, prefix="/api/v1", tags=["inventory-v53"])

# Import and include sales v53.0 endpoints - CC02 v53.0 ERP Business API Sprint Day 5-6
from app.api.v1.endpoints.sales_v53 import router as sales_v53_router
app.include_router(sales_v53_router, prefix="/api/v1/sales-v53", tags=["sales-v53"])

# Import and include CRM v53.0 endpoints - CC02 v53.0 ERP Business API Sprint Day 7-8
from app.api.v1.endpoints.crm_v53 import router as crm_v53_router
app.include_router(crm_v53_router, prefix="/api/v1/crm-v53", tags=["crm-v53"])

# Import and include Reporting & Analytics v53.0 endpoints - CC02 v53.0 ERP Business API Sprint Day 9-10
from app.api.v1.endpoints.reports_analytics_v53 import router as reports_v53_router
app.include_router(reports_v53_router, prefix="/api/v1/reports-v53", tags=["reports-v53"])

@app.get("/")
async def root():
    """Root endpoint for core ERP API."""
    return {
        "message": "ITDO ERP API - Core Business Logic",
        "version": "v21.0-core-business",
        "status": "working_over_perfect",
        "available_endpoints": [
            "/api/v1/simple-products/",
            "/api/v1/products/",
            "/api/v1/products-v53/",
            "/api/v1/products-v53/categories/",
            "/api/v1/products-v53/bulk",
            "/api/v1/products-v53/statistics",
            "/api/v1/inventory-v53/locations/",
            "/api/v1/inventory-v53/items/",
            "/api/v1/inventory-v53/adjustments/",
            "/api/v1/inventory-v53/transfers/",
            "/api/v1/inventory-v53/movements/",
            "/api/v1/inventory-v53/statistics",
            "/api/v1/sales-v53/customers/",
            "/api/v1/sales-v53/orders/",
            "/api/v1/sales-v53/payments/",
            "/api/v1/sales-v53/quotes/",
            "/api/v1/sales-v53/statistics",
            "/api/v1/crm-v53/leads/",
            "/api/v1/crm-v53/opportunities/",
            "/api/v1/crm-v53/contacts/",
            "/api/v1/crm-v53/activities/",
            "/api/v1/crm-v53/campaigns/",
            "/api/v1/crm-v53/statistics",
            "/api/v1/reports-v53/reports/",
            "/api/v1/reports-v53/dashboards/",
            "/api/v1/reports-v53/analytics/",
            "/api/v1/reports-v53/kpis/",
            "/api/v1/reports-v53/bi-dashboard",
            "/api/v1/reports-v53/statistics",
            "/api/v1/simple-inventory/items/",
            "/api/v1/simple-inventory/movements/",
            "/api/v1/inventory/locations/",
            "/api/v1/inventory/items/",
            "/api/v1/inventory/movements/",
            "/api/v1/inventory/real-time/",
            "/api/v1/inventory/alerts/",
            "/api/v1/reports/",
            "/health",
            "/test"
        ]
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "ITDO ERP Core Business API",
        "version": "v21.0-core-business",
        "mode": "working_over_perfect"
    }

@app.get("/test")
async def test_endpoint():
    """Basic test endpoint."""
    return {
        "status": "working", 
        "protocol": "v21.0",
        "message": "Core ERP business functionality ready"
    }