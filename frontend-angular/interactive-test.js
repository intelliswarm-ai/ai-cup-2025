import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { CONFIG as BASE_CONFIG, PAGES } from './visual-test-config.js';
import { INTERACTIVE_CONFIG, PAGE_INTERACTIONS, FORM_INTERACTIONS } from './interactive-test-config.js';

/**
 * Interactive Button-Click Visual Regression Testing
 *
 * This script:
 * 1. Navigates to each page (vanilla and Angular)
 * 2. Finds and clicks all interactive elements (buttons, links, etc.)
 * 3. Takes screenshots before and after each interaction
 * 4. Compares vanilla vs Angular behavior visually
 */

async function setupOutputDir() {
  if (!fs.existsSync(INTERACTIVE_CONFIG.OUTPUT_DIR)) {
    fs.mkdirSync(INTERACTIVE_CONFIG.OUTPUT_DIR, { recursive: true });
  }
}

async function testButtonInteractions(browser, page, pageName, url, isAngular) {
  const prefix = isAngular ? 'angular' : 'vanilla';
  const interactions = PAGE_INTERACTIONS[pageName] || [];
  const formData = FORM_INTERACTIONS[pageName];

  const results = [];

  console.log(`  📍 Testing ${interactions.length} interactions on ${prefix}...`);

  // Navigate to page
  await page.goto(url, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(BASE_CONFIG.WAIT_TIME);

  // Take initial screenshot
  const initialScreenshot = path.join(
    INTERACTIVE_CONFIG.OUTPUT_DIR,
    `${pageName}-${prefix}-initial.png`
  );
  await page.screenshot({ path: initialScreenshot, fullPage: true });

  // Fill form fields if defined
  if (formData && formData.fields) {
    console.log(`  📝 Filling form with ${formData.fields.length} fields...`);
    for (const field of formData.fields) {
      try {
        if (field.action === 'check') {
          await page.check(field.selector);
        } else {
          await page.fill(field.selector, field.value);
        }
      } catch (error) {
        console.log(`    ⚠️ Could not fill field ${field.selector}: ${error.message}`);
      }
    }
    await page.waitForTimeout(500);
  }

  // Test each interaction
  for (let i = 0; i < interactions.length; i++) {
    const interaction = interactions[i];
    const interactionName = `${pageName}-${prefix}-${interaction.name}`;

    console.log(`    🖱️  [${i + 1}/${interactions.length}] ${interaction.description || interaction.name}`);

    try {
      // Wait for element to be visible
      await page.waitForSelector(interaction.selector, { timeout: 5000 });

      // Take screenshot before click
      const beforeScreenshot = path.join(
        INTERACTIVE_CONFIG.OUTPUT_DIR,
        `${interactionName}-before.png`
      );
      await page.screenshot({ path: beforeScreenshot, fullPage: true });

      // Perform the interaction (click)
      await page.click(interaction.selector);

      // Wait for any transitions/animations
      await page.waitForTimeout(INTERACTIVE_CONFIG.WAIT_AFTER_CLICK);

      // Wait for specific element if defined
      if (interaction.waitFor) {
        try {
          await page.waitForSelector(interaction.waitFor, { timeout: 5000 });
        } catch (e) {
          console.log(`    ⚠️ Element ${interaction.waitFor} not found`);
        }
      }

      await page.waitForTimeout(INTERACTIVE_CONFIG.WAIT_BEFORE_SCREENSHOT);

      // Take screenshot after click
      const afterScreenshot = path.join(
        INTERACTIVE_CONFIG.OUTPUT_DIR,
        `${interactionName}-after.png`
      );
      await page.screenshot({ path: afterScreenshot, fullPage: true });

      results.push({
        name: interaction.name,
        description: interaction.description,
        success: true,
        beforeScreenshot,
        afterScreenshot
      });

      // Close modal if specified
      if (interaction.closeModal) {
        try {
          await page.click(interaction.closeModal);
          await page.waitForTimeout(1000);
        } catch (e) {
          console.log(`    ⚠️ Could not close modal: ${e.message}`);
        }
      }

    } catch (error) {
      console.log(`    ❌ Failed: ${error.message}`);
      results.push({
        name: interaction.name,
        description: interaction.description,
        success: false,
        error: error.message
      });
    }
  }

  return results;
}

async function compareInteractionScreenshots(vanillaResults, angularResults, pageName) {
  const comparisons = [];

  for (let i = 0; i < vanillaResults.length; i++) {
    const vanillaResult = vanillaResults[i];
    const angularResult = angularResults[i];

    if (!vanillaResult.success || !angularResult.success) {
      comparisons.push({
        name: vanillaResult.name,
        status: 'error',
        message: 'Interaction failed on one or both platforms'
      });
      continue;
    }

    // Compare before screenshots
    const beforeComparison = await compareImages(
      vanillaResult.beforeScreenshot,
      angularResult.beforeScreenshot,
      path.join(INTERACTIVE_CONFIG.OUTPUT_DIR, `${pageName}-${vanillaResult.name}-before-diff.png`)
    );

    // Compare after screenshots
    const afterComparison = await compareImages(
      vanillaResult.afterScreenshot,
      angularResult.afterScreenshot,
      path.join(INTERACTIVE_CONFIG.OUTPUT_DIR, `${pageName}-${vanillaResult.name}-after-diff.png`)
    );

    comparisons.push({
      name: vanillaResult.name,
      description: vanillaResult.description,
      beforeSimilarity: beforeComparison.similarity,
      afterSimilarity: afterComparison.similarity,
      passed: parseFloat(beforeComparison.similarity) >= BASE_CONFIG.PASS_THRESHOLD &&
              parseFloat(afterComparison.similarity) >= BASE_CONFIG.PASS_THRESHOLD
    });
  }

  return comparisons;
}

function compareImages(img1Path, img2Path, diffPath) {
  try {
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
      return { success: false, error: 'Height mismatch', similarity: '0' };
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

function generateInteractiveReport(allResults) {
  let report = '# Interactive Button-Click Test Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += '## Summary\n\n';

  const totalTests = allResults.reduce((sum, page) => sum + page.comparisons.length, 0);
  const passedTests = allResults.reduce((sum, page) =>
    sum + page.comparisons.filter(c => c.passed).length, 0);

  report += `- **Total Interactions Tested**: ${totalTests}\n`;
  report += `- **Passed**: ${passedTests}\n`;
  report += `- **Failed**: ${totalTests - passedTests}\n`;
  report += `- **Pass Rate**: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;

  report += '---\n\n';

  // Detailed results per page
  for (const pageResult of allResults) {
    report += `## ${pageResult.page.toUpperCase()}\n\n`;
    report += `**Interactions Tested**: ${pageResult.comparisons.length}\n\n`;

    for (const comparison of pageResult.comparisons) {
      const status = comparison.passed ? '✅ PASS' : '⚠️ FAIL';
      report += `### ${status} - ${comparison.description || comparison.name}\n\n`;
      report += `- **Before Click Similarity**: ${comparison.beforeSimilarity}%\n`;
      report += `- **After Click Similarity**: ${comparison.afterSimilarity}%\n`;
      report += `- **Screenshots**:\n`;
      report += `  - Before: \`${pageResult.page}-${comparison.name}-before-diff.png\`\n`;
      report += `  - After: \`${pageResult.page}-${comparison.name}-after-diff.png\`\n\n`;
    }

    report += '---\n\n';
  }

  fs.writeFileSync(
    path.join(INTERACTIVE_CONFIG.OUTPUT_DIR, 'interactive-report.md'),
    report
  );
}

async function main() {
  console.log('🚀 Starting Interactive Button-Click Testing...\n');

  setupOutputDir();

  const browser = await chromium.launch({ headless: true });
  const allResults = [];

  // Get pages to test (only implemented ones for now)
  const pagesToTest = PAGES.filter(p => p.status === 'implemented');

  for (const pageConfig of pagesToTest) {
    console.log(`\n📄 Testing ${pageConfig.name}...`);

    const vanillaUrl = `${BASE_CONFIG.VANILLA_URL}${pageConfig.vanillaPath}`;
    const angularUrl = `${BASE_CONFIG.ANGULAR_URL}${pageConfig.angularPath}`;

    // Test vanilla
    const vanillaContext = await browser.newContext({
      ignoreHTTPSErrors: BASE_CONFIG.IGNORE_HTTPS_ERRORS
    });
    const vanillaPage = await vanillaContext.newPage();
    await vanillaPage.setViewportSize(BASE_CONFIG.VIEWPORT);

    const vanillaResults = await testButtonInteractions(
      browser,
      vanillaPage,
      pageConfig.name,
      vanillaUrl,
      false
    );

    await vanillaContext.close();

    // Test Angular
    const angularContext = await browser.newContext({
      ignoreHTTPSErrors: BASE_CONFIG.IGNORE_HTTPS_ERRORS
    });
    const angularPage = await angularContext.newPage();
    await angularPage.setViewportSize(BASE_CONFIG.VIEWPORT);

    const angularResults = await testButtonInteractions(
      browser,
      angularPage,
      pageConfig.name,
      angularUrl,
      true
    );

    await angularContext.close();

    // Compare results
    console.log(`  🔍 Comparing ${vanillaResults.length} interactions...`);
    const comparisons = await compareInteractionScreenshots(
      vanillaResults,
      angularResults,
      pageConfig.name
    );

    allResults.push({
      page: pageConfig.name,
      comparisons
    });

    const passed = comparisons.filter(c => c.passed).length;
    console.log(`  ✅ ${passed}/${comparisons.length} interactions passed`);
  }

  await browser.close();

  // Generate report
  console.log('\n📝 Generating interactive test report...');
  generateInteractiveReport(allResults);

  console.log(`\n✨ Interactive testing complete!`);
  console.log(`📊 Report: ${INTERACTIVE_CONFIG.OUTPUT_DIR}/interactive-report.md\n`);

  // Exit with error if any tests failed
  const totalPassed = allResults.reduce((sum, p) =>
    sum + p.comparisons.filter(c => c.passed).length, 0);
  const totalTests = allResults.reduce((sum, p) => sum + p.comparisons.length, 0);

  process.exit(totalPassed === totalTests ? 0 : 1);
}

main().catch(error => {
  console.error('❌ Error:', error);
  process.exit(1);
});
