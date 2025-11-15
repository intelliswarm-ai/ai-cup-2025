import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { CONFIG, PAGES, ELEMENTS_TO_INSPECT, STYLE_PROPERTIES } from './visual-test-config.js';

/**
 * Enhanced Visual Regression Testing System
 *
 * Compares vanilla JS and Angular implementations pixel-by-pixel,
 * checking DOM structure, CSS styles, and visual appearance.
 *
 * Usage:
 *   node visual-comparison.js                    # Test only implemented pages
 *   node visual-comparison.js --all              # Test all pages
 *   node visual-comparison.js --page=dashboard   # Test specific page
 */

// Parse command line arguments
const args = process.argv.slice(2);
const testAll = args.includes('--all');
const specificPage = args.find(arg => arg.startsWith('--page='))?.split('=')[1];

async function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.OUTPUT_DIR)) {
    fs.mkdirSync(CONFIG.OUTPUT_DIR, { recursive: true });
  }
}

async function archiveResults() {
  if (!CONFIG.ARCHIVE_RESULTS) return;

  // Check if there are existing results to archive
  if (!fs.existsSync(CONFIG.OUTPUT_DIR)) return;

  const files = fs.readdirSync(CONFIG.OUTPUT_DIR);
  if (files.length === 0) return;

  // Create archive directory
  if (!fs.existsSync(CONFIG.ARCHIVE_DIR)) {
    fs.mkdirSync(CONFIG.ARCHIVE_DIR, { recursive: true });
  }

  // Create timestamped subdirectory
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const archivePath = path.join(CONFIG.ARCHIVE_DIR, timestamp);
  fs.mkdirSync(archivePath, { recursive: true });

  // Copy all files to archive
  for (const file of files) {
    const sourcePath = path.join(CONFIG.OUTPUT_DIR, file);
    const destPath = path.join(archivePath, file);
    fs.copyFileSync(sourcePath, destPath);
  }

  console.log(`📦 Archived previous results to: ${archivePath}\n`);
}

async function captureScreenshot(browser, url, name, errorCallback) {
  try {
    const context = await browser.newContext({
      ignoreHTTPSErrors: CONFIG.IGNORE_HTTPS_ERRORS || false
    });
    const page = await context.newPage();
    await page.setViewportSize(CONFIG.VIEWPORT);

    // Navigate with timeout
    await page.goto(url, {
      waitUntil: 'load',
      timeout: 30000
    });

    // Wait for content to load
    await page.waitForTimeout(CONFIG.WAIT_TIME);

    // Page-specific wait conditions
    if (name.includes('mailbox')) {
      // For mailbox, wait for email cards to be loaded
      try {
        await page.waitForSelector('.email-card', { timeout: 15000 });
        // Wait a bit more for all emails to render
        await page.waitForTimeout(5000);
      } catch (e) {
        console.log('    ⚠️ Email cards not found, proceeding anyway...');
      }
    }

    const screenshotPath = path.join(CONFIG.OUTPUT_DIR, `${name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    await context.close();

    return { success: true, path: screenshotPath };
  } catch (error) {
    if (errorCallback) {
      errorCallback(error);
    }
    return { success: false, error: error.message };
  }
}

async function extractDOMStructure(browser, url, selectors) {
  try {
    const context = await browser.newContext({
      ignoreHTTPSErrors: CONFIG.IGNORE_HTTPS_ERRORS || false
    });
    const page = await context.newPage();
    await page.goto(url, {
      waitUntil: 'load',
      timeout: 30000
    });
    await page.waitForTimeout(CONFIG.WAIT_TIME);

    const structure = {};

    for (const { name, selector } of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          // Extract computed styles
          const styles = {};
          for (const prop of STYLE_PROPERTIES) {
            const value = await element.evaluate((el, property) => {
              return window.getComputedStyle(el)[property];
            }, prop);
            styles[prop] = value;
          }

          structure[name] = {
            exists: true,
            classes: await element.evaluate(el => el.className),
            styles,
            tagName: await element.evaluate(el => el.tagName),
            visible: await element.isVisible()
          };
        } else {
          structure[name] = { exists: false };
        }
      } catch (error) {
        structure[name] = { error: error.message };
      }
    }

    await context.close();
    return { success: true, data: structure };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

function compareImages(img1Path, img2Path, diffPath) {
  try {
    const img1 = PNG.sync.read(fs.readFileSync(img1Path));
    const img2 = PNG.sync.read(fs.readFileSync(img2Path));

    const { width: width1, height: height1 } = img1;
    const { width: width2, height: height2 } = img2;

    // Check width match (must be exact)
    if (width1 !== width2) {
      return {
        success: false,
        error: `Image widths don't match: ${width1} vs ${width2}`
      };
    }

    // Allow small height differences (within 1% or 100px, whichever is larger)
    const heightDiff = Math.abs(height1 - height2);
    const heightTolerance = Math.max(100, Math.max(height1, height2) * 0.01);

    if (heightDiff > heightTolerance) {
      return {
        success: false,
        error: `Image heights differ by ${heightDiff}px (tolerance: ${heightTolerance.toFixed(0)}px): ${height1} vs ${height2}`
      };
    }

    // Use the smaller height for comparison to avoid issues
    const compareHeight = Math.min(height1, height2);
    const width = width1;

    // Create cropped buffers if heights differ
    let img1Data = img1.data;
    let img2Data = img2.data;

    if (height1 !== compareHeight || height2 !== compareHeight) {
      const bytesPerRow = width * 4; // 4 bytes per pixel (RGBA)
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
      { threshold: CONFIG.DIFF_THRESHOLD }
    );

    fs.writeFileSync(diffPath, PNG.sync.write(diff));

    const totalPixels = width * compareHeight;
    const percentageDiff = (numDiffPixels / totalPixels) * 100;

    return {
      success: true,
      diffPixels: numDiffPixels,
      totalPixels,
      percentageDiff: percentageDiff.toFixed(4),
      similarity: (100 - percentageDiff).toFixed(4),
      heightDiff: heightDiff > 0 ? `${heightDiff}px (${height1}px vs ${height2}px)` : undefined
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
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
      // Compare visibility
      if (v.visible !== a.visible) {
        differences.push({
          element: key,
          issue: 'Visibility mismatch',
          vanilla: v.visible,
          angular: a.visible
        });
      }

      // Compare styles
      const styleDiffs = [];
      if (v.styles && a.styles) {
        for (const [prop, value] of Object.entries(v.styles)) {
          if (a.styles[prop] !== value) {
            // Normalize color values for comparison
            const normalized = normalizeStyle(prop, value, a.styles[prop]);
            if (!normalized.equal) {
              styleDiffs.push({
                property: prop,
                vanilla: normalized.vanilla,
                angular: normalized.angular
              });
            }
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

function normalizeStyle(property, vanilla, angular) {
  // Normalize color values (rgb, rgba, hex)
  if (property.toLowerCase().includes('color')) {
    const v = normalizeColor(vanilla);
    const a = normalizeColor(angular);
    return { equal: v === a, vanilla: v, angular: a };
  }

  // Normalize pixel values
  if (typeof vanilla === 'string' && vanilla.endsWith('px') && typeof angular === 'string' && angular.endsWith('px')) {
    const vNum = parseFloat(vanilla);
    const aNum = parseFloat(angular);
    // Allow 1px tolerance
    return { equal: Math.abs(vNum - aNum) <= 1, vanilla, angular };
  }

  return { equal: vanilla === angular, vanilla, angular };
}

function normalizeColor(color) {
  if (!color) return 'transparent';
  // Simple normalization - can be enhanced
  return color.toLowerCase().replace(/\s+/g, '');
}

function generateReport(results) {
  let report = '# Visual Regression Test Report\n\n';
  report += `Generated: ${new Date().toLocaleString()}\n\n`;
  report += `**Vanilla URL**: ${CONFIG.VANILLA_URL}\n`;
  report += `**Angular URL**: ${CONFIG.ANGULAR_URL}\n\n`;
  report += `**Pass Threshold**: ${CONFIG.PASS_THRESHOLD}%\n\n`;
  report += '---\n\n';

  // Summary table
  report += '## Summary\n\n';
  report += '| Page | Status | Similarity | Structural Diffs | Notes |\n';
  report += '|------|--------|------------|------------------|-------|\n';

  for (const result of results) {
    const pageInfo = PAGES.find(p => p.name === result.page);
    const status = result.skipped ? '⏭️ SKIPPED' :
                   result.error ? '❌ ERROR' :
                   parseFloat(result.visual?.similarity || 0) >= CONFIG.PASS_THRESHOLD ? '✅ PASS' : '⚠️ FAIL';
    const similarity = result.visual?.similarity || 'N/A';
    const diffs = result.structure?.differences?.length || 'N/A';
    const notes = result.skipped ? `(${pageInfo?.status || 'not implemented'})` :
                  result.error ? result.error : '';

    report += `| ${result.page} | ${status} | ${similarity}% | ${diffs} | ${notes} |\n`;
  }

  report += '\n---\n\n';

  // Detailed results
  report += '## Detailed Results\n\n';

  for (const result of results) {
    if (result.skipped) continue;

    const pageInfo = PAGES.find(p => p.name === result.page);
    report += `## ${result.page.toUpperCase()}\n\n`;

    if (pageInfo) {
      report += `**Description**: ${pageInfo.description}\n`;
      report += `**Status**: ${pageInfo.status}\n\n`;
    }

    if (result.error) {
      report += `❌ **ERROR**: ${result.error}\n\n`;
      continue;
    }

    // Visual comparison
    report += '### Visual Comparison\n\n';
    report += `- **Similarity**: ${result.visual.similarity}%\n`;
    report += `- **Different Pixels**: ${result.visual.diffPixels.toLocaleString()} / ${result.visual.totalPixels.toLocaleString()}\n`;
    report += `- **Screenshots**:\n`;
    report += `  - Vanilla: \`${result.page}-vanilla.png\`\n`;
    report += `  - Angular: \`${result.page}-angular.png\`\n`;
    report += `  - Diff: \`${result.page}-diff.png\`\n\n`;

    const similarity = parseFloat(result.visual.similarity);
    if (similarity >= CONFIG.PASS_THRESHOLD) {
      report += '✅ **Visual parity achieved!**\n\n';
    } else if (similarity >= 90) {
      report += '⚠️ **Good progress, minor differences remain**\n\n';
    } else {
      report += '❌ **Significant visual differences detected!**\n\n';
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
          report += '- **Style Differences**:\n\n';
          report += '| Property | Vanilla | Angular |\n';
          report += '|----------|---------|----------|\n';
          for (const styleDiff of diff.styleDiffs) {
            report += `| \`${styleDiff.property}\` | \`${styleDiff.vanilla}\` | \`${styleDiff.angular}\` |\n`;
          }
          report += '\n';
        }

        if (diff.vanilla !== undefined && diff.angular !== undefined && !diff.styleDiffs) {
          report += `- **Vanilla**: \`${diff.vanilla}\`\n`;
          report += `- **Angular**: \`${diff.angular}\`\n`;
        }

        report += '\n';
      }
    }

    report += '---\n\n';
  }

  return report;
}

async function runTests() {
  console.log('🚀 Starting Enhanced Visual Regression Tests...\n');

  // Determine which pages to test
  let pagesToTest;
  if (specificPage) {
    pagesToTest = PAGES.filter(p => p.name === specificPage);
    if (pagesToTest.length === 0) {
      console.error(`❌ Page "${specificPage}" not found`);
      process.exit(1);
    }
    console.log(`📋 Testing specific page: ${specificPage}\n`);
  } else if (testAll) {
    pagesToTest = PAGES;
    console.log(`📋 Testing ALL pages (${PAGES.length} total)\n`);
  } else {
    pagesToTest = PAGES.filter(p => p.status === 'implemented');
    console.log(`📋 Testing implemented pages only (${pagesToTest.length} pages)\n`);
    console.log(`💡 Use --all to test all pages, or --page=<name> for specific page\n`);
  }

  await archiveResults();
  await ensureOutputDir();

  const browser = await chromium.launch({
    headless: true,
    ignoreHTTPSErrors: CONFIG.IGNORE_HTTPS_ERRORS || false
  });
  const results = [];

  try {
    for (const page of pagesToTest) {
      console.log(`📸 Testing ${page.name} [${page.status}]...`);

      // Skip pending pages unless testing all
      if (page.status === 'pending' && !testAll && !specificPage) {
        console.log(`  ⏭️ Skipping (not yet implemented)\n`);
        results.push({
          page: page.name,
          skipped: true,
          reason: 'Not yet implemented'
        });
        continue;
      }

      // Capture screenshots
      const vanillaUrl = `${CONFIG.VANILLA_URL}${page.vanillaPath}`;
      const angularUrl = `${CONFIG.ANGULAR_URL}${page.angularPath}`;

      console.log(`  - Capturing vanilla screenshot: ${vanillaUrl}`);
      const vanillaScreenshot = await captureScreenshot(
        browser,
        vanillaUrl,
        `${page.name}-vanilla`,
        (error) => console.log(`    ⚠️ Warning: ${error.message}`)
      );

      if (!vanillaScreenshot.success) {
        console.log(`  ❌ Failed to capture vanilla screenshot\n`);
        results.push({
          page: page.name,
          error: `Vanilla: ${vanillaScreenshot.error}`
        });
        continue;
      }

      console.log(`  - Capturing Angular screenshot: ${angularUrl}`);
      const angularScreenshot = await captureScreenshot(
        browser,
        angularUrl,
        `${page.name}-angular`,
        (error) => console.log(`    ⚠️ Warning: ${error.message}`)
      );

      if (!angularScreenshot.success) {
        console.log(`  ❌ Failed to capture Angular screenshot\n`);
        results.push({
          page: page.name,
          error: `Angular: ${angularScreenshot.error}`
        });
        continue;
      }

      // Compare screenshots
      console.log('  - Comparing screenshots...');
      const diffPath = path.join(CONFIG.OUTPUT_DIR, `${page.name}-diff.png`);
      const visualComparison = compareImages(
        vanillaScreenshot.path,
        angularScreenshot.path,
        diffPath
      );

      if (!visualComparison.success) {
        console.log(`  ❌ Failed to compare screenshots: ${visualComparison.error}\n`);
        results.push({
          page: page.name,
          error: visualComparison.error
        });
        continue;
      }

      // Extract DOM structures
      console.log('  - Extracting DOM structures...');
      const selectors = ELEMENTS_TO_INSPECT[page.name] || [];
      const vanillaStructure = await extractDOMStructure(browser, vanillaUrl, selectors);
      const angularStructure = await extractDOMStructure(browser, angularUrl, selectors);

      // Compare structures
      console.log('  - Comparing structures...');
      const structuralDifferences = compareStructures(
        vanillaStructure.data || {},
        angularStructure.data || {}
      );

      results.push({
        page: page.name,
        visual: visualComparison,
        structure: {
          vanilla: vanillaStructure.data,
          angular: angularStructure.data,
          differences: structuralDifferences
        }
      });

      const status = parseFloat(visualComparison.similarity) >= CONFIG.PASS_THRESHOLD ? '✅' : '⚠️';
      console.log(`  ${status} ${page.name} - Similarity: ${visualComparison.similarity}%\n`);
    }

    // Generate report
    console.log('📝 Generating report...');
    const report = generateReport(results);
    const reportPath = path.join(CONFIG.OUTPUT_DIR, 'report.md');
    fs.writeFileSync(reportPath, report);

    // Save detailed JSON
    const jsonPath = path.join(CONFIG.OUTPUT_DIR, 'detailed-results.json');
    fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));

    console.log('\n✨ Tests complete!');
    console.log(`📊 Report: ${reportPath}`);
    console.log(`📄 Detailed results: ${jsonPath}`);
    console.log(`📁 Screenshots: ${CONFIG.OUTPUT_DIR}/\n`);

    // Print summary
    console.log('📋 Summary:');
    const passed = results.filter(r => !r.skipped && !r.error && parseFloat(r.visual?.similarity || 0) >= CONFIG.PASS_THRESHOLD).length;
    const failed = results.filter(r => !r.skipped && !r.error && parseFloat(r.visual?.similarity || 0) < CONFIG.PASS_THRESHOLD).length;
    const errors = results.filter(r => r.error).length;
    const skipped = results.filter(r => r.skipped).length;

    console.log(`  ✅ Passed: ${passed}`);
    console.log(`  ⚠️ Failed: ${failed}`);
    console.log(`  ❌ Errors: ${errors}`);
    console.log(`  ⏭️ Skipped: ${skipped}`);
    console.log(`  📊 Total: ${results.length}\n`);

    for (const result of results) {
      if (result.skipped) {
        console.log(`  ⏭️ ${result.page}: Skipped (${result.reason})`);
      } else if (result.error) {
        console.log(`  ❌ ${result.page}: Error - ${result.error}`);
      } else {
        const status = parseFloat(result.visual.similarity) >= CONFIG.PASS_THRESHOLD ? '✅' : '⚠️';
        console.log(`  ${status} ${result.page}: ${result.visual.similarity}% similar, ${result.structure.differences.length} structural diffs`);
      }
    }

    console.log();

    // Exit with error if any tests failed
    if (failed > 0 || errors > 0) {
      process.exit(1);
    }

  } finally {
    await browser.close();
  }
}

runTests().catch(console.error);
