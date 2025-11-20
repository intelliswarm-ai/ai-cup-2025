const fs = require('fs-extra');
const path = require('path');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

/**
 * Compare two screenshots and return the difference percentage
 * @param {Buffer} img1 - First image buffer
 * @param {Buffer} img2 - Second image buffer
 * @param {string} diffPath - Path to save diff image
 * @returns {Promise<{match: boolean, diffPixels: number, diffPercentage: number}>}
 */
async function compareScreenshots(img1Buffer, img2Buffer, diffPath) {
  const img1 = PNG.sync.read(img1Buffer);
  const img2 = PNG.sync.read(img2Buffer);

  const { width, height } = img1;
  const diff = new PNG({ width, height });

  const diffPixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 } // 10% threshold for differences
  );

  // Save diff image
  await fs.ensureDir(path.dirname(diffPath));
  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const totalPixels = width * height;
  const diffPercentage = (diffPixels / totalPixels) * 100;

  return {
    match: diffPixels === 0,
    diffPixels,
    diffPercentage,
    totalPixels
  };
}

/**
 * Extract and compare statistics data from both frontends
 * @param {Page} vanillaPage - Vanilla JS page
 * @param {Page} angularPage - Angular page
 * @returns {Promise<{match: boolean, differences: Array}>}
 */
async function compareStatistics(vanillaPage, angularPage) {
  // Extract statistics from vanilla JS frontend
  const vanillaStats = await vanillaPage.evaluate(() => {
    const stats = {};

    // Total Emails
    const totalEmailsEl = document.querySelector('[data-stat="total-emails"]');
    if (totalEmailsEl) {
      stats.totalEmails = parseInt(totalEmailsEl.textContent.replace(/,/g, ''));
    }

    // Unread Count
    const unreadEl = document.querySelector('[data-stat="unread"]');
    if (unreadEl) {
      stats.unread = parseInt(unreadEl.textContent.replace(/,/g, ''));
    }

    // Phishing Count
    const phishingEl = document.querySelector('[data-stat="phishing"]');
    if (phishingEl) {
      stats.phishing = parseInt(phishingEl.textContent.replace(/,/g, ''));
    }

    // Fraud Detected
    const fraudEl = document.querySelector('[data-stat="fraud"]');
    if (fraudEl) {
      stats.fraud = parseInt(fraudEl.textContent.replace(/,/g, ''));
    }

    return stats;
  });

  // Extract statistics from Angular frontend
  const angularStats = await angularPage.evaluate(() => {
    const stats = {};

    // Look for stats cards with Material Icons approach
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
      const title = card.querySelector('.text-capitalize, p.text-sm')?.textContent?.trim().toLowerCase();
      const value = card.querySelector('h4')?.textContent?.trim();

      if (title && value) {
        const numValue = parseInt(value.replace(/,/g, ''));
        if (title.includes('total')) stats.totalEmails = numValue;
        if (title.includes('unread')) stats.unread = numValue;
        if (title.includes('phishing')) stats.phishing = numValue;
        if (title.includes('fraud')) stats.fraud = numValue;
      }
    });

    return stats;
  });

  // Compare statistics
  const differences = [];
  const fields = ['totalEmails', 'unread', 'phishing', 'fraud'];

  fields.forEach(field => {
    if (vanillaStats[field] !== angularStats[field]) {
      differences.push({
        field,
        vanilla: vanillaStats[field],
        angular: angularStats[field]
      });
    }
  });

  return {
    match: differences.length === 0,
    differences,
    vanillaStats,
    angularStats
  };
}

/**
 * Compare page layout and structure
 * @param {Page} vanillaPage - Vanilla JS page
 * @param {Page} angularPage - Angular page
 * @returns {Promise<{match: boolean, differences: Array}>}
 */
async function compareLayout(vanillaPage, angularPage) {
  const vanillaLayout = await vanillaPage.evaluate(() => {
    return {
      hasHeader: !!document.querySelector('header, .header, nav'),
      hasSidebar: !!document.querySelector('.sidebar, aside, [role="navigation"]'),
      hasMainContent: !!document.querySelector('main, .main-content, .container-fluid'),
      statsCardCount: document.querySelectorAll('.card').length
    };
  });

  const angularLayout = await angularPage.evaluate(() => {
    return {
      hasHeader: !!document.querySelector('header, .header, nav'),
      hasSidebar: !!document.querySelector('.sidebar, aside, [role="navigation"]'),
      hasMainContent: !!document.querySelector('main, .main-content, .container-fluid'),
      statsCardCount: document.querySelectorAll('.card').length
    };
  });

  const differences = [];
  Object.keys(vanillaLayout).forEach(key => {
    if (vanillaLayout[key] !== angularLayout[key]) {
      differences.push({
        field: key,
        vanilla: vanillaLayout[key],
        angular: angularLayout[key]
      });
    }
  });

  return {
    match: differences.length === 0,
    differences,
    vanillaLayout,
    angularLayout
  };
}

/**
 * Generate HTML report
 * @param {Object} results - Test results
 * @param {string} outputPath - Output path for report
 */
async function generateReport(results, outputPath) {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Frontend Regression Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
    h1 { color: #333; border-bottom: 3px solid #e91e63; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
    .stat-card { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #e91e63; }
    .stat-card.pass { border-left-color: #4caf50; }
    .stat-card.fail { border-left-color: #f44336; }
    .stat-card h3 { margin: 0 0 5px 0; font-size: 14px; color: #666; }
    .stat-card .value { font-size: 24px; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background: #e91e63; color: white; }
    tr:hover { background: #f5f5f5; }
    .pass { color: #4caf50; font-weight: bold; }
    .fail { color: #f44336; font-weight: bold; }
    .screenshot { max-width: 100%; border: 1px solid #ddd; margin: 10px 0; }
    .comparison { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .comparison img { width: 100%; }
    .comparison-label { text-align: center; font-weight: bold; margin-bottom: 5px; }
    .timestamp { color: #999; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔄 Frontend Regression Test Report</h1>
    <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>

    <div class="summary">
      <div class="stat-card ${results.totalTests === results.passedTests ? 'pass' : 'fail'}">
        <h3>Total Tests</h3>
        <div class="value">${results.totalTests}</div>
      </div>
      <div class="stat-card pass">
        <h3>Passed</h3>
        <div class="value">${results.passedTests}</div>
      </div>
      <div class="stat-card fail">
        <h3>Failed</h3>
        <div class="value">${results.failedTests}</div>
      </div>
      <div class="stat-card">
        <h3>Success Rate</h3>
        <div class="value">${((results.passedTests / results.totalTests) * 100).toFixed(1)}%</div>
      </div>
    </div>

    <h2>📊 Test Results</h2>
    <table>
      <thead>
        <tr>
          <th>Page</th>
          <th>Test Type</th>
          <th>Status</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        ${results.tests.map(test => `
          <tr>
            <td>${test.page}</td>
            <td>${test.type}</td>
            <td class="${test.status}">${test.status.toUpperCase()}</td>
            <td>${test.details || 'N/A'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    ${results.screenshots ? `
      <h2>📸 Visual Comparison</h2>
      ${Object.keys(results.screenshots).map(page => `
        <h3>${page}</h3>
        <div class="comparison">
          <div>
            <div class="comparison-label">Vanilla JS</div>
            <img src="${results.screenshots[page].vanilla}" alt="Vanilla JS ${page}" class="screenshot">
          </div>
          <div>
            <div class="comparison-label">Angular</div>
            <img src="${results.screenshots[page].angular}" alt="Angular ${page}" class="screenshot">
          </div>
          <div>
            <div class="comparison-label">Difference</div>
            <img src="${results.screenshots[page].diff}" alt="Difference ${page}" class="screenshot">
            <p>Diff: ${results.screenshots[page].diffPercentage?.toFixed(2)}%</p>
          </div>
        </div>
      `).join('')}
    ` : ''}

    <h2>📝 Detailed Findings</h2>
    ${results.findings ? results.findings.map(finding => `
      <h3>${finding.title}</h3>
      <p>${finding.description}</p>
      ${finding.data ? `<pre>${JSON.stringify(finding.data, null, 2)}</pre>` : ''}
    `).join('') : '<p>No detailed findings recorded.</p>'}
  </div>
</body>
</html>
  `;

  await fs.ensureDir(path.dirname(outputPath));
  await fs.writeFile(outputPath, html);
}

module.exports = {
  compareScreenshots,
  compareStatistics,
  compareLayout,
  generateReport
};
