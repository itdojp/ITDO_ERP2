"""
Basic sales CRUD operations for ERP v17.0
Sales order management, customer management, and billing operations
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, UTC, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.sales import (
    Customer, SalesOrder, SalesOrderItem,
    CustomerStatus, CustomerType, OrderStatus, PaymentStatus, PaymentMethod
)
from app.models.product import Product
from app.schemas.sales_basic import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse,
    SalesOrderItemCreate, SalesOrderItemResponse
)
from app.core.exceptions import BusinessLogicError


# Customer CRUD operations
def create_customer(
    db: Session, 
    customer_data: CustomerCreate, 
    created_by: int
) -> Customer:
    """Create a new customer with validation."""
    # Check if customer number exists
    existing_customer = db.query(Customer).filter(
        and_(
            Customer.customer_number == customer_data.customer_number,
            Customer.organization_id == customer_data.organization_id,
            Customer.deleted_at.is_(None)
        )
    ).first()
    
    if existing_customer:
        raise BusinessLogicError("Customer with this number already exists in the organization")
    
    # Check email uniqueness if provided
    if customer_data.email:
        existing_email = db.query(Customer).filter(
            and_(
                Customer.email == customer_data.email,
                Customer.organization_id == customer_data.organization_id,
                Customer.deleted_at.is_(None)
            )
        ).first()
        if existing_email:
            raise BusinessLogicError("Customer with this email already exists")
    
    # Create customer
    customer_dict = customer_data.dict()
    customer_dict['created_by'] = created_by
    
    customer = Customer(**customer_dict)
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


def get_customer_by_id(db: Session, customer_id: int) -> Optional[Customer]:
    """Get customer by ID."""
    return db.query(Customer).filter(
        and_(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None)
        )
    ).first()


def get_customer_by_number(db: Session, customer_number: str, organization_id: int) -> Optional[Customer]:
    """Get customer by number within organization."""
    return db.query(Customer).filter(
        and_(
            Customer.customer_number == customer_number,
            Customer.organization_id == organization_id,
            Customer.deleted_at.is_(None)
        )
    ).first()


def get_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    status: Optional[CustomerStatus] = None,
    customer_type: Optional[CustomerType] = None,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> tuple[List[Customer], int]:
    """Get customers with filtering and pagination."""
    query = db.query(Customer).filter(Customer.deleted_at.is_(None))
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.customer_number.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )
    
    # Filters
    if organization_id:
        query = query.filter(Customer.organization_id == organization_id)
    
    if status:
        query = query.filter(Customer.status == status.value)
    
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type.value)
    
    # Sorting
    sort_column = getattr(Customer, sort_by, Customer.name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Count for pagination
    total = query.count()
    
    # Apply pagination
    customers = query.offset(skip).limit(limit).all()
    
    return customers, total


def update_customer(
    db: Session,
    customer_id: int,
    customer_data: CustomerUpdate,
    updated_by: int
) -> Optional[Customer]:
    """Update customer information."""
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        return None
    
    # Check for number conflicts if updating number
    if customer_data.customer_number and customer_data.customer_number != customer.customer_number:
        existing_customer = db.query(Customer).filter(
            and_(
                Customer.customer_number == customer_data.customer_number,
                Customer.organization_id == customer.organization_id,
                Customer.id != customer_id,
                Customer.deleted_at.is_(None)
            )
        ).first()
        if existing_customer:
            raise BusinessLogicError("Customer with this number already exists")
    
    # Check for email conflicts if updating email
    if customer_data.email and customer_data.email != customer.email:
        existing_email = db.query(Customer).filter(
            and_(
                Customer.email == customer_data.email,
                Customer.organization_id == customer.organization_id,
                Customer.id != customer_id,
                Customer.deleted_at.is_(None)
            )
        ).first()
        if existing_email:
            raise BusinessLogicError("Customer with this email already exists")
    
    # Update fields
    update_dict = customer_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    
    customer.updated_by = updated_by
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


def deactivate_customer(
    db: Session,
    customer_id: int,
    deactivated_by: int
) -> Optional[Customer]:
    """Deactivate customer."""
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        return None
    
    customer.status = CustomerStatus.INACTIVE.value
    customer.updated_by = deactivated_by
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


# Sales Order CRUD operations
def create_sales_order(
    db: Session,
    order_data: SalesOrderCreate,
    created_by: int
) -> SalesOrder:
    """Create a new sales order."""
    # Generate order number
    order_number = generate_order_number(db, order_data.organization_id)
    
    # Get customer
    customer = get_customer_by_id(db, order_data.customer_id)
    if not customer:
        raise BusinessLogicError("Customer not found")
    
    # Create order
    order_dict = order_data.dict(exclude={'order_items'})
    order_dict['order_number'] = order_number
    order_dict['created_by'] = created_by
    
    # Set payment terms from customer if not specified
    if not order_dict.get('payment_terms'):
        order_dict['payment_terms'] = customer.payment_terms
    
    # Set currency from customer if not specified
    if not order_dict.get('currency'):
        order_dict['currency'] = customer.currency
    
    sales_order = SalesOrder(**order_dict)
    
    # Set payment due date
    sales_order.set_payment_due_date()
    
    db.add(sales_order)
    db.flush()  # Get the ID
    
    # Create order items
    if order_data.order_items:
        for line_num, item_data in enumerate(order_data.order_items, 1):
            create_sales_order_item(db, sales_order.id, item_data, line_num, created_by)
    
    # Calculate totals
    sales_order.calculate_totals()
    
    db.add(sales_order)
    db.commit()
    db.refresh(sales_order)
    
    return sales_order


def get_sales_order_by_id(db: Session, order_id: int) -> Optional[SalesOrder]:
    """Get sales order by ID."""
    return db.query(SalesOrder).filter(
        and_(
            SalesOrder.id == order_id,
            SalesOrder.deleted_at.is_(None)
        )
    ).first()


def get_sales_order_by_number(db: Session, order_number: str, organization_id: int) -> Optional[SalesOrder]:
    """Get sales order by number within organization."""
    return db.query(SalesOrder).filter(
        and_(
            SalesOrder.order_number == order_number,
            SalesOrder.organization_id == organization_id,
            SalesOrder.deleted_at.is_(None)
        )
    ).first()


def get_sales_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    sort_by: str = "order_date",
    sort_order: str = "desc"
) -> tuple[List[SalesOrder], int]:
    """Get sales orders with filtering and pagination."""
    query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                SalesOrder.order_number.ilike(search_term),
                SalesOrder.customer_po_number.ilike(search_term),
                SalesOrder.notes.ilike(search_term)
            )
        )
    
    # Filters
    if organization_id:
        query = query.filter(SalesOrder.organization_id == organization_id)
    
    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)
    
    if status:
        query = query.filter(SalesOrder.status == status.value)
    
    if payment_status:
        query = query.filter(SalesOrder.payment_status == payment_status.value)
    
    if from_date:
        query = query.filter(SalesOrder.order_date >= from_date)
    
    if to_date:
        query = query.filter(SalesOrder.order_date <= to_date)
    
    # Sorting
    sort_column = getattr(SalesOrder, sort_by, SalesOrder.order_date)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Count for pagination
    total = query.count()
    
    # Apply pagination
    orders = query.offset(skip).limit(limit).all()
    
    return orders, total


def update_sales_order(
    db: Session,
    order_id: int,
    order_data: SalesOrderUpdate,
    updated_by: int
) -> Optional[SalesOrder]:
    """Update sales order information."""
    order = get_sales_order_by_id(db, order_id)
    if not order:
        return None
    
    # Check if order can be updated
    if order.status in [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value]:
        raise BusinessLogicError("Cannot update completed or cancelled orders")
    
    # Update fields
    update_dict = order_data.dict(exclude_unset=True, exclude={'order_items'})
    for key, value in update_dict.items():
        if hasattr(order, key):
            setattr(order, key, value)
    
    # Update payment due date if payment terms changed
    if order_data.payment_terms:
        order.set_payment_due_date()
    
    order.updated_by = updated_by
    
    # Recalculate totals
    order.calculate_totals()
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order


def cancel_sales_order(
    db: Session,
    order_id: int,
    cancelled_by: int,
    reason: Optional[str] = None
) -> Optional[SalesOrder]:
    """Cancel a sales order."""
    order = get_sales_order_by_id(db, order_id)
    if not order:
        return None
    
    if order.status in [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value]:
        raise BusinessLogicError("Cannot cancel completed or already cancelled orders")
    
    order.status = OrderStatus.CANCELLED.value
    order.payment_status = PaymentStatus.CANCELLED.value
    order.updated_by = cancelled_by
    
    if reason:
        order.internal_notes = f"Cancelled: {reason}\n{order.internal_notes or ''}"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order


# Sales Order Item CRUD operations
def create_sales_order_item(
    db: Session,
    sales_order_id: int,
    item_data: SalesOrderItemCreate,
    line_number: int,
    created_by: int
) -> SalesOrderItem:
    """Create a sales order item."""
    # Get product information
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise BusinessLogicError("Product not found")
    
    # Create item
    item_dict = item_data.dict()
    item_dict['sales_order_id'] = sales_order_id
    item_dict['line_number'] = line_number
    item_dict['created_by'] = created_by
    
    # Get organization_id from the sales order
    sales_order = get_sales_order_by_id(db, sales_order_id)
    if sales_order:
        item_dict['organization_id'] = sales_order.organization_id
    
    order_item = SalesOrderItem(**item_dict)
    
    # Update product snapshot
    order_item.update_product_snapshot(product)
    
    # Calculate totals
    order_item.calculate_total_amount()
    
    db.add(order_item)
    db.flush()
    
    return order_item


def get_order_items_by_order(db: Session, sales_order_id: int) -> List[SalesOrderItem]:
    """Get all items for a sales order."""
    return db.query(SalesOrderItem).filter(
        and_(
            SalesOrderItem.sales_order_id == sales_order_id,
            SalesOrderItem.deleted_at.is_(None)
        )
    ).order_by(SalesOrderItem.line_number).all()


def update_order_item(
    db: Session,
    item_id: int,
    item_data: SalesOrderItemCreate,
    updated_by: int
) -> Optional[SalesOrderItem]:
    """Update sales order item."""
    item = db.query(SalesOrderItem).filter(
        and_(
            SalesOrderItem.id == item_id,
            SalesOrderItem.deleted_at.is_(None)
        )
    ).first()
    
    if not item:
        return None
    
    # Check if order can be updated
    sales_order = get_sales_order_by_id(db, item.sales_order_id)
    if sales_order and sales_order.status in [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value]:
        raise BusinessLogicError("Cannot update items for completed or cancelled orders")
    
    # Update fields
    update_dict = item_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(item, key):
            setattr(item, key, value)
    
    # Recalculate totals
    item.calculate_total_amount()
    
    item.updated_by = updated_by
    
    db.add(item)
    
    # Recalculate order totals
    if sales_order:
        sales_order.calculate_totals()
        db.add(sales_order)
    
    db.commit()
    db.refresh(item)
    
    return item


def generate_order_number(db: Session, organization_id: int) -> str:
    """Generate unique sales order number."""
    # Get current date for prefix
    today = date.today()
    prefix = f"SO-{today.strftime('%Y%m%d')}"
    
    # Get next sequence number for today
    last_order = db.query(SalesOrder).filter(
        and_(
            SalesOrder.order_number.like(f"{prefix}-%"),
            SalesOrder.organization_id == organization_id
        )
    ).order_by(desc(SalesOrder.id)).first()
    
    if last_order and last_order.order_number:
        try:
            last_number = int(last_order.order_number.split('-')[2])
            next_number = last_number + 1
        except (IndexError, ValueError):
            next_number = 1
    else:
        next_number = 1
    
    return f"{prefix}-{next_number:04d}"


def generate_customer_number(db: Session, organization_id: int) -> str:
    """Generate unique customer number."""
    # Get next sequence number
    last_customer = db.query(Customer).filter(
        and_(
            Customer.customer_number.like("CU-%"),
            Customer.organization_id == organization_id
        )
    ).order_by(desc(Customer.id)).first()
    
    if last_customer and last_customer.customer_number:
        try:
            last_number = int(last_customer.customer_number.split('-')[1])
            next_number = last_number + 1
        except (IndexError, ValueError):
            next_number = 1
    else:
        next_number = 1
    
    return f"CU-{next_number:06d}"


def get_sales_statistics(
    db: Session, 
    organization_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> Dict[str, Any]:
    """Get comprehensive sales statistics."""
    query = db.query(SalesOrder).filter(SalesOrder.deleted_at.is_(None))
    
    if organization_id:
        query = query.filter(SalesOrder.organization_id == organization_id)
    
    if from_date:
        query = query.filter(SalesOrder.order_date >= from_date)
    
    if to_date:
        query = query.filter(SalesOrder.order_date <= to_date)
    
    # Basic counts
    total_orders = query.count()
    completed_orders = query.filter(SalesOrder.status == OrderStatus.COMPLETED.value).count()
    pending_orders = query.filter(SalesOrder.status == OrderStatus.PENDING.value).count()
    
    # Revenue calculations
    total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        and_(
            SalesOrder.deleted_at.is_(None),
            SalesOrder.status != OrderStatus.CANCELLED.value,
            SalesOrder.organization_id == organization_id if organization_id else True,
            SalesOrder.order_date >= from_date if from_date else True,
            SalesOrder.order_date <= to_date if to_date else True
        )
    ).scalar() or Decimal(0)
    
    # Orders by status
    status_counts = {}
    for status in OrderStatus:
        count = query.filter(SalesOrder.status == status.value).count()
        status_counts[status.value] = count
    
    # Payment status counts
    payment_status_counts = {}
    for payment_status in PaymentStatus:
        count = query.filter(SalesOrder.payment_status == payment_status.value).count()
        payment_status_counts[payment_status.value] = count
    
    # Customer count
    customer_count = db.query(Customer).filter(
        and_(
            Customer.deleted_at.is_(None),
            Customer.organization_id == organization_id if organization_id else True
        )
    ).count()
    
    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "total_revenue": float(total_revenue),
        "average_order_value": float(total_revenue / total_orders) if total_orders > 0 else 0,
        "by_status": status_counts,
        "by_payment_status": payment_status_counts,
        "customer_count": customer_count
    }


def convert_customer_to_response(customer: Customer) -> CustomerResponse:
    """Convert Customer model to response schema."""
    return CustomerResponse(
        id=customer.id,
        customer_number=customer.customer_number,
        name=customer.name,
        name_en=customer.name_en,
        display_name=customer.display_name,
        customer_type=customer.customer_type,
        organization_id=customer.organization_id,
        email=customer.email,
        phone=customer.phone,
        mobile=customer.mobile,
        billing_address=customer.billing_address,
        billing_postal_code=customer.billing_postal_code,
        billing_city=customer.billing_city,
        billing_prefecture=customer.billing_prefecture,
        billing_country=customer.billing_country,
        full_billing_address=customer.full_billing_address,
        shipping_address=customer.shipping_address,
        shipping_postal_code=customer.shipping_postal_code,
        shipping_city=customer.shipping_city,
        shipping_prefecture=customer.shipping_prefecture,
        shipping_country=customer.shipping_country,
        full_shipping_address=customer.full_shipping_address,
        tax_registration_number=customer.tax_registration_number,
        business_registration_number=customer.business_registration_number,
        industry=customer.industry,
        credit_limit=customer.credit_limit,
        current_balance=customer.current_balance,
        credit_available=customer.credit_available,
        payment_terms=customer.payment_terms,
        status=customer.status,
        preferred_payment_method=customer.preferred_payment_method,
        currency=customer.currency,
        first_order_date=customer.first_order_date,
        last_order_date=customer.last_order_date,
        total_orders=customer.total_orders,
        total_sales_amount=customer.total_sales_amount,
        contact_person_name=customer.contact_person_name,
        contact_person_email=customer.contact_person_email,
        contact_person_phone=customer.contact_person_phone,
        is_over_credit_limit=customer.is_over_credit_limit,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


def convert_sales_order_to_response(order: SalesOrder) -> SalesOrderResponse:
    """Convert SalesOrder model to response schema."""
    return SalesOrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        organization_id=order.organization_id,
        order_date=order.order_date,
        required_date=order.required_date,
        shipped_date=order.shipped_date,
        delivery_date=order.delivery_date,
        status=order.status,
        subtotal_amount=order.subtotal_amount,
        tax_amount=order.tax_amount,
        discount_amount=order.discount_amount,
        shipping_amount=order.shipping_amount,
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        payment_terms=order.payment_terms,
        payment_due_date=order.payment_due_date,
        shipping_address=order.shipping_address,
        full_shipping_address=order.full_shipping_address,
        shipping_method=order.shipping_method,
        tracking_number=order.tracking_number,
        customer_po_number=order.customer_po_number,
        sales_rep_id=order.sales_rep_id,
        notes=order.notes,
        currency=order.currency,
        exchange_rate=order.exchange_rate,
        is_overdue=order.is_overdue,
        days_until_due=order.days_until_due,
        created_at=order.created_at,
        updated_at=order.updated_at
    )