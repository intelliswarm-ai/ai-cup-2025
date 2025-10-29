#!/bin/bash
# Quick deployment script for other machines/AWS
set -e

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
print_msg "$BLUE" "🚀 AI Cup 2025 - Deployment Setup"
print_msg "$BLUE" "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_msg "$RED" "❌ Don't run this script as root!"
    print_msg "$YELLOW" "💡 Run as regular user with docker group membership"
    print_msg "$YELLOW" "   If needed: sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fi

# Check docker group membership
print_msg "$BLUE" "🔍 Checking Docker permissions..."
if ! groups | grep -q docker; then
    print_msg "$RED" "❌ Current user '$USER' is not in docker group"
    echo ""
    print_msg "$YELLOW" "Fix this with:"
    print_msg "$YELLOW" "   sudo usermod -aG docker $USER"
    print_msg "$YELLOW" "   newgrp docker"
    print_msg "$YELLOW" ""
    print_msg "$YELLOW" "Or logout and login again, then re-run this script"
    exit 1
else
    print_msg "$GREEN" "✅ User is in docker group"
fi

# Check docker daemon
print_msg "$BLUE" "🔍 Checking Docker daemon..."
if ! docker ps &> /dev/null; then
    print_msg "$RED" "❌ Cannot connect to Docker daemon"
    echo ""
    print_msg "$YELLOW" "Possible fixes:"
    print_msg "$YELLOW" "   1. Start Docker: sudo systemctl start docker"
    print_msg "$YELLOW" "   2. Check socket: ls -l /var/run/docker.sock"
    print_msg "$YELLOW" "   3. Fix permissions: sudo chmod 666 /var/run/docker.sock"
    exit 1
else
    print_msg "$GREEN" "✅ Docker daemon is running"
    docker --version
fi

# Check docker compose
print_msg "$BLUE" "🔍 Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    print_msg "$RED" "❌ Docker Compose plugin not found"
    echo ""
    print_msg "$YELLOW" "Install Docker Compose plugin:"
    print_msg "$YELLOW" "   Ubuntu/Debian: sudo apt-get install docker-compose-plugin"
    print_msg "$YELLOW" "   Or manually: https://docs.docker.com/compose/install/"
    exit 1
else
    print_msg "$GREEN" "✅ Docker Compose is available"
    docker compose version
fi

# Make scripts executable
print_msg "$BLUE" "🔧 Setting up scripts..."
chmod +x *.sh 2>/dev/null || true
print_msg "$GREEN" "✅ Scripts are executable"

# Check disk space
print_msg "$BLUE" "🔍 Checking disk space..."
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    print_msg "$YELLOW" "⚠️  Warning: Low disk space (${AVAILABLE_SPACE}GB available)"
    print_msg "$YELLOW" "   Recommended: 20GB+ for Docker images and data"
else
    print_msg "$GREEN" "✅ Sufficient disk space (${AVAILABLE_SPACE}GB available)"
fi

# Fix ownership (only if needed and possible without sudo)
print_msg "$BLUE" "🔧 Checking file ownership..."
OWNER=$(stat -c '%U' .)
if [ "$OWNER" != "$USER" ]; then
    print_msg "$YELLOW" "⚠️  Directory owner is '$OWNER', not '$USER'"
    print_msg "$YELLOW" "   You may need to run: sudo chown -R $USER:$USER ."
    read -p "Try to fix with sudo? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo chown -R $USER:$USER .
        print_msg "$GREEN" "✅ Ownership fixed"
    fi
else
    print_msg "$GREEN" "✅ Correct file ownership"
fi

# All checks passed
echo ""
print_msg "$GREEN" "=========================================="
print_msg "$GREEN" "✅ All pre-deployment checks passed!"
print_msg "$GREEN" "=========================================="
echo ""

# Ask to start
read -p "Start the application now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_msg "$BLUE" "🚀 Starting application..."
    echo ""
    ./start.sh
else
    echo ""
    print_msg "$BLUE" "To start manually, run: ./start.sh"
    print_msg "$BLUE" "=========================================="
fi
