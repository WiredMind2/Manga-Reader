<script lang="ts">
  export let message = "Loading..."
  export let size: 'sm' | 'md' | 'lg' = 'md'
  export let showMessage = true

  $: sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-12 h-12 border-4', 
    lg: 'w-16 h-16 border-4'
  }

  $: containerClasses = size === 'sm' ? 'inline-flex items-center gap-2' : 'flex flex-col items-center justify-center py-12'
</script>

<div class={containerClasses}>
  <div class="relative">
    <!-- Spinning circle -->
    <div class="{sizeClasses[size]} border-border border-t-primary rounded-full animate-spin"></div>
  </div>
  
  {#if showMessage && (size !== 'sm' || message !== 'Loading...')}
    <p class="mt-4 text-muted-foreground text-sm" class:mt-0={size === 'sm'} class:ml-2={size === 'sm'}>{message}</p>
  {/if}
</div>

<style>
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>