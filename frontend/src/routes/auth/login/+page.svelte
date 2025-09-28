<script lang="ts">
  import { onMount } from 'svelte'
  import { goto } from '$app/navigation'
  import { authStore, isAuthenticated, isLoading, authError } from '$lib/stores/auth'
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte'

  let username = ''
  let password = ''
  let formErrors: Record<string, string> = {}
  let isSubmitting = false

  // Redirect if already authenticated
  $: if ($isAuthenticated) {
    goto('/')
  }

  function validateForm(): boolean {
    formErrors = {}

    if (!username.trim()) {
      formErrors.username = 'Username is required'
    }

    if (!password) {
      formErrors.password = 'Password is required'
    } else if (password.length < 6) {
      formErrors.password = 'Password must be at least 6 characters'
    }

    return Object.keys(formErrors).length === 0
  }

  async function handleSubmit() {
    if (!validateForm()) return

    isSubmitting = true
    authStore.clearError()

    try {
      await authStore.login({ username, password })
    } catch (error) {
      // Error is handled by the auth store
      console.error('Login failed:', error)
    } finally {
      isSubmitting = false
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSubmit()
    }
  }
</script>

<svelte:head>
  <title>Login - Manga Reader</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-background px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h2 class="mt-6 text-3xl font-bold text-foreground">
        Sign in to your account
      </h2>
      <p class="mt-2 text-sm text-muted-foreground">
        Or
        <a 
          href="/auth/register" 
          class="font-medium text-primary hover:text-primary/80 transition-colors"
        >
          create a new account
        </a>
      </p>
    </div>

    <!-- Loading spinner -->
    {#if $isLoading}
      <div class="flex justify-center">
        <LoadingSpinner />
      </div>
    {:else}
      <!-- Login form -->
      <form class="mt-8 space-y-6" on:submit|preventDefault={handleSubmit}>
        <!-- Error message -->
        {#if $authError}
          <div class="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
            <p class="text-sm">{$authError}</p>
          </div>
        {/if}

        <div class="space-y-4">
          <!-- Username field -->
          <div>
            <label for="username" class="block text-sm font-medium text-foreground mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              bind:value={username}
              on:keydown={handleKeydown}
              class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              class:border-destructive={formErrors.username}
              placeholder="Enter your username"
              disabled={isSubmitting}
              required
            />
            {#if formErrors.username}
              <p class="text-sm text-destructive mt-1">{formErrors.username}</p>
            {/if}
          </div>

          <!-- Password field -->
          <div>
            <label for="password" class="block text-sm font-medium text-foreground mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              bind:value={password}
              on:keydown={handleKeydown}
              class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              class:border-destructive={formErrors.password}
              placeholder="Enter your password"
              disabled={isSubmitting}
              required
            />
            {#if formErrors.password}
              <p class="text-sm text-destructive mt-1">{formErrors.password}</p>
            {/if}
          </div>
        </div>

        <!-- Submit button -->
        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {#if isSubmitting}
              <LoadingSpinner size="sm" />
              Signing in...
            {:else}
              Sign in
            {/if}
          </button>
        </div>

        <!-- Additional links -->
        <div class="text-center">
          <p class="text-sm text-muted-foreground">
            Don't have an account?
            <a 
              href="/auth/register"
              class="font-medium text-primary hover:text-primary/80 transition-colors"
            >
              Sign up here
            </a>
          </p>
        </div>
      </form>
    {/if}
  </div>
</div>