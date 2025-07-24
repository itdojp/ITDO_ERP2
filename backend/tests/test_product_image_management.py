"""
Comprehensive TDD Tests for Product Image Management API - CC02 v48.0
Testing file upload, image processing, metadata management, and gallery features
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import uuid
import io
from datetime import datetime
from PIL import Image
import tempfile
import os

# Import the main app
from app.main_super_minimal import app

client = TestClient(app)

class TestProductImageManagementAPI:
    """Comprehensive test suite for Product Image Management API"""

    def setup_method(self):
        """Setup test data before each test"""
        # Clear any existing test data
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass
        
        # Create a test product
        self.test_product = {
            "code": "IMG001",
            "name": "Image Test Product",
            "description": "Product for image testing",
            "price": 199.99,
            "category": "Electronics"
        }
        
        response = client.post("/api/v1/products/", json=self.test_product)
        self.product_id = response.json()["id"]
        
        # Create test image data
        self.test_image_data = self.create_test_image()

    def create_test_image(self) -> bytes:
        """Create a test image in memory"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def create_test_image_file(self, filename: str = "test.jpg") -> io.BytesIO:
        """Create a test image file-like object"""
        return io.BytesIO(self.test_image_data)

    def test_upload_product_image_success(self):
        """Test successful image upload"""
        image_file = self.create_test_image_file()
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")},
            data={"alt_text": "Test image", "is_primary": "true"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "image" in data
        assert "message" in data
        assert data["image"]["product_id"] == self.product_id
        assert data["image"]["alt_text"] == "Test image"
        assert data["image"]["is_primary"] == True
        assert data["image"]["mime_type"] == "image/jpeg"
        assert data["image"]["file_size"] > 0
        assert "url" in data["image"]
        assert "thumbnail_url" in data["image"]

    def test_upload_product_image_invalid_product(self):
        """Test image upload for non-existent product"""
        fake_id = str(uuid.uuid4())
        image_file = self.create_test_image_file()
        
        response = client.post(
            f"/api/v1/products/{fake_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_upload_product_image_invalid_file_type(self):
        """Test image upload with invalid file type"""
        # Create a text file instead of image
        text_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_product_image_too_large(self):
        """Test image upload with file too large"""
        # Create a large test image (simulate > 10MB)
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = io.BytesIO(large_data)
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("large_image.jpg", large_file, "image/jpeg")}
        )
        
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    def test_bulk_upload_product_images(self):
        """Test bulk image upload"""
        # Create multiple test images
        image1 = self.create_test_image_file("image1.jpg")
        image2 = self.create_test_image_file("image2.jpg")
        image3 = self.create_test_image_file("image3.jpg")
        
        files = [
            ("files", ("image1.jpg", image1, "image/jpeg")),
            ("files", ("image2.jpg", image2, "image/jpeg")),
            ("files", ("image3.jpg", image3, "image/jpeg"))
        ]
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/bulk-upload",
            files=files,
            data={"alt_texts": "First image, Second image, Third image"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_processed"] == 3
        assert len(data["successful_uploads"]) == 3
        assert len(data["failed_uploads"]) == 0
        
        # Check that first image is set as primary
        assert data["successful_uploads"][0]["is_primary"] == True
        assert data["successful_uploads"][1]["is_primary"] == False

    def test_bulk_upload_too_many_files(self):
        """Test bulk upload with too many files"""
        # Create 11 files (exceeds limit of 10)
        files = []
        for i in range(11):
            image_file = self.create_test_image_file(f"image{i}.jpg")
            files.append(("files", (f"image{i}.jpg", image_file, "image/jpeg")))
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/bulk-upload",
            files=files
        )
        
        assert response.status_code == 400
        assert "Maximum 10 files" in response.json()["detail"]

    def test_get_product_images(self):
        """Test retrieving product images"""
        # First upload some images
        image_file = self.create_test_image_file()
        client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")},
            data={"alt_text": "Test image"}
        )
        
        response = client.get(f"/api/v1/products/{self.product_id}/images")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["product_id"] == self.product_id
        assert "id" in data[0]
        assert "url" in data[0]

    def test_get_product_images_empty(self):
        """Test retrieving images for product with no images"""
        response = client.get(f"/api/v1/products/{self.product_id}/images")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_specific_product_image(self):
        """Test retrieving specific image metadata"""
        # Upload an image first
        image_file = self.create_test_image_file()
        upload_response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")},
            data={"alt_text": "Specific test image"}
        )
        
        image_id = upload_response.json()["image"]["id"]
        
        response = client.get(f"/api/v1/products/{self.product_id}/images/{image_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == image_id
        assert data["product_id"] == self.product_id
        assert data["alt_text"] == "Specific test image"

    def test_get_nonexistent_image(self):
        """Test retrieving non-existent image"""
        fake_image_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/products/{self.product_id}/images/{fake_image_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_product_image_metadata(self):
        """Test updating image metadata"""
        # Upload an image first
        image_file = self.create_test_image_file()
        upload_response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")},
            data={"alt_text": "Original alt text"}
        )
        
        image_id = upload_response.json()["image"]["id"]
        
        # Update metadata
        response = client.put(
            f"/api/v1/products/{self.product_id}/images/{image_id}",
            data={
                "alt_text": "Updated alt text",
                "display_order": "5",
                "is_primary": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["alt_text"] == "Updated alt text"
        assert data["display_order"] == 5
        assert data["is_primary"] == True

    def test_delete_product_image(self):
        """Test deleting a product image"""
        # Upload an image first
        image_file = self.create_test_image_file()
        upload_response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("test_image.jpg", image_file, "image/jpeg")}
        )
        
        image_id = upload_response.json()["image"]["id"]
        
        # Delete the image
        response = client.delete(f"/api/v1/products/{self.product_id}/images/{image_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "deleted successfully" in data["message"]
        assert data["image_id"] == image_id
        
        # Verify image is deleted
        get_response = client.get(f"/api/v1/products/{self.product_id}/images/{image_id}")
        assert get_response.status_code == 404

    def test_set_primary_image(self):
        """Test setting an image as primary"""
        # Upload two images
        image1 = self.create_test_image_file("image1.jpg")
        image2 = self.create_test_image_file("image2.jpg")
        
        upload1 = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("image1.jpg", image1, "image/jpeg")},
            data={"is_primary": "true"}
        )
        
        upload2 = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("image2.jpg", image2, "image/jpeg")}
        )
        
        image2_id = upload2.json()["image"]["id"]
        
        # Set second image as primary
        response = client.post(f"/api/v1/products/{self.product_id}/images/{image2_id}/set-primary")
        assert response.status_code == 200
        
        # Verify primary status
        images_response = client.get(f"/api/v1/products/{self.product_id}/images")
        images = images_response.json()
        
        primary_images = [img for img in images if img["is_primary"]]
        assert len(primary_images) == 1
        assert primary_images[0]["id"] == image2_id

    def test_get_primary_image(self):
        """Test getting primary image"""
        # Upload an image
        image_file = self.create_test_image_file()
        upload_response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("primary_image.jpg", image_file, "image/jpeg")},
            data={"is_primary": "true"}
        )
        
        response = client.get(f"/api/v1/products/{self.product_id}/images/primary")
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_primary"] == True
        assert data["product_id"] == self.product_id

    def test_get_primary_image_no_images(self):
        """Test getting primary image when no images exist"""
        response = client.get(f"/api/v1/products/{self.product_id}/images/primary")
        assert response.status_code == 404
        assert "No images found" in response.json()["detail"]

    def test_get_product_image_gallery(self):
        """Test getting organized gallery data"""
        # Upload multiple images with different display orders
        images_data = [
            {"file": "image1.jpg", "display_order": 2, "alt": "Second image"},
            {"file": "image2.jpg", "display_order": 1, "alt": "First image"},
            {"file": "image3.jpg", "display_order": 3, "alt": "Third image", "primary": True}
        ]
        
        for img_data in images_data:
            image_file = self.create_test_image_file(img_data["file"])
            data = {
                "display_order": str(img_data["display_order"]),
                "alt_text": img_data["alt"]
            }
            if img_data.get("primary"):
                data["is_primary"] = "true"
                
            client.post(
                f"/api/v1/products/{self.product_id}/images/upload",
                files={"file": (img_data["file"], image_file, "image/jpeg")},
                data=data
            )
        
        response = client.get(f"/api/v1/products/{self.product_id}/images/gallery")
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == self.product_id
        assert data["total_images"] == 3
        assert "primary_image" in data
        assert data["primary_image"]["alt_text"] == "Third image"
        assert len(data["all_images"]) == 3
        assert len(data["thumbnail_urls"]) == 3
        assert len(data["full_size_urls"]) == 3
        
        # Check that images are sorted by display order
        assert data["all_images"][0]["display_order"] == 1
        assert data["all_images"][1]["display_order"] == 2
        assert data["all_images"][2]["display_order"] == 3

    def test_image_statistics(self):
        """Test image storage statistics"""
        # Upload some images
        image_file1 = self.create_test_image_file()
        image_file2 = self.create_test_image_file()
        
        client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("stat_image1.jpg", image_file1, "image/jpeg")}
        )
        client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("stat_image2.jpg", image_file2, "image/jpeg")}
        )
        
        response = client.get("/api/v1/products/images/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_images" in data
        assert "products_with_images" in data
        assert "total_storage_bytes" in data
        assert "total_storage_mb" in data
        assert "average_images_per_product" in data
        
        assert data["total_images"] >= 2
        assert data["products_with_images"] >= 1
        assert data["total_storage_bytes"] > 0

    def test_cleanup_orphaned_images(self):
        """Test cleanup of orphaned image files"""
        # This endpoint is for admin use
        response = client.delete("/api/v1/products/images/cleanup-orphaned")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "orphaned_files_found" in data
        assert "files_deleted" in data
        assert isinstance(data["orphaned_files_found"], int)
        assert isinstance(data["files_deleted"], int)

    def test_image_file_serving(self):
        """Test serving image files"""
        # Note: This test may not work in the test environment without actual file system
        # but we can test the endpoint structure
        response = client.get("/api/v1/products/images/file/nonexistent.jpg")
        assert response.status_code == 404

    def test_thumbnail_file_serving(self):
        """Test serving thumbnail files"""
        # Note: This test may not work in the test environment without actual file system
        # but we can test the endpoint structure
        response = client.get("/api/v1/products/images/thumbnail/nonexistent.jpg")
        assert response.status_code == 404

    def test_multiple_primary_images_handling(self):
        """Test that only one primary image is maintained"""
        # Upload first image as primary
        image1 = self.create_test_image_file("primary1.jpg")
        upload1 = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("primary1.jpg", image1, "image/jpeg")},
            data={"is_primary": "true"}
        )
        
        # Upload second image as primary
        image2 = self.create_test_image_file("primary2.jpg")
        upload2 = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("primary2.jpg", image2, "image/jpeg")},
            data={"is_primary": "true"}
        )
        
        # Check that only one primary exists
        images_response = client.get(f"/api/v1/products/{self.product_id}/images")
        images = images_response.json()
        
        primary_count = sum(1 for img in images if img["is_primary"])
        assert primary_count == 1

    def test_image_dimensions_extraction(self):
        """Test that image dimensions are properly extracted"""
        # Create an image with specific dimensions
        test_img = Image.new('RGB', (200, 150), color='blue')
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("dimension_test.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["image"]["width"] == 200
        assert data["image"]["height"] == 150

    def test_image_metadata_timestamps(self):
        """Test that image metadata includes proper timestamps"""
        image_file = self.create_test_image_file()
        
        before_upload = datetime.now()
        response = client.post(
            f"/api/v1/products/{self.product_id}/images/upload",
            files={"file": ("timestamp_test.jpg", image_file, "image/jpeg")}
        )
        after_upload = datetime.now()
        
        assert response.status_code == 200
        data = response.json()
        
        created_at = datetime.fromisoformat(data["image"]["created_at"])
        updated_at = datetime.fromisoformat(data["image"]["updated_at"])
        
        assert before_upload <= created_at <= after_upload
        assert before_upload <= updated_at <= after_upload

    def teardown_method(self):
        """Clean up after each test"""
        try:
            client.delete("/api/v1/products/test/clear-all")
        except:
            pass