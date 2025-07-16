# Phase 4-7 Database Model Extensions - Technical Design

## 概要

基本機能が85%完了した現在、拡張機能（Phase 4-7）の実装に向けたデータベースモデル拡張設計を行います。既存のマルチテナント・アーキテクチャを活用し、段階的に機能を追加していきます。

## 設計原則

### 1. 既存アーキテクチャの活用
- `BaseModel`, `AuditableModel`, `SoftDeletableModel` の継承
- `organization_id` による マルチテナント対応
- 既存の認証・認可システムとの統合

### 2. 段階的実装
- Phase 4: 財務管理（予算・経費・請求）
- Phase 5: CRM（顧客・商談管理）
- Phase 6: 高度なワークフロー
- Phase 7: 分析・レポート機能

### 3. 拡張性の確保
- 将来的な機能拡張を考慮した設計
- 標準的なERPパターンの採用
- API設計との整合性

## Phase 4: 財務管理機能

### 4.1 予算管理システム

#### Budget Model (予算)
```python
class Budget(SoftDeletableModel):
    """予算モデル"""
    __tablename__ = "budgets"
    
    # Basic fields
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    
    # Budget details
    budget_type: Mapped[str] = mapped_column(String(50), nullable=False)  # project/department/annual
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Financial amounts
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_amount: Mapped[float] = mapped_column(Float, default=0.0)
    remaining_amount: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status and approval
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft/submitted/approved/rejected
    approved_by: Mapped[UserId | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    project = relationship("Project", lazy="select")
    department = relationship("Department", lazy="select")
    budget_items: Mapped[List["BudgetItem"]] = relationship(
        "BudgetItem", back_populates="budget", cascade="all, delete-orphan"
    )
```

#### BudgetItem Model (予算明細)
```python
class BudgetItem(SoftDeletableModel):
    """予算明細モデル"""
    __tablename__ = "budget_items"
    
    # Foreign keys
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("budgets.id"), nullable=False
    )
    expense_category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expense_categories.id"), nullable=False
    )
    
    # Item details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Financial amounts
    budgeted_amount: Mapped[float] = mapped_column(Float, nullable=False)
    actual_amount: Mapped[float] = mapped_column(Float, default=0.0)
    variance_amount: Mapped[float] = mapped_column(Float, default=0.0)
    variance_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_items")
    expense_category = relationship("ExpenseCategory", lazy="select")
```

#### ExpenseCategory Model (費目)
```python
class ExpenseCategory(SoftDeletableModel):
    """費目マスタ"""
    __tablename__ = "expense_categories"
    
    # Basic fields
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("expense_categories.id"), nullable=True
    )
    
    # Category details
    category_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fixed/variable/capital
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    parent = relationship("ExpenseCategory", remote_side="ExpenseCategory.id")
    children: Mapped[List["ExpenseCategory"]] = relationship(
        "ExpenseCategory", back_populates="parent"
    )
```

### 4.2 経費管理システム

#### Expense Model (経費)
```python
class Expense(SoftDeletableModel):
    """経費モデル"""
    __tablename__ = "expenses"
    
    # Basic fields
    expense_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    applicant_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    expense_category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expense_categories.id"), nullable=False
    )
    
    # Expense details
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # cash/card/transfer
    
    # Receipt information
    receipt_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    receipt_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Approval workflow
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft/submitted/approved/rejected/paid
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[UserId | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    applicant = relationship("User", foreign_keys=[applicant_id])
    project = relationship("Project", lazy="select")
    expense_category = relationship("ExpenseCategory", lazy="select")
    approvals: Mapped[List["ExpenseApproval"]] = relationship(
        "ExpenseApproval", back_populates="expense", cascade="all, delete-orphan"
    )
```

#### ExpenseApproval Model (経費承認)
```python
class ExpenseApproval(AuditableModel):
    """経費承認モデル"""
    __tablename__ = "expense_approvals"
    
    # Foreign keys
    expense_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expenses.id"), nullable=False
    )
    approver_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Approval details
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # pending/approved/rejected
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    expense = relationship("Expense", back_populates="approvals")
    approver = relationship("User", lazy="select")
```

### 4.3 請求管理システム

#### Invoice Model (請求書)
```python
class Invoice(SoftDeletableModel):
    """請求書モデル"""
    __tablename__ = "invoices"
    
    # Basic fields
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    
    # Invoice details
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Financial amounts
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, default=0.0)
    remaining_amount: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status and payment
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft/sent/paid/overdue/cancelled
    payment_status: Mapped[str] = mapped_column(String(50), default="unpaid")  # unpaid/partial/paid
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    customer = relationship("Customer", lazy="select")
    project = relationship("Project", lazy="select")
    invoice_items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
```

#### InvoiceItem Model (請求明細)
```python
class InvoiceItem(SoftDeletableModel):
    """請求明細モデル"""
    __tablename__ = "invoice_items"
    
    # Foreign keys
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id"), nullable=False
    )
    
    # Item details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Pricing
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Float, default=0.10)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")
```

## Phase 5: CRM機能

### 5.1 顧客管理システム

#### Customer Model (顧客)
```python
class Customer(SoftDeletableModel):
    """顧客モデル"""
    __tablename__ = "customers"
    
    # Basic fields
    customer_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    
    # Contact information
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Address
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Customer details
    customer_type: Mapped[str] = mapped_column(String(50), nullable=False)  # individual/corporate
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Business relationship
    status: Mapped[str] = mapped_column(String(50), default="active")  # active/inactive/prospect
    rating: Mapped[str] = mapped_column(String(10), default="C")  # A/B/C rating
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    contacts: Mapped[List["CustomerContact"]] = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="customer", cascade="all, delete-orphan"
    )
```

#### CustomerContact Model (顧客担当者)
```python
class CustomerContact(SoftDeletableModel):
    """顧客担当者モデル"""
    __tablename__ = "customer_contacts"
    
    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    
    # Contact details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Contact information
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Status
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="contacts")
```

### 5.2 商談管理システム

#### Opportunity Model (商談)
```python
class Opportunity(SoftDeletableModel):
    """商談モデル"""
    __tablename__ = "opportunities"
    
    # Basic fields
    opportunity_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Opportunity details
    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # prospecting/qualification/proposal/negotiation/closed_won/closed_lost
    probability: Mapped[int] = mapped_column(Integer, default=0)  # 0-100%
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    
    # Dates
    expected_close_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="active")  # active/won/lost
    lost_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    customer = relationship("Customer", back_populates="opportunities")
    owner = relationship("User", lazy="select")
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="opportunity", cascade="all, delete-orphan"
    )
```

#### Activity Model (活動履歴)
```python
class Activity(SoftDeletableModel):
    """活動履歴モデル"""
    __tablename__ = "activities"
    
    # Basic fields
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    opportunity_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("opportunities.id"), nullable=True
    )
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # call/meeting/email/note
    activity_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # minutes
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed")  # planned/completed/cancelled
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    customer = relationship("Customer", lazy="select")
    opportunity = relationship("Opportunity", back_populates="activities")
    user = relationship("User", lazy="select")
```

## Phase 6: 高度なワークフロー機能

### 6.1 ワークフロー定義

#### WorkflowDefinition Model (ワークフロー定義)
```python
class WorkflowDefinition(SoftDeletableModel):
    """ワークフロー定義モデル"""
    __tablename__ = "workflow_definitions"
    
    # Basic fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    
    # Workflow details
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False)  # expense/invoice/project
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # JSON configuration
    flow_definition: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    instances: Mapped[List["WorkflowInstance"]] = relationship(
        "WorkflowInstance", back_populates="definition", cascade="all, delete-orphan"
    )
```

#### WorkflowInstance Model (ワークフローインスタンス)
```python
class WorkflowInstance(SoftDeletableModel):
    """ワークフローインスタンスモデル"""
    __tablename__ = "workflow_instances"
    
    # Foreign keys
    definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workflow_definitions.id"), nullable=False
    )
    initiator_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Instance details
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # expense/invoice/project
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="running")  # running/completed/cancelled/failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="instances")
    initiator = relationship("User", lazy="select")
    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep", back_populates="instance", cascade="all, delete-orphan"
    )
```

## Phase 7: 分析・レポート機能

### 7.1 ダッシュボード

#### Dashboard Model (ダッシュボード)
```python
class Dashboard(SoftDeletableModel):
    """ダッシュボードモデル"""
    __tablename__ = "dashboards"
    
    # Basic fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Dashboard details
    dashboard_type: Mapped[str] = mapped_column(String(50), nullable=False)  # personal/shared/public
    layout: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    owner = relationship("User", lazy="select")
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan"
    )
```

### 7.2 レポート

#### Report Model (レポート)
```python
class Report(SoftDeletableModel):
    """レポートモデル"""
    __tablename__ = "reports"
    
    # Basic fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    created_by_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Report details
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # financial/project/sales
    query_definition: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    
    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    created_by = relationship("User", lazy="select")
```

## インデックス設計

### 基本インデックス
```sql
-- 組織別検索用
CREATE INDEX idx_budgets_organization_id ON budgets(organization_id);
CREATE INDEX idx_expenses_organization_id ON expenses(organization_id);
CREATE INDEX idx_invoices_organization_id ON invoices(organization_id);
CREATE INDEX idx_customers_organization_id ON customers(organization_id);

-- 日付範囲検索用
CREATE INDEX idx_expenses_date_range ON expenses(expense_date, organization_id);
CREATE INDEX idx_invoices_date_range ON invoices(invoice_date, organization_id);
CREATE INDEX idx_opportunities_close_date ON opportunities(expected_close_date, organization_id);

-- ステータス検索用
CREATE INDEX idx_expenses_status ON expenses(status, organization_id);
CREATE INDEX idx_invoices_status ON invoices(status, organization_id);
CREATE INDEX idx_opportunities_stage ON opportunities(stage, organization_id);

-- 参照用
CREATE INDEX idx_budget_items_budget_id ON budget_items(budget_id);
CREATE INDEX idx_expense_approvals_expense_id ON expense_approvals(expense_id);
CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
```

## マイグレーション計画

### Phase 4 (7/20-7/27)
1. 費目マスタ (`expense_categories`)
2. 予算管理 (`budgets`, `budget_items`)
3. 経費管理 (`expenses`, `expense_approvals`)
4. 請求管理 (`invoices`, `invoice_items`)

### Phase 5 (7/27-8/3)
1. 顧客管理 (`customers`, `customer_contacts`)
2. 商談管理 (`opportunities`, `activities`)

### Phase 6 (8/3-8/10)
1. ワークフロー (`workflow_definitions`, `workflow_instances`, `workflow_steps`)

### Phase 7 (8/10-8/17)
1. ダッシュボード (`dashboards`, `dashboard_widgets`)
2. レポート (`reports`)

## 実装優先順位

### 高優先度 (即座実装)
1. **ExpenseCategory** - 他の機能の基盤
2. **Customer** - CRM機能の基盤
3. **WorkflowDefinition** - 承認プロセスの基盤

### 中優先度 (段階的実装)
1. **Budget/BudgetItem** - 予算管理
2. **Expense/ExpenseApproval** - 経費管理
3. **Invoice/InvoiceItem** - 請求管理

### 低優先度 (最終段階)
1. **Dashboard/DashboardWidget** - 分析機能
2. **Report** - レポート機能

---

**作成日**: 2025-07-16  
**更新日**: 2025-07-16  
**承認者**: CC01  
**実装開始予定**: 2025-07-20