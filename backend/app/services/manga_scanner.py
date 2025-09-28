import os
import re
import json
import zipfile
import rarfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import aiofiles
from PIL import Image
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Manga, Chapter, Page
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MangaScanner:
    def __init__(self):
        self.manga_dir = Path(settings.MANGA_DIRECTORY)
        self.supported_images = settings.SUPPORTED_IMAGE_FORMATS
        self.supported_archives = settings.SUPPORTED_ARCHIVE_FORMATS
    
    async def scan_manga_directory(self, db: AsyncSession) -> List[Manga]:
        """Scan the manga directory and update database"""
        if not self.manga_dir.exists():
            logger.warning(f"Manga directory does not exist: {self.manga_dir}")
            return []
        
        manga_list = []
        
        for item in self.manga_dir.iterdir():
            if item.is_dir():
                # Folder-based manga
                manga = await self._scan_folder_manga(item, db)
                if manga:
                    manga_list.append(manga)
            elif item.suffix.lower()[1:] in self.supported_archives:
                # Archive-based manga
                manga = await self._scan_archive_manga(item, db)
                if manga:
                    manga_list.append(manga)
        
        return manga_list
    
    async def _scan_folder_manga(self, manga_path: Path, db: AsyncSession) -> Optional[Manga]:
        """Scan a folder-based manga series"""
        try:
            # Check if manga already exists in database
            result = await db.execute(
                select(Manga).where(Manga.folder_path == str(manga_path))
            )
            manga = result.scalar_one_or_none()
            
            if not manga:
                # Create new manga entry
                slug = self._create_slug(manga_path.name)
                manga = Manga(
                    title=manga_path.name,
                    slug=slug,
                    folder_path=str(manga_path),
                    is_archive=False
                )
                
                # Load metadata if available
                await self._load_metadata(manga, manga_path)
                
                db.add(manga)
                await db.commit()
                await db.refresh(manga)
            
            # Scan chapters
            await self._scan_chapters(manga, manga_path, db)
            
            # Update total chapters count
            result = await db.execute(
                select(func.count(Chapter.id)).where(Chapter.manga_id == manga.id)
            )
            manga.total_chapters = result.scalar()
            await db.commit()
            
            return manga
            
        except Exception as e:
            logger.error(f"Error scanning manga folder {manga_path}: {e}")
            return None
    
    async def _scan_archive_manga(self, archive_path: Path, db: AsyncSession) -> Optional[Manga]:
        """Scan an archive-based manga (CBZ, CBR, etc.) with support for multi-chapter archives"""
        try:
            result = await db.execute(
                select(Manga).where(Manga.folder_path == str(archive_path))
            )
            manga = result.scalar_one_or_none()
            
            if not manga:
                title = archive_path.stem
                slug = self._create_slug(title)
                manga = Manga(
                    title=title,
                    slug=slug,
                    folder_path=str(archive_path),
                    is_archive=True,
                    total_chapters=0  # Will be updated after scanning
                )
                
                db.add(manga)
                await db.commit()
                await db.refresh(manga)
            
            # Analyze archive structure to determine if it's single or multi-chapter
            chapters_found = await self._analyze_and_scan_archive_chapters(manga, archive_path, db)
            
            # Update total chapters count
            manga.total_chapters = chapters_found
            await db.commit()
            
            return manga
            
        except Exception as e:
            logger.error(f"Error scanning archive {archive_path}: {e}")
            return None
    
    async def _scan_chapters(self, manga: Manga, manga_path: Path, db: AsyncSession):
        """Scan chapters in a manga folder"""
        chapter_folders = []
        
        for item in manga_path.iterdir():
            if item.is_dir():
                chapter_folders.append(item)
            elif item.suffix.lower()[1:] in self.supported_archives:
                # Archive file as chapter
                chapter_folders.append(item)
        
        # Sort chapters naturally (handles Chapter 1, Chapter 2, Chapter 10 correctly)
        chapter_folders.sort(key=lambda x: self._natural_sort_key(x.name))
        
        for chapter_path in chapter_folders:
            await self._process_chapter(manga, chapter_path, db)
    
    async def _process_chapter(self, manga: Manga, chapter_path: Path, db: AsyncSession):
        """Process a single chapter (folder or archive)"""
        try:
            # Check if chapter already exists
            result = await db.execute(
                select(Chapter).where(
                    Chapter.manga_id == manga.id,
                    Chapter.folder_path == str(chapter_path)
                )
            )
            chapter = result.scalar_one_or_none()
            
            if not chapter:
                # Extract chapter number from folder name
                chapter_num = self._extract_chapter_number(chapter_path.name)
                
                chapter = Chapter(
                    manga_id=manga.id,
                    title=chapter_path.name,
                    chapter_number=chapter_num,
                    folder_name=chapter_path.name,
                    folder_path=str(chapter_path)
                )
                
                db.add(chapter)
                await db.commit()
                await db.refresh(chapter)
            
            # Scan pages in chapter
            if chapter_path.is_dir():
                await self._scan_folder_pages(chapter, chapter_path, db)
            else:
                await self._scan_archive_pages(chapter, chapter_path, db)
            
            # Update page count
            result = await db.execute(
                select(func.count(Page.id)).where(Page.chapter_id == chapter.id)
            )
            chapter.page_count = result.scalar()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error processing chapter {chapter_path}: {e}")
    
    async def _scan_folder_pages(self, chapter: Chapter, chapter_path: Path, db: AsyncSession):
        """Scan pages in a chapter folder"""
        image_files = []
        
        for file_path in chapter_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower()[1:] in self.supported_images:
                image_files.append(file_path)
        
        # Sort images naturally
        image_files.sort(key=lambda x: self._natural_sort_key(x.name))
        
        for i, image_path in enumerate(image_files, 1):
            await self._create_page_entry(chapter, image_path, i, db)
    
    async def _scan_archive_pages(self, chapter: Chapter, archive_path: Path, db: AsyncSession):
        """Scan pages in an archive file (for single-chapter archives)"""
        try:
            if archive_path.suffix.lower() in ['.cbz', '.zip']:
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    file_list = archive.namelist()
            elif archive_path.suffix.lower() in ['.cbr', '.rar']:
                with rarfile.RarFile(archive_path, 'r') as archive:
                    file_list = archive.namelist()
            else:
                return
            
            # Filter and sort image files (only root level for single-chapter)
            image_files = [
                f for f in file_list 
                if f.lower().endswith(tuple(f'.{ext}' for ext in self.supported_images))
                and not f.startswith('__MACOSX/')
                and '/' not in f.replace('\\', '/')  # Only root-level files for single chapter
            ]
            
            # If no root-level images, get all images (fallback for flat archives)
            if not image_files:
                image_files = [
                    f for f in file_list 
                    if f.lower().endswith(tuple(f'.{ext}' for ext in self.supported_images))
                    and not f.startswith('__MACOSX/')
                ]
            
            image_files.sort(key=self._natural_sort_key)
            
            for i, image_file in enumerate(image_files, 1):
                await self._create_archive_page_entry(chapter, archive_path, image_file, i, db)
                
        except Exception as e:
            logger.error(f"Error scanning archive {archive_path}: {e}")
    
    async def _analyze_and_scan_archive_chapters(self, manga: Manga, archive_path: Path, db: AsyncSession) -> int:
        """Analyze archive structure and scan chapters accordingly"""
        try:
            # Get file list from archive
            if archive_path.suffix.lower() in ['.cbz', '.zip']:
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    file_list = archive.namelist()
            elif archive_path.suffix.lower() in ['.cbr', '.rar']:
                with rarfile.RarFile(archive_path, 'r') as archive:
                    file_list = archive.namelist()
            else:
                return 0
            
            # Analyze directory structure
            chapters_data = self._analyze_archive_structure(file_list)
            
            if len(chapters_data) > 1:
                # Multi-chapter archive
                return await self._scan_multi_chapter_archive(manga, archive_path, chapters_data, db)
            else:
                # Single chapter archive (or flat structure)
                return await self._scan_single_chapter_archive(manga, archive_path, db)
                
        except Exception as e:
            logger.error(f"Error analyzing archive structure {archive_path}: {e}")
            return 0
    
    def _analyze_archive_structure(self, file_list: List[str]) -> Dict[str, List[str]]:
        """Analyze archive file structure to detect chapters"""
        chapters = {}
        image_extensions = tuple(f'.{ext}' for ext in self.supported_images)
        
        for file_path in file_list:
            # Skip system files
            if file_path.startswith('__MACOSX/') or file_path.startswith('.'):
                continue
                
            # Only process image files
            if not file_path.lower().endswith(image_extensions):
                continue
            
            # Normalize path separators
            normalized_path = file_path.replace('\\', '/')
            path_parts = normalized_path.split('/')
            
            if len(path_parts) > 1:
                # File is in a subdirectory - potential chapter folder
                chapter_folder = path_parts[0]
                
                # Group files by their parent directory
                if chapter_folder not in chapters:
                    chapters[chapter_folder] = []
                chapters[chapter_folder].append(file_path)
            else:
                # File is at root level
                if 'root' not in chapters:
                    chapters['root'] = []
                chapters['root'].append(file_path)
        
        # Filter out chapters with too few images (likely not actual chapters)
        filtered_chapters = {
            folder: files for folder, files in chapters.items() 
            if len(files) >= 3  # Minimum 3 images to be considered a chapter
        }
        
        # If we filtered everything out, fall back to treating root as single chapter
        if not filtered_chapters and 'root' in chapters:
            filtered_chapters = {'root': chapters['root']}
        
        return filtered_chapters
    
    async def _scan_multi_chapter_archive(self, manga: Manga, archive_path: Path, chapters_data: Dict[str, List[str]], db: AsyncSession) -> int:
        """Scan multi-chapter archive"""
        chapter_count = 0
        
        # Sort chapter folders naturally
        sorted_chapters = sorted(chapters_data.keys(), key=self._natural_sort_key)
        
        for i, chapter_folder in enumerate(sorted_chapters, 1):
            files = chapters_data[chapter_folder]
            
            # Check if chapter already exists
            chapter_identifier = f"{archive_path}:{chapter_folder}"
            result = await db.execute(
                select(Chapter).where(
                    Chapter.manga_id == manga.id,
                    Chapter.folder_path == chapter_identifier
                )
            )
            chapter = result.scalar_one_or_none()
            
            if not chapter:
                chapter_num = self._extract_chapter_number(chapter_folder) if chapter_folder != 'root' else float(i)
                
                chapter = Chapter(
                    manga_id=manga.id,
                    title=chapter_folder if chapter_folder != 'root' else f"Chapter {i}",
                    chapter_number=chapter_num,
                    folder_name=chapter_folder,
                    folder_path=chapter_identifier
                )
                
                db.add(chapter)
                await db.commit()
                await db.refresh(chapter)
            
            # Scan pages for this chapter
            await self._scan_archive_chapter_pages(chapter, archive_path, files, db)
            
            # Update page count
            result = await db.execute(
                select(func.count(Page.id)).where(Page.chapter_id == chapter.id)
            )
            chapter.page_count = result.scalar()
            await db.commit()
            
            chapter_count += 1
        
        return chapter_count
    
    async def _scan_single_chapter_archive(self, manga: Manga, archive_path: Path, db: AsyncSession) -> int:
        """Scan single-chapter archive (original behavior)"""
        result = await db.execute(
            select(Chapter).where(
                Chapter.manga_id == manga.id,
                Chapter.folder_path == str(archive_path)
            )
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            chapter = Chapter(
                manga_id=manga.id,
                title=archive_path.stem,
                chapter_number=1.0,
                folder_name=archive_path.name,
                folder_path=str(archive_path)
            )
            
            db.add(chapter)
            await db.commit()
            await db.refresh(chapter)
        
        await self._scan_archive_pages(chapter, archive_path, db)
        
        # Update page count
        result = await db.execute(
            select(func.count(Page.id)).where(Page.chapter_id == chapter.id)
        )
        chapter.page_count = result.scalar()
        await db.commit()
        
        return 1
    
    async def _scan_archive_chapter_pages(self, chapter: Chapter, archive_path: Path, file_list: List[str], db: AsyncSession):
        """Scan pages for a specific chapter within an archive"""
        # Sort images naturally
        sorted_files = sorted(file_list, key=self._natural_sort_key)
        
        for i, image_file in enumerate(sorted_files, 1):
            await self._create_archive_page_entry(chapter, archive_path, image_file, i, db)
    
    async def _create_page_entry(self, chapter: Chapter, image_path: Path, page_num: int, db: AsyncSession):
        """Create a page entry for a regular file"""
        result = await db.execute(
            select(Page).where(
                Page.chapter_id == chapter.id,
                Page.file_path == str(image_path)
            )
        )
        
        if result.scalar_one_or_none():
            return  # Page already exists
        
        # Get image dimensions
        width, height = None, None
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except Exception:
            pass
        
        page = Page(
            chapter_id=chapter.id,
            page_number=page_num,
            filename=image_path.name,
            file_path=str(image_path),
            file_size=image_path.stat().st_size if image_path.exists() else None,
            width=width,
            height=height
        )
        
        db.add(page)
        await db.commit()
    
    async def _create_archive_page_entry(self, chapter: Chapter, archive_path: Path, image_filename: str, page_num: int, db: AsyncSession):
        """Create a page entry for an archive file"""
        # Use archive_path:image_filename as unique identifier
        file_path = f"{archive_path}:{image_filename}"
        
        result = await db.execute(
            select(Page).where(
                Page.chapter_id == chapter.id,
                Page.file_path == file_path
            )
        )
        
        if result.scalar_one_or_none():
            return  # Page already exists
        
        page = Page(
            chapter_id=chapter.id,
            page_number=page_num,
            filename=os.path.basename(image_filename),
            file_path=file_path,
            file_size=None,  # Could extract from archive info if needed
            width=None,
            height=None
        )
        
        db.add(page)
        await db.commit()
    
    async def _load_metadata(self, manga: Manga, manga_path: Path):
        """Load metadata from JSON file if it exists"""
        metadata_file = manga_path / "metadata.json"
        if metadata_file.exists():
            try:
                async with aiofiles.open(metadata_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    metadata = json.loads(content)
                
                manga.description = metadata.get('description')
                manga.author = metadata.get('author')
                manga.artist = metadata.get('artist')
                manga.status = metadata.get('status')
                manga.year = metadata.get('year')
                manga.genres = json.dumps(metadata.get('genres', []))
                
            except Exception as e:
                logger.warning(f"Error loading metadata for {manga_path}: {e}")
        
        # Look for cover image
        cover_files = ['cover.jpg', 'cover.jpeg', 'cover.png', 'cover.webp']
        for cover_file in cover_files:
            cover_path = manga_path / cover_file
            if cover_path.exists():
                manga.cover_image = str(cover_path)
                break
    
    def _create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _extract_chapter_number(self, folder_name: str) -> float:
        """Extract chapter number from folder name"""
        # Look for patterns like "Chapter 1", "Ch 1.5", "001", etc.
        patterns = [
            r'chapter\s*(\d+(?:\.\d+)?)',
            r'ch\s*(\d+(?:\.\d+)?)',
            r'^(\d+(?:\.\d+)?)(?:\s|$)',
            r'(\d+(?:\.\d+))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, folder_name.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # Fallback: use hash of folder name
        return float(abs(hash(folder_name)) % 10000)
    
    def _natural_sort_key(self, text: str) -> List:
        """Natural sorting key for proper ordering of chapters and pages"""
        def convert(text_part):
            return int(text_part) if text_part.isdigit() else text_part.lower()
        
        return [convert(c) for c in re.split(r'(\d+)', text)]


# Create singleton instance
manga_scanner = MangaScanner()