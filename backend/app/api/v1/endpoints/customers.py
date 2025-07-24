"""
Customer Management API Endpoints - CC02 v49.0 Phase 3
48-Hour Backend Blitz - Customer Management TDD Implementation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum
import uuid

# Import database dependencies
from app.core.database import get_db

router = APIRouter(prefix="/customers", tags=["Customers"])

# Enums for customer data
class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PROSPECT = "prospect"

# Response models for TDD tests
class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    customer_type: str = CustomerType.INDIVIDUAL.value
    status: str = CustomerStatus.ACTIVE.value
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int

class CustomerContactResponse(BaseModel):
    id: str
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    is_primary: bool = False
    created_at: datetime

class CustomerOrdersResponse(BaseModel):
    items: List[Dict[str, Any]]  # Will be replaced with proper Order model
    total: int

class CustomerTypeStats(BaseModel):
    type: str
    count: int

class CustomerStatisticsResponse(BaseModel):
    total_customers: int
    active_customers: int
    inactive_customers: int
    customer_types: List[CustomerTypeStats]
    recent_customers: int  # Last 30 days

# In-memory storage for TDD (will be replaced with database)
customers_store: Dict[str, Dict[str, Any]] = {}
customer_contacts_store: Dict[str, Dict[str, Any]] = {}

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Create a new customer"""
    
    try:
        customer_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in customer_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Check for duplicate email
    email = customer_data["email"].lower()
    for existing_customer in customers_store.values():
        if existing_customer["email"].lower() == email:
            raise HTTPException(
                status_code=400,
                detail=f"Customer with email '{customer_data['email']}' already exists"
            )
    
    # Create customer
    customer_id = str(uuid.uuid4())
    now = datetime.now()
    
    customer = {
        "id": customer_id,
        "name": customer_data["name"],
        "email": customer_data["email"],
        "phone": customer_data.get("phone"),
        "address": customer_data.get("address"),
        "customer_type": customer_data.get("customer_type", CustomerType.INDIVIDUAL.value),
        "status": customer_data.get("status", CustomerStatus.ACTIVE.value),
        "is_active": customer_data.get("is_active", True),
        "created_at": now,
        "updated_at": now
    }
    
    customers_store[customer_id] = customer
    return CustomerResponse(**customer)

@router.get("/statistics", response_model=CustomerStatisticsResponse)
async def get_customer_statistics(
    db: AsyncSession = Depends(get_db)
) -> CustomerStatisticsResponse:
    """Get customer statistics"""
    
    all_customers = list(customers_store.values())
    total_customers = len(all_customers)
    active_customers = len([c for c in all_customers if c["is_active"]])
    inactive_customers = total_customers - active_customers
    
    # Customer type breakdown
    type_counts = {}
    for customer in all_customers:
        customer_type = customer.get("customer_type", CustomerType.INDIVIDUAL.value)
        type_counts[customer_type] = type_counts.get(customer_type, 0) + 1
    
    customer_types = [
        CustomerTypeStats(type=type_name, count=count)
        for type_name, count in type_counts.items()
    ]
    
    # Recent customers (last 30 days) - simplified for TDD
    recent_customers = len([c for c in all_customers if c["is_active"]])  # Simplified
    
    return CustomerStatisticsResponse(
        total_customers=total_customers,
        active_customers=active_customers,
        inactive_customers=inactive_customers,
        customer_types=customer_types,
        recent_customers=recent_customers
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Get customer by ID"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customers_store[customer_id]
    return CustomerResponse(**customer)

@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> CustomerListResponse:
    """List customers with pagination and filtering"""
    
    all_customers = list(customers_store.values())
    
    # Apply filters
    if search:
        search_lower = search.lower()
        all_customers = [
            c for c in all_customers
            if (search_lower in c["name"].lower() or 
                search_lower in c["email"].lower() or
                (c.get("phone") and search_lower in c["phone"]))
        ]
    
    if customer_type:
        all_customers = [c for c in all_customers if c.get("customer_type") == customer_type]
    
    if status:
        all_customers = [c for c in all_customers if c.get("status") == status]
    
    # Sort by created_at descending
    all_customers.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_customers)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_customers = all_customers[start_idx:end_idx]
    
    # Convert to response format
    items = [CustomerResponse(**customer) for customer in paginated_customers]
    
    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size  # Ceiling division
    )

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Update customer information"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    customer = customers_store[customer_id].copy()
    
    # Update fields (prevent updating immutable fields)
    for field, value in update_data.items():
        if field not in ["id", "created_at"]:
            customer[field] = value
    
    customer["updated_at"] = datetime.now()
    customers_store[customer_id] = customer
    
    return CustomerResponse(**customer)

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete customer (soft delete)"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    customers_store[customer_id]["is_active"] = False
    customers_store[customer_id]["status"] = CustomerStatus.INACTIVE.value
    customers_store[customer_id]["updated_at"] = datetime.now()
    
    return {"message": "Customer deleted successfully", "id": customer_id}

@router.post("/{customer_id}/contacts", response_model=CustomerContactResponse, status_code=201)
async def create_customer_contact(
    customer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> CustomerContactResponse:
    """Create a customer contact"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        contact_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    if "name" not in contact_data:
        raise HTTPException(status_code=422, detail="Missing required field: name")
    
    # Create contact
    contact_id = str(uuid.uuid4())
    now = datetime.now()
    
    contact = {
        "id": contact_id,
        "customer_id": customer_id,
        "name": contact_data["name"],
        "email": contact_data.get("email"),
        "phone": contact_data.get("phone"),
        "title": contact_data.get("title"),
        "is_primary": contact_data.get("is_primary", False),
        "created_at": now
    }
    
    customer_contacts_store[contact_id] = contact
    return CustomerContactResponse(**contact)

@router.get("/{customer_id}/contacts", response_model=List[CustomerContactResponse])
async def get_customer_contacts(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[CustomerContactResponse]:
    """Get all contacts for a customer"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    contacts = [
        CustomerContactResponse(**contact)
        for contact in customer_contacts_store.values()
        if contact["customer_id"] == customer_id
    ]
    
    return contacts

@router.get("/{customer_id}/orders", response_model=CustomerOrdersResponse)
async def get_customer_orders(
    customer_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> CustomerOrdersResponse:
    """Get customer orders (placeholder for future Order integration)"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Placeholder response - will be integrated with Order API later
    return CustomerOrdersResponse(
        items=[],  # Empty for now, will be populated with actual orders
        total=0
    )

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for customers"""
    start_time = datetime.now()
    
    # Simulate some processing
    customer_count = len(customers_store)
    contacts_count = len(customer_contacts_store)
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "customer_count": customer_count,
        "contacts_count": contacts_count,
        "timestamp": start_time.isoformat()
    }