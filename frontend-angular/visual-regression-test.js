import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

// Configuration
const VANILLA_URL = 'http://localhost';
const ANGULAR_URL = 'http://localhost:4200';
const OUTPUT_DIR = './visual-regression-results';

// Pages to test
const PAGES = [
  { name: 'dashboard', vanillaPath: '/pages/dashboard.html', angularPath: '/dashboard' },
  { name: 'mailbox', vanillaPath: '/pages/mailbox.html', angularPath: '/mailbox' },
  // Virtual Teams
  { name: 'virtual-teams-fraud', vanillaPath: '/pages/agentic-teams.html?team=fraud', angularPath: '/agentic-teams?team=fraud' },
  { name: 'virtual-teams-compliance', vanillaPath: '/pages/agentic-teams.html?team=compliance', angularPath: '/agentic-teams?team=compliance' },
  { name: 'virtual-teams-investments', vanillaPath: '/pages/agentic-teams.html?team=investments', angularPath: '/agentic-teams?team=investments' },
  { name: 'virtual-teams-all', vanillaPath: '/pages/agentic-teams.html?team=all', angularPath: '/agentic-teams?team=all' }
];

// Key elements to inspect for each page
const ELEMENTS_TO_INSPECT = {
  dashboard: [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Total Emails Card', selector: '.col-xl-3:nth-child(1) .card' },
    { name: 'Processed Card', selector: '.col-xl-3:nth-child(2) .card' },
    { name: 'Legitimate Card', selector: '.col-xl-3:nth-child(3) .card' },
    { name: 'Phishing Card', selector: '.col-xl-3:nth-child(4) .card' },
    { name: 'Distribution Chart', selector: 'canvas:first-of-type' },
    { name: 'Workflow Chart', selector: 'canvas:nth-of-type(2)' },
    { name: 'Virtual Teams Header', selector: '.nav-item.mt-3 h6' }
  ],
  mailbox: [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Statistics Cards', selector: '.row:first-child' },
    { name: 'Quick Actions', selector: '.card-header:has-text("Quick Actions")' },
    { name: 'Email List', selector: '.email-card:first-child' }
  ],
  'virtual-teams-fraud': [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Email Queue Panel', selector: '.email-queue' },
    { name: 'Email Queue Header', selector: '.email-queue-header' },
    { name: 'First Email Card', selector: '.email-card:first-child' },
    { name: 'Discussion Panel', selector: '.discussion-panel' },
    { name: 'Discussion Header', selector: '.discussion-header' },
    { name: 'Direct Interaction Panel', selector: '.direct-interaction-panel' },
    { name: 'Direct Query Input', selector: '#direct-query-input' },
    { name: 'Query Hint', selector: '.form-text.text-muted' },
    { name: 'Team Presentation Panel', selector: '.team-presentation-panel' },
    { name: 'Team Members Grid', selector: '.presentation-members-grid' },
    { name: 'First Member Card', selector: '.member-card:first-child' },
    { name: 'Member Icon', selector: '.member-icon:first-of-type' },
    { name: 'Member Name', selector: '.member-name:first-of-type' },
    { name: 'Member Type', selector: '.member-type:first-of-type' },
    { name: 'Member Details', selector: '.member-details:first-of-type' }
  ],
  'virtual-teams-compliance': [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Email Queue Panel', selector: '.email-queue' },
    { name: 'Email Queue Header', selector: '.email-queue-header' },
    { name: 'First Email Card', selector: '.email-card:first-child' },
    { name: 'Discussion Panel', selector: '.discussion-panel' },
    { name: 'Discussion Header', selector: '.discussion-header' },
    { name: 'Direct Interaction Panel', selector: '.direct-interaction-panel' },
    { name: 'Direct Query Input', selector: '#direct-query-input' },
    { name: 'Query Hint', selector: '.form-text.text-muted' },
    { name: 'Team Presentation Panel', selector: '.team-presentation-panel' },
    { name: 'Team Members Grid', selector: '.presentation-members-grid' },
    { name: 'First Member Card', selector: '.member-card:first-child' },
    { name: 'Member Icon', selector: '.member-icon:first-of-type' },
    { name: 'Member Name', selector: '.member-name:first-of-type' },
    { name: 'Member Type', selector: '.member-type:first-of-type' },
    { name: 'Member Details', selector: '.member-details:first-of-type' }
  ],
  'virtual-teams-investments': [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Email Queue Panel', selector: '.email-queue' },
    { name: 'Email Queue Header', selector: '.email-queue-header' },
    { name: 'First Email Card', selector: '.email-card:first-child' },
    { name: 'Discussion Panel', selector: '.discussion-panel' },
    { name: 'Discussion Header', selector: '.discussion-header' },
    { name: 'Direct Interaction Panel', selector: '.direct-interaction-panel' },
    { name: 'Direct Query Input', selector: '#direct-query-input' },
    { name: 'Query Hint', selector: '.form-text.text-muted' },
    { name: 'Team Presentation Panel', selector: '.team-presentation-panel' },
    { name: 'Team Members Grid', selector: '.presentation-members-grid' },
    { name: 'First Member Card', selector: '.member-card:first-child' },
    { name: 'Member Icon', selector: '.member-icon:first-of-type' },
    { name: 'Member Name', selector: '.member-name:first-of-type' },
    { name: 'Member Type', selector: '.member-type:first-of-type' },
    { name: 'Member Details', selector: '.member-details:first-of-type' }
  ],
  'virtual-teams-all': [
    { name: 'Sidebar', selector: '#sidenav-main' },
    { name: 'Navbar', selector: '.navbar-main' },
    { name: 'Email Queue Panel', selector: '.email-queue' },
    { name: 'Email Queue Header', selector: '.email-queue-header' },
    { name: 'First Email Card', selector: '.email-card:first-child' },
    { name: 'Discussion Panel', selector: '.discussion-panel' },
    { name: 'Empty State', selector: '.empty-state' }
  ]
};

async function ensureOutputDir() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
}

async function captureScreenshot(browser, url, name) {
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait for content to load
  await page.waitForTimeout(2000);

  const screenshotPath = path.join(OUTPUT_DIR, `${name}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await page.close();

  return screenshotPath;
}

async function extractDOMStructure(browser, url, selectors) {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  const structure = {};

  for (const { name, selector } of selectors) {
    try {
      const element = await page.$(selector);
      if (element) {
        structure[name] = {
          exists: true,
          html: await element.innerHTML(),
          outerHTML: (await element.evaluate(el => el.outerHTML)).substring(0, 500), // Limit length
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
              minWidth: computed.minWidth,
              minHeight: computed.minHeight,
              // Effects
              opacity: computed.opacity,
              transform: computed.transform,
              transition: computed.transition
            };
          })
        };
      } else {
        structure[name] = { exists: false };
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

      // Compare classes
      if (v.classes !== a.classes) {
        differences.push({
          element: key,
          issue: 'Class differences',
          vanilla: v.classes,
          angular: a.classes
        });
      }
    }
  }

  return differences;
}

function generateReport(results) {
  let report = '# Visual Regression Test Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += `Vanilla URL: ${VANILLA_URL}\n`;
  report += `Angular URL: ${ANGULAR_URL}\n\n`;
  report += '---\n\n';

  for (const result of results) {
    report += `## ${result.page.toUpperCase()}\n\n`;

    // Visual comparison
    report += '### Visual Comparison\n\n';
    report += `- **Similarity**: ${result.visual.similarity}%\n`;
    report += `- **Different Pixels**: ${result.visual.diffPixels} / ${result.visual.totalPixels}\n`;
    report += `- **Screenshot Diff**: ${result.visual.diffPath}\n\n`;

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
          for (const styleDiff of diff.styleDiffs) {
            report += `  - \`${styleDiff.property}\`:\n`;
            report += `    - Vanilla: \`${styleDiff.vanilla}\`\n`;
            report += `    - Angular: \`${styleDiff.angular}\`\n`;
          }
        }

        if (diff.vanilla && diff.angular) {
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

async function runTests() {
  console.log('🚀 Starting Visual Regression Tests...\n');

  await ensureOutputDir();

  const browser = await chromium.launch({ headless: true });
  const results = [];

  try {
    for (const page of PAGES) {
      console.log(`📸 Testing ${page.name}...`);

      // Capture screenshots
      const vanillaUrl = `${VANILLA_URL}${page.vanillaPath}`;
      const angularUrl = `${ANGULAR_URL}${page.angularPath}`;

      console.log(`  - Capturing vanilla screenshot: ${vanillaUrl}`);
      const vanillaScreenshot = await captureScreenshot(
        browser,
        vanillaUrl,
        `${page.name}-vanilla`
      );

      console.log(`  - Capturing Angular screenshot: ${angularUrl}`);
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
      const selectors = ELEMENTS_TO_INSPECT[page.name] || [];
      const vanillaStructure = await extractDOMStructure(browser, vanillaUrl, selectors);
      const angularStructure = await extractDOMStructure(browser, angularUrl, selectors);

      // Compare structures
      console.log('  - Comparing structures...');
      const structuralDifferences = compareStructures(vanillaStructure, angularStructure);

      results.push({
        page: page.name,
        visual: visualComparison,
        structure: {
          vanilla: vanillaStructure,
          angular: angularStructure,
          differences: structuralDifferences
        }
      });

      console.log(`  ✅ ${page.name} - Similarity: ${visualComparison.similarity}%\n`);
    }

    // Generate report
    console.log('📝 Generating report...');
    const report = generateReport(results);
    const reportPath = path.join(OUTPUT_DIR, 'report.md');
    fs.writeFileSync(reportPath, report);

    // Save detailed JSON
    const jsonPath = path.join(OUTPUT_DIR, 'detailed-results.json');
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));

    console.log('\n✨ Tests complete!');
    console.log(`📊 Report: ${reportPath}`);
    console.log(`📄 Detailed results: ${jsonPath}`);
    console.log(`📁 Screenshots: ${OUTPUT_DIR}/\n`);

    // Print summary
    console.log('📋 Summary:');
    for (const result of results) {
      const status = parseFloat(result.visual.similarity) >= 99 ? '✅' : '⚠️';
      console.log(`  ${status} ${result.page}: ${result.visual.similarity}% similar, ${result.structure.differences.length} structural diffs`);
    }

  } finally {
    await browser.close();
  }
}

runTests().catch(console.error);
