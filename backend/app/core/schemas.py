from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Manga schemas
class MangaBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    status: Optional[str] = None
    year: Optional[int] = None


class MangaResponse(MangaBase):
    id: int
    cover_image: Optional[str] = None
    total_chapters: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MangaDetail(MangaResponse):
    genres: List[str] = []
    folder_path: str
    is_archive: bool
    
    class Config:
        from_attributes = True


# Chapter schemas
class ChapterBase(BaseModel):
    title: str
    chapter_number: float
    folder_name: str


class ChapterResponse(ChapterBase):
    id: int
    page_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Page schemas
class PageBase(BaseModel):
    page_number: int
    filename: str


class PageResponse(PageBase):
    id: int
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        from_attributes = True


# Reading Progress schemas
class ReadingProgressUpdate(BaseModel):
    chapter_id: int
    page_number: int = Field(..., ge=1)
    reading_direction: Optional[str] = Field(None, pattern="^(rtl|ltr|ttb)$")
    zoom_level: Optional[float] = Field(None, ge=0.1, le=5.0)
    scroll_position: Optional[float] = Field(None, ge=0.0)


class ReadingProgressResponse(BaseModel):
    id: int
    manga_id: int
    chapter_id: Optional[int] = None
    page_number: int
    last_read_at: datetime
    reading_direction: str
    zoom_level: float
    scroll_position: float
    
    class Config:
        from_attributes = True


# Pagination schemas
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Manga schemas
class MangaBase(BaseModel):
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    status: Optional[str] = None
    year: Optional[int] = None


class MangaResponse(MangaBase):
    id: int
    slug: str
    cover_image: Optional[str] = None
    total_chapters: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MangaDetail(MangaResponse):
    genres: Optional[list] = None
    folder_path: str
    is_archive: bool


# Chapter schemas
class ChapterBase(BaseModel):
    title: str
    chapter_number: float


class ChapterResponse(ChapterBase):
    id: int
    folder_name: str
    page_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Page schemas  
class PageResponse(BaseModel):
    id: int
    page_number: int
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        from_attributes = True


# Progress schemas (duplicate removed - see line 102 for actual definition)


class ReadingProgressResponse(BaseModel):
    id: int
    manga_id: int
    chapter_id: Optional[int] = None
    page_number: int
    last_read_at: datetime
    reading_direction: str
    zoom_level: float
    scroll_position: float
    
    class Config:
        from_attributes = True


# User Preference schemas
class UserPreferenceUpdate(BaseModel):
    default_reading_direction: Optional[str] = Field(None, pattern="^(rtl|ltr|ttb)$")
    auto_next_chapter: Optional[bool] = None
    page_fit_mode: Optional[str] = Field(None, pattern="^(fit-width|fit-height|original)$") 
    theme: Optional[str] = Field(None, pattern="^(dark|light|auto)$")
    items_per_page: Optional[int] = Field(None, ge=5, le=100)
    ocr_enabled: Optional[bool] = None
    ocr_auto_translate: Optional[bool] = None
    ocr_source_language: Optional[str] = None
    ocr_target_language: Optional[str] = None


class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    default_reading_direction: str
    auto_next_chapter: bool
    page_fit_mode: str
    theme: str
    items_per_page: int
    ocr_enabled: bool
    ocr_auto_translate: bool
    ocr_source_language: str
    ocr_target_language: str
    
    class Config:
        from_attributes = True


# Pagination
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int