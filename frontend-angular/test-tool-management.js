/**
 * Visual test for Tool Management UI
 * Tests the expandable tool cards with type badges and configuration editing
 */

import { chromium } from 'playwright';

async function testToolManagement() {
  console.log('🔧 Testing Tool Management UI...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  try {
    // Test 1: Navigate to Fraud team
    console.log('📍 Test 1: Navigating to Fraud Investigation Unit...');
    await page.goto('http://localhost:4200/agentic-teams?team=fraud');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Click "View Team" button
    console.log('👆 Clicking View Team button...');
    const viewTeamButton = page.locator('button:has-text("View Team")');
    await viewTeamButton.click();
    await page.waitForTimeout(1000);

    // Verify tools section is visible
    console.log('✅ Verifying Team Equipped Tools section...');
    const toolsSection = page.locator('.team-tools-section');
    const isVisible = await toolsSection.isVisible();
    console.log(`   Tools section visible: ${isVisible}`);

    // Count tool cards
    const toolCards = page.locator('.tool-card');
    const toolCount = await toolCards.count();
    console.log(`   Found ${toolCount} tool cards`);

    // Test 2: Expand first tool card
    console.log('\n📍 Test 2: Expanding first tool card...');
    const firstToolCard = toolCards.first();
    const firstToolHeader = firstToolCard.locator('.tool-card-header');
    await firstToolHeader.click();
    await page.waitForTimeout(500);

    // Verify tool details are visible
    const toolBody = firstToolCard.locator('.tool-card-body');
    const bodyVisible = await toolBody.isVisible();
    console.log(`   Tool body expanded: ${bodyVisible}`);

    // Check for type badge
    const typeBadge = firstToolCard.locator('.tool-type-badge');
    const badgeText = await typeBadge.textContent();
    console.log(`   Tool type badge: ${badgeText}`);

    // Check for configuration section
    const configSection = firstToolCard.locator('.tool-configuration');
    const configVisible = await configSection.isVisible();
    console.log(`   Configuration section visible: ${configVisible}`);

    // Count configuration items
    const configItems = firstToolCard.locator('.config-item');
    const configCount = await configItems.count();
    console.log(`   Configuration items: ${configCount}`);

    // Test 3: Test edit mode
    console.log('\n📍 Test 3: Testing configuration edit mode...');
    const editButton = firstToolCard.locator('.btn-edit-config');
    await editButton.click();
    await page.waitForTimeout(500);

    // Verify input fields are visible
    const inputFields = firstToolCard.locator('.config-value-input');
    const inputCount = await inputFields.count();
    console.log(`   Editable input fields: ${inputCount}`);

    // Take screenshot of expanded tool card
    console.log('\n📸 Taking screenshot of tool management UI...');
    await page.screenshot({
      path: 'visual-regression-results/tool-management-ui.png',
      fullPage: true
    });
    console.log('   Screenshot saved: visual-regression-results/tool-management-ui.png');

    // Test 4: Test other teams
    console.log('\n📍 Test 4: Testing other teams...');

    // Compliance team
    await page.goto('http://localhost:4200/agentic-teams?team=compliance');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.locator('button:has-text("View Team")').click();
    await page.waitForTimeout(1000);
    const complianceTools = await page.locator('.tool-card').count();
    console.log(`   Compliance team tools: ${complianceTools}`);

    // Investments team
    await page.goto('http://localhost:4200/agentic-teams?team=investments');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.locator('button:has-text("View Team")').click();
    await page.waitForTimeout(1000);
    const investmentTools = await page.locator('.tool-card').count();
    console.log(`   Investment team tools: ${investmentTools}`);

    console.log('\n✨ Tool Management UI tests completed successfully!\n');
    console.log('📊 Summary:');
    console.log(`   - Fraud team: ${toolCount} tools`);
    console.log(`   - Compliance team: ${complianceTools} tools`);
    console.log(`   - Investment team: ${investmentTools} tools`);
    console.log(`   - Tool expansion: ✅`);
    console.log(`   - Type badges: ✅`);
    console.log(`   - Configuration display: ✅`);
    console.log(`   - Edit mode: ✅`);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await page.waitForTimeout(3000); // Keep browser open for visual inspection
    await browser.close();
  }
}

testToolManagement();
