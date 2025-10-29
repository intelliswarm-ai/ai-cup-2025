# Deployment Guide for Other Machines

## Prerequisites
1. Docker Engine 20.10+
2. Docker Compose plugin v2.0+
3. Linux (Ubuntu 20.04+, Amazon Linux 2, etc.)

## Setup Steps

### 1. Install Docker and Docker Compose Plugin

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# Amazon Linux 2
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose plugin on Amazon Linux 2
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
```

### 2. Configure User Permissions

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout/login or use newgrp)
newgrp docker

# Verify
docker ps
groups | grep docker
```

### 3. Fix Docker Socket Permissions (if needed)

```bash
# Check current permissions
ls -l /var/run/docker.sock

# Should show: srw-rw---- 1 root docker

# If not correct:
sudo chown root:docker /var/run/docker.sock
sudo chmod 660 /var/run/docker.sock
```

### 4. Clone Repository and Set Permissions

```bash
# Clone or copy the project
git clone <your-repo> ai-cup-2025
cd ai-cup-2025

# Make scripts executable (if not already)
chmod +x *.sh

# Fix file ownership if needed
sudo chown -R $USER:$USER .
```

### 5. Handle Volume Mount Permissions

The backend service mounts `./backend:/app` which can cause permission issues.

**Option A: Run without sudo (recommended)**
```bash
# After adding user to docker group
./start.sh
```

**Option B: Fix permissions in docker-compose.yml**
Add user mapping to backend service:
```yaml
backend:
  build:
    context: ./backend
  user: "${UID}:${GID}"  # Add this line
  volumes:
    - ./backend:/app
```

Then run:
```bash
export UID=$(id -u)
export GID=$(id -g)
./start.sh
```

**Option C: Remove development volume mount (production)**
For production deployments, remove the volume mount and build the code into the image:

Edit `docker-compose.yml` backend service:
```yaml
backend:
  build:
    context: ./backend
  # Comment out or remove this line:
  # volumes:
  #   - ./backend:/app
```

### 6. AWS-Specific Considerations

#### Security Groups
Ensure these ports are open in your AWS Security Group:
- 80 (Frontend)
- 8000 (Backend API)
- 8025 (MailPit Web UI)
- 5432 (PostgreSQL) - only if accessing externally

#### Instance Type
Minimum recommended: **t3.medium** (2 vCPU, 4GB RAM)
- Ollama LLM service requires significant memory
- Multiple ML model containers need resources

#### Disk Space
Ensure at least **20GB free space** for:
- Docker images
- Ollama models
- PostgreSQL data
- Application logs

### 7. Start the Application

```bash
# Ensure you're in the project directory
cd ai-cup-2025

# Start all services
./start.sh

# If you get "permission denied" errors:
# 1. Check docker group membership: groups
# 2. Check docker socket: ls -l /var/run/docker.sock
# 3. Try: newgrp docker && ./start.sh
```

### 8. Verify Deployment

```bash
# Check all containers are running
docker compose ps

# Check logs if any issues
./logs.sh

# Test the application
curl http://localhost:8000/health
curl http://localhost:8000/api/stats
```

## Recent Fixes (Applied)

The following issues have been fixed in this deployment:

### 1. Frontend Cannot Find Backend
**Problem:** Nginx failed to start if backend DNS couldn't be resolved at startup time.

**Fix Applied:** Modified `frontend/nginx.conf` to use runtime DNS resolution:
```nginx
location /api/ {
    set $backend_upstream http://backend:8000;
    proxy_pass $backend_upstream;
    # ... other settings
}
```

The `set` directive forces nginx to resolve the backend hostname at request time instead of startup time.

### 2. Backend start.sh Permission Denied
**Problem:** The backend container couldn't execute `start.sh` due to permission issues from volume mounts.

**Fix Applied:** Modified `backend/Dockerfile` to call bash explicitly:
```dockerfile
CMD ["bash", "/app/start.sh"]
```

This doesn't rely on the execute bit, which can be lost when volumes are mounted from different filesystems.

### 3. Backend Health Check
**Added:** Backend now has:
- Health check endpoint at `/health`
- `curl` installed in container
- Docker Compose healthcheck configuration
- Frontend waits for backend to be healthy before starting

## Common Errors and Solutions

### Error: "Cannot connect to the Docker daemon"
```bash
# Check if docker is running
sudo systemctl status docker
sudo systemctl start docker

# Check socket permissions
ls -l /var/run/docker.sock
sudo chmod 666 /var/run/docker.sock  # temporary fix
```

### Error: "Permission denied while trying to connect to Docker daemon socket"
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended for development)
sudo ./start.sh
```

### Error: "Bind for 0.0.0.0:80 failed: port is already allocated"
```bash
# Find what's using port 80
sudo lsof -i :80
sudo netstat -tulpn | grep :80

# Stop the conflicting service
sudo systemctl stop apache2  # if Apache
sudo systemctl stop nginx    # if Nginx

# Or the script will prompt to stop conflicting containers
```

### Error: Backend container exits with "Permission denied" on /app
```bash
# Option 1: Fix ownership
sudo chown -R $USER:$USER ./backend

# Option 2: Run with proper user ID
export UID=$(id -u)
export GID=$(id -g)
docker compose down
docker compose up -d

# Option 3: For production, remove volume mount
# Edit docker-compose.yml and remove: - ./backend:/app
```

### Error: "SQLAlchemy cannot connect to database"
```bash
# Check PostgreSQL container is running and healthy
docker compose ps postgres

# Check logs
docker compose logs postgres

# Verify database is accessible
docker compose exec postgres psql -U mailbox_user -d mailbox_db -c "SELECT 1;"
```

## Production Recommendations

1. **Use Docker Compose production override:**
   ```bash
   # Create docker-compose.prod.yml
   # Remove development volume mounts
   # Add restart policies
   # Configure resource limits
   ```

2. **Set up reverse proxy (nginx/traefik):**
   - SSL/TLS termination
   - Domain routing
   - Load balancing

3. **Configure monitoring:**
   - Container health checks
   - Log aggregation (ELK, CloudWatch)
   - Metrics (Prometheus/Grafana)

4. **Backup strategy:**
   - PostgreSQL regular backups
   - Named volumes backup
   - Configuration files version control

5. **Security hardening:**
   - Non-root user in containers
   - Read-only file systems where possible
   - Network segmentation
   - Secrets management (AWS Secrets Manager, Vault)

## Quick Start Script

Create `deploy.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Setting up AI Cup 2025 Email Security Dashboard..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run as root. Run as regular user with docker group membership."
    exit 1
fi

# Check docker group
if ! groups | grep -q docker; then
    echo "❌ Current user not in docker group"
    echo "Run: sudo usermod -aG docker $USER && newgrp docker"
    exit 1
fi

# Check docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Cannot connect to Docker daemon"
    echo "Is Docker running? Try: sudo systemctl start docker"
    exit 1
fi

# Set permissions
chmod +x *.sh

# Fix ownership
sudo chown -R $USER:$USER .

# Start application
./start.sh
```

Then:
```bash
chmod +x deploy.sh
./deploy.sh
```
