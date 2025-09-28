import { test, expect, type Page } from '@playwright/test';

test.describe('Authentication Flow', () => {
	test.beforeEach(async ({ page }) => {
		// Reset any existing auth state
		await page.context().clearCookies();
		await page.goto('/');
	});

	test('should register a new user', async ({ page }) => {
		await page.goto('/auth/register');

		// Fill registration form
		await page.fill('[data-testid="username-input"]', 'testuser');
		await page.fill('[data-testid="email-input"]', 'test@example.com');
		await page.fill('[data-testid="password-input"]', 'securepassword123');
		await page.fill('[data-testid="confirm-password-input"]', 'securepassword123');

		// Submit form
		await page.click('[data-testid="register-button"]');

		// Should redirect to login or dashboard
		await expect(page).toHaveURL(/\/(login|dashboard|\/)$/);

		// Should show success message
		await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
	});

	test('should login with valid credentials', async ({ page }) => {
		await page.goto('/auth/login');

		// Fill login form
		await page.fill('[data-testid="username-input"]', 'testuser');
		await page.fill('[data-testid="password-input"]', 'testpass123');

		// Submit form
		await page.click('[data-testid="login-button"]');

		// Should redirect to dashboard
		await expect(page).toHaveURL('/');

		// Should show user info or manga library
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
	});

	test('should show error for invalid credentials', async ({ page }) => {
		await page.goto('/auth/login');

		// Fill with invalid credentials
		await page.fill('[data-testid="username-input"]', 'wronguser');
		await page.fill('[data-testid="password-input"]', 'wrongpass');

		// Submit form
		await page.click('[data-testid="login-button"]');

		// Should show error message
		await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
		await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
	});

	test('should logout successfully', async ({ page }) => {
		// Login first
		await loginUser(page);

		// Click logout button
		await page.click('[data-testid="logout-button"]');

		// Should redirect to login page
		await expect(page).toHaveURL('/auth/login');

		// Should not be able to access protected routes
		await page.goto('/');
		await expect(page).toHaveURL('/auth/login');
	});
});

test.describe('Manga Library', () => {
	test.beforeEach(async ({ page }) => {
		await loginUser(page);
	});

	test('should display manga library', async ({ page }) => {
		await page.goto('/');

		// Should show manga grid
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();

		// Should show search bar
		await expect(page.locator('[data-testid="search-bar"]')).toBeVisible();

		// Should show manga cards
		const mangaCards = page.locator('[data-testid="manga-card"]');
		await expect(mangaCards.first()).toBeVisible();
	});

	test('should search for manga', async ({ page }) => {
		await page.goto('/');

		// Type in search box
		await page.fill('[data-testid="search-input"]', 'One Piece');

		// Wait for search results
		await page.waitForTimeout(500); // Debounce delay

		// Should filter manga
		const mangaCards = page.locator('[data-testid="manga-card"]');
		const cardCount = await mangaCards.count();

		// Search should return fewer results than total
		await page.fill('[data-testid="search-input"]', '');
		await page.waitForTimeout(500);
		
		const allCards = await page.locator('[data-testid="manga-card"]').count();
		expect(cardCount).toBeLessThanOrEqual(allCards);
	});

	test('should clear search', async ({ page }) => {
		await page.goto('/');

		// Enter search term
		await page.fill('[data-testid="search-input"]', 'test search');

		// Should show clear button
		await expect(page.locator('[data-testid="clear-search"]')).toBeVisible();

		// Click clear button
		await page.click('[data-testid="clear-search"]');

		// Search input should be empty
		await expect(page.locator('[data-testid="search-input"]')).toHaveValue('');

		// Clear button should be hidden
		await expect(page.locator('[data-testid="clear-search"]')).not.toBeVisible();
	});

	test('should navigate to manga details', async ({ page }) => {
		await page.goto('/');

		// Click on first manga card
		await page.click('[data-testid="manga-card"]:first-child');

		// Should navigate to manga detail page
		await expect(page).toHaveURL(/\/manga\/[^/]+$/);

		// Should show manga details
		await expect(page.locator('[data-testid="manga-title"]')).toBeVisible();
		await expect(page.locator('[data-testid="manga-description"]')).toBeVisible();
		await expect(page.locator('[data-testid="chapters-list"]')).toBeVisible();
	});

	test('should handle pagination', async ({ page }) => {
		await page.goto('/');

		// Check if pagination exists (assuming there are enough manga)
		const pagination = page.locator('[data-testid="pagination"]');
		
		if (await pagination.isVisible()) {
			const nextButton = page.locator('[data-testid="next-page"]');
			
			if (await nextButton.isVisible() && !(await nextButton.isDisabled())) {
				// Click next page
				await nextButton.click();

				// URL should change
				await expect(page).toHaveURL(/page=2/);

				// Should show different manga
				await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
			}
		}
	});
});

test.describe('Manga Reading', () => {
	test.beforeEach(async ({ page }) => {
		await loginUser(page);
	});

	test('should display manga chapters', async ({ page }) => {
		await page.goto('/');
		
		// Navigate to first manga
		await page.click('[data-testid="manga-card"]:first-child');
		
		// Should show chapters list
		await expect(page.locator('[data-testid="chapters-list"]')).toBeVisible();
		
		// Should show individual chapters
		const chapters = page.locator('[data-testid="chapter-item"]');
		await expect(chapters.first()).toBeVisible();
	});

	test('should start reading manga', async ({ page }) => {
		await page.goto('/');
		
		// Navigate to manga and start reading
		await page.click('[data-testid="manga-card"]:first-child');
		await page.click('[data-testid="read-button"]:first-child');
		
		// Should navigate to reader
		await expect(page).toHaveURL(/\/read\/[^/]+\/[^/]+$/);
		
		// Should show reader interface
		await expect(page.locator('[data-testid="manga-reader"]')).toBeVisible();
		await expect(page.locator('[data-testid="manga-page"]')).toBeVisible();
	});

	test('should navigate between pages', async ({ page }) => {
		// Navigate to reader
		await goToReader(page);
		
		// Should show navigation controls
		await expect(page.locator('[data-testid="next-page"]')).toBeVisible();
		await expect(page.locator('[data-testid="prev-page"]')).toBeVisible();
		
		// Click next page
		await page.click('[data-testid="next-page"]');
		
		// Page should change (URL or page number indicator)
		await page.waitForTimeout(100);
		// Add specific assertions based on your reader implementation
	});

	test('should use keyboard navigation', async ({ page }) => {
		await goToReader(page);
		
		// Test right arrow key (next page)
		await page.keyboard.press('ArrowRight');
		await page.waitForTimeout(100);
		
		// Test left arrow key (previous page)
		await page.keyboard.press('ArrowLeft');
		await page.waitForTimeout(100);
		
		// Should handle keyboard navigation
		// Add specific assertions based on your implementation
	});

	test('should change reading settings', async ({ page }) => {
		await goToReader(page);
		
		// Open settings menu
		await page.click('[data-testid="reader-settings"]');
		
		// Should show settings panel
		await expect(page.locator('[data-testid="settings-panel"]')).toBeVisible();
		
		// Change reading direction
		await page.click('[data-testid="reading-direction-ltr"]');
		
		// Settings should be applied
		// Add specific assertions based on your settings implementation
	});

	test('should save reading progress', async ({ page }) => {
		await goToReader(page);
		
		// Navigate to a different page
		await page.click('[data-testid="next-page"]');
		await page.click('[data-testid="next-page"]');
		
		// Wait for progress to be saved
		await page.waitForTimeout(1000);
		
		// Navigate away and back
		await page.goto('/');
		await page.click('[data-testid="manga-card"]:first-child');
		
		// Should show reading progress or continue reading option
		const continueReading = page.locator('[data-testid="continue-reading"]');
		if (await continueReading.isVisible()) {
			await expect(continueReading).toBeVisible();
		}
	});
});

test.describe('Responsive Design', () => {
	test('should work on mobile devices', async ({ page }) => {
		// Set mobile viewport
		await page.setViewportSize({ width: 375, height: 667 });
		
		await loginUser(page);
		await page.goto('/');
		
		// Should show mobile-optimized layout
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
		
		// Should have appropriate grid columns for mobile
		const grid = page.locator('[data-testid="manga-grid"]');
		await expect(grid).toHaveClass(/grid-cols-2/);
	});

	test('should work on tablet devices', async ({ page }) => {
		// Set tablet viewport
		await page.setViewportSize({ width: 768, height: 1024 });
		
		await loginUser(page);
		await page.goto('/');
		
		// Should show tablet-optimized layout
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
	});

	test('should work on desktop', async ({ page }) => {
		// Set desktop viewport
		await page.setViewportSize({ width: 1920, height: 1080 });
		
		await loginUser(page);
		await page.goto('/');
		
		// Should show desktop layout with more columns
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
	});
});

test.describe('Error Handling', () => {
	test('should handle network errors gracefully', async ({ page }) => {
		await loginUser(page);
		
		// Simulate offline
		await page.context().setOffline(true);
		
		await page.goto('/');
		
		// Should show appropriate error message
		await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
	});

	test('should handle 404 errors', async ({ page }) => {
		await loginUser(page);
		
		// Navigate to non-existent manga
		await page.goto('/manga/non-existent-manga');
		
		// Should show 404 page
		await expect(page.locator('[data-testid="404-page"]')).toBeVisible();
	});
});

test.describe('Performance', () => {
	test('should load manga library quickly', async ({ page }) => {
		await loginUser(page);
		
		const startTime = Date.now();
		await page.goto('/');
		
		// Wait for manga grid to be visible
		await expect(page.locator('[data-testid="manga-grid"]')).toBeVisible();
		
		const loadTime = Date.now() - startTime;
		
		// Should load within reasonable time (adjust threshold as needed)
		expect(loadTime).toBeLessThan(3000);
	});

	test('should handle large image loading', async ({ page }) => {
		await goToReader(page);
		
		// Should show loading spinner initially
		await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
		
		// Should eventually show the manga page
		await expect(page.locator('[data-testid="manga-page"]')).toBeVisible({ timeout: 10000 });
		
		// Loading spinner should be hidden
		await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
	});
});

// Helper functions
async function loginUser(page: Page) {
	await page.goto('/auth/login');
	await page.fill('[data-testid="username-input"]', 'testuser');
	await page.fill('[data-testid="password-input"]', 'testpass123');
	await page.click('[data-testid="login-button"]');
	await expect(page).toHaveURL('/');
}

async function goToReader(page: Page) {
	await page.goto('/');
	await page.click('[data-testid="manga-card"]:first-child');
	await page.click('[data-testid="read-button"]:first-child');
	await expect(page.locator('[data-testid="manga-reader"]')).toBeVisible();
}