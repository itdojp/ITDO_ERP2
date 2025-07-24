"""Expense Category model implementation for financial management."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId

if TYPE_CHECKING:
    from app.models.organization import Organization


class ExpenseCategory(SoftDeletableModel):
    """費目マスタ - Expense category master for financial management."""

    __tablename__ = "expense_categories"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Expense category code"
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Expense category name"
    )
    name_en: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Expense category name in English"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Expense category description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        comment="Organization ID for multi-tenant support"
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("expense_categories.id"),
        nullable=True,
        comment="Parent category ID for hierarchical structure"
    )

    # Category details
    category_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category type: fixed/variable/capital"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Active status"
    )
    is_taxable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this category is subject to tax"
    )
    requires_receipt: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether receipt is required for this category"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Sort order for display"
    )

    # Approval settings
    approval_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether approval is required for this category"
    )
    approval_limit: Mapped[float | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Amount threshold for approval requirement"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="select"
    )
    parent: Mapped["ExpenseCategory | None"] = relationship(
        "ExpenseCategory",
        remote_side="ExpenseCategory.id",
        back_populates="children"
    )
    children: Mapped[List["ExpenseCategory"]] = relationship(
        "ExpenseCategory",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    # Computed properties
    @property
    def full_name(self) -> str:
        """Get full category name with parent hierarchy."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    @property
    def level(self) -> int:
        """Get hierarchy level (0 for root categories)."""
        if self.parent:
            return self.parent.level + 1
        return 0

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf category (no children)."""
        return len(self.children) == 0

    @property
    def path(self) -> str:
        """Get category path from root to this category."""
        if self.parent:
            return f"{self.parent.path}/{self.code}"
        return self.code

    def get_all_descendants(self) -> List["ExpenseCategory"]:
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_ancestors(self) -> List["ExpenseCategory"]:
        """Get all ancestor categories up to root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def can_be_deleted(self) -> bool:
        """Check if category can be deleted (no children and not used in expenses)."""
        # Check if has children
        if self.children:
            return False

        # TODO: Check if used in expenses/budgets when those models are implemented
        return True

    def __str__(self) -> str:
        """String representation."""
        return f"{self.code} - {self.name}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<ExpenseCategory(id={self.id}, code='{self.code}', name='{self.name}')>"


# Create default expense categories for new organizations
DEFAULT_EXPENSE_CATEGORIES = [
    {
        "code": "TRAVEL",
        "name": "交通費",
        "name_en": "Travel Expenses",
        "category_type": "variable",
        "children": [
            {
                "code": "TRAVEL_TRAIN",
                "name": "電車・バス",
                "name_en": "Train & Bus",
                "category_type": "variable",
            },
            {
                "code": "TRAVEL_TAXI",
                "name": "タクシー",
                "name_en": "Taxi",
                "category_type": "variable",
            },
            {
                "code": "TRAVEL_FLIGHT",
                "name": "航空券",
                "name_en": "Flight",
                "category_type": "variable",
            },
        ],
    },
    {
        "code": "MEAL",
        "name": "接待交際費",
        "name_en": "Entertainment Expenses",
        "category_type": "variable",
        "children": [
            {
                "code": "MEAL_BUSINESS",
                "name": "会議費",
                "name_en": "Business Meetings",
                "category_type": "variable",
            },
            {
                "code": "MEAL_ENTERTAIN",
                "name": "接待費",
                "name_en": "Entertainment",
                "category_type": "variable",
            },
        ],
    },
    {
        "code": "OFFICE",
        "name": "事務用品",
        "name_en": "Office Supplies",
        "category_type": "variable",
        "children": [
            {
                "code": "OFFICE_SUPPLY",
                "name": "消耗品",
                "name_en": "Consumables",
                "category_type": "variable",
            },
            {
                "code": "OFFICE_EQUIPMENT",
                "name": "備品",
                "name_en": "Equipment",
                "category_type": "capital",
            },
        ],
    },
    {
        "code": "COMMUNICATION",
        "name": "通信費",
        "name_en": "Communication Expenses",
        "category_type": "fixed",
        "children": [
            {
                "code": "COMM_PHONE",
                "name": "電話代",
                "name_en": "Phone",
                "category_type": "fixed",
            },
            {
                "code": "COMM_INTERNET",
                "name": "インターネット",
                "name_en": "Internet",
                "category_type": "fixed",
            },
        ],
    },
    {
        "code": "TRAINING",
        "name": "研修費",
        "name_en": "Training Expenses",
        "category_type": "variable",
        "children": [
            {
                "code": "TRAINING_EXTERNAL",
                "name": "外部研修",
                "name_en": "External Training",
                "category_type": "variable",
            },
            {
                "code": "TRAINING_BOOK",
                "name": "書籍・資料",
                "name_en": "Books & Materials",
                "category_type": "variable",
            },
        ],
    },
]
