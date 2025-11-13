# Frontend Regression Tests

Comprehensive regression testing suite comparing the vanilla JS frontend with the Angular frontend.

## Overview

This test suite ensures that the Angular frontend migration maintains feature parity and data accuracy with the existing vanilla JS frontend.

### Test Types

1. **Visual Regression**: Screenshot comparison with pixel-diff analysis
2. **Data Accuracy**: Statistics and content verification
3. **Layout Structure**: DOM structure and element presence
4. **Loading States**: Spinner and async data loading
5. **Responsive Design**: Multi-viewport testing
6. **API Integration**: Request/response verification
7. **Error Handling**: Graceful failure testing

## Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers
npm run install-browsers
```

## Running Tests

### Quick Start
```bash
# Run all tests
npm test

# Run with UI (interactive mode)
npm run test:ui

# Run in headed mode (see browser)
npm run test:headed

# View last test report
npm run test:report
```

### Advanced Usage
```bash
# Run specific test file
npx playwright test tests/dashboard.spec.js

# Run specific test
npx playwright test -g "Statistics Data Comparison"

# Run in debug mode
npx playwright test --debug

# Update snapshots
npx playwright test --update-snapshots
```

## Test Structure

```
regression-tests/
├── tests/
│   ├── dashboard.spec.js          # Dashboard page tests
│   ├── mailbox.spec.js            # Mailbox page tests (future)
│   └── agentic-teams.spec.js      # Agentic teams tests (future)
├── utils/
│   └── comparison-helpers.js       # Reusable comparison utilities
├── test-results/
│   ├── screenshots/                # Visual comparison screenshots
│   ├── html/                       # HTML test report
│   └── results.json                # JSON test results
├── playwright.config.js            # Playwright configuration
└── package.json
```

## Test Results

After running tests, view the HTML report:
```bash
npm run test:report
```

This opens a detailed report showing:
- Test pass/fail status
- Screenshot comparisons
- Data discrepancies
- Performance metrics
- Error logs

## Current Test Coverage

### Dashboard Page ✅

| Test | Status | Description |
|------|--------|-------------|
| Visual Comparison | ✅ | Compares full-page screenshots (<15% diff allowed) |
| Statistics Data | ✅ | Verifies all statistics match exactly |
| Layout Structure | ✅ | Checks DOM structure and element counts |
| Loading States | ✅ | Verifies loading spinner behavior |
| Responsive Layout | ✅ | Tests Desktop/Tablet/Mobile viewports |
| API Integration | ✅ | Validates API calls and responses |
| Error Handling | ✅ | Tests graceful error handling |

### Future Pages ⏳

- [ ] Mailbox Page
- [ ] Agentic Teams Page
- [ ] Profile Page
- [ ] Notifications Page
- [ ] Settings Page

## Configuration

### URLs
- **Vanilla Frontend**: `http://localhost:80`
- **Angular Frontend**: `http://localhost:4200`

Update in test files if URLs change.

### Thresholds

Visual comparison allows up to **15% pixel difference** to account for:
- Font rendering differences
- Anti-aliasing variations
- Framework-specific styling

Adjust in `tests/dashboard.spec.js` if needed:
```javascript
expect(comparison.diffPercentage).toBeLessThan(15); // Adjust this value
```

## Troubleshooting

### Servers Not Running
Ensure both frontends are running before testing:
```bash
# Start vanilla frontend (from project root)
docker-compose up frontend

# Start Angular frontend
cd frontend-angular
npm start
# OR
docker-compose up frontend-angular
```

### Port Conflicts
If ports are in use, update test files and docker-compose.yml:
- Vanilla: Port 80 (configurable)
- Angular: Port 4200 (configurable)

### Browser Installation Issues
```bash
# Reinstall browsers
npx playwright install --force --with-deps chromium
```

### Screenshot Differences
High diff percentages can indicate:
1. Styling differences (expected, within threshold)
2. Missing data (data loading issue)
3. Layout problems (needs fixing)
4. Font/rendering differences (usually acceptable)

Check the diff images in `test-results/screenshots/` to diagnose.

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Regression Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd regression-tests && npm install
      - run: npx playwright install --with-deps
      - run: docker-compose up -d frontend frontend-angular backend
      - run: npm test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: regression-tests/test-results/
```

## Development

### Adding New Tests

1. Create new test file in `tests/`:
```javascript
const { test, expect } = require('@playwright/test');

test.describe('My New Page', () => {
  test('should display correctly', async ({ page }) => {
    await page.goto('http://localhost:4200/my-page');
    // ... test logic
  });
});
```

2. Run specific test:
```bash
npx playwright test tests/my-new-page.spec.js
```

### Creating Custom Comparisons

Add to `utils/comparison-helpers.js`:
```javascript
async function compareMyFeature(vanillaPage, angularPage) {
  // Custom comparison logic
  return { match: true, differences: [] };
}
```

## Performance Benchmarks

Tests run with these timeout settings:
- Test timeout: 60 seconds
- Assertion timeout: 10 seconds
- Page load: Wait for networkidle

Average test duration:
- Visual Comparison: ~5-8 seconds
- Data Comparison: ~3-5 seconds
- Responsive Tests: ~10-15 seconds (3 viewports)

## Best Practices

1. **Wait for Data**: Always wait for network idle or specific elements
2. **Consistent Viewports**: Use same viewport sizes for comparison
3. **Stable Selectors**: Use data attributes or stable CSS classes
4. **Isolation**: Each test should be independent
5. **Cleanup**: Close pages and contexts in finally blocks

## Support

For issues or questions:
- Check test output and screenshots
- Review HTML test report
- Inspect browser console in headed mode
- Enable debug mode: `--debug` flag

## License

MIT
