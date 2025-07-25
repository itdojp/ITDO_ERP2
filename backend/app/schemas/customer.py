"""
Customer schemas for CRM functionality.
顧客管理スキーマ（CRM機能）
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Base schemas
class CustomerBase(BaseModel):
    """顧客基本スキーマ"""

    code: str = Field(..., description="顧客コード", max_length=50)
    name: str = Field(..., description="顧客名", max_length=200)
    name_kana: Optional[str] = Field(None, description="顧客名カナ", max_length=200)
    short_name: Optional[str] = Field(None, description="略称", max_length=100)
    customer_type: str = Field(
        "corporate", description="顧客種別: corporate, individual"
    )
    industry: Optional[str] = Field(None, description="業界", max_length=100)
    scale: Optional[str] = Field(None, description="規模: large, medium, small")
    postal_code: Optional[str] = Field(None, description="郵便番号", max_length=10)
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号", max_length=20)
    fax: Optional[str] = Field(None, description="FAX番号", max_length=20)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=255)
    website: Optional[str] = Field(None, description="ウェブサイト", max_length=255)
    sales_rep_id: Optional[int] = Field(None, description="担当営業ID")
    credit_limit: Optional[float] = Field(None, description="与信限度額")
    payment_terms: Optional[str] = Field(None, description="支払条件", max_length=100)
    status: str = Field("active", description="ステータス: active, inactive, prospect")
    priority: str = Field("normal", description="優先度: high, normal, low")
    description: Optional[str] = Field(None, description="備考")
    internal_memo: Optional[str] = Field(None, description="内部メモ")


class CustomerCreate(CustomerBase):
    """顧客作成スキーマ"""

    pass


class CustomerUpdate(BaseModel):
    """顧客更新スキーマ"""

    code: Optional[str] = Field(None, description="顧客コード", max_length=50)
    name: Optional[str] = Field(None, description="顧客名", max_length=200)
    name_kana: Optional[str] = Field(None, description="顧客名カナ", max_length=200)
    short_name: Optional[str] = Field(None, description="略称", max_length=100)
    customer_type: Optional[str] = Field(None, description="顧客種別")
    industry: Optional[str] = Field(None, description="業界", max_length=100)
    scale: Optional[str] = Field(None, description="規模")
    postal_code: Optional[str] = Field(None, description="郵便番号", max_length=10)
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号", max_length=20)
    fax: Optional[str] = Field(None, description="FAX番号", max_length=20)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=255)
    website: Optional[str] = Field(None, description="ウェブサイト", max_length=255)
    sales_rep_id: Optional[int] = Field(None, description="担当営業ID")
    credit_limit: Optional[float] = Field(None, description="与信限度額")
    payment_terms: Optional[str] = Field(None, description="支払条件", max_length=100)
    status: Optional[str] = Field(None, description="ステータス")
    priority: Optional[str] = Field(None, description="優先度")
    description: Optional[str] = Field(None, description="備考")
    internal_memo: Optional[str] = Field(None, description="内部メモ")


class CustomerResponse(CustomerBase):
    """顧客レスポンススキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    first_transaction_date: Optional[datetime]
    last_transaction_date: Optional[datetime]
    total_sales: float
    total_transactions: int
    created_at: datetime
    updated_at: datetime


# Customer Contact schemas
class CustomerContactBase(BaseModel):
    """顧客担当者基本スキーマ"""

    name: str = Field(..., description="氏名", max_length=100)
    name_kana: Optional[str] = Field(None, description="氏名カナ", max_length=100)
    title: Optional[str] = Field(None, description="役職", max_length=100)
    department: Optional[str] = Field(None, description="部署", max_length=100)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=255)
    phone: Optional[str] = Field(None, description="電話番号", max_length=20)
    mobile: Optional[str] = Field(None, description="携帯番号", max_length=20)
    is_primary: bool = Field(False, description="主担当者フラグ")
    decision_maker: bool = Field(False, description="決裁権者フラグ")
    notes: Optional[str] = Field(None, description="備考")


class CustomerContactCreate(CustomerContactBase):
    """顧客担当者作成スキーマ"""

    customer_id: int = Field(..., description="顧客ID")


class CustomerContactUpdate(BaseModel):
    """顧客担当者更新スキーマ"""

    name: Optional[str] = Field(None, description="氏名", max_length=100)
    name_kana: Optional[str] = Field(None, description="氏名カナ", max_length=100)
    title: Optional[str] = Field(None, description="役職", max_length=100)
    department: Optional[str] = Field(None, description="部署", max_length=100)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=255)
    phone: Optional[str] = Field(None, description="電話番号", max_length=20)
    mobile: Optional[str] = Field(None, description="携帯番号", max_length=20)
    is_primary: Optional[bool] = Field(None, description="主担当者フラグ")
    decision_maker: Optional[bool] = Field(None, description="決裁権者フラグ")
    notes: Optional[str] = Field(None, description="備考")


class CustomerContactResponse(CustomerContactBase):
    """顧客担当者レスポンススキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime


# Opportunity schemas
class OpportunityBase(BaseModel):
    """商談基本スキーマ"""

    title: str = Field(..., description="商談名", max_length=200)
    description: Optional[str] = Field(None, description="商談詳細")
    estimated_value: Optional[float] = Field(None, description="予想受注金額")
    probability: int = Field(0, description="受注確度（%）", ge=0, le=100)
    expected_close_date: Optional[datetime] = Field(None, description="予想クローズ日")
    status: str = Field("open", description="ステータス: open, won, lost, canceled")
    stage: str = Field("prospecting", description="営業段階")
    competitors: Optional[str] = Field(None, description="競合他社")
    loss_reason: Optional[str] = Field(None, description="失注理由")
    notes: Optional[str] = Field(None, description="備考")


class OpportunityCreate(OpportunityBase):
    """商談作成スキーマ"""

    customer_id: int = Field(..., description="顧客ID")
    owner_id: int = Field(..., description="営業担当者ID")


class OpportunityUpdate(BaseModel):
    """商談更新スキーマ"""

    title: Optional[str] = Field(None, description="商談名", max_length=200)
    description: Optional[str] = Field(None, description="商談詳細")
    estimated_value: Optional[float] = Field(None, description="予想受注金額")
    probability: Optional[int] = Field(None, description="受注確度（%）", ge=0, le=100)
    expected_close_date: Optional[datetime] = Field(None, description="予想クローズ日")
    actual_close_date: Optional[datetime] = Field(None, description="実際クローズ日")
    status: Optional[str] = Field(None, description="ステータス")
    stage: Optional[str] = Field(None, description="営業段階")
    owner_id: Optional[int] = Field(None, description="営業担当者ID")
    competitors: Optional[str] = Field(None, description="競合他社")
    loss_reason: Optional[str] = Field(None, description="失注理由")
    notes: Optional[str] = Field(None, description="備考")


class OpportunityResponse(OpportunityBase):
    """商談レスポンススキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    owner_id: int
    actual_close_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Customer Activity schemas
class CustomerActivityBase(BaseModel):
    """顧客活動基本スキーマ"""

    activity_type: str = Field(
        ..., description="活動種別: call, email, meeting, proposal, other"
    )
    subject: str = Field(..., description="件名", max_length=200)
    description: Optional[str] = Field(None, description="内容")
    activity_date: datetime = Field(..., description="活動日時")
    status: str = Field(
        "completed", description="ステータス: planned, completed, canceled"
    )
    outcome: Optional[str] = Field(None, description="結果・成果")
    next_action: Optional[str] = Field(None, description="次回アクション")
    next_action_date: Optional[datetime] = Field(
        None, description="次回アクション予定日"
    )


class CustomerActivityCreate(CustomerActivityBase):
    """顧客活動作成スキーマ"""

    customer_id: int = Field(..., description="顧客ID")
    opportunity_id: Optional[int] = Field(None, description="商談ID")


class CustomerActivityUpdate(BaseModel):
    """顧客活動更新スキーマ"""

    activity_type: Optional[str] = Field(None, description="活動種別")
    subject: Optional[str] = Field(None, description="件名", max_length=200)
    description: Optional[str] = Field(None, description="内容")
    activity_date: Optional[datetime] = Field(None, description="活動日時")
    status: Optional[str] = Field(None, description="ステータス")
    outcome: Optional[str] = Field(None, description="結果・成果")
    next_action: Optional[str] = Field(None, description="次回アクション")
    next_action_date: Optional[datetime] = Field(
        None, description="次回アクション予定日"
    )


class CustomerActivityResponse(CustomerActivityBase):
    """顧客活動レスポンススキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    opportunity_id: Optional[int]
    user_id: int
    created_at: datetime
    updated_at: datetime


# Complex response schemas with relationships
class CustomerDetailResponse(CustomerResponse):
    """顧客詳細レスポンススキーマ"""

    contacts: List[CustomerContactResponse] = []
    opportunities: List[OpportunityResponse] = []
    recent_activities: List[CustomerActivityResponse] = []


class OpportunityDetailResponse(OpportunityResponse):
    """商談詳細レスポンススキーマ"""

    activities: List[CustomerActivityResponse] = []


# Analytics schemas
class CustomerAnalytics(BaseModel):
    """顧客分析スキーマ"""

    total_customers: int
    active_customers: int
    prospects: int
    inactive_customers: int
    customers_by_industry: dict[str, int]
    customers_by_scale: dict[str, int]
    top_customers_by_sales: List[dict]
    recent_acquisitions: int


class OpportunityAnalytics(BaseModel):
    """商談分析スキーマ"""

    total_opportunities: int
    open_opportunities: int
    won_opportunities: int
    lost_opportunities: int
    total_pipeline_value: float
    average_deal_size: float
    win_rate: float
    opportunities_by_stage: dict[str, int]
    monthly_closed_deals: dict[str, int]


# Bulk operations
class CustomerBulkCreate(BaseModel):
    """顧客一括作成スキーマ"""

    customers: List[CustomerCreate]


class CustomerBulkUpdate(BaseModel):
    """顧客一括更新スキーマ"""

    updates: List[dict]  # [{"id": 1, "data": CustomerUpdate}, ...]
