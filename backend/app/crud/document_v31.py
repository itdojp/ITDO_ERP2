"""
Document Management CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for document management including:
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

import hashlib
import mimetypes
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.document_extended import (
    AccessLevel,
    ApprovalStatus,
    DocumentActivity,
    DocumentAnalytics,
    DocumentApproval,
    DocumentComment,
    DocumentExtended,
    DocumentFolder,
    DocumentShare,
    DocumentSignature,
    DocumentStatus,
    DocumentTemplate,
    DocumentType,
    DocumentWorkflow,
    ShareType,
    SignatureStatus,
)


class DocumentService:
    """Service class for document management operations."""

    # =============================================================================
    # Document Management
    # =============================================================================

    async def create_document(
        self, db: Session, document_data: dict, file_content: bytes = None
    ) -> DocumentExtended:
        """Create a new document with comprehensive metadata and file handling."""

        # Generate unique document number
        document_number = f"DOC-{uuid.uuid4().hex[:8].upper()}"

        # File processing
        file_hash = None
        file_size = 0
        mime_type = None

        if file_content:
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
            mime_type, _ = mimetypes.guess_type(document_data.get("filename", ""))

        # Create document record
        document = DocumentExtended(
            document_number=document_number,
            title=document_data["title"],
            description=document_data.get("description"),
            document_type=document_data["document_type"],
            category=document_data.get("category"),
            subcategory=document_data.get("subcategory"),
            filename=document_data["filename"],
            original_filename=document_data.get(
                "original_filename", document_data["filename"]
            ),
            file_extension=os.path.splitext(document_data["filename"])[1].lower(),
            mime_type=mime_type,
            file_size_bytes=file_size,
            file_hash=file_hash,
            storage_path=document_data.get("storage_path"),
            storage_bucket=document_data.get("storage_bucket"),
            storage_provider=document_data.get("storage_provider", "local"),
            organization_id=document_data["organization_id"],
            owner_id=document_data["owner_id"],
            created_by_id=document_data["created_by_id"],
            folder_id=document_data.get("folder_id"),
            tags=document_data.get("tags", []),
            metadata=document_data.get("metadata", {}),
            custom_properties=document_data.get("custom_properties", {}),
            is_confidential=document_data.get("is_confidential", False),
            security_classification=document_data.get("security_classification"),
            requires_approval=document_data.get("requires_approval", False),
            requires_signature=document_data.get("requires_signature", False),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Log activity
        await self._log_document_activity(
            db,
            document.id,
            "create",
            "Document created",
            document_data["created_by_id"],
            {"file_size": file_size},
        )

        return document

    async def get_document_by_id(
        self, db: Session, document_id: str
    ) -> Optional[DocumentExtended]:
        """Get document by ID with full details."""
        document = (
            db.query(DocumentExtended)
            .options(
                joinedload(DocumentExtended.owner),
                joinedload(DocumentExtended.creator),
                joinedload(DocumentExtended.folder),
                joinedload(DocumentExtended.shares),
                joinedload(DocumentExtended.comments),
            )
            .filter(DocumentExtended.id == document_id)
            .first()
        )

        if document:
            # Update view count and last viewed timestamp
            document.view_count += 1
            document.last_viewed_at = datetime.utcnow()
            db.commit()

        return document

    async def get_documents(
        self,
        db: Session,
        organization_id: str,
        folder_id: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        owner_id: Optional[str] = None,
        category: Optional[str] = None,
        search_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentExtended]:
        """Get documents with comprehensive filtering options."""

        query = db.query(DocumentExtended).filter(
            DocumentExtended.organization_id == organization_id,
            DocumentExtended.status != DocumentStatus.DELETED,
        )

        if folder_id:
            query = query.filter(DocumentExtended.folder_id == folder_id)

        if document_type:
            query = query.filter(DocumentExtended.document_type == document_type)

        if status:
            query = query.filter(DocumentExtended.status == status)

        if owner_id:
            query = query.filter(DocumentExtended.owner_id == owner_id)

        if category:
            query = query.filter(DocumentExtended.category == category)

        if search_text:
            search_filter = or_(
                DocumentExtended.title.ilike(f"%{search_text}%"),
                DocumentExtended.description.ilike(f"%{search_text}%"),
                DocumentExtended.filename.ilike(f"%{search_text}%"),
                DocumentExtended.extracted_text.ilike(f"%{search_text}%"),
            )
            query = query.filter(search_filter)

        if tags:
            for tag in tags:
                query = query.filter(DocumentExtended.tags.contains([tag]))

        if created_after:
            query = query.filter(DocumentExtended.created_at >= created_after)

        if created_before:
            query = query.filter(DocumentExtended.created_at <= created_before)

        return (
            query.order_by(desc(DocumentExtended.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_document(
        self, db: Session, document_id: str, update_data: dict, user_id: str
    ) -> Optional[DocumentExtended]:
        """Update document with change tracking and versioning."""

        document = (
            db.query(DocumentExtended)
            .filter(DocumentExtended.id == document_id)
            .first()
        )
        if not document:
            return None

        # Store old values for audit trail
        old_values = {}
        new_values = {}

        # Update allowed fields
        updatable_fields = [
            "title",
            "description",
            "category",
            "subcategory",
            "tags",
            "metadata",
            "custom_properties",
            "is_confidential",
            "security_classification",
            "status",
        ]

        for field in updatable_fields:
            if field in update_data:
                old_values[field] = getattr(document, field)
                setattr(document, field, update_data[field])
                new_values[field] = update_data[field]

        document.last_modified_at = datetime.utcnow()
        db.commit()
        db.refresh(document)

        # Log activity
        await self._log_document_activity(
            db,
            document_id,
            "update",
            "Document updated",
            user_id,
            {"old_values": old_values, "new_values": new_values},
        )

        return document

    async def create_document_version(
        self,
        db: Session,
        original_document_id: str,
        new_version_data: dict,
        file_content: bytes = None,
        user_id: str = None,
    ) -> DocumentExtended:
        """Create a new version of an existing document."""

        original_doc = await self.get_document_by_id(db, original_document_id)
        if not original_doc:
            raise ValueError("Original document not found")

        # Mark original as not latest
        original_doc.is_latest_version = False

        # Calculate new version number
        version_parts = original_doc.version.split(".")
        major, minor = int(version_parts[0]), int(version_parts[1])

        if new_version_data.get("major_update", False):
            major += 1
            minor = 0
        else:
            minor += 1

        new_version = f"{major}.{minor}"

        # Create new version
        version_data = {
            **new_version_data,
            "title": original_doc.title,
            "organization_id": original_doc.organization_id,
            "owner_id": original_doc.owner_id,
            "created_by_id": user_id or original_doc.owner_id,
            "folder_id": original_doc.folder_id,
            "parent_document_id": original_document_id,
            "version": new_version,
            "version_major": major,
            "version_minor": minor,
            "document_type": original_doc.document_type,
            "category": original_doc.category,
            "subcategory": original_doc.subcategory,
        }

        new_document = await self.create_document(db, version_data, file_content)

        # Log versioning activity
        await self._log_document_activity(
            db,
            original_document_id,
            "version",
            f"New version {new_version} created",
            user_id,
            {"new_version_id": new_document.id, "version": new_version},
        )

        db.commit()
        return new_document

    async def delete_document(
        self, db: Session, document_id: str, user_id: str
    ) -> bool:
        """Soft delete document (mark as deleted)."""

        document = (
            db.query(DocumentExtended)
            .filter(DocumentExtended.id == document_id)
            .first()
        )
        if not document:
            return False

        document.status = DocumentStatus.DELETED
        document.is_archived = True
        document.archived_at = datetime.utcnow()

        db.commit()

        # Log activity
        await self._log_document_activity(
            db, document_id, "delete", "Document deleted", user_id
        )

        return True

    # =============================================================================
    # Folder Management
    # =============================================================================

    async def create_folder(self, db: Session, folder_data: dict) -> DocumentFolder:
        """Create a new document folder with hierarchy support."""

        # Calculate full path and level
        full_path = folder_data["name"]
        level = 0

        if folder_data.get("parent_folder_id"):
            parent = (
                db.query(DocumentFolder)
                .filter(DocumentFolder.id == folder_data["parent_folder_id"])
                .first()
            )
            if parent:
                full_path = f"{parent.full_path}/{folder_data['name']}"
                level = parent.level + 1

        folder = DocumentFolder(
            name=folder_data["name"],
            description=folder_data.get("description"),
            full_path=full_path,
            level=level,
            parent_folder_id=folder_data.get("parent_folder_id"),
            organization_id=folder_data["organization_id"],
            owner_id=folder_data["owner_id"],
            created_by_id=folder_data["created_by_id"],
            default_access_level=folder_data.get(
                "default_access_level", AccessLevel.VIEW
            ),
            storage_quota_bytes=folder_data.get("storage_quota_bytes"),
            max_file_size_bytes=folder_data.get("max_file_size_bytes"),
            allowed_file_types=folder_data.get("allowed_file_types", []),
            tags=folder_data.get("tags", []),
            custom_properties=folder_data.get("custom_properties", {}),
        )

        db.add(folder)
        db.commit()
        db.refresh(folder)

        # Update parent folder subfolder count
        if folder.parent_folder_id:
            await self._update_folder_statistics(db, folder.parent_folder_id)

        return folder

    async def get_folder_contents(
        self,
        db: Session,
        folder_id: str,
        include_subfolders: bool = True,
        include_documents: bool = True,
    ) -> Dict[str, List]:
        """Get folder contents including subfolders and documents."""

        result = {"subfolders": [], "documents": []}

        if include_subfolders:
            subfolders = (
                db.query(DocumentFolder)
                .filter(
                    DocumentFolder.parent_folder_id == folder_id,
                    not DocumentFolder.is_archived,
                )
                .order_by(DocumentFolder.name)
                .all()
            )
            result["subfolders"] = subfolders

        if include_documents:
            documents = (
                db.query(DocumentExtended)
                .filter(
                    DocumentExtended.folder_id == folder_id,
                    DocumentExtended.status != DocumentStatus.DELETED,
                )
                .order_by(DocumentExtended.title)
                .all()
            )
            result["documents"] = documents

        return result

    async def move_document(
        self, db: Session, document_id: str, new_folder_id: Optional[str], user_id: str
    ) -> DocumentExtended:
        """Move document to a different folder."""

        document = await self.get_document_by_id(db, document_id)
        if not document:
            raise ValueError("Document not found")

        old_folder_id = document.folder_id
        document.folder_id = new_folder_id

        db.commit()

        # Update folder statistics
        if old_folder_id:
            await self._update_folder_statistics(db, old_folder_id)
        if new_folder_id:
            await self._update_folder_statistics(db, new_folder_id)

        # Log activity
        await self._log_document_activity(
            db,
            document_id,
            "move",
            "Document moved",
            user_id,
            {"old_folder_id": old_folder_id, "new_folder_id": new_folder_id},
        )

        return document

    # =============================================================================
    # Document Sharing
    # =============================================================================

    async def create_document_share(
        self, db: Session, document_id: str, share_data: dict, shared_by_id: str
    ) -> DocumentShare:
        """Create a document share with specified permissions."""

        # Generate share token for public/link shares
        share_token = None
        if share_data.get("share_type") in [ShareType.PUBLIC, ShareType.LINK]:
            share_token = f"share_{uuid.uuid4().hex[:16]}"

        share = DocumentShare(
            document_id=document_id,
            organization_id=share_data["organization_id"],
            share_type=share_data["share_type"],
            shared_with_user_id=share_data.get("shared_with_user_id"),
            shared_with_group_id=share_data.get("shared_with_group_id"),
            shared_with_email=share_data.get("shared_with_email"),
            access_level=share_data.get("access_level", AccessLevel.VIEW),
            can_download=share_data.get("can_download", True),
            can_print=share_data.get("can_print", True),
            can_copy=share_data.get("can_copy", True),
            can_share=share_data.get("can_share", False),
            is_public_link=share_data.get("is_public_link", False),
            share_token=share_token,
            expires_at=share_data.get("expires_at"),
            max_views=share_data.get("max_views"),
            max_downloads=share_data.get("max_downloads"),
            share_message=share_data.get("share_message"),
            notify_on_access=share_data.get("notify_on_access", False),
            shared_by_id=shared_by_id,
        )

        db.add(share)
        db.commit()
        db.refresh(share)

        # Update document share count
        document = await self.get_document_by_id(db, document_id)
        document.share_count += 1
        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            document_id,
            "share",
            "Document shared",
            shared_by_id,
            {
                "share_type": share_data["share_type"],
                "access_level": share_data.get("access_level"),
            },
        )

        return share

    async def get_document_shares(
        self, db: Session, document_id: str, include_expired: bool = False
    ) -> List[DocumentShare]:
        """Get all shares for a document."""

        query = db.query(DocumentShare).filter(
            DocumentShare.document_id == document_id,
            DocumentShare.is_active,
            not DocumentShare.is_revoked,
        )

        if not include_expired:
            now = datetime.utcnow()
            query = query.filter(
                or_(DocumentShare.expires_at.is_(None), DocumentShare.expires_at > now)
            )

        return query.all()

    async def revoke_document_share(
        self, db: Session, share_id: str, revoked_by_id: str
    ) -> bool:
        """Revoke a document share."""

        share = db.query(DocumentShare).filter(DocumentShare.id == share_id).first()
        if not share:
            return False

        share.is_revoked = True
        share.revoked_at = datetime.utcnow()
        share.revoked_by_id = revoked_by_id

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            share.document_id,
            "unshare",
            "Document share revoked",
            revoked_by_id,
            {"share_id": share_id},
        )

        return True

    # =============================================================================
    # Document Comments and Collaboration
    # =============================================================================

    async def create_document_comment(
        self, db: Session, comment_data: dict, author_id: str
    ) -> DocumentComment:
        """Create a comment on a document."""

        comment = DocumentComment(
            document_id=comment_data["document_id"],
            organization_id=comment_data["organization_id"],
            content=comment_data["content"],
            comment_type=comment_data.get("comment_type", "general"),
            page_number=comment_data.get("page_number"),
            position_x=comment_data.get("position_x"),
            position_y=comment_data.get("position_y"),
            selection_start=comment_data.get("selection_start"),
            selection_end=comment_data.get("selection_end"),
            selected_text=comment_data.get("selected_text"),
            parent_comment_id=comment_data.get("parent_comment_id"),
            thread_id=comment_data.get("thread_id", str(uuid.uuid4())),
            mentioned_users=comment_data.get("mentioned_users", []),
            is_private=comment_data.get("is_private", False),
            requires_response=comment_data.get("requires_response", False),
            attachments=comment_data.get("attachments", []),
            author_id=author_id,
        )

        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Update document comment count
        document = await self.get_document_by_id(db, comment_data["document_id"])
        document.comment_count += 1
        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            comment_data["document_id"],
            "comment",
            "Comment added",
            author_id,
            {
                "comment_id": comment.id,
                "comment_type": comment_data.get("comment_type"),
            },
        )

        return comment

    async def resolve_comment(
        self, db: Session, comment_id: str, resolved_by_id: str
    ) -> Optional[DocumentComment]:
        """Mark a comment as resolved."""

        comment = (
            db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()
        )
        if not comment:
            return None

        comment.is_resolved = True
        comment.resolved_at = datetime.utcnow()
        comment.resolved_by_id = resolved_by_id

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            comment.document_id,
            "comment_resolve",
            "Comment resolved",
            resolved_by_id,
            {"comment_id": comment_id},
        )

        return comment

    # =============================================================================
    # Document Approval Workflow
    # =============================================================================

    async def create_approval_workflow(
        self, db: Session, workflow_data: dict, created_by_id: str
    ) -> DocumentWorkflow:
        """Create a document approval workflow."""

        workflow = DocumentWorkflow(
            name=workflow_data["name"],
            description=workflow_data.get("description"),
            workflow_type=workflow_data.get("workflow_type", "approval"),
            organization_id=workflow_data["organization_id"],
            steps=workflow_data.get("steps", []),
            routing_rules=workflow_data.get("routing_rules", {}),
            escalation_rules=workflow_data.get("escalation_rules", {}),
            default_deadline_days=workflow_data.get("default_deadline_days", 7),
            reminder_intervals=workflow_data.get("reminder_intervals", [1, 3, 5]),
            auto_approve_timeout=workflow_data.get("auto_approve_timeout"),
            notification_templates=workflow_data.get("notification_templates", {}),
            send_notifications=workflow_data.get("send_notifications", True),
            trigger_conditions=workflow_data.get("trigger_conditions", {}),
            completion_actions=workflow_data.get("completion_actions", {}),
            tags=workflow_data.get("tags", []),
            created_by_id=created_by_id,
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        return workflow

    async def submit_document_for_approval(
        self,
        db: Session,
        document_id: str,
        workflow_id: str,
        approvers: List[Dict[str, Any]],
        requested_by_id: str,
    ) -> List[DocumentApproval]:
        """Submit document for approval workflow."""

        document = await self.get_document_by_id(db, document_id)
        if not document:
            raise ValueError("Document not found")

        workflow = (
            db.query(DocumentWorkflow)
            .filter(DocumentWorkflow.id == workflow_id)
            .first()
        )
        if not workflow:
            raise ValueError("Workflow not found")

        # Update document status
        document.status = DocumentStatus.PENDING_REVIEW
        document.requires_approval = True
        document.approval_workflow_id = workflow_id

        approvals = []

        for i, approver_data in enumerate(approvers):
            approval = DocumentApproval(
                document_id=document_id,
                organization_id=document.organization_id,
                workflow_id=workflow_id,
                step_number=i + 1,
                step_name=approver_data.get("step_name", f"Step {i + 1}"),
                approver_id=approver_data["approver_id"],
                approver_role=approver_data.get("approver_role"),
                is_required=approver_data.get("is_required", True),
                deadline=datetime.utcnow()
                + timedelta(days=workflow.default_deadline_days),
                approval_criteria=approver_data.get("approval_criteria", {}),
                requested_by_id=requested_by_id,
            )

            db.add(approval)
            approvals.append(approval)

        # Set current approver to first step
        if approvals:
            document.current_approver_id = approvals[0].approver_id
            document.approval_deadline = approvals[0].deadline

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            document_id,
            "approval_request",
            "Document submitted for approval",
            requested_by_id,
            {"workflow_id": workflow_id, "approver_count": len(approvers)},
        )

        return approvals

    async def process_approval_decision(
        self,
        db: Session,
        approval_id: str,
        decision: ApprovalStatus,
        comments: Optional[str] = None,
        conditions: Optional[str] = None,
    ) -> DocumentApproval:
        """Process an approval decision."""

        approval = (
            db.query(DocumentApproval)
            .filter(DocumentApproval.id == approval_id)
            .first()
        )
        if not approval:
            raise ValueError("Approval not found")

        approval.status = decision
        approval.decision_date = datetime.utcnow()
        approval.comments = comments
        approval.conditions = conditions

        document = await self.get_document_by_id(db, approval.document_id)

        if decision == ApprovalStatus.APPROVED:
            # Check if this was the final approval step
            remaining_approvals = (
                db.query(DocumentApproval)
                .filter(
                    DocumentApproval.document_id == approval.document_id,
                    DocumentApproval.status == ApprovalStatus.PENDING,
                    DocumentApproval.step_number > approval.step_number,
                )
                .all()
            )

            if not remaining_approvals:
                # All approvals complete
                document.status = DocumentStatus.APPROVED
                document.current_approver_id = None
                document.approval_deadline = None
            else:
                # Move to next approver
                next_approval = min(remaining_approvals, key=lambda x: x.step_number)
                document.current_approver_id = next_approval.approver_id
                document.approval_deadline = next_approval.deadline

        elif decision == ApprovalStatus.REJECTED:
            # Approval rejected - stop workflow
            document.status = DocumentStatus.DRAFT
            document.current_approver_id = None
            document.approval_deadline = None

            # Mark all pending approvals as withdrawn
            pending_approvals = (
                db.query(DocumentApproval)
                .filter(
                    DocumentApproval.document_id == approval.document_id,
                    DocumentApproval.status == ApprovalStatus.PENDING,
                )
                .all()
            )

            for pending in pending_approvals:
                if pending.id != approval_id:
                    pending.status = ApprovalStatus.WITHDRAWN

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            approval.document_id,
            "approval_decision",
            f"Approval {decision.value}",
            approval.approver_id,
            {"approval_id": approval_id, "decision": decision.value},
        )

        return approval

    # =============================================================================
    # Digital Signatures
    # =============================================================================

    async def request_document_signature(
        self,
        db: Session,
        document_id: str,
        signers: List[Dict[str, Any]],
        requested_by_id: str,
    ) -> List[DocumentSignature]:
        """Request digital signatures for a document."""

        document = await self.get_document_by_id(db, document_id)
        if not document:
            raise ValueError("Document not found")

        document.requires_signature = True
        document.signature_status = SignatureStatus.PENDING

        signatures = []

        for signer_data in signers:
            signature = DocumentSignature(
                document_id=document_id,
                organization_id=document.organization_id,
                signer_id=signer_data.get("signer_id"),
                signer_name=signer_data["signer_name"],
                signer_email=signer_data["signer_email"],
                signer_role=signer_data.get("signer_role"),
                signature_type=signer_data.get("signature_type", "electronic"),
                page_number=signer_data.get("page_number", 1),
                position_x=signer_data.get("position_x"),
                position_y=signer_data.get("position_y"),
                width=signer_data.get("width", 150),
                height=signer_data.get("height", 50),
                signing_deadline=signer_data.get("signing_deadline"),
                requested_by_id=requested_by_id,
            )

            db.add(signature)
            signatures.append(signature)

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            document_id,
            "signature_request",
            "Signature requested",
            requested_by_id,
            {"signer_count": len(signers)},
        )

        return signatures

    async def process_document_signature(
        self,
        db: Session,
        signature_id: str,
        signature_data: bytes,
        signer_metadata: Dict[str, Any],
    ) -> DocumentSignature:
        """Process a document signature."""

        signature = (
            db.query(DocumentSignature)
            .filter(DocumentSignature.id == signature_id)
            .first()
        )
        if not signature:
            raise ValueError("Signature request not found")

        # Generate signature hash
        signature_hash = hashlib.sha256(signature_data).hexdigest()

        signature.signature_data = signature_data
        signature.signature_hash = signature_hash
        signature.status = SignatureStatus.SIGNED
        signature.signed_at = datetime.utcnow()
        signature.ip_address = signer_metadata.get("ip_address")
        signature.user_agent = signer_metadata.get("user_agent")
        signature.geolocation = signer_metadata.get("geolocation", {})
        signature.consent_given = True
        signature.consent_timestamp = datetime.utcnow()
        signature.is_verified = True
        signature.verification_method = signer_metadata.get(
            "verification_method", "email"
        )

        # Update audit trail
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "signature_applied",
            "signer_email": signature.signer_email,
            "ip_address": signature.ip_address,
            "user_agent": signature.user_agent,
        }

        if signature.audit_trail:
            signature.audit_trail.append(audit_entry)
        else:
            signature.audit_trail = [audit_entry]

        # Check if all signatures are complete
        document = await self.get_document_by_id(db, signature.document_id)
        pending_signatures = (
            db.query(DocumentSignature)
            .filter(
                DocumentSignature.document_id == signature.document_id,
                DocumentSignature.status == SignatureStatus.PENDING,
            )
            .count()
        )

        if pending_signatures == 0:
            document.signature_status = SignatureStatus.SIGNED

        db.commit()

        # Log activity
        await self._log_document_activity(
            db,
            signature.document_id,
            "signature",
            "Document signed",
            signature.signer_id,
            {"signature_id": signature_id},
        )

        return signature

    # =============================================================================
    # Document Templates
    # =============================================================================

    async def create_document_template(
        self, db: Session, template_data: dict, created_by_id: str
    ) -> DocumentTemplate:
        """Create a document template."""

        template = DocumentTemplate(
            name=template_data["name"],
            description=template_data.get("description"),
            category=template_data.get("category"),
            subcategory=template_data.get("subcategory"),
            document_type=template_data["document_type"],
            template_format=template_data.get("template_format"),
            organization_id=template_data["organization_id"],
            template_content=template_data.get("template_content"),
            default_filename=template_data.get("default_filename"),
            placeholder_fields=template_data.get("placeholder_fields", []),
            required_fields=template_data.get("required_fields", []),
            auto_fill_rules=template_data.get("auto_fill_rules", {}),
            validation_rules=template_data.get("validation_rules", {}),
            output_format=template_data.get("output_format"),
            owner_id=template_data["owner_id"],
            is_public=template_data.get("is_public", False),
            is_restricted=template_data.get("is_restricted", False),
            allowed_groups=template_data.get("allowed_groups", []),
            tags=template_data.get("tags", []),
            created_by_id=created_by_id,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        return template

    async def generate_document_from_template(
        self,
        db: Session,
        template_id: str,
        field_values: Dict[str, Any],
        generated_by_id: str,
    ) -> DocumentExtended:
        """Generate a document from a template with field substitution."""

        template = (
            db.query(DocumentTemplate)
            .filter(DocumentTemplate.id == template_id)
            .first()
        )
        if not template:
            raise ValueError("Template not found")

        # Process template content with field values
        processed_content = template.template_content
        for field, value in field_values.items():
            placeholder = f"{{{{{field}}}}}"
            processed_content = processed_content.replace(placeholder, str(value))

        # Generate filename
        filename = (
            template.default_filename
            or f"Document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        for field, value in field_values.items():
            placeholder = f"{{{{{field}}}}}"
            filename = filename.replace(placeholder, str(value))

        # Create document
        document_data = {
            "title": filename,
            "filename": filename,
            "document_type": template.document_type,
            "category": template.category,
            "subcategory": template.subcategory,
            "organization_id": template.organization_id,
            "owner_id": generated_by_id,
            "created_by_id": generated_by_id,
            "metadata": {
                "generated_from_template": template_id,
                "template_name": template.name,
                "generation_date": datetime.utcnow().isoformat(),
                "field_values": field_values,
            },
        }

        document = await self.create_document(
            db, document_data, processed_content.encode()
        )

        # Update template usage statistics
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        db.commit()

        return document

    # =============================================================================
    # Search and Analytics
    # =============================================================================

    async def search_documents(
        self,
        db: Session,
        organization_id: str,
        search_query: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DocumentExtended]:
        """Advanced document search with full-text search and filtering."""

        query = db.query(DocumentExtended).filter(
            DocumentExtended.organization_id == organization_id,
            DocumentExtended.status != DocumentStatus.DELETED,
        )

        # Full-text search
        if search_query:
            search_terms = search_query.split()
            search_conditions = []

            for term in search_terms:
                term_condition = or_(
                    DocumentExtended.title.ilike(f"%{term}%"),
                    DocumentExtended.description.ilike(f"%{term}%"),
                    DocumentExtended.filename.ilike(f"%{term}%"),
                    DocumentExtended.extracted_text.ilike(f"%{term}%"),
                    DocumentExtended.ocr_text.ilike(f"%{term}%"),
                )
                search_conditions.append(term_condition)

            # All terms must match (AND operation)
            query = query.filter(and_(*search_conditions))

        # Apply filters
        if filters:
            if filters.get("document_type"):
                query = query.filter(
                    DocumentExtended.document_type == filters["document_type"]
                )

            if filters.get("category"):
                query = query.filter(DocumentExtended.category == filters["category"])

            if filters.get("owner_id"):
                query = query.filter(DocumentExtended.owner_id == filters["owner_id"])

            if filters.get("created_after"):
                query = query.filter(
                    DocumentExtended.created_at >= filters["created_after"]
                )

            if filters.get("created_before"):
                query = query.filter(
                    DocumentExtended.created_at <= filters["created_before"]
                )

            if filters.get("tags"):
                for tag in filters["tags"]:
                    query = query.filter(DocumentExtended.tags.contains([tag]))

        # Order by relevance (view count, last modified, etc.)
        query = query.order_by(
            desc(DocumentExtended.view_count),
            desc(DocumentExtended.last_modified_at),
            desc(DocumentExtended.created_at),
        )

        return query.offset(skip).limit(limit).all()

    async def get_document_analytics(
        self, db: Session, organization_id: str, period_start: date, period_end: date
    ) -> DocumentAnalytics:
        """Generate comprehensive document analytics for a period."""

        # Document metrics
        total_docs = (
            db.query(DocumentExtended)
            .filter(
                DocumentExtended.organization_id == organization_id,
                DocumentExtended.status != DocumentStatus.DELETED,
            )
            .count()
        )

        new_docs = (
            db.query(DocumentExtended)
            .filter(
                DocumentExtended.organization_id == organization_id,
                DocumentExtended.created_at >= period_start,
                DocumentExtended.created_at <= period_end,
            )
            .count()
        )

        updated_docs = (
            db.query(DocumentExtended)
            .filter(
                DocumentExtended.organization_id == organization_id,
                DocumentExtended.last_modified_at >= period_start,
                DocumentExtended.last_modified_at <= period_end,
                DocumentExtended.created_at < period_start,
            )
            .count()
        )

        deleted_docs = (
            db.query(DocumentExtended)
            .filter(
                DocumentExtended.organization_id == organization_id,
                DocumentExtended.status == DocumentStatus.DELETED,
                DocumentExtended.archived_at >= period_start,
                DocumentExtended.archived_at <= period_end,
            )
            .count()
        )

        # Storage metrics
        storage_stats = (
            db.query(
                func.sum(DocumentExtended.file_size_bytes).label("total_storage"),
                func.avg(DocumentExtended.file_size_bytes).label("avg_file_size"),
                func.max(DocumentExtended.file_size_bytes).label("max_file_size"),
            )
            .filter(
                DocumentExtended.organization_id == organization_id,
                DocumentExtended.status != DocumentStatus.DELETED,
            )
            .first()
        )

        # Activity metrics
        activities = db.query(DocumentActivity).filter(
            DocumentActivity.organization_id == organization_id,
            DocumentActivity.timestamp >= period_start,
            DocumentActivity.timestamp <= period_end,
        )

        total_views = activities.filter(
            DocumentActivity.activity_type == "view"
        ).count()
        total_downloads = activities.filter(
            DocumentActivity.activity_type == "download"
        ).count()
        total_shares = activities.filter(
            DocumentActivity.activity_type == "share"
        ).count()

        unique_viewers = (
            activities.filter(DocumentActivity.activity_type == "view")
            .distinct(DocumentActivity.user_id)
            .count()
        )

        # Collaboration metrics
        comments = (
            db.query(DocumentComment)
            .filter(
                DocumentComment.organization_id == organization_id,
                DocumentComment.created_at >= period_start,
                DocumentComment.created_at <= period_end,
            )
            .count()
        )

        active_collaborators = (
            db.query(DocumentComment)
            .filter(
                DocumentComment.organization_id == organization_id,
                DocumentComment.created_at >= period_start,
                DocumentComment.created_at <= period_end,
            )
            .distinct(DocumentComment.author_id)
            .count()
        )

        # Workflow metrics
        approvals_requested = (
            db.query(DocumentApproval)
            .filter(
                DocumentApproval.organization_id == organization_id,
                DocumentApproval.created_at >= period_start,
                DocumentApproval.created_at <= period_end,
            )
            .count()
        )

        approvals_completed = (
            db.query(DocumentApproval)
            .filter(
                DocumentApproval.organization_id == organization_id,
                DocumentApproval.decision_date >= period_start,
                DocumentApproval.decision_date <= period_end,
                DocumentApproval.status.in_(
                    [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]
                ),
            )
            .count()
        )

        # Signature metrics
        signatures_requested = (
            db.query(DocumentSignature)
            .filter(
                DocumentSignature.organization_id == organization_id,
                DocumentSignature.created_at >= period_start,
                DocumentSignature.created_at <= period_end,
            )
            .count()
        )

        signatures_completed = (
            db.query(DocumentSignature)
            .filter(
                DocumentSignature.organization_id == organization_id,
                DocumentSignature.signed_at >= period_start,
                DocumentSignature.signed_at <= period_end,
                DocumentSignature.status == SignatureStatus.SIGNED,
            )
            .count()
        )

        # Create analytics record
        analytics = DocumentAnalytics(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            total_documents=total_docs,
            new_documents=new_docs,
            updated_documents=updated_docs,
            deleted_documents=deleted_docs,
            total_storage_bytes=storage_stats.total_storage or 0,
            average_file_size_bytes=storage_stats.avg_file_size or 0,
            largest_file_size_bytes=storage_stats.max_file_size or 0,
            total_views=total_views,
            unique_viewers=unique_viewers,
            total_downloads=total_downloads,
            total_shares=total_shares,
            total_comments=comments,
            active_collaborators=active_collaborators,
            approvals_requested=approvals_requested,
            approvals_completed=approvals_completed,
            signatures_requested=signatures_requested,
            signatures_completed=signatures_completed,
            calculated_date=datetime.utcnow(),
        )

        db.add(analytics)
        db.commit()
        db.refresh(analytics)

        return analytics

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _log_document_activity(
        self,
        db: Session,
        document_id: str,
        activity_type: str,
        description: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> DocumentActivity:
        """Log document activity for audit trail."""

        activity = DocumentActivity(
            document_id=document_id,
            organization_id=db.query(DocumentExtended.organization_id)
            .filter(DocumentExtended.id == document_id)
            .scalar(),
            activity_type=activity_type,
            action=activity_type,
            description=description,
            user_id=user_id,
            details=details or {},
            success=True,
        )

        db.add(activity)
        db.commit()

        return activity

    async def _update_folder_statistics(self, db: Session, folder_id: str) -> dict:
        """Update folder statistics (document count, size, etc.)."""

        folder = db.query(DocumentFolder).filter(DocumentFolder.id == folder_id).first()
        if not folder:
            return

        # Count documents in folder
        doc_stats = (
            db.query(
                func.count(DocumentExtended.id).label("doc_count"),
                func.sum(DocumentExtended.file_size_bytes).label("total_size"),
            )
            .filter(
                DocumentExtended.folder_id == folder_id,
                DocumentExtended.status != DocumentStatus.DELETED,
            )
            .first()
        )

        # Count subfolders
        subfolder_count = (
            db.query(DocumentFolder)
            .filter(
                DocumentFolder.parent_folder_id == folder_id,
                not DocumentFolder.is_archived,
            )
            .count()
        )

        folder.document_count = doc_stats.doc_count or 0
        folder.total_size_bytes = doc_stats.total_size or 0
        folder.subfolder_count = subfolder_count
        folder.current_usage_bytes = doc_stats.total_size or 0

        db.commit()

    async def get_system_health(self, db: Session) -> Dict[str, Any]:
        """Get document management system health status."""

        try:
            # Test database connectivity
            db.execute("SELECT 1")

            # Get basic statistics
            total_documents = db.query(DocumentExtended).count()
            total_storage = (
                db.query(func.sum(DocumentExtended.file_size_bytes)).scalar() or 0
            )
            total_folders = db.query(DocumentFolder).count()

            return {
                "status": "healthy",
                "database_connection": "OK",
                "services_available": True,
                "statistics": {
                    "total_documents": total_documents,
                    "total_storage_bytes": total_storage,
                    "total_folders": total_folders,
                },
                "version": "31.0",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
