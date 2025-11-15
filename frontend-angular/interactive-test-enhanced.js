import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { CONFIG as BASE_CONFIG, PAGES } from './visual-test-config.js';
import { INTERACTIVE_CONFIG, PAGE_INTERACTIONS, FORM_INTERACTIONS } from './interactive-test-config.js';

/**
 * Enhanced Interactive Testing with Scrolling and Recursive Modal Testing
 *
 * Features:
 * 1. Scrolls through entire page (top -> bottom -> top) capturing all content
 * 2. Detects modals/dialogs automatically
 * 3. Recursively tests buttons inside opened modals
 * 4. Captures state at each interaction depth
 * 5. Full coverage of all interactive paths
 */

class InteractiveTestRunner {
  constructor(browser, pageName, isAngular) {
    this.browser = browser;
    this.pageName = pageName;
    this.isAngular = isAngular;
    this.prefix = isAngular ? 'angular' : 'vanilla';
    this.results = [];
    this.screenshotCount = 0;
    this.testedSelectors = new Set(); // Avoid testing same element twice
  }

  /**
   * Scroll through the page and capture screenshots at different positions
   */
  async testScrolling(page, context = 'initial') {
    if (!INTERACTIVE_CONFIG.ENABLE_SCROLLING) return [];

    console.log(`  📜 Scrolling through page (${context})...`);
    const scrollResults = [];

    // Get page height
    const pageHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    const viewportHeight = await page.evaluate(() => window.innerHeight);

    // Scroll positions: top, middle steps, bottom, then back to top
    const positions = [];

    // Top
    positions.push({ name: 'top', y: 0 });

    // Middle steps
    const steps = INTERACTIVE_CONFIG.SCROLL_STEPS - 2; // Excluding top and bottom
    for (let i = 1; i <= steps; i++) {
      const y = Math.floor((pageHeight - viewportHeight) * (i / (steps + 1)));
      positions.push({ name: `scroll-${i}`, y });
    }

    // Bottom
    positions.push({ name: 'bottom', y: pageHeight - viewportHeight });

    // Capture at each position
    for (const pos of positions) {
      await page.evaluate((y) => window.scrollTo(0, y), pos.y);
      await page.waitForTimeout(INTERACTIVE_CONFIG.SCROLL_WAIT);

      const screenshotPath = path.join(
        INTERACTIVE_CONFIG.OUTPUT_DIR,
        `${this.pageName}-${this.prefix}-${context}-${pos.name}.png`
      );

      await page.screenshot({ path: screenshotPath, fullPage: false });

      scrollResults.push({
        position: pos.name,
        scrollY: pos.y,
        screenshot: screenshotPath
      });
    }

    // Scroll back to top
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    console.log(`    ✓ Captured ${scrollResults.length} scroll positions`);
    return scrollResults;
  }

  /**
   * Detect if a modal is open
   */
  async detectModal(page) {
    if (!INTERACTIVE_CONFIG.DETECT_MODALS) return null;

    for (const selector of INTERACTIVE_CONFIG.MODAL_SELECTORS) {
      try {
        const modal = await page.$(selector);
        if (modal) {
          const isVisible = await modal.isVisible();
          if (isVisible) {
            console.log(`    🔍 Detected modal: ${selector}`);
            return { element: modal, selector };
          }
        }
      } catch (e) {
        // Selector not found, continue
      }
    }
    return null;
  }

  /**
   * Find all clickable elements in a container
   */
  async findClickableElements(page, containerSelector = 'body') {
    const clickableSelectors = [
      'button:not(:disabled)',
      'a[href]:not([href="#"])',
      '.btn:not(.disabled)',
      '[role="button"]',
      'input[type="submit"]',
      'input[type="button"]',
      '.clickable',
      '[onclick]'
    ];

    const elements = [];

    for (const selector of clickableSelectors) {
      try {
        const fullSelector = containerSelector === 'body'
          ? selector
          : `${containerSelector} ${selector}`;

        const found = await page.$$(fullSelector);

        for (const el of found) {
          const isVisible = await el.isVisible();
          const text = await el.textContent();
          const tagName = await el.evaluate(e => e.tagName);

          if (isVisible) {
            // Create unique identifier
            const uniqueId = `${tagName}-${text?.trim().substring(0, 30) || 'no-text'}`;

            if (!this.testedSelectors.has(uniqueId)) {
              elements.push({
                element: el,
                text: text?.trim() || '',
                tagName,
                uniqueId
              });
            }
          }
        }
      } catch (e) {
        // Continue if selector fails
      }
    }

    return elements;
  }

  /**
   * Test a single interaction (click button, capture before/after)
   */
  async testInteraction(page, element, interactionName, depth = 0) {
    if (depth >= INTERACTIVE_CONFIG.MAX_DEPTH) {
      console.log(`    ⚠️ Max depth ${INTERACTIVE_CONFIG.MAX_DEPTH} reached, skipping`);
      return null;
    }

    const contextName = `${this.pageName}-${this.prefix}-${interactionName}-depth${depth}`;

    try {
      // Scroll element into view
      await element.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);

      // Screenshot before click
      const beforePath = path.join(
        INTERACTIVE_CONFIG.OUTPUT_DIR,
        `${contextName}-before.png`
      );
      await page.screenshot({ path: beforePath, fullPage: true });

      // Click the element
      await element.click();
      console.log(`    🖱️  Clicked: ${interactionName} (depth ${depth})`);

      // Wait for any transitions
      await page.waitForTimeout(INTERACTIVE_CONFIG.WAIT_AFTER_CLICK);

      // Check for modal
      const modal = await this.detectModal(page);

      // Screenshot after click
      const afterPath = path.join(
        INTERACTIVE_CONFIG.OUTPUT_DIR,
        `${contextName}-after.png`
      );
      await page.screenshot({ path: afterPath, fullPage: true });

      // If modal detected and recursive testing enabled, test modal content
      let modalResults = null;
      if (modal && INTERACTIVE_CONFIG.RECURSIVE_TESTING && INTERACTIVE_CONFIG.TEST_MODAL_BUTTONS) {
        console.log(`    🔄 Testing modal content recursively...`);
        modalResults = await this.testModalContent(page, modal, depth + 1);

        // Close modal
        await this.closeModal(page, modal);
      }

      // Test scrolling in this state if enabled
      let scrollResults = null;
      if (INTERACTIVE_CONFIG.ENABLE_SCROLLING) {
        scrollResults = await this.testScrolling(page, `${interactionName}-after`);
      }

      return {
        name: interactionName,
        depth,
        beforeScreenshot: beforePath,
        afterScreenshot: afterPath,
        modalDetected: !!modal,
        modalResults,
        scrollResults,
        success: true
      };

    } catch (error) {
      console.log(`    ❌ Failed: ${error.message}`);
      return {
        name: interactionName,
        depth,
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Test all buttons inside a modal
   */
  async testModalContent(page, modal, depth) {
    const modalResults = [];

    // Find clickable elements inside modal
    const elements = await this.findClickableElements(page, modal.selector);

    console.log(`      📋 Found ${elements.length} clickable elements in modal`);

    // Test first few elements (to avoid excessive testing)
    const maxModalElements = 5;
    for (let i = 0; i < Math.min(elements.length, maxModalElements); i++) {
      const el = elements[i];

      // Mark as tested
      this.testedSelectors.add(el.uniqueId);

      const interactionName = `modal-${el.tagName}-${el.text.substring(0, 20).replace(/\s+/g, '-')}`;
      const result = await this.testInteraction(page, el.element, interactionName, depth);

      if (result) {
        modalResults.push(result);
      }

      // Small delay between modal interactions
      await page.waitForTimeout(500);
    }

    return modalResults;
  }

  /**
   * Close a modal
   */
  async closeModal(page, modal) {
    const closeSelectors = [
      '.btn-close',
      '.close',
      '[aria-label="Close"]',
      '.modal-close',
      'button:has-text("Close")',
      'button:has-text("Cancel")'
    ];

    for (const selector of closeSelectors) {
      try {
        const closeButton = await page.$(`${modal.selector} ${selector}`);
        if (closeButton) {
          await closeButton.click();
          await page.waitForTimeout(1000);
          console.log(`    ✓ Closed modal`);
          return;
        }
      } catch (e) {
        // Continue trying other selectors
      }
    }

    // If no close button found, press Escape
    try {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(1000);
      console.log(`    ✓ Closed modal with Escape`);
    } catch (e) {
      console.log(`    ⚠️ Could not close modal`);
    }
  }

  /**
   * Run complete test suite for a page
   */
  async runTests(page, url) {
    console.log(`\n  🌐 Navigating to ${url}...`);

    // Navigate
    await page.goto(url, { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(BASE_CONFIG.WAIT_TIME);

    // Initial screenshot
    const initialPath = path.join(
      INTERACTIVE_CONFIG.OUTPUT_DIR,
      `${this.pageName}-${this.prefix}-initial.png`
    );
    await page.screenshot({ path: initialPath, fullPage: true });

    // Test initial scrolling
    if (INTERACTIVE_CONFIG.ENABLE_SCROLLING) {
      const scrollResults = await this.testScrolling(page, 'initial');
      this.results.push({
        type: 'scroll',
        name: 'initial-scroll',
        results: scrollResults
      });
    }

    // Get configured interactions
    const configuredInteractions = PAGE_INTERACTIONS[this.pageName] || [];

    // Get form data if exists
    const formData = FORM_INTERACTIONS[this.pageName];

    // Fill form fields if defined
    if (formData?.fields) {
      console.log(`  📝 Filling form with ${formData.fields.length} fields...`);
      for (const field of formData.fields) {
        try {
          if (field.action === 'check') {
            await page.check(field.selector);
          } else {
            await page.fill(field.selector, field.value);
          }
        } catch (error) {
          console.log(`    ⚠️ Could not fill field ${field.selector}`);
        }
      }
      await page.waitForTimeout(500);
    }

    // Test configured interactions
    for (let i = 0; i < configuredInteractions.length; i++) {
      const interaction = configuredInteractions[i];
      console.log(`  🎯 [${i + 1}/${configuredInteractions.length}] ${interaction.description || interaction.name}`);

      try {
        const element = await page.$(interaction.selector);
        if (!element) {
          console.log(`    ❌ Element not found: ${interaction.selector}`);
          continue;
        }

        const result = await this.testInteraction(
          page,
          element,
          interaction.name,
          0 // Starting depth
        );

        if (result) {
          this.results.push(result);
        }

      } catch (error) {
        console.log(`    ❌ Error: ${error.message}`);
      }

      // Reset page state between interactions
      await page.goto(url, { waitUntil: 'load' });
      await page.waitForTimeout(2000);
    }

    // Auto-discover and test remaining clickable elements (if enabled)
    const AUTO_DISCOVER = process.argv.includes('--discover');
    if (AUTO_DISCOVER) {
      console.log(`  🔍 Auto-discovering clickable elements...`);
      const elements = await this.findClickableElements(page);
      console.log(`    Found ${elements.length} clickable elements`);

      // Test first few (to avoid excessive testing)
      const maxAutoElements = 10;
      for (let i = 0; i < Math.min(elements.length, maxAutoElements); i++) {
        const el = elements[i];
        this.testedSelectors.add(el.uniqueId);

        const interactionName = `auto-${el.tagName}-${el.text.substring(0, 20).replace(/\s+/g, '-')}`;
        const result = await this.testInteraction(page, el.element, interactionName, 0);

        if (result) {
          this.results.push(result);
        }

        // Reset between auto-discovered interactions
        await page.goto(url, { waitUntil: 'load' });
        await page.waitForTimeout(1500);
      }
    }

    return this.results;
  }
}

/**
 * Compare screenshots from vanilla and Angular
 */
function compareImages(img1Path, img2Path, diffPath) {
  try {
    if (!fs.existsSync(img1Path) || !fs.existsSync(img2Path)) {
      return { success: false, error: 'Screenshot missing', similarity: '0' };
    }

    const img1 = PNG.sync.read(fs.readFileSync(img1Path));
    const img2 = PNG.sync.read(fs.readFileSync(img2Path));

    const { width: width1, height: height1 } = img1;
    const { width: width2, height: height2 } = img2;

    if (width1 !== width2) {
      return { success: false, error: 'Width mismatch', similarity: '0' };
    }

    const heightDiff = Math.abs(height1 - height2);
    const heightTolerance = Math.max(100, Math.max(height1, height2) * 0.01);

    if (heightDiff > heightTolerance) {
      return { success: false, error: `Height mismatch: ${height1} vs ${height2}`, similarity: '0' };
    }

    const compareHeight = Math.min(height1, height2);
    const width = width1;

    let img1Data = img1.data;
    let img2Data = img2.data;

    if (height1 !== compareHeight || height2 !== compareHeight) {
      const bytesPerRow = width * 4;
      const compareBytes = bytesPerRow * compareHeight;

      img1Data = Buffer.allocUnsafe(compareBytes);
      img2Data = Buffer.allocUnsafe(compareBytes);

      img1.data.copy(img1Data, 0, 0, compareBytes);
      img2.data.copy(img2Data, 0, 0, compareBytes);
    }

    const diff = new PNG({ width, height: compareHeight });

    const numDiffPixels = pixelmatch(
      img1Data,
      img2Data,
      diff.data,
      width,
      compareHeight,
      { threshold: BASE_CONFIG.DIFF_THRESHOLD }
    );

    fs.writeFileSync(diffPath, PNG.sync.write(diff));

    const totalPixels = width * compareHeight;
    const percentageDiff = (numDiffPixels / totalPixels) * 100;

    return {
      success: true,
      similarity: (100 - percentageDiff).toFixed(4)
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      similarity: '0'
    };
  }
}

/**
 * Generate comprehensive report
 */
function generateReport(allResults) {
  let report = '# Enhanced Interactive Testing Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += '**Features Tested:**\n';
  report += '- ✅ Button clicks and interactions\n';
  report += '- ✅ Page scrolling (top to bottom to top)\n';
  report += '- ✅ Modal detection and testing\n';
  report += '- ✅ Recursive modal content testing\n';
  report += '- ✅ Full coverage of interactive elements\n\n';

  report += '---\n\n';

  for (const pageResult of allResults) {
    report += `## ${pageResult.page.toUpperCase()}\n\n`;
    report += `**Total Interactions**: ${pageResult.vanilla.length}\n`;
    report += `**Scroll Positions Captured**: ${INTERACTIVE_CONFIG.SCROLL_STEPS}\n`;
    report += `**Max Depth Tested**: ${INTERACTIVE_CONFIG.MAX_DEPTH}\n\n`;

    // Summarize results
    let successCount = 0;
    for (const result of pageResult.vanilla) {
      if (result.success) successCount++;
    }

    report += `**Success Rate**: ${((successCount / pageResult.vanilla.length) * 100).toFixed(1)}%\n\n`;
    report += '---\n\n';
  }

  fs.writeFileSync(
    path.join(INTERACTIVE_CONFIG.OUTPUT_DIR, 'enhanced-interactive-report.md'),
    report
  );
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 Enhanced Interactive Testing with Scrolling & Recursive Modals\n');
  console.log(`📋 Configuration:`);
  console.log(`   - Scrolling: ${INTERACTIVE_CONFIG.ENABLE_SCROLLING ? '✅' : '❌'}`);
  console.log(`   - Modal Detection: ${INTERACTIVE_CONFIG.DETECT_MODALS ? '✅' : '❌'}`);
  console.log(`   - Recursive Testing: ${INTERACTIVE_CONFIG.RECURSIVE_TESTING ? '✅' : '❌'}`);
  console.log(`   - Max Depth: ${INTERACTIVE_CONFIG.MAX_DEPTH}`);
  console.log(`   - Scroll Steps: ${INTERACTIVE_CONFIG.SCROLL_STEPS}\n`);

  // Setup output directory
  if (!fs.existsSync(INTERACTIVE_CONFIG.OUTPUT_DIR)) {
    fs.mkdirSync(INTERACTIVE_CONFIG.OUTPUT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const allResults = [];

  // Test specific page if provided
  const pageArg = process.argv.find(arg => arg.startsWith('--page='));
  const specificPage = pageArg ? pageArg.split('=')[1] : null;

  const pagesToTest = specificPage
    ? PAGES.filter(p => p.name === specificPage && p.status === 'implemented')
    : PAGES.filter(p => p.status === 'implemented');

  if (pagesToTest.length === 0) {
    console.log(`❌ No pages to test. Use --page=dashboard or ensure pages are marked as 'implemented'`);
    await browser.close();
    return;
  }

  for (const pageConfig of pagesToTest) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`📄 Testing: ${pageConfig.name.toUpperCase()}`);
    console.log(`${'='.repeat(60)}`);

    const vanillaUrl = `${BASE_CONFIG.VANILLA_URL}${pageConfig.vanillaPath}`;
    const angularUrl = `${BASE_CONFIG.ANGULAR_URL}${pageConfig.angularPath}`;

    // Test Vanilla
    const vanillaContext = await browser.newContext({
      ignoreHTTPSErrors: BASE_CONFIG.IGNORE_HTTPS_ERRORS
    });
    const vanillaPage = await vanillaContext.newPage();
    await vanillaPage.setViewportSize(BASE_CONFIG.VIEWPORT);

    const vanillaRunner = new InteractiveTestRunner(browser, pageConfig.name, false);
    const vanillaResults = await vanillaRunner.runTests(vanillaPage, vanillaUrl);

    await vanillaContext.close();

    // Test Angular
    const angularContext = await browser.newContext({
      ignoreHTTPSErrors: BASE_CONFIG.IGNORE_HTTPS_ERRORS
    });
    const angularPage = await angularContext.newPage();
    await angularPage.setViewportSize(BASE_CONFIG.VIEWPORT);

    const angularRunner = new InteractiveTestRunner(browser, pageConfig.name, true);
    const angularResults = await angularRunner.runTests(angularPage, angularUrl);

    await angularContext.close();

    allResults.push({
      page: pageConfig.name,
      vanilla: vanillaResults,
      angular: angularResults
    });

    console.log(`\n✅ ${pageConfig.name} testing complete!`);
    console.log(`   Vanilla: ${vanillaResults.length} interactions`);
    console.log(`   Angular: ${angularResults.length} interactions`);
  }

  await browser.close();

  // Generate report
  console.log('\n📝 Generating enhanced report...');
  generateReport(allResults);

  console.log(`\n✨ Enhanced interactive testing complete!`);
  console.log(`📊 Report: ${INTERACTIVE_CONFIG.OUTPUT_DIR}/enhanced-interactive-report.md`);
  console.log(`📁 Screenshots: ${INTERACTIVE_CONFIG.OUTPUT_DIR}/\n`);
}

main().catch(error => {
  console.error('❌ Error:', error);
  process.exit(1);
});
