import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

/**
 * Comprehensive Visual Regression Test Suite
 *
 * Tests all implemented pages with different states, routes, and interactions
 */

const CONFIG = {
  VANILLA_URL: 'https://localhost',
  ANGULAR_URL: 'http://localhost:4200',
  OUTPUT_DIR: './visual-regression-results/comprehensive',
  VIEWPORT: { width: 1920, height: 1080 },
  WAIT_TIME: 5000,
  DIFF_THRESHOLD: 0.1,
  PASS_THRESHOLD: 95,
  IGNORE_HTTPS_ERRORS: true
};

// Comprehensive test scenarios covering all pages and states
const TEST_SCENARIOS = [
  // Dashboard Tests
  {
    category: 'Dashboard',
    name: 'dashboard-main',
    vanillaPath: '/pages/dashboard.html',
    angularPath: '/dashboard',
    description: 'Main dashboard with all statistics and charts',
    waitFor: '.card'
  },

  // Mailbox Tests - Different States
  {
    category: 'Mailbox',
    name: 'mailbox-all-emails',
    vanillaPath: '/pages/mailbox.html',
    angularPath: '/mailbox',
    description: 'Mailbox showing all emails',
    waitFor: '.email-card'
  },
  {
    category: 'Mailbox',
    name: 'mailbox-processed',
    vanillaPath: '/pages/mailbox.html?filter=processed',
    angularPath: '/mailbox?filter=processed',
    description: 'Mailbox filtered to processed emails',
    waitFor: '.email-card'
  },
  {
    category: 'Mailbox',
    name: 'mailbox-unprocessed',
    vanillaPath: '/pages/mailbox.html?filter=unprocessed',
    angularPath: '/mailbox?filter=unprocessed',
    description: 'Mailbox filtered to unprocessed emails',
    waitFor: '.email-card'
  },

  // Daily Inbox Digest
  {
    category: 'Daily Inbox Digest',
    name: 'daily-inbox-digest',
    vanillaPath: '/pages/daily-inbox-digest.html',
    angularPath: '/daily-inbox-digest',
    description: 'Daily email digest summary',
    waitFor: '.digest-container'
  },

  // Virtual Teams - All Variations
  {
    category: 'Virtual Teams',
    name: 'agentic-teams-fraud',
    vanillaPath: '/pages/agentic-teams.html?team=fraud',
    angularPath: '/agentic-teams?team=fraud',
    description: 'Fraud Investigation Unit team view',
    waitFor: '.team-presentation-panel, .email-queue'
  },
  {
    category: 'Virtual Teams',
    name: 'agentic-teams-compliance',
    vanillaPath: '/pages/agentic-teams.html?team=compliance',
    angularPath: '/agentic-teams?team=compliance',
    description: 'Compliance & Regulatory Affairs team view',
    waitFor: '.team-presentation-panel, .email-queue'
  },
  {
    category: 'Virtual Teams',
    name: 'agentic-teams-investments',
    vanillaPath: '/pages/agentic-teams.html?team=investments',
    angularPath: '/agentic-teams?team=investments',
    description: 'Investment Research Team view',
    waitFor: '.team-presentation-panel, .email-queue'
  },
  {
    category: 'Virtual Teams',
    name: 'agentic-teams-all',
    vanillaPath: '/pages/agentic-teams.html?team=all',
    angularPath: '/agentic-teams?team=all',
    description: 'All teams overview',
    waitFor: '.email-queue'
  },
  {
    category: 'Virtual Teams',
    name: 'agentic-teams-default',
    vanillaPath: '/pages/agentic-teams.html',
    angularPath: '/agentic-teams',
    description: 'Virtual teams landing (no team selected)',
    waitFor: '.email-queue'
  }
];

// Elements to inspect across all pages
const COMMON_ELEMENTS = [
  { name: 'Sidebar', selector: '#sidenav-main' },
  { name: 'Navbar', selector: '.navbar-main' },
  { name: 'Main Content', selector: 'main.main-content' },
  { name: 'Footer', selector: 'footer' }
];

const CATEGORY_ELEMENTS = {
  Dashboard: [
    ...COMMON_ELEMENTS,
    { name: 'Stats Card 1', selector: '.row .col-xl-3:nth-child(1) .card' },
    { name: 'Stats Card 2', selector: '.row .col-xl-3:nth-child(2) .card' },
    { name: 'Stats Card 3', selector: '.row .col-xl-3:nth-child(3) .card' },
    { name: 'Stats Card 4', selector: '.row .col-xl-3:nth-child(4) .card' },
    { name: 'Chart Container', selector: 'canvas' }
  ],
  Mailbox: [
    ...COMMON_ELEMENTS,
    { name: 'Email Queue', selector: '.email-queue' },
    { name: 'First Email Card', selector: '.email-card:first-child' },
    { name: 'Filter Buttons', selector: '.btn-group' },
    { name: 'Email List Container', selector: '#email-list-container' }
  ],
  'Daily Inbox Digest': [
    ...COMMON_ELEMENTS,
    { name: 'Digest Container', selector: '.digest-container' },
    { name: 'Summary Section', selector: '.summary-section' },
    { name: 'Email Categories', selector: '.category-section' }
  ],
  'Virtual Teams': [
    ...COMMON_ELEMENTS,
    { name: 'Email Queue Panel', selector: '.email-queue' },
    { name: 'Discussion Panel', selector: '.discussion-panel' },
    { name: 'Team Presentation Panel', selector: '.team-presentation-panel' },
    { name: 'Direct Interaction Panel', selector: '.direct-interaction-panel' },
    { name: 'Empty State', selector: '.empty-state' },
    { name: 'Chat Container', selector: '#chat-container' }
  ]
};

async function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.OUTPUT_DIR)) {
    fs.mkdirSync(CONFIG.OUTPUT_DIR, { recursive: true });
  }
}

async function captureScreenshot(browser, url, name, waitForSelector) {
  try {
    const context = await browser.newContext({
      ignoreHTTPSErrors: CONFIG.IGNORE_HTTPS_ERRORS
    });
    const page = await context.newPage();
    await page.setViewportSize(CONFIG.VIEWPORT);

    console.log(`    - Navigating to: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Wait for specific element if specified
    if (waitForSelector) {
      try {
        await page.waitForSelector(waitForSelector.split(',')[0].trim(), { timeout: 10000 });
      } catch (e) {
        console.log(`    ⚠️ Selector "${waitForSelector}" not found, continuing...`);
      }
    }

    // Additional wait for content to render
    await page.waitForTimeout(CONFIG.WAIT_TIME);

    const screenshotPath = path.join(CONFIG.OUTPUT_DIR, `${name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    await context.close();

    return { success: true, path: screenshotPath };
  } catch (error) {
    console.error(`    ❌ Screenshot failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function extractDOMStructure(browser, url, selectors, waitForSelector) {
  const context = await browser.newContext({ ignoreHTTPSErrors: CONFIG.IGNORE_HTTPS_ERRORS });
  const page = await context.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

  if (waitForSelector) {
    try {
      await page.waitForSelector(waitForSelector.split(',')[0].trim(), { timeout: 10000 });
    } catch (e) {
      // Continue even if selector not found
    }
  }

  await page.waitForTimeout(CONFIG.WAIT_TIME);

  const structure = {};

  for (const { name, selector } of selectors) {
    try {
      const element = await page.$(selector);
      if (element) {
        const isVisible = await element.isVisible();
        const boundingBox = await element.boundingBox();

        structure[name] = {
          exists: true,
          visible: isVisible,
          boundingBox: boundingBox,
          textContent: (await element.textContent()).substring(0, 200)
        };
      } else {
        structure[name] = { exists: false, visible: false };
      }
    } catch (error) {
      structure[name] = { error: error.message };
    }
  }

  await context.close();
  return structure;
}

function compareImages(img1Path, img2Path, diffPath) {
  const img1 = PNG.sync.read(fs.readFileSync(img1Path));
  const img2 = PNG.sync.read(fs.readFileSync(img2Path));

  // Handle different image sizes by using the larger dimensions
  const width = Math.max(img1.width, img2.width);
  const height = Math.max(img1.height, img2.height);

  // Create new images with matching dimensions if needed
  let img1Data = img1.data;
  let img2Data = img2.data;

  if (img1.width !== width || img1.height !== height || img2.width !== width || img2.height !== height) {
    // Create padded versions
    const paddedImg1 = new PNG({ width, height });
    const paddedImg2 = new PNG({ width, height });

    // Fill with white background
    paddedImg1.data.fill(255);
    paddedImg2.data.fill(255);

    // Copy original image data
    PNG.bitblt(img1, paddedImg1, 0, 0, img1.width, img1.height, 0, 0);
    PNG.bitblt(img2, paddedImg2, 0, 0, img2.width, img2.height, 0, 0);

    img1Data = paddedImg1.data;
    img2Data = paddedImg2.data;
  }

  const diff = new PNG({ width, height });

  const numDiffPixels = pixelmatch(
    img1Data,
    img2Data,
    diff.data,
    width,
    height,
    { threshold: CONFIG.DIFF_THRESHOLD }
  );

  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const totalPixels = width * height;
  const percentageDiff = (numDiffPixels / totalPixels) * 100;

  return {
    diffPixels: numDiffPixels,
    totalPixels,
    percentageDiff: percentageDiff.toFixed(4),
    similarity: (100 - percentageDiff).toFixed(4),
    dimensionsMismatch: img1.width !== img2.width || img1.height !== img2.height
  };
}

function compareStructures(vanilla, angular) {
  const differences = [];
  const allKeys = new Set([...Object.keys(vanilla), ...Object.keys(angular)]);

  for (const key of allKeys) {
    const v = vanilla[key];
    const a = angular[key];

    if (!v) {
      differences.push({ element: key, issue: 'Missing in vanilla', angular: a });
    } else if (!a) {
      differences.push({ element: key, issue: 'Missing in Angular', vanilla: v });
    } else if (v.exists && a.exists) {
      if (v.visible !== a.visible) {
        differences.push({
          element: key,
          issue: 'Visibility mismatch',
          vanilla: v.visible ? 'visible' : 'hidden',
          angular: a.visible ? 'visible' : 'hidden'
        });
      }
    }
  }

  return differences;
}

function generateReport(results) {
  let report = '# Comprehensive Visual Regression Test Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += `Vanilla URL: ${CONFIG.VANILLA_URL}\n`;
  report += `Angular URL: ${CONFIG.ANGULAR_URL}\n\n`;
  report += '---\n\n';

  // Overall summary
  const totalTests = results.length;
  const passedTests = results.filter(r => parseFloat(r.visual.similarity) >= CONFIG.PASS_THRESHOLD).length;
  const failedTests = totalTests - passedTests;

  report += `## Overall Summary\n\n`;
  report += `- **Total Tests**: ${totalTests}\n`;
  report += `- **Passed**: ${passedTests} ✅ (${CONFIG.PASS_THRESHOLD}% threshold)\n`;
  report += `- **Failed**: ${failedTests} ⚠️\n`;
  report += `- **Pass Rate**: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
  report += '---\n\n';

  // Group by category
  const categories = [...new Set(results.map(r => r.category))];

  for (const category of categories) {
    const categoryResults = results.filter(r => r.category === category);
    const categoryPassed = categoryResults.filter(r => parseFloat(r.visual.similarity) >= CONFIG.PASS_THRESHOLD).length;

    report += `## ${category}\n\n`;
    report += `**Results**: ${categoryPassed}/${categoryResults.length} passed\n\n`;

    for (const result of categoryResults) {
      const status = parseFloat(result.visual.similarity) >= CONFIG.PASS_THRESHOLD ? '✅' : '⚠️';
      report += `### ${status} ${result.name}\n\n`;
      report += `- **Description**: ${result.description}\n`;
      report += `- **Similarity**: ${result.visual.similarity}%\n`;
      report += `- **Different Pixels**: ${result.visual.diffPixels} / ${result.visual.totalPixels}\n`;
      report += `- **Structural Differences**: ${result.structure.differences.length}\n`;
      report += `- **Vanilla**: ${result.screenshots.vanilla}\n`;
      report += `- **Angular**: ${result.screenshots.angular}\n`;
      report += `- **Diff**: ${result.visual.diffPath}\n\n`;

      if (result.structure.differences.length > 0 && result.structure.differences.length <= 10) {
        report += '**Key Differences:**\n';
        for (const diff of result.structure.differences.slice(0, 5)) {
          report += `- ${diff.element}: ${diff.issue}\n`;
        }
        report += '\n';
      }
    }

    report += '---\n\n';
  }

  return report;
}

async function runComprehensiveTests() {
  console.log('🚀 Starting Comprehensive Visual Regression Tests...\n');
  console.log(`📊 Testing ${TEST_SCENARIOS.length} scenarios across all pages\n`);

  await ensureOutputDir();

  const browser = await chromium.launch({ headless: true });
  const results = [];

  try {
    for (const scenario of TEST_SCENARIOS) {
      console.log(`\n📸 Testing: ${scenario.category} - ${scenario.name}`);
      console.log(`   ${scenario.description}`);

      const vanillaUrl = `${CONFIG.VANILLA_URL}${scenario.vanillaPath}`;
      const angularUrl = `${CONFIG.ANGULAR_URL}${scenario.angularPath}`;

      // Capture screenshots
      console.log('  - Capturing vanilla screenshot...');
      const vanillaScreenshot = await captureScreenshot(
        browser,
        vanillaUrl,
        `${scenario.name}-vanilla`,
        scenario.waitFor
      );

      if (!vanillaScreenshot.success) {
        console.log(`  ❌ Skipping ${scenario.name} - vanilla screenshot failed`);
        continue;
      }

      console.log('  - Capturing Angular screenshot...');
      const angularScreenshot = await captureScreenshot(
        browser,
        angularUrl,
        `${scenario.name}-angular`,
        scenario.waitFor
      );

      if (!angularScreenshot.success) {
        console.log(`  ❌ Skipping ${scenario.name} - Angular screenshot failed`);
        continue;
      }

      // Compare screenshots
      console.log('  - Comparing screenshots...');
      const diffPath = path.join(CONFIG.OUTPUT_DIR, `${scenario.name}-diff.png`);
      const visualComparison = compareImages(
        vanillaScreenshot.path,
        angularScreenshot.path,
        diffPath
      );
      visualComparison.diffPath = diffPath;

      // Extract DOM structures
      console.log('  - Extracting DOM structures...');
      const elements = CATEGORY_ELEMENTS[scenario.category] || COMMON_ELEMENTS;
      const vanillaStructure = await extractDOMStructure(browser, vanillaUrl, elements, scenario.waitFor);
      const angularStructure = await extractDOMStructure(browser, angularUrl, elements, scenario.waitFor);

      // Compare structures
      console.log('  - Comparing structures...');
      const structuralDifferences = compareStructures(vanillaStructure, angularStructure);

      results.push({
        category: scenario.category,
        name: scenario.name,
        description: scenario.description,
        visual: visualComparison,
        screenshots: {
          vanilla: vanillaScreenshot.path,
          angular: angularScreenshot.path
        },
        structure: {
          vanilla: vanillaStructure,
          angular: angularStructure,
          differences: structuralDifferences
        }
      });

      const status = parseFloat(visualComparison.similarity) >= CONFIG.PASS_THRESHOLD ? '✅' : '⚠️';
      console.log(`  ${status} ${scenario.name} - Similarity: ${visualComparison.similarity}% (${structuralDifferences.length} structural diffs)`);
    }

    // Generate report
    console.log('\n📝 Generating comprehensive report...');
    const report = generateReport(results);
    const reportPath = path.join(CONFIG.OUTPUT_DIR, 'comprehensive-report.md');
    fs.writeFileSync(reportPath, report);

    // Save detailed JSON
    const jsonPath = path.join(CONFIG.OUTPUT_DIR, 'comprehensive-results.json');
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));

    console.log('\n✨ Comprehensive tests complete!');
    console.log(`📊 Report: ${reportPath}`);
    console.log(`📄 Detailed results: ${jsonPath}`);
    console.log(`📁 Screenshots: ${CONFIG.OUTPUT_DIR}/\n`);

    // Print summary
    const totalTests = results.length;
    const passedTests = results.filter(r => parseFloat(r.visual.similarity) >= CONFIG.PASS_THRESHOLD).length;

    console.log('📋 Summary:');
    console.log(`  Total: ${totalTests} | Passed: ${passedTests} ✅ | Failed: ${totalTests - passedTests} ⚠️`);
    console.log(`  Pass Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n`);

    // Category breakdown
    const categories = [...new Set(results.map(r => r.category))];
    for (const category of categories) {
      const categoryResults = results.filter(r => r.category === category);
      const categoryPassed = categoryResults.filter(r => parseFloat(r.visual.similarity) >= CONFIG.PASS_THRESHOLD).length;
      console.log(`  ${category}: ${categoryPassed}/${categoryResults.length} passed`);
    }
    console.log('');

  } finally {
    await browser.close();
  }
}

runComprehensiveTests().catch(console.error);
