#!/usr/bin/env bash
# Email Security Dashboard - Startup Script
# Handles Docker Compose (plugin version) for WSL2/Linux environments

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

# Check for port conflicts
check_port_conflicts() {
    print_msg "$BLUE" "🔍 Checking for port conflicts..."

    local conflicts=0
    local conflicting_containers=""

    # Check port 5432 (PostgreSQL) - more thorough check
    while read -r container; do
        if [ -n "$container" ] && [ "$container" != "mailbox-postgres" ]; then
            if docker port "$container" 2>/dev/null | grep -q "5432"; then
                print_msg "$YELLOW" "⚠️  Port 5432 (PostgreSQL) is used by: $container"
                conflicting_containers="$conflicting_containers $container"
                conflicts=1
            fi
        fi
    done < <(docker ps --format '{{.Names}}')

    # Check port 8025 (MailPit)
    while read -r container; do
        if [ -n "$container" ] && [ "$container" != "mailbox-mailpit" ]; then
            if docker port "$container" 2>/dev/null | grep -q "0.0.0.0:8025"; then
                print_msg "$YELLOW" "⚠️  Port 8025 (MailPit) is used by: $container"
                conflicting_containers="$conflicting_containers $container"
                conflicts=1
            fi
        fi
    done < <(docker ps --format '{{.Names}}')

    # Check port 80 (Frontend)
    while read -r container; do
        if [ -n "$container" ] && [ "$container" != "mailbox-frontend" ]; then
            if docker port "$container" 2>/dev/null | grep -q "0.0.0.0:80"; then
                print_msg "$YELLOW" "⚠️  Port 80 (Frontend) is used by: $container"
                conflicting_containers="$conflicting_containers $container"
                conflicts=1
            fi
        fi
    done < <(docker ps --format '{{.Names}}')

    # Check port 8000 (Backend API)
    while read -r container; do
        if [ -n "$container" ] && [ "$container" != "mailbox-backend" ]; then
            if docker port "$container" 2>/dev/null | grep -q "0.0.0.0:8000"; then
                print_msg "$YELLOW" "⚠️  Port 8000 (Backend) is used by: $container"
                conflicting_containers="$conflicting_containers $container"
                conflicts=1
            fi
        fi
    done < <(docker ps --format '{{.Names}}')

    if [ $conflicts -eq 1 ]; then
        print_msg "$YELLOW" ""
        print_msg "$YELLOW" "💡 Conflicting containers:$conflicting_containers"
        print_msg "$YELLOW" ""
        print_msg "$YELLOW" "Options:"
        print_msg "$YELLOW" "   1. Stop conflicting containers automatically"
        print_msg "$YELLOW" "   2. Continue anyway (services may fail to start)"
        echo ""
        read -p "Stop conflicting containers? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_conflicting_containers "$conflicting_containers"
        fi
    else
        print_msg "$GREEN" "✅ No port conflicts detected"
    fi
}

# Stop containers using our ports
stop_conflicting_containers() {
    local containers="$1"

    print_msg "$BLUE" "🛑 Stopping conflicting containers..."

    for container in $containers; do
        if [ -n "$container" ]; then
            print_msg "$YELLOW" "   Stopping: $container"
            docker stop "$container" >/dev/null 2>&1
        fi
    done

    print_msg "$GREEN" "✅ Stopped conflicting containers"

    # Wait a moment for ports to be released
    sleep 2
}

# Stop existing mailbox containers if running
stop_existing_containers() {
    print_msg "$BLUE" "🔄 Checking for existing mailbox containers..."

    if docker compose ps --quiet 2>/dev/null | grep -q .; then
        print_msg "$YELLOW" "⏸️  Stopping existing containers..."
        docker compose down
        print_msg "$GREEN" "✅ Stopped existing containers"
    fi
}

# Build images if needed
build_images() {
    print_msg "$BLUE" "🔨 Building Docker images..."
    docker compose build --parallel
    print_msg "$GREEN" "✅ Images built successfully"
}

# Start services
start_services() {
    print_msg "$BLUE" "🚀 Starting services..."

    # Remove version warning by filtering stderr
    docker compose up -d 2>&1 | grep -v "the attribute .version. is obsolete" || true

    print_msg "$GREEN" "✅ Services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_msg "$BLUE" "⏳ Waiting for services to be ready..."

    local max_wait=60
    local elapsed=0

    # Wait for PostgreSQL
    while [ $elapsed -lt $max_wait ]; do
        if docker compose ps postgres | grep -q "healthy"; then
            print_msg "$GREEN" "✅ PostgreSQL is ready"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    if [ $elapsed -ge $max_wait ]; then
        print_msg "$YELLOW" "⚠️  PostgreSQL health check timeout (may still be starting)"
    fi

    # Wait for MailPit
    elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if docker compose ps mailpit | grep -q "healthy"; then
            print_msg "$GREEN" "✅ MailPit is ready"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    # Wait for Backend (no health check, just check if running)
    sleep 5
    if docker compose ps backend | grep -q "Up"; then
        print_msg "$GREEN" "✅ Backend is running"
    else
        print_msg "$YELLOW" "⚠️  Backend may not be running"
    fi

    # Frontend
    if docker compose ps frontend | grep -q "Up"; then
        print_msg "$GREEN" "✅ Frontend is running"
    else
        print_msg "$YELLOW" "⚠️  Frontend may not be running"
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
    echo ""
    print_msg "$BLUE" "📝 Next Steps:"
    print_msg "$YELLOW" "   1. Open http://localhost in your browser"
    print_msg "$YELLOW" "   2. Click 'Fetch Emails from MailPit' to load emails"
    print_msg "$YELLOW" "   3. Click 'Process All Unprocessed' to run phishing detection"
    echo ""
    print_msg "$BLUE" "🔍 Useful Commands:"
    print_msg "$YELLOW" "   View logs:        ./logs.sh"
    print_msg "$YELLOW" "   Stop services:    ./stop.sh"
    print_msg "$YELLOW" "   Restart:          ./start.sh"
    print_msg "$GREEN" "=========================================="
}

# Main execution
main() {
    print_msg "$BLUE" "=========================================="
    print_msg "$BLUE" "📧 Email Security Dashboard - Startup"
    print_msg "$BLUE" "=========================================="
    echo ""

    check_docker
    check_port_conflicts
    stop_existing_containers
    build_images
    start_services
    wait_for_services
    show_status
}

main "$@"
