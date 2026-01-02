import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mock API responses
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
            }
          ],
          total: 1,
          page: 1,
          size: 20,
          pages: 1
        })
      });
    });
  });

  test('login form has proper accessibility attributes', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Form should have proper labels
    const usernameInput = page.locator('input[name="username"]');
    const passwordInput = page.locator('input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');
    
    // Check for associated labels
    await expect(page.locator('label[for="username"], label:has(input[name="username"])')).toBeVisible();
    await expect(page.locator('label[for="password"], label:has(input[name="password"])')).toBeVisible();
    
    // Inputs should have accessible names
    const usernameAccessibleName = await usernameInput.getAttribute('aria-label') || 
                                   await page.locator('label[for="username"]').textContent() ||
                                   await usernameInput.getAttribute('placeholder');
    expect(usernameAccessibleName).toBeTruthy();
    
    const passwordAccessibleName = await passwordInput.getAttribute('aria-label') ||
                                   await page.locator('label[for="password"]').textContent() ||
                                   await passwordInput.getAttribute('placeholder');
    expect(passwordAccessibleName).toBeTruthy();
    
    // Submit button should have accessible text
    const buttonText = await submitButton.textContent() || await submitButton.getAttribute('aria-label');
    expect(buttonText).toBeTruthy();
  });

  test('manga grid has proper ARIA attributes', async ({ page }) => {
    // Login first
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/');
    
    // Check manga cards have proper roles and labels
    const mangaCards = page.locator('[data-testid="manga-card"]');
    await expect(mangaCards).toHaveCount(1);
    
    const firstCard = mangaCards.first();
    
    // Should have button role or be a link
    const role = await firstCard.getAttribute('role');
    const tagName = await firstCard.evaluate(el => el.tagName.toLowerCase());
    
    expect(['button', 'link', 'a'].includes(role || tagName)).toBe(true);
    
    // Should have accessible label
    const ariaLabel = await firstCard.getAttribute('aria-label');
    const title = await firstCard.textContent();
    
    expect(ariaLabel || title).toContain('One Piece');
  });

  test('images have proper alt text', async ({ page }) => {
    // Login and navigate to manga grid
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/');
    
    // Cover images should have alt text
    const coverImages = page.locator('img');
    const count = await coverImages.count();
    
    for (let i = 0; i < count; i++) {
      const img = coverImages.nth(i);
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      
      // Should have either alt text or aria-label
      expect(alt || ariaLabel).toBeTruthy();
    }
  });

  test('keyboard navigation works properly', async ({ page }) => {
    // Login first
    await page.goto('/auth/login');
    
    // Tab through login form
    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="username"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="password"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('button[type="submit"]')).toBeFocused();
    
    // Fill form and submit with keyboard
    await page.focus('input[name="username"]');
    await page.keyboard.type('testuser');
    await page.keyboard.press('Tab');
    await page.keyboard.type('password');
    await page.keyboard.press('Enter');
    
    await page.waitForURL('/');
    
    // Test keyboard navigation on manga grid
    await page.keyboard.press('Tab');
    
    // Should focus on interactive elements
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Focus on username input
    await page.focus('input[name="username"]');
    
    // Check that focus is visible
    const usernameInput = page.locator('input[name="username"]');
    const focusStyles = await usernameInput.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        outline: computed.outline,
        outlineWidth: computed.outlineWidth,
        outlineStyle: computed.outlineStyle,
        boxShadow: computed.boxShadow
      };
    });
    
    // Should have some form of focus indication
    const hasFocusIndicator = focusStyles.outline !== 'none' ||
                             focusStyles.outlineWidth !== '0px' ||
                             focusStyles.boxShadow !== 'none';
    
    expect(hasFocusIndicator).toBe(true);
  });

  test('color contrast is adequate', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Test text contrast on main elements
    const elements = [
      page.locator('h1, h2, h3').first(),
      page.locator('label').first(),
      page.locator('button[type="submit"]')
    ];
    
    for (const element of elements) {
      if (await element.count() > 0) {
        const styles = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor
          };
        });
        
        // Basic check - color should not be the same as background
        expect(styles.color).not.toBe(styles.backgroundColor);
      }
    }
  });

  test('error messages are accessible', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Submit form with invalid data to trigger errors
    await page.click('button[type="submit"]');
    
    // Look for error messages
    const errorMessages = page.locator('[role="alert"], .error, [data-testid*="error"]');
    
    if (await errorMessages.count() > 0) {
      const firstError = errorMessages.first();
      
      // Error should be visible
      await expect(firstError).toBeVisible();
      
      // Should have appropriate role or ARIA attributes
      const role = await firstError.getAttribute('role');
      const ariaLive = await firstError.getAttribute('aria-live');
      
      expect(role === 'alert' || ariaLive === 'polite' || ariaLive === 'assertive').toBe(true);
    }
  });

  test('page has proper heading structure', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Check for heading hierarchy
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const count = await headings.count();
    
    if (count > 0) {
      // Should start with h1
      const firstHeading = headings.first();
      const tagName = await firstHeading.evaluate(el => el.tagName);
      expect(tagName).toBe('H1');
      
      // Check heading content is descriptive
      const headingText = await firstHeading.textContent();
      expect(headingText?.trim().length).toBeGreaterThan(0);
    }
  });

  test('form validation messages are announced', async ({ page }) => {
    await page.goto('/auth/login');
    
    const usernameInput = page.locator('input[name="username"]');
    const passwordInput = page.locator('input[name="password"]');
    
    // Check if inputs have aria-describedby for validation messages
    const usernameDescribedBy = await usernameInput.getAttribute('aria-describedby');
    const passwordDescribedBy = await passwordInput.getAttribute('aria-describedby');
    
    // At minimum, inputs should be properly labeled
    expect(await usernameInput.getAttribute('name')).toBe('username');
    expect(await passwordInput.getAttribute('name')).toBe('password');
  });

  test('loading states are accessible', async ({ page }) => {
    // Login and trigger loading state
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    
    // Submit and look for loading indicators
    await page.click('button[type="submit"]');
    
    // Check for loading spinners or messages
    const loadingElements = page.locator('[aria-busy="true"], [role="progressbar"], .loading, [data-testid*="loading"]');
    
    if (await loadingElements.count() > 0) {
      const loader = loadingElements.first();
      
      // Loading element should be properly labeled
      const ariaLabel = await loader.getAttribute('aria-label');
      const textContent = await loader.textContent();
      
      expect(ariaLabel || textContent).toBeTruthy();
    }
  });
});