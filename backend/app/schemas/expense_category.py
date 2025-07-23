"""Expense category schemas for API serialization and validation."""

from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.base import BaseResponse


class ExpenseCategoryBase(BaseModel):
    """Base schema for expense categories."""

    code: str = Field(..., max_length=50, description="Expense category code")
    name: str = Field(..., max_length=200, description="Expense category name")
    name_en: Optional[str] = Field(None, max_length=200, description="Name in English")
    description: Optional[str] = Field(None, description="Category description")
    category_type: str = Field(..., description="Category type: fixed/variable/capital")
    is_active: bool = Field(True, description="Active status")
    is_taxable: bool = Field(True, description="Whether subject to tax")
    requires_receipt: bool = Field(True, description="Whether receipt is required")
    approval_required: bool = Field(True, description="Whether approval is required")
    approval_limit: Optional[float] = Field(
        None, ge=0, description="Approval limit amount"
    )
    sort_order: int = Field(0, description="Sort order")
    parent_id: Optional[int] = Field(None, description="Parent category ID")

    @validator("category_type")
    def validate_category_type(cls, v):
        allowed_types = ["fixed", "variable", "capital"]
        if v not in allowed_types:
            raise ValueError(
                f"Category type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @validator("code")
    def validate_code(cls, v):
        # Code should be uppercase alphanumeric with underscores
        import re

        if not re.match(r"^[A-Z0-9_]+$", v):
            raise ValueError(
                "Code must contain only uppercase letters, numbers, and underscores"
            )
        return v


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating expense categories."""

    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating expense categories."""

    code: Optional[str] = Field(
        None, max_length=50, description="Expense category code"
    )
    name: Optional[str] = Field(
        None, max_length=200, description="Expense category name"
    )
    name_en: Optional[str] = Field(None, max_length=200, description="Name in English")
    description: Optional[str] = Field(None, description="Category description")
    category_type: Optional[str] = Field(None, description="Category type")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_taxable: Optional[bool] = Field(None, description="Whether subject to tax")
    requires_receipt: Optional[bool] = Field(
        None, description="Whether receipt is required"
    )
    approval_required: Optional[bool] = Field(
        None, description="Whether approval is required"
    )
    approval_limit: Optional[float] = Field(
        None, ge=0, description="Approval limit amount"
    )
    sort_order: Optional[int] = Field(None, description="Sort order")
    parent_id: Optional[int] = Field(None, description="Parent category ID")

    @validator("category_type")
    def validate_category_type(cls, v):
        if v is not None:
            allowed_types = ["fixed", "variable", "capital"]
            if v not in allowed_types:
                raise ValueError(
                    f"Category type must be one of: {', '.join(allowed_types)}"
                )
        return v

    @validator("code")
    def validate_code(cls, v):
        if v is not None:
            import re

            if not re.match(r"^[A-Z0-9_]+$", v):
                raise ValueError(
                    "Code must contain only uppercase letters, numbers, and underscores"
                )
        return v


class ExpenseCategoryResponse(ExpenseCategoryBase, BaseResponse):
    """Schema for expense category responses."""

    id: int
    organization_id: int

    # Computed properties
    full_name: str
    level: int
    is_leaf: bool
    path: str

    # Relationships
    organization: Optional[dict] = Field(None, description="Organization details")
    parent: Optional[dict] = Field(None, description="Parent category details")
    children: List["ExpenseCategoryResponse"] = Field(
        default_factory=list, description="Child categories"
    )

    class Config:
        from_attributes = True


class ExpenseCategoryTree(BaseModel):
    """Schema for expense category tree structure."""

    id: int
    code: str
    name: str
    name_en: Optional[str]
    category_type: str
    is_active: bool
    level: int
    full_name: str
    children: List["ExpenseCategoryTree"] = Field(
        default_factory=list, description="Child categories"
    )

    class Config:
        from_attributes = True


<<<<<<< HEAD
# Alias for backward compatibility
ExpenseCategoryTreeResponse = ExpenseCategoryTree
=======
class ExpenseCategoryTreeResponse(BaseModel):
    """Schema for expense category tree response."""

    tree: List[ExpenseCategoryTree] = Field(
        default_factory=list, description="Category tree structure"
    )
    total_categories: int = Field(..., description="Total number of categories")
    max_depth: int = Field(..., description="Maximum tree depth")

    class Config:
        from_attributes = True
>>>>>>> main


class ExpenseCategoryListResponse(BaseModel):
    """Schema for expense category list responses."""

    items: List[ExpenseCategoryResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class ExpenseCategoryHierarchy(BaseModel):
    """Schema for expense category hierarchy."""

    roots: List[ExpenseCategoryTree] = Field(
        default_factory=list, description="Root categories"
    )
    total_categories: int
    max_depth: int

    class Config:
        from_attributes = True


class ExpenseCategoryMove(BaseModel):
    """Schema for moving expense categories."""

    new_parent_id: Optional[int] = Field(
        None, description="New parent category ID (None for root)"
    )
    new_sort_order: Optional[int] = Field(None, description="New sort order")


class ExpenseCategoryBulkCreate(BaseModel):
    """Schema for bulk creating expense categories."""

    categories: List[ExpenseCategoryCreate] = Field(..., description="Categories to create")

    @validator("categories")
    def validate_categories(cls, v):
        if not v:
            raise ValueError("At least one category must be provided")
        return v


class ExpenseCategoryBulkUpdate(BaseModel):
    """Schema for bulk updating expense categories."""

    category_ids: List[int] = Field(..., description="Category IDs to update")
    updates: ExpenseCategoryUpdate = Field(..., description="Updates to apply")

    @validator("category_ids")
    def validate_category_ids(cls, v):
        if not v:
            raise ValueError("At least one category ID must be provided")
        return v


class ExpenseCategoryUsage(BaseModel):
    """Schema for expense category usage statistics."""

    category_id: int
    category_name: str
    category_code: str
    total_expenses: int
    total_amount: float
    average_amount: float
    last_used: Optional[str] = Field(None, description="Last usage date")

    class Config:
        from_attributes = True


class ExpenseCategoryAnalytics(BaseModel):
    """Schema for expense category analytics."""

    total_categories: int
    active_categories: int
    inactive_categories: int

    # Usage statistics
    most_used_categories: List[ExpenseCategoryUsage] = Field(
        default_factory=list, description="Most used categories"
    )
    least_used_categories: List[ExpenseCategoryUsage] = Field(
        default_factory=list, description="Least used categories"
    )
    unused_categories: List[dict] = Field(
        default_factory=list, description="Unused categories"
    )

    # Type breakdown
    type_breakdown: dict = Field(default_factory=dict, description="Categories by type")

    # Hierarchy statistics
    max_depth: int
    average_depth: float
    root_categories_count: int
    leaf_categories_count: int

    class Config:
        from_attributes = True


class ExpenseCategorySearch(BaseModel):
    """Schema for expense category search."""

    query: Optional[str] = Field(None, description="Search query")
    category_type: Optional[str] = Field(None, description="Filter by category type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_taxable: Optional[bool] = Field(None, description="Filter by taxable status")
    requires_receipt: Optional[bool] = Field(
        None, description="Filter by receipt requirement"
    )
    approval_required: Optional[bool] = Field(
        None, description="Filter by approval requirement"
    )
    parent_id: Optional[int] = Field(None, description="Filter by parent category")
    include_children: bool = Field(
        False, description="Include child categories in results"
    )

    @validator("category_type")
    def validate_category_type(cls, v):
        if v is not None:
            allowed_types = ["fixed", "variable", "capital"]
            if v not in allowed_types:
                raise ValueError(
                    f"Category type must be one of: {', '.join(allowed_types)}"
                )
        return v


class ExpenseCategoryImport(BaseModel):
    """Schema for importing expense categories."""

    categories: List[ExpenseCategoryCreate] = Field(
        ..., description="Categories to import"
    )
    overwrite_existing: bool = Field(
        False, description="Whether to overwrite existing categories"
    )

    @validator("categories")
    def validate_categories(cls, v):
        if not v:
            raise ValueError("At least one category must be provided")
        return v


class ExpenseCategoryExport(BaseModel):
    """Schema for exporting expense categories."""

    format: str = Field("csv", description="Export format: csv/json/xlsx")
    include_inactive: bool = Field(False, description="Include inactive categories")
    include_hierarchy: bool = Field(True, description="Include hierarchy information")

    @validator("format")
    def validate_format(cls, v):
        allowed_formats = ["csv", "json", "xlsx"]
        if v not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v


# Forward reference resolution
ExpenseCategoryResponse.model_rebuild()
ExpenseCategoryTree.model_rebuild()
