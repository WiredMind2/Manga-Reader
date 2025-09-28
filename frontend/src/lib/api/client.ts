import { browser } from '$app/environment'
import type { 
  User, 
  Manga, 
  MangaDetail, 
  Chapter, 
  Page, 
  ReadingProgress, 
  PaginatedResponse,
  LoginRequest,
  RegisterRequest,
  ReadingProgressUpdate
} from './types.js'

const API_BASE_URL = 'http://localhost:8000/api'

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private baseURL: string = API_BASE_URL
  private token: string | null = null

  constructor() {
    if (browser) {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (browser) {
      if (token) {
        localStorage.setItem('auth_token', token)
      } else {
        localStorage.removeItem('auth_token')
      }
    }
  }

  getToken(): string | null {
    return this.token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const config: RequestInit = {
      ...options,
      headers
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        let errorData: any
        try {
          errorData = await response.json()
        } catch {
          errorData = { detail: `HTTP ${response.status}: ${response.statusText}` }
        }
        
        throw new ApiError(
          errorData.detail || `HTTP ${response.status}`,
          response.status,
          errorData
        )
      }

      // Handle empty responses
      if (response.status === 204) {
        return {} as T
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error',
        0
      )
    }
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<{ access_token: string; token_type: string }> {
    const response = await this.request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    })
    
    this.setToken(response.access_token)
    return response
  }

  async register(userData: RegisterRequest): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } finally {
      this.setToken(null)
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me')
  }

  // Manga endpoints
  async getManga(params: {
    page?: number
    size?: number
    search?: string
    sort_by?: string
    sort_order?: string
  } = {}): Promise<PaginatedResponse<Manga>> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString())
      }
    })

    const query = searchParams.toString()
    const endpoint = `/manga${query ? `?${query}` : ''}`
    
    return this.request<PaginatedResponse<Manga>>(endpoint)
  }

  async getMangaById(id: number): Promise<MangaDetail> {
    return this.request<MangaDetail>(`/manga/${id}`)
  }

  async getMangaBySlug(slug: string): Promise<MangaDetail> {
    return this.request<MangaDetail>(`/manga/slug/${slug}`)
  }

  async getMangaChapters(mangaId: number): Promise<Chapter[]> {
    return this.request<Chapter[]>(`/manga/${mangaId}/chapters`)
  }

  async getChapterPages(mangaId: number, chapterId: number): Promise<Page[]> {
    return this.request<Page[]>(`/manga/${mangaId}/chapters/${chapterId}/pages`)
  }

  async scanMangaLibrary(): Promise<{ message: string; manga_count: number }> {
    return this.request('/manga/scan', { method: 'GET' })
  }

  // Progress endpoints
  async getAllProgress(): Promise<ReadingProgress[]> {
    return this.request<ReadingProgress[]>('/progress')
  }

  async getMangaProgress(mangaId: number): Promise<ReadingProgress | null> {
    try {
      return await this.request<ReadingProgress>(`/progress/${mangaId}`)
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return null
      }
      throw error
    }
  }

  async updateProgress(mangaId: number, progress: ReadingProgressUpdate): Promise<ReadingProgress> {
    return this.request<ReadingProgress>(`/progress/${mangaId}`, {
      method: 'PUT',
      body: JSON.stringify(progress)
    })
  }

  async deleteProgress(mangaId: number): Promise<void> {
    await this.request(`/progress/${mangaId}`, { method: 'DELETE' })
  }

  async getRecentReads(limit: number = 10): Promise<any> {
    return this.request(`/progress/recent/${limit}`)
  }

  // Image endpoints
  getPageImageUrl(
    mangaId: number, 
    chapterId: number, 
    pageId: number, 
    options: {
      width?: number
      height?: number
      quality?: number
      thumbnail?: boolean
    } = {}
  ): string {
    const params = new URLSearchParams()
    
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const query = params.toString()
    const endpoint = `/images/${mangaId}/${chapterId}/${pageId}`
    
    return `${this.baseURL}${endpoint}${query ? `?${query}` : ''}`
  }

  getCoverImageUrl(
    mangaId: number,
    options: {
      width?: number
      height?: number
      quality?: number
    } = {}
  ): string {
    const params = new URLSearchParams()
    
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const query = params.toString()
    const endpoint = `/covers/${mangaId}`
    
    return `${this.baseURL}${endpoint}${query ? `?${query}` : ''}`
  }

  // Utility method to check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.token
  }

  // Method to handle token refresh (if implemented in backend)
  async refreshToken(): Promise<void> {
    // This would be implemented if the backend supports token refresh
    // For now, we'll just check if the current token is still valid
    try {
      await this.getCurrentUser()
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        this.setToken(null)
        throw error
      }
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient()
export { ApiError }
export type { ApiClient }