from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import httpx
import os
import uuid
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database import get_db, init_db
from models import Email, WorkflowResult, WorkflowConfig, Team, TeamAgent
from mailpit_client import MailPitClient
from workflows import WorkflowEngine
from llm_service import ollama_service
from wiki_enrichment import email_enricher
from pydantic import BaseModel
from events import broadcaster
from email_fetcher import email_fetcher
from agentic_teams import orchestrator, detect_team_for_email, suggest_team_for_email_llm, TEAMS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mailbox Analysis API", version="1.0.0")

# Global storage for async agentic team tasks
agentic_tasks = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
mailpit_client = MailPitClient()
workflow_engine = WorkflowEngine()

# Employee Directory Configuration
EMPLOYEE_DIRECTORY_HOST = os.getenv("EMPLOYEE_DIRECTORY_HOST", "employee-directory")
EMPLOYEE_DIRECTORY_PORT = os.getenv("EMPLOYEE_DIRECTORY_PORT", "8100")
EMPLOYEE_DIRECTORY_URL = f"http://{EMPLOYEE_DIRECTORY_HOST}:{EMPLOYEE_DIRECTORY_PORT}"

async def lookup_employee_by_email(email: str) -> Optional[dict]:
    """
    Look up employee information from the Employee Directory API
    Returns employee data including mobile, phone, department, etc.
    Returns None if employee not found or on error
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{EMPLOYEE_DIRECTORY_URL}/api/employees/by-email/{email}"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"Employee directory returned status {response.status_code} for {email}")
                return None
    except Exception as e:
        logger.warning(f"Failed to lookup employee {email}: {e}")
        return None

# Pydantic models for API
class EmailResponse(BaseModel):
    id: int
    mailpit_id: Optional[str] = None
    subject: str
    sender: str
    recipient: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime
    is_phishing: bool
    processed: bool
    label: Optional[int] = None  # Ground truth: 1=phishing, 0=legitimate
    phishing_type: Optional[str] = None  # e.g., credential_harvesting, authority_scam, legitimate
    summary: Optional[str] = None
    call_to_actions: Optional[List[str]] = None
    badges: Optional[List[str]] = None
    ui_badges: Optional[List[str]] = None
    quick_reply_drafts: Optional[dict] = None
    llm_processed: Optional[bool] = False
    workflow_results: List[dict] = []
    enriched: Optional[bool] = False
    enriched_data: Optional[dict] = None
    enriched_at: Optional[datetime] = None
    wiki_enriched: Optional[bool] = False
    phone_enriched: Optional[bool] = False
    wiki_enriched_at: Optional[datetime] = None
    phone_enriched_at: Optional[datetime] = None
    suggested_team: Optional[str] = None
    assigned_team: Optional[str] = None
    agentic_task_id: Optional[str] = None
    team_assigned_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkflowResultResponse(BaseModel):
    id: int
    email_id: int
    workflow_name: str
    is_phishing_detected: bool
    confidence_score: int
    risk_indicators: list
    executed_at: datetime

    class Config:
        from_attributes = True

class ProcessEmailRequest(BaseModel):
    email_id: int
    workflows: Optional[List[str]] = None

class TeamAgentRequest(BaseModel):
    role: str
    icon: str
    personality: Optional[str] = None
    responsibilities: Optional[str] = None
    style: Optional[str] = None
    position_order: int = 0
    is_decision_maker: bool = False

class TeamAgentResponse(BaseModel):
    id: int
    team_id: int
    role: str
    icon: str
    personality: Optional[str] = None
    responsibilities: Optional[str] = None
    style: Optional[str] = None
    position_order: int
    is_decision_maker: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TeamRequest(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

class TeamResponse(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    agents: List[TeamAgentResponse] = []

    class Config:
        from_attributes = True

class TeamConfigRequest(BaseModel):
    agents: List[TeamAgentRequest]

@app.on_event("startup")
async def startup_event():
    """Initialize database and start email fetcher on startup"""
    import asyncio

    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    # Auto-start email fetcher in background
    logger.info("Starting email fetcher in background...")
    asyncio.create_task(email_fetcher.start_fetching())
    logger.info("Email fetcher started")

    # Initialize wiki enrichment knowledge base in background (unless disabled)
    if os.getenv("DISABLE_WIKI_ENRICHMENT", "false").lower() != "true":
        logger.info("Starting wiki enrichment initialization in background...")
        asyncio.create_task(email_enricher.initialize())
        logger.info("Wiki enrichment initialization started (loading in background)")
    else:
        logger.info("Wiki enrichment disabled via DISABLE_WIKI_ENRICHMENT env var")

def detect_ui_badges(email: Email) -> List[str]:
    """Detect UI state badges for an email

    Available UI badges: ACTION_REQUIRED, HIGH_PRIORITY, REPLIED, ATTACHMENT, SNOOZED, AI_SUGGESTED

    IMPORTANT: If email is phishing or has risk indicators, ONLY show security-related badges.
    Do not clutter the UI with informational badges when there's a security threat.
    """
    ui_badges = []

    # Check if email has any risk indicators from LLM badges
    has_risk_indicators = False
    if email.badges:
        # Check if any security-related badges are present
        risk_badges = ["RISK", "EXTERNAL", "SUSPICIOUS", "MALICIOUS", "URGENT"]
        has_risk_indicators = any(badge in email.badges for badge in risk_badges)

    # If email is phishing or has risk indicators, ONLY show security badges
    if email.is_phishing or has_risk_indicators:
        # Only show HIGH_PRIORITY for phishing emails that DON'T have explicit risk badges
        # If RISK badge is already present, don't add redundant HIGH_PRIORITY
        if email.is_phishing and not has_risk_indicators:
            ui_badges.append("HIGH_PRIORITY")
        # Do NOT add any other informational badges for risky emails
        return ui_badges

    # For safe emails, show informational badges
    # ACTION_REQUIRED: Email has call-to-actions
    if email.call_to_actions and len(email.call_to_actions) > 0:
        ui_badges.append("ACTION_REQUIRED")

    # AI_SUGGESTED: Email has AI-generated quick reply drafts
    if email.quick_reply_drafts:
        ui_badges.append("AI_SUGGESTED")

    # ATTACHMENT: Would need email metadata - skip for now
    # REPLIED: Would need user action tracking - skip for now
    # SNOOZED: Would need user action tracking - skip for now

    return ui_badges

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Mailbox Analysis API"}

@app.get("/health")
async def health():
    """Dedicated health check endpoint for Docker"""
    return {"status": "healthy", "service": "Mailbox Analysis API"}

@app.get("/api/mailpit/stats")
async def get_mailpit_stats():
    """Get MailPit statistics"""
    try:
        stats = await mailpit_client.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error fetching MailPit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def auto_suggest_teams_for_emails(db: Session):
    """
    Background task to automatically suggest teams for emails that don't have one.
    Uses LLM to intelligently route emails to appropriate teams.
    """
    try:
        # Get emails without suggested team
        emails = db.query(Email).filter(Email.suggested_team == None).limit(50).all()

        logger.info(f"Auto-suggesting teams for {len(emails)} emails")

        for email in emails:
            try:
                # Use LLM to suggest team
                suggested_team = await suggest_team_for_email_llm(
                    email.subject,
                    email.body_text or email.body_html or "",
                    email.sender
                )

                email.suggested_team = suggested_team
                logger.info(f"Suggested team '{suggested_team}' for email {email.id}")

            except Exception as e:
                logger.error(f"Error suggesting team for email {email.id}: {e}")
                continue

        db.commit()
        logger.info(f"Completed team suggestion for {len(emails)} emails")

    except Exception as e:
        logger.error(f"Error in auto_suggest_teams_for_emails: {e}")
        db.rollback()


@app.post("/api/emails/fetch")
async def fetch_emails_from_mailpit(
    background_tasks: BackgroundTasks,
    limit: int = 5000,
    db: Session = Depends(get_db)
):
    """Fetch emails from MailPit and store in database"""
    try:
        messages_data = await mailpit_client.get_messages(limit=limit)
        messages = messages_data.get("messages", [])

        fetched_count = 0
        for msg in messages:
            msg_id = msg.get("ID")

            # Check if email already exists
            existing = db.query(Email).filter(Email.mailpit_id == msg_id).first()
            if existing:
                continue

            # Fetch full message details
            full_msg = await mailpit_client.get_message(msg_id)

            # Fetch headers separately to get custom headers
            headers = await mailpit_client.get_message_headers(msg_id)

            # Extract ground truth labels from custom headers
            label = None
            phishing_type = None

            if "X-Email-Label" in headers:
                try:
                    label = int(headers["X-Email-Label"][0])
                except (ValueError, IndexError):
                    pass

            if "X-Phishing-Type" in headers:
                try:
                    phishing_type = headers["X-Phishing-Type"][0]
                except IndexError:
                    pass

            # Extract email data
            email = Email(
                mailpit_id=msg_id,
                subject=msg.get("Subject", ""),
                sender=msg.get("From", {}).get("Address", ""),
                recipient=", ".join([addr.get("Address", "") for addr in msg.get("To", [])]),
                body_text=full_msg.get("Text", ""),
                body_html=full_msg.get("HTML", ""),
                received_at=datetime.fromisoformat(msg.get("Created", "").replace("Z", "+00:00")),
                label=label,
                phishing_type=phishing_type
            )

            db.add(email)
            fetched_count += 1

        db.commit()

        # Auto-suggest teams for newly fetched emails in background (DISABLED - user preference)
        # if fetched_count > 0:
        #     background_tasks.add_task(auto_suggest_teams_for_emails, db)

        return {
            "status": "success",
            "fetched": fetched_count,
            "total_in_mailpit": messages_data.get("total", 0)
        }

    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/update-bodies")
async def update_email_bodies(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Update body_text for existing emails from MailPit"""
    try:
        # Get emails without body_text
        emails_to_update = db.query(Email).filter(
            (Email.body_text == None) | (Email.body_text == "")
        ).limit(limit).all()

        updated_count = 0
        for email in emails_to_update:
            try:
                # Fetch full message from MailPit
                full_msg = await mailpit_client.get_message(email.mailpit_id)

                # Update body_text and body_html
                email.body_text = full_msg.get("Text", "")
                email.body_html = full_msg.get("HTML", "")

                updated_count += 1

            except Exception as e:
                logger.error(f"Error updating email {email.id}: {e}")
                continue

        db.commit()

        return {
            "status": "success",
            "updated": updated_count,
            "total_without_body": db.query(Email).filter(
                (Email.body_text == None) | (Email.body_text == "")
            ).count()
        }

    except Exception as e:
        logger.error(f"Error updating email bodies: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 50,
    processed: Optional[bool] = None,
    is_phishing: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get emails from database with filters"""
    from sqlalchemy import case, and_

    query = db.query(Email)

    if processed is not None:
        query = query.filter(Email.processed == processed)

    if is_phishing is not None:
        query = query.filter(Email.is_phishing == is_phishing)

    # Sort by analysis completion status:
    # Priority 1: Both processed AND enriched (fully analyzed)
    # Priority 2: Processed only
    # Priority 3: Enriched only
    # Priority 4: Received date (newest first)
    priority = case(
        (and_(Email.processed == True, Email.enriched == True), 0),  # Fully analyzed - highest priority
        (Email.processed == True, 1),                                 # ML analysis done
        (Email.enriched == True, 2),                                  # Wiki enrichment done
        else_=3                                                        # Not processed - lowest priority
    )

    emails = query.order_by(priority, Email.received_at.desc()).offset(skip).limit(limit).all()

    # Convert to response format
    result = []
    for email in emails:
        email_dict = {
            "id": email.id,
            "mailpit_id": email.mailpit_id,
            "subject": email.subject,
            "sender": email.sender,
            "recipient": email.recipient,
            "received_at": email.received_at,
            "is_phishing": email.is_phishing,
            "processed": email.processed,
            "label": email.label,
            "phishing_type": email.phishing_type,
            "summary": email.summary,
            "call_to_actions": email.call_to_actions,
            "badges": email.badges,
            "ui_badges": email.ui_badges,
            "quick_reply_drafts": email.quick_reply_drafts,
            "llm_processed": email.llm_processed,
            "workflow_results": [
                {
                    "id": wr.id,
                    "workflow_name": wr.workflow_name,
                    "is_phishing_detected": wr.is_phishing_detected,
                    "confidence_score": wr.confidence_score,
                    "risk_indicators": wr.risk_indicators,
                    "result": wr.result
                }
                for wr in email.workflow_results
            ],
            "body_text": email.body_text,
            "body_html": email.body_html,
            "enriched": email.enriched,
            "enriched_data": email.enriched_data,
            "enriched_at": email.enriched_at,
            "wiki_enriched": email.wiki_enriched,
            "phone_enriched": email.phone_enriched,
            "suggested_team": email.suggested_team,
            "assigned_team": email.assigned_team,
            "agentic_task_id": email.agentic_task_id,
            "team_assigned_at": email.team_assigned_at
        }
        result.append(email_dict)

    return result

@app.get("/api/emails/{email_id}")
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get single email with workflow results"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": email.id,
        "mailpit_id": email.mailpit_id,
        "subject": email.subject,
        "sender": email.sender,
        "recipient": email.recipient,
        "body_text": email.body_text,
        "body_html": email.body_html,
        "received_at": email.received_at,
        "is_phishing": email.is_phishing,
        "processed": email.processed,
        "summary": email.summary,
        "call_to_actions": email.call_to_actions,
        "badges": email.badges,
        "ui_badges": email.ui_badges,
        "quick_reply_drafts": email.quick_reply_drafts,
        "llm_processed": email.llm_processed,
        "enriched": email.enriched,
        "enriched_data": email.enriched_data,
        "enriched_at": email.enriched_at,
        "wiki_enriched": email.wiki_enriched,
        "phone_enriched": email.phone_enriched,
        "suggested_team": email.suggested_team,
        "assigned_team": email.assigned_team,
        "agentic_task_id": email.agentic_task_id,
        "team_assigned_at": email.team_assigned_at,
        "workflow_results": [
            {
                "id": wr.id,
                "workflow_name": wr.workflow_name,
                "is_phishing_detected": wr.is_phishing_detected,
                "confidence_score": wr.confidence_score,
                "risk_indicators": wr.risk_indicators,
                "result": wr.result,
                "executed_at": wr.executed_at.isoformat()
            }
            for wr in email.workflow_results
        ]
    }

@app.delete("/api/emails/{email_id}")
async def delete_email(email_id: int, db: Session = Depends(get_db)):
    """Delete an email and its associated workflow results"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        # Delete associated workflow results first (due to foreign key constraints)
        db.query(WorkflowResult).filter(WorkflowResult.email_id == email_id).delete()

        # Delete the email
        db.delete(email)
        db.commit()

        logger.info(f"Deleted email {email_id} and associated workflow results")
        return {"status": "success", "message": f"Email {email_id} deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")

@app.post("/api/emails/{email_id}/process")
async def process_email(
    email_id: int,
    workflows: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """Process an email through phishing detection workflows and LLM analysis"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_data = {
        "subject": email.subject,
        "sender": email.sender,
        "body_text": email.body_text or "",
        "body_html": email.body_html or ""
    }

    # Step 1: Run workflows
    workflow_results = await workflow_engine.run_all_workflows(email_data)

    # Delete existing workflow results for this email to avoid duplicates
    db.query(WorkflowResult).filter(WorkflowResult.email_id == email.id).delete()

    # Store results
    phishing_votes = 0
    total_confidence = 0

    # Track high-precision models for ensemble
    naive_bayes_phishing = False
    fine_tuned_llm_phishing = False

    for result in workflow_results:
        workflow_result = WorkflowResult(
            email_id=email.id,
            workflow_name=result["workflow"],
            result=result,
            is_phishing_detected=result["is_phishing_detected"],
            confidence_score=result["confidence_score"],
            risk_indicators=result["risk_indicators"]
        )
        db.add(workflow_result)

        if result["is_phishing_detected"]:
            phishing_votes += 1
        total_confidence += result["confidence_score"]

        # Track high-precision models
        if "Naive Bayes" in result["workflow"] and result["is_phishing_detected"]:
            naive_bayes_phishing = True
        if "Fine-tuned LLM" in result["workflow"] and result["is_phishing_detected"]:
            fine_tuned_llm_phishing = True

    # Update email status
    email.processed = True
    # Use "High Precision" ensemble strategy (NB + LLM with OR logic)
    # This strategy achieved 82.10% accuracy and 81.90% F1-score in testing
    # If either high-precision model detects phishing, flag it
    email.is_phishing = naive_bayes_phishing or fine_tuned_llm_phishing

    # Step 2: Process with LLM
    llm_data = {}
    try:
        llm_result = await ollama_service.process_email(
            email.subject or "",
            email.body_text or "",
            is_phishing=email.is_phishing
        )

        badges = await ollama_service.detect_email_badges(
            email.subject or "",
            email.body_text or "",
            email.sender or "",
            email.is_phishing
        )

        quick_reply_drafts = await ollama_service.generate_quick_reply_drafts(
            email.subject or "",
            email.body_text or "",
            email.sender or ""
        )

        email.summary = llm_result["summary"]
        email.call_to_actions = llm_result["call_to_actions"]
        email.badges = badges
        email.quick_reply_drafts = quick_reply_drafts
        email.llm_processed = True
        email.llm_processed_at = datetime.utcnow()

        # Detect and set UI badges
        email.ui_badges = detect_ui_badges(email)

        llm_data = {
            "summary": email.summary,
            "badges": badges,
            "quick_reply_drafts": quick_reply_drafts,
            "ui_badges": email.ui_badges
        }

    except Exception as llm_error:
        logger.error(f"Error processing email {email_id} with LLM: {llm_error}")
        # Continue even if LLM processing fails

    db.commit()

    return {
        "status": "success",
        "email_id": email_id,
        "is_phishing": email.is_phishing,
        "workflows_run": len(workflow_results),
        "average_confidence": total_confidence / len(workflow_results) if workflow_results else 0,
        "results": workflow_results,
        "llm_data": llm_data
    }

@app.post("/api/emails/process-all")
async def process_all_unprocessed_emails(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process all unprocessed emails with workflow analysis and LLM processing"""
    unprocessed = db.query(Email).filter(Email.processed == False).all()

    async def process_batch():
        for email in unprocessed:
            try:
                # Step 1: Run workflow analysis
                email_data = {
                    "subject": email.subject,
                    "sender": email.sender,
                    "body_text": email.body_text or "",
                    "body_html": email.body_html or ""
                }

                workflow_results = await workflow_engine.run_all_workflows(email_data)

                phishing_votes = 0
                for result in workflow_results:
                    workflow_result = WorkflowResult(
                        email_id=email.id,
                        workflow_name=result["workflow"],
                        result=result,
                        is_phishing_detected=result["is_phishing_detected"],
                        confidence_score=result["confidence_score"],
                        risk_indicators=result["risk_indicators"]
                    )
                    db.add(workflow_result)

                    if result["is_phishing_detected"]:
                        phishing_votes += 1

                email.processed = True
                email.is_phishing = phishing_votes >= len(workflow_results) / 2

                # Broadcast event for workflow processing
                await broadcaster.broadcast("email_processed", {
                    "email_id": email.id,
                    "is_phishing": email.is_phishing,
                    "subject": email.subject,
                    "processed_count": unprocessed.index(email) + 1,
                    "total_count": len(unprocessed)
                })

                # Step 2: Process with LLM (summary, badges, quick replies)
                try:
                    llm_result = await ollama_service.process_email(
                        email.subject or "",
                        email.body_text or "",
                        is_phishing=email.is_phishing
                    )

                    # Detect badges
                    badges = await ollama_service.detect_email_badges(
                        email.subject or "",
                        email.body_text or "",
                        email.sender or "",
                        email.is_phishing
                    )

                    # Generate quick reply drafts
                    quick_reply_drafts = await ollama_service.generate_quick_reply_drafts(
                        email.subject or "",
                        email.body_text or "",
                        email.sender or ""
                    )

                    email.summary = llm_result["summary"]
                    email.call_to_actions = llm_result["call_to_actions"]
                    email.badges = badges
                    email.quick_reply_drafts = quick_reply_drafts
                    email.llm_processed = True
                    email.llm_processed_at = datetime.utcnow()

                    # Detect and set UI badges
                    email.ui_badges = detect_ui_badges(email)

                    # Broadcast event for LLM processing
                    await broadcaster.broadcast("email_llm_processed", {
                        "email_id": email.id,
                        "badges": badges,
                        "ui_badges": email.ui_badges,
                        "subject": email.subject,
                        "processed_count": unprocessed.index(email) + 1,
                        "total_count": len(unprocessed)
                    })

                except Exception as llm_error:
                    logger.error(f"Error processing email {email.id} with LLM: {llm_error}")
                    # Continue even if LLM processing fails

            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")

        db.commit()

        # Broadcast completion event
        await broadcaster.broadcast("batch_complete", {
            "total_processed": len(unprocessed)
        })

    background_tasks.add_task(process_batch)

    return {
        "status": "processing",
        "count": len(unprocessed),
        "message": "Processing emails with workflow analysis and LLM in background"
    }

@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_emails = db.query(Email).count()
    processed_emails = db.query(Email).filter(Email.processed == True).count()
    phishing_emails = db.query(Email).filter(Email.is_phishing == True).count()
    legitimate_emails = db.query(Email).filter(
        Email.processed == True,
        Email.is_phishing == False
    ).count()

    # Count emails by badge type
    all_emails = db.query(Email).filter(Email.llm_processed == True).all()
    badge_counts = {
        "MEETING": 0,
        "RISK": 0,
        "EXTERNAL": 0,
        "AUTOMATED": 0,
        "VIP": 0,
        "FOLLOW_UP": 0,
        "NEWSLETTER": 0,
        "FINANCE": 0
    }

    for email in all_emails:
        if email.badges:
            for badge in email.badges:
                if badge in badge_counts:
                    badge_counts[badge] += 1

    return {
        "total_emails": total_emails,
        "processed_emails": processed_emails,
        "unprocessed_emails": total_emails - processed_emails,
        "phishing_detected": phishing_emails,
        "legitimate_emails": legitimate_emails,
        "phishing_percentage": (phishing_emails / processed_emails * 100) if processed_emails > 0 else 0,
        "badge_counts": badge_counts,
        "llm_processed": len(all_emails)
    }

@app.get("/api/workflows")
async def get_workflows():
    """Get available workflows"""
    return {
        "workflows": [
            {
                "name": workflow.name,
                "description": workflow.__class__.__doc__
            }
            for workflow in workflow_engine.workflows
        ]
    }

@app.get("/api/events")
async def event_stream():
    """Server-Sent Events (SSE) endpoint for real-time updates"""
    return StreamingResponse(
        broadcaster.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/fetcher/start")
async def start_email_fetcher(background_tasks: BackgroundTasks):
    """Start the scheduled email fetcher"""
    if email_fetcher.is_running:
        return {
            "status": "already_running",
            "message": "Email fetcher is already running"
        }

    # Start fetcher in background
    background_tasks.add_task(email_fetcher.start_fetching)

    return {
        "status": "started",
        "message": "Email fetcher started",
        "batch_size": 100,
        "delay_seconds": 10
    }

@app.post("/api/fetcher/stop")
async def stop_email_fetcher():
    """Stop the scheduled email fetcher"""
    await email_fetcher.stop_fetching()
    return {
        "status": "stopped",
        "message": "Email fetcher stopped"
    }

@app.get("/api/fetcher/status")
async def get_fetcher_status():
    """Get the status of the email fetcher"""
    return email_fetcher.get_status()

@app.on_event("startup")
async def startup_llm():
    """Initialize LLM on startup - non-blocking"""
    async def init_ollama():
        try:
            logger.info("Initializing Ollama service...")
            model_loaded = await ollama_service.ensure_model_loaded()
            if model_loaded:
                logger.info(f"Ollama model '{ollama_service.model}' is ready")
            else:
                logger.warning(f"Ollama model '{ollama_service.model}' could not be loaded. LLM features may not work properly.")
        except Exception as e:
            logger.error(f"Error initializing Ollama on startup: {e}")
            logger.warning("LLM features may not work properly. Check Ollama service status.")

    # Run in background to avoid blocking startup
    asyncio.create_task(init_ollama())

@app.on_event("startup")
async def startup_mcp():
    """Initialize MCP servers on startup - non-blocking"""
    async def init_mcp_servers():
        try:
            logger.info("Initializing MCP servers for fraud detection...")
            from mcp_client import initialize_mcp_servers
            await initialize_mcp_servers()
            logger.info("MCP servers initialization complete")
        except Exception as e:
            logger.error(f"Error initializing MCP servers on startup: {e}")
            logger.warning("MCP features (DuckDuckGo fallback) may not work. Serper and mock fallbacks will still work.")

    # Run in background to avoid blocking startup
    import asyncio
    asyncio.create_task(init_mcp_servers())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/api/emails/{email_id}/process-llm")
async def process_email_with_llm(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Process an email with LLM: generate summary, extract CTAs, detect badges, and create quick reply drafts"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        # Process with LLM (only extract CTAs from safe emails)
        result = await ollama_service.process_email(
            email.subject or "",
            email.body_text or "",
            is_phishing=email.is_phishing
        )

        # Detect badges
        badges = await ollama_service.detect_email_badges(
            email.subject or "",
            email.body_text or "",
            email.sender or "",
            email.is_phishing
        )

        # Generate quick reply drafts
        quick_reply_drafts = await ollama_service.generate_quick_reply_drafts(
            email.subject or "",
            email.body_text or "",
            email.sender or ""
        )

        # Update email
        email.summary = result["summary"]
        email.call_to_actions = result["call_to_actions"]
        email.badges = badges
        email.quick_reply_drafts = quick_reply_drafts
        email.llm_processed = True
        email.llm_processed_at = datetime.utcnow()

        db.commit()

        return {
            "status": "success",
            "email_id": email_id,
            "summary": email.summary,
            "call_to_actions": email.call_to_actions,
            "badges": email.badges,
            "quick_reply_drafts": email.quick_reply_drafts
        }

    except Exception as e:
        logger.error(f"Error processing email {email_id} with LLM: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/enrich")
async def enrich_email_with_wiki(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Enrich email with wiki context using RAG - ONLY for non-phishing emails"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # IMPORTANT: Only enrich safe (non-phishing) emails
    if email.is_phishing:
        # Mark as enriched even though we skipped it (the enrichment process completed)
        email.enriched = True
        email.enriched_at = datetime.utcnow()
        email.enriched_data = {
            "enriched_keywords": [],
            "relevant_pages": []
        }
        email.wiki_enriched = False
        email.phone_enriched = False
        db.commit()

        return {
            "status": "skipped",
            "email_id": email_id,
            "reason": "Enrichment is only available for safe (non-phishing) emails",
            "enriched_keywords": [],
            "relevant_pages": []
        }

    try:
        # Enrich email with wiki context
        enrichment_data = await email_enricher.enrich_email(
            email.subject or "",
            email.body_text or ""
        )

        # Look up sender in employee directory
        sender_employee_data = None
        if email.sender:
            sender_employee_data = await lookup_employee_by_email(email.sender)
            if sender_employee_data:
                logger.info(f"Found sender employee data for {email.sender}: {sender_employee_data.get('first_name')} {sender_employee_data.get('last_name')}")

        # Look up recipient in employee directory
        recipient_employee_data = None
        if email.recipient:
            recipient_employee_data = await lookup_employee_by_email(email.recipient)
            if recipient_employee_data:
                logger.info(f"Found recipient employee data for {email.recipient}: {recipient_employee_data.get('first_name')} {recipient_employee_data.get('last_name')}")

        # Combine wiki enrichment with employee directory data
        enrichment_data["sender_employee"] = sender_employee_data
        enrichment_data["recipient_employee"] = recipient_employee_data

        # Set enrichment success tags - ONLY when actual data is found
        has_wiki_keywords = bool(enrichment_data.get("enriched_keywords"))  # Only true if keywords were actually matched
        has_phone_data = bool(sender_employee_data or recipient_employee_data)  # True if employee data was found

        # Update email with enrichment data
        email.enriched_data = enrichment_data
        email.enriched = True
        email.enriched_at = datetime.utcnow()

        # Set flags and timestamps only when actual data is found
        email.wiki_enriched = has_wiki_keywords
        email.phone_enriched = has_phone_data

        if has_wiki_keywords:
            email.wiki_enriched_at = datetime.utcnow()

        if has_phone_data:
            email.phone_enriched_at = datetime.utcnow()

        db.commit()

        logger.info(f"Email {email_id} enriched - Wiki keywords: {has_wiki_keywords} ({len(enrichment_data.get('enriched_keywords', []))} found), Phone: {has_phone_data}")

        return {
            "status": "success",
            "email_id": email_id,
            "enriched_keywords": enrichment_data.get("enriched_keywords", []),
            "relevant_pages": enrichment_data.get("relevant_pages", []),
            "sender_employee": sender_employee_data,
            "recipient_employee": recipient_employee_data,
            "wiki_enriched": has_wiki_keywords,
            "phone_enriched": has_phone_data
        }

    except Exception as e:
        logger.error(f"Error enriching email {email_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/process-all-llm")
async def process_all_emails_with_llm(
    background_tasks: BackgroundTasks,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Process all unprocessed emails with LLM in background"""
    unprocessed = db.query(Email).filter(Email.llm_processed == False).limit(limit).all()

    async def process_batch():
        for email in unprocessed:
            try:
                result = await ollama_service.process_email(
                    email.subject or "",
                    email.body_text or "",
                    is_phishing=email.is_phishing
                )

                # Detect badges
                badges = await ollama_service.detect_email_badges(
                    email.subject or "",
                    email.body_text or "",
                    email.sender or "",
                    email.is_phishing
                )

                # Generate quick reply drafts
                quick_reply_drafts = await ollama_service.generate_quick_reply_drafts(
                    email.subject or "",
                    email.body_text or "",
                    email.sender or ""
                )

                email.summary = result["summary"]
                email.call_to_actions = result["call_to_actions"]
                email.badges = badges
                email.quick_reply_drafts = quick_reply_drafts
                email.llm_processed = True
                email.llm_processed_at = datetime.utcnow()

                # Broadcast event for LLM processing
                await broadcaster.broadcast("email_llm_processed", {
                    "email_id": email.id,
                    "badges": badges,
                    "subject": email.subject,
                    "processed_count": unprocessed.index(email) + 1,
                    "total_count": len(unprocessed)
                })

            except Exception as e:
                logger.error(f"Error processing email {email.id} with LLM: {e}")

        db.commit()

        # Broadcast completion event
        await broadcaster.broadcast("llm_batch_complete", {
            "total_processed": len(unprocessed)
        })

    background_tasks.add_task(process_batch)

    return {
        "status": "processing",
        "count": len(unprocessed),
        "message": f"Processing {len(unprocessed)} emails with LLM in background"
    }

@app.get("/api/daily-summary")
async def get_daily_summary(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get aggregated summary for emails from last N hours"""
    try:
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        # Get emails from last N hours
        recent_emails = db.query(Email).filter(
            Email.received_at >= time_threshold,
            Email.llm_processed == True
        ).all()

        if not recent_emails:
            return {
                "period_hours": hours,
                "total_emails": 0,
                "aggregate_summary": "No emails processed in the selected time period",
                "consolidated_ctas": [],
                "top_senders": []
            }

        # Extract summaries and CTAs
        summaries = [email.summary for email in recent_emails if email.summary]

        # Normalize CTAs - handle both string arrays and dict arrays
        all_ctas = []
        for email in recent_emails:
            if email.call_to_actions:
                ctas = email.call_to_actions
                # Convert [{"action": "text"}] to ["text"]
                if isinstance(ctas, list) and len(ctas) > 0:
                    if isinstance(ctas[0], dict) and "action" in ctas[0]:
                        normalized = [item["action"] for item in ctas if isinstance(item, dict) and "action" in item]
                        all_ctas.append(normalized)
                    elif isinstance(ctas[0], str):
                        all_ctas.append(ctas)

        # Generate aggregate summary
        aggregate_summary = await ollama_service.aggregate_summaries(summaries)

        # Consolidate CTAs
        consolidated_ctas = await ollama_service.aggregate_call_to_actions(all_ctas) if all_ctas else []

        # Get top senders
        sender_counts = {}
        for email in recent_emails:
            sender = email.sender
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "period_hours": hours,
            "total_emails": len(recent_emails),
            "processed_emails": len([e for e in recent_emails if e.llm_processed]),
            "aggregate_summary": aggregate_summary,
            "consolidated_ctas": consolidated_ctas,
            "top_senders": [{"sender": s, "count": c} for s, c in top_senders],
            "phishing_detected": len([e for e in recent_emails if e.is_phishing]),
            "time_range": {
                "from": time_threshold.isoformat(),
                "to": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inbox-digest")
async def get_inbox_digest(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get emails grouped by badges for Daily Inbox Digest view"""
    try:
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        # Get recent emails that have been LLM processed
        recent_emails = db.query(Email).filter(
            Email.received_at >= time_threshold,
            Email.llm_processed == True
        ).order_by(Email.received_at.desc()).all()

        # Group emails by primary badge
        grouped = {
            "MEETING": [],
            "RISK": [],
            "EXTERNAL": [],
            "AUTOMATED": [],
            "VIP": [],
            "FOLLOW_UP": [],
            "NEWSLETTER": [],
            "FINANCE": [],
            "OTHER": []
        }

        total_today = len(recent_emails)

        for email in recent_emails:
            email_data = {
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "summary": email.summary,
                "badges": email.badges or [],
                "received_at": email.received_at.isoformat(),
                "is_phishing": email.is_phishing,
                "call_to_actions": email.call_to_actions or []
            }

            # Add to primary badge group (first badge takes priority)
            if email.badges and len(email.badges) > 0:
                primary_badge = email.badges[0]
                if primary_badge in grouped:
                    grouped[primary_badge].append(email_data)
                else:
                    grouped["OTHER"].append(email_data)
            else:
                grouped["OTHER"].append(email_data)

        # Calculate badge counts
        badge_counts = {
            badge: len(emails) for badge, emails in grouped.items() if len(emails) > 0
        }

        return {
            "period_hours": hours,
            "total_today": total_today,
            "badge_counts": badge_counts,
            "grouped_emails": grouped,
            "time_range": {
                "from": time_threshold.isoformat(),
                "to": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error generating inbox digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AGENTIC TEAMS ENDPOINTS
# ============================================================================

@app.get("/api/agentic/teams")
async def get_available_teams(db: Session = Depends(get_db)):
    """Get list of all available virtual bank teams from database"""
    teams = db.query(Team).filter(Team.is_active == True).all()

    # If no teams in database, return hardcoded TEAMS as fallback
    if not teams:
        teams_list = []
        for team_key, team_data in TEAMS.items():
            teams_list.append({
                "key": team_key,
                "name": team_data["name"],
                "agent_count": len(team_data["agents"]),
                "agents": [
                    {
                        "role": agent["role"],
                        "icon": agent["icon"],
                        "personality": agent.get("personality", ""),
                        "responsibilities": agent["responsibilities"],
                        "style": agent.get("style", "")
                    }
                    for agent in team_data["agents"]
                ]
            })
        return {"teams": teams_list}

    # Return teams from database
    teams_list = []
    for team in teams:
        teams_list.append({
            "id": team.id,
            "key": team.key,
            "name": team.name,
            "description": team.description,
            "icon": team.icon,
            "agent_count": len(team.agents),
            "agents": [
                {
                    "id": agent.id,
                    "role": agent.role,
                    "icon": agent.icon,
                    "personality": agent.personality,
                    "responsibilities": agent.responsibilities,
                    "style": agent.style,
                    "position_order": agent.position_order,
                    "is_decision_maker": agent.is_decision_maker
                }
                for agent in team.agents
            ]
        })
    return {"teams": teams_list}

@app.get("/api/agentic/teams/{team_key}/config")
async def get_team_config(team_key: str, db: Session = Depends(get_db)):
    """Get detailed configuration for a specific team"""
    team = db.query(Team).filter(Team.key == team_key, Team.is_active == True).first()

    if not team:
        # Fallback to hardcoded TEAMS
        if team_key in TEAMS:
            team_data = TEAMS[team_key]
            return {
                "key": team_key,
                "name": team_data["name"],
                "agents": [
                    {
                        "role": agent["role"],
                        "icon": agent["icon"],
                        "personality": agent.get("personality", ""),
                        "responsibilities": agent["responsibilities"],
                        "style": agent.get("style", "")
                    }
                    for agent in team_data["agents"]
                ]
            }
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamResponse.from_orm(team)

@app.post("/api/agentic/teams/{team_key}/config")
async def save_team_config(team_key: str, config: TeamConfigRequest, db: Session = Depends(get_db)):
    """Save team configuration"""
    team = db.query(Team).filter(Team.key == team_key).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Delete existing agents
    db.query(TeamAgent).filter(TeamAgent.team_id == team.id).delete()

    # Add new agents
    for agent_data in config.agents:
        agent = TeamAgent(
            team_id=team.id,
            role=agent_data.role,
            icon=agent_data.icon,
            personality=agent_data.personality,
            responsibilities=agent_data.responsibilities,
            style=agent_data.style,
            position_order=agent_data.position_order,
            is_decision_maker=agent_data.is_decision_maker
        )
        db.add(agent)

    team.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(team)

    return {"status": "success", "message": "Team configuration saved successfully"}

@app.post("/api/agentic/teams")
async def create_team(team: TeamRequest, db: Session = Depends(get_db)):
    """Create a new team"""
    # Check if team key already exists
    existing_team = db.query(Team).filter(Team.key == team.key).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team with this key already exists")

    new_team = Team(
        key=team.key,
        name=team.name,
        description=team.description,
        icon=team.icon,
        is_active=team.is_active
    )
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return TeamResponse.from_orm(new_team)

@app.put("/api/agentic/teams/{team_key}")
async def update_team(team_key: str, team: TeamRequest, db: Session = Depends(get_db)):
    """Update team metadata"""
    existing_team = db.query(Team).filter(Team.key == team_key).first()

    if not existing_team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing_team.name = team.name
    existing_team.description = team.description
    existing_team.icon = team.icon
    existing_team.is_active = team.is_active
    existing_team.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(existing_team)

    return TeamResponse.from_orm(existing_team)

@app.delete("/api/agentic/teams/{team_key}")
async def delete_team(team_key: str, db: Session = Depends(get_db)):
    """Delete a team (soft delete by setting is_active to false)"""
    team = db.query(Team).filter(Team.key == team_key).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team.is_active = False
    team.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Team deleted successfully"}


async def run_agentic_workflow_background(task_id: str, email_id: int, team: str, email_subject: str, email_body: str, email_sender: str):
    """Background task to run agentic team discussion with real-time updates"""
    try:
        logger.info(f"[Task {task_id}] Starting agentic workflow for email {email_id} with team '{team}'")

        # Create database session for this background task
        from database import SessionLocal
        db = SessionLocal()

        # Update status to processing
        agentic_tasks[task_id]["status"] = "processing"
        agentic_tasks[task_id]["team"] = team

        # Initialize result structure for real-time updates
        agentic_tasks[task_id]["result"] = {
            "status": "processing",
            "email_id": email_id,
            "team": team,
            "team_name": TEAMS[team]["name"],
            "discussion": {
                "messages": [],
                "status": "processing",
                "team": team,
                "team_name": TEAMS[team]["name"],
                "email_id": email_id
            }
        }

        # Callback to update task with new messages in real-time
        async def on_message(message, all_messages):
            """Update task status as each agent speaks"""
            logger.info(f"[Task {task_id}] Agent spoke: {message['role']}")
            agentic_tasks[task_id]["result"]["discussion"]["messages"] = all_messages.copy()

            # Broadcast message via SSE for real-time updates
            await broadcaster.broadcast("agentic_message", {
                "task_id": task_id,
                "message": message,
                "total_messages": len(all_messages),
                "status": "processing"
            })

        # Run the team discussion with real-time callback (2 rounds for faster CPU processing)
        result = await orchestrator.run_team_discussion(
            email_id=email_id,
            email_subject=email_subject,
            email_body=email_body,
            email_sender=email_sender,
            team=team,
            max_rounds=2,
            on_message_callback=on_message,
            db=db
        )

        # Store the final result
        agentic_tasks[task_id]["status"] = "completed"
        agentic_tasks[task_id]["result"] = {
            "status": "success",
            "email_id": email_id,
            "team": team,
            "team_name": result["team_name"],
            "discussion": result
        }

        # Save result to database for persistence across restarts
        # Using the same db session created at the beginning
        try:
            workflow_result = WorkflowResult(
                email_id=email_id,
                workflow_name=f"agentic_{team}_{task_id}",
                result=agentic_tasks[task_id]["result"],
                is_phishing_detected=False,
                confidence_score=100,
                risk_indicators=[],
                executed_at=datetime.now()
            )
            db.add(workflow_result)
            db.commit()
            logger.info(f"[Task {task_id}] Saved result to database")
        except Exception as db_error:
            logger.error(f"[Task {task_id}] Failed to save to database: {db_error}")
            db.rollback()

        # Broadcast completion via SSE
        await broadcaster.broadcast("agentic_complete", {
            "task_id": task_id,
            "status": "completed",
            "result": agentic_tasks[task_id]["result"]
        })

        logger.info(f"[Task {task_id}] Completed agentic workflow for email {email_id}")

    except Exception as e:
        logger.error(f"[Task {task_id}] Error in agentic workflow: {e}")
        agentic_tasks[task_id]["status"] = "failed"
        agentic_tasks[task_id]["error"] = str(e)
    finally:
        # Close database session
        if 'db' in locals():
            db.close()


@app.post("/api/agentic/emails/{email_id}/process")
async def process_email_with_agentic_team(
    email_id: int,
    team: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Start processing an email with a virtual bank team (async).
    Returns immediately with a task_id for polling.
    """
    try:
        # Get email from database
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        # Auto-detect team if not specified
        if not team:
            team = detect_team_for_email(email.subject, email.body_text or email.body_html)
            logger.info(f"Auto-detected team '{team}' for email {email_id}")

        # Validate team
        if team not in TEAMS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team '{team}'. Valid teams: {list(TEAMS.keys())}"
            )

        # Create task ID
        task_id = str(uuid.uuid4())

        # Initialize task status
        agentic_tasks[task_id] = {
            "status": "pending",
            "email_id": email_id,
            "team": team,
            "created_at": datetime.now().isoformat()
        }

        # Update email record with task_id and assigned_team
        email.assigned_team = team
        email.agentic_task_id = task_id
        email.team_assigned_at = datetime.now()
        db.commit()

        # Start background task
        asyncio.create_task(run_agentic_workflow_background(
            task_id=task_id,
            email_id=email.id,
            team=team,
            email_subject=email.subject,
            email_body=email.body_text or email.body_html,
            email_sender=email.sender
        ))

        logger.info(f"Started agentic workflow task {task_id} for email {email_id}")

        return {
            "status": "started",
            "task_id": task_id,
            "email_id": email_id,
            "team": team
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting agentic workflow for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agentic/tasks/{task_id}")
async def get_agentic_task_status(task_id: str, db: Session = Depends(get_db)):
    """Poll for agentic task status and results"""
    # First check in-memory cache
    if task_id in agentic_tasks:
        task = agentic_tasks[task_id]
        response = {
            "task_id": task_id,
            "status": task["status"],
            "email_id": task["email_id"],
            "team": task.get("team"),
            "created_at": task["created_at"]
        }
    else:
        # Task not in memory, check database for completed results
        logger.info(f"Task {task_id} not in memory, checking database...")
        email = db.query(Email).filter(Email.agentic_task_id == task_id).first()

        if not email:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Get workflow result from database
        workflow_result = db.query(WorkflowResult).filter(
            WorkflowResult.email_id == email.id,
            WorkflowResult.workflow_name.like(f"%{task_id}%")
        ).order_by(WorkflowResult.executed_at.desc()).first()

        if workflow_result and workflow_result.result:
            # Return stored result
            response = {
                "task_id": task_id,
                "status": "completed",
                "email_id": email.id,
                "team": email.assigned_team,
                "created_at": workflow_result.executed_at.isoformat(),
                "result": workflow_result.result
            }
            logger.info(f"Loaded task {task_id} from database")
        else:
            # Email exists but no workflow result stored
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} result not available. Please run analysis again."
            )

    # Add result if task is in memory and has result data
    if task_id in agentic_tasks:
        task = agentic_tasks[task_id]
        if task["status"] == "completed" or task["status"] == "processing":
            if "result" in task:
                response["result"] = task["result"]
        elif task["status"] == "failed":
            response["error"] = task.get("error", "Unknown error")

    return response


@app.post("/api/agentic/direct-query")
async def create_direct_query_task(request: dict, db: Session = Depends(get_db)):
    """
    Create a direct query task without an email
    Request body: {"team": "investments", "query": "I want a complete analysis for stock Apple"}
    """
    try:
        team = request.get("team")
        query = request.get("query", "")

        if not team or not query:
            raise HTTPException(status_code=400, detail="team and query are required")

        # Validate team
        if team not in TEAMS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team '{team}'. Valid teams: {list(TEAMS.keys())}"
            )

        # Create Email record in database for persistence
        email = Email(
            mailpit_id=None,  # No MailPit ID for direct queries
            subject=f"📊 Direct Query: {query[:100]}",
            sender="Direct User Query",
            recipient=TEAMS[team]["name"],
            body_text=query,
            body_html="",
            received_at=datetime.now(),
            assigned_team=team,  # Assign to team immediately
            team_assigned_at=datetime.now(),
            is_phishing=False,
            processed=False,
            llm_processed=False
        )
        db.add(email)
        db.commit()
        db.refresh(email)

        # Create task ID
        task_id = str(uuid.uuid4())

        # Update email with task_id
        email.agentic_task_id = task_id
        db.commit()

        # Initialize task status
        agentic_tasks[task_id] = {
            "status": "pending",
            "email_id": email.id,  # Link to database record
            "team": team,
            "query": query,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

        # Start background task for agentic workflow
        asyncio.create_task(run_agentic_workflow_background(
            task_id=task_id,
            email_id=email.id,  # Pass database ID
            team=team,
            email_subject=email.subject,
            email_body=query,
            email_sender="Direct User Query"
        ))

        logger.info(f"Created direct query task {task_id} for team '{team}' with email_id {email.id}")

        return {
            "status": "created",
            "task_id": task_id,
            "email_id": email.id,  # Return email ID
            "team": team,
            "query": query
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating direct query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agentic/task/{task_id}/chat")
async def send_chat_message_to_team(task_id: str, request: dict):
    """
    Send a chat message to the team and get a response
    Request body: {"message": "What about the company's debt levels?"}
    """
    try:
        message = request.get("message", "").strip()

        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        if task_id not in agentic_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = agentic_tasks[task_id]
        team = task.get("team")

        if not team or team not in TEAMS:
            raise HTTPException(status_code=400, detail="Invalid team")

        # Import orchestrator for LLM calls
        from agentic_teams import orchestrator, TEAMS as BACKEND_TEAMS

        # Add user message to investment workflow context if team is investments
        if team == "investments":
            from investment_workflow import investment_workflow
            investment_workflow.add_user_message(message)

        # Select an appropriate agent to respond (use first agent in team)
        team_info = BACKEND_TEAMS[team]
        agent = team_info["agents"][0]  # First agent responds to chat

        # Add to task messages
        if "messages" not in task:
            task["messages"] = []

        # User message
        user_msg = {
            "role": "You",
            "icon": "👤",
            "text": message,
            "timestamp": datetime.now().isoformat()
        }
        task["messages"].append(user_msg)

        # Broadcast user message via SSE
        await broadcast_sse_event({
            "type": "agentic_chat_user",
            "task_id": task_id,
            "message": user_msg
        })

        # Get analysis context from task result
        analysis_context = ""
        if "result" in task and "discussion" in task["result"]:
            messages = task["result"]["discussion"].get("messages", [])
            # Include last 3-5 messages as context
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            if recent_messages:
                analysis_context = "\n\nPREVIOUS ANALYSIS CONTEXT:\n"
                for msg in recent_messages:
                    role = msg.get("role", "Unknown")
                    text = msg.get("text", "")[:500]  # Limit length
                    analysis_context += f"{role}: {text}\n\n"

        # Create agent-specific prompt for chat response
        system_prompt = f"""You are a {agent['role']} at a Swiss bank. You are part of the {team_info['name']} team.

Your personality: {agent['personality']}
Your responsibilities: {agent['responsibilities']}
Your communication style: {agent['style']}

You are having a conversation with a user who asked a question about an analysis your team just completed.
Use the previous analysis context to inform your response. Be specific and reference actual findings from the analysis.
Keep your response concise but informative (3-5 sentences)."""

        user_prompt = f"""{analysis_context}

CURRENT USER QUESTION: {message}

Provide a helpful and professional response based on your role, expertise, and the analysis context above.
Reference specific findings or data points from the analysis when relevant."""

        # Call LLM
        response_text = await orchestrator.call_llm(user_prompt, system_prompt)

        # Agent response
        agent_msg = {
            "role": agent["role"],
            "icon": agent["icon"],
            "text": response_text,
            "timestamp": datetime.now().isoformat()
        }
        task["messages"].append(agent_msg)

        # Broadcast agent response via SSE
        await broadcast_sse_event({
            "type": "agentic_chat_response",
            "task_id": task_id,
            "message": agent_msg
        })

        logger.info(f"Chat message sent to task {task_id}")

        return {
            "status": "success",
            "agent": agent["role"],
            "icon": agent["icon"],
            "response": response_text
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agentic/emails/{email_id}/team")
async def detect_team_for_email_endpoint(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Detect which team should handle a specific email"""
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        team = detect_team_for_email(email.subject, email.body_text or email.body_html)
        team_info = TEAMS[team]

        return {
            "email_id": email_id,
            "detected_team": team,
            "team_name": team_info["name"],
            "agent_count": len(team_info["agents"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting team for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agentic/simulate-discussion")
async def simulate_team_discussion(
    team: str = "fraud",
    subject: str = "Suspicious Wire Transfer Request"
):
    """
    Simulate a team discussion for testing purposes.
    This endpoint creates a mock email scenario for demonstration.
    """
    try:
        if team not in TEAMS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team '{team}'. Valid teams: {list(TEAMS.keys())}"
            )

        # Create a mock email body based on the team
        mock_bodies = {
            "fraud": "We received a suspicious wire transfer request for CHF 500K to an unknown account. The email appears to be from our CEO but the sending domain is slightly different.",
            "compliance": "We need clarification on FATCA reporting requirements for our new US client accounts. What are the thresholds and documentation needed?",
            "investments": "Please provide a comprehensive analysis of Tesla (TSLA) stock, including financial metrics, valuation, and investment recommendation."
        }

        result = await orchestrator.run_team_discussion(
            email_id=0,  # Mock ID
            email_subject=subject,
            email_body=mock_bodies.get(team, "Sample email body for team discussion."),
            email_sender="client@example.com",
            team=team,
            max_rounds=1
        )

        return {
            "status": "success",
            "simulation": True,
            "team": team,
            "discussion": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating team discussion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/{email_id}/suggest-team")
async def suggest_team_for_email_endpoint(
    email_id: int,
    db: Session = Depends(get_db)
):
    """
    Use LLM to suggest which team should handle an email.
    Stores the suggestion in the email record.
    """
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        # Use LLM to suggest team
        suggested_team = await suggest_team_for_email_llm(
            email.subject,
            email.body_text or email.body_html,
            email.sender
        )

        # Store suggestion in database
        email.suggested_team = suggested_team
        db.commit()

        team_info = TEAMS[suggested_team]

        logger.info(f"Suggested team '{suggested_team}' for email {email_id}")

        return {
            "email_id": email_id,
            "suggested_team": suggested_team,
            "team_name": team_info["name"],
            "agent_count": len(team_info["agents"]),
            "agents": [agent["role"] for agent in team_info["agents"]]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting team for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/{email_id}/assign-team")
async def assign_team_to_email(
    email_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Manually assign a team to an email and trigger the agentic workflow.
    This is called when the operator drags an email to a team or confirms assignment.

    Request body:
    {
        "team": "investments",
        "assignment_message": "Please check this email and tell me what you suggest I should do?"
    }
    """
    try:
        team = request.get("team")
        assignment_message = request.get("assignment_message", "")

        # Get email from database
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        # Validate team
        if team not in TEAMS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team '{team}'. Valid teams: {list(TEAMS.keys())}"
            )

        # Create task ID for agentic workflow
        task_id = str(uuid.uuid4())

        # Update email record with assigned team and task_id
        email.assigned_team = team
        email.agentic_task_id = task_id
        email.team_assigned_at = datetime.now()
        db.commit()

        # Initialize task status
        agentic_tasks[task_id] = {
            "status": "pending",
            "email_id": email_id,
            "team": team,
            "assignment_message": assignment_message,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

        # Prepend assignment message to email body if provided
        email_body = email.body_text or email.body_html
        if assignment_message:
            email_body = f"ASSIGNMENT MESSAGE: {assignment_message}\n\n{email_body}"

        # Start background task for agentic workflow
        asyncio.create_task(run_agentic_workflow_background(
            task_id=task_id,
            email_id=email.id,
            team=team,
            email_subject=email.subject,
            email_body=email_body,
            email_sender=email.sender
        ))

        logger.info(f"Assigned team '{team}' to email {email_id} with message and started workflow task {task_id}")

        return {
            "status": "assigned",
            "email_id": email_id,
            "assigned_team": team,
            "task_id": task_id,
            "workflow_url": f"/pages/agentic-teams.html?email_id={email_id}&task_id={task_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning team to email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails/{email_id}/workflow-status")
async def get_email_workflow_status(
    email_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the agentic workflow status for an email.
    Returns workflow link if available.
    """
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        if not email.agentic_task_id:
            return {
                "email_id": email_id,
                "has_workflow": False,
                "suggested_team": email.suggested_team,
                "assigned_team": email.assigned_team
            }

        # Get task status
        task_id = email.agentic_task_id
        task = agentic_tasks.get(task_id)

        if not task:
            return {
                "email_id": email_id,
                "has_workflow": True,
                "task_id": task_id,
                "status": "unknown",
                "assigned_team": email.assigned_team,
                "workflow_url": f"/agentic-teams.html?email_id={email_id}&task_id={task_id}"
            }

        response = {
            "email_id": email_id,
            "has_workflow": True,
            "task_id": task_id,
            "status": task["status"],
            "assigned_team": email.assigned_team,
            "team_assigned_at": email.team_assigned_at.isoformat() if email.team_assigned_at else None,
            "workflow_url": f"/agentic-teams.html?email_id={email_id}&task_id={task_id}"
        }

        if task["status"] == "completed":
            response["result"] = task.get("result")
        elif task["status"] == "failed":
            response["error"] = task.get("error")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status for email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
async def events():
    """Server-Sent Events endpoint for real-time updates"""
    return StreamingResponse(
        broadcaster.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
