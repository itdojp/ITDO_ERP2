"""
Product Image Management API - CC02 v48.0
File upload, image processing, and media management for products
TDD implementation with comprehensive validation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import uuid
import os
import shutil
from pathlib import Path
import mimetypes
from PIL import Image
import io
import base64
from datetime import datetime

# Import product stores
from app.api.v1.simple_products import products_store
from app.api.v1.advanced_product_management import advanced_products_store

router = APIRouter(prefix="/products", tags=["Product Image Management"])

# Configuration
UPLOAD_DIR = Path("uploads/products")
THUMBNAIL_DIR = Path("uploads/products/thumbnails")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
THUMBNAIL_SIZE = (300, 300)

# Ensure upload directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# Models
class ProductImage(BaseModel):
    """Product image metadata model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Product ID")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="Image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")
    display_order: int = Field(default=0, description="Display order")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    is_primary: bool = Field(default=False, description="Primary product image flag")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ImageUploadResponse(BaseModel):
    """Response model for image upload"""
    image: ProductImage
    message: str

class BulkImageUploadResponse(BaseModel):
    """Response model for bulk image upload"""
    successful_uploads: List[ProductImage]
    failed_uploads: List[Dict[str, str]]
    total_processed: int

# In-memory storage for image metadata
product_images_store: Dict[str, List[ProductImage]] = {}

# Helper functions
def validate_file_type(file: UploadFile) -> bool:
    """Validate file type by extension and MIME type"""
    if not file.filename:
        return False
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check MIME type
    if file.content_type and not file.content_type.startswith('image/'):
        return False
    
    return True

def validate_file_size(file: UploadFile) -> bool:
    """Validate file size"""
    if hasattr(file, 'size') and file.size:
        return file.size <= MAX_FILE_SIZE
    return True  # Will be checked during upload

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension"""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"

def create_thumbnail(image_path: Path, thumbnail_path: Path) -> tuple[int, int]:
    """Create thumbnail and return dimensions of original image"""
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            
            # Create thumbnail
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, optimize=True, quality=85)
            
            return original_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

def get_product_from_stores(product_id: str) -> Optional[Dict[str, Any]]:
    """Get product from either store"""
    if product_id in advanced_products_store:
        return advanced_products_store[product_id]
    elif product_id in products_store:
        return products_store[product_id]
    return None

def update_product_image_urls(product_id: str, image_urls: List[str], thumbnail_url: Optional[str] = None):
    """Update product image URLs in product stores"""
    if product_id in advanced_products_store:
        advanced_products_store[product_id]["image_urls"] = image_urls
        if thumbnail_url:
            advanced_products_store[product_id]["thumbnail_url"] = thumbnail_url
        advanced_products_store[product_id]["updated_at"] = datetime.now()
    elif product_id in products_store:
        # Legacy products don't have image_urls field, could extend if needed
        pass

# API Endpoints

@router.post("/{product_id}/images/upload", response_model=ImageUploadResponse)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    display_order: int = Form(0),
    is_primary: bool = Form(False)
) -> ImageUploadResponse:
    """Upload a single image for a product"""
    
    # Validate product exists
    product = get_product_from_stores(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate file
    if not validate_file_type(file):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file_size} bytes exceeds maximum {MAX_FILE_SIZE} bytes"
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename or "image.jpg")
        file_path = UPLOAD_DIR / unique_filename
        thumbnail_filename = f"thumb_{unique_filename}"
        thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
        
        # Save original file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create thumbnail and get dimensions
        try:
            original_size = create_thumbnail(file_path, thumbnail_path)
            width, height = original_size
        except Exception as e:
            # Clean up original file if thumbnail creation fails
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
        
        # Create image metadata
        image = ProductImage(
            product_id=product_id,
            filename=file.filename or "unknown",
            url=f"/uploads/products/{unique_filename}",
            thumbnail_url=f"/uploads/products/thumbnails/{thumbnail_filename}",
            alt_text=alt_text,
            display_order=display_order,
            file_size=file_size,
            mime_type=file.content_type or mimetypes.guess_type(unique_filename)[0] or "image/jpeg",
            width=width,
            height=height,
            is_primary=is_primary
        )
        
        # Store image metadata
        if product_id not in product_images_store:
            product_images_store[product_id] = []
        
        # If setting as primary, unset other primary images
        if is_primary:
            for existing_image in product_images_store[product_id]:
                existing_image.is_primary = False
        
        product_images_store[product_id].append(image)
        
        # Update product image URLs
        image_urls = [img.url for img in product_images_store[product_id]]
        primary_image = next((img for img in product_images_store[product_id] if img.is_primary), None)
        thumbnail_url = primary_image.thumbnail_url if primary_image else image.thumbnail_url
        
        update_product_image_urls(product_id, image_urls, thumbnail_url)
        
        return ImageUploadResponse(
            image=image,
            message="Image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await file.close()

@router.post("/{product_id}/images/bulk-upload", response_model=BulkImageUploadResponse)
async def bulk_upload_product_images(
    product_id: str,
    files: List[UploadFile] = File(...),
    alt_texts: Optional[str] = Form(None),  # Comma-separated alt texts
) -> BulkImageUploadResponse:
    """Upload multiple images for a product"""
    
    # Validate product exists
    product = get_product_from_stores(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per bulk upload")
    
    # Parse alt texts
    alt_text_list = []
    if alt_texts:
        alt_text_list = [text.strip() for text in alt_texts.split(',')]
    
    successful_uploads = []
    failed_uploads = []
    
    for i, file in enumerate(files):
        try:
            alt_text = alt_text_list[i] if i < len(alt_text_list) else None
            
            # Use the single upload logic
            response = await upload_product_image(
                product_id=product_id,
                file=file,
                alt_text=alt_text,
                display_order=i,
                is_primary=(i == 0 and len(product_images_store.get(product_id, [])) == 0)
            )
            successful_uploads.append(response.image)
            
        except HTTPException as e:
            failed_uploads.append({
                "filename": file.filename or f"file_{i}",
                "error": str(e.detail)
            })
        except Exception as e:
            failed_uploads.append({
                "filename": file.filename or f"file_{i}",
                "error": str(e)
            })
    
    return BulkImageUploadResponse(
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        total_processed=len(files)
    )

@router.get("/{product_id}/images", response_model=List[ProductImage])
async def get_product_images(product_id: str) -> List[ProductImage]:
    """Get all images for a product"""
    
    # Validate product exists
    product = get_product_from_stores(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product_images_store.get(product_id, [])

@router.get("/{product_id}/images/{image_id}", response_model=ProductImage)
async def get_product_image(product_id: str, image_id: str) -> ProductImage:
    """Get specific image metadata"""
    
    images = product_images_store.get(product_id, [])
    image = next((img for img in images if img.id == image_id), None)
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return image

@router.put("/{product_id}/images/{image_id}", response_model=ProductImage)
async def update_product_image(
    product_id: str,
    image_id: str,
    alt_text: Optional[str] = Form(None),
    display_order: Optional[int] = Form(None),
    is_primary: Optional[bool] = Form(None)
) -> ProductImage:
    """Update image metadata"""
    
    images = product_images_store.get(product_id, [])
    image = next((img for img in images if img.id == image_id), None)
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Update fields
    if alt_text is not None:
        image.alt_text = alt_text
    if display_order is not None:
        image.display_order = display_order
    if is_primary is not None:
        if is_primary:
            # Unset other primary images
            for other_image in images:
                if other_image.id != image_id:
                    other_image.is_primary = False
        image.is_primary = is_primary
    
    image.updated_at = datetime.now()
    
    # Update product thumbnail if this became primary
    if image.is_primary:
        update_product_image_urls(
            product_id, 
            [img.url for img in images],
            image.thumbnail_url
        )
    
    return image

@router.delete("/{product_id}/images/{image_id}")
async def delete_product_image(product_id: str, image_id: str) -> Dict[str, str]:
    """Delete a product image"""
    
    images = product_images_store.get(product_id, [])
    image = next((img for img in images if img.id == image_id), None)
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Remove files from filesystem
    try:
        file_path = UPLOAD_DIR / Path(image.url).name
        thumbnail_path = THUMBNAIL_DIR / Path(image.thumbnail_url).name if image.thumbnail_url else None
        
        file_path.unlink(missing_ok=True)
        if thumbnail_path:
            thumbnail_path.unlink(missing_ok=True)
    except Exception as e:
        # Log error but don't fail the deletion
        pass
    
    # Remove from store
    product_images_store[product_id] = [img for img in images if img.id != image_id]
    
    # Update product image URLs
    remaining_images = product_images_store[product_id]
    image_urls = [img.url for img in remaining_images]
    primary_image = next((img for img in remaining_images if img.is_primary), None)
    thumbnail_url = primary_image.thumbnail_url if primary_image else (remaining_images[0].thumbnail_url if remaining_images else None)
    
    update_product_image_urls(product_id, image_urls, thumbnail_url)
    
    return {"message": "Image deleted successfully", "image_id": image_id}

@router.post("/{product_id}/images/{image_id}/set-primary")
async def set_primary_image(product_id: str, image_id: str) -> Dict[str, str]:
    """Set an image as the primary product image"""
    
    images = product_images_store.get(product_id, [])
    image = next((img for img in images if img.id == image_id), None)
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Unset all primary flags
    for img in images:
        img.is_primary = False
    
    # Set this image as primary
    image.is_primary = True
    image.updated_at = datetime.now()
    
    # Update product thumbnail
    update_product_image_urls(
        product_id,
        [img.url for img in images],
        image.thumbnail_url
    )
    
    return {"message": "Primary image set successfully", "image_id": image_id}

@router.get("/{product_id}/images/primary", response_model=ProductImage)
async def get_primary_image(product_id: str) -> ProductImage:
    """Get the primary image for a product"""
    
    images = product_images_store.get(product_id, [])
    primary_image = next((img for img in images if img.is_primary), None)
    
    if not primary_image and images:
        # If no primary set, return first image
        primary_image = images[0]
    
    if not primary_image:
        raise HTTPException(status_code=404, detail="No images found for product")
    
    return primary_image

# File serving endpoints
@router.get("/images/file/{filename}")
async def serve_image_file(filename: str):
    """Serve image files"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=file_path,
        media_type=mimetypes.guess_type(filename)[0] or "image/jpeg",
        filename=filename
    )

@router.get("/images/thumbnail/{filename}")
async def serve_thumbnail_file(filename: str):
    """Serve thumbnail files"""
    file_path = THUMBNAIL_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        path=file_path,
        media_type=mimetypes.guess_type(filename)[0] or "image/jpeg",
        filename=filename
    )

@router.get("/{product_id}/images/gallery")
async def get_product_image_gallery(product_id: str) -> Dict[str, Any]:
    """Get organized product image gallery data"""
    
    # Validate product exists
    product = get_product_from_stores(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    images = product_images_store.get(product_id, [])
    
    # Sort images by display order
    sorted_images = sorted(images, key=lambda x: x.display_order)
    
    # Find primary image
    primary_image = next((img for img in sorted_images if img.is_primary), None)
    if not primary_image and sorted_images:
        primary_image = sorted_images[0]
    
    return {
        "product_id": product_id,
        "product_name": product.get("name", "Unknown"),
        "total_images": len(sorted_images),
        "primary_image": primary_image.dict() if primary_image else None,
        "all_images": [img.dict() for img in sorted_images],
        "thumbnail_urls": [img.thumbnail_url for img in sorted_images if img.thumbnail_url],
        "full_size_urls": [img.url for img in sorted_images]
    }

# Admin/utility endpoints
@router.delete("/images/cleanup-orphaned")
async def cleanup_orphaned_images() -> Dict[str, Any]:
    """Clean up orphaned image files (admin endpoint)"""
    
    # Get all image files in storage
    all_files = set()
    if UPLOAD_DIR.exists():
        all_files.update(f.name for f in UPLOAD_DIR.iterdir() if f.is_file())
    
    all_thumbnails = set()
    if THUMBNAIL_DIR.exists():
        all_thumbnails.update(f.name for f in THUMBNAIL_DIR.iterdir() if f.is_file())
    
    # Get all referenced files
    referenced_files = set()
    referenced_thumbnails = set()
    
    for images in product_images_store.values():
        for image in images:
            referenced_files.add(Path(image.url).name)
            if image.thumbnail_url:
                referenced_thumbnails.add(Path(image.thumbnail_url).name)
    
    # Find orphaned files
    orphaned_files = all_files - referenced_files
    orphaned_thumbnails = all_thumbnails - referenced_thumbnails
    
    # Delete orphaned files
    deleted_count = 0
    for filename in orphaned_files:
        try:
            (UPLOAD_DIR / filename).unlink()
            deleted_count += 1
        except:
            pass
    
    for filename in orphaned_thumbnails:
        try:
            (THUMBNAIL_DIR / filename).unlink()
            deleted_count += 1
        except:
            pass
    
    return {
        "message": "Cleanup completed",
        "orphaned_files_found": len(orphaned_files) + len(orphaned_thumbnails),
        "files_deleted": deleted_count
    }

@router.get("/images/stats")
async def get_image_statistics() -> Dict[str, Any]:
    """Get image storage statistics"""
    
    total_images = sum(len(images) for images in product_images_store.values())
    products_with_images = len([p for p in product_images_store.keys() if product_images_store[p]])
    
    # Calculate storage usage
    total_size = 0
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    
    if THUMBNAIL_DIR.exists():
        for file_path in THUMBNAIL_DIR.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    
    return {
        "total_images": total_images,
        "products_with_images": products_with_images,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / (1024 * 1024), 2),
        "average_images_per_product": round(total_images / max(products_with_images, 1), 2)
    }