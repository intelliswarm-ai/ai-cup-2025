#!/bin/bash

echo "🔧 Setting up Visual Regression Testing Environment..."
echo ""

# Check if running on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Installing Playwright browser dependencies..."
    echo "This requires sudo privileges."
    echo ""

    # Option 1: Use Playwright's installer
    sudo npx playwright install-deps

    # Install Chromium browser
    echo ""
    echo "🌐 Installing Chromium browser..."
    npx playwright install chromium

    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "You can now run: npm run test:visual"
else
    echo "⚠️  Auto-installation is only available on Linux."
    echo "Please install Playwright manually:"
    echo "  npx playwright install chromium"
    echo ""
    echo "Then run: npm run test:visual"
fi
