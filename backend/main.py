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

from database import get_db, init_db
from models import Email, WorkflowResult, WorkflowConfig
from mailpit_client import MailPitClient
from workflows import WorkflowEngine
from llm_service import ollama_service
from wiki_enrichment import email_enricher
from pydantic import BaseModel
from events import broadcaster
from email_fetcher import email_fetcher
from agentic_teams import orchestrator, detect_team_for_email, TEAMS

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
    mailpit_id: str
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

    # Initialize wiki enrichment knowledge base in background
    logger.info("Starting wiki enrichment initialization in background...")
    asyncio.create_task(email_enricher.initialize())
    logger.info("Wiki enrichment initialization started (loading in background)")

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
            "phone_enriched": email.phone_enriched
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
            email.body_text or ""
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
                        email.body_text or ""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Commented out to prevent blocking startup - model should be pre-pulled
# @app.on_event("startup")
# async def startup_llm():
#     """Initialize LLM on startup"""
#     logger.info("Loading Ollama model...")
#     await ollama_service.ensure_model_loaded()
#     logger.info("Ollama model ready")

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
        # Process with LLM
        result = await ollama_service.process_email(
            email.subject or "",
            email.body_text or ""
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
            "wiki_enriched": has_wiki_data,
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
                    email.body_text or ""
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
                "is_phishing": email.is_phishing
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
async def get_available_teams():
    """Get list of all available virtual bank teams"""
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
                    "responsibilities": agent["responsibilities"]
                }
                for agent in team_data["agents"]
            ]
        })
    return {"teams": teams_list}


async def run_agentic_workflow_background(task_id: str, email_id: int, team: str, email_subject: str, email_body: str, email_sender: str):
    """Background task to run agentic team discussion"""
    try:
        logger.info(f"[Task {task_id}] Starting agentic workflow for email {email_id} with team '{team}'")

        # Update status to processing
        agentic_tasks[task_id]["status"] = "processing"
        agentic_tasks[task_id]["team"] = team

        # Run the team discussion
        result = await orchestrator.run_team_discussion(
            email_id=email_id,
            email_subject=email_subject,
            email_body=email_body,
            email_sender=email_sender,
            team=team,
            max_rounds=1
        )

        # Store the result
        agentic_tasks[task_id]["status"] = "completed"
        agentic_tasks[task_id]["result"] = {
            "status": "success",
            "email_id": email_id,
            "team": team,
            "team_name": result["team_name"],
            "discussion": result
        }

        logger.info(f"[Task {task_id}] Completed agentic workflow for email {email_id}")

    except Exception as e:
        logger.error(f"[Task {task_id}] Error in agentic workflow: {e}")
        agentic_tasks[task_id]["status"] = "failed"
        agentic_tasks[task_id]["error"] = str(e)


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
async def get_agentic_task_status(task_id: str):
    """Poll for agentic task status and results"""
    if task_id not in agentic_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = agentic_tasks[task_id]

    response = {
        "task_id": task_id,
        "status": task["status"],
        "email_id": task["email_id"],
        "team": task.get("team"),
        "created_at": task["created_at"]
    }

    if task["status"] == "completed":
        response["result"] = task["result"]
    elif task["status"] == "failed":
        response["error"] = task.get("error", "Unknown error")

    return response


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
    team: str = "credit_risk",
    subject: str = "Credit Line Increase Request"
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
            "credit_risk": "We are requesting a credit line increase from CHF 2M to CHF 5M to support our expansion plans. Our revenue has grown 40% YoY and we have strong cash flows.",
            "fraud": "We received a suspicious wire transfer request for CHF 500K to an unknown account. The email appears to be from our CEO but the sending domain is slightly different.",
            "compliance": "We need clarification on FATCA reporting requirements for our new US client accounts. What are the thresholds and documentation needed?",
            "wealth": "Our client inherited CHF 12M and wants to invest conservatively while minimizing tax exposure. They are 55 years old and planning retirement in 10 years.",
            "corporate": "We need a letter of credit for CHF 3M to support an import transaction from Asia. The goods are electronics with 90-day payment terms.",
            "operations": "Multiple customers have complained about the new account opening process taking too long. We need to streamline the workflow and improve response times."
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
