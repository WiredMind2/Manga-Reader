<script lang="ts">
  import { onMount } from 'svelte'
  import { goto } from '$app/navigation'
  import { page } from '$app/stores'
  import { apiClient } from '$lib/api/client'
  import { offlineStorage } from '$lib/services/offline'
  import type { MangaDetail, Chapter, ReadingProgress } from '$lib/api/types'
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte'

  export let data: { manga: MangaDetail; chapters: Chapter[] }

  let progress: ReadingProgress | null = null
  let loadingProgress = true
  let downloadedChapters: Set<number> = new Set()
  let downloadingChapters: Set<number> = new Set()

  $: manga = data.manga
  $: chapters = data.chapters

  // Load reading progress
  async function loadProgress() {
    try {
      progress = await apiClient.getMangaProgress(manga.id)
    } catch (error) {
      console.error('Failed to load progress:', error)
    } finally {
      loadingProgress = false
    }
  }

  async function checkDownloads() {
    for (const chapter of chapters) {
      const isDownloaded = await offlineStorage.isChapterDownloaded(chapter.id)
      if (isDownloaded) {
        downloadedChapters.add(chapter.id)
      }
    }
    downloadedChapters = downloadedChapters
  }

  async function downloadChapter(chapter: Chapter, e: Event) {
    e.stopPropagation()
    if (downloadingChapters.has(chapter.id)) return
    
    downloadingChapters.add(chapter.id)
    downloadingChapters = downloadingChapters

    try {
      const pages = await apiClient.getChapterPages(manga.id, chapter.id)
      await offlineStorage.saveManga(manga)
      await offlineStorage.saveChapter({ ...chapter, manga_id: manga.id, downloaded: true })
      
      for (const page of pages) {
        const imageUrl = apiClient.getPageImageUrl(manga.id, chapter.id, page.id)
        const response = await fetch(imageUrl)
        const blob = await response.blob()
        await offlineStorage.savePage(chapter.id, page.page_number - 1, blob)
      }
      
      downloadedChapters.add(chapter.id)
      downloadedChapters = downloadedChapters
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download failed')
    } finally {
      downloadingChapters.delete(chapter.id)
      downloadingChapters = downloadingChapters
    }
  }

  async function removeDownload(chapterId: number, e: Event) {
    e.stopPropagation()
    try {
      await offlineStorage.deleteChapter(chapterId)
      downloadedChapters.delete(chapterId)
      downloadedChapters = downloadedChapters
    } catch (error) {
      console.error('Failed to remove download:', error)
    }
  }

  function getCoverUrl() {
    return apiClient.getCoverImageUrl(manga.id, { width: 400, height: 600 })
  }

  function startReading(chapterId?: number) {
    let targetChapter: Chapter | undefined

    if (chapterId) {
      targetChapter = chapters.find(c => c.id === chapterId)
    } else if (progress && progress.chapter_id) {
      targetChapter = chapters.find(c => c.id === progress!.chapter_id)
    } else {
      targetChapter = chapters[0]
    }

    if (targetChapter) {
      goto(`/read/${manga.slug}/${targetChapter.id}`)
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString()
  }

  function getStatusColor(status?: string) {
    switch (status?.toLowerCase()) {
      case 'ongoing': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
      case 'completed': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100'
      case 'hiatus': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100'
      case 'cancelled': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100'
    }
  }

  onMount(() => {
    loadProgress()
    checkDownloads()
  })
</script>

<svelte:head>
  <title>{manga.title} - Manga Reader</title>
  <meta name="description" content={manga.description || `Read ${manga.title} manga online`} />
</svelte:head>

<div class="space-y-8">
  <!-- Back button -->
  <div>
    <button 
      on:click={() => goto('/')}
      class="flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      Back to Library
    </button>
  </div>

  <!-- Manga header -->
  <div class="flex flex-col md:flex-row gap-8">
    <!-- Cover image -->
    <div class="flex-shrink-0">
      <div class="w-64 aspect-[3/4] rounded-lg overflow-hidden shadow-lg bg-muted">
        <img
          src={getCoverUrl()}
          alt={manga.title}
          class="w-full h-full object-cover"
          on:error={(e) => {
            // Hide image and show placeholder on error
            const target = e.currentTarget as HTMLImageElement
            target.style.display = 'none'
            const placeholder = target.nextElementSibling as HTMLElement
            if (placeholder) placeholder.style.display = 'flex'
          }}
        />
        
        <!-- Fallback placeholder -->
        <div class="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5" style="display: none;">
          <div class="text-center">
            <svg class="h-16 w-16 mx-auto text-muted-foreground mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span class="text-sm text-muted-foreground font-medium">No Cover</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Manga info -->
    <div class="flex-1 space-y-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-2">{manga.title}</h1>
        
        <!-- Metadata -->
        <div class="flex flex-wrap gap-2 mb-4">
          {#if manga.status}
            <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(manga.status)}">
              {manga.status}
            </span>
          {/if}
          
          <span class="px-2 py-1 text-xs font-medium bg-muted text-muted-foreground rounded-full">
            {manga.total_chapters} Chapters
          </span>
          
          {#if manga.year}
            <span class="px-2 py-1 text-xs font-medium bg-muted text-muted-foreground rounded-full">
              {manga.year}
            </span>
          {/if}
        </div>

        <!-- Author/Artist -->
        {#if manga.author || manga.artist}
          <div class="text-sm text-muted-foreground mb-4">
            {#if manga.author}
              <div><strong>Author:</strong> {manga.author}</div>
            {/if}
            {#if manga.artist && manga.artist !== manga.author}
              <div><strong>Artist:</strong> {manga.artist}</div>
            {/if}
          </div>
        {/if}

        <!-- Description -->
        {#if manga.description}
          <p class="text-muted-foreground leading-relaxed mb-6">
            {manga.description}
          </p>
        {/if}

        <!-- Genres -->
        {#if manga.genres && manga.genres.length > 0}
          <div class="mb-6">
            <h3 class="text-sm font-medium mb-2">Genres</h3>
            <div class="flex flex-wrap gap-2">
              {#each manga.genres as genre}
                <span class="px-2 py-1 text-xs bg-primary/10 text-primary rounded-md">
                  {genre}
                </span>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Action buttons -->
        <div class="flex gap-3">
          <button 
            on:click={() => startReading()}
            class="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            {#if loadingProgress}
              <LoadingSpinner size="sm" showMessage={false} />
              <span class="ml-2">Loading...</span>
            {:else if progress}
              Continue Reading
            {:else}
              Start Reading
            {/if}
          </button>
          
          {#if progress}
            <button 
              on:click={() => startReading(chapters[0]?.id)}
              class="px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors font-medium"
            >
              Read from Beginning
            </button>
          {/if}
        </div>

        <!-- Progress info -->
        {#if progress && !loadingProgress}
          <div class="p-4 bg-muted/50 rounded-lg mt-4">
            <div class="text-sm">
              <div class="font-medium mb-1">Reading Progress</div>
              <div class="text-muted-foreground">
                {#if progress && progress.chapter_id}
                  {@const currentChapter = chapters.find(c => c.id === progress?.chapter_id)}
                  {#if currentChapter}
                    Chapter {currentChapter.chapter_number}: {currentChapter.title}
                    <span class="mx-2">•</span>
                    Page {progress.page_number}
                  {/if}
                {:else}
                  Not started yet
                {/if}
              </div>
              <div class="text-xs text-muted-foreground mt-1">
                Last read: {formatDate(progress.last_read_at)}
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Chapters list -->
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold">Chapters</h2>
      <span class="text-sm text-muted-foreground">
        {chapters.length} chapters available
      </span>
    </div>

    {#if chapters.length === 0}
      <div class="text-center py-8">
        <div class="text-muted-foreground">No chapters available</div>
      </div>
    {:else}
      <div class="space-y-2">
        {#each chapters as chapter (chapter.id)}
          <div 
            class="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
            on:click={() => startReading(chapter.id)}
            on:keydown={(e) => e.key === 'Enter' && startReading(chapter.id)}
            role="button"
            tabindex="0"
          >
            <div class="flex-1">
              <div class="font-medium">
                Chapter {chapter.chapter_number}
                {#if chapter.title !== `Chapter ${chapter.chapter_number}`}
                  - {chapter.title}
                {/if}
              </div>
              <div class="text-sm text-muted-foreground mt-1">
                {chapter.page_count} pages
                <span class="mx-2">•</span>
                Added {formatDate(chapter.created_at)}
              </div>
            </div>

            <!-- Progress indicator -->
            {#if progress?.chapter_id === chapter.id}
              <div class="flex items-center text-primary">
                <div class="w-2 h-2 bg-primary rounded-full mr-2"></div>
                <span class="text-sm font-medium">Reading</span>
              </div>
            {/if}

            <!-- Download button -->
            <button
              class="p-2 hover:bg-muted rounded-full ml-2 transition-colors z-10 relative"
              on:click={(e) => downloadedChapters.has(chapter.id) ? removeDownload(chapter.id, e) : downloadChapter(chapter, e)}
              title={downloadedChapters.has(chapter.id) ? "Remove download" : "Download chapter"}
            >
              {#if downloadingChapters.has(chapter.id)}
                 <div class="h-5 w-5 flex items-center justify-center">
                   <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                 </div>
              {:else if downloadedChapters.has(chapter.id)}
                 <svg class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                 </svg>
              {:else}
                 <svg class="h-5 w-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                 </svg>
              {/if}
            </button>

            <!-- Arrow icon -->
            <svg class="h-5 w-5 text-muted-foreground ml-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>