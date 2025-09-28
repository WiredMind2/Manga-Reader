<script lang="ts">
  import '../app.css'
  import { onMount } from 'svelte'
  import { page } from '$app/stores'
  import { goto } from '$app/navigation'
  import { authStore, user, isAuthenticated, isLoading } from '$lib/stores/auth'
  
  let { children } = $props();
  
  // Theme management
  let isDark = $state(false)
  let showUserMenu = $state(false)
  
  onMount(() => {
    // Check for saved theme or default to dark
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      isDark = savedTheme === 'dark'
    } else {
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    
    updateTheme()
    
    // Close user menu when clicking outside
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.user-menu')) {
        showUserMenu = false
      }
    }
    
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  })
  
  function updateTheme() {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }
  
  function toggleTheme() {
    isDark = !isDark
    updateTheme()
  }

  function handleLogout() {
    authStore.logout()
    showUserMenu = false
  }

  function navigateTo(path: string) {
    goto(path)
    showUserMenu = false
  }

  // Check if current page is auth page
  let isAuthPage = $derived($page.route.id?.startsWith('/auth'))
</script>

<div class="min-h-screen bg-background text-foreground">
  <!-- Navigation Header -->
  {#if !isAuthPage}
    <header class="border-b border-border bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50">
      <div class="container mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <!-- Logo/Title -->
          <div class="flex items-center space-x-4">
            <a href="/" class="flex items-center space-x-2 hover:opacity-80 transition-opacity">
              <div class="h-8 w-8 rounded bg-primary flex items-center justify-center">
                <span class="text-primary-foreground font-bold text-lg">M</span>
              </div>
              <h1 class="text-xl font-semibold">Manga Reader</h1>
            </a>
            
            <!-- Navigation Links -->
            {#if $isAuthenticated}
              <nav class="hidden md:flex items-center space-x-6 ml-8">
                <a 
                  href="/" 
                  class="text-sm font-medium hover:text-primary transition-colors"
                  class:text-primary={$page.route.id === '/'}
                >
                  Library
                </a>
              </nav>
            {/if}
          </div>
          
          <!-- Right side actions -->
          <div class="flex items-center space-x-4">
            <!-- Theme Toggle -->
            <button
              onclick={toggleTheme}
              class="p-2 rounded-md hover:bg-muted transition-colors"
              aria-label="Toggle theme"
            >
              {#if isDark}
                <!-- Sun icon -->
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              {:else}
                <!-- Moon icon -->
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              {/if}
            </button>
            
            {#if $isAuthenticated}
              <!-- User Menu -->
              <div class="relative user-menu">
                <button
                  onclick={() => showUserMenu = !showUserMenu}
                  class="flex items-center space-x-2 p-2 rounded-md hover:bg-muted transition-colors"
                >
                  <div class="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <span class="text-xs font-medium text-primary-foreground">
                      {$user?.username?.charAt(0)?.toUpperCase() || 'U'}
                    </span>
                  </div>
                  <span class="text-sm font-medium hidden sm:block">{$user?.username}</span>
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {#if showUserMenu}
                  <div class="absolute right-0 mt-2 w-48 bg-card border border-border rounded-md shadow-lg z-50">
                    <div class="py-1">
                      <button
                        onclick={() => navigateTo('/settings')}
                        class="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                      >
                        Settings
                      </button>
                      <button
                        onclick={handleLogout}
                        class="w-full text-left px-4 py-2 text-sm text-destructive hover:bg-muted transition-colors"
                      >
                        Sign out
                      </button>
                    </div>
                  </div>
                {/if}
              </div>
            {:else}
              <!-- Login/Register buttons -->
              <div class="flex items-center space-x-2">
                <a
                  href="/auth/login"
                  class="px-3 py-2 text-sm font-medium rounded-md hover:bg-muted transition-colors"
                >
                  Sign in
                </a>
                <a
                  href="/auth/register"
                  class="px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Sign up
                </a>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </header>
  {/if}
  
  <!-- Main Content -->
  <main class={isAuthPage ? '' : 'container mx-auto px-4 py-6'}>
    {@render children()}
  </main>
</div>

<style>
  :global(html) {
    font-family: 'Inter', system-ui, sans-serif;
  }
</style>
