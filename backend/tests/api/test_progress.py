import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models import User, Manga, Chapter, ReadingProgress


@pytest.mark.progress
@pytest.mark.asyncio
class TestProgressEndpoints:
    """Test reading progress endpoints."""
    
    async def test_get_all_reading_progress_empty(self, authenticated_client: AsyncClient):
        """Test getting all reading progress when none exists."""
        response = await authenticated_client.get("/api/progress/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_get_all_reading_progress_with_data(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test getting all reading progress with existing data."""
        # Create reading progress
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=2,
            reading_direction="rtl",
            zoom_level=1.5,
            scroll_position=0.3
        )
        test_db.add(progress)
        await test_db.commit()
        await test_db.refresh(progress)
        
        response = await authenticated_client.get("/api/progress/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        progress_data = data[0]
        assert progress_data["id"] == progress.id
        assert progress_data["manga_id"] == test_manga.id
        assert progress_data["chapter_id"] == chapter.id
        assert progress_data["page_number"] == 2
        assert progress_data["reading_direction"] == "rtl"
        assert progress_data["zoom_level"] == 1.5
        assert progress_data["scroll_position"] == 0.3
        assert "last_read_at" in progress_data
    
    async def test_get_manga_reading_progress_not_found(self, authenticated_client: AsyncClient):
        """Test getting progress for non-existent manga."""
        response = await authenticated_client.get("/api/progress/99999")
        
        assert response.status_code == 404
        assert "Manga not found" in response.json()["detail"]
    
    async def test_get_manga_reading_progress_no_progress(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga
    ):
        """Test getting progress for manga with no reading progress."""
        response = await authenticated_client.get(f"/api/progress/{test_manga.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data is None
    
    async def test_get_manga_reading_progress_with_data(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test getting progress for manga with existing progress."""
        # Create reading progress
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 2)
        )
        chapter = result.scalar_one()
        
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=1,
            reading_direction="ltr",
            zoom_level=2.0,
            scroll_position=0.7
        )
        test_db.add(progress)
        await test_db.commit()
        await test_db.refresh(progress)
        
        response = await authenticated_client.get(f"/api/progress/{test_manga.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["manga_id"] == test_manga.id
        assert data["chapter_id"] == chapter.id
        assert data["page_number"] == 1
        assert data["reading_direction"] == "ltr"
        assert data["zoom_level"] == 2.0
        assert data["scroll_position"] == 0.7
    
    async def test_update_reading_progress_new(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test creating new reading progress."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        progress_data = {
            "chapter_id": chapter.id,
            "page_number": 3,
            "reading_direction": "ttb",
            "zoom_level": 1.2,
            "scroll_position": 0.5
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["manga_id"] == test_manga.id
        assert data["chapter_id"] == chapter.id
        assert data["page_number"] == 3
        assert data["reading_direction"] == "ttb"
        assert data["zoom_level"] == 1.2
        assert data["scroll_position"] == 0.5
        assert "last_read_at" in data
    
    async def test_update_reading_progress_existing(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test updating existing reading progress."""
        # Create initial progress
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter1 = result.scalar_one()
        
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 2)
        )
        chapter2 = result.scalar_one()
        
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter1.id,
            page_number=1,
            reading_direction="rtl"
        )
        test_db.add(progress)
        await test_db.commit()
        
        # Update progress
        progress_data = {
            "chapter_id": chapter2.id,
            "page_number": 2,
            "reading_direction": "ltr",
            "zoom_level": 1.5,
            "scroll_position": 0.8
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["manga_id"] == test_manga.id
        assert data["chapter_id"] == chapter2.id
        assert data["page_number"] == 2
        assert data["reading_direction"] == "ltr"
        assert data["zoom_level"] == 1.5
        assert data["scroll_position"] == 0.8
    
    async def test_update_progress_invalid_chapter(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga
    ):
        """Test updating progress with invalid chapter ID."""
        progress_data = {
            "chapter_id": 99999,
            "page_number": 1,
            "reading_direction": "rtl"
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 400
        assert "Chapter not found or does not belong to this manga" in response.json()["detail"]
    
    async def test_update_progress_chapter_wrong_manga(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test updating progress with chapter from different manga."""
        # Create another manga with a chapter
        other_manga = Manga(
            title="Other Manga",
            slug="other-manga",
            folder_path="/path/to/other",
            is_archive=False
        )
        test_db.add(other_manga)
        await test_db.commit()
        await test_db.refresh(other_manga)
        
        other_chapter = Chapter(
            manga_id=other_manga.id,
            title="Other Chapter",
            chapter_number=1,
            folder_name="Chapter 001",
            folder_path="/path/to/other/chapter1"
        )
        test_db.add(other_chapter)
        await test_db.commit()
        await test_db.refresh(other_chapter)
        
        # Try to update progress with chapter from different manga
        progress_data = {
            "chapter_id": other_chapter.id,
            "page_number": 1,
            "reading_direction": "rtl"
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 400
        assert "Chapter not found or does not belong to this manga" in response.json()["detail"]
    
    async def test_update_progress_invalid_data(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test updating progress with invalid data."""
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        # Invalid page number (negative)
        progress_data = {
            "chapter_id": chapter.id,
            "page_number": -1,
            "reading_direction": "rtl"
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_progress_missing_chapter_id(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga
    ):
        """Test updating progress without chapter_id."""
        progress_data = {
            "page_number": 1,
            "reading_direction": "rtl"
        }
        
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_delete_reading_progress(
        self, 
        authenticated_client: AsyncClient, 
        test_user: User, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test deleting reading progress."""
        # Create reading progress
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        progress = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=2
        )
        test_db.add(progress)
        await test_db.commit()
        
        # Delete progress
        response = await authenticated_client.delete(f"/api/progress/{test_manga.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully deleted" in data["message"]
        
        # Verify deletion
        response = await authenticated_client.get(f"/api/progress/{test_manga.id}")
        assert response.status_code == 200
        assert response.json() is None
    
    async def test_delete_progress_not_found(
        self, 
        authenticated_client: AsyncClient, 
        test_manga: Manga
    ):
        """Test deleting non-existent progress."""
        response = await authenticated_client.delete(f"/api/progress/{test_manga.id}")
        
        assert response.status_code == 404
        assert "No reading progress found" in response.json()["detail"]
    
    async def test_progress_user_isolation(
        self, 
        client: AsyncClient, 
        test_user: User, 
        test_user2: User, 
        test_manga: Manga, 
        test_db: AsyncSession
    ):
        """Test that users can only see their own reading progress."""
        from tests.conftest import create_access_token_for_user
        from sqlalchemy import select
        
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        # Create progress for user1
        progress1 = ReadingProgress(
            user_id=test_user.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=1
        )
        test_db.add(progress1)
        
        # Create progress for user2
        progress2 = ReadingProgress(
            user_id=test_user2.id,
            manga_id=test_manga.id,
            chapter_id=chapter.id,
            page_number=3
        )
        test_db.add(progress2)
        
        await test_db.commit()
        
        # User1 should only see their progress
        token1 = await create_access_token_for_user(test_user)
        client.headers.update({"Authorization": f"Bearer {token1}"})
        
        response = await client.get("/api/progress/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["page_number"] == 1
        
        # User2 should only see their progress
        token2 = await create_access_token_for_user(test_user2)
        client.headers.update({"Authorization": f"Bearer {token2}"})
        
        response = await client.get("/api/progress/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["page_number"] == 3
    
    async def test_progress_endpoints_unauthorized(self, client: AsyncClient, test_manga: Manga):
        """Test that progress endpoints require authentication."""
        endpoints = [
            "/api/progress/",
            f"/api/progress/{test_manga.id}",
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401
        
        # Test PUT and DELETE as well
        response = await client.put(f"/api/progress/{test_manga.id}", json={"chapter_id": 1, "page_number": 1})
        assert response.status_code == 401
        
        response = await client.delete(f"/api/progress/{test_manga.id}")
        assert response.status_code == 401