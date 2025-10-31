#!/usr/bin/env bash
# Diagnostic script to check what's using required ports

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

print_msg "$BLUE" "=========================================="
print_msg "$BLUE" "🔍 Port Usage Diagnostic"
print_msg "$BLUE" "=========================================="
echo ""

PORTS=(80 5432 8000 8025 1025)

for port in "${PORTS[@]}"; do
    print_msg "$YELLOW" "Checking port $port..."

    # Check with lsof (system level)
    if command -v lsof >/dev/null 2>&1; then
        if sudo lsof -i :$port 2>/dev/null | grep -q LISTEN; then
            print_msg "$RED" "⚠️  Port $port is in use (system level):"
            sudo lsof -i :$port | grep LISTEN | awk '{print "   "$1, $2, $9}'
        fi
    fi

    # Check Docker containers
    while read -r container; do
        if docker port "$container" 2>/dev/null | grep -q "0.0.0.0:$port"; then
            print_msg "$YELLOW" "📦 Port $port used by Docker container: $container"
            docker port "$container" | grep ":$port" | sed 's/^/   /'
        fi
    done < <(docker ps --format '{{.Names}}')

    echo ""
done

print_msg "$BLUE" "=========================================="
print_msg "$BLUE" "📊 All Running Docker Containers:"
print_msg "$BLUE" "=========================================="
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}" | head -20

echo ""
print_msg "$BLUE" "=========================================="
print_msg "$GREEN" "✅ Diagnostic complete"
print_msg "$BLUE" "=========================================="
