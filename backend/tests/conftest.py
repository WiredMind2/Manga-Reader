import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models import User, Manga, Chapter, Page, UserPreference
from app.core.security import get_password_hash


# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with foreign key support
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
    echo=False
)

# Enable foreign key constraints for SQLite
async def enable_foreign_keys(connection, connection_record):
    """Enable foreign key constraints in SQLite."""
    cursor = await connection.execute("PRAGMA foreign_keys=ON")
    await cursor.close()

from sqlalchemy import event
event.listens_for(test_engine.sync_engine, "connect")(
    lambda dbapi_connection, connection_record: dbapi_connection.execute("PRAGMA foreign_keys=ON")
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with dependency overrides."""
    
    # Create a proper async dependency override
    async def get_test_db():
        return test_db
    
    # Override the dependency
    app.dependency_overrides[get_db] = get_test_db
    
    # Create the async client
    async with AsyncClient(base_url="http://testserver") as client:
        client._transport = ASGITransport(app=app)
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(test_db: AsyncSession) -> Generator[TestClient, None, None]:
    """Create a synchronous test client for simple tests."""
    
    def override_get_db():
        return test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_manga_dir() -> Generator[Path, None, None]:
    """Create a temporary manga directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create sample manga structure
    manga1_dir = temp_dir / "Test Manga 1"
    manga1_dir.mkdir()
    
    # Chapter 1
    chapter1_dir = manga1_dir / "Chapter 001"
    chapter1_dir.mkdir()
    (chapter1_dir / "001.jpg").touch()
    (chapter1_dir / "002.jpg").touch()
    (chapter1_dir / "003.jpg").touch()
    
    # Chapter 2
    chapter2_dir = manga1_dir / "Chapter 002"
    chapter2_dir.mkdir()
    (chapter2_dir / "001.jpg").touch()
    (chapter2_dir / "002.jpg").touch()
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Create user preferences
    prefs = UserPreference(user_id=user.id)
    test_db.add(prefs)
    await test_db.commit()
    
    return user


@pytest.fixture
async def test_user2(test_db: AsyncSession) -> User:
    """Create a second test user."""
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password=get_password_hash("testpass456")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Create user preferences
    prefs = UserPreference(user_id=user.id)
    test_db.add(prefs)
    await test_db.commit()
    
    return user


@pytest.fixture
async def test_manga(test_db: AsyncSession, temp_manga_dir: Path) -> Manga:
    """Create a test manga with chapters and pages."""
    manga = Manga(
        title="Test Manga",
        slug="test-manga",
        description="A test manga for testing",
        author="Test Author",
        artist="Test Artist",
        status="ongoing",
        year=2024,
        folder_path=str(temp_manga_dir / "Test Manga 1"),
        is_archive=False,
        total_chapters=2
    )
    test_db.add(manga)
    await test_db.commit()
    await test_db.refresh(manga)
    
    # Add chapters
    chapter1 = Chapter(
        manga_id=manga.id,
        title="Chapter 1",
        chapter_number=1,
        folder_name="Chapter 001",
        folder_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 001"),
        page_count=3
    )
    test_db.add(chapter1)
    
    chapter2 = Chapter(
        manga_id=manga.id,
        title="Chapter 2",
        chapter_number=2,
        folder_name="Chapter 002",
        folder_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 002"),
        page_count=2
    )
    test_db.add(chapter2)
    
    await test_db.commit()
    await test_db.refresh(chapter1)
    await test_db.refresh(chapter2)
    
    # Add pages
    pages = [
        Page(
            chapter_id=chapter1.id,
            page_number=1,
            filename="001.jpg",
            file_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 001" / "001.jpg"),
            width=800,
            height=1200
        ),
        Page(
            chapter_id=chapter1.id,
            page_number=2,
            filename="002.jpg",
            file_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 001" / "002.jpg"),
            width=800,
            height=1200
        ),
        Page(
            chapter_id=chapter1.id,
            page_number=3,
            filename="003.jpg",
            file_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 001" / "003.jpg"),
            width=800,
            height=1200
        ),
        Page(
            chapter_id=chapter2.id,
            page_number=1,
            filename="001.jpg",
            file_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 002" / "001.jpg"),
            width=800,
            height=1200
        ),
        Page(
            chapter_id=chapter2.id,
            page_number=2,
            filename="002.jpg",
            file_path=str(temp_manga_dir / "Test Manga 1" / "Chapter 002" / "002.jpg"),
            width=800,
            height=1200
        )
    ]
    
    for page in pages:
        test_db.add(page)
    
    await test_db.commit()
    
    return manga


@pytest.fixture
async def test_chapter(test_db: AsyncSession, test_manga: Manga) -> Chapter:
    """Get the first chapter from test_manga."""
    from sqlalchemy import select
    result = await test_db.execute(
        select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
    )
    chapter = result.scalar_one()
    return chapter


async def create_access_token_for_user(user: User) -> str:
    """Helper to create access token for test user."""
    from app.core.security import create_access_token
    from datetime import timedelta
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Create an authenticated test client."""
    token = await create_access_token_for_user(test_user)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# Helper functions for test assertions
def assert_manga_response(manga_data: dict, expected_manga: Manga):
    """Assert that manga response data matches expected manga."""
    assert manga_data["id"] == expected_manga.id
    assert manga_data["title"] == expected_manga.title
    assert manga_data["slug"] == expected_manga.slug
    assert manga_data["description"] == expected_manga.description
    assert manga_data["author"] == expected_manga.author
    assert manga_data["artist"] == expected_manga.artist
    assert manga_data["status"] == expected_manga.status
    assert manga_data["year"] == expected_manga.year
    assert manga_data["total_chapters"] == expected_manga.total_chapters


def assert_chapter_response(chapter_data: dict, expected_chapter: Chapter):
    """Assert that chapter response data matches expected chapter."""
    assert chapter_data["id"] == expected_chapter.id
    assert chapter_data["title"] == expected_chapter.title
    assert chapter_data["chapter_number"] == expected_chapter.chapter_number
    assert chapter_data["folder_name"] == expected_chapter.folder_name
    assert chapter_data["page_count"] == expected_chapter.page_count


def assert_page_response(page_data: dict, expected_page: Page):
    """Assert that page response data matches expected page."""
    assert page_data["id"] == expected_page.id
    assert page_data["page_number"] == expected_page.page_number
    assert page_data["filename"] == expected_page.filename
    assert page_data["width"] == expected_page.width
    assert page_data["height"] == expected_page.height