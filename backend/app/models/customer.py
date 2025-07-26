"""
Customer model for CRM functionality.
顧客管理モデル（CRM機能）
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel


class Customer(SoftDeletableModel):
    """顧客モデル - Customer master for CRM functionality."""

    __tablename__ = "customers"

    # 基本情報
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="顧客コード"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="顧客名")
    name_kana: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="顧客名カナ"
    )
    short_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="略称"
    )

    # 分類・属性
    customer_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="corporate",
        comment="顧客種別: corporate, individual",
    )
    industry: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="業界"
    )
    scale: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="規模: large, medium, small"
    )

    # 連絡先情報
    postal_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="郵便番号"
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True, comment="住所")
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="電話番号"
    )
    fax: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="FAX番号"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="メールアドレス"
    )
    website: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="ウェブサイト"
    )

    # 営業情報
    sales_rep_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="担当営業"
    )
    credit_limit: Mapped[float | None] = mapped_column(
        nullable=True, comment="与信限度額"
    )
    payment_terms: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="支払条件"
    )

    # ステータス
    status: Mapped[str] = mapped_column(
        String(50), default="active", comment="ステータス: active, inactive, prospect"
    )
    priority: Mapped[str] = mapped_column(
        String(50), default="normal", comment="優先度: high, normal, low"
    )

    # 備考・メモ
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="備考")
    internal_memo: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="内部メモ"
    )

    # 取引履歴サマリー
    first_transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="初回取引日"
    )
    last_transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最終取引日"
    )
    total_sales: Mapped[float] = mapped_column(default=0.0, comment="累計売上")
    total_transactions: Mapped[int] = mapped_column(default=0, comment="取引回数")

    # リレーション
    contacts: Mapped[List["CustomerContact"]] = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="customer", cascade="all, delete-orphan"
    )
    activities: Mapped[List["CustomerActivity"]] = relationship(
        "CustomerActivity", back_populates="customer", cascade="all, delete-orphan"
    )
    sales_rep: Mapped["User"] = relationship("User", foreign_keys=[sales_rep_id])

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<Customer(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"

    def update_sales_summary(self) -> None:
        """売上サマリー更新"""
        # 実装時に売上データから集計
        pass

    def get_latest_activity(self) -> Optional["CustomerActivity"]:
        """最新活動取得"""
        if self.activities:
            return max(self.activities, key=lambda x: x.activity_date)
        return None


class CustomerContact(SoftDeletableModel):
    """顧客担当者モデル - Customer contact person."""

    __tablename__ = "customer_contacts"

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )

    # 個人情報
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="氏名")
    name_kana: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="氏名カナ"
    )
    title: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="役職"
    )
    department: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="部署"
    )

    # 連絡先
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="メールアドレス"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="電話番号"
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="携帯番号"
    )

    # 属性
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="主担当者フラグ"
    )
    decision_maker: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="決裁権者フラグ"
    )

    # 備考
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="備考")

    # リレーション
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<CustomerContact(id={self.id}, name='{self.name}', customer_id={self.customer_id})>"


class Opportunity(SoftDeletableModel):
    """商談モデル - Sales opportunity."""

    __tablename__ = "opportunities"

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )

    # 基本情報
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="商談名")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="商談詳細"
    )

    # 金額・確度
    estimated_value: Mapped[float | None] = mapped_column(
        nullable=True, comment="予想受注金額"
    )
    probability: Mapped[int] = mapped_column(default=0, comment="受注確度（%）")

    # 日程
    expected_close_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="予想クローズ日"
    )
    actual_close_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="実際クローズ日"
    )

    # ステータス・フェーズ
    status: Mapped[str] = mapped_column(
        String(50), default="open", comment="ステータス: open, won, lost, canceled"
    )
    stage: Mapped[str] = mapped_column(
        String(50), default="prospecting", comment="営業段階"
    )

    # 担当者
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="営業担当者"
    )

    # 競合・理由
    competitors: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="競合他社"
    )
    loss_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="失注理由"
    )

    # 備考
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="備考")

    # リレーション
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="opportunities"
    )
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    activities: Mapped[List["CustomerActivity"]] = relationship(
        "CustomerActivity", back_populates="opportunity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<Opportunity(id={self.id}, title='{self.title}', status='{self.status}', probability={self.probability})>"

    def update_probability_by_stage(self) -> None:
        """段階に応じた確度自動更新"""
        stage_probability = {
            "prospecting": 10,
            "qualification": 25,
            "needs_analysis": 40,
            "proposal": 60,
            "negotiation": 80,
            "closed_won": 100,
            "closed_lost": 0,
        }
        if self.stage in stage_probability:
            self.probability = stage_probability[self.stage]


class CustomerActivity(SoftDeletableModel):
    """顧客活動履歴モデル - Customer activity log."""

    __tablename__ = "customer_activities"

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    opportunity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("opportunities.id"), nullable=True
    )

    # 活動情報
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="活動種別: call, email, meeting, proposal, other",
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False, comment="件名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="内容")

    # 日時・担当者
    activity_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="活動日時"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="実施者"
    )

    # ステータス
    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
        comment="ステータス: planned, completed, canceled",
    )

    # 結果・フォローアップ
    outcome: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="結果・成果"
    )
    next_action: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="次回アクション"
    )
    next_action_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="次回アクション予定日"
    )

    # リレーション
    customer: Mapped["Customer"] = relationship("Customer", back_populates="activities")
    opportunity: Mapped["Opportunity"] = relationship(
        "Opportunity", back_populates="activities"
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<CustomerActivity(id={self.id}, type='{self.activity_type}', subject='{self.subject}', date={self.activity_date})>"
