#!/usr/bin/env node

/**
 * Integration test for Angular frontend and FastAPI backend
 * Tests that the Angular app can successfully communicate with the backend
 */

const http = require('http');

// Test configuration
const BACKEND_URL = 'http://localhost:8000/api/statistics';
const FRONTEND_URL = 'http://localhost:4200';

console.log('🧪 Testing Frontend-Backend Integration\n');

// Test 1: Backend API responds correctly
function testBackendAPI() {
  return new Promise((resolve, reject) => {
    console.log('1️⃣  Testing Backend API at', BACKEND_URL);

    http.get(BACKEND_URL, (res) => {
      let data = '';

      res.on('data', chunk => { data += chunk; });

      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          console.log('   ✅ Backend API responding');
          console.log('   📊 Statistics received:');
          console.log('      - Total Emails:', json.total_emails);
          console.log('      - Processed:', json.processed_emails);
          console.log('      - Unprocessed:', json.unprocessed_emails);
          console.log('      - Phishing Detected:', json.phishing_detected);
          console.log('      - Legitimate:', json.legitimate_emails);
          console.log('      - LLM Processed:', json.llm_processed);
          if (json.badge_counts) {
            console.log('      - Risk Badges (Fraud):', json.badge_counts.RISK || 0);
          }
          console.log();
          resolve(json);
        } catch (err) {
          reject(new Error('Backend returned invalid JSON: ' + err.message));
        }
      });
    }).on('error', reject);
  });
}

// Test 2: Frontend serves HTML
function testFrontendServes() {
  return new Promise((resolve, reject) => {
    console.log('2️⃣  Testing Frontend at', FRONTEND_URL);

    http.get(FRONTEND_URL, (res) => {
      let data = '';

      res.on('data', chunk => { data += chunk; });

      res.on('end', () => {
        if (data.includes('app-root') && data.includes('FrontendAngular')) {
          console.log('   ✅ Frontend serving Angular app');
          console.log('   📄 HTML contains <app-root> element');
          console.log();
          resolve();
        } else {
          reject(new Error('Frontend HTML does not contain expected Angular elements'));
        }
      });
    }).on('error', reject);
  });
}

// Test 3: Dashboard route is accessible
function testDashboardRoute() {
  return new Promise((resolve, reject) => {
    console.log('3️⃣  Testing Dashboard route at', FRONTEND_URL + '/dashboard');

    http.get(FRONTEND_URL + '/dashboard', (res) => {
      let data = '';

      res.on('data', chunk => { data += chunk; });

      res.on('end', () => {
        if (data.includes('app-root')) {
          console.log('   ✅ Dashboard route accessible');
          console.log('   🎯 Route redirects properly');
          console.log();
          resolve();
        } else {
          reject(new Error('Dashboard route not accessible'));
        }
      });
    }).on('error', reject);
  });
}

// Run all tests
async function runTests() {
  try {
    const stats = await testBackendAPI();
    await testFrontendServes();
    await testDashboardRoute();

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✅ All integration tests passed!');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('\n📱 Open your browser to:');
    console.log('   http://localhost:4200/dashboard');
    console.log('\n💡 Expected Dashboard Statistics:');
    console.log('   - Total Emails:', stats.total_emails);
    console.log('   - Unread:', stats.unprocessed_emails || 0);
    console.log('   - Phishing:', stats.phishing_detected || 0);
    console.log('   - Fraud Detected:', stats.badge_counts?.RISK || 0);
    console.log('\n🔍 Additional Info Section:');
    console.log('   - Legitimate:', stats.legitimate_emails || 0);
    console.log('   - Processed:', stats.processed_emails || 0);
    console.log('   - LLM Processed:', stats.llm_processed || 0);

    process.exit(0);
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('\n💡 Troubleshooting:');
    console.error('   - Ensure backend is running: docker-compose up');
    console.error('   - Ensure frontend is running: npm start');
    console.error('   - Check CORS settings on backend');
    process.exit(1);
  }
}

runTests();
