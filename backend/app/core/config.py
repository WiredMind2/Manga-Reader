from pydantic_settings import BaseSettings
from typing import List
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/manga_reader.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Manga
    MANGA_DIRECTORY: str = "./manga"
    IMAGE_CACHE_DIR: str = "./data/cache/images"
    
    # Image processing
    THUMBNAIL_SIZE: tuple = (300, 400)
    MAX_IMAGE_SIZE: tuple = (1920, 2560)
    SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp", "gif", "bmp"]
    SUPPORTED_ARCHIVE_FORMATS: List[str] = ["zip", "cbz", "rar", "cbr"]
    
    # Reading
    DEFAULT_READING_DIRECTION: str = "rtl"  # rtl, ttb, ltr
    
    # API
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # OCR/Translation with Ollama
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-vl:7b"
    OLLAMA_TIMEOUT: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_from_config_file()

    def _load_from_config_file(self):
        """Load settings from config file if it exists"""
        # Try to find config file relative to project root
        # backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> root
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3]
        config_path = project_root / "config" / "settings.json"
        
        if not config_path.exists():
             # Fallback to CWD
             config_path = Path("config/settings.json")

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Map config file keys to class attributes
                mapping = {
                    "database_url": "DATABASE_URL",
                    "secret_key": "SECRET_KEY", 
                    "algorithm": "ALGORITHM",
                    "access_token_expire_minutes": "ACCESS_TOKEN_EXPIRE_MINUTES",
                    "manga_directory": "MANGA_DIRECTORY",
                    "image_cache_dir": "IMAGE_CACHE_DIR",
                    "thumbnail_size": "THUMBNAIL_SIZE",
                    "max_image_size": "MAX_IMAGE_SIZE",
                    "supported_image_formats": "SUPPORTED_IMAGE_FORMATS",
                    "supported_archive_formats": "SUPPORTED_ARCHIVE_FORMATS",
                    "default_reading_direction": "DEFAULT_READING_DIRECTION",
                    "cors_origins": "CORS_ORIGINS",
                    "pagination.default_page_size": "DEFAULT_PAGE_SIZE",
                    "pagination.max_page_size": "MAX_PAGE_SIZE",
                    "ollama.enabled": "OLLAMA_ENABLED",
                    "ollama.base_url": "OLLAMA_BASE_URL",
                    "ollama.model": "OLLAMA_MODEL",
                    "ollama.timeout": "OLLAMA_TIMEOUT"
                }
                
                for config_key, attr_name in mapping.items():
                    if "." in config_key:
                        # Handle nested keys like pagination.default_page_size
                        keys = config_key.split(".")
                        value = config_data
                        for key in keys:
                            if key in value:
                                value = value[key]
                            else:
                                value = None
                                break
                    else:
                        value = config_data.get(config_key)
                    
                    if value is not None:
                        setattr(self, attr_name, value)
                        
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                logger.error(f"Warning: Could not load config file: {e}")
        else:
            logger.warning(f"Config file not found at {config_path}")


settings = Settings()