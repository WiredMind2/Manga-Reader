<script lang="ts">
  import { goto } from '$app/navigation'
  import { apiClient } from '../api/client'
  import type { Manga } from '../api/types'
  
  export let manga: Manga[] = []
  
  function getMangaCoverUrl(mangaItem: Manga) {
    return apiClient.getCoverImageUrl(mangaItem.id, { width: 300, height: 400 })
  }
  
  function handleMangaClick(mangaItem: Manga) {
    goto(`/manga/${mangaItem.slug}`)
  }
  
  function getStatusColor(status: string) {
    switch (status?.toLowerCase()) {
      case 'ongoing': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
      case 'completed': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100'
      case 'hiatus': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100'
      case 'cancelled': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100'
    }
  }
  
  function truncateText(text: string, maxLength: number) {
    if (!text || text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }
</script>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
  {#each manga as item (item.id)}
    <div 
      class="relative overflow-hidden rounded-lg shadow-md hover:shadow-lg transition-shadow bg-card group cursor-pointer"
      on:click={() => handleMangaClick(item)}
      on:keydown={(e) => e.key === 'Enter' && handleMangaClick(item)}
      role="button"
      tabindex="0"
    >
      <!-- Cover Image -->
      <div class="aspect-[3/4] relative overflow-hidden rounded-t-lg bg-muted">
        <img
          src={getMangaCoverUrl(item)}
          alt={item.title}
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          on:error={(e) => {
            // Hide image and show placeholder on error
            const target = e.currentTarget as HTMLImageElement
            target.style.display = 'none'
            const placeholder = target.nextElementSibling as HTMLElement
            if (placeholder) placeholder.style.display = 'flex'
          }}
        />
        
        <!-- Fallback placeholder (initially hidden) -->
        <div class="absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5" style="display: none;">
          <div class="text-center">
            <svg class="h-12 w-12 mx-auto text-muted-foreground mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span class="text-xs text-muted-foreground font-medium">No Cover</span>
          </div>
        </div>
        
        <!-- Status Badge -->
        {#if item.status}
          <div class="absolute top-2 right-2">
            <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(item.status)}">
              {item.status}
            </span>
          </div>
        {/if}
        
        <!-- Chapter Count -->
        <div class="absolute bottom-2 left-2">
          <span class="px-2 py-1 text-xs font-medium bg-black/70 text-white rounded-full">
            {item.total_chapters} ch
          </span>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-4">
        <!-- Title -->
        <h3 class="font-semibold text-sm mb-1 line-clamp-2 group-hover:text-primary transition-colors">
          {truncateText(item.title, 50)}
        </h3>
        
        <!-- Author -->
        {#if item.author}
          <p class="text-xs text-muted-foreground mb-2">
            by {truncateText(item.author, 30)}
          </p>
        {/if}
        
        <!-- Description -->
        {#if item.description}
          <p class="text-xs text-muted-foreground line-clamp-2 mb-3">
            {truncateText(item.description, 80)}
          </p>
        {/if}
        
        <!-- Action Button -->
        <button 
          class="w-full px-3 py-2 text-xs font-medium bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground rounded-md transition-colors"
          on:click|stopPropagation={() => handleMangaClick(item)}
        >
          Read Now
        </button>
      </div>
    </div>
  {/each}
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>