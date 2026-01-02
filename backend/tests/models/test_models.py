import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models import User, Manga, Chapter, Page, ReadingProgress, UserPreference
from app.core.security import get_password_hash, verify_password


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserModel:
    """Test User model functionality."""
    
    async def test_create_user(self, test_db: AsyncSession):
        """Test creating a basic user."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True  # Default value
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    async def test_user_unique_constraints(self, test_db: AsyncSession):
        """Test user unique constraints on username and email."""
        # Create first user
        user1 = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        test_db.add(user1)
        await test_db.commit()
        
        # Try to create user with same username
        user2 = User(
            username="testuser",  # Duplicate username
            email="different@example.com",
            hashed_password=get_password_hash("password456")
        )
        test_db.add(user2)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()
        
        await test_db.rollback()
        
        # Try to create user with same email
        user3 = User(
            username="differentuser",
            email="test@example.com",  # Duplicate email
            hashed_password=get_password_hash("password789")
        )
        test_db.add(user3)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()
    
    async def test_password_hashing(self, test_db: AsyncSession):
        """Test password hashing and verification."""
        password = "mySecretPassword123!"
        hashed = get_password_hash(password)
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Password should be hashed, not stored in plain text
        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)
        assert not verify_password("wrongPassword", user.hashed_password)
    
    async def test_user_relationships(self, test_db: AsyncSession):
        """Test user relationships with other models."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Create user preferences
        prefs = UserPreference(
            user_id=user.id,
            default_reading_direction="ltr",
            theme="light"
        )
        test_db.add(prefs)
        await test_db.commit()
        
        # Test relationship
        result = await test_db.execute(
            select(User).where(User.id == user.id)
        )
        user_with_prefs = result.scalar_one()
        
        # Note: In async SQLAlchemy, relationships need explicit loading
        # This is just testing the model structure is correct
        assert user_with_prefs.id == user.id


@pytest.mark.unit
@pytest.mark.asyncio
class TestMangaModel:
    """Test Manga model functionality."""
    
    async def test_create_manga(self, test_db: AsyncSession):
        """Test creating a manga."""
        manga = Manga(
            title="Test Manga",
            slug="test-manga",
            description="A test manga for testing",
            author="Test Author",
            artist="Test Artist",
            status="ongoing",
            year=2024,
            folder_path="/path/to/manga",
            is_archive=False,
            total_chapters=10
        )
        
        test_db.add(manga)
        await test_db.commit()
        await test_db.refresh(manga)
        
        assert manga.id is not None
        assert manga.title == "Test Manga"
        assert manga.slug == "test-manga"
        assert manga.description == "A test manga for testing"
        assert manga.author == "Test Author"
        assert manga.artist == "Test Artist"
        assert manga.status == "ongoing"
        assert manga.year == 2024
        assert manga.is_archive is False
        assert manga.total_chapters == 10
        assert manga.created_at is not None
    
    async def test_manga_unique_slug(self, test_db: AsyncSession):
        """Test manga slug uniqueness constraint."""
        # Create first manga
        manga1 = Manga(
            title="First Manga",
            slug="test-manga",
            folder_path="/path/to/first",
            is_archive=False
        )
        test_db.add(manga1)
        await test_db.commit()
        
        # Try to create manga with same slug
        manga2 = Manga(
            title="Second Manga",
            slug="test-manga",  # Duplicate slug
            folder_path="/path/to/second",
            is_archive=False
        )
        test_db.add(manga2)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()
    
    async def test_manga_required_fields(self, test_db: AsyncSession):
        """Test manga required fields."""
        # Missing title (required)
        with pytest.raises(IntegrityError):
            manga = Manga(
                slug="test-manga",
                folder_path="/path/to/manga",
                is_archive=False
            )
            test_db.add(manga)
            await test_db.commit()
        
        await test_db.rollback()
        
        # Missing slug (required)
        with pytest.raises(IntegrityError):
            manga = Manga(
                title="Test Manga",
                folder_path="/path/to/manga",
                is_archive=False
            )
            test_db.add(manga)
            await test_db.commit()
    
    async def test_manga_optional_fields(self, test_db: AsyncSession):
        """Test manga with minimal required fields."""
        manga = Manga(
            title="Minimal Manga",
            slug="minimal-manga",
            folder_path="/path/to/minimal",
            is_archive=False
        )
        
        test_db.add(manga)
        await test_db.commit()
        await test_db.refresh(manga)
        
        assert manga.description is None
        assert manga.author is None
        assert manga.artist is None
        assert manga.genres is None
        assert manga.status is None
        assert manga.year is None
        assert manga.cover_image is None
        assert manga.total_chapters == 0  # Default value


@pytest.mark.unit
@pytest.mark.asyncio
class TestChapterModel:
    """Test Chapter model functionality."""
    
    async def test_create_chapter(self, test_db: AsyncSession, test_manga: Manga):
        """Test creating a chapter."""
        chapter = Chapter(
            manga_id=test_manga.id,
            title="Chapter 1: The Beginning",
            chapter_number=1.0,
            folder_name="Chapter 001",
            folder_path="/path/to/chapter1",
            page_count=20
        )
        
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        assert chapter.id is not None
        assert chapter.manga_id == test_manga.id
        assert chapter.title == "Chapter 1: The Beginning"
        assert chapter.chapter_number == 1.0
        assert chapter.folder_name == "Chapter 001"
        assert chapter.folder_path == "/path/to/chapter1"
        assert chapter.page_count == 20
        assert chapter.created_at is not None
    
    async def test_chapter_decimal_numbers(self, test_db: AsyncSession, test_manga: Manga):
        """Test chapters with decimal numbers."""
        chapter = Chapter(
            manga_id=test_manga.id,
            title="Chapter 5.5: Extra",
            chapter_number=5.5,
            folder_name="Chapter 005.5",
            folder_path="/path/to/chapter5.5"
        )
        
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        assert chapter.chapter_number == 5.5
    
    async def test_chapter_foreign_key(self, test_db: AsyncSession):
        """Test chapter foreign key constraint."""
        # Try to create chapter with non-existent manga_id
        chapter = Chapter(
            manga_id=99999,  # Non-existent manga
            title="Invalid Chapter",
            chapter_number=1,
            folder_name="Chapter 001",
            folder_path="/path/to/invalid"
        )
        
        test_db.add(chapter)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPageModel:
    """Test Page model functionality."""
    
    async def test_create_page(self, test_db: AsyncSession, test_manga: Manga):
        """Test creating a page."""
        # Get a chapter from test_manga
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        chapter = result.scalar_one()
        
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path="/path/to/page001.jpg",
            file_size=1024000,
            width=800,
            height=1200
        )
        
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        assert page.id is not None
        assert page.chapter_id == chapter.id
        assert page.page_number == 1
        assert page.filename == "001.jpg"
        assert page.file_path == "/path/to/page001.jpg"
        assert page.file_size == 1024000
        assert page.width == 800
        assert page.height == 1200
    
    async def test_page_minimal_fields(self, test_db: AsyncSession, test_manga: Manga):
        """Test creating page with minimal required fields."""
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        chapter = result.scalar_one()
        
        page = Page(
            chapter_id=chapter.id,
            page_number=2,
            filename="002.jpg",
            file_path="/path/to/page002.jpg"
        )
        
        test_db.add(page)
        await test_db.commit()
        await test_db.refresh(page)
        
        assert page.file_size is None
        assert page.width is None
        assert page.height is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestReadingProgressModel:
    """Test ReadingProgress model functionality."""
    
    async def test_create_reading_progress(
        self, 
        test_db: AsyncSession, 
        test_user: User, 
        test_manga: Manga
    ):
        """Test creating reading progress."""
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        chapter = result.scalar_one()
        
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=5,
            reading_direction="rtl",
            zoom_level=1.5,
            scroll_position=0.3
        )
        
        test_db.add(progress)
        await test_db.commit()
        await test_db.refresh(progress)
        
        assert progress.id is not None
        assert progress.user_id == test_user.id
        assert progress.manga_id == test_manga.id
        assert progress.chapter_id == chapter.id
        assert progress.page_number == 5
        assert progress.reading_direction == "rtl"
        assert progress.zoom_level == 1.5
        assert progress.scroll_position == 0.3
        assert progress.last_read_at is not None
    
    async def test_reading_progress_defaults(
        self, 
        test_db: AsyncSession, 
        test_user: User, 
        test_manga: Manga
    ):
        """Test reading progress default values."""
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id
        )
        
        test_db.add(progress)
        await test_db.commit()
        await test_db.refresh(progress)
        
        assert progress.page_number == 1  # Default
        assert progress.reading_direction == "rtl"  # Default
        assert progress.zoom_level == 1.0  # Default
        assert progress.scroll_position == 0.0  # Default
        assert progress.chapter_id is None  # Optional
    
    async def test_reading_progress_foreign_keys(self, test_db: AsyncSession):
        """Test reading progress foreign key constraints."""
        # Invalid user_id
        with pytest.raises(IntegrityError):
            progress = ReadingProgress(
                user_id=99999,  # Non-existent user
                manga_id=1,
                page_number=1
            )
            test_db.add(progress)
            await test_db.commit()
        
        await test_db.rollback()
        
        # Invalid manga_id
        with pytest.raises(IntegrityError):
            progress = ReadingProgress(
                user_id=1,
                manga_id=99999,  # Non-existent manga
                page_number=1
            )
            test_db.add(progress)
            await test_db.commit()


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserPreferenceModel:
    """Test UserPreference model functionality."""
    
    async def test_create_user_preference(self, test_db: AsyncSession, test_user: User):
        """Test creating user preferences."""
        prefs = UserPreference(
            user_id=test_user.id,
            default_reading_direction="ltr",
            auto_next_chapter=False,
            page_fit_mode="fit-height",
            theme="light",
            items_per_page=30
        )
        
        test_db.add(prefs)
        await test_db.commit()
        await test_db.refresh(prefs)
        
        assert prefs.id is not None
        assert prefs.user_id == test_user.id
        assert prefs.default_reading_direction == "ltr"
        assert prefs.auto_next_chapter is False
        assert prefs.page_fit_mode == "fit-height"
        assert prefs.theme == "light"
        assert prefs.items_per_page == 30
    
    async def test_user_preference_defaults(self, test_db: AsyncSession, test_user: User):
        """Test user preference default values."""
        prefs = UserPreference(user_id=test_user.id)
        
        test_db.add(prefs)
        await test_db.commit()
        await test_db.refresh(prefs)
        
        assert prefs.default_reading_direction == "rtl"  # Default
        assert prefs.auto_next_chapter is True  # Default
        assert prefs.page_fit_mode == "fit-width"  # Default
        assert prefs.theme == "dark"  # Default
        assert prefs.items_per_page == 20  # Default


@pytest.mark.unit
@pytest.mark.asyncio
class TestModelRelationships:
    """Test model relationships and cascading."""
    
    async def test_manga_chapter_relationship(self, test_db: AsyncSession, test_manga: Manga):
        """Test manga-chapter relationship."""
        # Chapters should be associated with manga
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id)
        )
        chapters = result.scalars().all()
        
        assert len(chapters) > 0
        for chapter in chapters:
            assert chapter.manga_id == test_manga.id
    
    async def test_chapter_page_relationship(self, test_db: AsyncSession, test_manga: Manga):
        """Test chapter-page relationship."""
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        chapter = result.scalar_one()
        
        result = await test_db.execute(
            select(Page).where(Page.chapter_id == chapter.id)
        )
        pages = result.scalars().all()
        
        assert len(pages) > 0
        for page in pages:
            assert page.chapter_id == chapter.id
    
    async def test_user_progress_relationship(
        self, 
        test_db: AsyncSession, 
        test_user: User, 
        test_manga: Manga
    ):
        """Test user-progress relationship."""
        # Create reading progress
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            page_number=1
        )
        test_db.add(progress)
        await test_db.commit()
        
        # Verify relationship
        result = await test_db.execute(
            select(ReadingProgress).where(ReadingProgress.user_id == test_user.id)
        )
        user_progress = result.scalars().all()
        
        assert len(user_progress) == 1
        assert user_progress[0].user_id == test_user.id
        assert user_progress[0].manga_id == test_manga.id
    
    async def test_cascading_deletes(self, test_db: AsyncSession):
        """Test that related records are properly handled on deletion."""
        # Create a manga with chapters and pages
        manga = Manga(
            title="Delete Test Manga",
            slug="delete-test-manga",
            folder_path="/path/to/delete/test",
            is_archive=False
        )
        test_db.add(manga)
        await test_db.commit()
        await test_db.refresh(manga)
        
        # Add chapter
        chapter = Chapter(
            manga_id=manga.id,
            title="Chapter 1",
            chapter_number=1,
            folder_name="Chapter 001",
            folder_path="/path/to/chapter1"
        )
        test_db.add(chapter)
        await test_db.commit()
        await test_db.refresh(chapter)
        
        # Add page
        page = Page(
            chapter_id=chapter.id,
            page_number=1,
            filename="001.jpg",
            file_path="/path/to/page1.jpg"
        )
        test_db.add(page)
        await test_db.commit()
        
        # Delete manga (should cascade to chapters and pages)
        await test_db.delete(manga)
        await test_db.commit()
        
        # Verify chapters and pages were also deleted
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == manga.id)
        )
        assert len(result.scalars().all()) == 0
        
        result = await test_db.execute(
            select(Page).where(Page.chapter_id == chapter.id)
        )
        assert len(result.scalars().all()) == 0