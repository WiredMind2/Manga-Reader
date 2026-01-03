<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { goto } from '$app/navigation'
  import { page } from '$app/stores'
  import { apiClient } from '$lib/api/client'
  import type { MangaDetail, Chapter, Page, ReadingProgress, ReadingDirection, OcrResponse } from '$lib/api/types'
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte'
  import TranslationPanel from '$lib/components/TranslationPanel.svelte'

  export let data: { manga: MangaDetail; chapters: Chapter[]; chapter: Chapter; pages: Page[] }

  let currentPageIndex = 0
  let readingDirection: ReadingDirection = 'rtl'
  let pageLoading = false
  let showControls = true
  let zoomLevel = 1
  let autoHideTimer: number | null = null
  let pageContainer: HTMLElement
  let progress: ReadingProgress | null = null
  
  // OCR mode variables
  let ocrMode = false
  let isSelecting = false
  let selectionStart: { x: number; y: number } | null = null
  let selectionEnd: { x: number; y: number } | null = null
  let ocrLoading = false
  let translationResult: OcrResponse | null = null
  let showTranslationPanel = false
  let imageElement: HTMLImageElement | null = null

  $: manga = data.manga
  $: chapters = data.chapters
  $: chapter = data.chapter
  $: pages = data.pages
  $: currentPage = pages[currentPageIndex]
  $: isFirstPage = currentPageIndex === 0
  $: isLastPage = currentPageIndex === pages.length - 1
  $: currentChapterIndex = chapters.findIndex(c => c.id === chapter.id)
  $: previousChapter = currentChapterIndex > 0 ? chapters[currentChapterIndex - 1] : null
  $: nextChapter = currentChapterIndex < chapters.length - 1 ? chapters[currentChapterIndex + 1] : null

  $: selectionRect = (ocrMode && selectionStart && selectionEnd) ? {
    x: Math.min(selectionStart.x, selectionEnd.x),
    y: Math.min(selectionStart.y, selectionEnd.y),
    width: Math.abs(selectionEnd.x - selectionStart.x),
    height: Math.abs(selectionEnd.y - selectionStart.y)
  } : null

  $: selectionStyle = selectionRect ? 
    `left: ${selectionRect.x}px; top: ${selectionRect.y}px; width: ${selectionRect.width}px; height: ${selectionRect.height}px;` : ''

  // Load reading progress
  async function loadProgress() {
    try {
      progress = await apiClient.getMangaProgress(manga.id)
      if (progress && progress.chapter_id === chapter.id) {
        currentPageIndex = Math.max(0, progress.page_number - 1)
        readingDirection = progress.reading_direction || 'rtl'
        zoomLevel = progress.zoom_level || 1
      }
    } catch (error) {
      console.error('Failed to load progress:', error)
    }
  }

  // Save reading progress
  async function saveProgress() {
    try {
      await apiClient.updateProgress(manga.id, {
        chapter_id: chapter.id,
        page_number: currentPageIndex + 1,
        reading_direction: readingDirection,
        zoom_level: zoomLevel,
        scroll_position: pageContainer?.scrollTop || 0
      })
    } catch (error) {
      console.error('Failed to save progress:', error)
    }
  }

  // Navigation functions
  function nextPage() {
    if (readingDirection === 'rtl') {
      if (currentPageIndex > 0) {
        currentPageIndex--
        saveProgress()
      } else if (previousChapter) {
        goToChapter(previousChapter.id, 'last')
      }
    } else {
      if (currentPageIndex < pages.length - 1) {
        currentPageIndex++
        saveProgress()
      } else if (nextChapter) {
        goToChapter(nextChapter.id, 'first')
      }
    }
  }

  function previousPage() {
    if (readingDirection === 'rtl') {
      if (currentPageIndex < pages.length - 1) {
        currentPageIndex++
        saveProgress()
      } else if (nextChapter) {
        goToChapter(nextChapter.id, 'first')
      }
    } else {
      if (currentPageIndex > 0) {
        currentPageIndex--
        saveProgress()
      } else if (previousChapter) {
        goToChapter(previousChapter.id, 'last')
      }
    }
  }

  function goToPage(pageIndex: number) {
    if (pageIndex >= 0 && pageIndex < pages.length) {
      currentPageIndex = pageIndex
      saveProgress()
    }
  }

  function goToChapter(chapterId: number, position: 'first' | 'last' = 'first') {
    goto(`/read/${manga.slug}/${chapterId}?page=${position}`)
  }

  // Zoom functions
  function zoomIn() {
    zoomLevel = Math.min(zoomLevel * 1.25, 3)
    saveProgress()
  }

  function zoomOut() {
    zoomLevel = Math.max(zoomLevel / 1.25, 0.5)
    saveProgress()
  }

  function resetZoom() {
    zoomLevel = 1
    saveProgress()
  }

  // Reading direction toggle
  function toggleReadingDirection() {
    readingDirection = readingDirection === 'rtl' ? 'ltr' : 'rtl'
    saveProgress()
  }

  // OCR mode functions
  function toggleOcrMode() {
    ocrMode = !ocrMode
    if (!ocrMode) {
      // Clear selection when exiting OCR mode
      selectionStart = null
      selectionEnd = null
      isSelecting = false
    } else {
      // Show translation panel when entering OCR mode
      showTranslationPanel = true
    }
  }

  function handleMouseDown(event: MouseEvent) {
    if (!ocrMode || !imageElement) return
    
    const rect = imageElement.getBoundingClientRect()
    const x = (event.clientX - rect.left) / zoomLevel
    const y = (event.clientY - rect.top) / zoomLevel
    
    isSelecting = true
    selectionStart = { x, y }
    selectionEnd = { x, y }
  }

  function handleMouseMove(event: MouseEvent) {
    if (!ocrMode || !isSelecting || !selectionStart || !imageElement) return
    
    const rect = imageElement.getBoundingClientRect()
    const x = (event.clientX - rect.left) / zoomLevel
    const y = (event.clientY - rect.top) / zoomLevel
    
    selectionEnd = { x, y }
  }

  async function handleMouseUp(event: MouseEvent) {
    if (!ocrMode || !isSelecting || !selectionStart || !selectionEnd || !imageElement || !currentPage) return
    
    isSelecting = false
    
    // Calculate normalized coordinates relative to actual image dimensions
    const rect = imageElement.getBoundingClientRect()
    const unscaledWidth = rect.width / zoomLevel
    const unscaledHeight = rect.height / zoomLevel
    
    const scaleX = imageElement.naturalWidth / unscaledWidth
    const scaleY = imageElement.naturalHeight / unscaledHeight
    
    // Get selection coordinates (normalize to top-left corner)
    const x1 = Math.min(selectionStart.x, selectionEnd.x)
    const y1 = Math.min(selectionStart.y, selectionEnd.y)
    const x2 = Math.max(selectionStart.x, selectionEnd.x)
    const y2 = Math.max(selectionStart.y, selectionEnd.y)
    
    const width = x2 - x1
    const height = y2 - y1
    
    console.log('Selected area:', { x1, y1, width, height })

    // Ignore very small selections (likely accidental clicks)
    if (width < 10 || height < 10) {
      selectionStart = null
      selectionEnd = null
      return
    }
    
    // Convert to actual image coordinates
    const actualX = Math.round(x1 * scaleX)
    const actualY = Math.round(y1 * scaleY)
    const actualWidth = Math.round(width * scaleX)
    const actualHeight = Math.round(height * scaleY)
    
    try {
      ocrLoading = true
      translationResult = await apiClient.processOcr({
        manga_id: manga.id,
        chapter_id: chapter.id,
        page_id: currentPage.id,
        x: actualX,
        y: actualY,
        width: actualWidth,
        height: actualHeight
      })
    } catch (error) {
      console.error('OCR processing failed:', error)
      translationResult = {
        original: '',
        reading: '',
        translation: 'Failed to process OCR request',
        kanji_breakdown: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    } finally {
      ocrLoading = false
    }
  }

  // Controls visibility
  function showControlsTemporarily() {
    showControls = true
    if (autoHideTimer) {
      clearTimeout(autoHideTimer)
    }
    autoHideTimer = setTimeout(() => {
      showControls = false
    }, 3000)
  }

  function toggleControls() {
    showControls = !showControls
    if (autoHideTimer) {
      clearTimeout(autoHideTimer)
      autoHideTimer = null
    }
  }

  // Get page image URL
  function getPageImageUrl(page: Page) {
    if (page.localUrl) return page.localUrl;
    return apiClient.getPageImageUrl(manga.id, chapter.id, page.id)
  }

  // Keyboard navigation
  function handleKeydown(event: KeyboardEvent) {
    // Handle OCR mode toggle and exit
    if (event.key === 'o' || event.key === 'O') {
      event.preventDefault()
      toggleOcrMode()
      return
    }
    
    if (event.key === 'Escape') {
      if (ocrMode) {
        event.preventDefault()
        toggleOcrMode()
        return
      }
      // Otherwise, exit to manga list (handled below)
    }
    
    if (ocrMode) return // Disable other shortcuts in OCR mode
    
    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault()
        if (readingDirection === 'rtl') {
          nextPage()
        } else {
          previousPage()
        }
        break
      case 'ArrowRight':
        event.preventDefault()
        if (readingDirection === 'rtl') {
          previousPage()
        } else {
          nextPage()
        }
        break
      case 'ArrowUp':
        event.preventDefault()
        previousPage()
        break
      case 'ArrowDown':
        event.preventDefault()
        nextPage()
        break
      case ' ':
        event.preventDefault()
        nextPage()
        break
      case 'Escape':
        goto(`/manga/${manga.slug}`)
        break
      case 'f':
        toggleControls()
        break
      case 'r':
        toggleReadingDirection()
        break
      case '+':
      case '=':
        zoomIn()
        break
      case '-':
        zoomOut()
        break
      case '0':
        resetZoom()
        break
    }
    showControlsTemporarily()
  }

  // Mouse/touch navigation
  function handleImageClick(event: MouseEvent) {
    // Don't navigate in OCR mode
    if (ocrMode) return
    
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const x = event.clientX - rect.left
    const clickPosition = x / rect.width

    if (clickPosition < 0.3) {
      previousPage()
    } else if (clickPosition > 0.7) {
      nextPage()
    } else {
      toggleControls()
    }
  }

  // Initialize page from URL params
  function initializePage() {
    const urlParams = new URLSearchParams(window.location.search)
    const pageParam = urlParams.get('page')
    
    if (pageParam === 'last') {
      currentPageIndex = pages.length - 1
    } else if (pageParam && !isNaN(parseInt(pageParam))) {
      currentPageIndex = Math.max(0, Math.min(parseInt(pageParam) - 1, pages.length - 1))
    }
  }

  onMount(() => {
    loadProgress()
    initializePage()
    showControlsTemporarily()
    
    // Add keyboard event listener
    window.addEventListener('keydown', handleKeydown)
    
    // Add mouse move listener to show controls
    window.addEventListener('mousemove', showControlsTemporarily)
    
    return () => {
      window.removeEventListener('keydown', handleKeydown)
      window.removeEventListener('mousemove', showControlsTemporarily)
      if (autoHideTimer) {
        clearTimeout(autoHideTimer)
      }
    }
  })

  onDestroy(() => {
    if (autoHideTimer) {
      clearTimeout(autoHideTimer)
    }
  })
</script>

<svelte:head>
  <title>{manga.title} - Chapter {chapter.chapter_number} - Manga Reader</title>
  <meta name="description" content="Reading {manga.title} Chapter {chapter.chapter_number}" />
</svelte:head>

<svelte:window 
  on:mousemove={handleMouseMove} 
  on:mouseup={handleMouseUp} 
/>

<div class="fixed inset-0 bg-black text-white overflow-hidden" class:reading-rtl={readingDirection === 'rtl'} class:ocr-active={ocrMode}>
  <!-- Page container -->
  <div 
    bind:this={pageContainer}
    class="h-full flex items-center justify-center overflow-auto"
    class:cursor-crosshair={ocrMode}
    class:cursor-pointer={!ocrMode}
    on:click={handleImageClick}
    on:keydown={(e) => e.key === 'Enter' && handleImageClick(e as any)}
    role="button"
    tabindex="0"
    aria-label={ocrMode ? "OCR mode - select text area" : "Manga page - click left or right to navigate"}
  >
    <div class="relative inline-block transition-transform duration-200" style="transform: scale({zoomLevel})">
      {#if currentPage}
        <img
          bind:this={imageElement}
          src={getPageImageUrl(currentPage)}
          alt="Page {currentPageIndex + 1}"
          class="manga-page max-w-full max-h-full"
          draggable={!ocrMode}
          loading="lazy"
          on:load={() => pageLoading = false}
          on:loadstart={() => pageLoading = true}
          on:mousedown={handleMouseDown}
        />
        
        <!-- Selection rectangle overlay -->
        {#if selectionRect}
          <div 
            class="absolute border-2 border-blue-500 bg-blue-500/20 pointer-events-none"
            style={selectionStyle}
          ></div>
        {/if}
      {/if}

      {#if pageLoading}
        <div class="absolute inset-0 flex items-center justify-center bg-black/50">
          <LoadingSpinner message="Loading page..." />
        </div>
      {/if}
    </div>
  </div>

  <!-- Navigation controls -->
  <div 
    class="fixed inset-0 pointer-events-none transition-opacity duration-300"
    class:opacity-0={!showControls}
    class:opacity-100={showControls}
  >
    <!-- Top bar -->
    <div class="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4 pointer-events-auto">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button 
            on:click={() => goto(`/manga/${manga.slug}`)}
            class="flex items-center space-x-2 text-white/80 hover:text-white transition-colors"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            <span class="hidden sm:inline">Back</span>
          </button>
          
          <div class="text-white">
            <div class="font-medium">{manga.title}</div>
            <div class="text-sm text-white/60">
              Chapter {chapter.chapter_number}
              {#if chapter.title !== `Chapter ${chapter.chapter_number}`}
                - {chapter.title}
              {/if}
            </div>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <!-- OCR mode toggle -->
          <button
            on:click={toggleOcrMode}
            class="p-2 rounded transition-colors {ocrMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-white/20 hover:bg-white/30'}"
            title="Toggle OCR mode (O)"
            aria-label="Toggle OCR mode"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </button>

          <!-- Reading direction toggle -->
          <button
            on:click={toggleReadingDirection}
            class="p-2 rounded bg-white/20 hover:bg-white/30 transition-colors"
            title="Toggle reading direction"
            aria-label="Toggle reading direction"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </button>

          <!-- Zoom controls -->
          <div class="flex items-center space-x-1 bg-white/20 rounded">
            <button
              on:click={zoomOut}
              class="p-2 hover:bg-white/10 transition-colors"
              title="Zoom out"
              aria-label="Zoom out"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
              </svg>
            </button>
            
            <button
              on:click={resetZoom}
              class="px-3 py-2 text-sm hover:bg-white/10 transition-colors"
              title="Reset zoom"
            >
              {Math.round(zoomLevel * 100)}%
            </button>
            
            <button
              on:click={zoomIn}
              class="p-2 hover:bg-white/10 transition-colors"
              title="Zoom in"
              aria-label="Zoom in"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom bar -->
    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 pointer-events-auto">
      <div class="flex items-center justify-between">
        <!-- Chapter navigation -->
        <div class="flex items-center space-x-2">
          {#if previousChapter}
            <button
              on:click={() => goToChapter(previousChapter.id, 'last')}
              class="px-3 py-2 bg-white/20 hover:bg-white/30 rounded transition-colors text-sm"
            >
              {#if readingDirection === 'rtl'}
                Next Chapter
              {:else}
                Previous Chapter
              {/if}
            </button>
          {/if}
          
          {#if nextChapter}
            <button
              on:click={() => goToChapter(nextChapter.id, 'first')}
              class="px-3 py-2 bg-white/20 hover:bg-white/30 rounded transition-colors text-sm"
            >
              {#if readingDirection === 'rtl'}
                Previous Chapter
              {:else}
                Next Chapter
              {/if}
            </button>
          {/if}
        </div>

        <!-- Page navigation -->
        <div class="flex items-center space-x-4">
          <button
            on:click={previousPage}
            disabled={readingDirection === 'rtl' ? isLastPage : isFirstPage}
            class="p-2 rounded bg-white/20 hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div class="text-white text-sm">
            <span>Page {currentPageIndex + 1} of {pages.length}</span>
          </div>

          <button
            on:click={nextPage}
            disabled={readingDirection === 'rtl' ? isFirstPage : isLastPage}
            class="p-2 rounded bg-white/20 hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Page progress -->
        <div class="flex-1 mx-8 max-w-md">
          <div class="bg-white/20 rounded-full h-2">
            <div 
              class="bg-white rounded-full h-2 transition-all duration-300"
              style="width: {((currentPageIndex + 1) / pages.length) * 100}%"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Keyboard shortcuts help -->
  <div class="fixed bottom-4 right-4 text-xs text-white/60 pointer-events-none" class:right-[25rem]={showTranslationPanel && ocrMode}>
    <div>← → Arrow keys or click to navigate</div>
    <div>F: Toggle controls • R: Reading direction</div>
    <div>O: OCR mode • +/-: Zoom • ESC: Exit</div>
  </div>
  
  <!-- Translation Panel -->
  <TranslationPanel 
    bind:visible={showTranslationPanel}
    translation={translationResult}
    loading={ocrLoading}
    on:close={() => { showTranslationPanel = false; ocrMode = false }}
  />
</div>

<style>
  .manga-page {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }

  .reading-rtl {
    direction: rtl;
  }
  
  .ocr-active {
    user-select: none;
  }
  
  .cursor-crosshair {
    cursor: crosshair;
  }
  
  .cursor-pointer {
    cursor: pointer;
  }
</style>