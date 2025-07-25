from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.database_simple import Base

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions_v20"

    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey('products_v20.id'), nullable=False)
    transaction_type = Column(String, nullable=False)  # 'in', 'out', 'adjustment'
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    reference_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, nullable=True)

class StockLevel(Base):
    __tablename__ = "stock_levels_v20"

    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey('products_v20.id'), nullable=False, unique=True)
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)
    max_stock = Column(Integer, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String, nullable=True)