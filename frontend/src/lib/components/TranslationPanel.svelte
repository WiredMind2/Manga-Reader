<script lang="ts">
  import type { OcrResponse } from '$lib/api/types'
  import { createEventDispatcher } from 'svelte'

  export let translation: OcrResponse | null = null
  export let loading = false
  export let visible = true

  const dispatch = createEventDispatcher()

  function close() {
    dispatch('close')
  }
</script>

{#if visible}
  <div class="fixed right-0 top-0 h-full w-96 bg-gray-900 text-white shadow-2xl z-50 overflow-y-auto transition-transform duration-300 border-l border-gray-700">
    <!-- Header -->
    <div class="sticky top-0 bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold">Translation</h2>
      <button
        on:click={close}
        class="p-2 hover:bg-gray-700 rounded transition-colors"
        aria-label="Close translation panel"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Content -->
    <div class="p-4 space-y-4">
      {#if loading}
        <div class="flex flex-col items-center justify-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
          <p class="text-gray-400">Processing...</p>
        </div>
      {:else if translation}
        {#if translation.error}
          <div class="bg-red-900/50 border border-red-700 rounded p-4">
            <p class="text-red-200">{translation.error}</p>
          </div>
        {:else}
          <!-- Original Text -->
          <div class="bg-gray-800 rounded p-4">
            <h3 class="text-sm font-semibold text-gray-400 mb-2">Original Text</h3>
            <p class="text-lg" lang="ja">{translation.original}</p>
          </div>

          <!-- Reading -->
          {#if translation.reading}
            <div class="bg-gray-800 rounded p-4">
              <h3 class="text-sm font-semibold text-gray-400 mb-2">Reading</h3>
              <p class="text-base text-gray-300">{translation.reading}</p>
            </div>
          {/if}

          <!-- Translation -->
          <div class="bg-blue-900/30 border border-blue-700 rounded p-4">
            <h3 class="text-sm font-semibold text-blue-300 mb-2">Translation</h3>
            <p class="text-base">{translation.translation}</p>
          </div>

          <!-- Kanji Breakdown -->
          {#if translation.kanji_breakdown && translation.kanji_breakdown.length > 0}
            <div class="bg-gray-800 rounded p-4">
              <h3 class="text-sm font-semibold text-gray-400 mb-3">Kanji Breakdown</h3>
              <div class="space-y-3">
                {#each translation.kanji_breakdown as kanji}
                  <div class="border-l-2 border-purple-500 pl-3">
                    <div class="flex items-baseline space-x-2">
                      <span class="text-2xl font-bold" lang="ja">{kanji.kanji}</span>
                      <span class="text-sm text-gray-400">{kanji.reading}</span>
                    </div>
                    <p class="text-sm text-gray-300 mt-1">{kanji.meaning}</p>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Cultural Notes -->
          {#if translation.notes}
            <div class="bg-yellow-900/30 border border-yellow-700 rounded p-4">
              <h3 class="text-sm font-semibold text-yellow-300 mb-2">Cultural Notes</h3>
              <p class="text-sm text-gray-300">{translation.notes}</p>
            </div>
          {/if}
        {/if}
      {:else}
        <div class="flex flex-col items-center justify-center py-8 text-center">
          <svg class="h-16 w-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <p class="text-gray-400 mb-2">Select text to translate</p>
          <p class="text-sm text-gray-500">Draw a rectangle around Japanese text on the page</p>
        </div>
      {/if}
    </div>
  </div>
{/if}
