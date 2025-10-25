from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    mailpit_id = Column(String, unique=True, index=True)
    subject = Column(String)
    sender = Column(String)
    recipient = Column(String)
    body_text = Column(Text)
    body_html = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)
    is_phishing = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)

    # Ground truth labels from dataset
    label = Column(Integer)  # 1 = phishing, 0 = legitimate (from dataset)
    phishing_type = Column(String)  # e.g., authority_scam, credential_harvesting, legitimate

    # LLM Processing fields
    summary = Column(Text)  # LLM-generated summary
    call_to_actions = Column(JSON)  # List of extracted CTAs
    llm_processed = Column(Boolean, default=False)
    llm_processed_at = Column(DateTime)

    # Email categorization and badges
    badges = Column(JSON)  # List of badge types: MEETING, RISK, EXTERNAL, etc.

    # UI state badges (ACTION_REQUIRED, HIGH_PRIORITY, REPLIED, ATTACHMENT, SNOOZED, AI_SUGGESTED)
    ui_badges = Column(JSON)  # List of UI state badge types

    # Quick reply drafts (3 versions: formal, friendly, brief)
    quick_reply_drafts = Column(JSON)  # {formal: "", friendly: "", brief: ""}

    # Wiki enrichment data
    enriched_data = Column(JSON)  # {enriched_keywords: [{keyword, context, wiki_page, confidence}], relevant_pages: []}
    enriched = Column(Boolean, default=False)  # Flag to indicate if email has been enriched
    enriched_at = Column(DateTime)  # When enrichment was performed

    # Relationships
    workflow_results = relationship("WorkflowResult", back_populates="email", cascade="all, delete-orphan")

class WorkflowResult(Base):
    __tablename__ = "workflow_results"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    workflow_name = Column(String)
    result = Column(JSON)  # Store workflow analysis results
    is_phishing_detected = Column(Boolean, default=False)
    confidence_score = Column(Integer)  # 0-100
    risk_indicators = Column(JSON)  # List of detected risk factors
    executed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    email = relationship("Email", back_populates="workflow_results")

class WorkflowConfig(Base):
    __tablename__ = "workflow_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    config = Column(JSON)  # Workflow-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow)
