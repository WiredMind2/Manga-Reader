from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional

from app.core.database import get_db
from app.core.schemas import ReadingProgressUpdate, ReadingProgressResponse
from app.models import ReadingProgress, Manga, Chapter, User
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ReadingProgressResponse])
async def get_all_reading_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all reading progress for current user"""
    result = await db.execute(
        select(ReadingProgress)
        .where(ReadingProgress.user_id == current_user.id)
        .order_by(ReadingProgress.last_read_at.desc())
    )
    
    progress_list = result.scalars().all()
    
    return [
        ReadingProgressResponse(
            id=progress.id,
            manga_id=progress.manga_id,
            chapter_id=progress.chapter_id,
            page_number=progress.page_number,
            last_read_at=progress.last_read_at,
            reading_direction=progress.reading_direction,
            zoom_level=progress.zoom_level,
            scroll_position=progress.scroll_position
        )
        for progress in progress_list
    ]


@router.get("/{manga_id}", response_model=Optional[ReadingProgressResponse])
async def get_manga_reading_progress(
    manga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reading progress for a specific manga"""
    # Verify manga exists
    result = await db.execute(select(Manga).where(Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Get user's progress for this manga
    result = await db.execute(
        select(ReadingProgress)
        .where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.manga_id == manga_id
        )
    )
    
    progress = result.scalar_one_or_none()
    
    if not progress:
        return None
    
    return ReadingProgressResponse(
        id=progress.id,
        manga_id=progress.manga_id,
        chapter_id=progress.chapter_id,
        page_number=progress.page_number,
        last_read_at=progress.last_read_at,
        reading_direction=progress.reading_direction,
        zoom_level=progress.zoom_level,
        scroll_position=progress.scroll_position
    )


@router.put("/{manga_id}", response_model=ReadingProgressResponse)
async def update_reading_progress(
    manga_id: int,
    progress_data: ReadingProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update reading progress for a manga"""
    # Verify manga exists
    result = await db.execute(select(Manga).where(Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Verify chapter belongs to manga
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.id == progress_data.chapter_id,
            Chapter.manga_id == manga_id
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=400, detail="Chapter not found or does not belong to this manga")
    
    # Get or create progress record
    result = await db.execute(
        select(ReadingProgress)
        .where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.manga_id == manga_id
        )
    )
    
    progress = result.scalar_one_or_none()
    
    if progress:
        # Update existing progress
        progress.chapter_id = progress_data.chapter_id
        progress.page_number = progress_data.page_number
        if progress_data.reading_direction:
            progress.reading_direction = progress_data.reading_direction
        if progress_data.zoom_level is not None:
            progress.zoom_level = progress_data.zoom_level
        if progress_data.scroll_position is not None:
            progress.scroll_position = progress_data.scroll_position
    else:
        # Create new progress record
        progress = ReadingProgress(
            user_id=current_user.id,
            manga_id=manga_id,
            chapter_id=progress_data.chapter_id,
            page_number=progress_data.page_number,
            reading_direction=progress_data.reading_direction or "rtl",
            zoom_level=progress_data.zoom_level or 1.0,
            scroll_position=progress_data.scroll_position or 0.0
        )
        db.add(progress)
    
    await db.commit()
    await db.refresh(progress)
    
    return ReadingProgressResponse(
        id=progress.id,
        manga_id=progress.manga_id,
        chapter_id=progress.chapter_id,
        page_number=progress.page_number,
        last_read_at=progress.last_read_at,
        reading_direction=progress.reading_direction,
        zoom_level=progress.zoom_level,
        scroll_position=progress.scroll_position
    )


@router.delete("/{manga_id}")
async def delete_reading_progress(
    manga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete reading progress for a manga"""
    result = await db.execute(
        select(ReadingProgress)
        .where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.manga_id == manga_id
        )
    )
    
    progress = result.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="No reading progress found")
    
    await db.delete(progress)
    await db.commit()
    
    return {"message": "Successfully deleted reading progress"}


@router.get("/recent/{limit}")
async def get_recent_reading_progress(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recently read manga with progress info"""
    result = await db.execute(
        select(ReadingProgress, Manga, Chapter)
        .join(Manga, ReadingProgress.manga_id == Manga.id)
        .outerjoin(Chapter, ReadingProgress.chapter_id == Chapter.id)
        .where(ReadingProgress.user_id == current_user.id)
        .order_by(ReadingProgress.last_read_at.desc())
        .limit(limit)
    )
    
    recent_reads = []
    for progress, manga, chapter in result.all():
        recent_reads.append({
            "manga": {
                "id": manga.id,
                "title": manga.title,
                "slug": manga.slug,
                "cover_image": manga.cover_image,
                "total_chapters": manga.total_chapters
            },
            "chapter": {
                "id": chapter.id if chapter else None,
                "title": chapter.title if chapter else None,
                "chapter_number": chapter.chapter_number if chapter else None
            } if chapter else None,
            "progress": {
                "page_number": progress.page_number,
                "last_read_at": progress.last_read_at,
                "reading_direction": progress.reading_direction
            }
        })
    
    return {"recent_reads": recent_reads}