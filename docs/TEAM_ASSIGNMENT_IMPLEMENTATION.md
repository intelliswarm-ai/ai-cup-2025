# Intelligent Team Assignment System - Implementation Guide

## Overview

This implementation adds an intelligent, LLM-powered team assignment system for the email mailbox with manual operator control over agentic workflow triggering.

## Key Features

### 1. **LLM-Based Team Suggestion**
- Automatically analyzes incoming emails using LLM (phi3:latest)
- Suggests the most appropriate team from 6 available teams:
  - **Credit Risk Committee** - Loan requests, credit analysis
  - **Fraud Investigation Unit** - Suspicious activities, phishing
  - **Compliance & Regulatory Affairs** - Legal, regulatory matters
  - **Wealth Management Advisory** - Investments, estate planning
  - **Corporate Banking Team** - Trade finance, corporate services
  - **Operations & Quality** - Customer complaints, process issues

### 2. **Manual Workflow Triggering**
- No automatic agentic workflow execution on email arrival
- Workflow only starts when mailbox operator manually assigns email to team
- Operator can accept AI suggestion or choose different team

### 3. **Workflow Tracking**
- Each email stores link to its agentic workflow discussion room
- Email modal displays direct link to view team discussion
- Task ID tracked for status monitoring

## Implementation Details

### Backend Changes

#### 1. Database Schema (`backend/models.py`)
Added new fields to `Email` model:
```python
suggested_team: str          # LLM-suggested team
assigned_team: str           # Operator-assigned team
agentic_task_id: str        # Workflow task ID for tracking
team_assigned_at: DateTime  # Assignment timestamp
```

#### 2. LLM Team Suggestion (`backend/agentic_teams.py`)
New function `suggest_team_for_email_llm()`:
- Analyzes email subject, body, and sender
- Provides team descriptions to LLM
- Returns suggested team key
- Falls back to keyword-based detection on error

#### 3. New API Endpoints (`backend/main.py`)

**POST `/api/emails/{email_id}/suggest-team`**
- Uses LLM to suggest team for email
- Stores suggestion in database
- Returns suggested team info

**POST `/api/emails/{email_id}/assign-team?team={team_key}`**
- Assigns email to specified team
- Creates agentic workflow task
- Stores task_id in email record
- Returns workflow URL

**GET `/api/emails/{email_id}/workflow-status`**
- Gets current workflow status
- Returns workflow room link
- Includes task completion status

#### 4. Auto-Suggestion on Fetch (`backend/main.py`)
- Background task `auto_suggest_teams_for_emails()`
- Runs after email fetching completes
- Suggests teams for emails without suggestions
- Processes up to 50 emails per batch

#### 5. Modified Workflow Trigger
- Updated `/api/agentic/emails/{email_id}/process`
- Now stores task_id and assigned_team in email record
- Links email to workflow for tracking

### Frontend Changes

#### 1. Team Badge Styles (`frontend/pages/mailbox.html`)
Added CSS for team badges with color-coded gradients:
- Credit Risk: Blue gradient
- Fraud: Red gradient
- Compliance: Gray gradient
- Wealth: Gold gradient
- Corporate: Green gradient
- Operations: Brown gradient

#### 2. Email Card Display
Updated email list cards to show:
- Suggested team badge (with AI icon)
- Assigned team badge (with team icon)
- Visual distinction between suggested vs assigned

#### 3. Email Modal Team Assignment
Added comprehensive team assignment section:
- Shows AI-suggested team with "Accept Suggestion" button
- Provides buttons for all 6 teams to manually assign
- Displays assigned team badge when already assigned
- Shows direct link to agentic workflow discussion room
- Includes task ID for reference

#### 4. JavaScript Functions
- `getTeamDisplayName(teamKey)` - Maps keys to display names
- `assignTeamToEmail(emailId, teamKey)` - Assigns team and triggers workflow
- Updates UI after assignment
- Opens workflow page on user confirmation

### Database Migration

#### Files Created:
1. `backend/migrations/add_team_assignment_fields.sql`
   - SQL script to add new columns
   - Can be run manually if needed

2. `backend/migrations/run_migration.py`
   - Python script to run migration
   - Adds columns using IF NOT EXISTS for safety

#### Running Migration:

**Option 1: Automatic (recommended)**
```bash
cd backend
python migrations/run_migration.py
```

**Option 2: Manual SQL**
```bash
psql -U mailbox_user -d mailbox_db -f backend/migrations/add_team_assignment_fields.sql
```

**Option 3: Restart Backend**
- SQLAlchemy will attempt to create columns on startup
- Works for new installations only

## User Workflow

### Email Processing Flow

1. **Email Arrives**
   - Fetched from Mailpit
   - Stored in database
   - LLM automatically suggests team (background)
   - NO workflow triggered yet

2. **Operator Views Mailbox**
   - Sees email with suggested team badge
   - Badge shows: "Psychology icon + Team Name (Suggested)"
   - Example: "🧠 Fraud Investigation (Suggested)"

3. **Operator Opens Email**
   - Modal displays AI suggestion prominently
   - "Accept Suggestion" button to use AI's choice
   - Alternative: 6 team buttons to manually select

4. **Operator Assigns Team**
   - Clicks team button
   - System assigns email to team
   - Creates agentic workflow task
   - Stores task_id in email record
   - Shows success message with task ID

5. **Operator Views Workflow** (Optional)
   - Confirmation dialog asks if user wants to view workflow
   - OR: Click "View Team Discussion" link in email modal
   - Opens agentic-teams.html with email_id and task_id
   - Shows real-time team discussion

6. **Future Reference**
   - Email modal always shows workflow link
   - Can revisit discussion anytime
   - Task ID preserved for tracking

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/emails/{id}/suggest-team` | POST | LLM suggests team for email |
| `/api/emails/{id}/assign-team?team={key}` | POST | Assign team & trigger workflow |
| `/api/emails/{id}/workflow-status` | GET | Get workflow status and link |
| `/api/agentic/emails/{id}/process?team={key}` | POST | Existing: Start workflow (now with tracking) |
| `/api/agentic/tasks/{task_id}` | GET | Existing: Poll workflow status |
| `/api/agentic/teams` | GET | Existing: List all teams |

## Team Keys and Display Names

| Key | Display Name | Icon |
|-----|-------------|------|
| `credit_risk` | Credit Risk | account_balance |
| `fraud` | Fraud Investigation | search |
| `compliance` | Compliance | gavel |
| `wealth` | Wealth Management | trending_up |
| `corporate` | Corporate Banking | business |
| `operations` | Operations | settings |

## Testing Checklist

- [ ] Run database migration
- [ ] Restart backend service
- [ ] Fetch emails from Mailpit
- [ ] Verify team suggestions appear automatically
- [ ] Open email modal and check team assignment section
- [ ] Assign email to suggested team
- [ ] Verify workflow link appears
- [ ] Click workflow link to view discussion
- [ ] Assign email to different team than suggested
- [ ] Verify email list shows assigned team badge
- [ ] Check that workflow doesn't trigger on fetch (only on assignment)

## Configuration

### Environment Variables
No new environment variables required. Uses existing:
- `DATABASE_URL` - PostgreSQL connection
- `OLLAMA_HOST` - LLM service (default: http://ollama:11434)

### LLM Model
- Uses: `phi3:latest`
- Configured in: `backend/agentic_teams.py`
- Can be changed by updating `call_llm()` method

## Troubleshooting

### Teams Not Suggested
- Check Ollama service is running
- Verify `phi3:latest` model is loaded
- Check backend logs for LLM errors
- Fallback: Uses keyword-based detection

### Workflow Link Not Appearing
- Ensure email was assigned via operator action
- Check `agentic_task_id` field is populated
- Verify workflow task exists in `agentic_tasks` dict

### Migration Issues
- Use manual SQL script if Python script fails
- Check PostgreSQL permissions
- Verify database connection string

## Future Enhancements

Potential improvements for consideration:
1. **Drag-and-Drop UI** - Visual team zones for email dragging
2. **Team Performance Analytics** - Track team response times
3. **Batch Assignment** - Assign multiple emails at once
4. **Team Availability** - Show team workload before assignment
5. **Assignment History** - Log of all team assignments
6. **Workflow Status in List** - Show workflow progress in email list

## Architecture Diagram

```
┌─────────────────┐
│   Email Fetch   │
│   from Mailpit  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Store in DB    │
│  (No workflow)  │
└────────┬────────┘
         │
         v
┌─────────────────┐     ┌──────────────┐
│  LLM Suggests   │────>│  Store       │
│  Team (BG task) │     │  suggestion  │
└─────────────────┘     └──────────────┘
         │
         v
┌─────────────────┐
│  Operator Views │
│  in Mailbox     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Operator Opens │
│  Email Modal    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Operator       │
│  Assigns Team   │
└────────┬────────┘
         │
         v
┌─────────────────┐     ┌──────────────┐
│  Trigger        │────>│  Store       │
│  Agentic Flow   │     │  task_id     │
└────────┬────────┘     └──────────────┘
         │
         v
┌─────────────────┐
│  View Workflow  │
│  Discussion     │
└─────────────────┘
```

## Files Modified

### Backend
- ✅ `backend/models.py` - Added team assignment fields
- ✅ `backend/agentic_teams.py` - Added LLM suggestion function
- ✅ `backend/main.py` - Added API endpoints, auto-suggestion task

### Frontend
- ✅ `frontend/pages/mailbox.html` - Added team badges, assignment UI, workflow links

### Database
- ✅ `backend/migrations/add_team_assignment_fields.sql` - SQL migration
- ✅ `backend/migrations/run_migration.py` - Python migration script

### Documentation
- ✅ `docs/TEAM_ASSIGNMENT_IMPLEMENTATION.md` - This document

## Summary

This implementation provides a complete intelligent team assignment system with:
- ✅ LLM-powered automatic team suggestions
- ✅ Manual operator control over workflow triggering
- ✅ No automatic workflow execution on email arrival
- ✅ Full workflow tracking with direct links
- ✅ Clean, professional UI with Material Icons
- ✅ Comprehensive API for team assignment operations
- ✅ Database migration scripts for deployment

The system ensures human oversight while providing AI assistance, making email routing more efficient without sacrificing control.
