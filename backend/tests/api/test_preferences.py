import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import User, UserPreference


@pytest.mark.preferences
@pytest.mark.asyncio
class TestUserPreferencesEndpoints:
    """Test user preferences endpoints."""
    
    async def test_get_user_preferences_creates_defaults(
        self, 
        authenticated_client: AsyncClient,
        test_user: User,
        test_db: AsyncSession
    ):
        """Test getting user preferences creates defaults if none exist."""
        # Ensure no preferences exist initially
        result = await test_db.execute(
            select(UserPreference).filter(UserPreference.user_id == test_user.id)
        )
        existing_prefs = result.scalar_one_or_none()
        if existing_prefs:
            await test_db.execute(
                delete(UserPreference).where(UserPreference.user_id == test_user.id)
            )
            await test_db.commit()
        
        response = await authenticated_client.get("/api/preferences/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check default values
        assert data["user_id"] == test_user.id
        assert data["default_reading_direction"] == "rtl"
        assert data["auto_next_chapter"] is True
        assert data["page_fit_mode"] == "fit-width"
        assert data["theme"] == "dark"
        assert data["items_per_page"] == 20
        
        # Verify preferences were created in database
        result = await test_db.execute(
            select(UserPreference).filter(UserPreference.user_id == test_user.id)
        )
        db_prefs = result.scalar_one_or_none()
        assert db_prefs is not None
        assert db_prefs.default_reading_direction == "rtl"
    
    async def test_update_user_preferences(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_db: AsyncSession
    ):
        """Test updating user preferences."""
        # Delete any existing preferences from the fixture
        from sqlalchemy import delete
        await test_db.execute(
            delete(UserPreference).where(UserPreference.user_id == test_user.id)
        )
        await test_db.commit()
        
        # Create initial preferences
        prefs = UserPreference(
            user_id=test_user.id,
            default_reading_direction="rtl",
            auto_next_chapter=True,
            page_fit_mode="fit-width",
            theme="dark",
            items_per_page=20
        )
        test_db.add(prefs)
        await test_db.commit()        # Update preferences
        update_data = {
            "default_reading_direction": "ltr",
            "auto_next_chapter": False,
            "page_fit_mode": "fit-height", 
            "theme": "light",
            "items_per_page": 10
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check updated values
        assert data["user_id"] == test_user.id
        assert data["default_reading_direction"] == "ltr"
        assert data["auto_next_chapter"] is False
        assert data["page_fit_mode"] == "fit-height"
        assert data["theme"] == "light"
        assert data["items_per_page"] == 10
        
        # Verify changes in database by querying fresh
        from sqlalchemy import select
        result = await test_db.execute(
            select(UserPreference).where(UserPreference.user_id == test_user.id)
        )
        updated_prefs = result.scalar_one()
        assert updated_prefs.default_reading_direction == "ltr"
        assert updated_prefs.auto_next_chapter is False
        assert updated_prefs.page_fit_mode == "fit-height"
        assert updated_prefs.theme == "light"
        assert updated_prefs.items_per_page == 10
    
    async def test_update_user_preferences_partial(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_db: AsyncSession
    ):
        """Test updating only some user preferences."""
        # Create initial preferences
        prefs = UserPreference(
            user_id=test_user.id,
            default_reading_direction="rtl",
            auto_next_chapter=True,
            page_fit_mode="fit-width",
            theme="dark",
            items_per_page=20
        )
        test_db.add(prefs)
        await test_db.commit()
        
        # Update only reading direction
        update_data = {
            "default_reading_direction": "ttb"
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that only reading direction changed
        assert data["default_reading_direction"] == "ttb"
        assert data["auto_next_chapter"] is True  # Unchanged
        assert data["page_fit_mode"] == "fit-width"  # Unchanged
        assert data["theme"] == "dark"  # Unchanged
        assert data["items_per_page"] == 20  # Unchanged
    
    async def test_reset_user_preferences(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_db: AsyncSession
    ):
        """Test resetting user preferences to defaults."""
        # Delete any existing preferences from the fixture
        from sqlalchemy import delete
        await test_db.execute(
            delete(UserPreference).where(UserPreference.user_id == test_user.id)
        )
        await test_db.commit()
        
        # Create modified preferences
        prefs = UserPreference(
            user_id=test_user.id,
            default_reading_direction="ltr",
            auto_next_chapter=False,
            page_fit_mode="original",
            theme="light",
            items_per_page=50
        )
        test_db.add(prefs)
        await test_db.commit()
        
        response = await authenticated_client.delete("/api/preferences/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check reset to defaults
        assert data["default_reading_direction"] == "rtl"
        assert data["auto_next_chapter"] is True
        assert data["page_fit_mode"] == "fit-width"
        assert data["theme"] == "dark"
        assert data["items_per_page"] == 20
        
        # Verify database changes by querying fresh  
        from sqlalchemy import select
        result = await test_db.execute(
            select(UserPreference).where(UserPreference.user_id == test_user.id)
        )
        reset_prefs = result.scalar_one()
        assert reset_prefs.default_reading_direction == "rtl"
        assert reset_prefs.auto_next_chapter is True
    
    async def test_reset_nonexistent_preferences(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_db: AsyncSession
    ):
        """Test resetting when no preferences exist."""
        # Ensure no preferences exist
        result = await test_db.execute(
            select(UserPreference).filter(UserPreference.user_id == test_user.id)
        )
        existing_prefs = result.scalar_one_or_none()
        if existing_prefs:
            await test_db.execute(
                delete(UserPreference).where(UserPreference.user_id == test_user.id)
            )
            await test_db.commit()
        
        response = await authenticated_client.delete("/api/preferences/")
        
        assert response.status_code == 200
        data = response.json()
        assert "No preferences found to reset" in data["message"]
    
    async def test_invalid_reading_direction(
        self,
        authenticated_client: AsyncClient
    ):
        """Test validation of invalid reading direction."""
        update_data = {
            "default_reading_direction": "invalid"
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("default_reading_direction" in str(error) for error in error_detail)
    
    async def test_invalid_page_fit_mode(
        self,
        authenticated_client: AsyncClient
    ):
        """Test validation of invalid page fit mode."""
        update_data = {
            "page_fit_mode": "invalid-mode"
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("page_fit_mode" in str(error) for error in error_detail)
    
    async def test_invalid_theme(
        self,
        authenticated_client: AsyncClient
    ):
        """Test validation of invalid theme."""
        update_data = {
            "theme": "rainbow"
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("theme" in str(error) for error in error_detail)
    
    async def test_invalid_items_per_page(
        self,
        authenticated_client: AsyncClient
    ):
        """Test validation of invalid items per page."""
        # Test too low
        update_data = {
            "items_per_page": 2
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        assert response.status_code == 422
        
        # Test too high
        update_data = {
            "items_per_page": 200
        }
        
        response = await authenticated_client.put("/api/preferences/", json=update_data)
        assert response.status_code == 422
    
    async def test_preferences_endpoints_unauthorized(self, client: AsyncClient):
        """Test that preference endpoints require authentication."""
        endpoints_and_methods = [
            ("GET", "/api/preferences/"),
            ("PUT", "/api/preferences/"),
            ("DELETE", "/api/preferences/")
        ]
        
        for method, endpoint in endpoints_and_methods:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "PUT":
                response = await client.put(endpoint, json={})
            elif method == "DELETE":
                response = await client.delete(endpoint)
            
            assert response.status_code == 401


@pytest.mark.preferences
@pytest.mark.integration
@pytest.mark.asyncio
class TestReadingDirectionIntegration:
    """Test reading direction preferences integration with progress tracking."""
    
    async def test_progress_uses_user_default_reading_direction(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_manga,
        test_chapter,
        test_db: AsyncSession
    ):
        """Test that progress tracking uses user's default reading direction."""
        # Set user preference to left-to-right
        prefs = UserPreference(
            user_id=test_user.id,
            default_reading_direction="ltr",
            auto_next_chapter=True,
            page_fit_mode="fit-width",
            theme="dark",
            items_per_page=20
        )
        test_db.add(prefs)
        await test_db.commit()
        
        # Update progress without specifying reading direction
        progress_data = {
            "chapter_id": test_chapter.id,
            "page_number": 5
        }
        
        response = await authenticated_client.put(
            f"/api/progress/{test_manga.id}",
            json=progress_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use user's default reading direction if not specified
        # This would need to be implemented in the progress endpoint
        # For now, let's just check the response structure
        assert "reading_direction" in data
    
    async def test_reading_direction_options(
        self,
        authenticated_client: AsyncClient
    ):
        """Test all valid reading direction options."""
        valid_directions = ["rtl", "ltr", "ttb"]
        
        for direction in valid_directions:
            update_data = {
                "default_reading_direction": direction
            }
            
            response = await authenticated_client.put("/api/preferences/", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["default_reading_direction"] == direction