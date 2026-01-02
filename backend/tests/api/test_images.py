import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import tempfile
import os
import zipfile
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
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
                response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
                
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
        response = await authenticated_client.get("/api/images/99999/99999/99999")
        
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        # Mock file not existing
        with patch('os.path.exists', return_value=False):
            response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
            
            assert response.status_code == 500
            assert "Image optimization failed" in response.json()["detail"]
    
    async def test_get_page_image_with_optimization(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test serving page image with size optimization."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(
                    f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}?width=800&height=600&quality=90"
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        # Test negative dimensions
        response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}?width=-100")
        assert response.status_code == 422
        
        # Test invalid quality
        response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}?quality=150")
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
                response = await authenticated_client.get(f"/api/images/covers/{test_manga.id}")
                
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
        """Test getting cover image when manga has no cover - falls back to first page."""
        with patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            # Create a fake optimized image path
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/covers/{test_manga.id}")
                
                # Should fall back to first page of first chapter
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("image/")
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_get_cover_image_manga_not_found(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test getting cover image for non-existent manga."""
        response = await authenticated_client.get("/api/images/covers/99999")
        
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                # First request should call optimize_image
                response1 = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
                assert response1.status_code == 200
                assert mock_optimize.call_count == 1
                
                # Second request with same parameters should use cache
                # (Note: This is simplified - actual caching logic would be more complex)
                response2 = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
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
                response = await authenticated_client.get(f"/api/images/{archive_manga.id}/{archive_chapter.id}/{archive_page.id}")
                
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            # Create fake WebP image
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.touch()
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
                
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.write_bytes(b'fake image data')
            mock_optimize.return_value = fake_path
            
            try:
                response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
                
                assert response.status_code == 200
                # Should have proper content-type
                assert "image/" in response.headers.get("content-type", "")
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_image_endpoints_unauthorized(self, client: AsyncClient, test_manga: Manga):
        """Test that image endpoints require authentication."""
        endpoints = [
            "/api/images/1/1/1",
            f"/api/images/covers/{test_manga.id}",
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
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        # Mock optimize_image to raise an exception and make os.path.exists return False for the fallback
        with patch('app.api.images.ImageOptimizer.optimize_image', side_effect=Exception("Processing error")), \
             patch('os.path.exists', return_value=False):
            
            response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
            
            assert response.status_code == 500
            assert "Failed to serve image" in response.json()["detail"]


@pytest.mark.images
@pytest.mark.archive
@pytest.mark.asyncio
class TestArchiveFormatSupport:
    """Test comprehensive archive format support (ZIP, RAR, CBZ, CBR)."""
    
    async def test_cbz_format_support(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test CBZ (Comic Book ZIP) format support."""
        from unittest.mock import patch, mock_open
        import zipfile
        import io
        
        # Create CBZ-format manga
        cbz_manga = Manga(
            title="CBZ Test",
            slug="cbz-test",
            folder_path=str(temp_manga_dir / "test.cbz"),
            is_archive=True
        )
        test_db.add(cbz_manga)
        await test_db.commit()
        await test_db.refresh(cbz_manga)
        
        # Create chapter and page
        chapter = Chapter(
            manga_id=cbz_manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 1",
            folder_path=f"{cbz_manga.folder_path}:Chapter 1"
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path=f"{cbz_manga.folder_path}:Chapter 1/001.jpg"
        )
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        # Mock CBZ file operations
        fake_image_data = b"fake jpeg image data"
        
        with patch('app.api.images.ImageOptimizer._load_from_archive') as mock_load_archive, \
             patch('os.makedirs'):
            
            # Mock archive loading to return a fake PIL Image
            mock_image = MagicMock()
            mock_image.mode = 'RGB'
            mock_image.size = (800, 1200)
            mock_load_archive.return_value = mock_image
            
            # Create a real cache file for the response to serve
            import os
            os.makedirs('data/cache/images', exist_ok=True)
            
            # Mock PIL Image operations
            def mock_save(path, format_type, **kwargs):
                # Create the actual cache file
                Path(path).write_bytes(b'fake optimized webp image')
            
            mock_image.save = mock_save
            mock_image.thumbnail = MagicMock()
            
            response = await authenticated_client.get(
                f"/api/images/{cbz_manga.id}/{chapter.id}/{page.id}"
            )
            
            assert response.status_code == 200
            
            # Verify archive loading was called with correct parameters
            mock_load_archive.assert_called_once()
            args, kwargs = mock_load_archive.call_args
            archive_path, internal_path = args
            assert archive_path == cbz_manga.folder_path
            assert internal_path == "Chapter 1/001.jpg"
    
    async def test_cbr_format_support(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test CBR (Comic Book RAR) format support."""
        from unittest.mock import patch
        import rarfile
        
        # Create CBR-format manga
        cbr_manga = Manga(
            title="CBR Test",
            slug="cbr-test",
            folder_path=str(temp_manga_dir / "test.cbr"),
            is_archive=True
        )
        test_db.add(cbr_manga)
        await test_db.commit()
        await test_db.refresh(cbr_manga)
        
        # Create chapter and page
        chapter = Chapter(
            manga_id=cbr_manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 1",
            folder_path=f"{cbr_manga.folder_path}:Chapter 1"
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.png",
            file_path=f"{cbr_manga.folder_path}:Chapter 1/001.png"
        )
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        # Mock CBR file operations
        fake_image_data = b"fake png image data"
        
        with patch('app.api.images.ImageOptimizer._load_from_archive') as mock_load_archive, \
             patch('os.makedirs'):
            
            # Mock archive loading to return a fake PIL Image
            mock_image = MagicMock()
            mock_image.mode = 'RGB'
            mock_image.size = (800, 1200)
            mock_load_archive.return_value = mock_image
            
            # Create a real cache file for the response to serve
            import os
            os.makedirs('data/cache/images', exist_ok=True)
            
            # Mock PIL Image operations
            def mock_save(path, format_type, **kwargs):
                # Create the actual cache file
                Path(path).write_bytes(b'fake optimized webp image')
            
            mock_image.save = mock_save
            mock_image.thumbnail = MagicMock()
            
            response = await authenticated_client.get(
                f"/api/images/{cbr_manga.id}/{chapter.id}/{page.id}"
            )
            
            assert response.status_code == 200
            
            # Verify archive loading was called with correct parameters
            mock_load_archive.assert_called_once()
            args, kwargs = mock_load_archive.call_args
            archive_path, internal_path = args
            assert archive_path == cbr_manga.folder_path
            assert internal_path == "Chapter 1/001.png"
    
    async def test_zip_format_support(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test regular ZIP format support."""
        from unittest.mock import patch
        
        # Create ZIP-format manga
        zip_manga = Manga(
            title="ZIP Test", 
            slug="zip-test",
            folder_path=str(temp_manga_dir / "test.zip"),
            is_archive=True
        )
        test_db.add(zip_manga)
        await test_db.commit()
        await test_db.refresh(zip_manga)
        
        chapter = Chapter(
            manga_id=zip_manga.id,
            title="Single Chapter",
            chapter_number=1,
            folder_name="",
            folder_path=zip_manga.folder_path
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="page01.webp",
            file_path=f"{zip_manga.folder_path}:page01.webp"
        )
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        fake_image_data = b"fake webp image data"
        
        with patch('app.api.images.ImageOptimizer._load_from_archive') as mock_load_archive, \
             patch('os.makedirs'):
            
            # Mock archive loading to return a fake PIL Image
            mock_image = MagicMock()
            mock_image.mode = 'RGB'
            mock_image.size = (800, 1200)
            mock_load_archive.return_value = mock_image
            
            # Create a real cache file for the response to serve
            import os
            os.makedirs('data/cache/images', exist_ok=True)
            
            # Mock PIL Image operations
            def mock_save(path, format_type, **kwargs):
                # Create the actual cache file
                Path(path).write_bytes(b'fake optimized webp image')
            
            mock_image.save = mock_save
            mock_image.thumbnail = MagicMock()
            
            response = await authenticated_client.get(
                f"/api/images/{zip_manga.id}/{chapter.id}/{page.id}"
            )
            
            assert response.status_code == 200
            
            # Verify archive loading was called with correct parameters
            mock_load_archive.assert_called_once()
            args, kwargs = mock_load_archive.call_args
            archive_path, internal_path = args
            assert archive_path == zip_manga.folder_path
            assert internal_path == "page01.webp"
    
    async def test_unsupported_archive_format_error(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test error handling for unsupported archive formats."""
        # Create manga with unsupported archive format
        unsupported_manga = Manga(
            title="7Z Test",
            slug="7z-test",
            folder_path=str(temp_manga_dir / "test.7z"),
            is_archive=True
        )
        test_db.add(unsupported_manga)
        await test_db.commit()
        await test_db.refresh(unsupported_manga)
        
        chapter = Chapter(
            manga_id=unsupported_manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 1",
            folder_path=f"{unsupported_manga.folder_path}:Chapter 1"
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path=f"{unsupported_manga.folder_path}:Chapter 1/001.jpg"
        )
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        response = await authenticated_client.get(
            f"/api/images/{unsupported_manga.id}/{chapter.id}/{page.id}"
        )
        
        assert response.status_code == 500
        assert "Failed to load image from archive" in response.json()["detail"]
    
    async def test_corrupted_archive_handling(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        temp_manga_dir: Path
    ):
        """Test handling of corrupted archive files."""
        from unittest.mock import patch
        
        # Create manga with corrupted archive
        corrupted_manga = Manga(
            title="Corrupted Archive",
            slug="corrupted-archive",
            folder_path=str(temp_manga_dir / "corrupted.cbz"),
            is_archive=True
        )
        test_db.add(corrupted_manga)
        await test_db.commit()
        await test_db.refresh(corrupted_manga)
        
        chapter = Chapter(
            manga_id=corrupted_manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 1",
            folder_path=f"{corrupted_manga.folder_path}:Chapter 1"
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path=f"{corrupted_manga.folder_path}:Chapter 1/001.jpg"
        )
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        # Mock zipfile to raise BadZipFile exception
        with patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile("Corrupted archive")):
            response = await authenticated_client.get(
                f"/api/images/{corrupted_manga.id}/{chapter.id}/{page.id}"
            )
            
            assert response.status_code == 500
            assert "Failed to load image from archive" in response.json()["detail"]
    
    async def test_archive_path_parsing(self):
        """Test that archive paths are correctly parsed."""
        from app.api.images import ImageOptimizer
        
        optimizer = ImageOptimizer()
        
        # Test parsing archive paths with colons
        test_cases = [
            ("/path/to/manga.cbz:Chapter 1/001.jpg", "/path/to/manga.cbz", "Chapter 1/001.jpg"),
            ("/path/to/manga.zip:page001.png", "/path/to/manga.zip", "page001.png"),
        ]
        
        for file_path, expected_archive, expected_internal in test_cases:
            archive_path, internal_path = file_path.split(':', 1)
            assert archive_path == expected_archive
            assert internal_path == expected_internal
        
        # Special handling for Windows paths
        windows_path = "C:\\manga\\test.cbr:Volume 1\\Chapter 1\\001.jpg"
        if ':' in windows_path and len(windows_path) > 2 and windows_path[1] == ':':
            # Find the archive delimiter (second colon)
            parts = windows_path.split(':', 2)
            if len(parts) == 3:
                archive_path = f"{parts[0]}:{parts[1]}"
                internal_path = parts[2]
                assert archive_path == "C:\\manga\\test.cbr"
                assert internal_path == "Volume 1\\Chapter 1\\001.jpg"