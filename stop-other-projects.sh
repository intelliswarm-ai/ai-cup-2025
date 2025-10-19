#!/usr/bin/env bash
# Helper script to stop containers from other projects
# Run this before starting ai-cup-2025 if you have port conflicts

set -euo pipefail

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

print_msg "$BLUE" "🔍 Finding what's using ports 80, 5432, 8000, 8025..."
echo ""

# Check for system-level services
print_msg "$YELLOW" "Checking system services..."
if sudo lsof -i :5432 >/dev/null 2>&1; then
    print_msg "$YELLOW" "⚠️  Port 5432 is in use by:"
    sudo lsof -i :5432 | grep LISTEN || true
fi

if sudo lsof -i :80 >/dev/null 2>&1; then
    print_msg "$YELLOW" "⚠️  Port 80 is in use by:"
    sudo lsof -i :80 | grep LISTEN || true
fi
echo ""

# Find all containers using our ports (excluding mailbox containers)
CONTAINERS=""

while read -r container; do
    if [[ ! "$container" =~ ^mailbox- ]]; then
        # Check all port mappings for this container
        port_output=$(docker port "$container" 2>/dev/null || true)
        if echo "$port_output" | grep -qE "0\.0\.0\.0:(80|5432|8000|8025)"; then
            print_msg "$YELLOW" "📦 $container"
            echo "$port_output" | grep -E "0\.0\.0\.0:(80|5432|8000|8025)" | sed 's/^/   /'
            CONTAINERS="$CONTAINERS $container"
        fi
    fi
done < <(docker ps --format '{{.Names}}')

if [ -z "$CONTAINERS" ]; then
    print_msg "$GREEN" "✅ No conflicting containers found"
    exit 0
fi

echo ""
print_msg "$YELLOW" "Found containers:$CONTAINERS"
echo ""
read -p "Stop these containers? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_msg "$BLUE" "Cancelled"
    exit 0
fi

print_msg "$BLUE" "🛑 Stopping containers..."
for container in $CONTAINERS; do
    print_msg "$YELLOW" "   Stopping: $container"
    docker stop "$container" >/dev/null 2>&1
done

print_msg "$GREEN" "✅ Done! You can now run ./start.sh"
