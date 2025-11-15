#!/usr/bin/env node

/**
 * Server Availability Checker
 *
 * Checks if both vanilla and Angular servers are running
 * before running visual regression tests
 */

import http from 'http';
import { spawn } from 'child_process';

const VANILLA_URL = 'http://localhost';
const ANGULAR_URL = 'http://localhost:4200';

console.log('🔍 Checking server availability...\n');

async function checkServer(url, name) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: '/',
      method: 'GET',
      timeout: 2000
    };

    const req = http.request(options, (res) => {
      if (res.statusCode === 200 || res.statusCode === 304) {
        console.log(`✅ ${name} is running at ${url}`);
        resolve(true);
      } else {
        console.log(`⚠️ ${name} responded with status ${res.statusCode}`);
        resolve(false);
      }
    });

    req.on('error', (error) => {
      console.log(`❌ ${name} is NOT running at ${url}`);
      console.log(`   Error: ${error.message}`);
      resolve(false);
    });

    req.on('timeout', () => {
      console.log(`❌ ${name} timed out at ${url}`);
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function main() {
  const vanillaRunning = await checkServer(VANILLA_URL, 'Vanilla frontend');
  const angularRunning = await checkServer(ANGULAR_URL, 'Angular frontend');

  console.log();

  if (vanillaRunning && angularRunning) {
    console.log('✨ Both servers are running! Ready to test.\n');
    console.log('Run visual tests with:');
    console.log('  npm run test:visual              # Test implemented pages');
    console.log('  npm run test:visual:all          # Test all pages');
    console.log('  npm run test:visual:page <name>  # Test specific page');
    console.log('  npm run test:visual:list         # List all pages\n');

    // Ask if user wants to run tests
    const args = process.argv.slice(2);
    if (args.includes('--run')) {
      console.log('🚀 Starting visual regression tests...\n');
      const proc = spawn('node', ['visual-comparison.js'], {
        stdio: 'inherit',
        shell: true
      });

      proc.on('close', (code) => {
        process.exit(code);
      });
    }
  } else {
    console.log('⚠️ One or both servers are not running.\n');

    if (!vanillaRunning) {
      console.log('To start vanilla frontend:');
      console.log('  docker-compose up frontend\n');
      console.log('Or if already running, check port 80:');
      console.log('  docker-compose ps\n');
    }

    if (!angularRunning) {
      console.log('To start Angular frontend:');
      console.log('  cd frontend-angular');
      console.log('  npm start\n');
      console.log('Or check if already running on port 4200:');
      console.log('  lsof -i :4200\n');
    }

    console.log('Once both servers are running, run this script again or run tests directly.\n');
    process.exit(1);
  }
}

main().catch(console.error);
