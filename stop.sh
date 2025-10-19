#!/usr/bin/env bash
# Email Security Dashboard - Stop Script
# Gracefully stops all services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Parse arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -i|--images)
            REMOVE_IMAGES=true
            shift
            ;;
        -a|--all)
            REMOVE_VOLUMES=true
            REMOVE_IMAGES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove volumes (deletes all data)"
            echo "  -i, --images     Remove images (requires rebuild)"
            echo "  -a, --all        Remove everything (volumes + images)"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Stop containers only"
            echo "  $0 -v           # Stop and remove volumes"
            echo "  $0 -a           # Stop and remove everything"
            exit 0
            ;;
        *)
            print_msg "$RED" "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "🛑 Stopping Email Security Dashboard"
    print_msg "$BLUE" "=========================================="
    echo ""

    # Check if any containers are running
    if ! docker compose ps --quiet 2>/dev/null | grep -q .; then
        print_msg "$YELLOW" "ℹ️  No containers are currently running"
        exit 0
    fi

    # Show current status
    print_msg "$BLUE" "📊 Current Status:"
    docker compose ps
    echo ""

    # Stop containers
    print_msg "$BLUE" "🛑 Stopping containers..."
    docker compose down 2>&1 | grep -v "the attribute .version. is obsolete" || true
    print_msg "$GREEN" "✅ Containers stopped"

    # Remove volumes if requested
    if [ "$REMOVE_VOLUMES" = true ]; then
        echo ""
        print_msg "$YELLOW" "⚠️  WARNING: This will delete all data (emails, database, etc.)"
        read -p "Are you sure you want to remove volumes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_msg "$BLUE" "🗑️  Removing volumes..."
            docker compose down -v 2>&1 | grep -v "the attribute .version. is obsolete" || true
            print_msg "$GREEN" "✅ Volumes removed"
        else
            print_msg "$YELLOW" "ℹ️  Skipped volume removal"
        fi
    fi

    # Remove images if requested
    if [ "$REMOVE_IMAGES" = true ]; then
        echo ""
        print_msg "$YELLOW" "⚠️  WARNING: This will remove images (requires rebuild)"
        read -p "Are you sure you want to remove images? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_msg "$BLUE" "🗑️  Removing images..."
            docker compose down --rmi all 2>&1 | grep -v "the attribute .version. is obsolete" || true
            print_msg "$GREEN" "✅ Images removed"
        else
            print_msg "$YELLOW" "ℹ️  Skipped image removal"
        fi
    fi

    echo ""
    print_msg "$GREEN" "=========================================="
    print_msg "$GREEN" "✅ Email Security Dashboard Stopped"
    print_msg "$GREEN" "=========================================="
    echo ""

    if [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_IMAGES" = true ]; then
        print_msg "$BLUE" "💡 To start fresh, run: ./start.sh"
    else
        print_msg "$BLUE" "💡 To restart, run: ./start.sh"
        print_msg "$YELLOW" "   Data is preserved and will be available when you restart"
    fi
}

main "$@"
