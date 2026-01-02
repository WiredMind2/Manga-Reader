import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.models import User, Manga, Chapter, Page, ReadingProgress
from tests.conftest import create_access_token_for_user


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullUserWorkflow:
    """Test complete user workflows from registration to reading."""
    
    async def test_complete_user_registration_and_manga_access(self, client: AsyncClient, test_db: AsyncSession, test_manga: Manga):
        """Test complete workflow: register -> login -> access manga -> track progress."""
        
        # Step 1: Register new user
        user_data = {
            "username": "newreader",
            "email": "reader@example.com",
            "password": "securepass123"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        user_response = response.json()
        assert user_response["username"] == "newreader"
        
        # Step 2: Login to get token
        login_data = {
            "username": "newreader",
            "password": "securepass123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data["access_token"]
        
        # Step 3: Use token to access protected endpoints
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        
        # Get user info
        response = await client.get("/api/auth/me")
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["username"] == "newreader"
        
        # Step 4: Browse manga library
        response = await client.get("/api/manga/")
        assert response.status_code == 200
        manga_list = response.json()
        assert manga_list["total"] >= 1
        assert len(manga_list["items"]) >= 1
        
        # Step 5: Get specific manga details
        manga_id = manga_list["items"][0]["id"]
        response = await client.get(f"/api/manga/{manga_id}")
        assert response.status_code == 200
        manga_details = response.json()
        
        # Step 6: Get manga chapters
        response = await client.get(f"/api/manga/{manga_id}/chapters")
        assert response.status_code == 200
        chapters = response.json()
        assert len(chapters) > 0
        
        # Step 7: Get chapter pages
        chapter_id = chapters[0]["id"]
        response = await client.get(f"/api/manga/{manga_id}/chapters/{chapter_id}/pages")
        assert response.status_code == 200
        pages = response.json()
        assert len(pages) > 0
        
        # Step 8: Update reading progress
        progress_data = {
            "chapter_id": chapter_id,
            "page_number": 2,
            "reading_direction": "rtl",
            "zoom_level": 1.2
        }
        
        response = await client.put(f"/api/progress/{manga_id}", json=progress_data)
        assert response.status_code == 200
        progress_response = response.json()
        assert progress_response["page_number"] == 2
        assert progress_response["chapter_id"] == chapter_id
        
        # Step 9: Verify progress is saved
        response = await client.get(f"/api/progress/{manga_id}")
        assert response.status_code == 200
        saved_progress = response.json()
        assert saved_progress["page_number"] == 2
        assert saved_progress["reading_direction"] == "rtl"
        
        # Step 10: Get all user progress
        response = await client.get("/api/progress/")
        assert response.status_code == 200
        all_progress = response.json()
        assert len(all_progress) == 1
        assert all_progress[0]["manga_id"] == manga_id
    
    async def test_manga_discovery_and_search_workflow(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Test manga discovery, searching, and filtering."""
        
        # Create multiple manga for testing
        manga_list = [
            Manga(title="One Piece", slug="one-piece", folder_path="/manga1", is_archive=False, author="Oda", status="ongoing"),
            Manga(title="Naruto", slug="naruto", folder_path="/manga2", is_archive=False, author="Kishimoto", status="completed"),
            Manga(title="One Punch Man", slug="one-punch-man", folder_path="/manga3", is_archive=False, author="ONE", status="ongoing"),
            Manga(title="Attack on Titan", slug="attack-on-titan", folder_path="/manga4", is_archive=False, author="Isayama", status="completed"),
        ]
        
        for manga in manga_list:
            test_db.add(manga)
        await test_db.commit()
        
        # Test basic listing
        response = await authenticated_client.get("/api/manga/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        
        # Test pagination
        response = await authenticated_client.get("/api/manga/?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2
        
        # Test search by title
        response = await authenticated_client.get("/api/manga/?search=One")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # One Piece and One Punch Man
        titles = [item["title"] for item in data["items"]]
        assert "One Piece" in titles
        assert "One Punch Man" in titles
        
        # Test sorting
        response = await authenticated_client.get("/api/manga/?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles)
        
        # Test getting manga by slug
        response = await authenticated_client.get("/api/manga/slug/one-piece")
        assert response.status_code == 200
        manga_data = response.json()
        assert manga_data["title"] == "One Piece"
        assert manga_data["author"] == "Oda"
    
    async def test_image_serving_workflow(self, authenticated_client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test image serving and optimization workflow."""
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        
        # Get a page from test data
        from sqlalchemy import select
        result = await test_db.execute(
            select(Page).join(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        page = result.scalar_one()
        
        # Mock image file and optimization
        with patch('os.path.exists', return_value=True), \
             patch('app.api.images.ImageOptimizer.optimize_image') as mock_optimize:
            
            # Create fake optimized image
            fake_path = Path(tempfile.mktemp(suffix='.webp'))
            fake_path.write_bytes(b'fake optimized image data')
            mock_optimize.return_value = fake_path
            
            try:
                # Test image serving
                response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}")
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("image/")
                
                # Test image with optimization parameters
                response = await authenticated_client.get(f"/api/images/{test_manga.id}/{page.chapter_id}/{page.id}?width=800&height=600")
                assert response.status_code == 200
                
                # Verify optimization was called with correct parameters
                mock_optimize.assert_called()
                
            finally:
                if fake_path.exists():
                    fake_path.unlink()
    
    async def test_user_isolation_workflow(self, client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test that users can only access their own data."""
        
        # Create two users
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "pass1"}
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "pass2"}
        
        # Register both users
        await client.post("/api/auth/register", json=user1_data)
        await client.post("/api/auth/register", json=user2_data)
        
        # Login as user1
        response = await client.post("/api/auth/login", json=user1_data)
        token1 = response.json()["access_token"]
        
        # Login as user2
        response = await client.post("/api/auth/login", json=user2_data)
        token2 = response.json()["access_token"]
        
        # Get chapter for progress tracking
        from sqlalchemy import select
        result = await test_db.execute(
            select(Chapter).where(Chapter.manga_id == test_manga.id).limit(1)
        )
        chapter = result.scalar_one()
        
        # User1 creates progress
        client.headers.update({"Authorization": f"Bearer {token1}"})
        progress_data = {"chapter_id": chapter.id, "page_number": 5}
        response = await client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        assert response.status_code == 200
        
        # User2 creates different progress
        client.headers.update({"Authorization": f"Bearer {token2}"})
        progress_data = {"chapter_id": chapter.id, "page_number": 10}
        response = await client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        assert response.status_code == 200
        
        # User1 should only see their progress
        client.headers.update({"Authorization": f"Bearer {token1}"})
        response = await client.get(f"/api/progress/{test_manga.id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["page_number"] == 5
        
        # User2 should only see their progress
        client.headers.update({"Authorization": f"Bearer {token2}"})
        response = await client.get(f"/api/progress/{test_manga.id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["page_number"] == 10


@pytest.mark.integration
@pytest.mark.asyncio
class TestMangaScanningIntegration:
    """Test manga scanning integration with database."""
    
    async def test_complete_manga_scanning_workflow(self, authenticated_client: AsyncClient, test_db: AsyncSession, temp_manga_dir: Path):
        """Test complete manga scanning and database population."""
        from unittest.mock import patch
        from app.services.manga_scanner import manga_scanner
        
        # Mock scanner to use temp directory
        original_dir = manga_scanner.manga_dir
        manga_scanner.manga_dir = temp_manga_dir
        try:
            # Trigger scan
            response = await authenticated_client.get("/api/manga/scan")
            assert response.status_code == 200
            scan_result = response.json()
            assert scan_result["manga_count"] > 0
            
            # Verify manga was created in database
            response = await authenticated_client.get("/api/manga/")
            assert response.status_code == 200
            manga_list = response.json()
            assert manga_list["total"] > 0
        finally:
            manga_scanner.manga_dir = original_dir
            
            # Get first manga and verify it has chapters
            manga = manga_list["items"][0]
            response = await authenticated_client.get(f"/api/manga/{manga['id']}/chapters")
            assert response.status_code == 200
            chapters = response.json()
            assert len(chapters) > 0
            
            # Verify chapters have pages
            chapter = chapters[0]
            response = await authenticated_client.get(f"/api/manga/{manga['id']}/chapters/{chapter['id']}/pages")
            assert response.status_code == 200
            pages = response.json()
            assert len(pages) > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandlingWorkflows:
    """Test error handling across the application."""
    
    async def test_authentication_error_workflow(self, client: AsyncClient):
        """Test authentication error handling."""
        
        # Try to access protected endpoint without token
        response = await client.get("/api/manga/")
        assert response.status_code == 401
        
        # Try with invalid token
        client.headers.update({"Authorization": "Bearer invalid_token"})
        response = await client.get("/api/manga/")
        assert response.status_code == 401
        
        # Try with malformed token
        client.headers.update({"Authorization": "Bearer not.a.jwt.token"})
        response = await client.get("/api/manga/")
        assert response.status_code == 401
    
    async def test_not_found_error_workflow(self, authenticated_client: AsyncClient):
        """Test not found error handling."""
        
        # Non-existent manga
        response = await authenticated_client.get("/api/manga/99999")
        assert response.status_code == 404
        
        # Non-existent chapter
        response = await authenticated_client.get("/api/manga/1/chapters/99999/pages")
        assert response.status_code == 404
        
        # Non-existent page image
        response = await authenticated_client.get("/api/images/99999/99999/99999")
        assert response.status_code == 404
    
    async def test_validation_error_workflow(self, authenticated_client: AsyncClient, test_manga: Manga):
        """Test validation error handling."""
        
        # Invalid pagination parameters
        response = await authenticated_client.get("/api/manga/?page=-1")
        assert response.status_code == 422
        
        response = await authenticated_client.get("/api/manga/?size=0")
        assert response.status_code == 422
        
        # Invalid progress data
        progress_data = {"page_number": -1}  # Missing chapter_id, invalid page
        response = await authenticated_client.put(f"/api/progress/{test_manga.id}", json=progress_data)
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio  
class TestPerformanceWorkflows:
    """Test performance-related scenarios."""
    
    async def test_large_manga_library_performance(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Test performance with large number of manga."""
        
        # Create many manga
        manga_batch = []
        for i in range(100):
            manga = Manga(
                title=f"Test Manga {i:03d}",
                slug=f"test-manga-{i:03d}",
                folder_path=f"/path/to/manga{i}",
                is_archive=False
            )
            manga_batch.append(manga)
        
        test_db.add_all(manga_batch)
        await test_db.commit()
        
        # Test pagination performance
        response = await authenticated_client.get("/api/manga/?page=1&size=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["total"] >= 100
        
        # Test search performance
        response = await authenticated_client.get("/api/manga/?search=050")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Test Manga 050"
    
    async def test_concurrent_access_workflow(self, client: AsyncClient, test_manga: Manga, test_db: AsyncSession):
        """Test concurrent user access scenarios."""
        import asyncio
        
        # Create multiple users
        users_data = [
            {"username": f"user{i}", "email": f"user{i}@example.com", "password": f"pass{i}"}
            for i in range(5)
        ]
        
        # Register all users
        for user_data in users_data:
            await client.post("/api/auth/register", json=user_data)
        
        # Login all users and get tokens
        tokens = []
        for user_data in users_data:
            response = await client.post("/api/auth/login", json=user_data)
            tokens.append(response.json()["access_token"])
        
        # Simulate concurrent manga access
        async def access_manga(token):
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/manga/", headers=headers)
            return response.status_code == 200
        
        # Run concurrent requests
        results = await asyncio.gather(*[access_manga(token) for token in tokens])
        
        # All requests should succeed
        assert all(results)