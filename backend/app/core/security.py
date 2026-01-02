from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings
import hashlib
import secrets
import base64

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using PBKDF2"""
    try:
        # Extract salt and hash from stored password
        stored_hash, salt = hashed_password.split(':', 1)
        salt = base64.b64decode(salt.encode())
        
        # Hash the plain password with the same salt
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        computed_hash = base64.b64encode(pwd_hash).decode()
        
        return secrets.compare_digest(stored_hash, computed_hash)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2 with SHA-256"""
    # Generate a random salt
    salt = secrets.token_bytes(32)
    
    # Hash the password
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    # Encode and combine hash with salt
    hash_b64 = base64.b64encode(pwd_hash).decode()
    salt_b64 = base64.b64encode(salt).decode()
    
    return f"{hash_b64}:{salt_b64}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials", 
            headers={"WWW-Authenticate": "Bearer"},
        )