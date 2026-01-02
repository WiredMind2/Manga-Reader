import { test, expect, type Page } from '@playwright/test';

// Mobile device configurations for testing
const mobileDevices = [
  { name: 'iPhone 12', viewport: { width: 390, height: 844 } },
  { name: 'Samsung Galaxy S21', viewport: { width: 384, height: 854 } },
  { name: 'iPad', viewport: { width: 768, height: 1024 } }
];

test.describe('Mobile Responsiveness', () => {
  
  mobileDevices.forEach(device => {
    test.describe(`${device.name} - ${device.viewport.width}x${device.viewport.height}`, () => {
      
      test.beforeEach(async ({ page }) => {
        await page.setViewportSize(device.viewport);
        
        // Mock API responses for consistent testing
        await page.route('**/api/auth/login', async route => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              access_token: 'mock-token',
              token_type: 'bearer'
            })
          });
        });

        await page.route('**/api/manga', async route => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              items: [
                {
                  id: 1,
                  title: 'One Piece',
                  slug: 'one-piece',
                  author: 'Eiichiro Oda',
                  description: 'A story about pirates',
                  total_chapters: 1000,
                  status: 'ongoing',
                  cover_image: '/covers/one-piece.jpg'
                },
                {
                  id: 2,
                  title: 'Very Long Manga Title That Should Be Truncated On Mobile',
                  slug: 'long-title',
                  author: 'Very Long Author Name That Should Also Be Truncated',
                  description: 'A very long description that tests text wrapping and truncation behavior on mobile devices',
                  total_chapters: 50,
                  status: 'completed',
                  cover_image: '/covers/long-title.jpg'
                }
              ],
              total: 2,
              page: 1,
              size: 20,
              pages: 1
            })
          });
        });

        await page.route('**/images/**', async route => {
          // Mock image responses
          await route.fulfill({
            status: 200,
            contentType: 'image/jpeg',
            body: Buffer.from('mock-image-data')
          });
        });
      });

      test('login form is mobile-friendly', async ({ page }) => {
        await page.goto('/auth/login');
        
        // Check form is properly sized for mobile
        const form = page.locator('form');
        await expect(form).toBeVisible();
        
        // Input fields should be touch-friendly
        const usernameInput = page.locator('input[name="username"]');
        const passwordInput = page.locator('input[name="password"]');
        
        await expect(usernameInput).toBeVisible();
        await expect(passwordInput).toBeVisible();
        
        // Check input field heights are adequate for touch
        const usernameBox = await usernameInput.boundingBox();
        const passwordBox = await passwordInput.boundingBox();
        
        expect(usernameBox?.height).toBeGreaterThanOrEqual(44); // iOS minimum touch target
        expect(passwordBox?.height).toBeGreaterThanOrEqual(44);
        
        // Submit button should be large enough for touch
        const submitButton = page.locator('button[type="submit"]');
        await expect(submitButton).toBeVisible();
        
        const buttonBox = await submitButton.boundingBox();
        expect(buttonBox?.height).toBeGreaterThanOrEqual(44);
      });

      test('manga grid adapts to mobile layout', async ({ page }) => {
        // Login first
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Check grid layout
        const grid = page.locator('[data-testid="manga-grid"]').first();
        await expect(grid).toBeVisible();
        
        // Manga cards should be visible and properly sized
        const mangaCards = page.locator('[data-testid="manga-card"]');
        await expect(mangaCards).toHaveCount(2);
        
        // Check first card dimensions
        const firstCard = mangaCards.first();
        const cardBox = await firstCard.boundingBox();
        
        // Card should not overflow viewport width
        expect(cardBox?.width).toBeLessThanOrEqual(device.viewport.width);
        
        // Check that cards are arranged in mobile-appropriate columns
        const allCards = await mangaCards.all();
        const cardBoxes = await Promise.all(allCards.map(card => card.boundingBox()));
        
        // For mobile, expect fewer columns (cards should be wider)
        if (device.viewport.width <= 768) {
          // Check that cards are arranged in 2-3 columns max
          const cardsPerRow = cardBoxes.filter(box => 
            box && Math.abs(box.y - cardBoxes[0]!.y) < 10
          ).length;
          expect(cardsPerRow).toBeLessThanOrEqual(3);
        }
      });

      test('manga cards have proper touch targets', async ({ page }) => {
        // Login and navigate to manga grid
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        const mangaCard = page.locator('[data-testid="manga-card"]').first();
        await expect(mangaCard).toBeVisible();
        
        // Card should be large enough for touch interaction
        const cardBox = await mangaCard.boundingBox();
        expect(cardBox?.height).toBeGreaterThanOrEqual(200);
        expect(cardBox?.width).toBeGreaterThanOrEqual(120);
        
        // Tap the card (mobile touch simulation)
        await mangaCard.tap();
        
        // Should navigate to manga detail page
        await expect(page).toHaveURL(/\/manga\/.+/);
      });

      test('text is readable on mobile screens', async ({ page }) => {
        // Login and view manga grid
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Check text elements are visible and readable
        const mangaTitle = page.locator('[data-testid="manga-title"]').first();
        await expect(mangaTitle).toBeVisible();
        
        // Title should not be too small
        const titleStyles = await mangaTitle.evaluate(el => 
          window.getComputedStyle(el)
        );
        const fontSize = parseFloat(titleStyles.fontSize);
        expect(fontSize).toBeGreaterThanOrEqual(14); // Minimum readable size
        
        // Author text
        const authorText = page.locator('[data-testid="manga-author"]').first();
        if (await authorText.count() > 0) {
          const authorStyles = await authorText.evaluate(el => 
            window.getComputedStyle(el)
          );
          const authorFontSize = parseFloat(authorStyles.fontSize);
          expect(authorFontSize).toBeGreaterThanOrEqual(12);
        }
      });

      test('long titles and text are properly truncated', async ({ page }) => {
        // Login and view manga grid
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Find the manga with long title
        const longTitleCard = page.locator('[data-testid="manga-card"]').filter({ 
          hasText: 'Very Long Manga Title' 
        });
        await expect(longTitleCard).toBeVisible();
        
        // Title should be truncated with ellipsis
        const titleElement = longTitleCard.locator('[data-testid="manga-title"]');
        const titleText = await titleElement.textContent();
        
        if (device.viewport.width <= 390) {
          // On very small screens, title should be truncated
          expect(titleText).toMatch(/\.\.\.$/);
        }
      });

      test('search functionality works on mobile', async ({ page }) => {
        // Login first
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Find search bar
        const searchInput = page.locator('input[placeholder*="Search"]');
        await expect(searchInput).toBeVisible();
        
        // Search input should be touch-friendly
        const searchBox = await searchInput.boundingBox();
        expect(searchBox?.height).toBeGreaterThanOrEqual(44);
        
        // Test search functionality
        await searchInput.tap();
        await searchInput.fill('One Piece');
        
        // Should trigger search (debounced)
        await page.waitForTimeout(1000);
      });

      test('navigation is mobile-friendly', async ({ page }) => {
        // Login and check navigation
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Check for mobile navigation elements
        const nav = page.locator('nav').first();
        if (await nav.count() > 0) {
          await expect(nav).toBeVisible();
          
          // Navigation items should be touch-friendly
          const navItems = page.locator('nav a, nav button');
          const count = await navItems.count();
          
          for (let i = 0; i < count; i++) {
            const item = navItems.nth(i);
            if (await item.isVisible()) {
              const itemBox = await item.boundingBox();
              expect(itemBox?.height).toBeGreaterThanOrEqual(36);
            }
          }
        }
      });

      test('orientation changes are handled properly', async ({ page }) => {
        // Start in portrait
        await page.setViewportSize({ 
          width: device.viewport.height, 
          height: device.viewport.width 
        });
        
        // Login and view content
        await page.goto('/auth/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'password');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/');
        
        // Check that content is still properly laid out in landscape
        const mangaCards = page.locator('[data-testid="manga-card"]');
        await expect(mangaCards.first()).toBeVisible();
        
        // In landscape, might show more columns
        const cardCount = await mangaCards.count();
        expect(cardCount).toBeGreaterThan(0);
      });
    });
  });
});

test.describe('Mobile Performance', () => {
  test('page loads quickly on mobile networks', async ({ page }) => {
    // Simulate slow 3G network
    await page.route('**/*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 100)); // Add 100ms delay
      await route.continue();
    });

    const startTime = Date.now();
    
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/');
    await page.waitForSelector('[data-testid="manga-card"]');
    
    const loadTime = Date.now() - startTime;
    
    // Should load within reasonable time even on slow network
    expect(loadTime).toBeLessThan(10000); // 10 second max
  });

  test('images load progressively on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    
    // Login and navigate to manga grid  
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/');
    
    // Cover images should load
    const coverImages = page.locator('[data-testid="manga-cover"]');
    const firstImage = coverImages.first();
    
    // Wait for image to load
    await expect(firstImage).toBeVisible();
    
    // Should have proper loading behavior
    const isLoaded = await firstImage.evaluate((img: HTMLImageElement) => img.complete);
    expect(isLoaded).toBe(true);
  });
});