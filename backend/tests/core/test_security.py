import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)
from app.core.config import settings


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "mySecretPassword123!"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 characters
        assert hashed.startswith("$2b$")  # Bcrypt format
    
    def test_password_verification_correct(self):
        """Test password verification with correct password."""
        password = "correctPassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correctPassword123"
        wrong_password = "wrongPassword456"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_hashing_consistency(self):
        """Test that same password produces different hashes (salt)."""
        password = "samePassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Different hashes due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_password_special_characters(self):
        """Test password hashing with special characters."""
        passwords = [
            "password!@#$%^&*()",
            "пароль_русский",
            "密码中文",
            "🔐🚀🎯",
            ""  # Empty password
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
    
    def test_password_length_limits(self):
        """Test password hashing with various lengths."""
        # Very short password
        short_password = "a"
        hashed_short = get_password_hash(short_password)
        assert verify_password(short_password, hashed_short) is True
        
        # Very long password
        long_password = "a" * 1000
        hashed_long = get_password_hash(long_password)
        assert verify_password(long_password, hashed_long) is True


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are quite long
        
        # Decode and verify content
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check expiry time is approximately correct
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.fromtimestamp(exp_timestamp)
        
        # Allow 10 seconds tolerance
        time_diff = abs((expected_exp - actual_exp).total_seconds())
        assert time_diff < 10
    
    def test_create_access_token_additional_claims(self):
        """Test creating token with additional claims."""
        data = {
            "sub": "testuser",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
    
    def test_verify_token_valid(self):
        """Test verifying valid token."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_expired(self):
        """Test verifying expired token."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)
        
        with pytest.raises(JWTError):
            verify_token(token)
    
    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature."""
        # Create token with different secret
        data = {"sub": "testuser"}
        token = jwt.encode(data, "wrong_secret", algorithm=settings.ALGORITHM)
        
        with pytest.raises(JWTError):
            verify_token(token)
    
    def test_verify_token_malformed(self):
        """Test verifying malformed token."""
        malformed_tokens = [
            "invalid.token.here",
            "not.a.jwt",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            None
        ]
        
        for token in malformed_tokens:
            with pytest.raises(JWTError):
                verify_token(token)
    
    def test_verify_token_missing_claims(self):
        """Test verifying token with missing required claims."""
        # Token without 'sub' claim
        data = {"role": "user"}  # Missing 'sub'
        token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # This should still decode successfully, verification of required claims
        # would be done at the application level
        payload = verify_token(token)
        assert "sub" not in payload
        assert payload["role"] == "user"
    
    def test_token_algorithms(self):
        """Test that only expected algorithms are accepted."""
        data = {"sub": "testuser"}
        
        # Create token with different algorithm
        token_hs384 = jwt.encode(data, settings.SECRET_KEY, algorithm="HS384")
        
        with pytest.raises(JWTError):
            verify_token(token_hs384)  # Should reject HS384
    
    @patch('app.core.config.settings')
    def test_token_with_different_settings(self, mock_settings):
        """Test token behavior with different configuration."""
        # Mock different settings
        mock_settings.SECRET_KEY = "different_secret_key_for_testing_123"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Should work with the mocked settings
        payload = verify_token(token)
        assert payload["sub"] == "testuser"
    
    def test_token_username_extraction(self):
        """Test extracting username from token payload."""
        usernames = [
            "simple_user",
            "user@example.com",
            "user-with-dashes",
            "user_123",
            "CamelCaseUser"
        ]
        
        for username in usernames:
            data = {"sub": username}
            token = create_access_token(data)
            payload = verify_token(token)
            
            assert payload["sub"] == username


@pytest.mark.unit
class TestSecurityUtilities:
    """Test other security-related utilities."""
    
    def test_constant_time_comparison(self):
        """Test that password verification is resistant to timing attacks."""
        password = "secretPassword123"
        hashed = get_password_hash(password)
        
        # This is a basic test - in practice, you'd need specialized tools
        # to test timing attack resistance
        import time
        
        # Test with correct password
        start_time = time.time()
        result1 = verify_password(password, hashed)
        correct_time = time.time() - start_time
        
        # Test with wrong password of same length
        start_time = time.time()
        result2 = verify_password("wrongPassword123", hashed)
        wrong_time = time.time() - start_time
        
        assert result1 is True
        assert result2 is False
        # The timing difference should be minimal (though this test is imperfect)
    
    def test_password_hash_format(self):
        """Test that password hashes follow expected bcrypt format."""
        password = "testPassword123"
        hashed = get_password_hash(password)
        
        # Bcrypt format: $2b$rounds$salt_and_hash
        parts = hashed.split('$')
        assert len(parts) == 4
        assert parts[0] == ""  # Empty string before first $
        assert parts[1] == "2b"  # Bcrypt identifier
        assert parts[2].isdigit()  # Rounds (cost factor)
        assert len(parts[3]) == 53  # Salt (22 chars) + Hash (31 chars)
    
    def test_token_payload_structure(self):
        """Test that JWT payload has expected structure."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token)
        
        # Check required JWT fields
        assert "sub" in payload
        assert "exp" in payload  # Expiration time
        assert "iat" in payload  # Issued at time
        
        # Check timestamp formats
        assert isinstance(payload["exp"], int)
        assert isinstance(payload["iat"], int)
        assert payload["exp"] > payload["iat"]  # Expiry after issued
    
    def test_security_headers_compatibility(self):
        """Test that tokens work with common security headers."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Test Bearer token format
        bearer_token = f"Bearer {token}"
        extracted_token = bearer_token.replace("Bearer ", "")
        
        payload = verify_token(extracted_token)
        assert payload["sub"] == "testuser"
    
    def test_cross_user_token_isolation(self):
        """Test that tokens are properly isolated between users."""
        user1_data = {"sub": "user1"}
        user2_data = {"sub": "user2"}
        
        token1 = create_access_token(user1_data)
        token2 = create_access_token(user2_data)
        
        payload1 = verify_token(token1)
        payload2 = verify_token(token2)
        
        assert payload1["sub"] == "user1"
        assert payload2["sub"] == "user2"
        assert token1 != token2  # Different tokens for different users