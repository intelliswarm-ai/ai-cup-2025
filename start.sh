#!/usr/bin/env bash
# Email Security Dashboard - Start Script
# Starts existing containers (preserves data)
# For clean installation, use: ./clean-start.sh

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

# Check if docker compose is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_msg "$RED" "❌ Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        print_msg "$RED" "❌ Docker Compose plugin not available"
        print_msg "$YELLOW" "💡 Install it with: sudo apt-get install docker-compose-plugin"
        exit 1
    fi

    print_msg "$GREEN" "✅ Docker Compose version: $(docker compose version --short)"
}

# Check if images exist
check_images() {
    if ! docker images | grep -q "ai-cup-2025-backend"; then
        print_msg "$YELLOW" "⚠️  Images not found. Running first-time build..."
        print_msg "$BLUE" "🔨 Building Docker images..."
        docker compose build --parallel
        print_msg "$GREEN" "✅ Images built successfully"
        return 0
    fi
    print_msg "$GREEN" "✅ Images already exist"
}

# Start services
start_services() {
    print_msg "$BLUE" "🚀 Starting services..."

    # Remove version warning by filtering stderr
    docker compose up -d 2>&1 | grep -v "the attribute .version. is obsolete" || true

    print_msg "$GREEN" "✅ Services started"
}

# Wait for key services
wait_for_services() {
    print_msg "$BLUE" "⏳ Waiting for key services to be ready..."

    local max_wait=60
    local elapsed=0

    # Wait for PostgreSQL
    while [ $elapsed -lt $max_wait ]; do
        if docker compose ps postgres 2>/dev/null | grep -q "healthy"; then
            print_msg "$GREEN" "✅ PostgreSQL is ready"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    if [ $elapsed -ge $max_wait ]; then
        print_msg "$YELLOW" "⚠️  PostgreSQL health check timeout (may still be starting)"
    fi

    # Wait for Backend
    elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if docker compose ps backend 2>/dev/null | grep -q "healthy"; then
            print_msg "$GREEN" "✅ Backend is ready"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    if [ $elapsed -ge $max_wait ]; then
        print_msg "$YELLOW" "⚠️  Backend health check timeout (may still be starting)"
    fi
}

# Display service status and URLs
show_status() {
    echo ""
    print_msg "$GREEN" "=========================================="
    print_msg "$GREEN" "🎉 Email Security Dashboard Started!"
    print_msg "$GREEN" "=========================================="
    echo ""
    print_msg "$BLUE" "📊 Service Status:"
    docker compose ps
    echo ""
    print_msg "$BLUE" "🌐 Access URLs:"
    print_msg "$GREEN" "   📧 Email Dashboard:    http://localhost"
    print_msg "$GREEN" "   📬 MailPit Web UI:     http://localhost:8025"
    print_msg "$GREEN" "   🔧 Backend API:        http://localhost:8000"
    print_msg "$GREEN" "   📚 API Documentation:  http://localhost:8000/docs"
    print_msg "$GREEN" "   📖 OtterWiki:          http://localhost:9000"
    echo ""
    print_msg "$BLUE" "📝 Useful Commands:"
    print_msg "$YELLOW" "   View logs:        docker compose logs -f [service]"
    print_msg "$YELLOW" "   Stop services:    ./stop.sh"
    print_msg "$YELLOW" "   Clean rebuild:    ./clean-start.sh"
    print_msg "$GREEN" "=========================================="
}

# Main execution
main() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "📧 Email Security Dashboard - Start"
    print_msg "$BLUE" "=========================================="
    echo ""

    check_docker
    check_images
    start_services
    wait_for_services
    show_status
}

main "$@"
