"""
Document Management API Schemas - CC02 v31.0 Phase 2

Pydantic schemas for document management including:
- Document Storage & Versioning
- Folder & Category Management
- Document Sharing & Permissions
- Workflow & Approval Processes
- Document Templates & Generation
- Search & Indexing
- Collaboration & Comments
- Document Analytics & Tracking
- Digital Signatures & E-signing
- Integration & API Management
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.document_extended import (
    AccessLevel,
    ApprovalStatus,
    DocumentStatus,
    DocumentType,
    ShareType,
    SignatureStatus,
)

# =============================================================================
# Document Schemas
# =============================================================================


class DocumentBase(BaseModel):
    """Base schema for Document."""

    organization_id: str
    title: str
    description: Optional[str] = None
    document_type: DocumentType
    category: Optional[str] = None
    subcategory: Optional[str] = None
    filename: str
    folder_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    custom_properties: Dict[str, Any] = {}
    is_confidential: bool = False
    security_classification: Optional[str] = None
    requires_approval: bool = False
    requires_signature: bool = False


class DocumentCreate(DocumentBase):
    """Schema for creating Document."""

    owner_id: str
    created_by_id: str
    original_filename: Optional[str] = None
    storage_path: Optional[str] = None
    storage_bucket: Optional[str] = None
    storage_provider: str = "local"
    is_template: bool = False
    retention_period_years: Optional[int] = Field(None, ge=1, le=100)


class DocumentUpdate(BaseModel):
    """Schema for updating Document."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    custom_properties: Optional[Dict[str, Any]] = None
    is_confidential: Optional[bool] = None
    security_classification: Optional[str] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(DocumentBase):
    """Schema for Document response."""

    id: str
    document_number: str
    file_extension: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: int
    file_hash: Optional[str] = None
    storage_path: Optional[str] = None
    version: str
    version_major: int
    version_minor: int
    version_patch: int
    is_latest_version: bool
    parent_document_id: Optional[str] = None
    status: DocumentStatus
    is_public: bool
    is_archived: bool
    is_locked: bool
    locked_by_id: Optional[str] = None
    locked_at: Optional[datetime] = None
    owner_id: str
    created_by_id: str
    access_level: AccessLevel
    approval_workflow_id: Optional[str] = None
    current_approver_id: Optional[str] = None
    approval_deadline: Optional[datetime] = None
    signature_status: SignatureStatus
    signature_deadline: Optional[datetime] = None
    view_count: int
    download_count: int
    share_count: int
    comment_count: int
    last_viewed_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentVersionCreate(BaseModel):
    """Schema for creating document version."""

    filename: str
    description: Optional[str] = None
    major_update: bool = False
    change_summary: Optional[str] = None


class DocumentMoveRequest(BaseModel):
    """Schema for moving document to different folder."""

    new_folder_id: Optional[str] = None


# =============================================================================
# Folder Schemas
# =============================================================================


class FolderBase(BaseModel):
    """Base schema for Folder."""

    organization_id: str
    name: str
    description: Optional[str] = None
    parent_folder_id: Optional[str] = None
    default_access_level: AccessLevel = AccessLevel.VIEW
    storage_quota_bytes: Optional[int] = Field(None, ge=0)
    max_file_size_bytes: Optional[int] = Field(None, ge=0)
    allowed_file_types: List[str] = []
    tags: List[str] = []
    custom_properties: Dict[str, Any] = {}


class FolderCreate(FolderBase):
    """Schema for creating Folder."""

    owner_id: str
    created_by_id: str
    inherit_permissions: bool = True


class FolderUpdate(BaseModel):
    """Schema for updating Folder."""

    name: Optional[str] = None
    description: Optional[str] = None
    default_access_level: Optional[AccessLevel] = None
    storage_quota_bytes: Optional[int] = Field(None, ge=0)
    max_file_size_bytes: Optional[int] = Field(None, ge=0)
    allowed_file_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_properties: Optional[Dict[str, Any]] = None
    is_archived: Optional[bool] = None


class FolderResponse(FolderBase):
    """Schema for Folder response."""

    id: str
    full_path: str
    level: int
    sort_order: int
    is_system_folder: bool
    is_public: bool
    is_archived: bool
    owner_id: str
    created_by_id: str
    inherit_permissions: bool
    current_usage_bytes: int
    document_count: int
    subfolder_count: int
    total_size_bytes: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FolderContentsResponse(BaseModel):
    """Schema for folder contents response."""

    subfolders: List[FolderResponse]
    documents: List[DocumentResponse]


# =============================================================================
# Document Sharing Schemas
# =============================================================================


class ShareBase(BaseModel):
    """Base schema for Document Share."""

    document_id: str
    organization_id: str
    share_type: ShareType
    shared_with_user_id: Optional[str] = None
    shared_with_group_id: Optional[str] = None
    shared_with_email: Optional[str] = None
    access_level: AccessLevel = AccessLevel.VIEW
    can_download: bool = True
    can_print: bool = True
    can_copy: bool = True
    can_share: bool = False
    expires_at: Optional[datetime] = None
    max_views: Optional[int] = Field(None, ge=1)
    max_downloads: Optional[int] = Field(None, ge=1)
    share_message: Optional[str] = None
    notify_on_access: bool = False
    notify_on_download: bool = False


class ShareCreate(ShareBase):
    """Schema for creating Document Share."""

    password_protected: bool = False
    password: Optional[str] = None


class ShareUpdate(BaseModel):
    """Schema for updating Document Share."""

    access_level: Optional[AccessLevel] = None
    can_download: Optional[bool] = None
    can_print: Optional[bool] = None
    can_copy: Optional[bool] = None
    can_share: Optional[bool] = None
    expires_at: Optional[datetime] = None
    max_views: Optional[int] = Field(None, ge=1)
    max_downloads: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class ShareResponse(ShareBase):
    """Schema for Document Share response."""

    id: str
    is_public_link: bool
    share_token: Optional[str] = None
    password_protected: bool
    current_views: int
    current_downloads: int
    notify_on_expiry: bool
    is_active: bool
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_by_id: Optional[str] = None
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    shared_by_id: str

    class Config:
        from_attributes = True


class ShareAccessRequest(BaseModel):
    """Schema for accessing shared document."""

    share_token: str
    password: Optional[str] = None


# =============================================================================
# Comment and Collaboration Schemas
# =============================================================================


class CommentBase(BaseModel):
    """Base schema for Document Comment."""

    document_id: str
    organization_id: str
    content: str
    comment_type: str = "general"
    page_number: Optional[int] = Field(None, ge=1)
    position_x: Optional[Decimal] = None
    position_y: Optional[Decimal] = None
    selection_start: Optional[int] = Field(None, ge=0)
    selection_end: Optional[int] = Field(None, ge=0)
    selected_text: Optional[str] = None
    parent_comment_id: Optional[str] = None
    thread_id: Optional[str] = None
    mentioned_users: List[str] = []
    is_private: bool = False
    requires_response: bool = False
    attachments: List[Dict[str, str]] = []


class CommentCreate(CommentBase):
    """Schema for creating Document Comment."""

    pass


class CommentUpdate(BaseModel):
    """Schema for updating Document Comment."""

    content: Optional[str] = None
    is_resolved: Optional[bool] = None
    attachments: Optional[List[Dict[str, str]]] = None


class CommentResponse(CommentBase):
    """Schema for Document Comment response."""

    id: str
    author_id: str
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Approval Workflow Schemas
# =============================================================================


class WorkflowBase(BaseModel):
    """Base schema for Document Workflow."""

    organization_id: str
    name: str
    description: Optional[str] = None
    workflow_type: str = "approval"
    steps: List[Dict[str, Any]] = []
    routing_rules: Dict[str, Any] = {}
    escalation_rules: Dict[str, Any] = {}
    default_deadline_days: int = Field(7, ge=1, le=365)
    reminder_intervals: List[int] = [1, 3, 5]
    auto_approve_timeout: Optional[int] = Field(None, ge=1)
    notification_templates: Dict[str, Any] = {}
    send_notifications: bool = True
    notification_channels: List[str] = ["email"]
    trigger_conditions: Dict[str, Any] = {}
    completion_actions: Dict[str, Any] = {}
    failure_actions: Dict[str, Any] = {}
    tags: List[str] = []
    custom_properties: Dict[str, Any] = {}


class WorkflowCreate(WorkflowBase):
    """Schema for creating Document Workflow."""

    created_by_id: str
    is_template: bool = False
    auto_assign: bool = False
    parallel_processing: bool = False


class WorkflowUpdate(BaseModel):
    """Schema for updating Document Workflow."""

    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    routing_rules: Optional[Dict[str, Any]] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    default_deadline_days: Optional[int] = Field(None, ge=1, le=365)
    reminder_intervals: Optional[List[int]] = None
    send_notifications: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class WorkflowResponse(WorkflowBase):
    """Schema for Document Workflow response."""

    id: str
    created_by_id: str
    is_active: bool
    is_template: bool
    auto_assign: bool
    parallel_processing: bool
    usage_count: int
    average_completion_time_hours: Optional[Decimal] = None
    success_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalBase(BaseModel):
    """Base schema for Document Approval."""

    document_id: str
    organization_id: str
    workflow_id: Optional[str] = None
    step_number: int
    step_name: Optional[str] = None
    approver_id: str
    approver_role: Optional[str] = None
    is_required: bool = True
    deadline: Optional[datetime] = None
    approval_criteria: Dict[str, Any] = {}
    custom_properties: Dict[str, Any] = {}


class ApprovalCreate(ApprovalBase):
    """Schema for creating Document Approval."""

    requested_by_id: str


class ApprovalDecisionRequest(BaseModel):
    """Schema for approval decision."""

    decision: ApprovalStatus
    comments: Optional[str] = None
    conditions: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalResponse(ApprovalBase):
    """Schema for Document Approval response."""

    id: str
    requested_by_id: str
    status: ApprovalStatus
    decision_date: Optional[datetime] = None
    comments: Optional[str] = None
    conditions: Optional[str] = None
    rejection_reason: Optional[str] = None
    delegated_to_id: Optional[str] = None
    delegation_reason: Optional[str] = None
    delegated_at: Optional[datetime] = None
    reminder_sent_count: int
    last_reminder_sent: Optional[datetime] = None
    escalation_level: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalSubmissionRequest(BaseModel):
    """Schema for submitting document for approval."""

    workflow_id: str
    approvers: List[Dict[str, Any]]
    deadline_override: Optional[datetime] = None
    notes: Optional[str] = None


# =============================================================================
# Digital Signature Schemas
# =============================================================================


class SignatureBase(BaseModel):
    """Base schema for Document Signature."""

    document_id: str
    organization_id: str
    signer_name: str
    signer_email: str
    signer_role: Optional[str] = None
    signature_type: str = "electronic"
    page_number: int = Field(1, ge=1)
    position_x: Optional[Decimal] = None
    position_y: Optional[Decimal] = None
    width: Decimal = Field(150, ge=50, le=500)
    height: Decimal = Field(50, ge=20, le=200)
    signing_deadline: Optional[datetime] = None


class SignatureRequestCreate(SignatureBase):
    """Schema for creating Signature Request."""

    requested_by_id: str
    signer_id: Optional[str] = None


class SignatureProcessRequest(BaseModel):
    """Schema for processing signature."""

    signature_data: str  # Base64 encoded signature image
    consent_given: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    verification_method: str = "email"


class SignatureResponse(SignatureBase):
    """Schema for Document Signature response."""

    id: str
    requested_by_id: str
    signer_id: Optional[str] = None
    signature_method: Optional[str] = None
    signature_hash: Optional[str] = None
    certificate_id: Optional[str] = None
    certificate_issuer: Optional[str] = None
    certificate_valid_from: Optional[datetime] = None
    certificate_valid_to: Optional[datetime] = None
    status: SignatureStatus
    signed_at: Optional[datetime] = None
    is_verified: bool
    verification_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    consent_given: bool
    consent_timestamp: Optional[datetime] = None
    legal_basis: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = []
    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkSignatureRequest(BaseModel):
    """Schema for bulk signature request."""

    document_ids: List[str]
    signers: List[Dict[str, Any]]
    signing_deadline: Optional[datetime] = None
    notification_message: Optional[str] = None


# =============================================================================
# Template Schemas
# =============================================================================


class TemplateBase(BaseModel):
    """Base schema for Document Template."""

    organization_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    document_type: DocumentType
    template_format: Optional[str] = None
    template_content: Optional[str] = None
    default_filename: Optional[str] = None
    placeholder_fields: List[Dict[str, Any]] = []
    required_fields: List[str] = []
    auto_fill_rules: Dict[str, Any] = {}
    validation_rules: Dict[str, Any] = {}
    output_format: Optional[str] = None
    is_public: bool = False
    is_restricted: bool = False
    allowed_groups: List[str] = []
    tags: List[str] = []
    custom_properties: Dict[str, Any] = {}


class TemplateCreate(TemplateBase):
    """Schema for creating Document Template."""

    owner_id: str
    created_by_id: str


class TemplateUpdate(BaseModel):
    """Schema for updating Document Template."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    template_content: Optional[str] = None
    placeholder_fields: Optional[List[Dict[str, Any]]] = None
    required_fields: Optional[List[str]] = None
    auto_fill_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class TemplateResponse(TemplateBase):
    """Schema for Document Template response."""

    id: str
    owner_id: str
    created_by_id: str
    is_active: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    success_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateGenerationRequest(BaseModel):
    """Schema for generating document from template."""

    template_id: str
    field_values: Dict[str, Any]
    output_filename: Optional[str] = None
    folder_id: Optional[str] = None
    auto_save: bool = True


class TemplateGenerationResponse(BaseModel):
    """Schema for template generation response."""

    document_id: str
    filename: str
    generation_success: bool
    validation_errors: List[str] = []
    field_values_used: Dict[str, Any]


# =============================================================================
# Search and Filter Schemas
# =============================================================================


class DocumentSearchRequest(BaseModel):
    """Schema for document search request."""

    query: str
    document_type: Optional[DocumentType] = None
    category: Optional[str] = None
    owner_id: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None
    min_file_size: Optional[int] = Field(None, ge=0)
    max_file_size: Optional[int] = Field(None, ge=0)
    status: Optional[DocumentStatus] = None
    is_confidential: Optional[bool] = None
    has_comments: Optional[bool] = None
    requires_approval: Optional[bool] = None
    requires_signature: Optional[bool] = None


class DocumentFilterRequest(BaseModel):
    """Schema for document filtering request."""

    organization_id: Optional[str] = None
    folder_id: Optional[str] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    owner_id: Optional[str] = None
    category: Optional[str] = None
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class AdvancedSearchResponse(BaseModel):
    """Schema for advanced search response."""

    documents: List[DocumentResponse]
    total_count: int
    search_time_ms: int
    facets: Dict[str, List[Dict[str, Any]]] = {}
    suggestions: List[str] = []


# =============================================================================
# Analytics and Reporting Schemas
# =============================================================================


class DocumentAnalyticsRequest(BaseModel):
    """Schema for document analytics request."""

    organization_id: str
    period_start: date
    period_end: date
    period_type: str = "monthly"
    include_details: bool = False


class DocumentUsageStats(BaseModel):
    """Schema for document usage statistics."""

    document_id: str
    title: str
    view_count: int
    download_count: int
    share_count: int
    comment_count: int
    last_accessed: Optional[datetime] = None
    popularity_score: float


class CollaborationMetrics(BaseModel):
    """Schema for collaboration metrics."""

    total_comments: int
    active_collaborators: int
    collaboration_sessions: int
    average_response_time_hours: Optional[Decimal] = None
    most_collaborative_documents: List[DocumentUsageStats]


class WorkflowMetrics(BaseModel):
    """Schema for workflow metrics."""

    approvals_requested: int
    approvals_completed: int
    average_approval_time_hours: Optional[Decimal] = None
    approval_success_rate: Optional[Decimal] = None
    signatures_requested: int
    signatures_completed: int
    average_signing_time_hours: Optional[Decimal] = None
    signature_success_rate: Optional[Decimal] = None


class StorageMetrics(BaseModel):
    """Schema for storage metrics."""

    total_documents: int
    total_storage_bytes: int
    storage_growth_bytes: int
    average_file_size_bytes: Optional[Decimal] = None
    largest_file_size_bytes: int
    storage_by_type: Dict[str, int] = {}
    storage_by_category: Dict[str, int] = {}


class DocumentAnalyticsResponse(BaseModel):
    """Schema for comprehensive document analytics."""

    organization_id: str
    period_start: date
    period_end: date
    period_type: str
    storage_metrics: StorageMetrics
    usage_metrics: Dict[str, int]
    collaboration_metrics: CollaborationMetrics
    workflow_metrics: WorkflowMetrics
    popular_content: Dict[str, List[DocumentUsageStats]]
    user_engagement: Dict[str, int]
    system_performance: Dict[str, float]
    calculated_date: datetime


# =============================================================================
# Permission and Access Control Schemas
# =============================================================================


class FolderPermissionBase(BaseModel):
    """Base schema for Folder Permission."""

    folder_id: str
    organization_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    permission_type: str = "user"
    access_level: AccessLevel = AccessLevel.VIEW
    can_create: bool = False
    can_delete: bool = False
    can_manage_permissions: bool = False
    applies_to_subfolders: bool = True
    applies_to_documents: bool = True
    inherit_from_parent: bool = True
    conditions: Dict[str, Any] = {}
    ip_restrictions: List[str] = []
    time_restrictions: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None


class FolderPermissionCreate(FolderPermissionBase):
    """Schema for creating Folder Permission."""

    granted_by_id: str


class FolderPermissionUpdate(BaseModel):
    """Schema for updating Folder Permission."""

    access_level: Optional[AccessLevel] = None
    can_create: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_manage_permissions: Optional[bool] = None
    applies_to_subfolders: Optional[bool] = None
    applies_to_documents: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class FolderPermissionResponse(FolderPermissionBase):
    """Schema for Folder Permission response."""

    id: str
    granted_by_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Activity and Audit Schemas
# =============================================================================


class ActivityBase(BaseModel):
    """Base schema for Document Activity."""

    document_id: str
    organization_id: str
    activity_type: str
    action: str
    description: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    source_system: Optional[str] = None
    details: Dict[str, Any] = {}
    bytes_transferred: Optional[int] = None
    operation_duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None


class ActivityResponse(ActivityBase):
    """Schema for Document Activity response."""

    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ActivityFilterRequest(BaseModel):
    """Schema for activity filtering."""

    document_id: Optional[str] = None
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    activity_type: Optional[str] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# =============================================================================
# Bulk Operations Schemas
# =============================================================================


class BulkDocumentOperation(BaseModel):
    """Schema for bulk document operations."""

    document_ids: List[str]
    operation: str  # move, copy, delete, archive, tag, share
    parameters: Dict[str, Any] = {}


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""

    operation: str
    total_requested: int
    successful_count: int
    failed_count: int
    success_rate: float
    successful_documents: List[str]
    failed_documents: List[Dict[str, str]]
    execution_time_ms: int


class BulkTagOperation(BaseModel):
    """Schema for bulk tag operations."""

    document_ids: List[str]
    tags_to_add: List[str] = []
    tags_to_remove: List[str] = []


class BulkMoveOperation(BaseModel):
    """Schema for bulk move operations."""

    document_ids: List[str]
    target_folder_id: Optional[str] = None


class BulkShareOperation(BaseModel):
    """Schema for bulk share operations."""

    document_ids: List[str]
    share_settings: Dict[str, Any]


# =============================================================================
# System and Integration Schemas
# =============================================================================


class SystemHealthResponse(BaseModel):
    """Schema for system health response."""

    status: str
    database_connection: str
    services_available: bool
    statistics: Dict[str, int]
    performance_metrics: Dict[str, float] = {}
    version: str
    timestamp: str


class IntegrationSettings(BaseModel):
    """Schema for integration settings."""

    provider: str
    configuration: Dict[str, Any]
    is_enabled: bool = True
    sync_frequency: str = "daily"
    last_sync: Optional[datetime] = None


class ExportRequest(BaseModel):
    """Schema for document export request."""

    document_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None
    export_format: str = "zip"
    include_metadata: bool = True
    include_versions: bool = False
    include_comments: bool = False


class ImportRequest(BaseModel):
    """Schema for document import request."""

    source_type: str  # file_upload, url, external_system
    source_location: str
    target_folder_id: Optional[str] = None
    preserve_structure: bool = True
    auto_categorize: bool = True
    import_metadata: bool = True


class SyncStatus(BaseModel):
    """Schema for synchronization status."""

    sync_id: str
    status: str
    progress_percentage: float
    total_items: int
    processed_items: int
    failed_items: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    last_error: Optional[str] = None


# =============================================================================
# Validation and Helper Schemas
# =============================================================================


class FileUploadMetadata(BaseModel):
    """Schema for file upload metadata."""

    filename: str
    content_type: str
    file_size: int
    checksum: Optional[str] = None


class DocumentAccessCheck(BaseModel):
    """Schema for document access check."""

    user_id: str
    document_id: str
    requested_access: AccessLevel


class AccessCheckResponse(BaseModel):
    """Schema for access check response."""

    has_access: bool
    granted_level: Optional[AccessLevel] = None
    restrictions: List[str] = []
    expiry: Optional[datetime] = None


class QuotaUsage(BaseModel):
    """Schema for quota usage information."""

    organization_id: str
    user_id: Optional[str] = None
    current_usage_bytes: int
    quota_limit_bytes: int
    usage_percentage: float
    document_count: int
    max_documents: Optional[int] = None
