"""Organization schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class OrganizationBase(BaseModel):
    """Base organization schema."""

    code: str = Field(..., min_length=1, max_length=50, description="組織コード")
    name: str = Field(..., min_length=1, max_length=255, description="組織名")
    name_kana: Optional[str] = Field(None, max_length=255, description="組織名（カナ）")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    email: Optional[str] = Field(None, max_length=255, description="メールアドレス")
    website: Optional[str] = Field(None, max_length=255, description="ウェブサイト")
    fiscal_year_start: int = Field(4, ge=1, le=12, description="会計年度開始月")

    @validator("email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v

    @validator("fiscal_year_start")
    def validate_fiscal_year_start(cls, v):
        if v < 1 or v > 12:
            raise ValueError("会計年度開始月は1-12の範囲で入力してください")
        return v


class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""

    pass


class OrganizationUpdate(BaseModel):
    """Organization update schema."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="組織名"
    )
    name_kana: Optional[str] = Field(None, max_length=255, description="組織名（カナ）")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    email: Optional[str] = Field(None, max_length=255, description="メールアドレス")
    website: Optional[str] = Field(None, max_length=255, description="ウェブサイト")
    fiscal_year_start: Optional[int] = Field(
        None, ge=1, le=12, description="会計年度開始月"
    )

    @validator("email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v


class OrganizationResponse(OrganizationBase):
    """Organization response schema."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class OrganizationList(BaseModel):
    """Organization list response schema."""

    items: list[OrganizationResponse]
    total: int
    page: int = 1
    limit: int = 10

    class Config:
        from_attributes = True
