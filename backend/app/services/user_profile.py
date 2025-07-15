"""User profile management service."""

import io
from datetime import UTC, datetime

import pytz
from PIL import Image
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.user_privacy import UserPrivacySettings as UserPrivacy
from app.schemas.user_profile import (
    ProfileImageUploadResponse,
    UserPrivacySettings,
    UserPrivacySettingsUpdate,
    UserProfileResponse,
    UserProfileSettings,
    UserProfileSettingsUpdate,
    UserProfileUpdate,
)


# Mock storage client for now
class StorageClient:
    """Mock storage client."""

    def upload(self, file_data: bytes, path: str, content_type: str) -> str:
        """Mock upload method."""
        return f"/uploads/{path}"


storage_client = StorageClient()


class UserProfileService:
    """Service for managing user profiles."""

    # Allowed image formats
    ALLOWED_IMAGE_FORMATS = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    # Max image size: 5MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    # Profile image dimensions
    PROFILE_IMAGE_SIZE = (400, 400)
    # Thumbnail size
    THUMBNAIL_SIZE = (100, 100)

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db

    def upload_profile_image(
        self,
        user_id: int,
        file_data: bytes,
        filename: str,
        content_type: str,
        uploader: User,
        db: Session,
    ) -> ProfileImageUploadResponse:
        """Upload user profile image."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if uploader.id != user.id and not uploader.is_superuser:
            raise PermissionDenied("Cannot upload profile image for another user")

        # Validate image format
        if content_type not in self.ALLOWED_IMAGE_FORMATS:
            raise BusinessLogicError(
                "Invalid image format. Allowed formats: "
                f"{', '.join(self.ALLOWED_IMAGE_FORMATS)}"
            )

        # Validate image size
        if len(file_data) > self.MAX_IMAGE_SIZE:
            raise BusinessLogicError(
                f"Image size exceeds limit of {self.MAX_IMAGE_SIZE // 1024 // 1024}MB"
            )

        # Process image
        processed_data, size = self._process_image(file_data)

        # Generate unique filename
        ext = filename.split(".")[-1] if "." in filename else "png"
        unique_filename = f"{user_id}_{datetime.now(UTC).timestamp()}.{ext}"
        storage_path = f"profile/{unique_filename}"

        # Upload to storage
        url = storage_client.upload(processed_data, storage_path, content_type)

        # Update user profile
        user.profile_image_url = url
        db.add(user)
        db.commit()

        return ProfileImageUploadResponse(
            url=url,
            size=size,
            content_type=content_type,
            uploaded_at=datetime.now(UTC),
        )

    def delete_profile_image(self, user_id: int, deleter: User, db: Session) -> None:
        """Delete user profile image."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if deleter.id != user.id and not deleter.is_superuser:
            raise PermissionDenied("Cannot delete profile image for another user")

        # Remove profile image
        user.profile_image_url = None
        db.add(user)
        db.commit()

    def update_profile(
        self,
        user_id: int,
        data: UserProfileUpdate,
        updater: User,
        db: Session,
    ) -> UserProfileResponse:
        """Update user profile information."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if updater.id != user.id and not updater.is_superuser:
            raise PermissionDenied("Cannot update profile for another user")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)

        return self._user_to_profile_response(user, updater)

    def get_profile_settings(
        self, user_id: int, viewer: User, db: Session
    ) -> UserProfileSettings:
        """Get user profile settings."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if viewer.id != user.id and not viewer.is_superuser:
            raise PermissionDenied("Cannot view profile settings for another user")

        # Get or create preferences
        prefs = (
            db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        )

        if not prefs:
            # Return defaults
            return UserProfileSettings(
                language="en",
                timezone="UTC",
                date_format="YYYY-MM-DD",
                time_format="24h",
                notification_email=True,
                notification_push=True,
                updated_at=datetime.now(UTC),
            )

        return UserProfileSettings(
            language=prefs.language,
            timezone=prefs.timezone,
            date_format=prefs.date_format,

            time_format="24h"
            if prefs.time_format not in ["12h", "24h"]
            else ("12h" if prefs.time_format == "12h" else "24h"),


            notification_email=prefs.notifications_email,
            notification_push=prefs.notifications_push,
            updated_at=prefs.updated_at,
        )

    def update_profile_settings(
        self,
        user_id: int,
        settings: UserProfileSettingsUpdate,
        updater: User,
        db: Session,
    ) -> UserProfileSettings:
        """Update user profile settings."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if updater.id != user.id and not updater.is_superuser:
            raise PermissionDenied("Cannot update profile settings for another user")

        # Validate settings
        update_data = settings.model_dump(exclude_unset=True)

        if "language" in update_data:
            # Validate language code
            valid_languages = ["en", "ja", "zh", "ko", "es", "fr", "de"]
            if update_data["language"] not in valid_languages:
                raise BusinessLogicError(
                    f"Invalid language code: {update_data['language']}"
                )

        if "timezone" in update_data:
            # Validate timezone
            try:
                pytz.timezone(update_data["timezone"])
            except pytz.exceptions.UnknownTimeZoneError:
                raise BusinessLogicError(f"Invalid timezone: {update_data['timezone']}")

        # Get or create preferences
        prefs = (
            db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        )

        if not prefs:
            prefs = UserPreferences(user_id=user.id)
            db.add(prefs)

        # Update settings - map field names
        field_mapping = {
            "notification_email": "notifications_email",
            "notification_push": "notifications_push",
        }

        for field, value in update_data.items():
            actual_field = field_mapping.get(field, field)
            setattr(prefs, actual_field, value)

        prefs.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(prefs)

        return UserProfileSettings(
            language=prefs.language,
            timezone=prefs.timezone,
            date_format=prefs.date_format,

            time_format="24h"
            if prefs.time_format not in ["12h", "24h"]
            else ("12h" if prefs.time_format == "12h" else "24h"),


            notification_email=prefs.notifications_email,
            notification_push=prefs.notifications_push,
            updated_at=prefs.updated_at,
        )

    def get_privacy_settings(
        self, user_id: int, viewer: User, db: Session
    ) -> UserPrivacySettings:
        """Get user privacy settings."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if viewer.id != user.id and not viewer.is_superuser:
            raise PermissionDenied("Cannot view privacy settings for another user")

        # Get or create privacy settings
        privacy = db.query(UserPrivacy).filter(UserPrivacy.user_id == user.id).first()

        if not privacy:
            # Return defaults
            return UserPrivacySettings(
                profile_visibility="organization",
                email_visibility="organization",
                phone_visibility="department",
                allow_direct_messages=True,
                show_online_status=True,
                updated_at=datetime.now(UTC),
            )

        return UserPrivacySettings(
            profile_visibility=privacy.profile_visibility.value,
            email_visibility=privacy.email_visibility.value,
            phone_visibility=privacy.phone_visibility.value,
            allow_direct_messages=privacy.allow_direct_messages,
            show_online_status=privacy.show_online_status,
            updated_at=privacy.updated_at,
        )

    def update_privacy_settings(
        self,
        user_id: int,
        settings: UserPrivacySettingsUpdate,
        updater: User,
        db: Session,
    ) -> UserPrivacySettings:
        """Update user privacy settings."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        # Permission check
        if updater.id != user.id and not updater.is_superuser:
            raise PermissionDenied("Cannot update privacy settings for another user")

        # Get or create privacy settings
        privacy = db.query(UserPrivacy).filter(UserPrivacy.user_id == user.id).first()

        if not privacy:
            privacy = UserPrivacy(user_id=user.id)
            db.add(privacy)

        # Update settings
        update_data = settings.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(privacy, field, value)

        privacy.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(privacy)

        return UserPrivacySettings(
            profile_visibility=privacy.profile_visibility.value,
            email_visibility=privacy.email_visibility.value,
            phone_visibility=privacy.phone_visibility.value,
            allow_direct_messages=privacy.allow_direct_messages,
            show_online_status=privacy.show_online_status,
            updated_at=privacy.updated_at,
        )

    def get_user_profile(
        self, user_id: int, viewer: User, db: Session
    ) -> UserProfileResponse:
        """Get user profile with privacy rules applied."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("User not found")

        return self._user_to_profile_response(user, viewer)

    def _process_image(self, file_data: bytes) -> tuple[bytes, int]:
        """Process image: resize, optimize."""
        try:
            # Open image
            img = Image.open(io.BytesIO(file_data))

            # Convert to RGB if necessary
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")  # type: ignore[assignment]

            # Resize to profile size
            img.thumbnail(self.PROFILE_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Save optimized image
            output = io.BytesIO()
            img.save(output, format="PNG", optimize=True)
            processed_data = output.getvalue()

            return processed_data, len(processed_data)

        except Exception:
            raise BusinessLogicError("Failed to process image")

    def _user_to_profile_response(
        self, user: User, viewer: User
    ) -> UserProfileResponse:
        """Convert user to profile response with privacy rules."""
        # Get privacy settings
        privacy = (
            self.db.query(UserPrivacy).filter(UserPrivacy.user_id == user.id).first()
        )

        # Admin can see everything
        if viewer.is_superuser:
            return UserProfileResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
                profile_image_url=user.profile_image_url,
                bio=getattr(user, "bio", None),
                location=getattr(user, "location", None),
                website=getattr(user, "website", None),
                is_online=user.is_online() if hasattr(user, "is_online") else None,
                last_seen_at=user.last_login_at,
            )

        # Apply privacy rules
        response_data = {
            "id": user.id,
            "full_name": user.full_name,
            "profile_image_url": user.profile_image_url,
            "bio": getattr(user, "bio", None),
            "location": getattr(user, "location", None),
            "website": getattr(user, "website", None),
        }

        # Import VisibilityLevel for comparison
        from app.schemas.user_privacy import VisibilityLevel

        # Check email visibility
        if (
            privacy
            and privacy.email_visibility == VisibilityLevel.PRIVATE
            and viewer.id != user.id
        ):
            response_data["email"] = None
        else:
            response_data["email"] = user.email

        # Check phone visibility
        if (
            privacy
            and privacy.phone_visibility == VisibilityLevel.PRIVATE
            and viewer.id != user.id
        ):
            response_data["phone"] = None
        else:
            response_data["phone"] = user.phone

        # Check online status visibility
        if privacy and not privacy.show_online_status and viewer.id != user.id:
            response_data["is_online"] = None
            response_data["last_seen_at"] = None
        else:
            response_data["is_online"] = (
                user.is_online() if hasattr(user, "is_online") else None
            )
            response_data["last_seen_at"] = user.last_login_at


        return UserProfileResponse(
            id=int(response_data["id"]) if response_data["id"] is not None else 0,  # type: ignore[arg-type]
            full_name=str(response_data["full_name"]),
            email=str(response_data.get("email"))
            if response_data.get("email") is not None
            else None,
            phone=str(response_data.get("phone"))
            if response_data.get("phone") is not None
            else None,
            profile_image_url=str(response_data.get("profile_image_url"))
            if response_data.get("profile_image_url") is not None
            else None,
            bio=str(response_data.get("bio"))
            if response_data.get("bio") is not None
            else None,
            location=str(response_data.get("location"))
            if response_data.get("location") is not None
            else None,
            website=str(response_data.get("website"))
            if response_data.get("website") is not None
            else None,
            is_online=bool(response_data.get("is_online"))
            if response_data.get("is_online") is not None
            else None,
            last_seen_at=response_data.get("last_seen_at")
            if isinstance(response_data.get("last_seen_at"), datetime)
            else None,  # type: ignore[arg-type]
        )

