from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    # 組織情報
    organization_type = Column(String(50))  # corporation, division, department, team
    industry = Column(String(100))
    tax_id = Column(String(50))
    registration_number = Column(String(50))
    
    # 連絡先情報
    email = Column(String(200))
    phone = Column(String(50))
    fax = Column(String(50))
    website = Column(String(200))
    
    # 住所情報
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Japan")
    
    # 階層構造
    parent_id = Column(String, ForeignKey('organizations.id'))
    level = Column(Integer, default=0)
    path = Column(Text)  # /root/parent/child 形式のパス
    
    # ステータス
    is_active = Column(Boolean, default=True)
    is_headquarters = Column(Boolean, default=False)
    
    # メタデータ
    metadata_json = Column(JSON, default={})
    settings = Column(JSON, default={})
    
    # 財務情報
    annual_revenue = Column(Decimal(15, 2))
    employee_count = Column(Integer)
    
    # タイムスタンプ
    established_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    parent = relationship("Organization", remote_side=[id], back_populates="children")
    children = relationship("Organization", back_populates="parent")
    departments = relationship("Department", back_populates="organization")
    employees = relationship("User", back_populates="organization")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    
    # 組織関連
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    parent_department_id = Column(String, ForeignKey('departments.id'))
    
    # 部署情報
    department_type = Column(String(50))  # operational, support, management
    cost_center = Column(String(50))
    budget = Column(Decimal(12, 2))
    location = Column(String(200))
    
    # マネージャー
    manager_id = Column(String, ForeignKey('users.id'))
    
    # ステータス
    is_active = Column(Boolean, default=True)
    
    # メタデータ
    settings = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    organization = relationship("Organization", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], back_populates="child_departments")
    child_departments = relationship("Department", back_populates="parent_department")
    employees = relationship("User", back_populates="department")
    manager = relationship("User", foreign_keys=[manager_id])

class OrganizationAddress(Base):
    __tablename__ = "organization_addresses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    address_type = Column(String(50), nullable=False)  # headquarters, branch, warehouse, etc.
    
    # 住所情報
    name = Column(String(200))  # 拠点名
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="Japan")
    
    # 連絡先
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(200))
    
    # ステータス
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # 位置情報
    latitude = Column(Decimal(10, 8))
    longitude = Column(Decimal(11, 8))
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    organization = relationship("Organization")

class OrganizationContact(Base):
    __tablename__ = "organization_contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    
    # 連絡先情報
    name = Column(String(200), nullable=False)
    title = Column(String(100))
    department = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    mobile = Column(String(50))
    
    # 連絡先種別
    contact_type = Column(String(50))  # primary, billing, technical, emergency
    
    # ステータス
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # メタデータ
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    organization = relationship("Organization")