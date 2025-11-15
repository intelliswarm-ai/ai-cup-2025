const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture console logs
  page.on('console', msg => {
    const text = msg.text();
    console.log('CONSOLE:', text);
  });

  // Capture errors
  page.on('pageerror', error => {
    console.error('PAGE ERROR:', error.message);
  });

  console.log('Navigating to dashboard...');
  await page.goto('http://localhost:4200/dashboard', {
    waitUntil: 'domcontentloaded',
    timeout: 30000
  });

  // Wait a bit for charts to initialize
  await page.waitForTimeout(3000);

  // Check if canvas elements exist
  const canvasCount = await page.locator('canvas').count();
  console.log(`\nFound ${canvasCount} canvas elements`);

  // Try to get chart data
  const chartData = await page.evaluate(() => {
    const canvases = document.querySelectorAll('canvas');
    return Array.from(canvases).map((canvas, index) => ({
      index,
      id: canvas.id,
      width: canvas.width,
      height: canvas.height
    }));
  });

  console.log('\nCanvas details:');
  chartData.forEach(canvas => {
    console.log(`  Canvas ${canvas.index}: ${canvas.id || 'no-id'} (${canvas.width}x${canvas.height})`);
  });

  // Wait for any additional logs
  await page.waitForTimeout(2000);

  await browser.close();
  console.log('\nTest complete!');
})();
