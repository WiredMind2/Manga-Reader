import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

from app.models import User, Manga, Chapter, Page


@pytest.mark.images
@pytest.mark.asyncio
class TestImageEndpoints:
    """Test image serving and optimization endpoints."""
    
    async def test_get_page_image_success(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test serving a page image successfully."""
        # Get a page from the test data
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        # Mock image file existence and PIL Image
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            # Create a fake optimized image path
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()  # Create the file
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{page.id}")
                
                # Should return the image file
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("image/")
            finally:
                # Cleanup
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_get_page_image_not_found(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test getting non-existent page image."""
        response = await authenticated_client.get("/api/images/99999")
        
        assert response.status_code == 404
        assert "Page not found" in response.json()["detail"]
    
    async def test_get_page_image_file_not_found(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test getting page image when file doesn't exist on disk."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        # Mock file not existing
        with patch('os.path.exists', return_value=False):
            response = await authenticated_client.get(f"/api/images/{page.id}")
            
            assert response.status_code == 404
            assert "Image file not found" in response.json()["detail"]
    
    async def test_get_page_image_with_optimization(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test serving page image with size optimization."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(
                    f"/api/images/{page.id}?width=800&height=600&quality=90"
                )
                
                assert response.status_code == 200
                # Verify optimization was called with correct parameters
                mock_optimize.assert_called_once()
                args, kwargs = mock_optimize.call_args
                assert kwargs.get('width') == 800 or args[1] == 800
                assert kwargs.get('height') == 600 or args[2] == 600
                assert kwargs.get('quality') == 90 or args[3] == 90
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_get_page_image_invalid_parameters(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test getting page image with invalid parameters."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        # Test negative dimensions
        response = await authenticated_client.get(f"/api/images/{page.id}?width=-100")
        assert response.status_code == 422
        
        # Test invalid quality
        response = await authenticated_client.get(f"/api/images/{page.id}?quality=150")
        assert response.status_code == 422
    
    async def test_get_cover_image_success(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test serving manga cover image."""
        # Update manga to have cover image
        test_manga.cover_image = "/path/to/cover.jpg"
        await test_db.commit()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/cover/{test_manga.id}")
                
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("image/")
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_get_cover_image_no_cover(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga
    ):
        """Test getting cover image when manga has no cover."""
        response = await authenticated_client.get(f"/api/images/cover/{test_manga.id}")
        
        assert response.status_code == 404
        assert "Cover image not found" in response.json()["detail"]
    
    async def test_get_cover_image_manga_not_found(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test getting cover image for non-existent manga."""
        response = await authenticated_client.get("/api/images/cover/99999")
        
        assert response.status_code == 404
        assert "Manga not found" in response.json()["detail"]
    
    @pytest.mark.slow
    async def test_image_caching(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test that image caching works correctly."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                # First request should call optimize_image
                response1 = await authenticated_client.get(f"/api/images/{page.id}")
                assert response1.status_code == 200
                assert mock_optimize.call_count == 1
                
                # Second request with same parameters should use cache
                # (Note: This is simplified - actual caching logic would be more complex)
                response2 = await authenticated_client.get(f"/api/images/{page.id}")
                assert response2.status_code == 200
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_archive_image_extraction(
        self, 
        authenticated_client: AsyncClient, 
        test_db: AsyncSession
    ):
        """Test serving images from archive files."""
        # Create archive-based manga
        archive_manga = Manga(
            title="Archive Manga",
            slug="archive-manga",
            folder_path="/path/to/archive.cbz",
            is_archive=True
        )
        test_db.add(archive_manga)
        await test_db.commit()
        await test_db.refresh(archive_manga)
        
        # Create chapter and page for archive
        archive_chapter = Chapter(
            manga_id=archive_manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 1",
            folder_path="/path/to/archive.cbz:Chapter 1"
        )
        test_db.add(archive_chapter)
        await test_db.commit()
        await test_db.refresh(archive_chapter)
        
        archive_page = Page(
            chapter_id=archive_chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path="/path/to/archive.cbz:Chapter 1/001.jpg"
        )
        test_db.add(archive_page)
        await test_db.commit()
        await test_db.refresh(archive_page)
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer._load_from_archive') as mock_load, \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{archive_page.id}")
                
                assert response.status_code == 200
                # Should attempt to load from archive
                mock_optimize.assert_called_once()
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_image_format_conversion(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test that images are properly converted to web-friendly formats."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            # Create fake WebP image
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{page.id}")
                
                assert response.status_code == 200
                # Should optimize/convert image
                mock_optimize.assert_called_once()
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_streaming_response(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test that images are streamed efficiently."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.write_bytes(b'fake image data')
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{page.id}")
                
                assert response.status_code == 200
                # Should have proper content-type
                assert "image/" in response.headers.get("content-type", "")
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_image_endpoints_unauthorized(self, client: AsyncClient, test_manga: Manga):
        """Test that image endpoints require authentication."""
        endpoints = [
            "/api/images/1",
            f"/api/images/cover/{test_manga.id}",
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401
    
    async def test_image_error_handling(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test proper error handling in image processing."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image', side_effect=Exception("Processing error")):
            
            response = await authenticated_client.get(f"/api/images/{page.id}")
            
            assert response.status_code == 500
            assert "Error processing image" in response.json()["detail"]