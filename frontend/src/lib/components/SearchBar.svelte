<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  
  const dispatch = createEventDispatcher()
  
  let searchValue = ''
  let debounceTimer: number
  
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement
    searchValue = target.value
    
    // Debounce the search
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      dispatch('search', searchValue)
    }, 300)
  }
  
  function handleSubmit(event: Event) {
    event.preventDefault()
    dispatch('search', searchValue)
  }
  
  function clearSearch() {
    searchValue = ''
    dispatch('search', '')
  }
</script>

<form onsubmit={handleSubmit} class="relative max-w-md w-full">
  <div class="relative">
    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
      <svg class="h-5 w-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
    
    <input
      type="text"
      bind:value={searchValue}
      oninput={handleInput}
      placeholder="Search manga..."
      class="w-full pl-10 pr-10 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
    />
    
    {#if searchValue}
      <button
        type="button"
        onclick={clearSearch}
        class="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground"
        aria-label="Clear search"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    {/if}
  </div>
</form>