"""
Product Catalog Features API - CC02 v48.0
Bulk import/export, product duplication, and catalog management
TDD implementation with comprehensive validation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import uuid
import json
import csv
import io
import zipfile
import tempfile
from pathlib import Path

# Import product stores and models
from app.api.v1.simple_products import products_store
from app.api.v1.advanced_product_management import (
    advanced_products_store, 
    ProductAdvanced, 
    ProductCreate,
    ProductStatus,
    ProductType
)

router = APIRouter(prefix="/products/catalog", tags=["Product Catalog Management"])

# Models for catalog operations
class ProductImportResult(BaseModel):
    """Result of product import operation"""
    total_processed: int
    successful_imports: int
    failed_imports: int
    created_products: List[str]  # Product IDs
    failed_records: List[Dict[str, str]]  # Error details
    warnings: List[str]
    processing_time_seconds: float

class ProductExportRequest(BaseModel):
    """Request for product export"""
    format: str = Field(..., description="Export format: csv, json, xlsx")
    include_images: bool = Field(default=False, description="Include image URLs")
    include_inactive: bool = Field(default=False, description="Include inactive products")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    date_range_start: Optional[date] = Field(None, description="Filter by creation date start")
    date_range_end: Optional[date] = Field(None, description="Filter by creation date end")
    fields: Optional[List[str]] = Field(None, description="Specific fields to export")

class ProductDuplicationRequest(BaseModel):
    """Request for product duplication"""
    source_product_id: str = Field(..., description="ID of product to duplicate")
    new_code: str = Field(..., description="New product code")
    new_name: Optional[str] = Field(None, description="New product name (optional)")
    copy_images: bool = Field(default=True, description="Copy product images")
    quantity_to_create: int = Field(default=1, ge=1, le=100, description="Number of copies to create")
    code_pattern: Optional[str] = Field(None, description="Pattern for generating codes (e.g., 'PROD_{counter}')")

class BulkOperationRequest(BaseModel):
    """Request for bulk operations on products"""
    product_ids: List[str] = Field(..., description="List of product IDs")
    operation: str = Field(..., description="Operation: activate, deactivate, delete, update_category")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")

class CatalogStatistics(BaseModel):
    """Catalog statistics and metrics"""
    total_products: int
    active_products: int
    inactive_products: int
    categories_count: int
    brands_count: int
    average_price: float
    total_catalog_value: float
    products_with_images: int
    recent_additions: int  # Last 7 days
    top_categories: List[Dict[str, Any]]
    price_distribution: Dict[str, int]

# Helper functions
def get_all_products() -> List[Dict[str, Any]]:
    """Get all products from both stores"""
    all_products = []
    
    # Legacy products
    for product in products_store.values():
        legacy_product = {
            "id": product["id"],
            "code": product["code"],
            "name": product["name"],
            "description": product.get("description"),
            "price": Decimal(str(product["price"])),
            "category": product.get("category"),
            "status": "active" if product.get("is_active", True) else "inactive",
            "product_type": "physical",
            "created_at": product.get("created_at", datetime.now().isoformat()),
            "updated_at": product.get("updated_at", datetime.now().isoformat())
        }
        all_products.append(legacy_product)
    
    # Advanced products
    all_products.extend(list(advanced_products_store.values()))
    
    return all_products

def validate_csv_headers(headers: List[str]) -> Dict[str, str]:
    """Validate and map CSV headers to product fields"""
    required_fields = {"code", "name", "price"}
    optional_fields = {
        "description", "category", "sku", "barcode", "brand", "manufacturer",
        "product_type", "status", "weight", "color", "size", "material",
        "warranty_period", "is_featured"
    }
    
    header_map = {}
    missing_required = []
    
    # Normalize headers (lowercase, replace spaces/dashes with underscores)
    normalized_headers = {}
    for header in headers:
        normalized = header.lower().replace(" ", "_").replace("-", "_")
        normalized_headers[normalized] = header
    
    # Check required fields
    for field in required_fields:
        if field in normalized_headers:
            header_map[field] = normalized_headers[field]
        else:
            missing_required.append(field)
    
    if missing_required:
        raise ValueError(f"Missing required columns: {', '.join(missing_required)}")
    
    # Map optional fields
    for field in optional_fields:
        if field in normalized_headers:
            header_map[field] = normalized_headers[field]
    
    return header_map

def parse_csv_row(row: Dict[str, str], header_map: Dict[str, str]) -> Dict[str, Any]:
    """Parse a CSV row into product data"""
    product_data = {}
    
    # Required fields
    product_data["code"] = row[header_map["code"]].strip()
    product_data["name"] = row[header_map["name"]].strip()
    
    try:
        product_data["price"] = float(row[header_map["price"]])
    except (ValueError, TypeError):
        raise ValueError(f"Invalid price value: {row[header_map['price']]}")
    
    # Optional fields
    for field, header in header_map.items():
        if field in ["code", "name", "price"]:
            continue  # Already processed
        
        value = row[header].strip() if row[header] else None
        if not value:
            continue
        
        # Type conversions
        if field == "weight":
            try:
                product_data[field] = float(value)
            except ValueError:
                continue
        elif field == "warranty_period":
            try:
                product_data[field] = int(value)
            except ValueError:
                continue
        elif field == "is_featured":
            product_data[field] = value.lower() in ("true", "1", "yes", "y")
        elif field == "product_type":
            if value.lower() in [e.value for e in ProductType]:
                product_data[field] = value.lower()
        elif field == "status":
            if value.lower() in [e.value for e in ProductStatus]:
                product_data[field] = value.lower()
        else:
            product_data[field] = value
    
    return product_data

# API Endpoints

@router.post("/import/csv", response_model=ProductImportResult)
async def import_products_from_csv(
    file: UploadFile = File(...),
    skip_duplicates: bool = True,
    update_existing: bool = False
) -> ProductImportResult:
    """Import products from CSV file"""
    
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    start_time = datetime.now()
    
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        headers = csv_reader.fieldnames or []
        
        if not headers:
            raise HTTPException(status_code=400, detail="CSV file appears to be empty or invalid")
        
        # Validate headers
        try:
            header_map = validate_csv_headers(headers)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Process rows
        successful_imports = 0
        failed_imports = 0
        created_products = []
        failed_records = []
        warnings = []
        total_processed = 0
        
        existing_codes = set()
        for product in get_all_products():
            existing_codes.add(product["code"])
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
            total_processed += 1
            
            try:
                # Parse row data
                product_data = parse_csv_row(row, header_map)
                
                # Check for duplicates
                if product_data["code"] in existing_codes:
                    if skip_duplicates:
                        warnings.append(f"Row {row_num}: Skipped duplicate code '{product_data['code']}'")
                        continue
                    elif not update_existing:
                        failed_records.append({
                            "row": str(row_num),
                            "code": product_data["code"],
                            "error": "Duplicate product code"
                        })
                        failed_imports += 1
                        continue
                
                # Create product
                if update_existing and product_data["code"] in existing_codes:
                    # Update existing product logic would go here
                    warnings.append(f"Row {row_num}: Product update not implemented yet")
                    continue
                else:
                    # Create new product
                    product = ProductAdvanced(**product_data)
                    advanced_products_store[product.id] = product.dict()
                    existing_codes.add(product.code)
                    created_products.append(product.id)
                    successful_imports += 1
                
            except ValueError as e:
                failed_records.append({
                    "row": str(row_num),
                    "code": row.get(header_map.get("code", ""), "Unknown"),
                    "error": str(e)
                })
                failed_imports += 1
            except Exception as e:
                failed_records.append({
                    "row": str(row_num),
                    "code": row.get(header_map.get("code", ""), "Unknown"),
                    "error": f"Unexpected error: {str(e)}"
                })
                failed_imports += 1
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProductImportResult(
            total_processed=total_processed,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            created_products=created_products,
            failed_records=failed_records,
            warnings=warnings,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/export")
async def export_products(export_request: ProductExportRequest) -> StreamingResponse:
    """Export products in various formats"""
    
    # Get products based on filters
    all_products = get_all_products()
    
    # Apply filters
    filtered_products = all_products.copy()
    
    if not export_request.include_inactive:
        filtered_products = [p for p in filtered_products if p.get("status") != "inactive"]
    
    if export_request.categories:
        filtered_products = [p for p in filtered_products if p.get("category") in export_request.categories]
    
    if export_request.date_range_start:
        start_date = export_request.date_range_start
        filtered_products = [
            p for p in filtered_products 
            if datetime.fromisoformat(p.get("created_at", "")).date() >= start_date
        ]
    
    if export_request.date_range_end:
        end_date = export_request.date_range_end
        filtered_products = [
            p for p in filtered_products 
            if datetime.fromisoformat(p.get("created_at", "")).date() <= end_date
        ]
    
    # Determine fields to export
    if export_request.fields:
        export_fields = export_request.fields
    else:
        export_fields = [
            "code", "name", "description", "price", "category", "sku", "barcode",
            "brand", "manufacturer", "product_type", "status", "weight", "color",
            "size", "material", "warranty_period", "is_featured", "created_at", "updated_at"
        ]
        if export_request.include_images:
            export_fields.extend(["image_urls", "thumbnail_url"])
    
    # Generate export based on format
    if export_request.format.lower() == "csv":
        return export_as_csv(filtered_products, export_fields)
    elif export_request.format.lower() == "json":
        return export_as_json(filtered_products, export_fields)
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")

def export_as_csv(products: List[Dict[str, Any]], fields: List[str]) -> StreamingResponse:
    """Export products as CSV"""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    
    for product in products:
        row = {}
        for field in fields:
            value = product.get(field)
            if isinstance(value, list):
                row[field] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                row[field] = json.dumps(value)
            elif isinstance(value, Decimal):
                row[field] = float(value)
            else:
                row[field] = value
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

def export_as_json(products: List[Dict[str, Any]], fields: List[str]) -> StreamingResponse:
    """Export products as JSON"""
    
    filtered_products = []
    for product in products:
        filtered_product = {}
        for field in fields:
            if field in product:
                value = product[field]
                if isinstance(value, Decimal):
                    filtered_product[field] = float(value)
                else:
                    filtered_product[field] = value
        filtered_products.append(filtered_product)
    
    json_content = json.dumps({
        "export_info": {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(filtered_products),
            "fields_included": fields
        },
        "products": filtered_products
    }, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
    )

@router.post("/duplicate", response_model=List[ProductAdvanced])
async def duplicate_products(request: ProductDuplicationRequest) -> List[ProductAdvanced]:
    """Duplicate products with variations"""
    
    # Find source product
    source_product = None
    if request.source_product_id in advanced_products_store:
        source_product = advanced_products_store[request.source_product_id]
    elif request.source_product_id in products_store:
        # Convert legacy product
        legacy_product = products_store[request.source_product_id]
        source_product = {
            "code": legacy_product["code"],
            "name": legacy_product["name"],
            "description": legacy_product.get("description"),
            "price": Decimal(str(legacy_product["price"])),
            "category": legacy_product.get("category"),
            "status": "active" if legacy_product.get("is_active", True) else "inactive",
        }
    
    if not source_product:
        raise HTTPException(status_code=404, detail="Source product not found")
    
    # Check if new codes already exist
    existing_codes = set(p["code"] for p in get_all_products())
    
    duplicated_products = []
    
    for i in range(request.quantity_to_create):
        # Generate code
        if request.code_pattern and "{counter}" in request.code_pattern:
            new_code = request.code_pattern.replace("{counter}", str(i + 1))
        elif request.quantity_to_create == 1:
            new_code = request.new_code
        else:
            new_code = f"{request.new_code}_{i + 1:03d}"
        
        if new_code in existing_codes:
            raise HTTPException(
                status_code=400, 
                detail=f"Product with code '{new_code}' already exists"
            )
        
        # Create duplicate
        duplicate_data = source_product.copy()
        duplicate_data["code"] = new_code
        
        if request.new_name:
            if request.quantity_to_create == 1:
                duplicate_data["name"] = request.new_name
            else:
                duplicate_data["name"] = f"{request.new_name} #{i + 1}"
        else:
            duplicate_data["name"] = f"{source_product['name']} (Copy {i + 1})"
        
        # Remove ID and reset timestamps
        duplicate_data.pop("id", None)
        duplicate_data["created_at"] = datetime.now()
        duplicate_data["updated_at"] = datetime.now()
        
        # Clear image URLs if not copying images
        if not request.copy_images:
            duplicate_data.pop("image_urls", None)
            duplicate_data.pop("thumbnail_url", None)
        
        # Create product
        product = ProductAdvanced(**duplicate_data)
        advanced_products_store[product.id] = product.dict()
        existing_codes.add(new_code)
        duplicated_products.append(product)
    
    return duplicated_products

@router.post("/bulk-operations")
async def perform_bulk_operations(request: BulkOperationRequest) -> Dict[str, Any]:
    """Perform bulk operations on multiple products"""
    
    if len(request.product_ids) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 products allowed per bulk operation")
    
    successful_operations = []
    failed_operations = []
    
    for product_id in request.product_ids:
        try:
            if request.operation == "activate":
                if product_id in advanced_products_store:
                    advanced_products_store[product_id]["status"] = ProductStatus.ACTIVE
                    advanced_products_store[product_id]["updated_at"] = datetime.now()
                elif product_id in products_store:
                    products_store[product_id]["is_active"] = True
                    products_store[product_id]["updated_at"] = datetime.now()
                else:
                    raise ValueError("Product not found")
                successful_operations.append(product_id)
            
            elif request.operation == "deactivate":
                if product_id in advanced_products_store:
                    advanced_products_store[product_id]["status"] = ProductStatus.INACTIVE
                    advanced_products_store[product_id]["updated_at"] = datetime.now()
                elif product_id in products_store:
                    products_store[product_id]["is_active"] = False
                    products_store[product_id]["updated_at"] = datetime.now()
                else:
                    raise ValueError("Product not found")
                successful_operations.append(product_id)
            
            elif request.operation == "update_category":
                new_category = request.parameters.get("category")
                if not new_category:
                    raise ValueError("Category parameter required")
                
                if product_id in advanced_products_store:
                    advanced_products_store[product_id]["category"] = new_category
                    advanced_products_store[product_id]["updated_at"] = datetime.now()
                elif product_id in products_store:
                    products_store[product_id]["category"] = new_category
                    products_store[product_id]["updated_at"] = datetime.now()
                else:
                    raise ValueError("Product not found")
                successful_operations.append(product_id)
            
            else:
                raise ValueError(f"Unsupported operation: {request.operation}")
        
        except Exception as e:
            failed_operations.append({
                "product_id": product_id,
                "error": str(e)
            })
    
    return {
        "operation": request.operation,
        "total_requested": len(request.product_ids),
        "successful_operations": len(successful_operations),
        "failed_operations": len(failed_operations),
        "successful_product_ids": successful_operations,
        "failed_details": failed_operations
    }

@router.get("/statistics", response_model=CatalogStatistics)
async def get_catalog_statistics() -> CatalogStatistics:
    """Get comprehensive catalog statistics"""
    
    all_products = get_all_products()
    
    # Basic counts
    total_products = len(all_products)
    active_products = len([p for p in all_products if p.get("status") == "active"])
    inactive_products = total_products - active_products
    
    # Categories and brands
    categories = set()
    brands = set()
    prices = []
    products_with_images = 0
    
    for product in all_products:
        if product.get("category"):
            categories.add(product["category"])
        if product.get("brand"):
            brands.add(product["brand"])
        if product.get("status") == "active":
            prices.append(float(product["price"]))
        if product.get("image_urls") and len(product["image_urls"]) > 0:
            products_with_images += 1
    
    # Calculate statistics
    avg_price = sum(prices) / len(prices) if prices else 0
    total_catalog_value = sum(prices)
    
    # Recent additions (last 7 days)
    seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    recent_additions = 0
    for product in all_products:
        try:
            created_at_str = product.get("created_at", "")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', ''))
                if created_at.replace(tzinfo=None) >= seven_days_ago:
                    recent_additions += 1
        except (ValueError, TypeError):
            continue
    
    # Top categories
    category_counts = {}
    for product in all_products:
        category = product.get("category", "Uncategorized")
        category_counts[category] = category_counts.get(category, 0) + 1
    
    top_categories = [
        {"category": cat, "count": count}
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # Price distribution
    price_ranges = {
        "0-50": 0,
        "51-100": 0,
        "101-250": 0,
        "251-500": 0,
        "501-1000": 0,
        "1000+": 0
    }
    
    for price in prices:
        if price <= 50:
            price_ranges["0-50"] += 1
        elif price <= 100:
            price_ranges["51-100"] += 1
        elif price <= 250:
            price_ranges["101-250"] += 1
        elif price <= 500:
            price_ranges["251-500"] += 1
        elif price <= 1000:
            price_ranges["501-1000"] += 1
        else:
            price_ranges["1000+"] += 1
    
    return CatalogStatistics(
        total_products=total_products,
        active_products=active_products,
        inactive_products=inactive_products,
        categories_count=len(categories),
        brands_count=len(brands),
        average_price=round(avg_price, 2),
        total_catalog_value=round(total_catalog_value, 2),
        products_with_images=products_with_images,
        recent_additions=recent_additions,
        top_categories=top_categories,
        price_distribution=price_ranges
    )

@router.get("/template/csv")
async def download_csv_template() -> StreamingResponse:
    """Download CSV template for product import"""
    
    headers = [
        "code", "name", "description", "price", "category", "sku", "barcode",
        "brand", "manufacturer", "product_type", "status", "weight", "color",
        "size", "material", "warranty_period", "is_featured"
    ]
    
    # Create sample data
    sample_data = [
        {
            "code": "SAMPLE001",
            "name": "Sample Product 1",
            "description": "This is a sample product description",
            "price": "99.99",
            "category": "Electronics",
            "sku": "SKU001",
            "barcode": "1234567890123",
            "brand": "Sample Brand",
            "manufacturer": "Sample Manufacturer",
            "product_type": "physical",
            "status": "active",
            "weight": "1.5",
            "color": "Black",
            "size": "Medium",
            "material": "Plastic",
            "warranty_period": "12",
            "is_featured": "false"
        }
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample_data)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=product_import_template.csv"}
    )

# Import datetime.timedelta for recent_additions calculation
from datetime import timedelta