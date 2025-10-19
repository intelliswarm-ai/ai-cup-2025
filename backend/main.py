from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db, init_db
from models import Email, WorkflowResult, WorkflowConfig
from mailpit_client import MailPitClient
from workflows import WorkflowEngine
from llm_service import ollama_service
from pydantic import BaseModel
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mailbox Analysis API", version="1.0.0")

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

# Pydantic models for API
class EmailResponse(BaseModel):
    id: int
    mailpit_id: str
    subject: str
    sender: str
    recipient: str
    received_at: datetime
    is_phishing: bool
    processed: bool
    workflow_results: List[dict] = []

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
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
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

            # Extract email data
            email = Email(
                mailpit_id=msg_id,
                subject=msg.get("Subject", ""),
                sender=msg.get("From", {}).get("Address", ""),
                recipient=", ".join([addr.get("Address", "") for addr in msg.get("To", [])]),
                body_text=full_msg.get("Text", ""),
                body_html=full_msg.get("HTML", ""),
                received_at=datetime.fromisoformat(msg.get("Created", "").replace("Z", "+00:00"))
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

@app.get("/api/emails", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 50,
    processed: Optional[bool] = None,
    is_phishing: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get emails from database with filters"""
    query = db.query(Email)

    if processed is not None:
        query = query.filter(Email.processed == processed)

    if is_phishing is not None:
        query = query.filter(Email.is_phishing == is_phishing)

    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()

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
            ]
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
    """Process an email through phishing detection workflows"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_data = {
        "subject": email.subject,
        "sender": email.sender,
        "body_text": email.body_text or "",
        "body_html": email.body_html or ""
    }

    # Run workflows
    workflow_results = await workflow_engine.run_all_workflows(email_data)

    # Store results
    phishing_votes = 0
    total_confidence = 0

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

    # Update email status
    email.processed = True
    # Mark as phishing if majority of workflows detect it
    email.is_phishing = phishing_votes >= len(workflow_results) / 2

    db.commit()

    return {
        "status": "success",
        "email_id": email_id,
        "is_phishing": email.is_phishing,
        "workflows_run": len(workflow_results),
        "average_confidence": total_confidence / len(workflow_results) if workflow_results else 0,
        "results": workflow_results
    }

@app.post("/api/emails/process-all")
async def process_all_unprocessed_emails(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process all unprocessed emails"""
    unprocessed = db.query(Email).filter(Email.processed == False).all()

    async def process_batch():
        for email in unprocessed:
            try:
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

            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")

        db.commit()

    background_tasks.add_task(process_batch)

    return {
        "status": "processing",
        "count": len(unprocessed),
        "message": "Processing emails in background"
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

    return {
        "total_emails": total_emails,
        "processed_emails": processed_emails,
        "unprocessed_emails": total_emails - processed_emails,
        "phishing_detected": phishing_emails,
        "legitimate_emails": legitimate_emails,
        "phishing_percentage": (phishing_emails / processed_emails * 100) if processed_emails > 0 else 0
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
    """Process an email with LLM: generate summary and extract CTAs"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        # Process with LLM
        result = await ollama_service.process_email(
            email.subject or "",
            email.body_text or ""
        )

        # Update email
        email.summary = result["summary"]
        email.call_to_actions = result["call_to_actions"]
        email.llm_processed = True
        email.llm_processed_at = datetime.utcnow()

        db.commit()

        return {
            "status": "success",
            "email_id": email_id,
            "summary": email.summary,
            "call_to_actions": email.call_to_actions
        }

    except Exception as e:
        logger.error(f"Error processing email {email_id} with LLM: {e}")
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

                email.summary = result["summary"]
                email.call_to_actions = result["call_to_actions"]
                email.llm_processed = True
                email.llm_processed_at = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error processing email {email.id} with LLM: {e}")

        db.commit()

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
