<script lang="ts">
  import { onMount } from 'svelte'
  import { goto } from '$app/navigation'
  import { user, authStore, isAuthenticated } from '$lib/stores/auth'
  import { apiClient } from '$lib/api/client'
  import { theme } from '$lib/stores/theme'
  import type { UserPreference } from '$lib/api/types'
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte'

  let loading = false
  let scanningLibrary = false
  let scanResult = ''
  let preferences: UserPreference | null = null

  // Redirect if not authenticated
  $: if (!$isAuthenticated) {
    goto('/auth/login')
  }

  onMount(async () => {
    try {
      preferences = await apiClient.getPreferences()
      theme.setTheme(preferences.theme)
    } catch (error: any) {
      // If no preferences exist, create default
      preferences = {
        id: 0,
        user_id: $user?.id || 0,
        theme: 'auto',
        default_reading_direction: 'rtl',
        auto_next_chapter: true,
        page_fit_mode: 'fit-width',
        items_per_page: 20
      }
      theme.setTheme(preferences.theme)
    }
  })

  async function scanMangaLibrary() {
    scanningLibrary = true
    scanResult = ''
    
    try {
      const result = await apiClient.scanMangaLibrary()
      scanResult = result.message
    } catch (error: any) {
      scanResult = `Error: ${error.message}`
    } finally {
      scanningLibrary = false
    }
  }

  async function savePreferences() {
    if (!preferences) return

    loading = true
    try {
      preferences = await apiClient.updatePreferences(preferences)
      theme.setTheme(preferences.theme)
      // Could show a success message, but task says remove alert
    } catch (error: any) {
      console.error('Failed to save preferences:', error)
      // Could show error message
    } finally {
      loading = false
    }
  }

  function handleLogout() {
    authStore.logout()
  }
</script>

<svelte:head>
  <title>Settings - Manga Reader</title>
</svelte:head>

<div class="space-y-8 max-w-2xl">
  <!-- Header -->
  <div>
    <button 
      on:click={() => goto('/')}
      class="flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
    >
      <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      Back to Library
    </button>
    
    <h1 class="text-3xl font-bold tracking-tight">Settings</h1>
    <p class="text-muted-foreground mt-2">Manage your account and reading preferences</p>
  </div>

  <!-- Account section -->
  <div class="border border-border rounded-lg p-6 space-y-4">
    <h2 class="text-xl font-semibold">Account</h2>
    
    {#if $user}
      <div class="space-y-2">
        <div>
          <div class="text-sm font-medium text-muted-foreground">Username</div>
          <div class="text-foreground">{$user.username}</div>
        </div>
        <div>
          <div class="text-sm font-medium text-muted-foreground">Email</div>
          <div class="text-foreground">{$user.email}</div>
        </div>
      </div>
    {/if}

    <div class="pt-4">
      <button 
        on:click={handleLogout}
        class="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors"
      >
        Sign Out
      </button>
    </div>
  </div>

  <!-- Reading preferences -->
  <div class="border border-border rounded-lg p-6 space-y-6">
    <h2 class="text-xl font-semibold">Reading Preferences</h2>

    {#if preferences}
      <div class="space-y-4">
        <!-- Theme -->
        <div>
          <label for="theme-select" class="block text-sm font-medium mb-2">Theme</label>
          <select
            id="theme-select"
            bind:value={preferences.theme}
            class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="auto">Auto (System)</option>
          </select>
        </div>

        <!-- Default reading direction -->
        <div>
          <label for="direction-select" class="block text-sm font-medium mb-2">Default Reading Direction</label>
          <select
            id="direction-select"
            bind:value={preferences.default_reading_direction}
            class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          >
            <option value="rtl">Right to Left (Japanese Manga)</option>
            <option value="ltr">Left to Right (Western Comics)</option>
            <option value="ttb">Top to Bottom (Korean Manhwa)</option>
          </select>
        </div>

        <!-- Page fit mode -->
        <div>
          <label for="fit-select" class="block text-sm font-medium mb-2">Default Page Fit</label>
          <select
            id="fit-select"
            bind:value={preferences.page_fit_mode}
            class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          >
            <option value="fit-width">Fit to Width</option>
            <option value="fit-height">Fit to Height</option>
            <option value="original">Original Size</option>
          </select>
        </div>

        <!-- Auto next chapter -->
        <div class="flex items-center justify-between">
          <div>
            <label for="auto-next" class="text-sm font-medium">Auto-advance to Next Chapter</label>
            <div class="text-xs text-muted-foreground">Automatically go to the next chapter when reaching the last page</div>
          </div>
          <input
            id="auto-next"
            type="checkbox"
            bind:checked={preferences.auto_next_chapter}
            class="h-4 w-4 text-primary focus:ring-primary border-border rounded"
          >
        </div>

        <!-- Items per page -->
        <div>
          <label for="items-select" class="block text-sm font-medium mb-2">Manga per Page</label>
          <select
            id="items-select"
            bind:value={preferences.items_per_page}
            class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      <div class="pt-4">
        <button
          on:click={savePreferences}
          disabled={loading}
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {#if loading}
            <LoadingSpinner size="sm" showMessage={false} />
            <span class="ml-2">Saving...</span>
          {:else}
            Save Preferences
          {/if}
        </button>
      </div>
    {:else}
      <div class="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    {/if}
  </div>

  <!-- Library management -->
  <div class="border border-border rounded-lg p-6 space-y-4">
    <h2 class="text-xl font-semibold">Library Management</h2>
    
    <div class="space-y-4">
      <div>
        <h3 class="font-medium mb-2">Scan Manga Directory</h3>
        <p class="text-sm text-muted-foreground mb-4">
          Scan your configured manga directory for new manga series and chapters. 
          This will update your library with any newly added files.
        </p>
        
        <button 
          on:click={scanMangaLibrary}
          disabled={scanningLibrary}
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {#if scanningLibrary}
            <LoadingSpinner size="sm" showMessage={false} />
            <span class="ml-2">Scanning...</span>
          {:else}
            Scan Library
          {/if}
        </button>
        
        {#if scanResult}
          <div class="mt-3 p-3 bg-muted rounded-md">
            <p class="text-sm">{scanResult}</p>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Keyboard shortcuts -->
  <div class="border border-border rounded-lg p-6 space-y-4">
    <h2 class="text-xl font-semibold">Keyboard Shortcuts</h2>
    
    <div class="space-y-3 text-sm">
      <div class="flex justify-between">
        <span class="text-muted-foreground">Navigate pages</span>
        <span class="font-mono">← → ↑ ↓ Space</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">Toggle reading direction</span>
        <span class="font-mono">R</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">Toggle controls</span>
        <span class="font-mono">F</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">Zoom in/out</span>
        <span class="font-mono">+ -</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">Reset zoom</span>
        <span class="font-mono">0</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">Exit reader</span>
        <span class="font-mono">Esc</span>
      </div>
    </div>
  </div>
</div>