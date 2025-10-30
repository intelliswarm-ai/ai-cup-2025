"""
Agentic Virtual Bank Teams
Multi-agent collaboration system using LangGraph
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import httpx

from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

TEAMS = {
    "credit_risk": {
        "name": "🏦 Credit Risk Committee",
        "agents": [
            {
                "role": "Senior Credit Analyst",
                "icon": "👔",
                "personality": "Analytical and detail-oriented. Always starts by breaking down financial metrics. Uses phrases like 'Looking at the numbers...' and 'From a credit perspective...'",
                "responsibilities": "Analyze creditworthiness, financial ratios, debt capacity, and repayment ability",
                "style": "Data-driven, methodical, cautious"
            },
            {
                "role": "Risk Manager",
                "icon": "🛡️",
                "personality": "Conservative and protective. Focuses on downside scenarios. Often says 'What if...' and 'We need to consider the risks...'",
                "responsibilities": "Assess risk exposure, stress scenarios, collateral adequacy, and portfolio impact",
                "style": "Risk-averse, thorough, questioning"
            },
            {
                "role": "Relationship Manager",
                "icon": "💼",
                "personality": "Client-focused and diplomatic. Balances risk with opportunity. Uses phrases like 'The client has been...' and 'This relationship represents...'",
                "responsibilities": "Evaluate client relationship value, cross-sell opportunities, long-term potential",
                "style": "Diplomatic, balanced, opportunity-focused"
            },
            {
                "role": "Chief Risk Officer",
                "icon": "👨‍💼",
                "personality": "Strategic and decisive. Synthesizes input and makes final call. Says 'Based on the discussion...' and 'Here's what we'll do...'",
                "responsibilities": "Make final decision, set conditions, approve or decline with rationale",
                "style": "Authoritative, strategic, conclusive"
            }
        ]
    },
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
    "wealth": {
        "name": "💼 Wealth Management Advisory",
        "agents": [
            {
                "role": "Senior Wealth Advisor",
                "icon": "💼",
                "personality": "Client-centric and advisory. Understands client goals. Says 'Based on the client's objectives...' and 'I would recommend...'",
                "responsibilities": "Understand client goals, risk tolerance, time horizon, and constraints",
                "style": "Advisory, client-focused, holistic"
            },
            {
                "role": "Investment Specialist",
                "icon": "📈",
                "personality": "Market-savvy and analytical. Discusses investments. Uses phrases like 'Current market conditions...' and 'The portfolio allocation should...'",
                "responsibilities": "Recommend asset allocation, investment products, portfolio construction",
                "style": "Analytical, market-aware, strategic"
            },
            {
                "role": "Tax Consultant",
                "icon": "💰",
                "personality": "Detail-oriented and optimization-focused. Finds tax efficiencies. Says 'From a tax perspective...' and 'We can optimize by...'",
                "responsibilities": "Analyze tax implications, optimize tax efficiency, consider jurisdictions",
                "style": "Detail-oriented, optimization-focused, technical"
            },
            {
                "role": "Estate Planning Expert",
                "icon": "🏛️",
                "personality": "Long-term thinking and legacy-focused. Plans for generations. Uses phrases like 'Looking long-term...' and 'For wealth preservation...'",
                "responsibilities": "Plan wealth transfer, estate structures, succession planning, legacy goals",
                "style": "Long-term, legacy-focused, strategic"
            }
        ]
    },
    "corporate": {
        "name": "🏢 Corporate Banking Team",
        "agents": [
            {
                "role": "Corporate Relationship Manager",
                "icon": "🤝",
                "personality": "Business-savvy and relationship-focused. Understands corporate needs. Says 'The company's business model...' and 'This supports their strategy...'",
                "responsibilities": "Understand business model, strategic objectives, relationship potential",
                "style": "Business-savvy, relationship-focused, strategic"
            },
            {
                "role": "Trade Finance Specialist",
                "icon": "🌍",
                "personality": "Process-oriented and international. Knows trade mechanics. Uses phrases like 'The trade flow indicates...' and 'For cross-border transactions...'",
                "responsibilities": "Structure trade finance, letters of credit, export financing, guarantees",
                "style": "Process-oriented, international, technical"
            },
            {
                "role": "Treasury Expert",
                "icon": "💵",
                "personality": "Financial and liquidity-focused. Manages cash flows. Says 'The treasury position...' and 'Cash flow management requires...'",
                "responsibilities": "Analyze liquidity needs, cash management, FX hedging, interest rate risk",
                "style": "Financial, liquidity-focused, technical"
            },
            {
                "role": "Syndication Lead",
                "icon": "📊",
                "personality": "Deal-making and collaborative. Coordinates large deals. Uses phrases like 'We can syndicate with...' and 'The deal structure should...'",
                "responsibilities": "Structure syndicated facilities, coordinate with other banks, risk distribution",
                "style": "Deal-making, collaborative, strategic"
            }
        ]
    },
    "operations": {
        "name": "⚙️ Operations & Quality",
        "agents": [
            {
                "role": "Operations Manager",
                "icon": "⚙️",
                "personality": "Process-driven and efficiency-focused. Improves operations. Says 'The current process...' and 'We can streamline by...'",
                "responsibilities": "Analyze processes, identify bottlenecks, improve efficiency, quality control",
                "style": "Process-driven, efficiency-focused, systematic"
            },
            {
                "role": "Quality Assurance Lead",
                "icon": "✓",
                "personality": "Standards-focused and error-catching. Ensures quality. Uses phrases like 'Quality standards require...' and 'I've identified issues with...'",
                "responsibilities": "Check quality standards, identify errors, ensure compliance with procedures",
                "style": "Standards-focused, critical, thorough"
            },
            {
                "role": "Technology Liaison",
                "icon": "💻",
                "personality": "Tech-savvy and solution-oriented. Finds technical fixes. Says 'The system should...' and 'We can automate...'",
                "responsibilities": "Assess technical solutions, system capabilities, automation opportunities",
                "style": "Tech-savvy, solution-oriented, innovative"
            },
            {
                "role": "Customer Service Lead",
                "icon": "👥",
                "personality": "Empathetic and customer-focused. Champions client experience. Uses phrases like 'From the customer's perspective...' and 'We need to ensure satisfaction...'",
                "responsibilities": "Evaluate customer impact, satisfaction, communication strategy, resolution",
                "style": "Empathetic, customer-focused, communicative"
            }
        ]
    }
}


# ============================================================================
# LANGCHAIN/LANGGRAPH STATE AND WORKFLOW
# ============================================================================

class AgentState(TypedDict):
    """State for the multi-agent conversation"""
    email_id: int
    email_subject: str
    email_body: str
    email_sender: str
    team: str
    messages: Annotated[List[Dict[str, Any]], "The conversation messages"]
    current_speaker: str
    round: int
    max_rounds: int
    decision: Optional[Dict[str, Any]]
    completed: bool


class AgenticTeamOrchestrator:
    """Orchestrates multi-agent team discussions using LangGraph"""

    def __init__(self, openai_api_key: str = None, openai_model: str = "gpt-4o-mini", ollama_url: str = "http://ollama:11434"):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=120.0)

        # Determine which LLM to use
        self.use_openai = bool(openai_api_key and openai_api_key != "your_openai_api_key_here")

        if self.use_openai:
            print(f"[AgenticTeamOrchestrator] Using OpenAI API with model: {self.openai_model}")
        else:
            print(f"[AgenticTeamOrchestrator] Using Ollama at {self.ollama_url}")

    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """Call LLM (OpenAI or Ollama) based on configuration"""
        try:
            if self.use_openai:
                return await self._call_openai(prompt, system_message)
            else:
                return await self._call_ollama(prompt, system_message)
        except Exception as e:
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
                    "model": "tinyllama:latest",
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 100  # Limit response length for speed
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

                # Small delay for realistic pacing
                await asyncio.sleep(0.5)

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

    if any(word in combined for word in ['credit', 'loan', 'financing', 'credit line', 'credit increase']):
        return 'credit_risk'
    elif any(word in combined for word in ['fraud', 'suspicious', 'wire transfer', 'phishing', 'bec', 'scam']):
        return 'fraud'
    elif any(word in combined for word in ['compliance', 'regulatory', 'fatca', 'regulation', 'legal', 'audit']):
        return 'compliance'
    elif any(word in combined for word in ['wealth', 'investment', 'portfolio', 'inheritance', 'estate']):
        return 'wealth'
    elif any(word in combined for word in ['corporate', 'trade finance', 'letter of credit', 'import', 'export']):
        return 'corporate'
    elif any(word in combined for word in ['complaint', 'customer service', 'quality', 'operations', 'issue']):
        return 'operations'

    return 'credit_risk'  # default


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
- credit_risk: 🏦 Credit Risk Committee (handles loan requests, credit analysis, financing decisions)
- fraud: 🔍 Fraud Investigation Unit (handles suspicious activities, wire transfer issues, phishing, scams)
- compliance: ⚖️ Compliance & Regulatory Affairs (handles regulatory matters, legal questions, audit issues)
- wealth: 💼 Wealth Management Advisory (handles investment queries, portfolio management, estate planning)
- corporate: 🏢 Corporate Banking Team (handles corporate clients, trade finance, treasury services)
- operations: ⚙️ Operations & Quality (handles customer complaints, process issues, service quality)

Analyze the email and respond with ONLY the team key (e.g., 'fraud' or 'credit_risk'). No explanation, just the team key."""

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
