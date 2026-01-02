import { writable } from 'svelte/store'
import { browser } from '$app/environment'

export type Theme = 'dark' | 'light' | 'auto'

function createThemeStore() {
  const initialTheme: Theme = browser
    ? (localStorage.getItem('theme') as Theme) || 'auto'
    : 'auto'

  const { subscribe, set, update } = writable<Theme>(initialTheme)

  function applyTheme(theme: Theme) {
    if (!browser) return

    const root = document.documentElement
    const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)

    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  function setTheme(theme: Theme) {
    set(theme)
    if (browser) {
      localStorage.setItem('theme', theme)
    }
    applyTheme(theme)
  }

  // Initialize
  applyTheme(initialTheme)

  // Handle system preference changes for auto mode
  if (browser) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      // Only apply if current theme is auto
      update(currentTheme => {
        if (currentTheme === 'auto') {
          applyTheme('auto')
        }
        return currentTheme
      })
    }
    mediaQuery.addEventListener('change', handleChange)
  }

  return {
    subscribe,
    setTheme
  }
}

export const theme = createThemeStore()