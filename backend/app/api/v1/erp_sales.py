"""
ERP Sales Management API
Enhanced customer and sales order management with inventory integration
"""

import logging
from datetime import datetime, UTC, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field, EmailStr, validator

from app.core.dependencies import get_current_active_user, get_db
from app.core.tenant_deps import TenantDep, RequireApiAccess
from app.models.user import User
from app.models.organization import Organization
from app.models.product import Product
from app.models.sales import Customer, SalesOrder, SalesOrderItem, CustomerType, CustomerStatus, SalesOrderStatus, PaymentStatus
from app.models.warehouse import InventoryItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-sales", tags=["ERP Sales Management"])


# Pydantic schemas
class CustomerCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    organization_id: int = Field(..., description="Organization ID")
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    
    # Contact info
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    # Address
    postal_code: Optional[str] = Field(None, max_length=10)
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    
    # Business info (for corporate)
    industry: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Contact person (for corporate)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Financial
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=100)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Additional
    notes: Optional[str] = None
    is_active: bool = True


class SalesOrderCreateRequest(BaseModel):
    order_number: str = Field(..., min_length=2, max_length=50)
    organization_id: int = Field(..., description="Organization ID")
    customer_id: int = Field(..., description="Customer ID")
    sales_rep_id: Optional[int] = Field(None, description="Sales representative user ID")
    
    # Dates
    required_date: Optional[date] = None
    
    # Addresses
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    
    # Order items
    items: List["OrderItemRequest"] = Field(..., min_items=1)
    
    # Financial
    discount_amount: Decimal = Field(0, ge=0)
    shipping_cost: Decimal = Field(0, ge=0)
    
    # Additional
    notes: Optional[str] = None
    customer_po_number: Optional[str] = Field(None, max_length=100)
    shipping_method: Optional[str] = Field(None, max_length=100)
    is_rush_order: bool = False


class OrderItemRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    quantity: Decimal = Field(..., gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)  # If None, use product selling price
    discount_percentage: Decimal = Field(0, ge=0, le=100)
    notes: Optional[str] = None


class OrderStatusUpdateRequest(BaseModel):
    status: SalesOrderStatus = Field(..., description="New order status")
    notes: Optional[str] = Field(None, max_length=500)


class StockReservationRequest(BaseModel):
    reserve_stock: bool = Field(True, description="Whether to reserve stock for this order")
    warehouse_id: Optional[int] = Field(None, description="Preferred warehouse ID")


class CustomerResponse(BaseModel):
    id: int
    code: str
    name: str
    organization_id: int
    organization_name: Optional[str]
    customer_type: str
    status: str
    
    # Contact
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    website: Optional[str]
    full_address: str
    
    # Business info
    industry: Optional[str]
    tax_id: Optional[str]
    
    # Contact person
    contact_person: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    display_name: str
    
    # Financial
    credit_limit: Optional[Decimal]
    payment_terms: Optional[str]
    discount_rate: Optional[Decimal]
    
    # Metrics
    total_orders: int
    total_spent: Decimal
    average_order_value: Decimal
    first_purchase_date: Optional[str]
    last_purchase_date: Optional[str]
    
    # Flags
    is_active: bool
    is_vip: bool
    is_corporate: bool
    
    created_at: str
    updated_at: Optional[str]


class SalesOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_code: str
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    line_total: Decimal
    quantity_shipped: Decimal
    quantity_pending: Decimal
    is_fully_shipped: bool
    notes: Optional[str]


class SalesOrderResponse(BaseModel):
    id: int
    order_number: str
    organization_id: int
    organization_name: Optional[str]
    customer_id: int
    customer_name: str
    sales_rep_id: Optional[int]
    sales_rep_name: Optional[str]
    
    # Status
    status: str
    payment_status: str
    
    # Dates
    order_date: str
    required_date: Optional[str]
    shipped_date: Optional[str]
    delivered_date: Optional[str]
    days_until_due: Optional[int]
    is_overdue: bool
    
    # Financial
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    currency: str
    
    # Shipping
    shipping_method: Optional[str]
    tracking_number: Optional[str]
    shipping_address: Optional[str]
    billing_address: Optional[str]
    
    # Additional
    notes: Optional[str]
    customer_po_number: Optional[str]
    is_rush_order: bool
    can_be_shipped: bool
    
    # Items
    items: List[SalesOrderItemResponse] = []
    
    created_at: str
    updated_at: Optional[str]


class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class SalesOrderListResponse(BaseModel):
    orders: List[SalesOrderResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class SalesStatsResponse(BaseModel):
    total_customers: int
    active_customers: int
    total_orders: int
    orders_by_status: Dict[str, int]
    total_revenue: float
    average_order_value: float
    top_customers: List[Dict[str, Any]]
    recent_orders: int
    overdue_orders: int


# Fix forward reference
SalesOrderCreateRequest.model_rebuild()


# Customer Management
@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_request: CustomerCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new customer"""
    try:
        # Check if customer code exists in organization
        existing_customer = db.query(Customer).filter(
            and_(
                Customer.code == customer_request.code,
                Customer.organization_id == customer_request.organization_id
            )
        ).first()
        
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer with this code already exists in the organization"
            )
        
        # Validate organization
        organization = db.query(Organization).filter(Organization.id == customer_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Create customer
        customer_data = customer_request.dict()
        customer_data["status"] = CustomerStatus.ACTIVE.value
        customer_data["created_by"] = current_user.id
        
        customer = Customer(**customer_data)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        logger.info(f"Customer created: {customer.id} by {current_user.id}")
        
        return CustomerResponse(
            id=customer.id,
            code=customer.code,
            name=customer.name,
            organization_id=customer.organization_id,
            organization_name=organization.name,
            customer_type=customer.customer_type,
            status=customer.status,
            email=customer.email,
            phone=customer.phone,
            mobile=customer.mobile,
            website=customer.website,
            full_address=customer.full_address,
            industry=customer.industry,
            tax_id=customer.tax_id,
            contact_person=customer.contact_person,
            contact_email=customer.contact_email,
            contact_phone=customer.contact_phone,
            display_name=customer.display_name,
            credit_limit=customer.credit_limit,
            payment_terms=customer.payment_terms,
            discount_rate=customer.discount_rate,
            total_orders=customer.total_orders,
            total_spent=customer.total_spent,
            average_order_value=customer.average_order_value,
            first_purchase_date=customer.first_purchase_date.isoformat() if customer.first_purchase_date else None,
            last_purchase_date=customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
            is_active=customer.is_active,
            is_vip=customer.is_vip,
            is_corporate=customer.is_corporate,
            created_at=customer.created_at.isoformat(),
            updated_at=customer.updated_at.isoformat() if customer.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    customer_type: Optional[CustomerType] = Query(None),
    status: Optional[CustomerStatus] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_vip: Optional[bool] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List customers with filtering"""
    try:
        query = db.query(Customer).filter(Customer.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.code.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.contact_person.ilike(search_term)
                )
            )
        
        if organization_id:
            query = query.filter(Customer.organization_id == organization_id)
        
        if customer_type:
            query = query.filter(Customer.customer_type == customer_type.value)
        
        if status:
            query = query.filter(Customer.status == status.value)
        
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        
        if is_vip is not None:
            query = query.filter(Customer.is_vip == is_vip)
        
        # Apply sorting
        sort_column = getattr(Customer, sort_by, Customer.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        customers = query.offset(skip).limit(limit).all()
        
        # Prepare response
        customer_responses = []
        for customer in customers:
            organization_name = customer.organization.name if customer.organization else None
            
            customer_responses.append(CustomerResponse(
                id=customer.id,
                code=customer.code,
                name=customer.name,
                organization_id=customer.organization_id,
                organization_name=organization_name,
                customer_type=customer.customer_type,
                status=customer.status,
                email=customer.email,
                phone=customer.phone,
                mobile=customer.mobile,
                website=customer.website,
                full_address=customer.full_address,
                industry=customer.industry,
                tax_id=customer.tax_id,
                contact_person=customer.contact_person,
                contact_email=customer.contact_email,
                contact_phone=customer.contact_phone,
                display_name=customer.display_name,
                credit_limit=customer.credit_limit,
                payment_terms=customer.payment_terms,
                discount_rate=customer.discount_rate,
                total_orders=customer.total_orders,
                total_spent=customer.total_spent,
                average_order_value=customer.average_order_value,
                first_purchase_date=customer.first_purchase_date.isoformat() if customer.first_purchase_date else None,
                last_purchase_date=customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
                is_active=customer.is_active,
                is_vip=customer.is_vip,
                is_corporate=customer.is_corporate,
                created_at=customer.created_at.isoformat(),
                updated_at=customer.updated_at.isoformat() if customer.updated_at else None
            ))
        
        return CustomerListResponse(
            customers=customer_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )


# Sales Order Management
@router.post("/orders", response_model=SalesOrderResponse)
async def create_sales_order(
    order_request: SalesOrderCreateRequest,
    reserve_stock: bool = Query(True, description="Reserve stock for order items"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new sales order with inventory reservation"""
    try:
        # Check if order number exists
        existing_order = db.query(SalesOrder).filter(
            SalesOrder.order_number == order_request.order_number
        ).first()
        
        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order with this number already exists"
            )
        
        # Validate organization, customer, and sales rep
        organization = db.query(Organization).filter(Organization.id == order_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        customer = db.query(Customer).filter(Customer.id == order_request.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        sales_rep = None
        if order_request.sales_rep_id:
            sales_rep = db.query(User).filter(User.id == order_request.sales_rep_id).first()
            if not sales_rep:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sales representative not found"
                )
        
        # Validate products and calculate totals
        subtotal = Decimal(0)
        order_items_data = []
        stock_reservations = []
        
        for item_request in order_request.items:
            product = db.query(Product).filter(Product.id == item_request.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item_request.product_id} not found"
                )
            
            # Use product selling price if not specified
            unit_price = item_request.unit_price if item_request.unit_price else product.selling_price
            
            # Calculate discount and line total
            discount_amount = (unit_price * item_request.quantity * item_request.discount_percentage) / 100
            line_total = (unit_price * item_request.quantity) - discount_amount
            
            order_items_data.append({
                "product_id": product.id,
                "product_code": product.code,
                "product_name": product.name,
                "product_description": product.description,
                "quantity": item_request.quantity,
                "unit_price": unit_price,
                "discount_percentage": item_request.discount_percentage,
                "discount_amount": discount_amount,
                "line_total": line_total,
                "notes": item_request.notes
            })
            
            subtotal += line_total
            
            # Check stock availability if reserving
            if reserve_stock and product.track_inventory:
                # Find inventory with sufficient stock
                inventory_item = db.query(InventoryItem).filter(
                    and_(
                        InventoryItem.product_id == product.id,
                        InventoryItem.quantity_available >= item_request.quantity
                    )
                ).first()
                
                if not inventory_item:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for product {product.code}"
                    )
                
                stock_reservations.append({
                    "inventory_item": inventory_item,
                    "quantity": item_request.quantity
                })
        
        # Create sales order
        tax_amount = subtotal * Decimal('0.1')  # Assuming 10% tax rate
        total_amount = subtotal + tax_amount - order_request.discount_amount + order_request.shipping_cost
        
        sales_order = SalesOrder(
            order_number=order_request.order_number,
            organization_id=order_request.organization_id,
            customer_id=order_request.customer_id,
            sales_rep_id=order_request.sales_rep_id,
            status=SalesOrderStatus.DRAFT.value,
            payment_status=PaymentStatus.PENDING.value,
            order_date=date.today(),
            required_date=order_request.required_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=order_request.discount_amount,
            shipping_cost=order_request.shipping_cost,
            total_amount=total_amount,
            shipping_address=order_request.shipping_address,
            billing_address=order_request.billing_address,
            notes=order_request.notes,
            customer_po_number=order_request.customer_po_number,
            shipping_method=order_request.shipping_method,
            is_rush_order=order_request.is_rush_order,
            created_by=current_user.id
        )
        
        db.add(sales_order)
        db.flush()  # Get the order ID
        
        # Create order items
        order_item_objects = []
        for item_data in order_items_data:
            order_item = SalesOrderItem(
                sales_order_id=sales_order.id,
                organization_id=order_request.organization_id,
                **item_data,
                created_by=current_user.id
            )
            order_item_objects.append(order_item)
            db.add(order_item)
        
        # Reserve stock if requested
        if reserve_stock:
            for reservation in stock_reservations:
                inventory_item = reservation["inventory_item"]
                quantity = reservation["quantity"]
                
                inventory_item.quantity_reserved += quantity
                inventory_item.calculate_available_quantity()
        
        # Update customer metrics
        customer.update_metrics(total_amount)
        
        db.commit()
        db.refresh(sales_order)
        
        # Prepare response
        order_item_responses = []
        for item in order_item_objects:
            order_item_responses.append(SalesOrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                discount_amount=item.discount_amount,
                line_total=item.line_total,
                quantity_shipped=item.quantity_shipped,
                quantity_pending=item.quantity_pending,
                is_fully_shipped=item.is_fully_shipped,
                notes=item.notes
            ))
        
        logger.info(f"Sales order created: {sales_order.id} by {current_user.id}")
        
        return SalesOrderResponse(
            id=sales_order.id,
            order_number=sales_order.order_number,
            organization_id=sales_order.organization_id,
            organization_name=organization.name,
            customer_id=sales_order.customer_id,
            customer_name=customer.name,
            sales_rep_id=sales_order.sales_rep_id,
            sales_rep_name=sales_rep.full_name if sales_rep else None,
            status=sales_order.status,
            payment_status=sales_order.payment_status,
            order_date=sales_order.order_date.isoformat(),
            required_date=sales_order.required_date.isoformat() if sales_order.required_date else None,
            shipped_date=sales_order.shipped_date.isoformat() if sales_order.shipped_date else None,
            delivered_date=sales_order.delivered_date.isoformat() if sales_order.delivered_date else None,
            days_until_due=sales_order.days_until_due,
            is_overdue=sales_order.is_overdue,
            subtotal=sales_order.subtotal,
            tax_amount=sales_order.tax_amount,
            discount_amount=sales_order.discount_amount,
            shipping_cost=sales_order.shipping_cost,
            total_amount=sales_order.total_amount,
            currency=sales_order.currency,
            shipping_method=sales_order.shipping_method,
            tracking_number=sales_order.tracking_number,
            shipping_address=sales_order.shipping_address,
            billing_address=sales_order.billing_address,
            notes=sales_order.notes,
            customer_po_number=sales_order.customer_po_number,
            is_rush_order=sales_order.is_rush_order,
            can_be_shipped=sales_order.can_be_shipped(),
            items=order_item_responses,
            created_at=sales_order.created_at.isoformat(),
            updated_at=sales_order.updated_at.isoformat() if sales_order.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sales order creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sales order"
        )


@router.get("/orders", response_model=SalesOrderListResponse)
async def list_sales_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    status: Optional[SalesOrderStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    overdue_only: bool = Query(False),
    rush_orders_only: bool = Query(False),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sort_by: str = Query("order_date"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List sales orders with filtering"""
    try:
        query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.join(Customer).filter(
                or_(
                    SalesOrder.order_number.ilike(search_term),
                    Customer.name.ilike(search_term),
                    SalesOrder.customer_po_number.ilike(search_term),
                    SalesOrder.notes.ilike(search_term)
                )
            )
        
        if organization_id:
            query = query.filter(SalesOrder.organization_id == organization_id)
        
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        
        if sales_rep_id:
            query = query.filter(SalesOrder.sales_rep_id == sales_rep_id)
        
        if status:
            query = query.filter(SalesOrder.status == status.value)
        
        if payment_status:
            query = query.filter(SalesOrder.payment_status == payment_status.value)
        
        if overdue_only:
            today = date.today()
            query = query.filter(
                and_(
                    SalesOrder.required_date < today,
                    SalesOrder.status.not_in([SalesOrderStatus.DELIVERED.value, SalesOrderStatus.CANCELLED.value])
                )
            )
        
        if rush_orders_only:
            query = query.filter(SalesOrder.is_rush_order == True)
        
        if date_from:
            query = query.filter(SalesOrder.order_date >= date_from)
        
        if date_to:
            query = query.filter(SalesOrder.order_date <= date_to)
        
        # Apply sorting
        sort_column = getattr(SalesOrder, sort_by, SalesOrder.order_date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        orders = query.offset(skip).limit(limit).all()
        
        # Prepare response
        order_responses = []
        for order in orders:
            # Get related data
            organization_name = order.organization.name if order.organization else None
            customer_name = order.customer.name if order.customer else "Unknown"
            sales_rep_name = order.sales_rep.full_name if order.sales_rep else None
            
            # Get order items
            order_item_responses = []
            for item in order.order_items:
                order_item_responses.append(SalesOrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_percentage=item.discount_percentage,
                    discount_amount=item.discount_amount,
                    line_total=item.line_total,
                    quantity_shipped=item.quantity_shipped,
                    quantity_pending=item.quantity_pending,
                    is_fully_shipped=item.is_fully_shipped,
                    notes=item.notes
                ))
            
            order_responses.append(SalesOrderResponse(
                id=order.id,
                order_number=order.order_number,
                organization_id=order.organization_id,
                organization_name=organization_name,
                customer_id=order.customer_id,
                customer_name=customer_name,
                sales_rep_id=order.sales_rep_id,
                sales_rep_name=sales_rep_name,
                status=order.status,
                payment_status=order.payment_status,
                order_date=order.order_date.isoformat(),
                required_date=order.required_date.isoformat() if order.required_date else None,
                shipped_date=order.shipped_date.isoformat() if order.shipped_date else None,
                delivered_date=order.delivered_date.isoformat() if order.delivered_date else None,
                days_until_due=order.days_until_due,
                is_overdue=order.is_overdue,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                discount_amount=order.discount_amount,
                shipping_cost=order.shipping_cost,
                total_amount=order.total_amount,
                currency=order.currency,
                shipping_method=order.shipping_method,
                tracking_number=order.tracking_number,
                shipping_address=order.shipping_address,
                billing_address=order.billing_address,
                notes=order.notes,
                customer_po_number=order.customer_po_number,
                is_rush_order=order.is_rush_order,
                can_be_shipped=order.can_be_shipped(),
                items=order_item_responses,
                created_at=order.created_at.isoformat(),
                updated_at=order.updated_at.isoformat() if order.updated_at else None
            ))
        
        return SalesOrderListResponse(
            orders=order_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list sales orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sales orders"
        )


@router.put("/orders/{order_id}/status", response_model=SalesOrderResponse)
async def update_order_status(
    order_id: int,
    status_request: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Update sales order status"""
    try:
        order = db.query(SalesOrder).filter(
            and_(SalesOrder.id == order_id, SalesOrder.deleted_at.is_(None))
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        # Update status and related fields
        old_status = order.status
        order.status = status_request.status.value
        order.updated_by = current_user.id
        order.updated_at = datetime.now(UTC)
        
        # Set shipped date if status is shipped
        if status_request.status == SalesOrderStatus.SHIPPED and not order.shipped_date:
            order.shipped_date = date.today()
        
        # Set delivered date if status is delivered
        if status_request.status == SalesOrderStatus.DELIVERED and not order.delivered_date:
            order.delivered_date = date.today()
        
        # If order is cancelled, release reserved stock
        if status_request.status == SalesOrderStatus.CANCELLED:
            for item in order.order_items:
                # Find reserved inventory and release it
                inventory_items = db.query(InventoryItem).filter(
                    InventoryItem.product_id == item.product_id
                ).all()
                
                remaining_to_release = item.quantity - item.quantity_shipped
                for inventory_item in inventory_items:
                    if remaining_to_release <= 0:
                        break
                    
                    release_qty = min(inventory_item.quantity_reserved, remaining_to_release)
                    if release_qty > 0:
                        inventory_item.quantity_reserved -= release_qty
                        inventory_item.calculate_available_quantity()
                        remaining_to_release -= release_qty
        
        db.commit()
        db.refresh(order)
        
        # Prepare response (simplified for brevity)
        order_item_responses = []
        for item in order.order_items:
            order_item_responses.append(SalesOrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                discount_amount=item.discount_amount,
                line_total=item.line_total,
                quantity_shipped=item.quantity_shipped,
                quantity_pending=item.quantity_pending,
                is_fully_shipped=item.is_fully_shipped,
                notes=item.notes
            ))
        
        logger.info(f"Order status updated: {order.id} from {old_status} to {order.status} by {current_user.id}")
        
        return SalesOrderResponse(
            id=order.id,
            order_number=order.order_number,
            organization_id=order.organization_id,
            organization_name=order.organization.name if order.organization else None,
            customer_id=order.customer_id,
            customer_name=order.customer.name if order.customer else "Unknown",
            sales_rep_id=order.sales_rep_id,
            sales_rep_name=order.sales_rep.full_name if order.sales_rep else None,
            status=order.status,
            payment_status=order.payment_status,
            order_date=order.order_date.isoformat(),
            required_date=order.required_date.isoformat() if order.required_date else None,
            shipped_date=order.shipped_date.isoformat() if order.shipped_date else None,
            delivered_date=order.delivered_date.isoformat() if order.delivered_date else None,
            days_until_due=order.days_until_due,
            is_overdue=order.is_overdue,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            currency=order.currency,
            shipping_method=order.shipping_method,
            tracking_number=order.tracking_number,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            notes=order.notes,
            customer_po_number=order.customer_po_number,
            is_rush_order=order.is_rush_order,
            can_be_shipped=order.can_be_shipped(),
            items=order_item_responses,
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat() if order.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


@router.get("/statistics", response_model=SalesStatsResponse)
async def get_sales_statistics(
    organization_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get comprehensive sales statistics"""
    try:
        # Customer statistics
        customer_query = db.query(Customer).filter(Customer.deleted_at.is_(None))
        if organization_id:
            customer_query = customer_query.filter(Customer.organization_id == organization_id)
        
        total_customers = customer_query.count()
        active_customers = customer_query.filter(Customer.is_active == True).count()
        
        # Order statistics
        order_query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
        if organization_id:
            order_query = order_query.filter(SalesOrder.organization_id == organization_id)
        
        if date_from:
            order_query = order_query.filter(SalesOrder.order_date >= date_from)
        
        if date_to:
            order_query = order_query.filter(SalesOrder.order_date <= date_to)
        
        total_orders = order_query.count()
        
        # Orders by status
        status_stats = order_query.group_by(SalesOrder.status).with_entities(
            SalesOrder.status,
            func.count(SalesOrder.id)
        ).all()
        orders_by_status = {stat[0]: stat[1] for stat in status_stats}
        
        # Revenue statistics
        total_revenue = order_query.with_entities(func.sum(SalesOrder.total_amount)).scalar() or 0
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Recent orders (last 30 days)
        from datetime import timedelta
        recent_threshold = date.today() - timedelta(days=30)
        recent_orders = order_query.filter(SalesOrder.order_date >= recent_threshold).count()
        
        # Overdue orders
        today = date.today()
        overdue_orders = order_query.filter(
            and_(
                SalesOrder.required_date < today,
                SalesOrder.status.not_in([SalesOrderStatus.DELIVERED.value, SalesOrderStatus.CANCELLED.value])
            )
        ).count()
        
        # Top customers by revenue
        top_customer_stats = db.query(
            Customer.id,
            Customer.name,
            Customer.code,
            func.sum(SalesOrder.total_amount).label('total_revenue'),
            func.count(SalesOrder.id).label('order_count')
        ).join(SalesOrder).filter(
            SalesOrder.deleted_at.is_(None)
        )
        
        if organization_id:
            top_customer_stats = top_customer_stats.filter(Customer.organization_id == organization_id)
        
        top_customer_stats = top_customer_stats.group_by(
            Customer.id, Customer.name, Customer.code
        ).order_by(desc('total_revenue')).limit(10).all()
        
        top_customers = [
            {
                "customer_id": stat.id,
                "customer_name": stat.name,
                "customer_code": stat.code,
                "total_revenue": float(stat.total_revenue),
                "order_count": stat.order_count
            }
            for stat in top_customer_stats
        ]
        
        return SalesStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_orders=total_orders,
            orders_by_status=orders_by_status,
            total_revenue=float(total_revenue),
            average_order_value=float(average_order_value),
            top_customers=top_customers,
            recent_orders=recent_orders,
            overdue_orders=overdue_orders
        )
    
    except Exception as e:
        logger.error(f"Failed to get sales statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sales statistics"
        )