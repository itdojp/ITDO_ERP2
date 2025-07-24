from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from app.core.database_simple import Base

class SalesOrder(Base):
    __tablename__ = "sales_orders_v20"

    id = Column(String, primary_key=True)
    order_number = Column(String, unique=True, nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default='pending')  # pending, confirmed, shipped, delivered, cancelled
    total_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items_v20"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('sales_orders_v20.id'), nullable=False)
    product_id = Column(String, ForeignKey('products_v20.id'), nullable=False)
    product_name = Column(String, nullable=False)  # Snapshot at time of order
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.1)  # 10% tax
    notes = Column(Text, nullable=True)