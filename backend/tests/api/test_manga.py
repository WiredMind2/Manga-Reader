import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.models import User, Manga, Chapter
from tests.conftest import assert_manga_response, assert_chapter_response


@pytest.mark.manga
@pytest.mark.asyncio
class TestMangaEndpoints:
    """Test manga-related endpoints."""
    
    async def test_scan_manga_library(self, authenticated_client: AsyncClient, temp_manga_dir: Path):
        """Test manga library scanning."""
        response = await authenticated_client.get("/api/manga/scan")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "manga_count" in data
        assert isinstance(data["manga_count"], int)
    
    async def test_list_manga_empty(self, authenticated_client: AsyncClient):
        """Test listing manga when none exist."""
        response = await authenticated_client.get("/api/manga/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 0
    
    async def test_list_manga_with_data(self, authenticated_client: AsyncClient, test_manga: Manga):
        """Test listing manga with existing data."""
        response = await authenticated_client.get("/api/manga/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1
        
        manga_data = data["items"][0]
        assert_manga_response(manga_data, test_manga)
    
    async def test_list_manga_pagination(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Test manga list pagination."""
        # Create multiple manga
        for i in range(5):
            manga = Manga(
                title=f"Test Manga {i+1}",
                slug=f"test-manga-{i+1}",
                folder_path=f"/path/to/manga{i+1}",
                is_archive=False
            )
            test_db.add(manga)
        await test_db.commit()
        
        # Test first page with size 2
        response = await authenticated_client.get("/api/manga/?page=1&size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["pages"] == 3
        
        # Test second page
        response = await authenticated_client.get("/api/manga/?page=2&size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
    
    async def test_list_manga_search(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Test manga search functionality."""
        # Create manga with different titles
        manga1 = Manga(title="One Piece", slug="one-piece", folder_path="/path1", is_archive=False)
        manga2 = Manga(title="Naruto", slug="naruto", folder_path="/path2", is_archive=False)
        manga3 = Manga(title="One Punch Man", slug="one-punch-man", folder_path="/path3", is_archive=False)
        
        test_db.add_all([manga1, manga2, manga3])
        await test_db.commit()
        
        # Search for "One"
        response = await authenticated_client.get("/api/manga/?search=One")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # One Piece and One Punch Man
        assert data["total"] == 2
        
        titles = [item["title"] for item in data["items"]]
        assert "One Piece" in titles
        assert "One Punch Man" in titles
        assert "Naruto" not in titles
    
    async def test_list_manga_sorting(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Test manga list sorting."""
        # Create manga with different titles
        manga1 = Manga(title="Zebra Manga", slug="zebra-manga", folder_path="/path1", is_archive=False)
        manga2 = Manga(title="Alpha Manga", slug="alpha-manga", folder_path="/path2", is_archive=False)
        manga3 = Manga(title="Beta Manga", slug="beta-manga", folder_path="/path3", is_archive=False)
        
        test_db.add_all([manga1, manga2, manga3])
        await test_db.commit()
        
        # Test ascending sort by title (default)
        response = await authenticated_client.get("/api/manga/?sort_by=title&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == ["Alpha Manga", "Beta Manga", "Zebra Manga"]
        
        # Test descending sort by title
        response = await authenticated_client.get("/api/manga/?sort_by=title&sort_order=desc")
        
        assert response.status_code == 200
        data = response.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == ["Zebra Manga", "Beta Manga", "Alpha Manga"]
    
    async def test_list_manga_invalid_sort(self, authenticated_client: AsyncClient):
        """Test manga list with invalid sort parameters."""
        response = await authenticated_client.get("/api/manga/?sort_by=invalid_field")
        
        assert response.status_code == 422  # Validation error
    
    async def test_list_manga_unauthorized(self, client: AsyncClient):
        """Test listing manga without authentication."""
        response = await client.get("/api/manga/")
        
        assert response.status_code == 401
    
    async def test_get_manga_details_success(self, authenticated_client: AsyncClient, test_manga: Manga):
        """Test getting manga details by ID."""
        response = await authenticated_client.get(f"/api/manga/{test_manga.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert_manga_response(data, test_manga)
        assert "folder_path" in data
        assert "is_archive" in data
        assert "genres" in data
        assert isinstance(data["genres"], list)
    
    async def test_get_manga_details_not_found(self, authenticated_client: AsyncClient):
        """Test getting details for non-existent manga."""
        response = await authenticated_client.get("/api/manga/99999")
        
        assert response.status_code == 404
        assert "Manga not found" in response.json()["detail"]
    
    async def test_get_manga_by_slug_success(self, authenticated_client: AsyncClient, test_manga: Manga):
        """Test getting manga by slug."""
        response = await authenticated_client.get(f"/api/manga/slug/{test_manga.slug}")
        
        assert response.status_code == 200
        data = response.json()
        assert_manga_response(data, test_manga)
    
    async def test_get_manga_by_slug_not_found(self, authenticated_client: AsyncClient):
        """Test getting manga by non-existent slug."""
        response = await authenticated_client.get("/api/manga/slug/non-existent-slug")
        
        assert response.status_code == 404
        assert "Manga not found" in response.json()["detail"]
    
    async def test_list_manga_chapters_success(self, authenticated_client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test listing chapters for a manga."""
        response = await authenticated_client.get(f"/api/manga/{test_manga.id}/chapters")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Test manga has 2 chapters
        
        # Verify chapters are ordered by chapter number
        assert data[0]["chapter_number"] == 1
        assert data[1]["chapter_number"] == 2
        
        for chapter_data in data:
            assert "id" in chapter_data
            assert "title" in chapter_data
            assert "chapter_number" in chapter_data
            assert "folder_name" in chapter_data
            assert "page_count" in chapter_data
            assert "created_at" in chapter_data
    
    async def test_list_manga_chapters_not_found(self, authenticated_client: AsyncClient):
        """Test listing chapters for non-existent manga."""
        response = await authenticated_client.get("/api/manga/99999/chapters")
        
        assert response.status_code == 404
        assert "Manga not found" in response.json()["detail"]
    
    async def test_list_chapter_pages_success(self, authenticated_client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test listing pages for a chapter."""
        # Get first chapter
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        response = await authenticated_client.get(f"/api/manga/{test_manga.id}/chapters/{chapter.id}/pages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # First chapter has 3 pages
        
        # Verify pages are ordered by page number
        assert data[0]["page_number"] == 1
        assert data[1]["page_number"] == 2
        assert data[2]["page_number"] == 3
        
        for page_data in data:
            assert "id" in page_data
            assert "page_number" in page_data
            assert "filename" in page_data
            assert "width" in page_data
            assert "height" in page_data
    
    async def test_list_chapter_pages_wrong_manga(self, authenticated_client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test listing pages with wrong manga ID."""
        # Get first chapter
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id, Chapter.chapter_number == 1)
        )
        chapter = result.scalar_one()
        
        # Use wrong manga ID
        wrong_manga_id = test_manga.id + 1000
        response = await authenticated_client.get(f"/api/manga/{wrong_manga_id}/chapters/{chapter.id}/pages")
        
        assert response.status_code == 404
        assert "Chapter not found" in response.json()["detail"]
    
    async def test_list_chapter_pages_not_found(self, authenticated_client: AsyncClient, test_manga: Manga):
        """Test listing pages for non-existent chapter."""
        response = await authenticated_client.get(f"/api/manga/{test_manga.id}/chapters/99999/pages")
        
        assert response.status_code == 404
        assert "Chapter not found" in response.json()["detail"]
    
    async def test_manga_endpoints_unauthorized(self, client: AsyncClient, test_manga: Manga):
        """Test that all manga endpoints require authentication."""
        endpoints = [
            f"/api/manga/{test_manga.id}",
            f"/api/manga/slug/{test_manga.slug}",
            f"/api/manga/{test_manga.id}/chapters",
            f"/api/manga/{test_manga.id}/chapters/1/pages",
            "/api/manga/scan"
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401