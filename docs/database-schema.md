# PostgreSQL Database Schema Documentation

## Database: `mailbox_db`

This document describes the database schema for the AI Cup 2025 phishing detection system.

---

## Tables Overview

| Table Name | Description |
|------------|-------------|
| `emails` | Main table storing email messages and their analysis results |
| `workflow_configs` | Configuration for different phishing detection workflows |
| `workflow_results` | Individual results from each workflow execution per email |
| `databasechangelog` | Liquibase/Flyway migration tracking table |
| `databasechangeloglock` | Liquibase/Flyway migration lock table |

---

## Table Details

### **1. emails**
Main table storing email messages and their analysis results.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NOT NULL | auto-generated | Primary key, auto-generated identity |
| `mailpit_id` | varchar | YES | - | Unique identifier from MailPit system |
| `subject` | varchar | YES | - | Email subject line |
| `sender` | varchar | YES | - | Email sender address |
| `recipient` | varchar | YES | - | Email recipient address |
| `body_text` | text | YES | - | Plain text version of email body |
| `body_html` | text | YES | - | HTML version of email body |
| `received_at` | timestamp | YES | - | When the email was received |
| `is_phishing` | boolean | YES | - | Overall phishing detection result |
| `processed` | boolean | YES | - | Whether email has been processed by workflows |
| `summary` | text | YES | - | AI-generated summary of the email |
| `call_to_actions` | json | YES | - | Extracted call-to-action items from email |
| `llm_processed` | boolean | YES | - | Whether LLM has processed this email |
| `llm_processed_at` | timestamp | YES | - | When LLM processing completed |
| `badges` | jsonb | YES | - | Badge metadata for UI display |
| `quick_reply_drafts` | jsonb | YES | - | AI-generated quick reply suggestions |
| `ui_badges` | jsonb | YES | - | Additional UI badge information |
| `label` | integer | YES | - | Ground truth label (0=legitimate, 1=phishing) from dataset |
| `phishing_type` | varchar(255) | YES | - | Type of phishing (e.g., tech_support, business_email_compromise) |
| `enriched_data` | jsonb | YES | - | Additional enriched data from external sources |
| `enriched` | boolean | NOT NULL | false | Whether email has been enriched |
| `enriched_at` | timestamp | YES | - | When enrichment completed |
| `wiki_enriched` | boolean | NOT NULL | false | Whether Wikipedia enrichment completed |
| `phone_enriched` | boolean | NOT NULL | false | Whether phone number enrichment completed |
| `wiki_enriched_at` | timestamp | YES | - | When Wikipedia enrichment completed |
| `phone_enriched_at` | timestamp | YES | - | When phone enrichment completed |

**Indexes:**
- `emails_pkey` - PRIMARY KEY on `id`
- `ix_emails_id` - Index on `id`
- `ix_emails_mailpit_id` - UNIQUE index on `mailpit_id`

**Referenced By:**
- `workflow_results.email_id` (Foreign Key)

---

### **2. workflow_configs**
Configuration for different phishing detection workflows.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NOT NULL | auto-generated | Primary key, auto-generated identity |
| `name` | varchar | YES | - | Unique workflow name (e.g., "ML: Logistic Regression") |
| `description` | text | YES | - | Human-readable description of the workflow |
| `enabled` | boolean | YES | - | Whether this workflow is active |
| `config` | json | YES | - | JSON configuration for workflow parameters |
| `created_at` | timestamp | YES | - | When the workflow was created |

**Indexes:**
- `workflow_configs_pkey` - PRIMARY KEY on `id`
- `ix_workflow_configs_id` - Index on `id`
- `workflow_configs_name_key` - UNIQUE constraint on `name`

---

### **3. workflow_results**
Individual results from each workflow execution per email. Each email can have multiple workflow results (one per detection method/ML model).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | integer | NOT NULL | auto-generated | Primary key, auto-generated identity |
| `email_id` | integer | YES | - | Foreign key to emails table |
| `workflow_name` | varchar | YES | - | Name of the workflow that produced this result |
| `result` | json | YES | - | Detailed JSON result from workflow execution |
| `is_phishing_detected` | boolean | YES | - | Whether this workflow detected phishing |
| `confidence_score` | integer | YES | - | Confidence percentage (0-100) |
| `risk_indicators` | json | YES | - | Specific risk indicators identified by the workflow |
| `executed_at` | timestamp | YES | - | When this workflow executed |

**Indexes:**
- `workflow_results_pkey` - PRIMARY KEY on `id`
- `ix_workflow_results_id` - Index on `id`

**Foreign Keys:**
- `email_id` REFERENCES `emails(id)`

---

### **4. databasechangelog** & **5. databasechangeloglock**
These are Liquibase/Flyway migration tracking tables used for database schema version control. They track which database migrations have been applied and prevent concurrent migration execution.

---

## Entity Relationships

```
┌─────────────────┐
│     emails      │
│                 │
│  PK: id         │
│  UK: mailpit_id │
└────────┬────────┘
         │
         │ 1
         │
         │
         │ many
         │
         ▼
┌─────────────────────┐
│  workflow_results   │
│                     │
│  PK: id             │
│  FK: email_id       │
│      workflow_name  │
└─────────────────────┘
```

**Relationship Description:**
- One email can have multiple workflow results (one-to-many)
- Each workflow result belongs to exactly one email
- This allows the system to store independent results from different ML models and analysis workflows for the same email

---

## Data Flow

1. **Email Ingestion**: Emails are fetched from MailPit and stored in the `emails` table
2. **Workflow Processing**: Each enabled workflow (configured in `workflow_configs`) processes the email
3. **Results Storage**: Each workflow execution creates a record in `workflow_results` with detection outcome and confidence
4. **Aggregation**: The overall `is_phishing` determination in the `emails` table is based on aggregating multiple workflow results
5. **Enrichment**: Additional data can be added via the enrichment process (Wikipedia, phone lookups, etc.)

---

## Notes

- **Ground Truth Data**: The `label` and `phishing_type` fields in the `emails` table contain ground truth data from the Kaggle dataset for validation purposes
- **JSON Fields**: Several fields use JSON/JSONB for flexible storage of structured data (badges, enriched data, workflow configs, etc.)
- **Timestamps**: All timestamps are stored as `timestamp without time zone`
- **Enrichment Tracking**: Multiple boolean flags track different enrichment stages (general, wiki, phone) with corresponding timestamp fields
