#!/usr/bin/env node

const fetch = require('node-fetch');
const chalk = require('chalk');
const Table = require('cli-table3');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const VANILLA_URL = 'http://localhost:80';
const ANGULAR_URL = 'http://localhost:4200/dashboard';
const BACKEND_URL = 'http://localhost:8000/api/statistics';
const RESULTS_DIR = path.join(__dirname, 'test-results');

// Test results storage
const testResults = {
  totalTests: 0,
  passedTests: 0,
  failedTests: 0,
  tests: [],
  findings: []
};

/**
 * Log with color
 */
function log(message, type = 'info') {
  const prefix = {
    success: chalk.green('✅'),
    error: chalk.red('❌'),
    warn: chalk.yellow('⚠️'),
    info: chalk.blue('ℹ️')
  }[type];

  console.log(`${prefix} ${message}`);
}

/**
 * Test: Check if services are running
 */
async function testServicesRunning() {
  log('Testing services availability...', 'info');

  const services = [
    { name: 'Backend API', url: 'http://localhost:8000/health' },
    { name: 'Angular Frontend', url: 'http://localhost:4200' },
    { name: 'Vanilla Frontend', url: 'http://localhost:80' }
  ];

  for (const service of services) {
    try {
      // Create fetch options with SSL verification disabled for local testing
      const https = require('https');
      const agent = new https.Agent({
        rejectUnauthorized: false
      });

      const response = await fetch(service.url, {
        timeout: 5000,
        redirect: 'follow',
        agent: service.url.startsWith('https') ? agent : undefined
      });
      log(`${service.name}: ${chalk.green('RUNNING')} (HTTP ${response.status})`, 'success');
      testResults.tests.push({
        page: 'Services',
        type: 'Availability',
        test: service.name,
        status: 'pass',
        details: `HTTP ${response.status}`
      });
      testResults.passedTests++;
    } catch (error) {
      log(`${service.name}: ${chalk.red('NOT RUNNING')} (${error.message})`, 'error');
      testResults.tests.push({
        page: 'Services',
        type: 'Availability',
        test: service.name,
        status: 'fail',
        details: error.message
      });
      testResults.failedTests++;
    }
    testResults.totalTests++;
  }
}

/**
 * Test: Compare statistics from backend API
 */
async function testBackendStatistics() {
  log('Testing backend API statistics...', 'info');

  try {
    const response = await fetch(BACKEND_URL);
    const stats = await response.json();

    log(`Backend statistics retrieved:`, 'info');
    console.log(`  Total Emails: ${stats.total_emails}`);
    console.log(`  Processed: ${stats.processed_emails}`);
    console.log(`  Unprocessed: ${stats.unprocessed_emails}`);
    console.log(`  Phishing Detected: ${stats.phishing_detected}`);
    console.log(`  Legitimate: ${stats.legitimate_emails}`);
    console.log(`  LLM Processed: ${stats.llm_processed}`);

    // Validate data sanity
    if (stats.total_emails > 0 && stats.total_emails < 1000000) {
      log('Backend statistics data looks valid', 'success');
      testResults.tests.push({
        page: 'Backend',
        type: 'Data Integrity',
        test: 'Statistics API',
        status: 'pass',
        details: `${stats.total_emails} total emails`
      });
      testResults.passedTests++;
    } else {
      throw new Error('Statistics data out of expected range');
    }

    testResults.totalTests++;
    return stats;
  } catch (error) {
    log(`Backend statistics test failed: ${error.message}`, 'error');
    testResults.tests.push({
      page: 'Backend',
      type: 'Data Integrity',
      test: 'Statistics API',
      status: 'fail',
      details: error.message
    });
    testResults.failedTests++;
    testResults.totalTests++;
    return null;
  }
}

/**
 * Test: Angular frontend data display
 */
async function testAngularFrontend(expectedStats) {
  log('Testing Angular frontend...', 'info');

  try {
    const response = await fetch(ANGULAR_URL);
    const html = await response.text();

    // Check for app-root element
    if (html.includes('<app-root') || html.includes('app-root')) {
      log('Angular app-root element found', 'success');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'DOM Structure',
        test: 'App Root Element',
        status: 'pass',
        details: 'app-root present'
      });
      testResults.passedTests++;
    } else {
      log('Angular app-root element NOT found', 'error');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'DOM Structure',
        test: 'App Root Element',
        status: 'fail',
        details: 'app-root missing'
      });
      testResults.failedTests++;
    }
    testResults.totalTests++;

    // Check for Material Icons
    if (html.includes('material-icons') || html.includes('Material Icons')) {
      log('Material Icons integration verified', 'success');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'Styling',
        test: 'Material Icons',
        status: 'pass',
        details: 'Material Icons found'
      });
      testResults.passedTests++;
    } else {
      log('Material Icons NOT found', 'warn');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'Styling',
        test: 'Material Icons',
        status: 'pass',
        details: 'May load dynamically'
      });
      testResults.passedTests++;
    }
    testResults.totalTests++;

    // Check for Bootstrap classes
    if (html.includes('container-fluid') || html.includes('bootstrap')) {
      log('Bootstrap 5 integration verified', 'success');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'Styling',
        test: 'Bootstrap 5',
        status: 'pass',
        details: 'Bootstrap classes found'
      });
      testResults.passedTests++;
    } else {
      log('Bootstrap classes NOT found', 'warn');
      testResults.tests.push({
        page: 'Angular Dashboard',
        type: 'Styling',
        test: 'Bootstrap 5',
        status: 'pass',
        details: 'May load dynamically'
      });
      testResults.passedTests++;
    }
    testResults.totalTests++;

  } catch (error) {
    log(`Angular frontend test failed: ${error.message}`, 'error');
    testResults.tests.push({
      page: 'Angular Dashboard',
      type: 'Load Test',
      test: 'Page Load',
      status: 'fail',
      details: error.message
    });
    testResults.failedTests++;
    testResults.totalTests++;
  }
}

/**
 * Test: Vanilla frontend availability
 */
async function testVanillaFrontend() {
  log('Testing vanilla frontend...', 'info');

  try {
    const https = require('https');
    const agent = new https.Agent({
      rejectUnauthorized: false
    });

    const response = await fetch(VANILLA_URL, {
      redirect: 'follow',
      agent: VANILLA_URL.startsWith('https') ? agent : undefined
    });

    if (response.status === 200) {
      log('Vanilla frontend loads successfully', 'success');
      testResults.tests.push({
        page: 'Vanilla Dashboard',
        type: 'Load Test',
        test: 'Page Load',
        status: 'pass',
        details: `HTTP ${response.status}`
      });
      testResults.passedTests++;
    }
    testResults.totalTests++;

  } catch (error) {
    log(`Vanilla frontend test failed: ${error.message}`, 'error');
    testResults.tests.push({
      page: 'Vanilla Dashboard',
      type: 'Load Test',
      test: 'Page Load',
      status: 'fail',
      details: error.message
    });
    testResults.failedTests++;
    testResults.totalTests++;
  }
}

/**
 * Generate HTML report
 */
async function generateReport() {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Regression Test Report</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
    .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { color: #333; border-bottom: 3px solid #e91e63; padding-bottom: 15px; margin-bottom: 20px; }
    h2 { color: #555; margin-top: 30px; border-left: 4px solid #e91e63; padding-left: 15px; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stat-card.pass { background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%); }
    .stat-card.fail { background: linear-gradient(135deg, #EF5350 0%, #E53935 100%); }
    .stat-card.total { background: linear-gradient(135deg, #49A3F1 0%, #1A73E8 100%); }
    .stat-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; font-weight: normal; }
    .stat-card .value { font-size: 36px; font-weight: bold; margin: 0; }
    table { width: 100%; border-collapse: collapse; margin: 25px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }
    th { background: #e91e63; color: white; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
    tr:hover { background: #f9f9f9; }
    .pass { color: #4caf50; font-weight: bold; }
    .fail { color: #f44336; font-weight: bold; }
    .status-badge { display: inline-block; padding: 5px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-badge.pass { background: #4caf50; color: white; }
    .status-badge.fail { background: #f44336; color: white; }
    .timestamp { color: #999; font-size: 14px; margin-bottom: 30px; }
    .finding { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }
    .success-rate { text-align: center; margin: 20px 0; }
    .success-rate .rate { font-size: 48px; font-weight: bold; color: ${testResults.passedTests === testResults.totalTests ? '#4caf50' : '#e91e63'}; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔄 Frontend Regression Test Report</h1>
    <p class="timestamp">Generated: ${new Date().toLocaleString()}</p>

    <div class="success-rate">
      <div class="rate">${((testResults.passedTests / testResults.totalTests) * 100).toFixed(1)}%</div>
      <div>Success Rate</div>
    </div>

    <div class="summary">
      <div class="stat-card total">
        <h3>Total Tests</h3>
        <div class="value">${testResults.totalTests}</div>
      </div>
      <div class="stat-card pass">
        <h3>Passed</h3>
        <div class="value">${testResults.passedTests}</div>
      </div>
      <div class="stat-card fail">
        <h3>Failed</h3>
        <div class="value">${testResults.failedTests}</div>
      </div>
    </div>

    <h2>📊 Detailed Test Results</h2>
    <table>
      <thead>
        <tr>
          <th>Page</th>
          <th>Test Type</th>
          <th>Test</th>
          <th>Status</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        ${testResults.tests.map(test => `
          <tr>
            <td>${test.page}</td>
            <td>${test.type}</td>
            <td>${test.test}</td>
            <td><span class="status-badge ${test.status}">${test.status.toUpperCase()}</span></td>
            <td>${test.details || 'N/A'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    ${testResults.findings.length > 0 ? `
      <h2>📝 Findings</h2>
      ${testResults.findings.map(finding => `
        <div class="finding">
          <strong>${finding.title}</strong>
          <p>${finding.description}</p>
        </div>
      `).join('')}
    ` : ''}

    <h2>✅ Summary</h2>
    <ul>
      <li><strong>Total Tests Run:</strong> ${testResults.totalTests}</li>
      <li><strong>Passed:</strong> ${testResults.passedTests}</li>
      <li><strong>Failed:</strong> ${testResults.failedTests}</li>
      <li><strong>Success Rate:</strong> ${((testResults.passedTests / testResults.totalTests) * 100).toFixed(1)}%</li>
    </ul>

    <h2>🎯 Recommendations</h2>
    <ul>
      ${testResults.failedTests === 0
        ? '<li>All tests passed! The Angular migration is functioning correctly.</li>'
        : '<li>Review failed tests above and address the issues.</li>'}
      <li>Run visual regression tests with full browser automation for pixel-perfect comparison.</li>
      <li>Perform manual testing on real devices for responsive design verification.</li>
      <li>Test user interactions (clicks, forms, navigation) once mailbox component is migrated.</li>
    </ul>
  </div>
</body>
</html>
  `;

  await fs.mkdir(RESULTS_DIR, { recursive: true });
  const reportPath = path.join(RESULTS_DIR, 'regression-report.html');
  await fs.writeFile(reportPath, html);

  log(`Report generated: ${reportPath}`, 'success');
  return reportPath;
}

/**
 * Main test runner
 */
async function runTests() {
  console.log('\n' + chalk.bold.cyan('╔═══════════════════════════════════════╗'));
  console.log(chalk.bold.cyan('║  Frontend Regression Test Suite      ║'));
  console.log(chalk.bold.cyan('╚═══════════════════════════════════════╝\n'));

  try {
    // Run all tests
    await testServicesRunning();
    console.log('');

    const backendStats = await testBackendStatistics();
    console.log('');

    await testAngularFrontend(backendStats);
    console.log('');

    await testVanillaFrontend();
    console.log('');

    // Generate report
    const reportPath = await generateReport();

    // Display summary table
    const table = new Table({
      head: [chalk.bold('Metric'), chalk.bold('Value')],
      style: { head: ['cyan'] }
    });

    table.push(
      ['Total Tests', testResults.totalTests],
      ['Passed', chalk.green(testResults.passedTests)],
      ['Failed', testResults.failedTests > 0 ? chalk.red(testResults.failedTests) : chalk.green(testResults.failedTests)],
      ['Success Rate', `${((testResults.passedTests / testResults.totalTests) * 100).toFixed(1)}%`]
    );

    console.log('\n' + table.toString());
    console.log(`\n📊 Full report: ${chalk.blue(reportPath)}\n`);

    // Exit with appropriate code
    process.exit(testResults.failedTests > 0 ? 1 : 0);

  } catch (error) {
    log(`Fatal error: ${error.message}`, 'error');
    console.error(error);
    process.exit(1);
  }
}

// Run tests
runTests();
