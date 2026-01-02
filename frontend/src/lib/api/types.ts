// User related types
export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface UserPreference {
  id: number
  user_id: number
  default_reading_direction: 'rtl' | 'ltr' | 'ttb'
  auto_next_chapter: boolean
  page_fit_mode: 'fit-width' | 'fit-height' | 'original'
  theme: 'dark' | 'light' | 'auto'
  items_per_page: number
}

// Manga related types
export interface Manga {
  id: number
  title: string
  slug: string
  description?: string
  author?: string
  artist?: string
  status?: 'ongoing' | 'completed' | 'hiatus' | 'cancelled'
  year?: number
  cover_image?: string
  total_chapters: number
  created_at: string
}

export interface MangaDetail extends Manga {
  genres: string[]
  folder_path: string
  is_archive: boolean
}

export interface Chapter {
  id: number
  title: string
  chapter_number: number
  folder_name: string
  page_count: number
  created_at: string
}

export interface Page {
  id: number
  page_number: number
  filename: string
  width?: number
  height?: number
  localUrl?: string
}

// Progress related types
export interface ReadingProgress {
  id: number
  manga_id: number
  chapter_id?: number
  page_number: number
  last_read_at: string
  reading_direction: 'rtl' | 'ltr' | 'ttb'
  zoom_level: number
  scroll_position: number
}

export interface ReadingProgressUpdate {
  chapter_id: number
  page_number: number
  reading_direction?: 'rtl' | 'ltr' | 'ttb'
  zoom_level?: number
  scroll_position?: number
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  status?: number
}

// Reading related types
export type ReadingDirection = 'rtl' | 'ltr' | 'ttb'
export type PageFitMode = 'fit-width' | 'fit-height' | 'original' | 'fit-screen'
export type Theme = 'dark' | 'light' | 'auto'

export interface ReaderSettings {
  reading_direction: ReadingDirection
  page_fit_mode: PageFitMode
  zoom_level: number
  auto_next_chapter: boolean
  show_page_numbers: boolean
  background_color: string
}

// Component prop types
export interface MangaCardProps {
  manga: Manga
  progress?: ReadingProgress | null
  showProgress?: boolean
}

export interface ReaderProps {
  manga: MangaDetail
  chapter: Chapter
  pages: Page[]
  currentPage: number
  settings: ReaderSettings
}

// Recent reads type
export interface RecentRead {
  manga: {
    id: number
    title: string
    slug: string
    cover_image?: string
    total_chapters: number
  }
  chapter?: {
    id: number
    title: string
    chapter_number: number
  }
  progress: {
    page_number: number
    last_read_at: string
    reading_direction: ReadingDirection
  }
}