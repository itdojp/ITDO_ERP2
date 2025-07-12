"""File upload service for handling file operations."""

import uuid
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
from fastapi import UploadFile

from app.core.config import get_settings


class FileUploadService:
    """Service for handling file uploads and management."""

    # Constants for file validation
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    MAX_FILE_SIZE_MB = 5

    def __init__(self) -> None:
        """Initialize file upload service."""
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIRECTORY)

    def validate_file_type(self, file: UploadFile, allowed_types: List[str]) -> None:
        """Validate file type against allowed types.
        
        Args:
            file: The uploaded file
            allowed_types: List of allowed MIME types
            
        Raises:
            ValueError: If file type is not allowed or not provided
        """
        if not file.content_type:
            raise ValueError("File content type not provided")

        if file.content_type not in allowed_types:
            raise ValueError(
                f"Invalid file type: {file.content_type}. "
                f"Allowed types: {', '.join(allowed_types)}"
            )

    def validate_file_size(self, file: UploadFile, max_size_mb: int) -> None:
        """Validate file size against maximum allowed size.
        
        Args:
            file: The uploaded file
            max_size_mb: Maximum file size in megabytes
            
        Raises:
            ValueError: If file size exceeds limit or not provided
        """
        if file.size is None:
            raise ValueError("File size not provided")

        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise ValueError(
                f"File size exceeds maximum allowed size of {max_size_mb}MB. "
                f"File size: {file.size / (1024 * 1024):.2f}MB"
            )

        if file.size == 0:
            raise ValueError("File is empty")

    def generate_unique_filename(self, original_filename: str, user_id: int) -> str:
        """Generate a unique filename for uploaded file.
        
        Args:
            original_filename: Original name of the uploaded file
            user_id: ID of the user uploading the file
            
        Returns:
            Unique filename string
        """
        # Extract file extension
        file_path = Path(original_filename)
        extension = file_path.suffix
        name_without_ext = file_path.stem

        # Generate unique identifier
        unique_id = uuid.uuid4().hex[:8]

        # Create unique filename: userid_uniqueid_originalname.ext
        if extension:
            return f"{user_id}_{unique_id}_{name_without_ext}{extension}"
        else:
            return f"{user_id}_{unique_id}_{name_without_ext}"

    def ensure_upload_directory(self) -> None:
        """Ensure upload directory exists."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile, filename: str) -> Path:
        """Save uploaded file to disk.
        
        Args:
            file: The uploaded file
            filename: Name to save the file as
            
        Returns:
            Path to the saved file
        """
        self.ensure_upload_directory()
        file_path = self.upload_dir / filename

        # Read file content
        content = await file.read()

        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return file_path

    async def upload_profile_image(self, file: UploadFile, user_id: int) -> Dict[str, Any]:
        """Upload and save a user's profile image.
        
        Args:
            file: The uploaded image file
            user_id: ID of the user
            
        Returns:
            Dictionary containing upload result
        """
        try:
            # Validate file type
            self.validate_file_type(file, self.ALLOWED_IMAGE_TYPES)

            # Validate file size
            self.validate_file_size(file, self.MAX_FILE_SIZE_MB)

            # Generate unique filename
            if not file.filename:
                raise ValueError("Filename not provided")

            unique_filename = self.generate_unique_filename(file.filename, user_id)

            # Save file
            file_path = await self.save_file(file, unique_filename)

            return {
                "success": True,
                "file_path": str(file_path),
                "filename": unique_filename,
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "url": self.get_file_url(unique_filename)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_file_url(self, filename: str) -> str:
        """Generate URL for accessing uploaded file.
        
        Args:
            filename: Name of the file
            
        Returns:
            URL string for accessing the file
        """
        base_url = self.settings.BASE_URL.rstrip('/')
        return f"{base_url}/uploads/{filename}"

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path traversal attempts
        filename = filename.replace("..", "")
        filename = filename.replace("/", "_")
        filename = filename.replace("\\", "_")

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 100:
            name_part = filename[:80]
            ext_part = filename[-20:] if "." in filename else ""
            filename = name_part + ext_part

        return filename
