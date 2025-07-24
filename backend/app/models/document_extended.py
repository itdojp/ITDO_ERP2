"""
Document Management Models - CC02 v31.0 Phase 2

Comprehensive document management system with:
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

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class DocumentStatus(str, Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """Document type enumeration."""

    TEXT = "text"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class AccessLevel(str, Enum):
    """Access level enumeration."""

    NONE = "none"
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"
    OWNER = "owner"


class ShareType(str, Enum):
    """Share type enumeration."""

    USER = "user"
    GROUP = "group"
    ORGANIZATION = "organization"
    PUBLIC = "public"
    LINK = "link"


class ApprovalStatus(str, Enum):
    """Approval status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"
    WITHDRAWN = "withdrawn"


class SignatureStatus(str, Enum):
    """Digital signature status enumeration."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    SIGNED = "signed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DocumentExtended(Base):
    """Extended Document Management - Comprehensive document storage and management."""

    __tablename__ = "documents_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Document identification
    document_number = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Document classification
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    tags = Column(JSON, default=[])

    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_extension = Column(String(20))
    mime_type = Column(String(200))
    file_size_bytes = Column(Integer, default=0)
    file_hash = Column(String(128))  # SHA-256 hash for integrity
    encoding = Column(String(50))

    # Storage information
    storage_path = Column(String(1000))
    storage_bucket = Column(String(200))
    storage_provider = Column(String(50))  # local, s3, azure, gcp
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(100))

    # Version control
    version = Column(String(20), default="1.0")
    version_major = Column(Integer, default=1)
    version_minor = Column(Integer, default=0)
    version_patch = Column(Integer, default=0)
    is_latest_version = Column(Boolean, default=True)
    parent_document_id = Column(String, ForeignKey("documents_extended.id"))

    # Document status and lifecycle
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    locked_by_id = Column(String, ForeignKey("users.id"))
    locked_at = Column(DateTime)

    # Content and metadata
    content_preview = Column(Text)  # First few lines for preview
    extracted_text = Column(Text)  # For search indexing
    ocr_text = Column(Text)  # OCR extracted text for images/PDFs
    doc_metadata = Column(JSON, default={})
    custom_properties = Column(JSON, default={})

    # Ownership and permissions
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    folder_id = Column(String, ForeignKey("document_folders.id"))

    # Access and security
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.VIEW)
    is_confidential = Column(Boolean, default=False)
    security_classification = Column(String(50))
    retention_period_years = Column(Integer)
    auto_delete_date = Column(Date)

    # Workflow and approval
    requires_approval = Column(Boolean, default=False)
    approval_workflow_id = Column(String, ForeignKey("document_workflows.id"))
    current_approver_id = Column(String, ForeignKey("users.id"))
    approval_deadline = Column(DateTime)

    # Digital signatures
    requires_signature = Column(Boolean, default=False)
    signature_status = Column(
        SQLEnum(SignatureStatus), default=SignatureStatus.NOT_REQUIRED
    )
    signature_deadline = Column(DateTime)

    # Analytics and tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    last_modified_at = Column(DateTime)

    # External integration
    external_id = Column(String(200))
    external_system = Column(String(100))
    sync_status = Column(String(50))
    last_sync_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime)
    archived_at = Column(DateTime)

    # Relationships
    organization = relationship("Organization")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by_id])
    locked_by = relationship("User", foreign_keys=[locked_by_id])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    parent_document = relationship("DocumentExtended", remote_side=[id])
    folder = relationship("DocumentFolder", back_populates="documents")
    approval_workflow = relationship("DocumentWorkflow")

    # Document-related relationships
    versions = relationship("DocumentExtended", remote_side=[parent_document_id])
    shares = relationship("DocumentShare", back_populates="document")
    comments = relationship("DocumentComment", back_populates="document")
    approvals = relationship("DocumentApproval", back_populates="document")
    signatures = relationship("DocumentSignature", back_populates="document")
    activities = relationship("DocumentActivity", back_populates="document")


class DocumentFolder(Base):
    """Document Folder Management - Hierarchical folder structure for document organization."""

    __tablename__ = "document_folders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Folder identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    full_path = Column(String(1000))  # Complete hierarchical path

    # Hierarchy
    parent_folder_id = Column(String, ForeignKey("document_folders.id"))
    level = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)

    # Folder properties
    is_system_folder = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    # Permissions
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    default_access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.VIEW)
    inherit_permissions = Column(Boolean, default=True)

    # Storage and limits
    storage_quota_bytes = Column(Integer)
    current_usage_bytes = Column(Integer, default=0)
    max_file_size_bytes = Column(Integer)
    allowed_file_types = Column(JSON, default=[])

    # Analytics
    document_count = Column(Integer, default=0)
    subfolder_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)

    # Metadata
    tags = Column(JSON, default=[])
    custom_properties = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by_id])
    parent_folder = relationship("DocumentFolder", remote_side=[id])

    # Folder-related relationships
    subfolders = relationship("DocumentFolder", remote_side=[parent_folder_id])
    documents = relationship("DocumentExtended", back_populates="folder")
    permissions = relationship("DocumentFolderPermission", back_populates="folder")


class DocumentShare(Base):
    """Document Sharing Management - Document sharing and permission management."""

    __tablename__ = "document_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Share information
    share_type = Column(SQLEnum(ShareType), nullable=False)
    shared_with_user_id = Column(String, ForeignKey("users.id"))
    shared_with_group_id = Column(String)
    shared_with_email = Column(String(200))

    # Permissions
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.VIEW)
    can_download = Column(Boolean, default=True)
    can_print = Column(Boolean, default=True)
    can_copy = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)

    # Share settings
    is_public_link = Column(Boolean, default=False)
    share_token = Column(String(100), unique=True)
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(256))

    # Expiration and limits
    expires_at = Column(DateTime)
    max_views = Column(Integer)
    max_downloads = Column(Integer)
    current_views = Column(Integer, default=0)
    current_downloads = Column(Integer, default=0)

    # Notification settings
    notify_on_access = Column(Boolean, default=False)
    notify_on_download = Column(Boolean, default=False)
    notify_on_expiry = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    revoked_by_id = Column(String, ForeignKey("users.id"))

    # Metadata
    share_message = Column(Text)
    custom_properties = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime)
    shared_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("DocumentExtended", back_populates="shares")
    organization = relationship("Organization")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])


class DocumentComment(Base):
    """Document Comment Management - Comments and collaboration on documents."""

    __tablename__ = "document_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Comment content
    content = Column(Text, nullable=False)
    comment_type = Column(
        String(50), default="general"
    )  # general, review, approval, suggestion

    # Comment position (for annotations)
    page_number = Column(Integer)
    position_x = Column(Numeric(10, 6))
    position_y = Column(Numeric(10, 6))
    selection_start = Column(Integer)
    selection_end = Column(Integer)
    selected_text = Column(Text)

    # Comment hierarchy
    parent_comment_id = Column(String, ForeignKey("document_comments.id"))
    thread_id = Column(String)  # Groups related comments

    # Status and resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by_id = Column(String, ForeignKey("users.id"))

    # Mentions and notifications
    mentioned_users = Column(JSON, default=[])
    is_private = Column(Boolean, default=False)
    requires_response = Column(Boolean, default=False)

    # Attachments
    attachments = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    author_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("DocumentExtended", back_populates="comments")
    organization = relationship("Organization")
    author = relationship("User", foreign_keys=[author_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    parent_comment = relationship("DocumentComment", remote_side=[id])

    # Comment-related relationships
    replies = relationship("DocumentComment", remote_side=[parent_comment_id])


class DocumentApproval(Base):
    """Document Approval Management - Approval workflow and tracking."""

    __tablename__ = "document_approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Approval process
    workflow_id = Column(String, ForeignKey("document_workflows.id"))
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200))

    # Approver information
    approver_id = Column(String, ForeignKey("users.id"), nullable=False)
    approver_role = Column(String(100))
    is_required = Column(Boolean, default=True)

    # Approval status
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    decision_date = Column(DateTime)
    deadline = Column(DateTime)

    # Approval details
    comments = Column(Text)
    conditions = Column(Text)
    rejection_reason = Column(Text)

    # Delegation
    delegated_to_id = Column(String, ForeignKey("users.id"))
    delegation_reason = Column(String(500))
    delegated_at = Column(DateTime)

    # Notification settings
    reminder_sent_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime)
    escalation_level = Column(Integer, default=0)

    # Metadata
    approval_criteria = Column(JSON, default={})
    custom_properties = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    requested_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("DocumentExtended", back_populates="approvals")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approver_id])
    delegated_to = relationship("User", foreign_keys=[delegated_to_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    workflow = relationship("DocumentWorkflow")


class DocumentSignature(Base):
    """Document Digital Signature Management - E-signing and digital signatures."""

    __tablename__ = "document_signatures"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Signer information
    signer_id = Column(String, ForeignKey("users.id"))
    signer_name = Column(String(200), nullable=False)
    signer_email = Column(String(200), nullable=False)
    signer_role = Column(String(100))

    # Signature details
    signature_type = Column(String(50))  # electronic, digital, handwritten_scan
    signature_method = Column(String(50))  # drawn, typed, uploaded, certificate
    signature_data = Column(LargeBinary)  # Actual signature image/data
    signature_hash = Column(String(256))

    # Certificate information (for digital signatures)
    certificate_id = Column(String(200))
    certificate_issuer = Column(String(500))
    certificate_serial = Column(String(100))
    certificate_valid_from = Column(DateTime)
    certificate_valid_to = Column(DateTime)

    # Signature position
    page_number = Column(Integer)
    position_x = Column(Numeric(10, 6))
    position_y = Column(Numeric(10, 6))
    width = Column(Numeric(10, 6))
    height = Column(Numeric(10, 6))

    # Signature status
    status = Column(SQLEnum(SignatureStatus), default=SignatureStatus.PENDING)
    signed_at = Column(DateTime)
    signing_deadline = Column(DateTime)

    # Verification and validation
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    geolocation = Column(JSON)

    # Legal and compliance
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime)
    legal_basis = Column(String(500))
    audit_trail = Column(JSON, default=[])

    # Rejection handling
    rejection_reason = Column(Text)
    rejected_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    requested_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    document = relationship("DocumentExtended", back_populates="signatures")
    organization = relationship("Organization")
    signer = relationship("User", foreign_keys=[signer_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])


class DocumentWorkflow(Base):
    """Document Workflow Management - Workflow templates and processes."""

    __tablename__ = "document_workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Workflow identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(50))  # approval, review, signature, publication

    # Workflow configuration
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    auto_assign = Column(Boolean, default=False)
    parallel_processing = Column(Boolean, default=False)

    # Steps and routing
    steps = Column(JSON, default=[])  # Workflow step definitions
    routing_rules = Column(JSON, default={})  # Dynamic routing logic
    escalation_rules = Column(JSON, default={})

    # Timing and deadlines
    default_deadline_days = Column(Integer, default=7)
    reminder_intervals = Column(JSON, default=[1, 3, 5])  # Days before deadline
    auto_approve_timeout = Column(Integer)  # Hours

    # Notifications
    notification_templates = Column(JSON, default={})
    send_notifications = Column(Boolean, default=True)
    notification_channels = Column(JSON, default=["email"])

    # Conditions and triggers
    trigger_conditions = Column(JSON, default={})
    completion_actions = Column(JSON, default={})
    failure_actions = Column(JSON, default={})

    # Analytics
    usage_count = Column(Integer, default=0)
    average_completion_time_hours = Column(Numeric(10, 2))
    success_rate = Column(Numeric(5, 2))

    # Metadata
    tags = Column(JSON, default=[])
    custom_properties = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by_id])

    # Workflow-related relationships
    document_approvals = relationship("DocumentApproval", back_populates="workflow")


class DocumentActivity(Base):
    """Document Activity Tracking - Comprehensive document activity logging."""

    __tablename__ = "document_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Activity information
    activity_type = Column(
        String(50), nullable=False
    )  # view, download, edit, share, comment, approve
    action = Column(String(100), nullable=False)
    description = Column(Text)

    # User and session information
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_type = Column(String(50))

    # Activity context
    source_system = Column(String(100))
    api_endpoint = Column(String(200))
    referrer_url = Column(String(1000))

    # Activity details
    details = Column(JSON, default={})
    old_values = Column(JSON)  # For edit/update activities
    new_values = Column(JSON)

    # File operation details
    bytes_transferred = Column(Integer)
    operation_duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Geolocation (if available)
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("DocumentExtended", back_populates="activities")
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])


class DocumentTemplate(Base):
    """Document Template Management - Template creation and management."""

    __tablename__ = "document_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Template identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    subcategory = Column(String(100))

    # Template configuration
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    template_format = Column(String(50))  # docx, xlsx, pptx, html, markdown
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    # Template content
    template_content = Column(Text)  # Template markup/content
    default_filename = Column(String(500))
    placeholder_fields = Column(JSON, default=[])
    required_fields = Column(JSON, default=[])

    # Generation settings
    auto_fill_rules = Column(JSON, default={})
    validation_rules = Column(JSON, default={})
    output_format = Column(String(50))

    # Permissions and access
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_restricted = Column(Boolean, default=False)
    allowed_groups = Column(JSON, default=[])

    # Usage analytics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    success_rate = Column(Numeric(5, 2))

    # Metadata
    tags = Column(JSON, default=[])
    custom_properties = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by_id])


class DocumentFolderPermission(Base):
    """Document Folder Permission Management - Granular folder-level permissions."""

    __tablename__ = "document_folder_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    folder_id = Column(String, ForeignKey("document_folders.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Permission subject
    user_id = Column(String, ForeignKey("users.id"))
    group_id = Column(String)
    permission_type = Column(String(20))  # user, group, role

    # Access permissions
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.VIEW)
    can_create = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_manage_permissions = Column(Boolean, default=False)

    # Inheritance and propagation
    applies_to_subfolders = Column(Boolean, default=True)
    applies_to_documents = Column(Boolean, default=True)
    inherit_from_parent = Column(Boolean, default=True)

    # Conditions and restrictions
    conditions = Column(JSON, default={})
    ip_restrictions = Column(JSON, default=[])
    time_restrictions = Column(JSON, default={})

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    granted_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    folder = relationship("DocumentFolder", back_populates="permissions")
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])


class DocumentAnalytics(Base):
    """Document Analytics - Comprehensive document usage and performance analytics."""

    __tablename__ = "document_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Reporting period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(
        String(20), default="monthly"
    )  # daily, weekly, monthly, quarterly

    # Document metrics
    total_documents = Column(Integer, default=0)
    new_documents = Column(Integer, default=0)
    updated_documents = Column(Integer, default=0)
    deleted_documents = Column(Integer, default=0)

    # Storage metrics
    total_storage_bytes = Column(Integer, default=0)
    storage_growth_bytes = Column(Integer, default=0)
    average_file_size_bytes = Column(Numeric(15, 2))
    largest_file_size_bytes = Column(Integer)

    # Access and usage metrics
    total_views = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    unique_downloaders = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)

    # Collaboration metrics
    total_comments = Column(Integer, default=0)
    active_collaborators = Column(Integer, default=0)
    collaboration_sessions = Column(Integer, default=0)
    average_collaboration_time_minutes = Column(Numeric(10, 2))

    # Workflow metrics
    approvals_requested = Column(Integer, default=0)
    approvals_completed = Column(Integer, default=0)
    average_approval_time_hours = Column(Numeric(10, 2))
    approval_success_rate = Column(Numeric(5, 2))

    # Signature metrics
    signatures_requested = Column(Integer, default=0)
    signatures_completed = Column(Integer, default=0)
    average_signing_time_hours = Column(Numeric(10, 2))
    signature_success_rate = Column(Numeric(5, 2))

    # Search and discovery
    search_queries = Column(Integer, default=0)
    search_success_rate = Column(Numeric(5, 2))
    most_searched_terms = Column(JSON, default=[])

    # Popular content
    most_viewed_documents = Column(JSON, default=[])
    most_downloaded_documents = Column(JSON, default=[])
    most_shared_documents = Column(JSON, default=[])

    # User engagement
    active_users = Column(Integer, default=0)
    power_users = Column(Integer, default=0)  # Users with high activity
    new_users = Column(Integer, default=0)
    user_retention_rate = Column(Numeric(5, 2))

    # System performance
    average_upload_time_seconds = Column(Numeric(8, 2))
    average_download_time_seconds = Column(Numeric(8, 2))
    system_availability = Column(Numeric(5, 2))
    error_rate = Column(Numeric(5, 2))

    # Calculation metadata
    calculated_date = Column(DateTime)
    calculated_by_id = Column(String, ForeignKey("users.id"))
    data_sources = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    calculator = relationship("User", foreign_keys=[calculated_by_id])
