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

#### Sample Data

**Example Email Records:**

**Legitimate Email Example:**

| Column | Value |
|--------|-------|
| id | 1 |
| mailpit_id | legit-email-001 |
| subject | Q4 Financial Report - Action Required |
| sender | finance@company.com |
| recipient | employee@company.com |
| body_text | Dear Team, Please review the attached Q4 financial report... |
| received_at | 2025-01-15 09:30:00 |
| is_phishing | false |
| processed | true |
| summary | Request to review Q4 financial report with deadline |
| llm_processed | true |
| label | 0 |
| phishing_type | legitimate |
| enriched | false |

**Phishing Email Example (Urgent Action Scam):**

| Column | Value |
|--------|-------|
| id | 2 |
| mailpit_id | phish-email-001 |
| subject | URGENT: Your Account Will Be Suspended |
| sender | security@suspicious-bank.com |
| recipient | customer@email.com |
| body_text | Dear Customer, We detected suspicious activity... Click here immediately... |
| received_at | 2025-01-14 13:45:00 |
| is_phishing | true |
| processed | true |
| summary | Suspicious email claiming account suspension threat with urgent verification request |
| llm_processed | true |
| label | 1 |
| phishing_type | urgent_action |
| enriched | false |

**Phishing Email Example (Business Email Compromise):**

| Column | Value |
|--------|-------|
| id | 3 |
| mailpit_id | phish-email-002 |
| subject | CEO: Urgent Wire Transfer Needed |
| sender | ceo@company-typo.com |
| recipient | finance@company.com |
| body_text | I am currently in a meeting with investors and need you to process an urgent wire transfer for $50,000... |
| received_at | 2025-01-16 09:00:00 |
| is_phishing | true |
| processed | true |
| summary | CEO fraud/impersonation requesting urgent confidential wire transfer |
| llm_processed | true |
| label | 1 |
| phishing_type | business_email_compromise |
| enriched | false |

**Example JSON Fields:**

`badges` field example:
```json
["MEETING", "EXTERNAL"]
```

`call_to_actions` field example:
```json
[
  "Reschedule meeting time to accommodate new circumstances.",
  "Confirm availability for the rescheduled meeting with Jamie Singh."
]
```

`enriched_data` field example:
```json
{
  "relevant_pages": ["Conference and Events", "Meeting Policy"],
  "sender_employee": {
    "city": "Thun",
    "email": "friend@meetme.com",
    "phone": "+41 041 767 52 31",
    "mobile": "+41 77 749 67 17",
    "address": "Schulstrasse 135",
    "country": "Switzerland",
    "last_name": "Kaufmann",
    "department": "IT & Digital",
    "first_name": "René",
    "designation": "Cybersecurity Analyst",
    "employee_id": "SB05002"
  },
  "enriched_keywords": [
    {
      "keyword": "meeting",
      "wiki_page": "Meeting Policy",
      "confidence": 47.1,
      "context": "Company Meeting and Calendar Policy..."
    }
  ],
  "recipient_employee": null
}
```

**Current Database Statistics:**
- Total Emails: 4,000
- Processed: 35
- Phishing Detected: 14

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

#### Sample Data

**Example Workflow Configuration Records:**

| id | name | description | enabled | created_at |
|----|------|-------------|---------|------------|
| 1 | ML: Logistic Regression | Logistic Regression model for binary classification of phishing emails | true | 2025-01-01 10:00:00 |
| 2 | ML: Naive Bayes | Naive Bayes classifier for probabilistic phishing detection | true | 2025-01-01 10:00:00 |
| 3 | ML: Neural Network | Deep learning neural network for advanced pattern recognition | true | 2025-01-01 10:00:00 |
| 4 | ML: Random Forest | Ensemble Random Forest model with multiple decision trees | true | 2025-01-01 10:00:00 |
| 5 | ML: SVM | Support Vector Machine for high-dimensional feature classification | true | 2025-01-01 10:00:00 |
| 6 | ML: Fine-tuned LLM (DistilBERT) | Fine-tuned DistilBERT language model for contextual email analysis | true | 2025-01-01 10:00:00 |

**Example `config` JSON field:**

```json
{
  "model_path": "/app/data/models/logistic_regression_model.pkl",
  "threshold": 0.5,
  "port": 8001
}
```

**Example for Random Forest model:**
```json
{
  "model_path": "/app/data/models/random_forest_model.pkl",
  "n_estimators": 100,
  "max_depth": 10,
  "port": 8004
}
```

**Example for Fine-tuned LLM:**
```json
{
  "model_path": "/app/data/models/distilbert_model",
  "max_length": 512,
  "batch_size": 16,
  "port": 8006
}
```

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

#### Sample Data

**Example 1: Results for Legitimate Email (ID=1, Q4 Financial Report)**

| id | email_id | workflow_name | is_phishing_detected | confidence_score | executed_at |
|----|----------|---------------|----------------------|------------------|-------------|
| 1 | 1 | ML: Logistic Regression | false | 95 | 2025-01-15 09:32:00 |
| 2 | 1 | ML: Naive Bayes | false | 92 | 2025-01-15 09:32:00 |
| 3 | 1 | ML: Fine-tuned LLM (DistilBERT) | false | 98 | 2025-01-15 09:33:00 |

`result` field example (Logistic Regression):
```json
{
  "prediction": "legitimate",
  "features_analyzed": ["sender_domain", "content_analysis", "url_presence"]
}
```

`risk_indicators` field: `[]` (empty - no risks detected)

---

**Example 2: Results for Phishing Email (ID=2, Account Suspension Threat)**

| id | email_id | workflow_name | is_phishing_detected | confidence_score | executed_at |
|----|----------|---------------|----------------------|------------------|-------------|
| 4 | 2 | ML: Logistic Regression | true | 87 | 2025-01-14 13:47:00 |
| 5 | 2 | ML: Naive Bayes | true | 91 | 2025-01-14 13:47:00 |
| 6 | 2 | ML: Random Forest | true | 89 | 2025-01-14 13:47:00 |
| 7 | 2 | ML: Fine-tuned LLM (DistilBERT) | true | 96 | 2025-01-14 13:48:00 |
| 8 | 2 | Rule-Based: URL Analysis | true | 100 | 2025-01-14 13:47:00 |

`result` field example (Fine-tuned LLM):
```json
{
  "prediction": "phishing",
  "semantic_analysis": "threatening language with urgency tactics"
}
```

`risk_indicators` field example:
```json
["threat_language", "urgency_tactics", "suspicious_link", "blacklisted_domain"]
```

---

**Example 3: Results for BEC Email (ID=3, CEO Fraud)**

| id | email_id | workflow_name | is_phishing_detected | confidence_score | executed_at |
|----|----------|---------------|----------------------|------------------|-------------|
| 9 | 3 | ML: Logistic Regression | true | 82 | 2025-01-16 09:02:00 |
| 10 | 3 | ML: Fine-tuned LLM (DistilBERT) | true | 97 | 2025-01-16 09:03:00 |
| 11 | 3 | Rule-Based: Header Analysis | true | 95 | 2025-01-16 09:02:00 |

`result` field example (Header Analysis):
```json
{
  "spf_check": "fail",
  "domain_mismatch": "company-typo.com vs company.com"
}
```

`risk_indicators` field example:
```json
["ceo_fraud", "wire_fraud", "urgency_tactics", "confidentiality_manipulation", "domain_typosquatting", "spf_failure"]
```

---

**Analysis Notes:**
- **Consensus Detection**: Multiple ML models analyze each email independently - final decision uses ensemble voting
- **Confidence Scores**: Range from 0-100, representing model certainty
- **Model Disagreement**: Different models may have varying opinions (e.g., some borderline cases)
- **Risk Indicators**: Stored as JSON array of specific threat patterns detected
- **Execution Time**: All workflows run in parallel for faster processing
- **Rule-Based vs ML**: Rule-based workflows often have 100% confidence when patterns match exactly

---

### **4. databasechangelog**
Liquibase migration tracking table that records all database schema changes that have been applied.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar | Unique identifier for the changeset |
| `author` | varchar | Author of the migration |
| `filename` | varchar | Path to the changelog file |
| `dateexecuted` | timestamp | When the migration was executed |
| `orderexecuted` | integer | Order of execution |
| `exectype` | varchar | Type of execution (EXECUTED, RERAN, etc.) |
| `md5sum` | varchar | Checksum of the changeset |
| `description` | varchar | Description of the change |
| `comments` | varchar | Additional comments |
| `tag` | varchar | Version tag |
| `liquibase` | varchar | Liquibase version used |

#### Sample Data

| id | author | filename | dateexecuted | description |
|----|--------|----------|--------------|-------------|
| 000-create-emails-table | ai-cup-2025 | db/changelog/changes/000-initial-schema.xml | 2025-01-01 00:00:00 | createTable tableName=emails |
| 000-create-workflow-configs-table | ai-cup-2025 | db/changelog/changes/000-initial-schema.xml | 2025-01-01 00:00:01 | createTable tableName=workflow_configs |
| 000-create-workflow-results-table | ai-cup-2025 | db/changelog/changes/000-initial-schema.xml | 2025-01-01 00:00:02 | createTable tableName=workflow_results |
| 001-add-badges-column | ai-cup-2025 | db/changelog/changes/001-add-email-badges-and-drafts.xml | 2025-01-02 10:00:00 | addColumn tableName=emails |
| 003-add-dataset-label-column | ai-cup-2025 | db/changelog/changes/003-add-dataset-labels.xml | 2025-01-05 14:00:00 | addColumn tableName=emails |
| 006-add-wiki-enriched-timestamp | ai-cup-2025 | db/changelog/changes/006-add-enrichment-timestamps.xml | 2025-01-10 09:00:00 | addColumn tableName=emails |

---

### **5. databasechangeloglock**
Liquibase lock table that prevents concurrent migration execution.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Lock identifier (typically 1) |
| `locked` | boolean | Whether the lock is currently held |
| `lockgranted` | timestamp | When the lock was acquired |
| `lockedby` | varchar | Process/host that holds the lock |

#### Sample Data

| id | locked | lockgranted | lockedby |
|----|--------|-------------|----------|
| 1 | false | null | null |

**Note:** This table typically has only one row. When Liquibase runs migrations, it sets `locked=true` to prevent concurrent executions, then releases the lock when done.

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
