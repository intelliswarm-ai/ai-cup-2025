#!/usr/bin/env bash
# Email Security Dashboard - Logs Viewer
# View container logs easily

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
FOLLOW=false
SERVICE=""

show_help() {
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "View logs for Email Security Dashboard services"
    echo ""
    echo "Services:"
    echo "  postgres       PostgreSQL database"
    echo "  backend        Python FastAPI backend"
    echo "  frontend       Material Dashboard frontend"
    echo "  mailpit        MailPit mail server"
    echo "  email-seeder   Email generation seeder"
    echo ""
    echo "Options:"
    echo "  -f, --follow   Follow log output (like tail -f)"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Show all logs"
    echo "  $0 -f             # Follow all logs"
    echo "  $0 backend        # Show backend logs only"
    echo "  $0 -f backend     # Follow backend logs"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        postgres|backend|frontend|mailpit|email-seeder)
            SERVICE=$1
            shift
            ;;
        *)
            print_msg "$RED" "Unknown option or service: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
main() {
    # Check if any containers are running
    if ! docker compose ps --quiet 2>/dev/null | grep -q .; then
        print_msg "$YELLOW" "ℹ️  No containers are currently running"
        print_msg "$BLUE" "💡 Start the application with: ./start.sh"
        exit 0
    fi

    print_msg "$BLUE" "=========================================="
    if [ -n "$SERVICE" ]; then
        print_msg "$BLUE" "📋 Logs for: $SERVICE"
    else
        print_msg "$BLUE" "📋 Logs for: All Services"
    fi
    print_msg "$BLUE" "=========================================="
    echo ""

    # Build docker compose logs command
    CMD="docker compose logs"

    if [ "$FOLLOW" = true ]; then
        CMD="$CMD --follow"
    fi

    if [ -n "$SERVICE" ]; then
        CMD="$CMD $SERVICE"
    fi

    # Execute
    eval "$CMD" 2>&1 | grep -v "the attribute .version. is obsolete" || true
}

main "$@"
