from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import os
import zipfile
import rarfile
from pathlib import Path
from PIL import Image
import io
import hashlib
import aiofiles

from app.core.database import get_db
from app.models import Page, Chapter, Manga, User
from app.api.auth import get_current_user
from app.core.config import settings

router = APIRouter()


class ImageOptimizer:
    def __init__(self):
        self.cache_dir = Path(settings.IMAGE_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, original_path: str, width: Optional[int] = None, height: Optional[int] = None, quality: int = 85) -> Path:
        """Generate cache file path based on original path and parameters"""
        # Create hash of original path and parameters
        cache_key = f"{original_path}:{width}:{height}:{quality}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{cache_hash}.webp"
    
    async def optimize_image(
        self, 
        image_path: str, 
        width: Optional[int] = None, 
        height: Optional[int] = None,
        quality: int = 85
    ) -> Path:
        """Optimize image and return cached version path"""
        cache_path = self._get_cache_path(image_path, width, height, quality)
        
        # Return cached version if it exists and is newer than original
        if cache_path.exists():
            try:
                # Handle archive paths for stat check
                original_file_path = image_path
                if ':' in image_path:
                    # Find the last colon to handle Windows drive letters
                    archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
                    for ext in archive_extensions:
                        ext_pos = image_path.lower().find(ext + ':')
                        if ext_pos != -1:
                            original_file_path = image_path[:ext_pos + len(ext)]
                            break
                
                original_stat = os.stat(original_file_path)
                cache_stat = os.stat(cache_path)
                if cache_stat.st_mtime > original_stat.st_mtime:
                    return cache_path
            except (OSError, FileNotFoundError):
                # If we can't stat the original file (e.g., in tests), proceed with optimization
                pass
        
        # Load and optimize image
        try:
            # Handle archive paths
            if ':' in image_path:
                # Find the last colon to handle Windows drive letters (C:\path:internal)
                # Look for archive format extensions to determine proper split point
                archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
                colon_idx = -1
                
                for ext in archive_extensions:
                    ext_pos = image_path.lower().find(ext + ':')
                    if ext_pos != -1:
                        colon_idx = ext_pos + len(ext)
                        break
                
                if colon_idx > 0:
                    archive_path = image_path[:colon_idx]
                    internal_path = image_path[colon_idx + 1:]
                    image = await self._load_from_archive(archive_path, internal_path)
                else:
                    # Check if this looks like an archive path with unsupported format
                    if any(ext in image_path.lower() for ext in ['.7z:', '.tar:', '.gz:']):
                        raise HTTPException(status_code=500, detail="Failed to load image from archive: Unsupported archive format")
                    else:
                        # Fallback to regular file if no proper archive separator found
                        image = Image.open(image_path)
            else:
                image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if dimensions specified
            if width or height:
                original_width, original_height = image.size
                
                if width and height:
                    # Specific dimensions - maintain aspect ratio and crop if needed
                    aspect_ratio = original_width / original_height
                    target_ratio = width / height
                    
                    if aspect_ratio > target_ratio:
                        # Image is wider - fit to height and crop width
                        new_height = height
                        new_width = int(height * aspect_ratio)
                    else:
                        # Image is taller - fit to width and crop height
                        new_width = width
                        new_height = int(width / aspect_ratio)
                    
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Center crop to target dimensions
                    left = (new_width - width) // 2
                    top = (new_height - height) // 2
                    right = left + width
                    bottom = top + height
                    image = image.crop((left, top, right, bottom))
                    
                elif width:
                    # Fit to width, maintain aspect ratio
                    new_height = int(original_height * width / original_width)
                    image = image.resize((width, new_height), Image.Resampling.LANCZOS)
                    
                elif height:
                    # Fit to height, maintain aspect ratio
                    new_width = int(original_width * height / original_height)
                    image = image.resize((new_width, height), Image.Resampling.LANCZOS)
            
            # Apply max size limits
            max_width, max_height = settings.MAX_IMAGE_SIZE
            if image.size[0] > max_width or image.size[1] > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(cache_path, 'WEBP', quality=quality, optimize=True)
            return cache_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image optimization failed: {str(e)}")
    
    async def _load_from_archive(self, archive_path: str, internal_path: str) -> Image.Image:
        """Load image from archive file"""
        try:
            if archive_path.lower().endswith(('.zip', '.cbz')):
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    with archive.open(internal_path) as image_file:
                        return Image.open(io.BytesIO(image_file.read()))
            elif archive_path.lower().endswith(('.rar', '.cbr')):
                with rarfile.RarFile(archive_path, 'r') as archive:
                    with archive.open(internal_path) as image_file:
                        return Image.open(io.BytesIO(image_file.read()))
            else:
                raise ValueError(f"Unsupported archive format: {archive_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load image from archive: {str(e)}")


image_optimizer = ImageOptimizer()


@router.get("/{manga_id}/{chapter_id}/{page_id}")
async def get_page_image(
    manga_id: int,
    chapter_id: int,
    page_id: int,
    width: Optional[int] = Query(None, ge=50, le=2560),
    height: Optional[int] = Query(None, ge=50, le=2560),
    quality: int = Query(85, ge=10, le=100),
    thumbnail: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get optimized page image"""
    # Verify page exists and belongs to the correct manga/chapter
    result = await db.execute(
        select(Page, Chapter, Manga)
        .join(Chapter, Page.chapter_id == Chapter.id)
        .join(Manga, Chapter.manga_id == Manga.id)
        .where(
            Page.id == page_id,
            Chapter.id == chapter_id,
            Manga.id == manga_id
        )
    )
    
    page_data = result.first()
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page, chapter, manga = page_data
    
    # If thumbnail requested, use thumbnail dimensions
    if thumbnail:
        width, height = settings.THUMBNAIL_SIZE
        quality = 75  # Lower quality for thumbnails
    
    try:
        # Optimize and cache image
        optimized_path = await image_optimizer.optimize_image(
            page.file_path, width, height, quality
        )
        
        # Return optimized image
        return FileResponse(
            optimized_path,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1 year
                "X-Page-Number": str(page.page_number),
                "X-Chapter-Title": chapter.title,
                "X-Manga-Title": manga.title
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their error messages
        raise
    except Exception as e:
        # Fallback to serving original image if optimization fails
        if ':' not in page.file_path and os.path.exists(page.file_path):
            return FileResponse(page.file_path)
        else:
            raise HTTPException(status_code=500, detail="Failed to serve image")


@router.get("/covers/{manga_id}")
async def get_cover_image(
    manga_id: int,
    width: Optional[int] = Query(None, ge=50, le=800),
    height: Optional[int] = Query(None, ge=50, le=1200),
    quality: int = Query(85, ge=10, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get manga cover image"""
    result = await db.execute(select(Manga).where(Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    if not manga.cover_image or not os.path.exists(manga.cover_image):
        # Try to find first page of first chapter as cover
        result = await db.execute(
            select(Page, Chapter)
            .join(Chapter, Page.chapter_id == Chapter.id)
            .where(Chapter.manga_id == manga_id)
            .order_by(Chapter.chapter_number.asc(), Page.page_number.asc())
            .limit(1)
        )
        
        page_data = result.first()
        if not page_data:
            raise HTTPException(status_code=404, detail="No cover image or pages found")
        
        page, chapter = page_data
        cover_path = page.file_path
    else:
        cover_path = manga.cover_image
    
    # Use cover-specific dimensions if not provided
    if not width and not height:
        width, height = settings.THUMBNAIL_SIZE
    
    try:
        optimized_path = await image_optimizer.optimize_image(
            cover_path, width, height, quality
        )
        
        return FileResponse(
            optimized_path,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1 year
                "X-Manga-Title": manga.title
            }
        )
        
    except Exception as e:
        if ':' not in cover_path and os.path.exists(cover_path):
            return FileResponse(cover_path)
        else:
            raise HTTPException(status_code=404, detail="Cover image not found")