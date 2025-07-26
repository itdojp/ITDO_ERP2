from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database_simple import Base


class Product(Base):
    __tablename__ = "products_v20"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    unit_price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
