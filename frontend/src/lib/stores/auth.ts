import { writable, derived, type Readable } from 'svelte/store'
import { browser } from '$app/environment'
import { goto } from '$app/navigation'
import { apiClient, ApiError } from '../api/client'
import type { User, LoginRequest, RegisterRequest } from '../api/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

const createAuthStore = () => {
  const initialState: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  }

  const { subscribe, set, update } = writable<AuthState>(initialState)

  // Initialize authentication state
  const init = async () => {
    if (!browser) return

    const token = apiClient.getToken()
    if (!token) {
      update(state => ({ ...state, isLoading: false }))
      return
    }

    try {
      const user = await apiClient.getCurrentUser()
      update(state => ({
        ...state,
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null
      }))
    } catch (error) {
      console.error('Failed to initialize auth:', error)
      apiClient.setToken(null)
      update(state => ({
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      }))
    }
  }

  const login = async (credentials: LoginRequest): Promise<void> => {
    update(state => ({ ...state, isLoading: true, error: null }))

    try {
      await apiClient.login(credentials)
      const user = await apiClient.getCurrentUser()
      
      update(state => ({
        ...state,
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null
      }))

      // Redirect to home page after successful login
      goto('/')
    } catch (error) {
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Login failed. Please try again.'
      
      update(state => ({
        ...state,
        isLoading: false,
        error: errorMessage
      }))
      throw error
    }
  }

  const register = async (userData: RegisterRequest): Promise<void> => {
    update(state => ({ ...state, isLoading: true, error: null }))

    try {
      const user = await apiClient.register(userData)
      
      // Auto-login after successful registration
      await login({
        username: userData.username,
        password: userData.password
      })
    } catch (error) {
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Registration failed. Please try again.'
      
      update(state => ({
        ...state,
        isLoading: false,
        error: errorMessage
      }))
      throw error
    }
  }

  const logout = async (): Promise<void> => {
    update(state => ({ ...state, isLoading: true }))

    try {
      await apiClient.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      update(state => ({
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      }))

      // Redirect to login page after logout
      goto('/auth/login')
    }
  }

  const clearError = () => {
    update(state => ({ ...state, error: null }))
  }

  const refreshUser = async (): Promise<void> => {
    if (!apiClient.isAuthenticated()) return

    try {
      const user = await apiClient.getCurrentUser()
      update(state => ({ ...state, user }))
    } catch (error) {
      console.error('Failed to refresh user:', error)
      if (error instanceof ApiError && error.status === 401) {
        // Token is invalid, log out
        await logout()
      }
    }
  }

  // Check token validity periodically
  const startTokenValidation = () => {
    if (!browser) return

    setInterval(async () => {
      if (apiClient.isAuthenticated()) {
        try {
          await apiClient.refreshToken()
        } catch (error) {
          if (error instanceof ApiError && error.status === 401) {
            await logout()
          }
        }
      }
    }, 5 * 60 * 1000) // Check every 5 minutes
  }

  return {
    subscribe,
    init,
    login,
    register,
    logout,
    clearError,
    refreshUser,
    startTokenValidation
  }
}

export const authStore = createAuthStore()

// Derived stores for convenience
export const user: Readable<User | null> = derived(
  authStore,
  $auth => $auth.user
)

export const isAuthenticated: Readable<boolean> = derived(
  authStore,
  $auth => $auth.isAuthenticated
)

export const isLoading: Readable<boolean> = derived(
  authStore,
  $auth => $auth.isLoading
)

export const authError: Readable<string | null> = derived(
  authStore,
  $auth => $auth.error
)

// Initialize auth store when module loads
if (browser) {
  authStore.init()
  authStore.startTokenValidation()
}