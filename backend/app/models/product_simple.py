from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.sql import func

from app.core.database_simple import Base


class Product(Base):  # type: ignore[valid-type,misc]
    """Simple product model - v19.0 practical approach"""
    __tablename__ = "products_simple"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)  # type: ignore[arg-type]
    price = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=True)  # type: ignore[arg-type]
    stock_quantity = Column(Float, default=0.0)
    category = Column(String, nullable=True)  # type: ignore[arg-type]
    is_active = Column(Boolean, default=True)
    # Simple organization reference
    organization_id = Column(String, ForeignKey('organizations_simple.id'), nullable=True)  # type: ignore[arg-type]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):  # type: ignore[no-untyped-def]
        return f"<Product(id={self.id}, code={self.code}, name={self.name})>"
