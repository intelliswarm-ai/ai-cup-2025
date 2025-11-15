import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

// Configuration
const VANILLA_URL = 'https://localhost';
const ANGULAR_URL = 'http://localhost:4200';
const OUTPUT_DIR = './visual-regression-results/virtual-teams';

// Virtual Teams pages to test
const VIRTUAL_TEAMS_PAGES = [
  { name: 'fraud', vanillaPath: '/pages/agentic-teams.html?team=fraud', angularPath: '/agentic-teams?team=fraud' },
  { name: 'compliance', vanillaPath: '/pages/agentic-teams.html?team=compliance', angularPath: '/agentic-teams?team=compliance' },
  { name: 'investments', vanillaPath: '/pages/agentic-teams.html?team=investments', angularPath: '/agentic-teams?team=investments' },
  { name: 'all-teams', vanillaPath: '/pages/agentic-teams.html?team=all', angularPath: '/agentic-teams?team=all' }
];

// Comprehensive element inspection for virtual teams
const VIRTUAL_TEAMS_ELEMENTS = [
  // Layout structure
  { name: 'Sidebar', selector: '#sidenav-main' },
  { name: 'Navbar', selector: '.navbar-main' },
  { name: 'Dashboard Grid', selector: '.dashboard-grid' },

  // Email Queue Panel
  { name: 'Email Queue Panel', selector: '.email-queue' },
  { name: 'Email Queue Header', selector: '.email-queue-header' },
  { name: 'Queue Count', selector: '#queue-count' },
  { name: 'First Email Card', selector: '.email-card:first-child' },
  { name: 'Email Subject', selector: '.email-subject:first-of-type' },
  { name: 'Email Status Indicator', selector: '.email-status-indicator:first-of-type' },
  { name: 'Team Badge', selector: '.team-badge:first-of-type' },

  // Discussion Panel
  { name: 'Discussion Panel', selector: '.discussion-panel' },
  { name: 'Discussion Header', selector: '.discussion-header' },
  { name: 'Discussion Title', selector: '#discussion-team' },
  { name: 'Discussion Subtitle', selector: '#discussion-subject' },
  { name: 'Progress Bar', selector: '.progress-bar' },

  // Direct Interaction (visible for specific teams, not 'all')
  { name: 'Direct Interaction Panel', selector: '.direct-interaction-panel' },
  { name: 'Interaction Header', selector: '.interaction-header h3' },
  { name: 'Direct Query Input', selector: '#direct-query-input' },
  { name: 'Query Hint', selector: '.form-text.text-muted' },
  { name: 'Submit Button', selector: '.interaction-actions .btn-primary' },

  // Team Presentation (visible for specific teams, not 'all')
  { name: 'Team Presentation Panel', selector: '.team-presentation-panel' },
  { name: 'Presentation Header', selector: '.presentation-header h3' },
  { name: 'Team Members Grid', selector: '.presentation-members-grid' },
  { name: 'First Member Card', selector: '.member-card:first-child' },
  { name: 'Member Header', selector: '.member-header:first-of-type' },
  { name: 'Member Icon', selector: '.member-icon:first-of-type' },
  { name: 'Member Name', selector: '.member-name:first-of-type' },
  { name: 'Member Type', selector: '.member-type:first-of-type' },
  { name: 'Member Details', selector: '.member-details:first-of-type' },
  { name: 'Member Section', selector: '.member-section:first-of-type' },

  // Empty State (visible for 'all' teams or no emails)
  { name: 'Empty State', selector: '.empty-state' }
];

async function ensureOutputDir() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
}

async function captureScreenshot(browser, url, name) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });
  await page.setViewportSize({ width: 1920, height: 1080 });

  console.log(`    - Navigating to: ${url}`);
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Wait for content to load and render (longer wait to ensure all images/styles load)
  await page.waitForTimeout(5000);

  const screenshotPath = path.join(OUTPUT_DIR, `${name}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await page.close();

  return screenshotPath;
}

async function extractDOMStructure(browser, url, selectors) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);

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
          textContent: (await element.textContent()).substring(0, 200),
          classes: await element.evaluate(el => el.className),
          styles: await element.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
              // Colors
              backgroundColor: computed.backgroundColor,
              color: computed.color,
              borderColor: computed.borderColor,
              // Typography
              fontSize: computed.fontSize,
              fontWeight: computed.fontWeight,
              fontFamily: computed.fontFamily,
              lineHeight: computed.lineHeight,
              textAlign: computed.textAlign,
              // Spacing
              padding: computed.padding,
              margin: computed.margin,
              gap: computed.gap,
              // Borders & Shadows
              border: computed.border,
              borderRadius: computed.borderRadius,
              boxShadow: computed.boxShadow,
              // Layout
              display: computed.display,
              position: computed.position,
              flexDirection: computed.flexDirection,
              alignItems: computed.alignItems,
              justifyContent: computed.justifyContent,
              gridTemplateColumns: computed.gridTemplateColumns,
              // Dimensions
              width: computed.width,
              height: computed.height,
              // Effects
              opacity: computed.opacity,
              transform: computed.transform
            };
          })
        };
      } else {
        structure[name] = { exists: false, visible: false };
      }
    } catch (error) {
      structure[name] = { error: error.message };
    }
  }

  await page.close();
  return structure;
}

function compareImages(img1Path, img2Path, diffPath) {
  const img1 = PNG.sync.read(fs.readFileSync(img1Path));
  const img2 = PNG.sync.read(fs.readFileSync(img2Path));

  const { width, height } = img1;
  const diff = new PNG({ width, height });

  const numDiffPixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );

  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const totalPixels = width * height;
  const percentageDiff = (numDiffPixels / totalPixels) * 100;

  return {
    diffPixels: numDiffPixels,
    totalPixels,
    percentageDiff: percentageDiff.toFixed(4),
    similarity: (100 - percentageDiff).toFixed(4)
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
      // Check visibility
      if (v.visible !== a.visible) {
        differences.push({
          element: key,
          issue: 'Visibility mismatch',
          vanilla: v.visible ? 'visible' : 'hidden',
          angular: a.visible ? 'visible' : 'hidden'
        });
      }

      // Compare styles
      const styleDiffs = [];
      if (v.styles && a.styles) {
        for (const [prop, value] of Object.entries(v.styles)) {
          if (a.styles[prop] !== value) {
            styleDiffs.push({
              property: prop,
              vanilla: value,
              angular: a.styles[prop]
            });
          }
        }
      }

      if (styleDiffs.length > 0) {
        differences.push({
          element: key,
          issue: 'Style differences',
          styleDiffs
        });
      }

      // Compare text content
      if (v.textContent && a.textContent && v.textContent !== a.textContent) {
        differences.push({
          element: key,
          issue: 'Text content mismatch',
          vanilla: v.textContent,
          angular: a.textContent
        });
      }
    }
  }

  return differences;
}

function generateReport(results) {
  let report = '# Virtual Teams Visual Regression Test Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += `Vanilla URL: ${VANILLA_URL}\n`;
  report += `Angular URL: ${ANGULAR_URL}\n\n`;
  report += '---\n\n';

  // Overall summary
  const totalTests = results.length;
  const passedTests = results.filter(r => parseFloat(r.visual.similarity) >= 99).length;
  const failedTests = totalTests - passedTests;

  report += `## Overall Summary\n\n`;
  report += `- **Total Tests**: ${totalTests}\n`;
  report += `- **Passed**: ${passedTests} ✅\n`;
  report += `- **Failed**: ${failedTests} ⚠️\n`;
  report += `- **Pass Rate**: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
  report += '---\n\n';

  for (const result of results) {
    report += `## ${result.team.toUpperCase()} TEAM\n\n`;

    // Visual comparison
    report += '### Visual Comparison\n\n';
    report += `- **Similarity**: ${result.visual.similarity}%\n`;
    report += `- **Different Pixels**: ${result.visual.diffPixels} / ${result.visual.totalPixels}\n`;
    report += `- **Vanilla Screenshot**: ${result.screenshots.vanilla}\n`;
    report += `- **Angular Screenshot**: ${result.screenshots.angular}\n`;
    report += `- **Diff Image**: ${result.visual.diffPath}\n\n`;

    if (parseFloat(result.visual.similarity) < 99) {
      report += '⚠️ **Visual differences detected!**\n\n';
    } else {
      report += '✅ **Visual parity achieved!**\n\n';
    }

    // Structural comparison
    report += '### Structural Comparison\n\n';
    if (result.structure.differences.length === 0) {
      report += '✅ **No structural differences found!**\n\n';
    } else {
      report += `⚠️ **Found ${result.structure.differences.length} structural differences:**\n\n`;

      for (const diff of result.structure.differences) {
        report += `#### ${diff.element}\n\n`;
        report += `- **Issue**: ${diff.issue}\n`;

        if (diff.styleDiffs) {
          report += '- **Style Differences**:\n';
          for (const styleDiff of diff.styleDiffs.slice(0, 5)) { // Limit to first 5
            report += `  - \`${styleDiff.property}\`:\n`;
            report += `    - Vanilla: \`${styleDiff.vanilla}\`\n`;
            report += `    - Angular: \`${styleDiff.angular}\`\n`;
          }
          if (diff.styleDiffs.length > 5) {
            report += `  - ... and ${diff.styleDiffs.length - 5} more style differences\n`;
          }
        }

        if (diff.vanilla && diff.angular && typeof diff.vanilla === 'string') {
          report += `  - Vanilla: \`${diff.vanilla}\`\n`;
          report += `  - Angular: \`${diff.angular}\`\n`;
        }

        report += '\n';
      }
    }

    report += '---\n\n';
  }

  return report;
}

async function runVirtualTeamsTests() {
  console.log('🚀 Starting Virtual Teams Visual Regression Tests...\n');

  await ensureOutputDir();

  const browser = await chromium.launch({ headless: true });
  const results = [];

  try {
    for (const page of VIRTUAL_TEAMS_PAGES) {
      console.log(`📸 Testing ${page.name.toUpperCase()} team...`);

      // Capture screenshots
      const vanillaUrl = `${VANILLA_URL}${page.vanillaPath}`;
      const angularUrl = `${ANGULAR_URL}${page.angularPath}`;

      console.log(`  - Capturing vanilla screenshot...`);
      const vanillaScreenshot = await captureScreenshot(
        browser,
        vanillaUrl,
        `${page.name}-vanilla`
      );

      console.log(`  - Capturing Angular screenshot...`);
      const angularScreenshot = await captureScreenshot(
        browser,
        angularUrl,
        `${page.name}-angular`
      );

      // Compare screenshots
      console.log('  - Comparing screenshots...');
      const diffPath = path.join(OUTPUT_DIR, `${page.name}-diff.png`);
      const visualComparison = compareImages(
        vanillaScreenshot,
        angularScreenshot,
        diffPath
      );
      visualComparison.diffPath = diffPath;

      // Extract DOM structures
      console.log('  - Extracting DOM structures...');
      const vanillaStructure = await extractDOMStructure(browser, vanillaUrl, VIRTUAL_TEAMS_ELEMENTS);
      const angularStructure = await extractDOMStructure(browser, angularUrl, VIRTUAL_TEAMS_ELEMENTS);

      // Compare structures
      console.log('  - Comparing structures...');
      const structuralDifferences = compareStructures(vanillaStructure, angularStructure);

      results.push({
        team: page.name,
        visual: visualComparison,
        screenshots: {
          vanilla: vanillaScreenshot,
          angular: angularScreenshot
        },
        structure: {
          vanilla: vanillaStructure,
          angular: angularStructure,
          differences: structuralDifferences
        }
      });

      const status = parseFloat(visualComparison.similarity) >= 99 ? '✅' : '⚠️';
      console.log(`  ${status} ${page.name} - Similarity: ${visualComparison.similarity}% (${structuralDifferences.length} structural diffs)\n`);
    }

    // Generate report
    console.log('📝 Generating report...');
    const report = generateReport(results);
    const reportPath = path.join(OUTPUT_DIR, 'virtual-teams-report.md');
    fs.writeFileSync(reportPath, report);

    // Save detailed JSON
    const jsonPath = path.join(OUTPUT_DIR, 'virtual-teams-results.json');
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));

    console.log('\n✨ Virtual Teams tests complete!');
    console.log(`📊 Report: ${reportPath}`);
    console.log(`📄 Detailed results: ${jsonPath}`);
    console.log(`📁 Screenshots: ${OUTPUT_DIR}/\n`);

    // Print summary
    console.log('📋 Summary:');
    const totalTests = results.length;
    const passedTests = results.filter(r => parseFloat(r.visual.similarity) >= 99).length;
    console.log(`  Total: ${totalTests} | Passed: ${passedTests} ✅ | Failed: ${totalTests - passedTests} ⚠️`);
    console.log('');
    for (const result of results) {
      const status = parseFloat(result.visual.similarity) >= 99 ? '✅' : '⚠️';
      console.log(`  ${status} ${result.team.toUpperCase()}: ${result.visual.similarity}% similar, ${result.structure.differences.length} structural diffs`);
    }

  } finally {
    await browser.close();
  }
}

runVirtualTeamsTests().catch(console.error);
