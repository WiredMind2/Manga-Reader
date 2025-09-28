import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from tests.conftest import create_access_token_for_user


@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    async def test_register_success(self, client: AsyncClient, test_db: AsyncSession):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Should not expose password
    
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with existing username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_invalid_data(self, client: AsyncClient):
        """Test registration with invalid data."""
        # Missing required fields
        response = await client.post("/api/auth/register", json={})
        assert response.status_code == 422
        
        # Invalid email format
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        response = await client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    async def test_login_token_success(self, client: AsyncClient, test_user: User):
        """Test successful login via token endpoint."""
        form_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        response = await client.post("/api/auth/token", data=form_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    
    async def test_login_json_success(self, client: AsyncClient, test_user: User):
        """Test successful login via JSON endpoint."""
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_inactive_user(self, client: AsyncClient, test_db: AsyncSession):
        """Test login with inactive user."""
        # Create inactive user
        from app.core.security import get_password_hash
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        test_db.add(inactive_user)
        await test_db.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Inactive user" in response.json()["detail"]
    
    async def test_get_current_user(self, authenticated_client: AsyncClient, test_user: User):
        """Test getting current user info."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert "hashed_password" not in data
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        client.headers.update({"Authorization": "Bearer invalid_token"})
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test logout endpoint."""
        response = await authenticated_client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out" in data["message"]
    
    async def test_logout_unauthorized(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post("/api/auth/logout")
        
        assert response.status_code == 401
    
    async def test_token_expiration_handling(self, client: AsyncClient, test_user: User):
        """Test handling of expired tokens."""
        from datetime import timedelta
        from app.core.security import create_access_token
        
        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user.username}, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        client.headers.update({"Authorization": f"Bearer {expired_token}"})
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]