"""User privacy settings service."""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.models.user import User
from app.models.user_privacy import UserPrivacySettings
from app.schemas.user_privacy import (
    PrivacyCheckResult,
    PrivacySettingsCreate,
    PrivacySettingsResponse,
    PrivacySettingsUpdate,
    VisibilityLevel,
)


class UserPrivacyService:
    """User privacy settings management service."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def create_settings(
        self, user_id: int, data: PrivacySettingsCreate
    ) -> PrivacySettingsResponse:
        """Create privacy settings for user."""
        # Check if settings already exist
        existing = (
            self.db.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user_id)
            .first()
        )
        if existing:
            # Update existing settings instead
            return self.update_settings(user_id, PrivacySettingsUpdate(**data.dict()))

        # Create new settings
        settings = UserPrivacySettings.create(
            self.db,
            user_id=user_id,
            profile_visibility=data.profile_visibility,
            email_visibility=data.email_visibility,
            phone_visibility=data.phone_visibility,
            activity_visibility=data.activity_visibility,
            show_online_status=data.show_online_status,
            allow_direct_messages=data.allow_direct_messages,
            searchable_by_email=data.searchable_by_email,
            searchable_by_name=data.searchable_by_name,
        )

        self.db.commit()

        return PrivacySettingsResponse.from_orm(settings)

    def get_settings(self, user_id: int) -> PrivacySettingsResponse:
        """Get user's privacy settings."""
        settings = (
            self.db.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user_id)
            .first()
        )

        if not settings:
            raise NotFound("プライバシー設定が見つかりません")

        return PrivacySettingsResponse.from_orm(settings)

    def get_settings_or_default(self, user_id: int) -> PrivacySettingsResponse:
        """Get user's privacy settings or return defaults."""
        try:
            return self.get_settings(user_id)
        except NotFound:
            # Return default settings
            default_data = PrivacySettingsCreate()
            return PrivacySettingsResponse(
                id=0,  # Temporary ID for defaults
                user_id=user_id,
                profile_visibility=default_data.profile_visibility,
                email_visibility=default_data.email_visibility,
                phone_visibility=default_data.phone_visibility,
                activity_visibility=default_data.activity_visibility,
                show_online_status=default_data.show_online_status,
                allow_direct_messages=default_data.allow_direct_messages,
                searchable_by_email=default_data.searchable_by_email,
                searchable_by_name=default_data.searchable_by_name,
                created_at=None,
                updated_at=None,
            )

    def update_settings(
        self, user_id: int, data: PrivacySettingsUpdate
    ) -> PrivacySettingsResponse:
        """Update user's privacy settings."""
        settings = (
            self.db.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user_id)
            .first()
        )

        if not settings:
            raise NotFound("プライバシー設定が見つかりません")

        # Update only provided fields
        update_data = data.dict(exclude_unset=True)
        settings.update(self.db, **update_data)

        self.db.commit()

        return PrivacySettingsResponse.from_orm(settings)

    def set_all_private(self, user_id: int) -> PrivacySettingsResponse:
        """Set all privacy settings to most restrictive."""
        settings = (
            self.db.query(UserPrivacySettings)
            .filter(UserPrivacySettings.user_id == user_id)
            .first()
        )

        if not settings:
            # Create with all private
            settings = UserPrivacySettings.create(
                self.db,
                user_id=user_id,
                profile_visibility=VisibilityLevel.PRIVATE,
                email_visibility=VisibilityLevel.PRIVATE,
                phone_visibility=VisibilityLevel.PRIVATE,
                activity_visibility=VisibilityLevel.PRIVATE,
                show_online_status=False,
                allow_direct_messages=False,
                searchable_by_email=False,
                searchable_by_name=False,
            )
        else:
            settings.set_all_private(self.db)

        self.db.commit()

        return PrivacySettingsResponse.from_orm(settings)

    def can_view_profile(self, viewer_id: int, target_user_id: int) -> bool:
        """Check if viewer can see target user's profile."""
        if viewer_id == target_user_id:
            return True  # Users can always see their own profile

        # Check if viewer is admin
        viewer = self.db.query(User).filter(User.id == viewer_id).first()
        if viewer and viewer.is_superuser:
            return True  # Admins can see all profiles

        settings = self.get_settings_or_default(target_user_id)
        return self._check_visibility(
            viewer_id, target_user_id, settings.profile_visibility
        )

    def can_view_email(self, viewer_id: int, target_user_id: int) -> bool:
        """Check if viewer can see target user's email."""
        if viewer_id == target_user_id:
            return True

        viewer = self.db.query(User).filter(User.id == viewer_id).first()
        if viewer and viewer.is_superuser:
            return True

        settings = self.get_settings_or_default(target_user_id)
        return self._check_visibility(
            viewer_id, target_user_id, settings.email_visibility
        )

    def can_view_phone(self, viewer_id: int, target_user_id: int) -> bool:
        """Check if viewer can see target user's phone."""
        if viewer_id == target_user_id:
            return True

        viewer = self.db.query(User).filter(User.id == viewer_id).first()
        if viewer and viewer.is_superuser:
            return True

        settings = self.get_settings_or_default(target_user_id)
        return self._check_visibility(
            viewer_id, target_user_id, settings.phone_visibility
        )

    def can_view_activity(self, viewer_id: int, target_user_id: int) -> bool:
        """Check if viewer can see target user's activity."""
        if viewer_id == target_user_id:
            return True

        viewer = self.db.query(User).filter(User.id == viewer_id).first()
        if viewer and viewer.is_superuser:
            return True

        settings = self.get_settings_or_default(target_user_id)
        return self._check_visibility(
            viewer_id, target_user_id, settings.activity_visibility
        )

    def can_view_online_status(self, viewer_id: int, target_user_id: int) -> bool:
        """Check if viewer can see target user's online status."""
        if viewer_id == target_user_id:
            return True

        viewer = self.db.query(User).filter(User.id == viewer_id).first()
        if viewer and viewer.is_superuser:
            return True

        settings = self.get_settings_or_default(target_user_id)
        return settings.show_online_status

    def can_send_direct_message(self, sender_id: int, recipient_id: int) -> bool:
        """Check if sender can send direct message to recipient."""
        if sender_id == recipient_id:
            return False  # Can't message self

        sender = self.db.query(User).filter(User.id == sender_id).first()
        if sender and sender.is_superuser:
            return True

        settings = self.get_settings_or_default(recipient_id)
        return settings.allow_direct_messages

    def is_searchable_by_email(self, user_id: int) -> bool:
        """Check if user can be found by email search."""
        settings = self.get_settings_or_default(user_id)
        return settings.searchable_by_email

    def is_searchable_by_name(self, user_id: int) -> bool:
        """Check if user can be found by name search."""
        settings = self.get_settings_or_default(user_id)
        return settings.searchable_by_name

    def apply_privacy_filter(
        self, user_data: Dict[str, Any], viewer_id: int, target_user_id: int
    ) -> Dict[str, Any]:
        """Apply privacy filters to user data based on viewer permissions."""
        filtered_data = {"id": user_data["id"], "full_name": user_data["full_name"]}

        # Check email visibility
        if self.can_view_email(viewer_id, target_user_id):
            filtered_data["email"] = user_data.get("email")
        else:
            filtered_data["email"] = "***"

        # Check phone visibility
        if self.can_view_phone(viewer_id, target_user_id):
            filtered_data["phone"] = user_data.get("phone")
        else:
            filtered_data["phone"] = "***"

        # Check profile visibility
        if self.can_view_profile(viewer_id, target_user_id):
            filtered_data["profile_image_url"] = user_data.get("profile_image_url")

        # Check online status visibility
        if self.can_view_online_status(viewer_id, target_user_id):
            filtered_data["is_online"] = user_data.get("is_online")

        # Check activity visibility
        if self.can_view_activity(viewer_id, target_user_id):
            filtered_data["last_activity"] = user_data.get("last_activity")

        return filtered_data

    def _check_visibility(
        self, viewer_id: int, target_user_id: int, visibility: VisibilityLevel
    ) -> bool:
        """Check visibility based on level."""
        if visibility == VisibilityLevel.PUBLIC:
            return True
        elif visibility == VisibilityLevel.PRIVATE:
            return False
        elif visibility == VisibilityLevel.ORGANIZATION:
            return self._users_in_same_organization(viewer_id, target_user_id)
        elif visibility == VisibilityLevel.DEPARTMENT:
            return self._users_in_same_department(viewer_id, target_user_id)
        else:
            return False

    def _users_in_same_organization(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are in the same organization."""
        user1 = self.db.query(User).filter(User.id == user1_id).first()
        user2 = self.db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            return False

        # Get organizations for both users
        user1_org_ids = {org.id for org in user1.get_organizations()}
        user2_org_ids = {org.id for org in user2.get_organizations()}

        # Check for intersection
        return bool(user1_org_ids & user2_org_ids)

    def _users_in_same_department(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are in the same department."""
        user1 = self.db.query(User).filter(User.id == user1_id).first()
        user2 = self.db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            return False

        # Check direct department membership
        if user1.department_id and user1.department_id == user2.department_id:
            return True

        # Check departments through roles
        user1_dept_ids = {
            ur.department_id for ur in user1.user_roles if ur.department_id is not None
        }
        user2_dept_ids = {
            ur.department_id for ur in user2.user_roles if ur.department_id is not None
        }

        return bool(user1_dept_ids & user2_dept_ids)
