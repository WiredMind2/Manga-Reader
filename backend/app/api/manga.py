from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import json
import zipfile
import rarfile
from pathlib import Path

from app.core.database import get_db
from app.core.schemas import MangaResponse, MangaDetail, ChapterResponse, PageResponse, PaginatedResponse
from app.models import Manga, Chapter, Page, User
from app.api.auth import get_current_user
from app.services.manga_scanner import manga_scanner
from app.core.config import settings

router = APIRouter()


@router.get("/scan")
async def scan_manga_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scan the manga directory and update database"""
    manga_list = await manga_scanner.scan_manga_directory(db)
    return {
        "message": f"Scanned {len(manga_list)} manga series",
        "manga_count": len(manga_list)
    }


@router.get("/", response_model=PaginatedResponse)
async def list_manga(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("title", regex="^(title|created_at|updated_at|total_chapters)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of manga"""
    query = select(Manga)
    
    # Apply search filter
    if search:
        query = query.where(Manga.title.ilike(f"%{search}%"))
    
    # Apply sorting
    sort_column = getattr(Manga, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Get total count
    count_query = select(func.count(Manga.id))
    if search:
        count_query = count_query.where(Manga.title.ilike(f"%{search}%"))
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    result = await db.execute(query)
    manga_list = result.scalars().all()
    
    # Convert to response models
    manga_responses = []
    for manga in manga_list:
        manga_dict = {
            "id": manga.id,
            "title": manga.title,
            "slug": manga.slug,
            "description": manga.description,
            "author": manga.author,
            "artist": manga.artist,
            "status": manga.status,
            "year": manga.year,
            "cover_image": manga.cover_image,
            "total_chapters": manga.total_chapters,
            "created_at": manga.created_at
        }
        manga_responses.append(manga_dict)
    
    return PaginatedResponse(
        items=manga_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{manga_id}", response_model=MangaDetail)
async def get_manga_details(
    manga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed manga information"""
    result = await db.execute(select(Manga).where(Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Parse genres from JSON string
    genres = []
    if manga.genres:
        try:
            genres = json.loads(manga.genres)
        except json.JSONDecodeError:
            genres = []
    
    return MangaDetail(
        id=manga.id,
        title=manga.title,
        slug=manga.slug,
        description=manga.description,
        author=manga.author,
        artist=manga.artist,
        status=manga.status,
        year=manga.year,
        cover_image=manga.cover_image,
        total_chapters=manga.total_chapters,
        created_at=manga.created_at,
        genres=genres,
        folder_path=manga.folder_path,
        is_archive=manga.is_archive
    )


@router.get("/{manga_id}/chapters", response_model=List[ChapterResponse])
async def list_manga_chapters(
    manga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of chapters for a manga"""
    # Verify manga exists
    result = await db.execute(select(Manga).where(Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Get chapters ordered by chapter number
    result = await db.execute(
        select(Chapter)
        .where(Chapter.manga_id == manga_id)
        .order_by(Chapter.chapter_number.asc())
    )
    chapters = result.scalars().all()
    
    return [
        ChapterResponse(
            id=chapter.id,
            title=chapter.title,
            chapter_number=chapter.chapter_number,
            folder_name=chapter.folder_name,
            page_count=chapter.page_count,
            created_at=chapter.created_at
        )
        for chapter in chapters
    ]


@router.get("/{manga_id}/chapters/{chapter_id}/pages", response_model=List[PageResponse])
async def list_chapter_pages(
    manga_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of pages for a chapter"""
    # Verify chapter exists and belongs to manga
    result = await db.execute(
        select(Chapter)
        .where(Chapter.id == chapter_id, Chapter.manga_id == manga_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Get pages ordered by page number
    result = await db.execute(
        select(Page)
        .where(Page.chapter_id == chapter_id)
        .order_by(Page.page_number.asc())
    )
    pages = result.scalars().all()
    
    return [
        PageResponse(
            id=page.id,
            page_number=page.page_number,
            filename=page.filename,
            width=page.width,
            height=page.height
        )
        for page in pages
    ]


@router.get("/slug/{slug}", response_model=MangaDetail)
async def get_manga_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get manga by slug"""
    result = await db.execute(select(Manga).where(Manga.slug == slug))
    manga = result.scalar_one_or_none()
    
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Parse genres from JSON string
    genres = []
    if manga.genres:
        try:
            genres = json.loads(manga.genres)
        except json.JSONDecodeError:
            genres = []
    
    return MangaDetail(
        id=manga.id,
        title=manga.title,
        slug=manga.slug,
        description=manga.description,
        author=manga.author,
        artist=manga.artist,
        status=manga.status,
        year=manga.year,
        cover_image=manga.cover_image,
        total_chapters=manga.total_chapters,
        created_at=manga.created_at,
        genres=genres,
        folder_path=manga.folder_path,
        is_archive=manga.is_archive
    )