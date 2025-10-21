# Email Dashboard - AI Cup 2025

A multi-container Docker application for analyzing and detecting phishing emails using multiple agentic workflows.

## Architecture

The application consists of 5 main components:

1. **Frontend** - Material Dashboard (Angular-style template) for visualizing emails and analysis results
2. **Backend** - Python FastAPI service with multiple phishing detection workflows
3. **PostgreSQL** - Database for storing emails and analysis results
4. **MailPit** - Local mail server pre-seeded with 10,000 real-world emails from Kaggle phishing dataset
5. **Ollama** - Local LLM service (Phi3 model) for AI-powered email analysis

## Features

- **Email Collection**: Fetch emails from MailPit SMTP server
- **Multi-Workflow Analysis**: Three independent phishing detection workflows:
  - URL Analysis: Detects suspicious URLs, IP addresses, and URL shorteners
  - Sender Analysis: Identifies spoofing attempts and suspicious sender patterns
  - Content Analysis: Analyzes email content for phishing language patterns
- **AI-Powered Email Processing** (NEW):
  - LLM-generated email summaries
  - Automatic call-to-action (CTA) extraction
  - Smart email categorization with 8 badge types
  - 3 quick reply drafts (formal, friendly, brief) for each email
- **Daily Inbox Digest** (NEW): Organized view of emails grouped by category
- **Email Badges** (NEW): Visual categorization with icons
  - MEETING - Calendar events and scheduling
  - RISK - Phishing/security threats
  - EXTERNAL - Emails from external sources
  - AUTOMATED - Auto-generated notifications
  - VIP - Important contacts
  - FOLLOW_UP - Requires action or response
  - NEWSLETTER - Marketing/bulk emails
  - FINANCE - Financial transactions
- **Quick Reply Drafts** (NEW): AI-generated reply suggestions in 3 tones
- **Real-time Dashboard**: Interactive UI showing email status and analysis results
- **Statistics**: Overview of total emails, phishing detected, and processing status
- **Database Migrations**: Liquibase-managed schema versioning

## Quick Start

### Prerequisites

- Docker and Docker Compose plugin installed
- At least 4GB of available RAM
- Ports 80, 1025, 5432, 8000, 8025 available

### Running the Application

**Option 1: Using the startup script (Recommended)**

```bash
cd ai-cup-2025
./start.sh
```

The script will:
- Check for Docker availability
- Detect and handle port conflicts
- Build images if needed
- Start all services in the correct order
- Display access URLs when ready

**Option 2: Manual startup**

```bash
cd ai-cup-2025
docker compose up -d
```

### Using the Dashboard

1. Open http://localhost in your browser
2. Click "Fetch Emails from MailPit" to load all 10,000 dataset emails
3. Click "Run Analysis" on any email to run phishing detection workflows and LLM processing
4. View email details, workflow results, summaries, badges, and quick reply drafts
5. Navigate to "Daily Inbox Digest" to see emails organized by category

### Access URLs

Once started, access the following:
- **Email Dashboard**: http://localhost (main application)
- **Daily Inbox Digest**: http://localhost/pages/inbox-digest.html (NEW - categorized email view)
- **Mailbox**: http://localhost/pages/mailbox.html (detailed email view with quick replies)
- **MailPit Web UI**: http://localhost:8025 (view raw emails)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Management Scripts

The project includes convenient bash scripts for managing the application:

### start.sh - Start Application
```bash
./start.sh
```
- Checks for Docker and port conflicts
- Builds images if needed
- Starts all services
- Displays status and access URLs

### stop.sh - Stop Application
```bash
./stop.sh              # Stop containers only
./stop.sh -v           # Stop and remove volumes (deletes data)
./stop.sh -i           # Stop and remove images (requires rebuild)
./stop.sh -a           # Stop and remove everything
```

### logs.sh - View Logs
```bash
./logs.sh              # Show all logs
./logs.sh -f           # Follow all logs (live)
./logs.sh backend      # Show backend logs only
./logs.sh -f backend   # Follow backend logs
```

Available services: `postgres`, `backend`, `frontend`, `mailpit`, `email-seeder`

## Services

### Frontend (Port 80)
- Material Dashboard template
- Interactive email list and detail views
- Real-time statistics
- Workflow result visualization

### Backend API (Port 8000)
**Key Endpoints:**
- `GET /api/emails` - List all emails (includes badges, summaries, quick replies)
- `GET /api/emails/{id}` - Get email details with workflow results
- `POST /api/emails/fetch` - Fetch new emails from MailPit
- `POST /api/emails/{id}/process` - Run workflows on a single email
- `POST /api/emails/process-all` - Process all unprocessed emails
- `POST /api/emails/{id}/process-llm` - Generate summary, CTAs, badges, and quick replies
- `POST /api/emails/process-all-llm` - Process all emails with LLM in background 
- `GET /api/inbox-digest?hours=24` - Get emails grouped by badges 
- `GET /api/daily-summary?hours=24` - Get aggregated email summary 
- `GET /api/statistics` - Get overall statistics (includes badge counts)
- `GET /api/workflows` - List available workflows

### Database (Port 5432)
PostgreSQL database with tables:
- `emails` - Stores email metadata, content, summaries, badges, and quick reply drafts
- `workflow_results` - Stores analysis results from each workflow
- `workflow_configs` - Workflow configurations

**Database Migrations:**
- Managed by Liquibase
- Automatic migration on backend startup
- Changelog files in `backend/db/changelog/`

### MailPit (Port 8025)
- SMTP server on port 1025
- Web interface on port 8025
- Pre-seeded with 10,000 emails from Kaggle phishing dataset (6,000 phishing, 4,000 legitimate)

### Ollama LLM Service (NEW)
- Local LLM inference using Phi3 model
- Automatic model download on first startup
- Used for email summarization, CTA extraction, badge detection, and quick reply generation

## Email Dataset

The application uses a real-world phishing dataset for training and testing:

**Dataset Source:**
- **Phishing and Legitimate Emails Dataset** by Kuladeep19
- Available on Kaggle: https://www.kaggle.com/datasets/kuladeep19/phishing-and-legitimate-emails-dataset
- Contains 10,000 emails with ground truth labels

**Dataset Fields:**
- `label`: Target variable (1 = phishing, 0 = legitimate)
- `phishing_type`: Specific categories including:
  - `credential_harvesting` - Attempts to steal credentials
  - `authority_scam` - Impersonating authority figures
  - `romance_dating` - Romance/dating scams
  - `financial` - Financial fraud attempts
  - `legitimate` - Genuine emails
- `text`: Full email content including subject and body
- `severity`: Risk level (low, medium, high)
- `confidence`: Classification confidence (0.0-1.0)

**Email Seeder:**
- Loads emails from CSV dataset at startup
- Sends all 10,000 emails to MailPit by default (configurable via `NUM_EMAILS`)
- Preserves ground truth labels in custom email headers:
  - `X-Email-Label`: Original label (1=phishing, 0=legitimate)
  - `X-Phishing-Type`: Phishing category
- Generates contextual sender addresses based on phishing type
- Distribution: 60% phishing, 40% legitimate

## Phishing Detection Workflows

### 1. URL Analysis Workflow
Detects:
- Suspicious domains (bit.ly, tinyurl, etc.)
- IP addresses used instead of domain names
- URL shorteners
- Banking-related phishing domains

### 2. Sender Analysis Workflow
Detects:
- Email spoofing attempts
- Generic no-reply addresses
- Suspicious numbers in domains
- Mismatched sender domains

### 3. Content Analysis Workflow
Detects:
- Urgency language (urgent, immediately, etc.)
- Requests for sensitive information (password, SSN, etc.)
- Generic greetings instead of personalized
- Multiple urgency keywords

## Development

### Project Structure
```
.
├── docker-compose.yml          # Service orchestration
├── frontend/                   # Material Dashboard
│   ├── Dockerfile
│   ├── nginx.conf
│   └── pages/
│       └── mailbox.html       # Main dashboard page
├── backend/                    # Python FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py               # API endpoints
│   ├── models.py             # Database models
│   ├── database.py           # DB connection
│   ├── mailpit_client.py     # MailPit integration
│   └── workflows.py          # Phishing detection logic
├── email-seeder/              # Email generation
│   ├── Dockerfile
│   ├── seed_emails.py        # Main seeding script
│   └── email_templates.py    # Email templates
└── postgres/
    └── init.sql              # Database initialization
```

### Stopping the Application

**Using stop script (Recommended):**
```bash
./stop.sh              # Stop containers
./stop.sh -v           # Stop and remove data
```

**Manual:**
```bash
docker compose down         # Stop containers
docker compose down -v      # Stop and remove data
```

### Viewing Logs

**Using logs script (Recommended):**
```bash
./logs.sh              # All logs
./logs.sh -f           # Follow all logs
./logs.sh backend      # Backend logs only
```

**Manual:**
```bash
docker compose logs -f              # All services
docker compose logs -f backend      # Specific service
```

## API Examples

### Fetch emails from MailPit
```bash
curl -X POST http://localhost:8000/api/emails/fetch
```

### Get all emails
```bash
curl http://localhost:8000/api/emails
```

### Process a single email
```bash
curl -X POST http://localhost:8000/api/emails/1/process
```

### Get statistics
```bash
curl http://localhost:8000/api/statistics
```

## Troubleshooting

### Port Conflicts

If you see errors like "port is already allocated":

**Quick Fix:**
```bash
# Stop conflicting containers
docker stop <container-name>

# Or stop all containers
docker stop $(docker ps -q)

# Then restart
./start.sh
```

**Common port conflicts:**
- Port 5432 (PostgreSQL): Often used by other database containers
- Port 8025 (MailPit): May conflict with GreenMail or other mail servers
- Port 80 (Frontend): May conflict with nginx or other web servers

The `start.sh` script will automatically detect and offer to stop conflicting containers.

### Service Issues

**Emails not appearing:**
- Check if email-seeder completed: `./logs.sh email-seeder`
- Wait 30 seconds after startup for emails to be sent
- Click "Fetch Emails from MailPit" in the dashboard

**Analysis not working:**
- Ensure backend is running: `docker compose ps`
- Check backend logs: `./logs.sh backend`
- Verify database connection: `docker compose ps postgres`

**Frontend not loading:**
- Check if port 80 is available: `./start.sh` (automatic check)
- View nginx logs: `./logs.sh frontend`
- Verify nginx container is running: `docker compose ps frontend`

**Database connection errors:**
- Ensure PostgreSQL is healthy: `docker compose ps postgres`
- Check database logs: `./logs.sh postgres`
- Verify no other PostgreSQL is using port 5432

### WSL2 Specific Issues

**Docker Compose not found:**
```bash
# Install Docker Desktop for Windows and enable WSL2 integration
# Or install docker-compose-plugin:
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

**Permission errors:**
```bash
# Make scripts executable
chmod +x start.sh stop.sh logs.sh
```

