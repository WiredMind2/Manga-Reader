from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reading_progress = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")
    user_preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Manga(Base):
    __tablename__ = "manga"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    artist = Column(String(255), nullable=True)
    genres = Column(Text, nullable=True)  # JSON string of genres
    status = Column(String(50), nullable=True)  # ongoing, completed, hiatus
    year = Column(Integer, nullable=True)
    cover_image = Column(String(500), nullable=True)  # Path to cover image
    folder_path = Column(String(1000), nullable=False)  # Absolute path to manga folder
    is_archive = Column(Boolean, default=False)  # True if it's a compressed archive
    total_chapters = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chapters = relationship("Chapter", back_populates="manga", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="manga", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    title = Column(String(255), nullable=False)
    chapter_number = Column(Float, nullable=False)  # Allows for 1.5, 2.1 etc
    folder_name = Column(String(255), nullable=False)  # Original folder/archive name
    folder_path = Column(String(1000), nullable=False)  # Path to chapter folder/archive
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    manga = relationship("Manga", back_populates="chapters")
    pages = relationship("Page", back_populates="chapter", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)  # Full path to image file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Relationships  
    chapter = relationship("Chapter", back_populates="pages")


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    page_number = Column(Integer, default=1)  # Current page in the chapter
    last_read_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reading_direction = Column(String(10), default="rtl")  # rtl, ltr, ttb
    zoom_level = Column(Float, default=1.0)
    scroll_position = Column(Float, default=0.0)  # For vertical scrolling modes
    
    # Relationships
    user = relationship("User", back_populates="reading_progress")
    manga = relationship("Manga", back_populates="reading_progress")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    default_reading_direction = Column(String(10), default="rtl")
    auto_next_chapter = Column(Boolean, default=True)
    page_fit_mode = Column(String(20), default="fit-width")  # fit-width, fit-height, original
    theme = Column(String(20), default="dark")  # dark, light, auto
    items_per_page = Column(Integer, default=20)
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")