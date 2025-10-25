"""
RAG-based Email Enrichment Service using ChromaDB + SentenceTransformers

Modern RAG implementation with:
- Vector embeddings using sentence-transformers
- ChromaDB for persistent vector storage
- Semantic similarity search
- Context-aware keyword extraction
"""

import httpx
import logging
import re
from typing import Dict, List, Tuple, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class WikiKnowledgeBase:
    """Manages wiki content as a vector-based knowledge base for RAG"""

    def __init__(
        self,
        wiki_url: str = "http://otterwiki:8080",
        model_name: str = "all-MiniLM-L6-v2",
        chroma_persist_directory: str = "./chroma_db"
    ):
        self.wiki_url = wiki_url
        self.model_name = model_name
        self.chroma_persist_directory = chroma_persist_directory

        # Initialize sentence transformer model
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        logger.info(f"Initializing ChromaDB at {chroma_persist_directory}")
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=chroma_persist_directory,
            anonymized_telemetry=False
        ))

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="wiki_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

        self.knowledge_base = {}  # {page_title: {content, summary, keywords}}

    async def fetch_wiki_pages(self) -> Dict[str, Dict]:
        """Fetch all wiki pages and build knowledge base"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to get the wiki index/home page
                response = await client.get(f"{self.wiki_url}/")

                if response.status_code != 200:
                    logger.warning(f"Wiki not accessible: {response.status_code}")
                    return self._get_fallback_knowledge_base()

                # For now, return fallback knowledge base
                # In production, would parse wiki pages
                return self._get_fallback_knowledge_base()

        except Exception as e:
            logger.error(f"Error fetching wiki pages: {e}")
            return self._get_fallback_knowledge_base()

    def _get_fallback_knowledge_base(self) -> Dict[str, Dict]:
        """
        Fallback knowledge base with company information
        overlapping with email dataset topics (phishing, security, finance, etc.)
        """
        return {
            "Security Policy": {
                "content": """Company Security Policy

Our company has strict security protocols to protect against phishing and social engineering attacks:

1. Password Requirements: All passwords must be at least 12 characters with complexity requirements. Never share passwords via email.

2. Multi-Factor Authentication (MFA): MFA is mandatory for all email accounts and internal systems.

3. Email Verification: Always verify sender authenticity before clicking links or downloading attachments. Check for:
   - Suspicious sender addresses
   - Urgent language requesting immediate action
   - Requests for sensitive information
   - Unusual attachments or links

4. Phishing Reporting: Report suspected phishing emails to the security team immediately.

5. Data Classification: Mark emails containing sensitive data as CONFIDENTIAL.""",
                "summary": "Company security protocols covering passwords, MFA, phishing prevention, and data classification",
                "keywords": ["password", "MFA", "multi-factor authentication", "phishing", "security", "verification", "suspicious", "confidential"]
            },

            "Financial Procedures": {
                "content": """Company Financial Transaction Procedures

All financial transactions must follow these procedures:

1. Wire Transfer Authorization: Wire transfers require dual approval from Finance Director and CFO. Requests via email must be verified by phone.

2. Invoice Verification: Verify all invoices match purchase orders before payment. Check vendor information in our approved vendor list.

3. Banking Information: Never update banking details based solely on email requests. Always verify through known contact channels.

4. Payment Fraud Prevention: Be alert for:
   - Urgent payment requests
   - Last-minute banking detail changes
   - Pressure to bypass normal procedures
   - Requests to keep transactions confidential

5. Expense Reporting: Submit expense reports through the official portal, not via email attachments.""",
                "summary": "Financial procedures for wire transfers, invoice verification, and fraud prevention",
                "keywords": ["wire transfer", "invoice", "payment", "banking", "vendor", "fraud", "CFO", "finance", "expense"]
            },

            "IT Support Procedures": {
                "content": """Company IT Support Policy

Official IT support procedures:

1. Help Desk: Submit all IT requests through the help desk portal.

2. Account Issues: IT will NEVER ask for your password via email, phone, or chat. Use the password reset portal for account issues.

3. Software Updates: All software updates are pushed automatically. Ignore emails asking you to download software updates.

4. Legitimate IT Contacts:
   - Help Desk: Official support email only
   - IT Security: Official security team contact
   - Phone: Official company extensions only

5. Suspicious IT Requests: Report emails claiming to be from IT that:
   - Request password or credentials
   - Ask to download software from external sites
   - Create urgency about account suspension
   - Use non-company email addresses""",
                "summary": "IT support procedures and guidelines for identifying legitimate IT communications",
                "keywords": ["IT support", "help desk", "password reset", "account", "software update", "credentials", "suspension"]
            },

            "Meeting Policy": {
                "content": """Company Meeting and Calendar Policy

Company guidelines for meetings and calendar invites:

1. Meeting Invitations: All official meetings use company Outlook/Google Calendar. External calendar invites (.ics files) should be verified.

2. Video Conferencing: Use company-approved platforms:
   - Microsoft Teams (primary)
   - Zoom (with company SSO)
   - Google Meet (with company accounts)

3. External Meetings: Verify external meeting requests by:
   - Confirming with the organizer via known contact
   - Checking if the meeting relates to your role
   - Verifying the meeting platform is legitimate

4. Calendar Permissions: Never grant calendar editing permissions to external parties.

5. Meeting Recording: Inform participants before recording any meeting.""",
                "summary": "Meeting policy covering calendar invites, video conferencing platforms, and external meeting verification",
                "keywords": ["meeting", "calendar", "invite", "Teams", "Zoom", "conference", "video call", "organizer"]
            },

            "Data Protection": {
                "content": """Company Data Protection and Privacy Policy

Guidelines for handling company and customer data:

1. Personal Information: Handle all personal data per GDPR and data protection regulations. Never share customer data via unsecured email.

2. Email Encryption: Use encrypted email for sensitive information. Enable encryption in Outlook/Gmail for:
   - Customer PII
   - Financial data
   - Proprietary information

3. External Sharing: Before sharing data externally:
   - Verify recipient authority
   - Use secure file sharing (OneDrive, SharePoint)
   - Apply appropriate access controls
   - Set expiration dates

4. Data Breach Response: Report potential data breaches to the data protection officer within 24 hours.

5. Retention Policy: Follow data retention schedules. Don't keep sensitive emails beyond required period.""",
                "summary": "Data protection guidelines covering PII, encryption, external sharing, and breach response",
                "keywords": ["data protection", "GDPR", "personal information", "PII", "encryption", "privacy", "breach", "sensitive data"]
            },

            "Vendor Management": {
                "content": """Company Vendor and Supplier Policy

Procedures for working with external vendors:

1. Approved Vendors: Use only approved vendors from the procurement portal. New vendor requests require Procurement approval.

2. Vendor Communications: Verify vendor emails match our records. Be suspicious of:
   - New contacts from known vendors
   - Urgent payment requests
   - Banking detail changes
   - Requests to bypass procurement

3. Contract Requirements: All vendor contracts must:
   - Include security requirements
   - Specify data handling procedures
   - Define liability and insurance
   - Be reviewed by Legal

4. Performance Reporting: Report vendor issues to the procurement team.

5. Vendor Access: External vendors require sponsor approval for system access.""",
                "summary": "Vendor management procedures covering approved vendors, communications, and contracts",
                "keywords": ["vendor", "supplier", "procurement", "contract", "banking details", "approved", "external"]
            },

            "HR Policies": {
                "content": """Company Human Resources Policies

Important HR information for all employees:

1. Performance Reviews: Annual reviews conducted in Q1. HR will never request personal information via email.

2. Payroll: Payroll changes must be submitted through the HR portal. Direct deposit changes require identity verification.

3. Benefits: Open enrollment information sent via official HR communications. Verify links are from official company domains.

4. Onboarding: New hire documentation completed through secure HR portal, not email attachments.

5. Legitimate HR Contacts:
   - General HR: Official HR email only
   - Payroll: Official payroll team contact
   - Benefits: Official benefits portal

6. Suspicious HR Emails: Report emails requesting:
   - Social Security numbers
   - Bank account details
   - W-2 forms
   - Personal information updates via email""",
                "summary": "HR policies covering performance reviews, payroll, benefits, and legitimate HR contacts",
                "keywords": ["HR", "human resources", "payroll", "performance review", "benefits", "onboarding", "W-2", "direct deposit"]
            },

            "Conference and Events": {
                "content": """Company Conference and Event Policy

Guidelines for attending and organizing company events:

1. Conference Registration: All conference attendance requires manager approval. Submit registration requests through the events portal with:
   - Conference name and dates
   - Location and travel requirements
   - Registration fee and budget code
   - Business justification

2. Event Types:
   - Industry conferences (technical, trade shows)
   - Professional networking events
   - Company-sponsored events
   - Training and educational seminars
   - Customer and partner events

3. Travel and Expense: Follow company travel policy for conference-related expenses. Book through approved travel vendors.

4. Networking Events: Networking opportunities are valuable for business development. Share event details and registration information internally.

5. Event Communications: Official event communications come from:
   - Conference organizers with verified domains
   - Company events team
   - Professional associations
   - Approved vendors

6. Suspicious Event Emails: Be cautious of:
   - Free conference registrations from unknown sources
   - Requests for payment to personal accounts
   - Last-minute venue or detail changes
   - Unverified conference platforms""",
                "summary": "Conference and event policies covering registration, networking, travel, and legitimate event communications",
                "keywords": ["conference", "event", "registration", "networking", "seminar", "workshop", "speaker", "attendee", "venue", "schedule"]
            },

            "Performance Feedback": {
                "content": """Company Performance Management and Feedback

Performance review process and feedback guidelines:

1. Annual Performance Reviews: Conducted quarterly with formal annual review. Process includes:
   - Self-assessment submission
   - Manager evaluation
   - Goal setting for next period
   - Compensation review
   - Development plan

2. Continuous Feedback: Managers provide ongoing feedback throughout the year. Regular one-on-one meetings scheduled monthly.

3. 360-Degree Feedback: Peer and stakeholder feedback collected during annual review cycle. Feedback is confidential and constructive.

4. Performance Improvement Plans: When performance issues arise, formal PIP may be initiated with clear goals and timeline.

5. Feedback Best Practices:
   - Timely and specific
   - Focused on behaviors and outcomes
   - Balanced (strengths and development areas)
   - Actionable and clear

6. Review Calibration: Manager calibration sessions ensure consistency across teams and departments.

7. Documentation: All feedback documented in HR system. Never share performance information via unsecured email.""",
                "summary": "Performance management covering reviews, feedback, 360 assessments, and improvement plans",
                "keywords": ["performance", "review", "feedback", "evaluation", "assessment", "improvement", "goals", "development", "calibration"]
            },

            "Project Documentation": {
                "content": """Company Project Documentation Standards

Guidelines for creating and managing project documentation:

1. Documentation Requirements: All projects must maintain:
   - Project charter and scope
   - Requirements documentation
   - Technical specifications
   - Architecture diagrams
   - User guides and manuals
   - Change logs and version history

2. Documentation Tools:
   - Confluence for wiki pages
   - SharePoint for official documents
   - GitHub/GitLab for code documentation
   - Project management tools (Jira, Asana)

3. Document Version Control:
   - Use semantic versioning (v1.0.0)
   - Track all changes with revision history
   - Maintain current and archived versions
   - Label documents as DRAFT, FINAL, APPROVED

4. Access and Sharing:
   - Follow data classification policies
   - Use appropriate sharing permissions
   - Internal documentation on company systems only
   - External sharing requires approval

5. Review and Approval: Technical documentation requires review by technical leads and approval by project stakeholders.

6. Knowledge Transfer: Document lessons learned, best practices, and project retrospectives for future reference.""",
                "summary": "Project documentation standards covering requirements, tools, version control, and knowledge sharing",
                "keywords": ["documentation", "project", "requirements", "specifications", "wiki", "version", "technical", "guide", "manual"]
            },

            "Status Reports and Updates": {
                "content": """Company Status Reporting Guidelines

Guidelines for weekly status reports and project updates:

1. Weekly Status Reports: All project teams submit weekly status reports by Friday EOD including:
   - Accomplishments this week
   - Planned activities for next week
   - Blockers and risks
   - Resource needs
   - Key metrics and KPIs

2. Report Format:
   - Summary (1-2 sentences)
   - Progress against milestones
   - Issues and risks (RAG status)
   - Action items and owners
   - Supporting data and metrics

3. Stakeholder Updates: Tailor updates to audience:
   - Executive summaries for leadership
   - Detailed technical updates for teams
   - Customer-facing status reports
   - Cross-functional team updates

4. Update Cadence:
   - Daily standups for agile teams
   - Weekly status reports for projects
   - Monthly reviews for programs
   - Quarterly business reviews

5. Communication Channels:
   - Email for weekly summaries
   - Project dashboards for real-time status
   - Meetings for complex discussions
   - Documentation for historical record

6. Escalation: Flag critical issues and blockers immediately, don't wait for weekly report.""",
                "summary": "Status reporting guidelines covering weekly reports, formats, stakeholder communications, and escalation",
                "keywords": ["status", "report", "weekly", "update", "progress", "milestone", "summary", "KPI", "metrics", "standup"]
            },

            "Budget and Planning": {
                "content": """Company Budget and Financial Planning

Budget planning and financial management guidelines:

1. Annual Budget Cycle: Budget planning begins Q3 for following fiscal year:
   - Department budget proposals
   - Business case development
   - Executive review and approval
   - Budget allocation and communication
   - Quarterly reviews and adjustments

2. Budget Categories:
   - Personnel costs (salaries, benefits)
   - Operating expenses (travel, supplies)
   - Capital expenditures (equipment, software)
   - Professional services (consultants, contractors)
   - Marketing and events

3. Budget Approval Levels:
   - Under $5K: Manager approval
   - $5K-$25K: Director approval
   - $25K-$100K: VP approval
   - Over $100K: Executive approval

4. Expense Tracking: Monitor spending against budget monthly. Use financial systems to track:
   - Actual vs. planned spending
   - Variance analysis
   - Forecasting for remainder of year
   - Purchase order commitments

5. Budget Transfers: Request budget transfers between categories through finance team with business justification.

6. Planning Best Practices:
   - Include contingency (10-15%)
   - Document assumptions
   - Align with strategic priorities
   - Review and update quarterly""",
                "summary": "Budget and financial planning covering annual cycles, categories, approvals, tracking, and best practices",
                "keywords": ["budget", "planning", "financial", "expense", "cost", "spending", "approval", "forecast", "allocation"]
            },

            "Schedule and Calendar Management": {
                "content": """Company Scheduling and Calendar Guidelines

Best practices for managing schedules and calendar coordination:

1. Calendar Etiquette:
   - Send meeting invites at least 24 hours in advance
   - Include agenda and objectives
   - Respect others' calendar blocks and focus time
   - Cancel or update meetings promptly if plans change
   - Accept or decline meeting invites within 24 hours

2. Meeting Scheduling:
   - Check attendee availability before scheduling
   - Use scheduling assistant tools
   - Avoid back-to-back meetings
   - Schedule meetings during core hours (9 AM - 4 PM)
   - Include dial-in information for remote participants

3. Schedule Confirmations:
   - Confirm important meetings 24 hours in advance
   - Verify meeting details (time, location, attendees)
   - Send reminders for customer or external meetings
   - Update calendar immediately for any changes

4. Time Zone Management:
   - Specify time zones for global meetings
   - Use calendar tools for time zone conversion
   - Schedule at reasonable hours for all participants
   - Record meetings for those who can't attend live

5. Recurring Meetings:
   - Review recurring meetings quarterly
   - Cancel if no longer needed
   - Update attendees as teams change
   - Maintain consistent agenda and format

6. Appointment Types:
   - Team meetings and standups
   - One-on-one check-ins
   - Customer meetings
   - All-hands and town halls
   - Training and workshops""",
                "summary": "Calendar and scheduling guidelines covering meeting etiquette, confirmations, time zones, and appointments",
                "keywords": ["schedule", "calendar", "meeting", "appointment", "confirmation", "time", "invite", "coordination", "booking"]
            }
        }

    async def index_knowledge_base(self):
        """Build the knowledge base index with vector embeddings"""
        # Fetch knowledge base content
        self.knowledge_base = await self.fetch_wiki_pages()
        logger.info(f"Fetched {len(self.knowledge_base)} wiki pages")

        # Check if collection already has data
        existing_count = self.collection.count()
        if existing_count > 0:
            logger.info(f"ChromaDB collection already has {existing_count} documents. Skipping re-indexing.")
            return

        # Prepare documents for embedding
        documents = []
        metadatas = []
        ids = []

        for idx, (page_title, page_data) in enumerate(self.knowledge_base.items()):
            content = page_data.get("content", "")
            summary = page_data.get("summary", "")

            # Split content into chunks for better retrieval
            chunks = self._chunk_text(content, chunk_size=500, overlap=50)

            for chunk_idx, chunk in enumerate(chunks):
                doc_id = f"{page_title}_{chunk_idx}"
                documents.append(chunk)
                metadatas.append({
                    "page_title": page_title,
                    "summary": summary,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                })
                ids.append(doc_id)

        logger.info(f"Generating embeddings for {len(documents)} document chunks...")

        # Generate embeddings
        embeddings = self.embedding_model.encode(documents, show_progress_bar=True)

        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Indexed {len(documents)} chunks from {len(self.knowledge_base)} wiki pages")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better retrieval"""
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Start new chunk with overlap (keep last sentence for context)
                if len(current_chunk) > 0:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks if chunks else [text]

    def find_relevant_context(
        self,
        email_content: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find wiki content relevant to email using semantic search

        Returns list of dicts with:
        - chunk: The relevant text chunk
        - page_title: Source wiki page
        - summary: Page summary
        - similarity: Cosine similarity score
        """
        # Generate embedding for email content
        email_embedding = self.embedding_model.encode([email_content])[0]

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[email_embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        relevant_contexts = []

        if results['documents'] and len(results['documents'][0]) > 0:
            for idx in range(len(results['documents'][0])):
                chunk = results['documents'][0][idx]
                metadata = results['metadatas'][0][idx]
                distance = results['distances'][0][idx]

                # Convert distance to similarity (cosine distance to cosine similarity)
                similarity = 1 - distance

                relevant_contexts.append({
                    "chunk": chunk,
                    "page_title": metadata.get("page_title", "Unknown"),
                    "summary": metadata.get("summary", ""),
                    "similarity": float(similarity),
                    "chunk_index": metadata.get("chunk_index", 0)
                })

        return relevant_contexts


class EmailEnricher:
    """Enriches emails with wiki context using vector-based RAG"""

    def __init__(self):
        self.wiki_kb = WikiKnowledgeBase()

    async def initialize(self):
        """Initialize the knowledge base with vector embeddings"""
        await self.wiki_kb.index_knowledge_base()

    async def enrich_email(self, subject: str, body: str) -> Dict:
        """
        Enrich email with wiki context using semantic search

        Returns:
        {
            "enriched_keywords": [
                {
                    "keyword": "password",
                    "context": "Security Policy excerpt...",
                    "wiki_page": "Security Policy",
                    "confidence": 0.95
                }
            ],
            "relevant_pages": ["Security Policy", "IT Support Procedures"]
        }
        """
        full_text = f"{subject} {body}"

        # Find relevant wiki contexts using semantic search
        relevant_contexts = self.wiki_kb.find_relevant_context(full_text, top_k=5)

        if not relevant_contexts:
            return {
                "enriched_keywords": [],
                "relevant_pages": []
            }

        # Extract keywords from relevant contexts and build enrichment data
        enriched_keywords = []
        relevant_pages = set()

        # Group contexts by page
        page_contexts = {}
        for ctx in relevant_contexts:
            page = ctx["page_title"]
            if page not in page_contexts:
                page_contexts[page] = []
            page_contexts[page].append(ctx)

        # Extract keywords from each page's context
        for page_title, contexts in page_contexts.items():
            relevant_pages.add(page_title)

            # Get the most relevant context for this page
            best_context = max(contexts, key=lambda x: x["similarity"])

            # Extract important terms from the context
            keywords = self._extract_keywords_from_context(
                best_context["chunk"],
                full_text
            )

            for keyword, relevance in keywords[:3]:  # Top 3 keywords per page
                enriched_keywords.append({
                    "keyword": keyword,
                    "context": best_context["chunk"][:300] + "...",
                    "wiki_page": page_title,
                    "confidence": round(best_context["similarity"] * 100, 1)
                })

        # Sort by confidence
        enriched_keywords.sort(key=lambda x: x["confidence"], reverse=True)

        # Return top 10 keywords
        return {
            "enriched_keywords": enriched_keywords[:10],
            "relevant_pages": list(relevant_pages)
        }

    def _extract_keywords_from_context(
        self,
        context: str,
        email_text: str
    ) -> List[Tuple[str, float]]:
        """
        Extract important keywords from context that also appear in email
        Returns list of (keyword, relevance_score) tuples
        """
        # Extract potential keywords (2-3 word phrases and single important words)
        context_lower = context.lower()
        email_lower = email_text.lower()

        # Common keywords to look for
        keyword_patterns = [
            r'\b(password|passwords)\b',
            r'\b(multi-factor authentication|MFA|2FA)\b',
            r'\b(phishing|suspicious)\b',
            r'\b(wire transfer|payment|invoice)\b',
            r'\b(vendor|supplier)\b',
            r'\b(help desk|IT support)\b',
            r'\b(meeting|calendar|invite)\b',
            r'\b(data protection|GDPR|PII)\b',
            r'\b(HR|payroll|benefits)\b',
            r'\b(security|verification)\b',
            r'\b(banking|financial)\b',
            r'\b(credentials|account)\b',
        ]

        keywords = []

        for pattern in keyword_patterns:
            matches_context = re.finditer(pattern, context_lower, re.IGNORECASE)
            for match in matches_context:
                keyword = match.group(0)

                # Check if keyword appears in email
                if keyword in email_lower:
                    # Calculate relevance based on frequency
                    email_count = email_lower.count(keyword)
                    context_count = context_lower.count(keyword)
                    relevance = min(1.0, (email_count + context_count) / 5.0)

                    keywords.append((keyword, relevance))

        # Remove duplicates and sort by relevance
        keywords = list(set(keywords))
        keywords.sort(key=lambda x: x[1], reverse=True)

        return keywords


# Global instance
email_enricher = EmailEnricher()
