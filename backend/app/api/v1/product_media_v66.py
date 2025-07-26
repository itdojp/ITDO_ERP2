"""
ITDO ERP Backend - Product Media Management v66
Advanced media management system with file upload, processing, and CDN integration
Day 8: Product Media & File Management Implementation
"""

from __future__ import annotations

import asyncio
import json
import uuid
import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO
from enum import Enum
import aiofiles
import aioredis
from PIL import Image, ImageOps
import ffmpeg
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON, BigInteger
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, and_, or_
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, 
    Query, BackgroundTasks, Form, status
)
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import BaseTable
from app.core.config import get_settings

# ============================================================================
# Configuration and Constants
# ============================================================================

class MediaType(str, Enum):
    """Media type enumeration"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    MODEL_3D = "3d_model"
    ARCHIVE = "archive"

class ImageFormat(str, Enum):
    """Image format enumeration"""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    SVG = "svg"

class ProcessingStatus(str, Enum):
    """Media processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Media configuration
MEDIA_CONFIG = {
    "upload_path": "/app/media",
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "allowed_image_types": ["image/jpeg", "image/png", "image/webp", "image/gif"],
    "allowed_video_types": ["video/mp4", "video/webm", "video/avi", "video/mov"],
    "allowed_document_types": ["application/pdf", "text/plain", "application/msword"],
    "image_sizes": {
        "thumbnail": (150, 150),
        "small": (300, 300),
        "medium": (600, 600),
        "large": (1200, 1200),
        "original": None
    },
    "video_qualities": {
        "low": {"width": 480, "bitrate": "500k"},
        "medium": {"width": 720, "bitrate": "1000k"},
        "high": {"width": 1080, "bitrate": "2000k"}
    }
}

# ============================================================================
# Database Models
# ============================================================================

class MediaStorage(BaseTable):
    """Media storage configuration model"""
    __tablename__ = "media_storage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    storage_type = Column(String(50), nullable=False)  # local, s3, gcs, azure
    configuration = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    base_url = Column(String(500))
    
    # Usage statistics
    total_files = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    
    __table_args__ = (
        Index("idx_storage_type", "storage_type"),
        Index("idx_storage_active", "is_active"),
        Index("idx_storage_default", "is_default"),
    )

class MediaFile(BaseTable):
    """Media file model"""
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    media_type = Column(String(50), nullable=False)
    
    # File metadata
    dimensions = Column(JSON)  # {"width": 1920, "height": 1080}
    duration = Column(Integer)  # Video/audio duration in seconds
    metadata = Column(JSON)     # Additional metadata (EXIF, etc.)
    
    # Processing
    processing_status = Column(String(50), default=ProcessingStatus.PENDING)
    processing_error = Column(Text)
    processed_at = Column(DateTime)
    
    # Storage
    storage_id = Column(UUID(as_uuid=True), ForeignKey("media_storage.id"))
    cdn_url = Column(String(1000))
    
    # Security
    access_level = Column(String(50), default="public")  # public, private, restricted
    upload_user_id = Column(UUID(as_uuid=True))
    
    # File integrity
    file_hash = Column(String(64))  # SHA-256 hash
    checksum = Column(String(32))   # MD5 checksum
    
    # Relationships
    storage = relationship("MediaStorage")
    variants = relationship("MediaVariant", back_populates="original_file")
    product_media = relationship("ProductMediaMapping", back_populates="media_file")
    
    __table_args__ = (
        Index("idx_media_filename", "filename"),
        Index("idx_media_type", "media_type"),
        Index("idx_media_mime", "mime_type"),
        Index("idx_media_status", "processing_status"),
        Index("idx_media_hash", "file_hash"),
        Index("idx_media_upload_user", "upload_user_id"),
    )

class MediaVariant(BaseTable):
    """Media variant model for different sizes/formats"""
    __tablename__ = "media_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id"), nullable=False)
    variant_name = Column(String(100), nullable=False)  # thumbnail, small, medium, large
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    # Variant specifications
    dimensions = Column(JSON)
    quality = Column(Integer)  # Quality percentage for images/videos
    format = Column(String(20))  # Format of the variant
    
    # Processing
    processing_status = Column(String(50), default=ProcessingStatus.PENDING)
    processed_at = Column(DateTime)
    
    # CDN
    cdn_url = Column(String(1000))
    
    # Relationships
    original_file = relationship("MediaFile", back_populates="variants")
    
    __table_args__ = (
        Index("idx_variant_original", "original_file_id"),
        Index("idx_variant_name", "variant_name"),
        Index("idx_variant_status", "processing_status"),
        UniqueConstraint("original_file_id", "variant_name", name="uq_file_variant"),
    )

class ProductMediaMapping(BaseTable):
    """Product-media relationship model"""
    __tablename__ = "product_media_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)  # References products table
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id"), nullable=False)
    
    # Display settings
    alt_text = Column(String(500))
    title = Column(String(500))
    caption = Column(Text)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    is_visible = Column(Boolean, default=True)
    
    # Usage context
    usage_context = Column(JSON)  # Where this media is used (gallery, thumbnail, etc.)
    
    # Relationships
    media_file = relationship("MediaFile", back_populates="product_media")
    
    __table_args__ = (
        Index("idx_product_media_product", "product_id"),
        Index("idx_product_media_file", "media_file_id"),
        Index("idx_product_media_primary", "is_primary"),
        Index("idx_product_media_order", "sort_order"),
    )

class MediaProcessingJob(BaseTable):
    """Media processing job queue model"""
    __tablename__ = "media_processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id"), nullable=False)
    job_type = Column(String(100), nullable=False)  # resize, transcode, thumbnail, etc.
    job_config = Column(JSON, nullable=False)
    
    # Job status
    status = Column(String(50), default=ProcessingStatus.PENDING)
    priority = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timing
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    result_data = Column(JSON)
    error_message = Column(Text)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(200))
    
    __table_args__ = (
        Index("idx_job_media_file", "media_file_id"),
        Index("idx_job_status", "status"),
        Index("idx_job_priority", "priority"),
        Index("idx_job_scheduled", "scheduled_at"),
    )

# ============================================================================
# Pydantic Schemas
# ============================================================================

class MediaUploadResponse(BaseModel):
    media_id: uuid.UUID
    filename: str
    file_size: int
    media_type: str
    mime_type: str
    processing_status: str
    cdn_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    variants: List[Dict[str, Any]] = []

class MediaFileResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    filename: str
    file_size: int
    mime_type: str
    media_type: str
    dimensions: Optional[Dict[str, Any]]
    duration: Optional[int]
    processing_status: str
    cdn_url: Optional[str]
    access_level: str
    created_at: datetime
    updated_at: datetime
    variants: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class ProductMediaRequest(BaseModel):
    media_file_id: uuid.UUID
    alt_text: Optional[str] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False
    usage_context: Optional[Dict[str, Any]] = None

class MediaSearchFilter(BaseModel):
    media_type: Optional[MediaType] = None
    mime_type: Optional[str] = None
    processing_status: Optional[ProcessingStatus] = None
    access_level: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    has_variants: Optional[bool] = None

class BulkMediaOperation(BaseModel):
    media_ids: List[uuid.UUID]
    operation: str  # delete, move, update_access, regenerate_variants
    parameters: Optional[Dict[str, Any]] = None

# ============================================================================
# Service Classes
# ============================================================================

class MediaStorageService:
    """Media storage service with multiple backend support"""
    
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
        self.settings = get_settings()
    
    async def get_storage_backend(self, storage_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get storage backend configuration"""
        if storage_id:
            query = select(MediaStorage).where(MediaStorage.id == storage_id)
        else:
            query = select(MediaStorage).where(
                and_(MediaStorage.is_default == True, MediaStorage.is_active == True)
            )
        
        result = await self.db.execute(query)
        storage = result.scalar_one_or_none()
        
        if not storage:
            # Return local storage as fallback
            return {
                "type": "local",
                "config": {"base_path": MEDIA_CONFIG["upload_path"]},
                "base_url": "/media"
            }
        
        return {
            "type": storage.storage_type,
            "config": storage.configuration,
            "base_url": storage.base_url
        }
    
    async def store_file(
        self, 
        file_content: bytes, 
        filename: str, 
        storage_backend: Dict[str, Any]
    ) -> str:
        """Store file using specified backend"""
        storage_type = storage_backend["type"]
        config = storage_backend["config"]
        
        if storage_type == "local":
            return await self._store_local(file_content, filename, config)
        elif storage_type == "s3":
            return await self._store_s3(file_content, filename, config)
        elif storage_type == "gcs":
            return await self._store_gcs(file_content, filename, config)
        elif storage_type == "azure":
            return await self._store_azure(file_content, filename, config)
        else:
            raise HTTPException(status_code=500, detail="Unsupported storage backend")
    
    async def _store_local(self, file_content: bytes, filename: str, config: Dict[str, Any]) -> str:
        """Store file locally"""
        base_path = Path(config["base_path"])
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Create year/month directory structure
        now = datetime.utcnow()
        dir_path = base_path / str(now.year) / f"{now.month:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)
        
        file_path = dir_path / filename
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        
        return str(file_path.relative_to(base_path))
    
    async def _store_s3(self, file_content: bytes, filename: str, config: Dict[str, Any]) -> str:
        """Store file in AWS S3"""
        import boto3
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config["access_key"],
            aws_secret_access_key=config["secret_key"],
            region_name=config.get("region", "us-east-1")
        )
        
        # Create year/month key structure
        now = datetime.utcnow()
        key = f"{now.year}/{now.month:02d}/{filename}"
        
        s3_client.put_object(
            Bucket=config["bucket"],
            Key=key,
            Body=file_content,
            ContentType=mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        
        return key
    
    async def _store_gcs(self, file_content: bytes, filename: str, config: Dict[str, Any]) -> str:
        """Store file in Google Cloud Storage"""
        from google.cloud import storage
        
        client = storage.Client.from_service_account_info(config["credentials"])
        bucket = client.bucket(config["bucket"])
        
        # Create year/month key structure
        now = datetime.utcnow()
        blob_name = f"{now.year}/{now.month:02d}/{filename}"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            file_content,
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        
        return blob_name
    
    async def _store_azure(self, file_content: bytes, filename: str, config: Dict[str, Any]) -> str:
        """Store file in Azure Blob Storage"""
        from azure.storage.blob import BlobServiceClient
        
        blob_service = BlobServiceClient(
            account_url=f"https://{config['account_name']}.blob.core.windows.net",
            credential=config["account_key"]
        )
        
        # Create year/month key structure
        now = datetime.utcnow()
        blob_name = f"{now.year}/{now.month:02d}/{filename}"
        
        blob_client = blob_service.get_blob_client(
            container=config["container"],
            blob=blob_name
        )
        
        blob_client.upload_blob(
            file_content,
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            overwrite=True
        )
        
        return blob_name

class MediaProcessingService:
    """Media processing service for images and videos"""
    
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
    
    async def process_image(self, media_file: MediaFile) -> Dict[str, Any]:
        """Process image file and create variants"""
        try:
            file_path = Path(MEDIA_CONFIG["upload_path"]) / media_file.file_path
            
            with Image.open(file_path) as img:
                # Extract metadata
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    metadata["exif"] = dict(img._getexif().items())
                
                # Update media file with dimensions and metadata
                media_file.dimensions = {"width": img.size[0], "height": img.size[1]}
                media_file.metadata = metadata
                
                # Create variants
                variants_created = []
                for size_name, dimensions in MEDIA_CONFIG["image_sizes"].items():
                    if size_name == "original":
                        continue
                    
                    variant = await self._create_image_variant(
                        media_file, img, size_name, dimensions
                    )
                    if variant:
                        variants_created.append(variant)
                
                # Update processing status
                media_file.processing_status = ProcessingStatus.COMPLETED
                media_file.processed_at = datetime.utcnow()
                
                await self.db.commit()
                
                return {
                    "status": "success",
                    "variants_created": len(variants_created),
                    "metadata": metadata
                }
                
        except Exception as e:
            media_file.processing_status = ProcessingStatus.FAILED
            media_file.processing_error = str(e)
            await self.db.commit()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_image_variant(
        self, 
        original_file: MediaFile, 
        img: Image.Image, 
        variant_name: str, 
        dimensions: tuple
    ) -> Optional[MediaVariant]:
        """Create image variant with specified dimensions"""
        try:
            # Calculate new dimensions maintaining aspect ratio
            resized_img = ImageOps.fit(img, dimensions, Image.Resampling.LANCZOS)
            
            # Generate variant filename
            original_path = Path(original_file.filename)
            variant_filename = f"{original_path.stem}_{variant_name}{original_path.suffix}"
            
            # Save variant
            variant_path = Path(MEDIA_CONFIG["upload_path"]) / "variants" / variant_filename
            variant_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Optimize for web
            save_kwargs = {"optimize": True}
            if resized_img.format == "JPEG":
                save_kwargs["quality"] = 85
                save_kwargs["progressive"] = True
            elif resized_img.format == "PNG":
                save_kwargs["compress_level"] = 6
            
            resized_img.save(variant_path, **save_kwargs)
            
            # Create variant record
            variant = MediaVariant(
                original_file_id=original_file.id,
                variant_name=variant_name,
                filename=variant_filename,
                file_path=str(variant_path.relative_to(Path(MEDIA_CONFIG["upload_path"]))),
                file_size=variant_path.stat().st_size,
                dimensions={"width": resized_img.size[0], "height": resized_img.size[1]},
                format=resized_img.format,
                processing_status=ProcessingStatus.COMPLETED,
                processed_at=datetime.utcnow()
            )
            
            self.db.add(variant)
            return variant
            
        except Exception as e:
            print(f"Error creating variant {variant_name}: {e}")
            return None
    
    async def process_video(self, media_file: MediaFile) -> Dict[str, Any]:
        """Process video file and create variants"""
        try:
            file_path = Path(MEDIA_CONFIG["upload_path"]) / media_file.file_path
            
            # Get video metadata using ffprobe
            probe = ffmpeg.probe(str(file_path))
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            metadata = {
                "duration": float(probe['format']['duration']),
                "bitrate": int(probe['format']['bit_rate']),
                "format_name": probe['format']['format_name'],
                "codec": video_info['codec_name'],
                "width": video_info['width'],
                "height": video_info['height'],
                "fps": eval(video_info['r_frame_rate'])
            }
            
            # Update media file
            media_file.dimensions = {"width": video_info['width'], "height": video_info['height']}
            media_file.duration = int(float(probe['format']['duration']))
            media_file.metadata = metadata
            
            # Create thumbnail
            await self._create_video_thumbnail(media_file, file_path)
            
            # Create video variants for different qualities
            variants_created = []
            for quality, settings in MEDIA_CONFIG["video_qualities"].items():
                variant = await self._create_video_variant(
                    media_file, file_path, quality, settings
                )
                if variant:
                    variants_created.append(variant)
            
            # Update processing status
            media_file.processing_status = ProcessingStatus.COMPLETED
            media_file.processed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "status": "success",
                "variants_created": len(variants_created),
                "metadata": metadata
            }
            
        except Exception as e:
            media_file.processing_status = ProcessingStatus.FAILED
            media_file.processing_error = str(e)
            await self.db.commit()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_video_thumbnail(self, media_file: MediaFile, video_path: Path):
        """Create video thumbnail"""
        try:
            thumbnail_filename = f"{Path(media_file.filename).stem}_thumbnail.jpg"
            thumbnail_path = Path(MEDIA_CONFIG["upload_path"]) / "thumbnails" / thumbnail_filename
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract frame at 10% of video duration
            (
                ffmpeg
                .input(str(video_path), ss=media_file.duration * 0.1 if media_file.duration else 1)
                .output(str(thumbnail_path), vframes=1, format='image2', vcodec='mjpeg')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Create thumbnail variant record
            thumbnail_variant = MediaVariant(
                original_file_id=media_file.id,
                variant_name="thumbnail",
                filename=thumbnail_filename,
                file_path=str(thumbnail_path.relative_to(Path(MEDIA_CONFIG["upload_path"]))),
                file_size=thumbnail_path.stat().st_size,
                format="JPEG",
                processing_status=ProcessingStatus.COMPLETED,
                processed_at=datetime.utcnow()
            )
            
            self.db.add(thumbnail_variant)
            
        except Exception as e:
            print(f"Error creating video thumbnail: {e}")
    
    async def _create_video_variant(
        self, 
        original_file: MediaFile, 
        video_path: Path, 
        quality: str, 
        settings: Dict[str, Any]
    ) -> Optional[MediaVariant]:
        """Create video variant with specified quality"""
        try:
            variant_filename = f"{Path(original_file.filename).stem}_{quality}.mp4"
            variant_path = Path(MEDIA_CONFIG["upload_path"]) / "variants" / variant_filename
            variant_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Transcode video
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(variant_path),
                    vcodec='h264',
                    acodec='aac',
                    vf=f'scale={settings["width"]}:-2',
                    video_bitrate=settings["bitrate"],
                    preset='medium',
                    crf=23
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Create variant record
            variant = MediaVariant(
                original_file_id=original_file.id,
                variant_name=quality,
                filename=variant_filename,
                file_path=str(variant_path.relative_to(Path(MEDIA_CONFIG["upload_path"]))),
                file_size=variant_path.stat().st_size,
                format="MP4",
                processing_status=ProcessingStatus.COMPLETED,
                processed_at=datetime.utcnow()
            )
            
            self.db.add(variant)
            return variant
            
        except Exception as e:
            print(f"Error creating video variant {quality}: {e}")
            return None

class MediaManagementService:
    """Comprehensive media management service"""
    
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
        self.storage_service = MediaStorageService(db, redis_client)
        self.processing_service = MediaProcessingService(db, redis_client)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        user_id: Optional[uuid.UUID] = None,
        access_level: str = "public"
    ) -> MediaUploadResponse:
        """Upload and process media file"""
        # Validate file
        await self._validate_upload(file)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Calculate file hash and checksum
        file_hash = hashlib.sha256(file_content).hexdigest()
        checksum = hashlib.md5(file_content).hexdigest()
        
        # Check for duplicate files
        existing_query = select(MediaFile).where(MediaFile.file_hash == file_hash)
        existing_result = await self.db.execute(existing_query)
        existing_file = existing_result.scalar_one_or_none()
        
        if existing_file:
            return MediaUploadResponse(
                media_id=existing_file.id,
                filename=existing_file.filename,
                file_size=existing_file.file_size,
                media_type=existing_file.media_type,
                mime_type=existing_file.mime_type,
                processing_status=existing_file.processing_status,
                cdn_url=existing_file.cdn_url
            )
        
        # Get storage backend
        storage_backend = await self.storage_service.get_storage_backend()
        
        # Store file
        file_path = await self.storage_service.store_file(
            file_content, unique_filename, storage_backend
        )
        
        # Determine media type
        media_type = self._determine_media_type(file.content_type)
        
        # Create media file record
        media_file = MediaFile(
            original_filename=file.filename,
            filename=unique_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            media_type=media_type,
            access_level=access_level,
            upload_user_id=user_id,
            file_hash=file_hash,
            checksum=checksum,
            processing_status=ProcessingStatus.PENDING
        )
        
        self.db.add(media_file)
        await self.db.commit()
        await self.db.refresh(media_file)
        
        # Queue processing job
        await self._queue_processing_job(media_file)
        
        return MediaUploadResponse(
            media_id=media_file.id,
            filename=media_file.filename,
            file_size=media_file.file_size,
            media_type=media_file.media_type,
            mime_type=media_file.mime_type,
            processing_status=media_file.processing_status
        )
    
    async def _validate_upload(self, file: UploadFile):
        """Validate uploaded file"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > MEDIA_CONFIG["max_file_size"]:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Reset file position
        await file.seek(0)
        
        # Check content type
        allowed_types = (
            MEDIA_CONFIG["allowed_image_types"] +
            MEDIA_CONFIG["allowed_video_types"] +
            MEDIA_CONFIG["allowed_document_types"]
        )
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="File type not supported")
    
    def _determine_media_type(self, mime_type: str) -> str:
        """Determine media type from MIME type"""
        if mime_type.startswith("image/"):
            return MediaType.IMAGE
        elif mime_type.startswith("video/"):
            return MediaType.VIDEO
        elif mime_type.startswith("audio/"):
            return MediaType.AUDIO
        elif mime_type in ["application/pdf", "text/plain", "application/msword"]:
            return MediaType.DOCUMENT
        else:
            return MediaType.DOCUMENT
    
    async def _queue_processing_job(self, media_file: MediaFile):
        """Queue media processing job"""
        job_config = {
            "media_type": media_file.media_type,
            "create_variants": True,
            "extract_metadata": True
        }
        
        processing_job = MediaProcessingJob(
            media_file_id=media_file.id,
            job_type="process_media",
            job_config=job_config,
            priority=1 if media_file.media_type == MediaType.IMAGE else 0
        )
        
        self.db.add(processing_job)
        await self.db.commit()
        
        # Add to Redis queue for background processing
        await self.redis.lpush(
            "media_processing_queue",
            json.dumps({
                "job_id": str(processing_job.id),
                "media_file_id": str(media_file.id),
                "job_type": processing_job.job_type,
                "priority": processing_job.priority
            })
        )
    
    async def process_media_file(self, media_file_id: uuid.UUID) -> Dict[str, Any]:
        """Process media file (called by background worker)"""
        # Get media file
        query = select(MediaFile).where(MediaFile.id == media_file_id)
        result = await self.db.execute(query)
        media_file = result.scalar_one_or_none()
        
        if not media_file:
            return {"status": "error", "error": "Media file not found"}
        
        # Update status to processing
        media_file.processing_status = ProcessingStatus.PROCESSING
        await self.db.commit()
        
        # Process based on media type
        if media_file.media_type == MediaType.IMAGE:
            return await self.processing_service.process_image(media_file)
        elif media_file.media_type == MediaType.VIDEO:
            return await self.processing_service.process_video(media_file)
        else:
            # For other types, just mark as completed
            media_file.processing_status = ProcessingStatus.COMPLETED
            media_file.processed_at = datetime.utcnow()
            await self.db.commit()
            
            return {"status": "success", "message": "No processing required"}
    
    async def search_media(
        self,
        filters: MediaSearchFilter,
        page: int = 1,
        size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Search media files with filters"""
        query = select(MediaFile).options(selectinload(MediaFile.variants))
        count_query = select(func.count(MediaFile.id))
        
        # Apply filters
        if filters.media_type:
            query = query.where(MediaFile.media_type == filters.media_type)
            count_query = count_query.where(MediaFile.media_type == filters.media_type)
        
        if filters.mime_type:
            query = query.where(MediaFile.mime_type == filters.mime_type)
            count_query = count_query.where(MediaFile.mime_type == filters.mime_type)
        
        if filters.processing_status:
            query = query.where(MediaFile.processing_status == filters.processing_status)
            count_query = count_query.where(MediaFile.processing_status == filters.processing_status)
        
        if filters.access_level:
            query = query.where(MediaFile.access_level == filters.access_level)
            count_query = count_query.where(MediaFile.access_level == filters.access_level)
        
        if filters.date_from:
            query = query.where(MediaFile.created_at >= filters.date_from)
            count_query = count_query.where(MediaFile.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.where(MediaFile.created_at <= filters.date_to)
            count_query = count_query.where(MediaFile.created_at <= filters.date_to)
        
        if filters.min_size:
            query = query.where(MediaFile.file_size >= filters.min_size)
            count_query = count_query.where(MediaFile.file_size >= filters.min_size)
        
        if filters.max_size:
            query = query.where(MediaFile.file_size <= filters.max_size)
            count_query = count_query.where(MediaFile.file_size <= filters.max_size)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(MediaFile, sort_by, MediaFile.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        media_files = result.scalars().all()
        
        # Convert to response format
        media_responses = []
        for media_file in media_files:
            variants = []
            for variant in media_file.variants:
                variants.append({
                    "name": variant.variant_name,
                    "url": f"/media/{variant.file_path}",
                    "size": variant.file_size,
                    "dimensions": variant.dimensions
                })
            
            media_dict = {
                **media_file.__dict__,
                "variants": variants
            }
            media_responses.append(media_dict)
        
        return {
            "media_files": media_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    async def associate_media_with_product(
        self,
        product_id: uuid.UUID,
        media_requests: List[ProductMediaRequest]
    ) -> Dict[str, Any]:
        """Associate media files with product"""
        associations_created = []
        
        for request in media_requests:
            # Check if media file exists
            media_query = select(MediaFile).where(MediaFile.id == request.media_file_id)
            media_result = await self.db.execute(media_query)
            media_file = media_result.scalar_one_or_none()
            
            if not media_file:
                continue
            
            # Check if association already exists
            existing_query = select(ProductMediaMapping).where(
                and_(
                    ProductMediaMapping.product_id == product_id,
                    ProductMediaMapping.media_file_id == request.media_file_id
                )
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                continue
            
            # Create association
            association = ProductMediaMapping(
                product_id=product_id,
                media_file_id=request.media_file_id,
                alt_text=request.alt_text,
                title=request.title,
                caption=request.caption,
                sort_order=request.sort_order,
                is_primary=request.is_primary,
                usage_context=request.usage_context
            )
            
            self.db.add(association)
            associations_created.append(association)
        
        await self.db.commit()
        
        return {
            "associations_created": len(associations_created),
            "product_id": product_id
        }

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/media", tags=["Product Media v66"])

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    access_level: str = Form(default="public"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload media file"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = MediaManagementService(db, redis_client)
    
    user_id = current_user.get("id") if current_user else None
    return await service.upload_file(file, user_id, access_level)

@router.get("/search", response_model=Dict[str, Any])
async def search_media(
    media_type: Optional[MediaType] = Query(None),
    processing_status: Optional[ProcessingStatus] = Query(None),
    access_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Search media files"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = MediaManagementService(db, redis_client)
    
    filters = MediaSearchFilter(
        media_type=media_type,
        processing_status=processing_status,
        access_level=access_level
    )
    
    return await service.search_media(filters, page, size, sort_by, sort_order)

@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get media file details"""
    query = select(MediaFile).options(selectinload(MediaFile.variants)).where(
        MediaFile.id == media_id
    )
    result = await db.execute(query)
    media_file = result.scalar_one_or_none()
    
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    return media_file

@router.post("/products/{product_id}/associate", response_model=Dict[str, Any])
async def associate_product_media(
    product_id: uuid.UUID,
    media_requests: List[ProductMediaRequest],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Associate media with product"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = MediaManagementService(db, redis_client)
    
    return await service.associate_media_with_product(product_id, media_requests)

@router.get("/serve/{file_path:path}")
async def serve_media(file_path: str):
    """Serve media file"""
    full_path = Path(MEDIA_CONFIG["upload_path"]) / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        full_path,
        media_type=mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    )

@router.post("/process/{media_id}", response_model=Dict[str, Any])
async def process_media(
    media_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Trigger media processing"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = MediaManagementService(db, redis_client)
    
    # Add to background tasks
    background_tasks.add_task(service.process_media_file, media_id)
    
    return {
        "media_id": media_id,
        "status": "processing_queued",
        "message": "Media processing has been queued"
    }

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Media service health check"""
    return {
        "status": "healthy",
        "service": "product_media_v66",
        "version": "66.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "file_upload",
            "image_processing",
            "video_processing",
            "variant_generation",
            "cdn_integration",
            "bulk_operations",
            "metadata_extraction"
        ]
    }