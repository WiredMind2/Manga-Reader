import pytest
from pathlib import Path
import tempfile
import shutil
import zipfile
import json
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.manga_scanner import MangaScanner
from app.models import Manga, Chapter, Page


@pytest.mark.unit
@pytest.mark.asyncio
class TestMangaScanner:
    """Test the manga scanner service."""
    
    @pytest.fixture
    def scanner(self):
        """Create a manga scanner instance."""
        with patch('app.services.manga_scanner.settings') as mock_settings:
            mock_settings.MANGA_DIRECTORY = "/fake/manga/dir"
            mock_settings.SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp"]
            mock_settings.SUPPORTED_ARCHIVE_FORMATS = ["zip", "cbz", "rar", "cbr"]
            return MangaScanner()
    
    @pytest.fixture
    def complex_manga_dir(self):
        """Create a complex manga directory structure for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Manga 1: Regular folder structure
        manga1_dir = temp_dir / "One Piece"
        manga1_dir.mkdir()
        
        # Chapter 1 with images
        ch1_dir = manga1_dir / "Chapter 001"
        ch1_dir.mkdir()
        (ch1_dir / "001.jpg").touch()
        (ch1_dir / "002.jpg").touch()
        (ch1_dir / "003.png").touch()
        
        # Chapter 2 with images
        ch2_dir = manga1_dir / "Chapter 002"
        ch2_dir.mkdir()
        (ch2_dir / "001.webp").touch()
        (ch2_dir / "002.jpg").touch()
        
        # Manga 2: With metadata
        manga2_dir = temp_dir / "Naruto"
        manga2_dir.mkdir()
        
        # Create metadata file
        metadata = {
            "title": "Naruto",
            "author": "Masashi Kishimoto",
            "description": "A ninja manga",
            "genres": ["Action", "Adventure"],
            "status": "completed",
            "year": 1999
        }
        import json
        (manga2_dir / "metadata.json").write_text(json.dumps(metadata))
        
        ch1_dir = manga2_dir / "Chapter 001"
        ch1_dir.mkdir()
        (ch1_dir / "page01.jpg").touch()
        (ch1_dir / "page02.jpg").touch()
        
        # Manga 3: Archive format
        archive_path = temp_dir / "Attack on Titan.cbz"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("Chapter 1/001.jpg", b"fake image data")
            zf.writestr("Chapter 1/002.jpg", b"fake image data")
            zf.writestr("Chapter 2/001.jpg", b"fake image data")
        
        # Invalid folder (should be ignored)
        (temp_dir / "not_manga.txt").touch()
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    async def test_scan_empty_directory(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test scanning an empty directory."""
        with patch.object(scanner, 'manga_dir', Path("/nonexistent")):
            result = await scanner.scan_manga_directory(test_db)
            assert result == []
    
    async def test_scan_folder_manga_new(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning new folder-based manga."""
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            manga_list = await scanner.scan_manga_directory(test_db)
            
            assert len(manga_list) >= 2  # At least folder-based manga
            
            # Check that manga were created in database
            result = await test_db.execute(select(Manga))
            manga_in_db = result.scalars().all()
            
            titles = [manga.title for manga in manga_in_db]
            assert "One Piece" in titles
            assert "Naruto" in titles
    
    async def test_scan_folder_manga_existing(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning existing manga (should update, not duplicate)."""
        # Create existing manga
        existing_manga = Manga(
            title="One Piece",
            slug="one-piece",
            folder_path=str(complex_manga_dir / "One Piece"),
            is_archive=False,
            total_chapters=1  # Will be updated to 2
        )
        test_db.add(existing_manga)
        await test_db.commit()
        
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            manga_list = await scanner.scan_manga_directory(test_db)
            
            # Should update existing manga
            result = await test_db.execute(select(Manga).where(Manga.title == "One Piece"))
            updated_manga = result.scalar_one()
            
            assert updated_manga.total_chapters == 2  # Should be updated
    
    async def test_metadata_loading(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test loading manga metadata from metadata.json."""
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            await scanner.scan_manga_directory(test_db)
            
            # Check Naruto manga has metadata loaded
            result = await test_db.execute(select(Manga).where(Manga.title == "Naruto"))
            naruto_manga = result.scalar_one_or_none()
            
            assert naruto_manga is not None
            assert naruto_manga.author == "Masashi Kishimoto"
            assert naruto_manga.description == "A ninja manga"
            assert naruto_manga.status == "completed"
            assert naruto_manga.year == 1999
            
            # Genres should be stored as JSON
            import json
            genres = json.loads(naruto_manga.genres) if naruto_manga.genres else []
            assert "Action" in genres
            assert "Adventure" in genres
    
    async def test_metadata_with_cover_image(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test metadata loading with cover image support."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create manga directory with metadata and cover
            manga_dir = temp_dir / "Test Manga"
            manga_dir.mkdir()
            
            # Create metadata file with cover image reference
            metadata = {
                "title": "Test Manga",
                "author": "Test Author",
                "description": "A test manga with cover",
                "cover_image": "cover.jpg",
                "genres": ["Test", "Drama"],
                "status": "ongoing",
                "year": 2023
            }
            (manga_dir / "metadata.json").write_text(json.dumps(metadata))
            
            # Create cover image file
            cover_path = manga_dir / "cover.jpg"
            cover_path.touch()
            
            # Create chapter
            ch_dir = manga_dir / "Chapter 01"
            ch_dir.mkdir()
            (ch_dir / "01.jpg").touch()
            
            with patch.object(scanner, 'manga_dir', temp_dir):
                await scanner.scan_manga_directory(test_db)
                
                # Check manga was created with cover image
                result = await test_db.execute(select(Manga).where(Manga.title == "Test Manga"))
                manga = result.scalar_one_or_none()
                
                assert manga is not None
                assert manga.author == "Test Author"
                assert manga.description == "A test manga with cover"
                assert manga.cover_image == "cover.jpg"  # Should store relative path
                assert manga.status == "ongoing"
                assert manga.year == 2023
                
                genres = json.loads(manga.genres) if manga.genres else []
                assert "Test" in genres
                assert "Drama" in genres
        
        finally:
            shutil.rmtree(temp_dir)
    
    async def test_metadata_invalid_json(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test handling of invalid metadata.json files."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            manga_dir = temp_dir / "Invalid Metadata Manga"
            manga_dir.mkdir()
            
            # Create invalid JSON metadata
            (manga_dir / "metadata.json").write_text("{invalid json content}")
            
            # Create chapter
            ch_dir = manga_dir / "Chapter 01"
            ch_dir.mkdir()
            (ch_dir / "01.jpg").touch()
            
            with patch.object(scanner, 'manga_dir', temp_dir):
                # Should not crash, just skip metadata loading
                manga_list = await scanner.scan_manga_directory(test_db)
                
                assert len(manga_list) == 1
                
                # Check manga was created without metadata
                result = await test_db.execute(select(Manga).where(Manga.title == "Invalid Metadata Manga"))
                manga = result.scalar_one_or_none()
                
                assert manga is not None
                assert manga.author is None  # No metadata loaded
                assert manga.description is None
                
        finally:
            shutil.rmtree(temp_dir)
    
    async def test_metadata_partial_data(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test metadata with only some fields provided."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            manga_dir = temp_dir / "Partial Metadata Manga"
            manga_dir.mkdir()
            
            # Create partial metadata (missing some fields)
            metadata = {
                "author": "Partial Author",
                "year": 2020
                # Missing description, genres, status, etc.
            }
            (manga_dir / "metadata.json").write_text(json.dumps(metadata))
            
            # Create chapter
            ch_dir = manga_dir / "Chapter 01"
            ch_dir.mkdir()
            (ch_dir / "01.jpg").touch()
            
            with patch.object(scanner, 'manga_dir', temp_dir):
                await scanner.scan_manga_directory(test_db)
                
                # Check manga was created with partial metadata
                result = await test_db.execute(select(Manga).where(Manga.title == "Partial Metadata Manga"))
                manga = result.scalar_one_or_none()
                
                assert manga is not None
                assert manga.author == "Partial Author"
                assert manga.year == 2020
                assert manga.description is None  # Not provided
                assert manga.status is None  # Not provided
                
        finally:
            shutil.rmtree(temp_dir)
    
    async def test_metadata_without_file(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test scanning manga without metadata.json (fallback behavior)."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            manga_dir = temp_dir / "No Metadata Manga"
            manga_dir.mkdir()
            
            # Create chapter without metadata file
            ch_dir = manga_dir / "Chapter 01"
            ch_dir.mkdir()
            (ch_dir / "01.jpg").touch()
            
            with patch.object(scanner, 'manga_dir', temp_dir):
                manga_list = await scanner.scan_manga_directory(test_db)
                
                assert len(manga_list) == 1
                
                # Check manga was created with default values
                result = await test_db.execute(select(Manga).where(Manga.title == "No Metadata Manga"))
                manga = result.scalar_one_or_none()
                
                assert manga is not None
                assert manga.author is None
                assert manga.description is None
                assert manga.status is None
                assert manga.year is None
                assert manga.genres is None or manga.genres == "[]"
                
        finally:
            shutil.rmtree(temp_dir)
    
    async def test_chapter_scanning(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning chapters within manga."""
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            await scanner.scan_manga_directory(test_db)
            
            # Check One Piece chapters
            result = await test_db.execute(select(Manga).where(Manga.title == "One Piece"))
            one_piece = result.scalar_one()
            
            result = await test_db.execute(
                select(Chapter).where(Chapter.manga_id == one_piece.id).order_by(Chapter.chapter_number)
            )
            chapters = result.scalars().all()
            
            assert len(chapters) == 2
            assert chapters[0].chapter_number == 1
            assert chapters[1].chapter_number == 2
            assert chapters[0].page_count == 3  # 3 images in Chapter 001
            assert chapters[1].page_count == 2  # 2 images in Chapter 002
    
    async def test_page_scanning(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning pages within chapters."""
        with patch.object(scanner, 'manga_dir', complex_manga_dir), \
             patch('PIL.Image.open') as mock_open:
            
            # Mock image dimensions for all files
            mock_image = MagicMock()
            mock_image.size = (800, 1200)
            mock_open.return_value.__enter__.return_value = mock_image
            
            await scanner.scan_manga_directory(test_db)
            
            # Check pages in first chapter of One Piece
            result = await test_db.execute(select(Manga).where(Manga.title == "One Piece"))
            one_piece = result.scalar_one()
            
            result = await test_db.execute(
                select(Chapter).where(
                    Chapter.manga_id == one_piece.id, 
                    Chapter.chapter_number == 1
                )
            )
            chapter1 = result.scalar_one()
            
            result = await test_db.execute(
                select(Page).where(Page.chapter_id == chapter1.id).order_by(Page.page_number)
            )
            pages = result.scalars().all()
            
            assert len(pages) == 3
            assert pages[0].filename == "001.jpg"
            assert pages[1].filename == "002.jpg"
            assert pages[2].filename == "003.png"
            assert all(page.width is not None for page in pages)  # Should have dimensions
            assert all(page.height is not None for page in pages)
    
    async def test_archive_manga_scanning(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning archive-based manga."""
        with patch.object(scanner, 'manga_dir', complex_manga_dir), \
             patch('rarfile.is_rarfile', return_value=False), \
             patch('zipfile.is_zipfile', return_value=True):
            
            manga_list = await scanner.scan_manga_directory(test_db)
            
            # Check that archive manga was created
            result = await test_db.execute(
                select(Manga).where(Manga.title == "Attack on Titan")
            )
            archive_manga = result.scalar_one_or_none()
            
            assert archive_manga is not None
            assert archive_manga.is_archive is True
            assert archive_manga.folder_path.endswith(".cbz")
    
    async def test_slug_generation(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test manga slug generation."""
        test_cases = [
            ("One Piece", "one-piece"),
            ("Attack on Titan", "attack-on-titan"),
            ("Dr. Stone", "dr-stone"),
            ("Jujutsu Kaisen", "jujutsu-kaisen"),
            ("Special@#$%Characters!", "specialcharacters")
        ]
        
        for title, expected_slug in test_cases:
            slug = scanner._create_slug(title)
            assert slug == expected_slug
    
    async def test_duplicate_slug_handling(self, scanner: MangaScanner, test_db: AsyncSession):
        """Test handling of duplicate slugs."""
        # Create manga with existing slug
        existing_manga = Manga(
            title="Test Manga",
            slug="test-manga",
            folder_path="/path/to/existing",
            is_archive=False
        )
        test_db.add(existing_manga)
        await test_db.commit()
        
        # Should generate unique slug
        new_slug = await scanner._get_unique_slug("test-manga", test_db)
        assert new_slug != "test-manga"
        assert new_slug.startswith("test-manga-")
    
    async def test_image_dimension_extraction(self, scanner: MangaScanner, temp_manga_dir: Path):
        """Test extracting image dimensions."""
        with patch('PIL.Image.open') as mock_open:
            mock_image = MagicMock()
            mock_image.size = (800, 1200)
            # Set up context manager behavior
            mock_open.return_value.__enter__.return_value = mock_image
            
            width, height = scanner._get_image_dimensions(str(temp_manga_dir / "test.jpg"))
            
            assert width == 800
            assert height == 1200
    
    async def test_image_dimension_extraction_error(self, scanner: MangaScanner, temp_manga_dir: Path):
        """Test handling errors in image dimension extraction."""
        with patch('PIL.Image.open', side_effect=Exception("Cannot open image")):
            width, height = scanner._get_image_dimensions(str(temp_manga_dir / "test.jpg"))
            
            # Should return None for both dimensions on error
            assert width is None
            assert height is None
    
    async def test_chapter_number_parsing(self, scanner: MangaScanner):
        """Test parsing chapter numbers from folder names."""
        test_cases = [
            ("Chapter 001", 1.0),
            ("Chapter 10", 10.0),
            ("Ch. 5.5", 5.5),
            ("Volume 2 Chapter 15", 15.0),
            ("Chapter 001 - Title", 1.0),
            ("Random Folder", None)
        ]
        
        for folder_name, expected in test_cases:
            result = scanner._extract_chapter_number(folder_name)
            if expected is None:
                assert result is None
            else:
                assert abs(result - expected) < 0.01  # Float comparison
    
    async def test_supported_image_filtering(self, scanner: MangaScanner):
        """Test filtering of supported image formats."""
        files = [
            "image.jpg",
            "image.jpeg", 
            "image.png",
            "image.webp",
            "image.gif",  # Not in supported formats
            "document.txt",
            "video.mp4"
        ]
        
        supported = scanner._filter_supported_images(files)
        
        assert "image.jpg" in supported
        assert "image.jpeg" in supported
        assert "image.png" in supported
        assert "image.webp" in supported
        assert "image.gif" not in supported
        assert "document.txt" not in supported
        assert "video.mp4" not in supported
    
    async def test_natural_sort_pages(self, scanner: MangaScanner):
        """Test natural sorting of page files."""
        files = [
            "page10.jpg",
            "page2.jpg", 
            "page1.jpg",
            "page20.jpg"
        ]
        
        sorted_files = scanner._natural_sort(files)
        
        assert sorted_files == ["page1.jpg", "page2.jpg", "page10.jpg", "page20.jpg"]
    
    async def test_cover_image_detection(self, scanner: MangaScanner, complex_manga_dir: Path):
        """Test automatic cover image detection."""
        # Add cover image to manga directory
        manga_dir = complex_manga_dir / "One Piece"
        (manga_dir / "cover.jpg").touch()
        
        cover_path = await scanner._find_cover_image(manga_dir)
        
        assert cover_path is not None
        assert "cover.jpg" in str(cover_path)
    
    async def test_scan_with_errors(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test scanning continues despite errors in individual manga."""
        # Mock one manga to raise an error
        original_scan_folder = scanner._scan_folder_manga
        
        async def mock_scan_folder(manga_path, db):
            if "One Piece" in str(manga_path):
                raise Exception("Simulated error")
            return await original_scan_folder(manga_path, db)
        
        with patch.object(scanner, '_scan_folder_manga', side_effect=mock_scan_folder):
            with patch.object(scanner, 'manga_dir', complex_manga_dir):
                manga_list = await scanner.scan_manga_directory(test_db)
                
                # Should still process other manga despite error
                result = await test_db.execute(select(Manga))
                manga_in_db = result.scalars().all()
                
                # Should have processed Naruto even though One Piece failed
                titles = [manga.title for manga in manga_in_db]
                assert "Naruto" in titles
                assert "One Piece" not in titles
    
    async def test_incremental_scanning(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test incremental scanning (only processing new/changed manga)."""
        # First scan
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            await scanner.scan_manga_directory(test_db)
            
            initial_count = len((await test_db.execute(select(Manga))).scalars().all())
            
            # Second scan (should not duplicate)
            await scanner.scan_manga_directory(test_db)
            
            final_count = len((await test_db.execute(select(Manga))).scalars().all())
            
            assert initial_count == final_count  # No duplicates
    
    async def test_concurrent_scanning_safety(self, scanner: MangaScanner, test_db: AsyncSession, complex_manga_dir: Path):
        """Test that concurrent scanning is handled safely."""
        # This is a simplified test - in practice, you'd need proper database locking
        with patch.object(scanner, 'manga_dir', complex_manga_dir):
            # Simulate concurrent scans
            import asyncio
            results = await asyncio.gather(
                scanner.scan_manga_directory(test_db),
                scanner.scan_manga_directory(test_db),
                return_exceptions=True
            )
            
            # Should not crash
            assert all(not isinstance(result, Exception) for result in results)