#!/usr/bin/env node

/**
 * Regression Test Runner
 *
 * Helps run visual regression tests with different configurations
 */

import { spawn } from 'child_process';
import { PAGES } from './visual-test-config.js';

const args = process.argv.slice(2);
const command = args[0];

function printHelp() {
  console.log(`
📸 Visual Regression Test Runner

Usage:
  npm run test:visual              - Test only implemented pages
  npm run test:visual:all          - Test all pages (including pending)
  npm run test:visual:page <name>  - Test specific page
  npm run test:visual:list         - List all available pages

Available Pages:
${PAGES.map(p => `  - ${p.name.padEnd(25)} [${p.status}] ${p.description}`).join('\n')}

Examples:
  npm run test:visual:page dashboard
  npm run test:visual:page mailbox

Similarity Threshold: 95% (configurable in visual-test-config.js)
  `);
}

function listPages() {
  console.log('\n📋 Available Pages:\n');
  console.log('Name'.padEnd(25) + 'Status'.padEnd(15) + 'Description');
  console.log('─'.repeat(70));

  for (const page of PAGES) {
    const statusEmoji = page.status === 'implemented' ? '✅' :
                       page.status === 'redirect' ? '🔄' : '⏳';
    console.log(
      page.name.padEnd(25) +
      `${statusEmoji} ${page.status}`.padEnd(15) +
      page.description
    );
  }

  console.log('\n💡 Implemented pages will be tested by default');
  console.log('💡 Use --all to test all pages\n');
}

function runTest(args) {
  const proc = spawn('node', ['visual-comparison.js', ...args], {
    stdio: 'inherit',
    shell: true
  });

  proc.on('close', (code) => {
    process.exit(code);
  });
}

// Handle commands
if (command === 'help' || command === '--help' || command === '-h') {
  printHelp();
} else if (command === 'list') {
  listPages();
} else if (command === 'page' && args[1]) {
  console.log(`\n🎯 Testing specific page: ${args[1]}\n`);
  runTest([`--page=${args[1]}`]);
} else if (command === 'all') {
  console.log('\n🌐 Testing all pages\n');
  runTest(['--all']);
} else if (command) {
  console.log(`❌ Unknown command: ${command}\n`);
  printHelp();
  process.exit(1);
} else {
  // Default: test implemented pages
  runTest([]);
}
