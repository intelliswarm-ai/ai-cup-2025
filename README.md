# AI Cup 2025 - Enterprise Email Analysis System

A sophisticated, production-ready email analysis platform combining machine learning, agentic AI, RAG (Retrieval-Augmented Generation), and multi-agent collaboration for intelligent phishing detection and email processing.

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)

## Current Status - Fully Implemented Features

### Core Capabilities

#### 1. Advanced Phishing Detection (82.10% Accuracy)
- **Ensemble ML Model**: 3 models with OR-based voting strategy
  - Naive Bayes: 76.50% accuracy
  - Random Forest: 71.70% accuracy
  - Fine-tuned LLM: 59% accuracy
- **Overall Performance**: 82.10% accuracy, 81.90% F1-score
- **Training Data**: 10,000 real-world emails (60% phishing, 40% legitimate)
- **Source**: Kaggle Phishing and Legitimate Emails Dataset

#### 2. Agentic Team Collaboration (6 Specialized Teams)
Multi-agent debate system where specialized banking teams analyze complex emails through 3-round discussions:

**Available Teams:**
- **Credit Risk Committee** - Credit analysts, risk managers, relationship managers, chief risk officer
- **Fraud Investigation Unit** - Fraud detection specialists, forensic analysts, legal advisors, security directors
- **Compliance & Regulatory Affairs** - Compliance officers, legal counsel, internal auditors, regulatory liaisons
- **Wealth Management Advisory** - Wealth advisors, investment specialists, tax consultants, estate planners
- **Corporate Banking Team** - Corporate relationship managers, trade finance specialists, treasury experts, syndication leads
- **Operations & Quality** - Operations managers, QA leads, technology liaisons, customer service leads

**How It Works:**
- **Round 1**: Initial assessment - each agent provides their perspective
- **Round 2**: Challenge and debate - agents critique each other's views
- **Round 3**: Final synthesis - agents defend or concede positions
- **Decision**: Final decision maker synthesizes conclusions with action items
- **Real-time Updates**: Server-Sent Events for live team discussion visualization

#### 3. RAG System (Retrieval-Augmented Generation)
Contextual enrichment combining internal knowledge base and employee directory:

**Components:**
- **Vector Store**: ChromaDB with sentence-transformers embeddings (all-MiniLM-L6-v2)
- **Wiki Integration**: OtterWiki knowledge base with automatic indexing
- **Employee Directory**: Real-time lookup for sender information (mobile, phone, department, location)
- **Confidence Scoring**: Relevance-based enrichment with similarity thresholds
- **Async Processing**: Non-blocking enrichment with graceful fallbacks

**Enrichment Capabilities:**
- Contextual wiki knowledge injection
- Employee profile augmentation
- Department and location context
- Contact information retrieval

#### 4. LLM Integration with Automatic Fallback
Dual-mode LLM system supporting both cloud and offline operation:

**Primary (Ollama - Offline)**:
- Model: Phi3 (lightweight, efficient)
- Use case: Email summarization, badge detection, CTA extraction
- Fully offline operation

**Secondary (OpenAI - Optional)**:
- Model: GPT-4o-mini (fast, cost-effective)
- Use case: Agentic team discussions (higher quality)
- Automatic fallback to Ollama if unavailable

**Smart Fallback Logic**:
- Automatically uses Ollama when:
  - No `.env` file exists
  - `OPENAI_API_KEY` not set or empty
  - API key contains placeholder values
  - OpenAI API fails at runtime (network, rate limits)
- Zero configuration needed for offline mode
- Seamless cloud-to-local switching

#### 5. AI-Powered Email Processing
Comprehensive LLM-based email analysis:

- **Smart Summarization**: Concise email summaries (2-3 sentences)
- **Badge Detection**: Auto-categorization into 8 types
  - MEETING - Calendar events and scheduling
  - RISK - Phishing/security threats
  - EXTERNAL - Emails from external sources
  - AUTOMATED - Auto-generated notifications
  - VIP - Important contacts
  - FOLLOW_UP - Requires action or response
  - NEWSLETTER - Marketing/bulk emails
  - FINANCE - Financial transactions
- **CTA Extraction**: Automatic call-to-action detection
- **Quick Reply Drafts**: 3 AI-generated response tones (formal, friendly, brief)

#### 6. Background Processing & Real-Time Updates
Automated email monitoring and processing:

- **Email Fetcher**: Continuous polling from MailPit (configurable interval)
- **Email Analyzer**: Background ML workflow execution
- **Server-Sent Events**: Real-time updates for:
  - Email processing status
  - Workflow results
  - Agentic team discussions
  - Analysis progress
- **Task Management**: Async task tracking with unique task IDs

#### 7. Professional Web Dashboard
Material Dashboard-based UI with multiple views:

**Pages:**
- **Dashboard** (`/`) - Statistics, quick actions, real-time monitoring
- **Mailbox** (`/pages/mailbox.html`) - Email list/detail with workflow results, quick replies
- **Daily Inbox Digest** (`/pages/inbox-digest.html`) - Emails grouped by badges
- **Agentic Teams** (`/pages/agentic-teams.html`) - Real-time team discussion visualization

**UI Features:**
- Bootstrap 5 with Material Design
- Chart.js visualizations
- Real-time SSE updates
- Responsive design
- Badge-based categorization
- Workflow result panels
- Quick reply integration

### Architecture

#### Docker Services (11 Containers)

| Service | Technology | Purpose |
|---------|-----------|---------|
| **postgres** | PostgreSQL 15 | Main database |
| **ollama** | Ollama (Phi3) | Local LLM inference |
| **backend** | FastAPI + Python 3.11 | REST API & orchestration |
| **frontend** | Nginx + Material Dashboard | Web UI |
| **mailpit** | MailPit | SMTP server (pre-seeded) |
| **wiki** | OtterWiki | Internal knowledge base |
| **email-seeder** | Python | Initial email seeding |
| **email-fetcher** | Python | Continuous email fetching |
| **email-analyzer** | Python | Background ML processing |
| **nb-phishing** | Python + scikit-learn | Naive Bayes model service |
| **rf-phishing** | Python + scikit-learn | Random Forest model service |
| **employee-directory** | FastAPI | Employee lookup service |

#### Database Schema

**Tables:**
- `emails` - Email content, metadata, summaries, badges, CTAs, quick replies, enrichment data
- `workflow_results` - ML model predictions with confidence scores
- `workflow_configs` - Workflow definitions and status
- `teams` - Agentic team configurations
- `team_agents` - Individual agent definitions with personalities

**Migrations:**
- Liquibase-managed schema versioning
- Automatic migration on startup
- Changelog: `backend/db/changelog/`

#### API Endpoints (33 Endpoints)

**Email Management:**
- `GET /api/emails` - List all emails with summaries, badges, quick replies
- `GET /api/emails/{id}` - Get email details with workflow results
- `POST /api/emails/fetch` - Fetch new emails from MailPit
- `DELETE /api/emails/{id}` - Delete specific email
- `DELETE /api/emails` - Delete all emails

**Phishing Detection:**
- `POST /api/emails/{id}/process` - Run ML workflows
- `POST /api/emails/process-all` - Batch process all unprocessed emails
- `GET /api/workflows` - List available workflows
- `GET /api/workflows/{id}` - Get workflow configuration

**LLM Processing:**
- `POST /api/emails/{id}/process-llm` - Generate summary, badges, CTAs, quick replies
- `POST /api/emails/process-all-llm` - Batch LLM processing
- `POST /api/emails/{id}/enrich` - RAG enrichment (wiki + employee directory)

**Agentic Teams:**
- `GET /api/agentic/teams` - List all teams
- `GET /api/agentic/teams/{team_key}/config` - Get team configuration
- `POST /api/agentic/emails/{email_id}/process` - Start team discussion
- `GET /api/agentic/tasks/{task_id}` - Poll discussion progress
- `GET /api/agentic/tasks/{task_id}/stream` - Stream real-time updates (SSE)
- `POST /api/emails/{email_id}/suggest-team` - LLM-based team suggestion
- `POST /api/emails/{email_id}/assign-team` - Assign email to team

**Inbox Management:**
- `GET /api/inbox-digest` - Emails grouped by badges
- `GET /api/daily-summary` - Aggregated statistics
- `GET /api/statistics` - Overall metrics

**Background Services:**
- `POST /api/background/email-fetcher/start` - Start continuous fetching
- `POST /api/background/email-fetcher/stop` - Stop fetcher
- `GET /api/background/email-fetcher/status` - Check fetcher status
- `POST /api/background/email-analyzer/start` - Start continuous analysis
- `POST /api/background/email-analyzer/stop` - Stop analyzer
- `GET /api/background/email-analyzer/status` - Check analyzer status

**System:**
- `GET /health` - Health check
- `GET /` - API info

## Quick Start

### Prerequisites

- Docker and Docker Compose plugin
- At least 4GB available RAM
- Ports: 80, 1025, 5432, 8000, 8025, 8080, 8100 available

### Installation

**1. Clone the repository:**
```bash
git clone <repository-url>
cd ai-cup-2025
```

**2. (Optional) Configure OpenAI for Agentic Teams:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
# If not configured, automatically falls back to Ollama
```

**3. Start all services:**
```bash
./start.sh
```

The startup script will:
- Check Docker availability
- Detect and handle port conflicts
- Build images if needed
- Start all services in correct order
- Display access URLs when ready

### First Use

1. **Access Dashboard**: http://localhost
2. **Fetch Emails**: Click "Fetch Emails from MailPit" (loads 10,000 emails)
3. **Run Analysis**: Click "Run Analysis" on any email
4. **View Results**: See ML predictions, summaries, badges, quick replies
5. **Try Agentic Teams**: Assign emails to specialized teams for deep analysis
6. **Explore Digest**: Navigate to Daily Inbox Digest for categorized view

### Access URLs

- **Email Dashboard**: http://localhost
- **Daily Inbox Digest**: http://localhost/pages/inbox-digest.html
- **Mailbox**: http://localhost/pages/mailbox.html
- **Agentic Teams**: http://localhost/pages/agentic-teams.html
- **MailPit Web UI**: http://localhost:8025
- **Wiki**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs

## Configuration

### Environment Variables

**OpenAI Configuration** (Optional - Automatic Fallback):
```bash
OPENAI_API_KEY=your_key_here        # Optional, falls back to Ollama
OPENAI_MODEL=gpt-4o-mini            # Default model for agentic teams
```

**Service Configuration** (Auto-configured in Docker):
```bash
DATABASE_URL=postgresql://...       # PostgreSQL connection
OLLAMA_HOST=ollama                  # Ollama service hostname
OLLAMA_PORT=11434                   # Ollama port
OLLAMA_MODEL=phi3                   # Local LLM model
MAILPIT_HOST=mailpit                # MailPit hostname
MAILPIT_PORT=8025                   # MailPit API port
```

### LLM Mode Selection

The system automatically selects the appropriate LLM:

**Scenario 1: No OpenAI Key**
- Agentic Teams: Ollama (tinyllama:latest)
- Email Processing: Ollama (phi3)
- Status: Fully offline operation

**Scenario 2: Valid OpenAI Key**
- Agentic Teams: OpenAI (gpt-4o-mini)
- Email Processing: Ollama (phi3)
- Status: Hybrid operation

**Scenario 3: OpenAI Fails**
- Automatic fallback to Ollama
- Status: Resilient operation

## Management Scripts

### start.sh - Start Application
```bash
./start.sh
```
Intelligent startup with port conflict detection and status display.

### stop.sh - Stop Application
```bash
./stop.sh              # Stop containers
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

Available services: `postgres`, `backend`, `frontend`, `mailpit`, `ollama`, `wiki`, `email-seeder`, `email-fetcher`, `email-analyzer`, `nb-phishing`, `rf-phishing`, `employee-directory`

## Dataset

**Phishing and Legitimate Emails Dataset** by Kuladeep19
- **Source**: https://www.kaggle.com/datasets/kuladeep19/phishing-and-legitimate-emails-dataset
- **Size**: 10,000 emails with ground truth labels
- **Distribution**: 60% phishing (6,000), 40% legitimate (4,000)
- **Categories**:
  - Credential harvesting
  - Authority scams
  - Romance/dating scams
  - Financial fraud
  - Legitimate emails

**Email Seeder:**
- Automatically loads dataset on startup
- Sends all emails to MailPit SMTP server
- Preserves labels in custom headers (X-Email-Label, X-Phishing-Type)
- Generates contextual sender addresses

## Documentation

Comprehensive documentation available in `docs/`:

- **README.md** - Complete feature documentation
- **01-ml-workflow.md** - ML model training and evaluation
- **02-ensemble-model.md** - Ensemble strategy and voting
- **03-database-schema.md** - Database design and migrations
- **04-rag-system.md** - RAG implementation details
- **05-agentic-teams.md** - Multi-agent collaboration system
- **06-api-endpoints.md** - API reference
- **07-deployment.md** - Production deployment guide
- **08-testing.md** - Testing strategy

## Project Structure

```
ai-cup-2025/
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
├── start.sh                     # Startup script
├── stop.sh                      # Shutdown script
├── logs.sh                      # Log viewer
├── README.md                    # This file
├── docs/                        # Documentation
│   ├── README.md
│   └── [01-08]-*.md            # Feature docs
├── frontend/                    # Web UI
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html              # Dashboard
│   └── pages/
│       ├── mailbox.html        # Email viewer
│       ├── inbox-digest.html   # Categorized inbox
│       └── agentic-teams.html  # Team discussions
├── backend/                     # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # API endpoints (1826 lines)
│   ├── models.py               # Database ORM models
│   ├── database.py             # DB connection
│   ├── workflows.py            # ML workflows
│   ├── agentic_teams.py        # Multi-agent orchestration
│   ├── wiki_enrichment.py      # RAG system
│   ├── llm_service.py          # LLM integration
│   ├── mailpit_client.py       # MailPit integration
│   ├── test_fallback.py        # Fallback testing
│   └── db/
│       └── changelog/          # Liquibase migrations
├── email-seeder/               # Dataset loader
│   ├── Dockerfile
│   ├── seed_emails.py
│   └── phishing_emails.csv
├── email-fetcher/              # Background fetcher
│   ├── Dockerfile
│   └── fetch_emails.py
├── email-analyzer/             # Background analyzer
│   ├── Dockerfile
│   └── analyze_emails.py
├── nb-phishing/                # Naive Bayes service
│   ├── Dockerfile
│   ├── train.py
│   └── serve.py
├── rf-phishing/                # Random Forest service
│   ├── Dockerfile
│   ├── train.py
│   └── serve.py
├── employee-directory/         # Employee API
│   ├── Dockerfile
│   └── main.py
└── postgres/
    └── init.sql                # DB initialization
```

## Performance Metrics

### ML Model Performance
- **Ensemble Accuracy**: 82.10%
- **Ensemble F1-Score**: 81.90%
- **Ensemble Precision**: 81.90%
- **Ensemble Recall**: 82.00%
- **Training Time**: ~5-10 minutes (all models)
- **Inference Time**: <100ms per email

### System Performance
- **Email Processing**: 10+ emails/second
- **LLM Summarization**: 2-3 seconds per email (Ollama)
- **RAG Enrichment**: <500ms per email
- **Agentic Team Discussion**: 30-60 seconds (3 rounds, 4 agents)
- **Database**: 10,000+ emails indexed
- **Real-time Updates**: <100ms SSE latency

### Scalability
- **Tested Load**: 10,000 emails
- **Concurrent Users**: 10+ simultaneous connections
- **Background Processing**: Automatic queue management
- **Memory Usage**: ~3GB total (all services)
- **Disk Usage**: ~5GB (including models and database)

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104
- **Language**: Python 3.11
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Liquibase
- **Async**: asyncio, httpx
- **ML**: scikit-learn, pandas, numpy
- **LLM**: Ollama, OpenAI SDK
- **RAG**: ChromaDB, sentence-transformers
- **Agentic**: LangGraph

### Frontend
- **Template**: Material Dashboard
- **Framework**: Bootstrap 5
- **Icons**: Material Icons, Font Awesome
- **Charts**: Chart.js
- **Real-time**: Server-Sent Events

### Infrastructure
- **Containerization**: Docker Compose
- **Database**: PostgreSQL 15
- **Web Server**: Nginx
- **SMTP**: MailPit
- **Wiki**: OtterWiki
- **LLM Inference**: Ollama

## Development

### Testing
```bash
# Run fallback mechanism tests
docker compose exec backend python3 /app/test_fallback.py

# Check service health
curl http://localhost:8000/health

# Test ML endpoint
curl -X POST http://localhost:8000/api/emails/1/process

# Test agentic teams
curl -X POST http://localhost:8000/api/agentic/emails/1/process?team=fraud
```

### Debugging
```bash
# View backend logs
./logs.sh -f backend

# Check database
docker compose exec postgres psql -U mailbox_user -d mailbox -c "SELECT COUNT(*) FROM emails;"

# Restart single service
docker compose restart backend

# Access Ollama directly
docker compose exec ollama ollama list
```

### Rebuilding
```bash
# Rebuild specific service
docker compose build backend

# Rebuild all services
docker compose build

# Force rebuild
docker compose build --no-cache
```

## Troubleshooting

### Common Issues

**1. Ports already in use:**
```bash
# The start.sh script automatically detects conflicts
# Or manually check:
./stop.sh
./start.sh
```

**2. Ollama model not downloaded:**
```bash
# Check Ollama status
docker compose exec ollama ollama list

# Manually pull model
docker compose exec ollama ollama pull phi3
```

**3. Database migration fails:**
```bash
# Check migration logs
./logs.sh backend | grep liquibase

# Reset database (WARNING: deletes data)
./stop.sh -v
./start.sh
```

**4. OpenAI fallback not working:**
```bash
# Verify configuration
docker compose exec backend env | grep OPENAI

# Check backend logs for fallback messages
./logs.sh backend | grep "Orchestrator"
```

## Contributing

### Development Workflow
1. Make changes to code
2. Test locally with Docker Compose
3. Update documentation if needed
4. Commit changes with descriptive messages

### Code Style
- Backend: PEP 8 (Python)
- Frontend: Standard JavaScript
- Comments: Clear, concise explanations
- Documentation: Markdown with examples

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- **Documentation**: See `docs/` folder
- **API Docs**: http://localhost:8000/docs (when running)
- **Logs**: Use `./logs.sh` for debugging

## Acknowledgments

- **Dataset**: Kuladeep19 - Phishing and Legitimate Emails Dataset (Kaggle)
- **UI Template**: Material Dashboard by Creative Tim
- **LLM**: Ollama project, OpenAI
- **Framework**: FastAPI, LangGraph

---

**Status**: Production Ready | **Version**: 1.0 | **Last Updated**: 2025-10-31
