#!/bin/bash
#
# OtterWiki Auto-Initialization Script
# Automatically populates wiki on first startup
#

set -e

echo "🦦 OtterWiki Auto-Init: Starting..."

# Wait for OtterWiki to be fully started
sleep 5

# Always ensure RETAIN_PAGE_NAME_CASE setting is present
echo "⚙️  Ensuring OtterWiki settings are correct..."
if ! grep -q "RETAIN_PAGE_NAME_CASE" /app-data/settings.cfg 2>/dev/null; then
    echo "RETAIN_PAGE_NAME_CASE = True" >> /app-data/settings.cfg
    echo "✓ Added RETAIN_PAGE_NAME_CASE setting"
fi

# Check if wiki already has content (more than just home.md)
PAGE_COUNT=$(ls /app-data/repository/*.md 2>/dev/null | wc -l)

if [ "$PAGE_COUNT" -gt 10 ]; then
    echo "✓ Wiki already populated with $PAGE_COUNT pages - skipping wiki page generation"
    exit 0
fi

echo "📝 Initializing wiki knowledge base..."

# Run the wiki initialization script
export WIKI_DIR="/app/data"
bash /docker-entrypoint-initdb.d/wiki-init.sh

# Copy generated pages to OtterWiki repository
echo "📋 Copying pages to OtterWiki repository..."
cp /app/data/*.md /app-data/repository/ 2>/dev/null || true

# Commit to git repository
echo "💾 Committing to git repository..."
cd /app-data/repository

git config --global --add safe.directory /app-data/repository
git config user.name "Wiki Admin"
git config user.email "admin@intelliswarm.ai"
git add *.md
git commit -m "Auto-initialize: Add comprehensive wiki knowledge base" || true

FINAL_COUNT=$(ls /app-data/repository/*.md 2>/dev/null | wc -l)
echo "✅ Wiki initialization complete! Total pages: $FINAL_COUNT"
