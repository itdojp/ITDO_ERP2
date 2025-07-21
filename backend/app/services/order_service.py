"""Order processing service."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.core.base_service import BaseService
from app.core.exceptions import BusinessLogicError, NotFound
from app.core.monitoring import monitor_performance
from app.core.service_registry import register_service
from app.models.order import Order, OrderItem, OrderStatusHistory, OrderPayment
from app.models.inventory import Product


@register_service(name="order", aliases=["orders", "order_processing"])
class OrderService(BaseService[Order]):
    """Order processing service with comprehensive order management."""

    def __init__(self, db: Union[Session, AsyncSession]):
        """Initialize order service."""
        super().__init__(Order, db)

    @monitor_performance("order.create_order")
    async def create_order(
        self, 
        customer_id: Optional[int],
        order_items: List[Dict],
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        order_data: Optional[Dict] = None
    ) -> Order:
        """Create a new order with items."""
        # Generate order number
        order_number = await self._generate_order_number()
        
        # Calculate totals
        subtotal = Decimal("0.00")
        for item in order_items:
            line_total = Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
            if 'discount_amount' in item:
                line_total -= Decimal(str(item['discount_amount']))
            subtotal += line_total
        
        # Create order
        order_dict = {
            'order_number': order_number,
            'customer_id': customer_id,
            'status': 'pending',
            'order_type': 'sales',
            'subtotal': subtotal,
            'total_amount': subtotal,  # Simplified calculation
            'organization_id': organization_id,
            'created_by': user_id
        }
        
        if order_data:
            order_dict.update(order_data)
        
        order = Order(**order_dict)
        self.db.add(order)
        
        # Flush to get order ID
        if hasattr(self.db, 'flush'):  # AsyncSession
            await self.db.flush()
        else:  # Session
            self.db.flush()
        
        # Create order items
        for item_data in order_items:
            # Validate product exists
            if 'product_id' in item_data:
                product = await self._get_product_by_id(item_data['product_id'])
                if not product:
                    raise NotFound(f"Product {item_data['product_id']} not found")
                
                product_name = product.name
                product_sku = product.sku
            else:
                product_name = item_data['product_name']
                product_sku = item_data['product_sku']
            
            # Calculate line total
            line_total = Decimal(str(item_data['quantity'])) * Decimal(str(item_data['unit_price']))
            if 'discount_amount' in item_data:
                line_total -= Decimal(str(item_data['discount_amount']))
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.get('product_id'),
                product_name=product_name,
                product_sku=product_sku,
                quantity=item_data['quantity'],
                unit_price=Decimal(str(item_data['unit_price'])),
                discount_amount=Decimal(str(item_data.get('discount_amount', '0.00'))),
                line_total=line_total,
                description=item_data.get('description')
            )
            self.db.add(order_item)
        
        # Create initial status history
        status_history = OrderStatusHistory(
            order_id=order.id,
            new_status='pending',
            reason='Order created',
            changed_by=user_id
        )
        self.db.add(status_history)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(order)
        else:  # Session
            self.db.commit()
            self.db.refresh(order)
        
        return order

    @monitor_performance("order.update_status")
    async def update_order_status(
        self,
        order_id: int,
        new_status: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> Order:
        """Update order status with history tracking."""
        order = await self.get_by_id(order_id, organization_id)
        if not order:
            raise NotFound("Order not found")
        
        previous_status = order.status
        
        # Validate status transition
        if not self._is_valid_status_transition(previous_status, new_status):
            raise BusinessLogicError(
                f"Invalid status transition from '{previous_status}' to '{new_status}'"
            )
        
        # Update order status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        # Set status-specific dates
        if new_status == 'shipped' and not order.shipped_date:
            order.shipped_date = datetime.utcnow()
        elif new_status == 'delivered' and not order.delivered_date:
            order.delivered_date = datetime.utcnow()
        
        # Create status history record
        status_history = OrderStatusHistory(
            order_id=order.id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            notes=notes,
            changed_by=user_id
        )
        self.db.add(status_history)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(order)
        else:  # Session
            self.db.commit()
            self.db.refresh(order)
        
        return order

    @monitor_performance("order.get_orders")
    async def get_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Order]:
        """Get orders with filtering."""
        query = select(Order).options(
            joinedload(Order.customer),
            joinedload(Order.order_items)
        )
        
        # Organization filter
        if organization_id:
            query = query.where(Order.organization_id == organization_id)
        
        # Apply filters
        if status:
            query = query.where(Order.status == status)
        
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        
        if date_from:
            query = query.where(Order.order_date >= date_from)
        
        if date_to:
            query = query.where(Order.order_date <= date_to)
        
        # Pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        # Ordering
        query = query.order_by(desc(Order.order_date))
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return list(result.scalars().unique().all())
        else:  # Session
            return list(self.db.execute(query).scalars().unique().all())

    @monitor_performance("order.process_payment")
    async def process_payment(
        self,
        order_id: int,
        payment_method: str,
        amount: Decimal,
        transaction_id: Optional[str] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> OrderPayment:
        """Process payment for an order."""
        order = await self.get_by_id(order_id, organization_id)
        if not order:
            raise NotFound("Order not found")
        
        if order.status == 'cancelled':
            raise BusinessLogicError("Cannot process payment for cancelled order")
        
        # Create payment record
        payment = OrderPayment(
            order_id=order.id,
            payment_method=payment_method,
            payment_status='completed',  # Simplified - would integrate with payment gateway
            amount=amount,
            transaction_id=transaction_id,
            payment_date=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            created_by=user_id
        )
        self.db.add(payment)
        
        # Update order status if fully paid
        if amount >= order.total_amount:
            await self.update_order_status(
                order_id,
                'confirmed',
                reason='Payment received',
                user_id=user_id,
                organization_id=organization_id
            )
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(payment)
        else:  # Session
            self.db.commit()
            self.db.refresh(payment)
        
        return payment

    # Helper methods
    async def _generate_order_number(self) -> str:
        """Generate unique order number."""
        # Simple implementation - in production, use more sophisticated numbering
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"ORD-{timestamp}"

    async def _get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(
                select(Product).where(Product.id == product_id)
            )
            return result.scalar_one_or_none()
        else:  # Session
            return self.db.execute(
                select(Product).where(Product.id == product_id)
            ).scalar_one_or_none()

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate order status transitions."""
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'returned'],
            'delivered': ['returned'],
            'cancelled': [],  # No transitions from cancelled
            'returned': []    # No transitions from returned
        }
        
        return new_status in valid_transitions.get(current_status, [])