<script lang="ts">
  import { onMount } from 'svelte'
  import { goto } from '$app/navigation'
  import { isAuthenticated, isLoading as authLoading } from '$lib/stores/auth'
  import { apiClient } from '$lib/api/client'
  import type { Manga, PaginatedResponse } from '$lib/api/types'
  import MangaGrid from '$lib/components/MangaGrid.svelte'
  import SearchBar from '$lib/components/SearchBar.svelte'
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte'
  
  // State
  let manga: Manga[] = []
  let loading = true
  let error = ''
  let searchTerm = ''
  let currentPage = 1
  let totalPages = 1
  let totalManga = 0
  let sortBy = 'title'
  let sortOrder = 'asc'
  let pageSize = 20
  let showScanButton = false
  let hasAttemptedLoad = false
  let notification = ''
  let notificationType = 'success' // 'success' | 'error'
  
  // Redirect to login if not authenticated
  $: if (!$authLoading && !$isAuthenticated) {
    goto('/auth/login')
  }
  
  // Load manga data
  async function loadManga() {
    if (!$isAuthenticated) return
    
    loading = true
    error = ''
    
    try {
      const response: PaginatedResponse<Manga> = await apiClient.getManga({
        page: currentPage,
        size: pageSize,
        search: searchTerm || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      })
      
      manga = response.items
      totalPages = response.pages
      totalManga = response.total
      
      // Show scan button if no manga found
      showScanButton = response.total === 0
      
    } catch (err: any) {
      console.error('Failed to load manga:', err)
      error = err.message || 'Failed to load manga library'
      showScanButton = true
    } finally {
      loading = false
      hasAttemptedLoad = true
    }
  }
  
  // Scan manga library
  async function scanLibrary() {
    try {
      loading = true
      notification = ''
      const result = await apiClient.scanMangaLibrary()
      
      // Reload manga after scan
      await loadManga()
      
      // Show success notification
      notification = `Successfully scanned library: ${result.message}`
      notificationType = 'success'
      
      // Auto-hide notification after 5 seconds
      setTimeout(() => {
        notification = ''
      }, 5000)
      
    } catch (err: any) {
      error = err.message || 'Failed to scan manga library'
      notification = `Scan failed: ${err.message}`
      notificationType = 'error'
      
      // Auto-hide error notification after 5 seconds
      setTimeout(() => {
        notification = ''
      }, 5000)
    } finally {
      // Always reset loading state
      loading = false
    }
  }
  
  // Handle search
  function handleSearch(event: CustomEvent<string>) {
    searchTerm = event.detail
    currentPage = 1
    loadManga()
  }
  
  // Handle sorting
  function handleSort(newSortBy: string) {
    if (sortBy === newSortBy) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = newSortBy
      sortOrder = 'asc'
    }
    currentPage = 1
    loadManga()
  }
  
  // Handle pagination
  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page
      loadManga()
    }
  }
  
  // Load data when component mounts and user is authenticated
  onMount(() => {
    if ($isAuthenticated) {
      loadManga()
    }
  })
  
  // Reload when authentication state changes (but only if we haven't attempted to load yet)
  $: if ($isAuthenticated && !loading && !hasAttemptedLoad) {
    loadManga()
  }
</script>

<svelte:head>
  <title>Manga Library - Manga Reader</title>
  <meta name="description" content="Browse and read your manga collection" />
</svelte:head>

{#if $authLoading}
  <div class="flex justify-center items-center min-h-[50vh]">
    <LoadingSpinner message="Loading..." />
  </div>
{:else if !$isAuthenticated}
  <!-- This will redirect to login, but show loading state briefly -->
  <div class="flex justify-center items-center min-h-[50vh]">
    <LoadingSpinner message="Redirecting to login..." />
  </div>
{:else}
  <div class="space-y-6">
    <!-- Notification Toast -->
    {#if notification}
      <div class={`
        p-4 rounded-lg border flex items-center gap-3 transition-all duration-300
        ${notificationType === 'success' 
          ? 'bg-green-50 border-green-200 text-green-800' 
          : 'bg-red-50 border-red-200 text-red-800'
        }
      `}>
        <div class="flex-shrink-0">
          {#if notificationType === 'success'}
            <svg class="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          {:else}
            <svg class="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          {/if}
        </div>
        <div class="flex-1">
          {notification}
        </div>
        <button 
          onclick={() => notification = ''} 
          class="flex-shrink-0 text-current hover:opacity-75 transition-opacity"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    {/if}

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Manga Library</h1>
        <p class="text-muted-foreground mt-1">
          {#if !loading && totalManga > 0}
            {totalManga} manga series available
          {:else if totalManga === 0 && !loading}
            No manga found
          {/if}
        </p>
      </div>
      
      <div class="flex gap-2">
        <!-- Rescan Library Button - Always visible -->
        <button 
          onclick={scanLibrary}
          class="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
          disabled={loading}
          title="Rescan manga directory for new or updated files"
        >
          {#if loading}
            <LoadingSpinner size="sm" showMessage={false} />
            <span>Scanning...</span>
          {:else}
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Rescan Library
          {/if}
        </button>

        {#if showScanButton && totalManga === 0}
          <!-- Initial scan prompt for empty library -->
          <button 
            onclick={scanLibrary}
            class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            disabled={loading}
          >
            {#if loading}
              <LoadingSpinner size="sm" showMessage={false} />
              <span class="ml-2">Scanning...</span>
            {:else}
              Scan Library
            {/if}
          </button>
        {/if}
        
        <!-- Sort dropdown -->
        <div class="relative">
          <select 
            bind:value={sortBy} 
            onclick={() => handleSort(sortBy)}
            class="px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
          >
            <option value="title">Title</option>
            <option value="created_at">Date Added</option>
            <option value="updated_at">Last Updated</option>
            <option value="total_chapters">Chapter Count</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Search Bar -->
    <SearchBar on:search={handleSearch} />

    <!-- Loading State -->
    {#if loading}
      <LoadingSpinner message="Loading your manga library..." />
    
    <!-- Error State -->
    {:else if error}
      <div class="text-center py-12">
        <div class="mx-auto max-w-md">
          <div class="h-16 w-16 mx-auto mb-4 rounded-full bg-destructive/10 flex items-center justify-center">
            <svg class="h-8 w-8 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold mb-2">Unable to load manga</h2>
          <p class="text-muted-foreground mb-4">{error}</p>
          <div class="flex gap-2 justify-center">
            <button 
              onclick={loadManga}
              class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Try Again
            </button>
            {#if totalManga === 0}
              <button 
                onclick={scanLibrary}
                class="px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors"
              >
                Scan Library
              </button>
            {/if}
          </div>
        </div>
      </div>
    
    <!-- Empty State -->
    {:else if manga.length === 0}
      <div class="text-center py-12">
        <div class="mx-auto max-w-md">
          <div class="h-16 w-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center">
            <svg class="h-8 w-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold mb-2">No manga found</h2>
          <p class="text-muted-foreground mb-4">
            {#if searchTerm}
              No manga found matching "{searchTerm}". Try a different search term.
            {:else}
              Your manga library is empty. Add some manga files to your configured directory and scan your library.
            {/if}
          </p>
          <div class="flex gap-2 justify-center">
            {#if searchTerm}
              <button 
                onclick={() => { searchTerm = ''; loadManga(); }}
                class="px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors"
              >
                Clear Search
              </button>
            {/if}
            <button 
              onclick={scanLibrary}
              class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Scan Library
            </button>
          </div>
        </div>
      </div>
    
    <!-- Manga Grid -->
    {:else}
      <MangaGrid {manga} />
      
      <!-- Pagination -->
      {#if totalPages > 1}
        <div class="flex justify-center items-center gap-2">
          <button 
            onclick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            class="px-3 py-2 rounded-md border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          
          <!-- Page numbers -->
          <div class="flex gap-1">
            {#each Array.from({length: Math.min(5, totalPages)}, (_, i) => {
              const start = Math.max(1, currentPage - 2)
              const end = Math.min(totalPages, start + 4)
              return start + i <= end ? start + i : null
            }).filter((page): page is number => page !== null) as page}
              <button
                onclick={() => goToPage(page)}
                class="px-3 py-2 rounded-md text-sm transition-colors"
                class:bg-primary={page === currentPage}
                class:text-primary-foreground={page === currentPage}
                class:hover:bg-muted={page !== currentPage}
              >
                {page}
              </button>
            {/each}
          </div>
          
          <button 
            onclick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= totalPages}
            class="px-3 py-2 rounded-md border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      {/if}
    {/if}
  </div>
{/if}
