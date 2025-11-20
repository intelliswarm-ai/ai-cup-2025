#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');
const chalk = require('chalk');

const VANILLA_URL = 'http://localhost:80';
const ANGULAR_URL = 'http://localhost:4200/dashboard';
const SCREENSHOTS_DIR = path.join(__dirname, 'test-results', 'screenshots');

/**
 * Take screenshot of a page
 */
async function takeScreenshot(url, filename, page) {
  console.log(chalk.blue(`📸 Capturing: ${url}`));

  try {
    await page.goto(url, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for content to render
    await page.waitForTimeout(3000);

    // Take screenshot
    const screenshotPath = path.join(SCREENSHOTS_DIR, filename);
    await page.screenshot({
      path: screenshotPath,
      fullPage: true
    });

    console.log(chalk.green(`✅ Saved: ${filename}`));
    return screenshotPath;
  } catch (error) {
    console.error(chalk.red(`❌ Failed to capture ${url}: ${error.message}`));
    return null;
  }
}

/**
 * Compare two screenshots
 */
async function compareScreenshots(img1Path, img2Path, diffPath) {
  console.log(chalk.blue('\n🔍 Comparing screenshots...'));

  try {
    const img1 = PNG.sync.read(await fs.readFile(img1Path));
    const img2 = PNG.sync.read(await fs.readFile(img2Path));

    // Ensure images are same size
    const width = Math.max(img1.width, img2.width);
    const height = Math.max(img1.height, img2.height);

    // Resize if needed
    const resized1 = new PNG({ width, height });
    const resized2 = new PNG({ width, height });

    PNG.bitblt(img1, resized1, 0, 0, img1.width, img1.height, 0, 0);
    PNG.bitblt(img2, resized2, 0, 0, img2.width, img2.height, 0, 0);

    const diff = new PNG({ width, height });

    const diffPixels = pixelmatch(
      resized1.data,
      resized2.data,
      diff.data,
      width,
      height,
      { threshold: 0.1 }
    );

    // Save diff image
    await fs.writeFile(diffPath, PNG.sync.write(diff));

    const totalPixels = width * height;
    const diffPercentage = (diffPixels / totalPixels) * 100;

    console.log(chalk.yellow(`\n📊 Comparison Results:`));
    console.log(`  Resolution: ${width}x${height}`);
    console.log(`  Different pixels: ${diffPixels.toLocaleString()}`);
    console.log(`  Total pixels: ${totalPixels.toLocaleString()}`);
    console.log(`  Difference: ${diffPercentage.toFixed(2)}%`);

    if (diffPercentage < 5) {
      console.log(chalk.green(`\n✅ Images are very similar (< 5% diff)`));
    } else if (diffPercentage < 15) {
      console.log(chalk.yellow(`\n⚠️  Images have minor differences (5-15% diff)`));
    } else {
      console.log(chalk.red(`\n❌ Images are significantly different (> 15% diff)`));
    }

    return {
      diffPixels,
      totalPixels,
      diffPercentage,
      width,
      height
    };
  } catch (error) {
    console.error(chalk.red(`❌ Comparison failed: ${error.message}`));
    return null;
  }
}

/**
 * Extract visible elements from page
 */
async function analyzePageStructure(page, name) {
  console.log(chalk.blue(`\n🔍 Analyzing ${name} structure...`));

  const structure = await page.evaluate(() => {
    const info = {
      title: document.title,
      hasHeader: !!document.querySelector('header, nav, .header'),
      hasSidebar: !!document.querySelector('aside, .sidebar, [role="navigation"]'),
      statsCards: document.querySelectorAll('.card').length,
      buttons: document.querySelectorAll('button').length,
      inputs: document.querySelectorAll('input').length,
      links: document.querySelectorAll('a').length,
      headings: {
        h1: document.querySelectorAll('h1').length,
        h2: document.querySelectorAll('h2').length,
        h3: document.querySelectorAll('h3').length,
        h4: document.querySelectorAll('h4').length
      },
      colors: {
        backgroundColor: window.getComputedStyle(document.body).backgroundColor,
        color: window.getComputedStyle(document.body).color
      }
    };

    // Extract text content of stats cards
    const cards = Array.from(document.querySelectorAll('.card'));
    info.cardContents = cards.slice(0, 5).map(card => {
      const title = card.querySelector('.text-capitalize, .text-sm')?.textContent?.trim();
      const value = card.querySelector('h4, h3, .h4, .h3')?.textContent?.trim();
      return { title, value };
    });

    return info;
  });

  console.log(chalk.cyan(`\n  Title: ${structure.title}`));
  console.log(`  Header: ${structure.hasHeader ? '✅' : '❌'}`);
  console.log(`  Sidebar: ${structure.hasSidebar ? '✅' : '❌'}`);
  console.log(`  Stats Cards: ${structure.statsCards}`);
  console.log(`  Buttons: ${structure.buttons}`);
  console.log(`  Links: ${structure.links}`);
  console.log(`  Card Contents:`, structure.cardContents);

  return structure;
}

/**
 * Generate HTML report
 */
async function generateHTMLReport(vanillaPath, angularPath, diffPath, comparison, vanillaStructure, angularStructure) {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Visual Regression Report</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      margin: 0;
      padding: 20px;
      background: #f5f5f5;
    }
    .container {
      max-width: 1600px;
      margin: 0 auto;
      background: white;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 {
      color: #333;
      border-bottom: 4px solid #e91e63;
      padding-bottom: 15px;
      margin-bottom: 30px;
    }
    h2 {
      color: #555;
      margin-top: 40px;
      border-left: 5px solid #e91e63;
      padding-left: 15px;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin: 30px 0;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 25px;
      border-radius: 12px;
      color: white;
      box-shadow: 0 4px 6px rgba(0,0,0,0.15);
      text-align: center;
    }
    .stat-card h3 {
      margin: 0 0 10px 0;
      font-size: 14px;
      opacity: 0.9;
      font-weight: 500;
    }
    .stat-card .value {
      font-size: 36px;
      font-weight: bold;
      margin: 0;
    }
    .comparison-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 20px;
      margin: 30px 0;
    }
    .screenshot-box {
      border: 2px solid #ddd;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .screenshot-box h3 {
      margin: 0;
      padding: 15px;
      background: #f8f9fa;
      border-bottom: 2px solid #ddd;
      font-size: 16px;
      text-align: center;
    }
    .screenshot-box img {
      width: 100%;
      display: block;
      max-height: 600px;
      object-fit: contain;
      background: #fafafa;
    }
    .structure-comparison {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      margin: 30px 0;
    }
    .structure-box {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      border: 1px solid #dee2e6;
    }
    .structure-box h3 {
      margin-top: 0;
      color: #e91e63;
    }
    .structure-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #e9ecef;
    }
    .structure-item:last-child {
      border-bottom: none;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: bold;
    }
    .badge.match { background: #d4edda; color: #155724; }
    .badge.diff { background: #f8d7da; color: #721c24; }
    .timestamp {
      color: #6c757d;
      font-size: 14px;
      margin-bottom: 20px;
    }
    .alert {
      padding: 15px 20px;
      border-radius: 8px;
      margin: 20px 0;
    }
    .alert-success {
      background: #d4edda;
      border-left: 4px solid #28a745;
      color: #155724;
    }
    .alert-warning {
      background: #fff3cd;
      border-left: 4px solid #ffc107;
      color: #856404;
    }
    .alert-danger {
      background: #f8d7da;
      border-left: 4px solid #dc3545;
      color: #721c24;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📸 Visual Regression Test Report</h1>
    <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>

    ${comparison ? `
      ${comparison.diffPercentage < 5 ? `
        <div class="alert alert-success">
          <strong>✅ Excellent!</strong> Images are very similar (${comparison.diffPercentage.toFixed(2)}% difference)
        </div>
      ` : comparison.diffPercentage < 15 ? `
        <div class="alert alert-warning">
          <strong>⚠️ Minor Differences</strong> Images have some differences (${comparison.diffPercentage.toFixed(2)}%)
        </div>
      ` : `
        <div class="alert alert-danger">
          <strong>❌ Significant Differences</strong> Images are substantially different (${comparison.diffPercentage.toFixed(2)}%)
        </div>
      `}

      <div class="summary">
        <div class="stat-card">
          <h3>Resolution</h3>
          <div class="value">${comparison.width}×${comparison.height}</div>
        </div>
        <div class="stat-card">
          <h3>Different Pixels</h3>
          <div class="value">${comparison.diffPixels.toLocaleString()}</div>
        </div>
        <div class="stat-card">
          <h3>Total Pixels</h3>
          <div class="value">${comparison.totalPixels.toLocaleString()}</div>
        </div>
        <div class="stat-card">
          <h3>Difference %</h3>
          <div class="value">${comparison.diffPercentage.toFixed(2)}%</div>
        </div>
      </div>
    ` : ''}

    <h2>📷 Visual Comparison</h2>
    <div class="comparison-grid">
      <div class="screenshot-box">
        <h3>Vanilla JS Dashboard</h3>
        <img src="../screenshots/${path.basename(vanillaPath)}" alt="Vanilla Dashboard">
      </div>
      <div class="screenshot-box">
        <h3>Angular Dashboard</h3>
        <img src="../screenshots/${path.basename(angularPath)}" alt="Angular Dashboard">
      </div>
      <div class="screenshot-box">
        <h3>Pixel Difference</h3>
        <img src="../screenshots/${path.basename(diffPath)}" alt="Difference">
      </div>
    </div>

    <h2>🔍 Structure Analysis</h2>
    <div class="structure-comparison">
      <div class="structure-box">
        <h3>Vanilla JS Structure</h3>
        <div class="structure-item">
          <span>Header</span>
          <span class="badge ${vanillaStructure.hasHeader ? 'match' : 'diff'}">${vanillaStructure.hasHeader ? 'Yes' : 'No'}</span>
        </div>
        <div class="structure-item">
          <span>Sidebar</span>
          <span class="badge ${vanillaStructure.hasSidebar ? 'match' : 'diff'}">${vanillaStructure.hasSidebar ? 'Yes' : 'No'}</span>
        </div>
        <div class="structure-item">
          <span>Stats Cards</span>
          <span class="badge match">${vanillaStructure.statsCards}</span>
        </div>
        <div class="structure-item">
          <span>Buttons</span>
          <span class="badge match">${vanillaStructure.buttons}</span>
        </div>
        <div class="structure-item">
          <span>Links</span>
          <span class="badge match">${vanillaStructure.links}</span>
        </div>
      </div>

      <div class="structure-box">
        <h3>Angular Structure</h3>
        <div class="structure-item">
          <span>Header</span>
          <span class="badge ${angularStructure.hasHeader ? 'match' : 'diff'}">${angularStructure.hasHeader ? 'Yes' : 'No'}</span>
        </div>
        <div class="structure-item">
          <span>Sidebar</span>
          <span class="badge ${angularStructure.hasSidebar ? 'match' : 'diff'}">${angularStructure.hasSidebar ? 'Yes' : 'No'}</span>
        </div>
        <div class="structure-item">
          <span>Stats Cards</span>
          <span class="badge ${vanillaStructure.statsCards === angularStructure.statsCards ? 'match' : 'diff'}">${angularStructure.statsCards}</span>
        </div>
        <div class="structure-item">
          <span>Buttons</span>
          <span class="badge ${vanillaStructure.buttons === angularStructure.buttons ? 'match' : 'diff'}">${angularStructure.buttons}</span>
        </div>
        <div class="structure-item">
          <span>Links</span>
          <span class="badge ${vanillaStructure.links === angularStructure.links ? 'match' : 'diff'}">${angularStructure.links}</span>
        </div>
      </div>
    </div>

    <h2>📋 Findings</h2>
    <ul>
      ${vanillaStructure.hasHeader !== angularStructure.hasHeader ?
        `<li><strong>Header:</strong> Vanilla has ${vanillaStructure.hasHeader ? 'header' : 'no header'}, Angular has ${angularStructure.hasHeader ? 'header' : 'no header'}</li>` : ''}
      ${vanillaStructure.hasSidebar !== angularStructure.hasSidebar ?
        `<li><strong>Sidebar:</strong> Vanilla has ${vanillaStructure.hasSidebar ? 'sidebar' : 'no sidebar'}, Angular has ${angularStructure.hasSidebar ? 'sidebar' : 'no sidebar'}</li>` : ''}
      ${vanillaStructure.statsCards !== angularStructure.statsCards ?
        `<li><strong>Stats Cards:</strong> Vanilla has ${vanillaStructure.statsCards}, Angular has ${angularStructure.statsCards}</li>` : ''}
      ${comparison && comparison.diffPercentage > 15 ?
        `<li><strong>Visual Difference:</strong> ${comparison.diffPercentage.toFixed(2)}% of pixels differ - likely due to styling, colors, fonts, or layout differences</li>` : ''}
    </ul>

    <h2>💡 Recommendations</h2>
    <ul>
      <li>Review the screenshot comparison above to identify specific styling differences</li>
      <li>Check header/sidebar implementation if structures don't match</li>
      <li>Verify Bootstrap classes and Material Design implementation</li>
      <li>Compare font families, sizes, and colors</li>
      <li>Check spacing, padding, and margins</li>
      <li>Ensure card layouts and grid systems match</li>
    </ul>
  </div>
</body>
</html>
  `;

  const reportPath = path.join(SCREENSHOTS_DIR, '..', 'visual-report.html');
  await fs.writeFile(reportPath, html);
  return reportPath;
}

/**
 * Main function
 */
async function main() {
  console.log(chalk.bold.cyan('\n╔════════════════════════════════════════╗'));
  console.log(chalk.bold.cyan('║  Visual Regression Comparison          ║'));
  console.log(chalk.bold.cyan('╚════════════════════════════════════════╝\n'));

  // Create screenshots directory
  await fs.mkdir(SCREENSHOTS_DIR, { recursive: true });

  let browser;
  try {
    // Launch browser
    console.log(chalk.blue('🚀 Launching browser...'));
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // Take screenshots
    const vanillaPath = await takeScreenshot(VANILLA_URL, 'vanilla-dashboard.png', page);
    const vanillaStructure = await analyzePageStructure(page, 'Vanilla JS');

    const angularPath = await takeScreenshot(ANGULAR_URL, 'angular-dashboard.png', page);
    const angularStructure = await analyzePageStructure(page, 'Angular');

    await browser.close();

    if (!vanillaPath || !angularPath) {
      console.error(chalk.red('\n❌ Failed to capture one or more screenshots'));
      process.exit(1);
    }

    // Compare screenshots
    const diffPath = path.join(SCREENSHOTS_DIR, 'diff.png');
    const comparison = await compareScreenshots(vanillaPath, angularPath, diffPath);

    // Generate HTML report
    console.log(chalk.blue('\n📄 Generating HTML report...'));
    const reportPath = await generateHTMLReport(
      vanillaPath,
      angularPath,
      diffPath,
      comparison,
      vanillaStructure,
      angularStructure
    );

    console.log(chalk.green(`\n✅ Report generated: ${reportPath}`));
    console.log(chalk.cyan(`\n📊 View the report in your browser:`));
    console.log(chalk.cyan(`   file://${reportPath}\n`));

    // Exit with appropriate code
    if (comparison && comparison.diffPercentage > 15) {
      console.log(chalk.red('⚠️  Significant visual differences detected (>15%)'));
      process.exit(1);
    } else {
      console.log(chalk.green('✅ Visual comparison complete'));
      process.exit(0);
    }

  } catch (error) {
    console.error(chalk.red(`\n❌ Error: ${error.message}`));
    console.error(error.stack);
    if (browser) await browser.close();
    process.exit(1);
  }
}

main();
