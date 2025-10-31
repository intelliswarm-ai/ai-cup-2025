#!/usr/bin/env bash
# Helper script to stop all running Docker containers from other projects
# Run this before starting ai-cup-2025 to ensure clean state
#
# Usage:
#   ./stop-other-projects.sh       # Stop all containers except mailbox-*
#   ./stop-other-projects.sh --all # Stop ALL containers including mailbox-*

set -euo pipefail

# Parse arguments
STOP_ALL=false
if [ $# -gt 0 ] && [ "$1" == "--all" ]; then
    STOP_ALL=true
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

if [ "$STOP_ALL" = true ]; then
    print_msg "$BLUE" "🔍 Finding ALL running Docker containers..."
else
    print_msg "$BLUE" "🔍 Finding all running Docker containers (excluding mailbox-*)..."
fi
echo ""

# Get all running containers (excluding mailbox containers unless --all flag is used)
if [ "$STOP_ALL" = true ]; then
    CONTAINERS=$(docker ps --format '{{.Names}}' || true)
else
    CONTAINERS=$(docker ps --format '{{.Names}}' | grep -v '^mailbox-' || true)
fi

if [ -z "$CONTAINERS" ]; then
    print_msg "$GREEN" "✅ No other containers running"
    exit 0
fi

# Display container information
print_msg "$YELLOW" "Found running containers:"
echo ""

while read -r container; do
    if [ -n "$container" ]; then
        print_msg "$YELLOW" "📦 $container"
        # Show image and status
        docker ps --filter "name=$container" --format "   Image: {{.Image}}" || true
        docker ps --filter "name=$container" --format "   Status: {{.Status}}" || true
        # Show port mappings
        port_output=$(docker port "$container" 2>/dev/null || true)
        if [ -n "$port_output" ]; then
            echo "$port_output" | sed 's/^/   Port: /'
        fi
        echo ""
    fi
done <<< "$CONTAINERS"

# Count containers
CONTAINER_COUNT=$(echo "$CONTAINERS" | wc -l)
print_msg "$YELLOW" "Total: $CONTAINER_COUNT container(s)"
echo ""

# Ask for confirmation
read -p "Stop all these containers? (y/N): " -n 1 -r
echo
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_msg "$BLUE" "❌ Cancelled - no containers stopped"
    exit 0
fi

# Stop all containers
print_msg "$BLUE" "🛑 Stopping all containers..."
echo ""

while read -r container; do
    if [ -n "$container" ]; then
        print_msg "$YELLOW" "   Stopping: $container"
        if docker stop "$container" >/dev/null 2>&1; then
            print_msg "$GREEN" "      ✓ Stopped"
        else
            print_msg "$RED" "      ✗ Failed to stop"
        fi
    fi
done <<< "$CONTAINERS"

echo ""
if [ "$STOP_ALL" = true ]; then
    print_msg "$GREEN" "✅ Done! All containers have been stopped."
    print_msg "$BLUE" "💡 You can now run: docker compose up -d"
else
    print_msg "$GREEN" "✅ Done! All non-mailbox containers have been stopped."
    print_msg "$BLUE" "💡 You can now run: docker compose up -d"
    print_msg "$YELLOW" "💡 To stop mailbox containers too, use: ./stop-other-projects.sh --all"
fi
