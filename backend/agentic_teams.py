"""
Agentic Virtual Bank Teams
Multi-agent collaboration system for email analysis
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import httpx


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

TEAMS = {
    "fraud": {
        "name": "🔍 Fraud Investigation Unit",
        "agents": [
            {
                "role": "Fraud Detection Specialist",
                "icon": "🔍",
                "personality": "Suspicious and investigative. Looks for red flags. Says 'I notice that...' and 'This pattern suggests...'",
                "responsibilities": "Identify suspicious patterns, transaction anomalies, and fraud indicators",
                "style": "Skeptical, detail-focused, investigative"
            },
            {
                "role": "Forensic Analyst",
                "icon": "🧪",
                "personality": "Technical and methodical. Deep dives into evidence. Uses phrases like 'The technical analysis shows...' and 'Examining the metadata...'",
                "responsibilities": "Conduct technical analysis, trace transactions, analyze digital evidence",
                "style": "Technical, precise, methodical"
            },
            {
                "role": "Legal Advisor",
                "icon": "⚖️",
                "personality": "Cautious and procedural. Ensures compliance. Says 'From a legal standpoint...' and 'We must ensure...'",
                "responsibilities": "Assess legal implications, regulatory requirements, evidence admissibility",
                "style": "Procedural, cautious, compliance-focused"
            },
            {
                "role": "Security Director",
                "icon": "🛡️",
                "personality": "Decisive and action-oriented. Makes containment decisions. Uses phrases like 'We need to immediately...' and 'The priority is...'",
                "responsibilities": "Decide on containment actions, client contact, law enforcement involvement",
                "style": "Decisive, action-oriented, protective"
            }
        ]
    },
    "compliance": {
        "name": "⚖️ Compliance & Regulatory Affairs",
        "agents": [
            {
                "role": "Compliance Officer",
                "icon": "📋",
                "personality": "Rule-oriented and systematic. Checks regulations. Says 'According to regulation...' and 'We must comply with...'",
                "responsibilities": "Verify regulatory compliance, policy adherence, documentation requirements",
                "style": "Systematic, rule-bound, thorough"
            },
            {
                "role": "Legal Counsel",
                "icon": "⚖️",
                "personality": "Analytical and interpretive. Explains legal nuances. Uses phrases like 'The legal interpretation is...' and 'From a liability perspective...'",
                "responsibilities": "Interpret regulations, assess legal risks, provide legal opinions",
                "style": "Analytical, interpretive, cautious"
            },
            {
                "role": "Auditor",
                "icon": "📊",
                "personality": "Meticulous and verification-focused. Double-checks everything. Says 'Let me verify...' and 'The audit trail shows...'",
                "responsibilities": "Audit compliance processes, verify documentation, check audit trails",
                "style": "Meticulous, verification-focused, detail-oriented"
            },
            {
                "role": "Regulatory Liaison",
                "icon": "🏛️",
                "personality": "Strategic and communicative. Manages regulator relationships. Uses phrases like 'Based on regulator expectations...' and 'We should report...'",
                "responsibilities": "Determine reporting obligations, draft regulator communications, manage relationships",
                "style": "Strategic, communicative, proactive"
            }
        ]
    },
    "investments": {
        "name": "📈 Investment Research Team",
        "agents": [
            {
                "role": "Research Analyst",
                "icon": "🔍",
                "personality": "Data-driven and thorough. Dives deep into financial data. Says 'Looking at the fundamentals...' and 'The data shows...'",
                "responsibilities": "Analyze company financials, SEC filings, industry trends, competitive positioning",
                "style": "Analytical, detail-oriented, evidence-based"
            },
            {
                "role": "Financial Analyst",
                "icon": "📊",
                "personality": "Numbers-focused and valuation-oriented. Calculates everything. Uses phrases like 'The valuation metrics indicate...' and 'Based on DCF analysis...'",
                "responsibilities": "Perform valuation analysis, financial modeling, ratio analysis, price targets",
                "style": "Quantitative, methodical, precise"
            },
            {
                "role": "Market Strategist",
                "icon": "🌐",
                "personality": "Big-picture thinker and macro-aware. Understands market context. Says 'Given current market conditions...' and 'The macro environment suggests...'",
                "responsibilities": "Assess market trends, sector dynamics, economic indicators, timing considerations",
                "style": "Strategic, contextual, forward-looking"
            },
            {
                "role": "Chief Investment Officer",
                "icon": "💼",
                "personality": "Decisive and risk-balanced. Synthesizes research into recommendations. Uses phrases like 'Based on our analysis...' and 'My recommendation is...'",
                "responsibilities": "Make final investment recommendation, assess risk-reward, set conviction level",
                "style": "Authoritative, balanced, actionable"
            }
        ]
    }
}


# ============================================================================
# AGENT STATE AND WORKFLOW
# ============================================================================

class AgentState(TypedDict):
    """State for the multi-agent conversation"""
    email_id: int
    email_subject: str
    email_body: str
    email_sender: str
    team: str
    messages: List[Dict[str, Any]]
    current_speaker: str
    round: int
    max_rounds: int
    decision: Optional[Dict[str, Any]]
    completed: bool


class AgenticTeamOrchestrator:
    """Orchestrates multi-agent team discussions"""

    def __init__(self, openai_api_key: str = None, openai_model: str = "gpt-4o-mini", ollama_url: str = "http://ollama:11434"):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.ollama_url = ollama_url
        self.ollama_model = os.getenv("OLLAMA_MODEL", "phi3")
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutes timeout for CPU-only Ollama

        # Determine which LLM to use - automatically fallback to Ollama if OpenAI key is not valid
        # Fallback cases: no .env file, missing key, empty key, placeholder value, or whitespace
        self.use_openai = self._is_valid_openai_key(openai_api_key)

        if self.use_openai:
            print(f"[AgenticTeamOrchestrator] Using OpenAI API with model: {self.openai_model}")
        else:
            print(f"[AgenticTeamOrchestrator] OpenAI API key not configured - using Ollama at {self.ollama_url} with model: {self.ollama_model}")

    def _is_valid_openai_key(self, api_key: str) -> bool:
        """
        Check if the OpenAI API key is valid and configured.
        Returns False (triggers Ollama fallback) if:
        - API key is None (not set in .env or no .env file exists)
        - API key is empty string
        - API key is only whitespace
        - API key is the example placeholder
        """
        if not api_key:
            return False

        api_key_stripped = api_key.strip()
        if not api_key_stripped:
            return False

        # Check for common placeholder values
        placeholder_values = ["your_openai_api_key_here", "your-api-key-here", "REPLACE_ME"]
        if api_key_stripped in placeholder_values:
            return False

        return True

    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """
        Call LLM (OpenAI or Ollama) based on configuration.
        Automatically falls back to Ollama if OpenAI fails.
        """
        try:
            if self.use_openai:
                result = await self._call_openai(prompt, system_message)
                # If OpenAI returns an error, fallback to Ollama
                if result.startswith("Error"):
                    print(f"[AgenticTeamOrchestrator] OpenAI failed, falling back to Ollama: {result}")
                    return await self._call_ollama(prompt, system_message)
                return result
            else:
                return await self._call_ollama(prompt, system_message)
        except Exception as e:
            # Last resort: try Ollama if we haven't already
            if self.use_openai:
                print(f"[AgenticTeamOrchestrator] Exception with OpenAI, attempting Ollama fallback: {str(e)}")
                try:
                    return await self._call_ollama(prompt, system_message)
                except Exception as ollama_e:
                    return f"Error: OpenAI failed ({str(e)}), Ollama fallback also failed ({str(ollama_e)})"
            return f"Error: {str(e)}"

    async def _call_openai(self, prompt: str, system_message: str = None) -> str:
        """Call OpenAI API"""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.openai_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 350
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = response.text
                return f"Error calling OpenAI API: {response.status_code} - {error_text}"

        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    async def _call_ollama(self, prompt: str, system_message: str = None) -> str:
        """Call Ollama LLM using /api/generate endpoint"""
        try:
            # Combine system message and prompt for generate endpoint
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"

            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 500  # Increased for better team discussions
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result["response"]
            else:
                return f"Error calling Ollama: {response.status_code}"

        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    async def agent_speaks(self, state: AgentState, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response from a specific agent"""
        team_info = TEAMS[state["team"]]
        current_round = state.get("round", 0)

        # Build context from previous messages
        conversation_context = "\n".join([
            f"{msg['role']}: {msg['text']}"
            for msg in state["messages"][-8:]  # Last 8 messages for context
        ])

        # Create agent-specific prompt
        system_prompt = f"""You are a {agent['role']} at a Swiss bank. You are part of the {team_info['name']} team.

Your personality: {agent['personality']}
Your responsibilities: {agent['responsibilities']}
Your communication style: {agent['style']}

You are in a professional debate with your team about an email. This is an interactive discussion where you should:
- Challenge ideas you disagree with (respectfully but firmly)
- Build on good points made by colleagues
- Offer alternative perspectives
- Defend your position with evidence and reasoning

Stay in character and be concise (2-3 sentences) but bold in your opinions."""

        # Different prompts based on round - get progressively more challenging
        if current_round == 0:
            # Round 1: Initial assessment
            user_prompt = f"""EMAIL DETAILS:
Subject: {state['email_subject']}
From: {state['email_sender']}
Body: {state['email_body'][:500]}

PREVIOUS DISCUSSION:
{conversation_context if conversation_context else "This is the start of the discussion."}

As {agent['role']}, provide your initial assessment of THIS SPECIFIC EMAIL. Reference the actual subject, sender, and content details in your analysis. What's your take? Be direct and clear about your concerns or recommendations."""
        elif current_round == 1:
            # Round 2: Challenge and debate
            user_prompt = f"""EMAIL DETAILS:
Subject: {state['email_subject']}
From: {state['email_sender']}
Body: {state['email_body'][:500]}

DEBATE SO FAR:
{conversation_context}

As {agent['role']}, CHALLENGE your colleagues' views. What flaws do you see in their arguments about THIS SPECIFIC EMAIL? What details from the subject, sender, or body are they overlooking? If you disagree, say so directly and explain why. Push back on weak points and propose better alternatives."""
        else:
            # Round 3+: Intense debate and synthesis
            user_prompt = f"""EMAIL DETAILS:
Subject: {state['email_subject']}
From: {state['email_sender']}
Body: {state['email_body'][:500]}

HEATED DEBATE:
{conversation_context}

As {agent['role']}, this is the final round. Based on the SPECIFIC details of this email (subject, sender, body), either:
1) STRONGLY defend your position if you're right, citing the specific email details that support your view
2) Or CONCEDE if someone made a better argument and build on it
Be decisive - what's the BEST course of action for THIS SPECIFIC EMAIL and why? No more hedging."""

        # Call LLM
        response = await self.call_llm(user_prompt, system_prompt)

        # Add message to state
        message = {
            "role": agent["role"],
            "icon": agent["icon"],
            "text": response,
            "timestamp": datetime.now().isoformat()
        }

        return message

    async def make_decision(self, state: AgentState) -> Dict[str, Any]:
        """Final decision maker synthesizes the discussion"""
        team_info = TEAMS[state["team"]]

        # Get the final decision maker (last agent)
        decision_maker = team_info["agents"][-1]

        # Build full conversation summary
        conversation_summary = "\n".join([
            f"{msg['role']}: {msg['text']}"
            for msg in state["messages"]
        ])

        system_prompt = f"""You are the {decision_maker['role']} at a Swiss bank. You are leading the {team_info['name']} team.

Your personality: {decision_maker['personality']}
Your responsibilities: {decision_maker['responsibilities']}

Your team just had a heated debate with different perspectives. You must now close the discussion with your final verdict."""

        user_prompt = f"""EMAIL BEING DISCUSSED:
Subject: {state['email_subject']}
From: {state['email_sender']}
Body: {state['email_body'][:300]}

TEAM DEBATE TRANSCRIPT:
{conversation_summary}

As {decision_maker['role']}, you've heard the debate about THIS SPECIFIC EMAIL. Now give your FINAL VERDICT with this structure:

**Opening (1-2 sentences):** Acknowledge the key debate points and reference the specific email details (subject, sender, or content). State which approach won and why.

**Decision:** State the decisive conclusion - what action we're taking about THIS EMAIL specifically.

**Action Items:**
• [First concrete action related to this email]
• [Second concrete action]
• [Third concrete action]

**Risk Note:** One sentence about key risks related to this specific type of email.

Keep the tone natural and authoritative, like a real team leader closing a meeting."""

        response = await self.call_llm(user_prompt, system_prompt)

        decision = {
            "decision_maker": decision_maker["role"],
            "decision_text": response,
            "timestamp": datetime.now().isoformat(),
            "team": state["team"]
        }

        return decision

    async def run_investment_analysis(
        self,
        email_id: int,
        email_subject: str,
        email_body: str,
        email_sender: str,
        on_message_callback = None
    ) -> Dict[str, Any]:
        """
        Run investment research workflow for the Investment Team
        Uses specialized tools for stock analysis
        """
        try:
            # Import the investment workflow
            from investment_workflow import investment_workflow

            # Extract company/ticker from email
            # Look for stock analysis request in subject or body
            combined_text = f"{email_subject} {email_body}".lower()

            # Extract company name or ticker (simple pattern matching)
            company = self._extract_company_from_text(combined_text)

            if not company:
                company = "the requested company"

            # Send initial message
            if on_message_callback:
                await on_message_callback({
                    "role": "Investment Research Team",
                    "icon": "📈",
                    "text": f"Starting comprehensive stock analysis for {company}...",
                    "timestamp": datetime.now().isoformat()
                }, [])

            # Run the investment analysis workflow
            async def progress_callback(update):
                if on_message_callback:
                    await on_message_callback(update, [])

            analysis = await investment_workflow.analyze_stock(
                company,
                on_progress_callback=progress_callback
            )

            # Format the results as messages
            all_messages = []
            team_info = TEAMS["investments"]

            # Add messages for each stage
            for i, stage_data in enumerate(analysis["stages"]):
                agent_name = stage_data["agent"]

                # Find matching agent icon
                agent_icon = "💼"
                for agent in team_info["agents"]:
                    if agent["role"] == agent_name:
                        agent_icon = agent["icon"]
                        break

                # Create message with stage results
                message_text = self._format_investment_stage_message(
                    stage_data["stage"],
                    stage_data["data"]
                )

                message = {
                    "role": agent_name,
                    "icon": agent_icon,
                    "text": message_text,
                    "timestamp": datetime.now().isoformat(),
                    "is_decision": (stage_data["stage"] == "recommendation")
                }

                all_messages.append(message)

                if on_message_callback:
                    await on_message_callback(message, all_messages)
                    await asyncio.sleep(0.5)  # Delay for UX

            return {
                "status": "completed",
                "team": "investments",
                "team_name": team_info["name"],
                "email_id": email_id,
                "messages": all_messages,
                "decision": analysis.get("final_recommendation", {}),
                "rounds": len(analysis["stages"]),
                "investment_analysis": analysis
            }

        except Exception as e:
            # Fallback to standard team discussion if workflow fails
            print(f"Investment workflow error: {e}")
            return await self._run_standard_discussion("investments", email_id, email_subject, email_body, email_sender, on_message_callback)

    def _extract_company_from_text(self, text: str) -> str:
        """Extract company name or ticker from text"""
        # Simple extraction - look for common patterns
        patterns = [
            r"analysis for (?:stock )?([A-Z]{1,5})\b",  # Ticker symbols
            r"analyze ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",  # Company names
            r"stock (Apple|Microsoft|Amazon|Tesla|Google|Meta|Netflix)",  # Common companies
        ]

        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _format_investment_stage_message(self, stage: str, data: Dict[str, Any]) -> str:
        """Format investment analysis stage data into a readable message"""
        if stage == "research":
            summary = data.get('summary', 'Data collection completed')
            has_10k = 'Available' if '10-K' in str(data.get('10k_filing', '')) and 'N/A' not in str(data.get('10k_filing', '')) else 'Not Available'
            has_10q = 'Available' if '10-Q' in str(data.get('10q_filing', '')) and 'N/A' not in str(data.get('10q_filing', '')) else 'Not Available'

            return f"""📊 **Research & Data Collection Complete**

**Data Sources Accessed:**
✓ Financial news and market data
✓ SEC 10-K Filing: {has_10k}
✓ SEC 10-Q Filing: {has_10q}
✓ Company website and investor relations

**Research Summary:**
{summary}"""

        elif stage == "financial_analysis":
            analysis = data.get('analysis', 'Financial analysis in progress...')
            return f"""💰 **Financial Analysis & Valuation**

{analysis}"""

        elif stage == "market_analysis":
            analysis = data.get('analysis', 'Market analysis in progress...')
            news_count = data.get('news_sources_count', 0)

            return f"""🌐 **Market Context & Competitive Analysis**

{analysis}

*Analysis based on {news_count} recent news sources*"""

        elif stage == "recommendation":
            executive_summary = data.get('executive_summary', 'Generating final recommendation...')
            company = data.get('company', 'the company')

            return f"""📋 **Executive Investment Recommendation for {company}**

{executive_summary}

---
*This recommendation is based on comprehensive analysis of SEC filings, market data, financial metrics, and industry trends available as of {data.get('analysis_date', 'today')}.*"""

        return str(data)

    async def _run_standard_discussion(self, team: str, email_id: int, email_subject: str, email_body: str, email_sender: str, on_message_callback):
        """Fallback to standard discussion format"""
        team_info = TEAMS[team]
        # Simplified discussion for fallback
        all_messages = []

        for agent in team_info["agents"]:
            message = {
                "role": agent["role"],
                "icon": agent["icon"],
                "text": f"Analyzing the email regarding {email_subject}...",
                "timestamp": datetime.now().isoformat()
            }
            all_messages.append(message)
            if on_message_callback:
                await on_message_callback(message, all_messages)

        return {
            "status": "completed",
            "team": team,
            "team_name": team_info["name"],
            "email_id": email_id,
            "messages": all_messages,
            "decision": {"decision_text": "Analysis completed."},
            "rounds": 1
        }

    async def run_team_discussion(
        self,
        email_id: int,
        email_subject: str,
        email_body: str,
        email_sender: str,
        team: str,
        max_rounds: int = 3,
        on_message_callback = None
    ) -> Dict[str, Any]:
        """Run a full team discussion on an email with optional real-time callbacks"""

        if team not in TEAMS:
            raise ValueError(f"Unknown team: {team}")

        # Special handling for Investment Team - use research workflow
        if team == "investments":
            return await self.run_investment_analysis(
                email_id,
                email_subject,
                email_body,
                email_sender,
                on_message_callback
            )

        team_info = TEAMS[team]

        # Initialize state
        state: AgentState = {
            "email_id": email_id,
            "email_subject": email_subject,
            "email_body": email_body,
            "email_sender": email_sender,
            "team": team,
            "messages": [],
            "current_speaker": "",
            "round": 0,
            "max_rounds": max_rounds,
            "decision": None,
            "completed": False
        }

        all_messages = []

        # Each agent speaks in multiple rounds for debate
        for round_num in range(max_rounds):
            for agent in team_info["agents"][:-1]:  # All except decision maker
                message = await self.agent_speaks(state, agent)
                state["messages"].append(message)
                all_messages.append(message)

                # Call callback if provided (for real-time updates)
                if on_message_callback:
                    await on_message_callback(message, all_messages)

                # Small delay for realistic pacing (reduced for CPU performance)
                await asyncio.sleep(0.1)

            # Update round counter after all agents speak
            state["round"] += 1

        # Final decision
        decision = await self.make_decision(state)
        state["decision"] = decision
        state["completed"] = True

        # Add decision as final message
        decision_message = {
            "role": decision["decision_maker"],
            "icon": team_info["agents"][-1]["icon"],
            "text": decision["decision_text"],
            "timestamp": decision["timestamp"],
            "is_decision": True
        }
        all_messages.append(decision_message)

        # Call callback for final decision
        if on_message_callback:
            await on_message_callback(decision_message, all_messages)

        return {
            "status": "completed",
            "team": team,
            "team_name": team_info["name"],
            "email_id": email_id,
            "messages": all_messages,
            "decision": decision,
            "rounds": state["round"]
        }


# ============================================================================
# TEAM ROUTING LOGIC
# ============================================================================

def detect_team_for_email(email_subject: str, email_body: str) -> str:
    """Detect which team should handle an email based on content (keyword-based fallback)"""
    combined = (email_subject + " " + email_body).lower()

    if any(word in combined for word in ['stock analysis', 'stock research', 'equity analysis', 'company analysis', 'investment research', 'stock recommendation', 'financial analysis']):
        return 'investments'
    elif any(word in combined for word in ['fraud', 'suspicious', 'wire transfer', 'phishing', 'bec', 'scam', 'unauthorized', 'security breach']):
        return 'fraud'
    elif any(word in combined for word in ['compliance', 'regulatory', 'fatca', 'regulation', 'legal', 'audit', 'aml', 'kyc']):
        return 'compliance'

    # Default to fraud for security-related inquiries
    return 'fraud'


async def suggest_team_for_email_llm(email_subject: str, email_body: str, email_sender: str = "") -> str:
    """
    Use LLM to intelligently suggest which team should handle an email.
    Analyzes email content and matches with team expertise.
    """
    # Build team descriptions for LLM
    team_descriptions = []
    for team_key, team_data in TEAMS.items():
        agents_summary = ", ".join([agent["role"] for agent in team_data["agents"]])
        team_descriptions.append(f"- {team_key}: {team_data['name']} (Specialists: {agents_summary})")

    teams_text = "\n".join(team_descriptions)

    system_prompt = """You are an intelligent email routing system for a Swiss bank. Your task is to analyze incoming emails and suggest which specialized team should handle them.

Available teams:
- fraud: 🔍 Fraud Investigation Unit (handles suspicious activities, wire transfer issues, phishing, scams, security breaches, unauthorized transactions)
- compliance: ⚖️ Compliance & Regulatory Affairs (handles regulatory matters, legal questions, audit issues, AML, KYC, FATCA)
- investments: 📈 Investment Research Team (handles stock analysis, equity research, company analysis, investment recommendations, financial analysis)

Analyze the email and respond with ONLY the team key (e.g., 'fraud', 'compliance', or 'investments'). No explanation, just the team key."""

    user_prompt = f"""EMAIL TO ANALYZE:
Subject: {email_subject}
From: {email_sender}
Body: {email_body[:800]}

Which team should handle this email? Respond with only the team key."""

    try:
        # Call LLM for suggestion
        response = await orchestrator.call_llm(user_prompt, system_prompt)

        # Clean and validate response
        suggested_team = response.strip().lower()

        # Extract team key if LLM included extra text
        for team_key in TEAMS.keys():
            if team_key in suggested_team:
                return team_key

        # Fallback to keyword-based detection if LLM response is unclear
        return detect_team_for_email(email_subject, email_body)

    except Exception as e:
        print(f"Error in LLM team suggestion: {e}")
        # Fallback to keyword-based detection
        return detect_team_for_email(email_subject, email_body)


# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE
# ============================================================================

# Load OpenAI configuration from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

orchestrator = AgenticTeamOrchestrator(
    openai_api_key=openai_api_key,
    openai_model=openai_model
)
