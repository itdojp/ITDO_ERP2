"""
Employee model implementation for ERP system
"""

from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.organization import Organization
    from app.models.department import Department


class Employee(SoftDeletableModel):
    """Employee model for ERP system with comprehensive employee management"""

    __tablename__ = "employees"

    # Employee identification
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Related user and organization
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name_kana: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name_kana: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Birth and personal details
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)  # male, female, other
    nationality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Address information
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    prefecture: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Employment information
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full_time")  # full_time, part_time, contract, intern
    employment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, inactive, terminated, on_leave
    
    # Employment dates
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Salary and compensation
    base_salary: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    pay_frequency: Mapped[str | None] = mapped_column(String(20), nullable=True)  # monthly, bi_weekly, weekly
    
    # Manager and reporting
    manager_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Work schedule
    work_hours_per_day: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True, default=8.0)
    work_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True, default=5)
    
    # Additional information
    emergency_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emergency_contact_relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Benefits and leave
    annual_leave_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=20)
    sick_leave_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=10)
    
    # Notes and comments
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="employee_profile")
    organization: Mapped["Organization"] = relationship("Organization")
    department: Mapped["Department | None"] = relationship("Department")
    manager: Mapped["Employee | None"] = relationship("Employee", remote_side="Employee.id")
    direct_reports: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="manager", remote_side="Employee.manager_id"
    )
    
    @property
    def full_name(self) -> str:
        """Get employee's full name"""
        return f"{self.last_name} {self.first_name}"
    
    @property
    def full_name_kana(self) -> str:
        """Get employee's full name in Katakana"""
        if self.last_name_kana and self.first_name_kana:
            return f"{self.last_name_kana} {self.first_name_kana}"
        return ""
    
    @property
    def age(self) -> int | None:
        """Calculate employee's age"""
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def years_of_service(self) -> int:
        """Calculate years of service"""
        if not self.hire_date:
            return 0
        end_date = self.termination_date or date.today()
        return end_date.year - self.hire_date.year - ((end_date.month, end_date.day) < (self.hire_date.month, self.hire_date.day))
    
    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        parts = []
        if self.postal_code:
            parts.append(f"〒{self.postal_code}")
        if self.prefecture:
            parts.append(self.prefecture)
        if self.city:
            parts.append(self.city)
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        return " ".join(parts) if parts else ""
    
    def is_on_contract(self) -> bool:
        """Check if employee is currently on contract"""
        return self.employment_type == "contract"
    
    def is_manager(self) -> bool:
        """Check if employee is a manager (has direct reports)"""
        return len(self.direct_reports) > 0
    
    def get_reporting_hierarchy(self) -> list["Employee"]:
        """Get the full reporting hierarchy from CEO to this employee"""
        hierarchy = [self]
        current = self
        while current.manager:
            hierarchy.insert(0, current.manager)
            current = current.manager
        return hierarchy
    
    def can_manage(self, other_employee: "Employee") -> bool:
        """Check if this employee can manage another employee"""
        # Check direct report
        if other_employee.manager_id == self.id:
            return True
        
        # Check if other employee is in reporting hierarchy
        hierarchy = other_employee.get_reporting_hierarchy()
        return self in hierarchy[:-1]  # Exclude the employee themselves
    
    def __str__(self) -> str:
        return f"{self.employee_number} - {self.full_name}"
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, number='{self.employee_number}', name='{self.full_name}')>"