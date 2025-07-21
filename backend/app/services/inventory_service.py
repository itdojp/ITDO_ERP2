"""Inventory management service."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.core.base_service import BaseService
from app.core.exceptions import BusinessLogicError, NotFound
from app.core.monitoring import monitor_performance
from app.core.service_registry import register_service
from app.models.inventory import (
    Category, Product, StockMovement, ProductSerial, InventoryLocation
)
from app.models.user import User
from app.schemas.inventory import (
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    StockMovementCreate,
    ProductSerialCreate, ProductSerialUpdate,
    InventoryLocationCreate, InventoryLocationUpdate,
    StockMovementFilters, ProductFilters,
    InventoryReport, ProductStockSummary
)


@register_service(name="inventory", aliases=["stock", "products"])
class InventoryService(BaseService[Product]):
    """Inventory management service with comprehensive stock operations."""

    def __init__(self, db: Union[Session, AsyncSession]):
        """Initialize inventory service."""
        super().__init__(Product, db)

    # Category Management
    @monitor_performance("inventory.create_category")
    async def create_category(
        self, 
        data: CategoryCreate, 
        organization_id: Optional[int] = None
    ) -> Category:
        """Create a new product category."""
        category_dict = data.dict()
        if organization_id:
            category_dict['organization_id'] = organization_id
        
        # Validate parent category exists
        if category_dict.get('parent_id'):
            parent = await self._get_category_by_id(category_dict['parent_id'])
            if not parent:
                raise NotFound("Parent category not found")
            
            # Prevent circular references
            if await self._would_create_circular_reference(
                category_dict['parent_id'], 
                category_dict.get('id')
            ):
                raise BusinessLogicError("Circular reference detected in category hierarchy")
        
        category = Category(**category_dict)
        self.db.add(category)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(category)
        else:  # Session
            self.db.commit()
            self.db.refresh(category)
        
        return category

    @monitor_performance("inventory.get_categories")
    async def get_categories(
        self, 
        organization_id: Optional[int] = None,
        include_children: bool = False
    ) -> List[Category]:
        """Get all categories with optional hierarchy."""
        query = select(Category)
        
        if organization_id:
            query = query.where(Category.organization_id == organization_id)
        
        query = query.where(Category.is_active == True)
        query = query.order_by(Category.sort_order, Category.name)
        
        if include_children:
            query = query.options(joinedload(Category.children))
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return list(result.scalars().unique().all())
        else:  # Session
            return list(self.db.execute(query).scalars().unique().all())

    # Product Management
    @monitor_performance("inventory.create_product")
    async def create_product(
        self, 
        data: ProductCreate, 
        organization_id: Optional[int] = None
    ) -> Product:
        """Create a new product with validation."""
        product_dict = data.dict()
        if organization_id:
            product_dict['organization_id'] = organization_id
        
        # Validate SKU uniqueness within organization
        existing_product = await self._get_product_by_sku(
            product_dict['sku'], 
            organization_id
        )
        if existing_product:
            raise BusinessLogicError(f"Product with SKU '{product_dict['sku']}' already exists")
        
        # Validate category exists
        if product_dict.get('category_id'):
            category = await self._get_category_by_id(product_dict['category_id'])
            if not category:
                raise NotFound("Category not found")
        
        # Initialize stock tracking
        product_dict['current_stock'] = 0
        
        product = Product(**product_dict)
        self.db.add(product)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(product)
        else:  # Session
            self.db.commit()
            self.db.refresh(product)
        
        return product

    @monitor_performance("inventory.update_product")
    async def update_product(
        self, 
        product_id: int, 
        data: ProductUpdate, 
        organization_id: Optional[int] = None
    ) -> Product:
        """Update product with validation."""
        product = await self.get_by_id(product_id, organization_id)
        if not product:
            raise NotFound("Product not found")
        
        update_dict = data.dict(exclude_unset=True)
        
        # Validate SKU uniqueness if being updated
        if 'sku' in update_dict:
            existing_product = await self._get_product_by_sku(
                update_dict['sku'], 
                organization_id,
                exclude_id=product_id
            )
            if existing_product:
                raise BusinessLogicError(f"Product with SKU '{update_dict['sku']}' already exists")
        
        # Update product fields
        for field, value in update_dict.items():
            setattr(product, field, value)
        
        product.updated_at = datetime.utcnow()
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(product)
        else:  # Session
            self.db.commit()
            self.db.refresh(product)
        
        return product

    @monitor_performance("inventory.get_products")
    async def get_products(
        self, 
        filters: Optional[ProductFilters] = None,
        organization_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Product]:
        """Get products with filtering and pagination."""
        query = select(Product)
        
        # Organization filter
        if organization_id:
            query = query.where(Product.organization_id == organization_id)
        
        # Apply filters
        if filters:
            if filters.category_id:
                query = query.where(Product.category_id == filters.category_id)
            
            if filters.sku:
                query = query.where(Product.sku.ilike(f"%{filters.sku}%"))
            
            if filters.barcode:
                query = query.where(Product.barcode == filters.barcode)
            
            if filters.is_active is not None:
                query = query.where(Product.is_active == filters.is_active)
            
            if filters.track_quantity is not None:
                query = query.where(Product.track_quantity == filters.track_quantity)
            
            if filters.low_stock:
                query = query.where(Product.current_stock <= Product.minimum_stock)
            
            if filters.out_of_stock:
                query = query.where(Product.current_stock == 0)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        Product.name.ilike(search_term),
                        Product.sku.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
        
        # Pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        # Ordering
        query = query.order_by(Product.name)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return list(result.scalars().all())
        else:  # Session
            return list(self.db.execute(query).scalars().all())

    # Stock Movement Management
    @monitor_performance("inventory.create_stock_movement")
    async def create_stock_movement(
        self, 
        data: StockMovementCreate, 
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> StockMovement:
        """Create stock movement and update product stock."""
        product = await self.get_by_id(data.product_id, organization_id)
        if not product:
            raise NotFound("Product not found")
        
        if not product.track_quantity:
            raise BusinessLogicError("Product does not track quantity")
        
        # Calculate new stock level
        previous_stock = product.current_stock
        
        if data.movement_type in ['in', 'return']:
            new_stock = previous_stock + abs(data.quantity)
        elif data.movement_type == 'out':
            new_stock = previous_stock - abs(data.quantity)
            if new_stock < 0:
                raise BusinessLogicError("Insufficient stock for outgoing movement")
        elif data.movement_type == 'adjustment':
            new_stock = previous_stock + data.quantity
            if new_stock < 0:
                raise BusinessLogicError("Stock adjustment would result in negative stock")
        else:
            raise BusinessLogicError(f"Invalid movement type: {data.movement_type}")
        
        # Calculate costs
        total_cost = None
        if data.unit_cost and data.quantity:
            total_cost = data.unit_cost * abs(data.quantity)
        
        # Create stock movement record
        movement_dict = data.dict()
        movement_dict.update({
            'previous_stock': previous_stock,
            'new_stock': new_stock,
            'total_cost': total_cost,
            'user_id': user_id,
            'organization_id': organization_id
        })
        
        stock_movement = StockMovement(**movement_dict)
        self.db.add(stock_movement)
        
        # Update product stock
        product.current_stock = new_stock
        product.updated_at = datetime.utcnow()
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(stock_movement)
        else:  # Session
            self.db.commit()
            self.db.refresh(stock_movement)
        
        return stock_movement

    @monitor_performance("inventory.get_stock_movements")
    async def get_stock_movements(
        self,
        filters: Optional[StockMovementFilters] = None,
        organization_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[StockMovement]:
        """Get stock movements with filtering."""
        query = select(StockMovement)
        
        # Organization filter
        if organization_id:
            query = query.where(StockMovement.organization_id == organization_id)
        
        # Apply filters
        if filters:
            if filters.product_id:
                query = query.where(StockMovement.product_id == filters.product_id)
            
            if filters.movement_type:
                query = query.where(StockMovement.movement_type == filters.movement_type)
            
            if filters.date_from:
                query = query.where(StockMovement.movement_date >= filters.date_from)
            
            if filters.date_to:
                query = query.where(StockMovement.movement_date <= filters.date_to)
            
            if filters.user_id:
                query = query.where(StockMovement.user_id == filters.user_id)
        
        # Pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        # Ordering
        query = query.order_by(desc(StockMovement.movement_date))
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return list(result.scalars().all())
        else:  # Session
            return list(self.db.execute(query).scalars().all())

    # Analytics and Reporting
    @monitor_performance("inventory.get_inventory_report")
    async def get_inventory_report(
        self, 
        organization_id: Optional[int] = None
    ) -> InventoryReport:
        """Generate comprehensive inventory report."""
        # Total products count
        products_query = select(func.count(Product.id))
        if organization_id:
            products_query = products_query.where(Product.organization_id == organization_id)
        products_query = products_query.where(Product.is_active == True)
        
        # Total inventory value
        value_query = select(func.sum(Product.current_stock * Product.unit_price))
        if organization_id:
            value_query = value_query.where(Product.organization_id == organization_id)
        value_query = value_query.where(Product.is_active == True)
        
        # Low stock products
        low_stock_query = select(func.count(Product.id)).where(
            and_(
                Product.current_stock <= Product.minimum_stock,
                Product.track_quantity == True,
                Product.is_active == True
            )
        )
        if organization_id:
            low_stock_query = low_stock_query.where(Product.organization_id == organization_id)
        
        # Out of stock products
        out_stock_query = select(func.count(Product.id)).where(
            and_(
                Product.current_stock == 0,
                Product.track_quantity == True,
                Product.is_active == True
            )
        )
        if organization_id:
            out_stock_query = out_stock_query.where(Product.organization_id == organization_id)
        
        # Categories count
        categories_query = select(func.count(Category.id))
        if organization_id:
            categories_query = categories_query.where(Category.organization_id == organization_id)
        categories_query = categories_query.where(Category.is_active == True)
        
        # Today's movements
        today = datetime.utcnow().date()
        movements_query = select(func.count(StockMovement.id)).where(
            func.date(StockMovement.movement_date) == today
        )
        if organization_id:
            movements_query = movements_query.where(StockMovement.organization_id == organization_id)
        
        # Execute queries
        if hasattr(self.db, 'execute'):  # AsyncSession
            total_products = (await self.db.execute(products_query)).scalar() or 0
            total_value = (await self.db.execute(value_query)).scalar() or Decimal('0')
            low_stock = (await self.db.execute(low_stock_query)).scalar() or 0
            out_stock = (await self.db.execute(out_stock_query)).scalar() or 0
            categories_count = (await self.db.execute(categories_query)).scalar() or 0
            movements_today = (await self.db.execute(movements_query)).scalar() or 0
        else:  # Session
            total_products = self.db.execute(products_query).scalar() or 0
            total_value = self.db.execute(value_query).scalar() or Decimal('0')
            low_stock = self.db.execute(low_stock_query).scalar() or 0
            out_stock = self.db.execute(out_stock_query).scalar() or 0
            categories_count = self.db.execute(categories_query).scalar() or 0
            movements_today = self.db.execute(movements_query).scalar() or 0
        
        return InventoryReport(
            total_products=total_products,
            total_value=total_value,
            low_stock_products=low_stock,
            out_of_stock_products=out_stock,
            categories_count=categories_count,
            movements_today=movements_today,
            organization_id=organization_id,
            generated_at=datetime.utcnow()
        )

    # Helper methods
    async def _get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(
                select(Category).where(Category.id == category_id)
            )
            return result.scalar_one_or_none()
        else:  # Session
            return self.db.execute(
                select(Category).where(Category.id == category_id)
            ).scalar_one_or_none()

    async def _get_product_by_sku(
        self, 
        sku: str, 
        organization_id: Optional[int] = None,
        exclude_id: Optional[int] = None
    ) -> Optional[Product]:
        """Get product by SKU."""
        query = select(Product).where(Product.sku == sku)
        
        if organization_id:
            query = query.where(Product.organization_id == organization_id)
        
        if exclude_id:
            query = query.where(Product.id != exclude_id)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        else:  # Session
            return self.db.execute(query).scalar_one_or_none()

    async def _would_create_circular_reference(
        self, 
        parent_id: int, 
        category_id: Optional[int] = None
    ) -> bool:
        """Check if setting parent would create circular reference."""
        if not category_id or parent_id == category_id:
            return True
        
        # Simple circular reference check (for production, implement full tree traversal)
        parent = await self._get_category_by_id(parent_id)
        while parent and parent.parent_id:
            if parent.parent_id == category_id:
                return True
            parent = await self._get_category_by_id(parent.parent_id)
        
        return False