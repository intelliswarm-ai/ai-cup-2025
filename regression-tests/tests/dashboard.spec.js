const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs-extra');
const { compareScreenshots, compareStatistics, compareLayout } = require('../utils/comparison-helpers');

const VANILLA_URL = 'http://localhost:80';
const ANGULAR_URL = 'http://localhost:4200/dashboard';
const SCREENSHOTS_DIR = path.join(__dirname, '../test-results/screenshots');

test.describe('Dashboard Page Regression Tests', () => {

  test.beforeAll(async () => {
    // Ensure screenshots directory exists
    await fs.ensureDir(SCREENSHOTS_DIR);
  });

  test('Dashboard - Visual Comparison', async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });

    // Create two pages for comparison
    const vanillaPage = await context.newPage();
    const angularPage = await context.newPage();

    try {
      // Navigate to both dashboards
      await vanillaPage.goto(VANILLA_URL, { waitUntil: 'networkidle' });
      await angularPage.goto(ANGULAR_URL, { waitUntil: 'networkidle' });

      // Wait for content to load
      await vanillaPage.waitForTimeout(2000);
      await angularPage.waitForTimeout(2000);

      // Take screenshots
      const vanillaScreenshot = await vanillaPage.screenshot({ fullPage: true });
      const angularScreenshot = await angularPage.screenshot({ fullPage: true });

      // Save screenshots
      const vanillaPath = path.join(SCREENSHOTS_DIR, 'dashboard-vanilla.png');
      const angularPath = path.join(SCREENSHOTS_DIR, 'dashboard-angular.png');
      const diffPath = path.join(SCREENSHOTS_DIR, 'dashboard-diff.png');

      await fs.writeFile(vanillaPath, vanillaScreenshot);
      await fs.writeFile(angularPath, angularScreenshot);

      // Compare screenshots
      const comparison = await compareScreenshots(vanillaScreenshot, angularScreenshot, diffPath);

      console.log(`Visual Comparison:`);
      console.log(`  - Diff Pixels: ${comparison.diffPixels}`);
      console.log(`  - Diff Percentage: ${comparison.diffPercentage.toFixed(2)}%`);

      // Allow up to 15% visual difference due to styling/framework differences
      expect(comparison.diffPercentage).toBeLessThan(15);

    } finally {
      await vanillaPage.close();
      await angularPage.close();
      await context.close();
    }
  });

  test('Dashboard - Statistics Data Comparison', async ({ browser }) => {
    const context = await browser.newContext();
    const vanillaPage = await context.newPage();
    const angularPage = await context.newPage();

    try {
      // Navigate to both dashboards
      await vanillaPage.goto(VANILLA_URL, { waitUntil: 'networkidle' });
      await angularPage.goto(ANGULAR_URL, { waitUntil: 'networkidle' });

      // Wait for data to load
      await vanillaPage.waitForTimeout(2000);
      await angularPage.waitForTimeout(3000); // Angular might need more time

      // Compare statistics
      const statsComparison = await compareStatistics(vanillaPage, angularPage);

      console.log('Statistics Comparison:');
      console.log('  Vanilla:', statsComparison.vanillaStats);
      console.log('  Angular:', statsComparison.angularStats);

      if (!statsComparison.match) {
        console.log('  Differences:', statsComparison.differences);
      }

      // Statistics should match exactly
      expect(statsComparison.match).toBe(true);

      if (!statsComparison.match) {
        statsComparison.differences.forEach(diff => {
          console.error(`Mismatch in ${diff.field}: Vanilla=${diff.vanilla}, Angular=${diff.angular}`);
        });
      }

    } finally {
      await vanillaPage.close();
      await angularPage.close();
      await context.close();
    }
  });

  test('Dashboard - Layout Structure Comparison', async ({ browser }) => {
    const context = await browser.newContext();
    const vanillaPage = await context.newPage();
    const angularPage = await context.newPage();

    try {
      await vanillaPage.goto(VANILLA_URL, { waitUntil: 'networkidle' });
      await angularPage.goto(ANGULAR_URL, { waitUntil: 'networkidle' });

      await vanillaPage.waitForTimeout(2000);
      await angularPage.waitForTimeout(2000);

      const layoutComparison = await compareLayout(vanillaPage, angularPage);

      console.log('Layout Comparison:');
      console.log('  Vanilla:', layoutComparison.vanillaLayout);
      console.log('  Angular:', layoutComparison.angularLayout);

      if (!layoutComparison.match) {
        console.log('  Differences:', layoutComparison.differences);
      }

      // Allow minor differences in layout structure
      expect(layoutComparison.differences.length).toBeLessThanOrEqual(2);

    } finally {
      await vanillaPage.close();
      await angularPage.close();
      await context.close();
    }
  });

  test('Dashboard - Loading States', async ({ browser }) => {
    const context = await browser.newContext();
    const angularPage = await context.newPage();

    try {
      // Slow down network to test loading states
      await angularPage.route('**/api/statistics', route => {
        setTimeout(() => route.continue(), 1000);
      });

      await angularPage.goto(ANGULAR_URL);

      // Check for loading spinner
      const loadingSpinner = angularPage.locator('.spinner-border, [role="status"]');
      await expect(loadingSpinner).toBeVisible({ timeout: 2000 });

      // Wait for data to load
      await angularPage.waitForTimeout(3000);

      // Loading spinner should disappear
      await expect(loadingSpinner).not.toBeVisible();

      // Stats cards should be visible
      const statsCards = angularPage.locator('.card');
      await expect(statsCards.first()).toBeVisible();

    } finally {
      await angularPage.close();
      await context.close();
    }
  });

  test('Dashboard - Responsive Layout', async ({ browser }) => {
    const viewports = [
      { name: 'Desktop', width: 1920, height: 1080 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Mobile', width: 375, height: 667 }
    ];

    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();

      try {
        await page.goto(ANGULAR_URL, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        // Take screenshot for each viewport
        const screenshot = await page.screenshot({ fullPage: true });
        const screenshotPath = path.join(SCREENSHOTS_DIR, `dashboard-${viewport.name.toLowerCase()}.png`);
        await fs.writeFile(screenshotPath, screenshot);

        // Check that stats cards are visible
        const statsCards = page.locator('.card');
        const count = await statsCards.count();
        expect(count).toBeGreaterThanOrEqual(4);

        console.log(`${viewport.name} (${viewport.width}x${viewport.height}): ${count} cards visible`);

      } finally {
        await page.close();
        await context.close();
      }
    }
  });

  test('Dashboard - API Integration', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Track API calls
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/statistics')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          timestamp: new Date()
        });
      }
    });

    try {
      await page.goto(ANGULAR_URL, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      // Should have made at least one API call to /api/statistics
      expect(apiCalls.length).toBeGreaterThanOrEqual(1);

      console.log('API Calls:', apiCalls);

      // Verify response
      const response = await page.waitForResponse(
        response => response.url().includes('/api/statistics'),
        { timeout: 5000 }
      );

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('total_emails');
      expect(data.total_emails).toBeGreaterThan(0);

      console.log('Statistics Data:', data);

    } finally {
      await page.close();
      await context.close();
    }
  });

  test('Dashboard - Error Handling', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      // Simulate API error
      await page.route('**/api/statistics', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });

      await page.goto(ANGULAR_URL);
      await page.waitForTimeout(3000);

      // Check if error is handled gracefully (no crash, shows 0 or error message)
      const pageContent = await page.content();
      expect(pageContent).not.toContain('undefined');
      expect(pageContent).not.toContain('NaN');

      console.log('Error handling test passed - no crashes or undefined values');

    } finally {
      await page.close();
      await context.close();
    }
  });
});
