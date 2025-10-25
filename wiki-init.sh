#!/bin/bash
#
# OtterWiki Initialization Script
# Automatically generates and populates comprehensive wiki knowledge base
# Runs on container startup
#

set -e

WIKI_DATA_DIR="${WIKI_DATA_DIR:-/app/data}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "================================================================"
echo "  OTTERWIKI KNOWLEDGE BASE INITIALIZATION"
echo "================================================================"
echo ""
echo "Wiki data directory: $WIKI_DATA_DIR"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Create data directory if it doesn't exist
mkdir -p "$WIKI_DATA_DIR"

# Check if wiki pages already exist
EXISTING_PAGES=$(find "$WIKI_DATA_DIR" -name "*.md" 2>/dev/null | wc -l)

if [ "$EXISTING_PAGES" -ge 500 ]; then
    echo "✓ Wiki already initialized with $EXISTING_PAGES pages"
    echo "  Skipping regeneration"
    echo ""
    echo "================================================================"
    exit 0
fi

echo "📝 Generating comprehensive wiki knowledge base..."
echo "  Target: 500+ pages covering all business topics"
echo ""

# Generate wiki pages
export WIKI_DIR="$WIKI_DATA_DIR"
python3 "$SCRIPT_DIR/generate_wiki_pages.py"

if [ $? -eq 0 ]; then
    TOTAL_PAGES=$(find "$WIKI_DATA_DIR" -name "*.md" 2>/dev/null | wc -l)
    echo ""
    echo "================================================================"
    echo "✓ WIKI INITIALIZATION COMPLETE!"
    echo "================================================================"
    echo ""
    echo "  Total wiki pages: $TOTAL_PAGES"
    echo "  Data directory: $WIKI_DATA_DIR"
    echo ""
    echo "Knowledge base coverage:"
    echo "  • Confirmations (meetings, registrations, bookings)"
    echo "  • Reviews (performance, code, quarterly, audits)"
    echo "  • Documentation (technical, project, processes)"
    echo "  • Status Reports (weekly, monthly, project updates)"
    echo "  • Training (onboarding, technical, compliance)"
    echo ""
    echo "All email topics are now covered for enrichment!"
    echo "================================================================"
    echo ""
else
    echo ""
    echo "================================================================"
    echo "⚠ WARNING: Wiki generation encountered errors"
    echo "================================================================"
    echo ""
    exit 1
fi
