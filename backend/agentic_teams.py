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

    def __init__(self, ollama_url: str = "http://ollama:11434"):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """Call Ollama LLM using /api/generate endpoint"""
        try:
            # Combine system message and prompt for generate endpoint
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"

            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:latest",
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result["response"]
            else:
                return f"Error calling LLM: {response.status_code}"

        except Exception as e:
            return f"Error: {str(e)}"

    async def agent_speaks(self, state: AgentState, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response from a specific agent"""
        team_info = TEAMS[state["team"]]

        # Build context from previous messages
        conversation_context = "\n".join([
            f"{msg['role']}: {msg['text']}"
            for msg in state["messages"][-6:]  # Last 6 messages for context
        ])

        # Create agent-specific prompt
        system_prompt = f"""You are a {agent['role']} at a Swiss bank. You are part of the {team_info['name']} team.

Your personality: {agent['personality']}
Your responsibilities: {agent['responsibilities']}
Your communication style: {agent['style']}

You are analyzing an email and discussing it with your team. Provide your professional perspective in 2-3 sentences.
Stay in character and use your characteristic phrases. Be concise but insightful."""

        user_prompt = f"""EMAIL DETAILS:
Subject: {state['email_subject']}
From: {state['email_sender']}
Body: {state['email_body'][:500]}...

PREVIOUS DISCUSSION:
{conversation_context if conversation_context else "This is the start of the discussion."}

As {agent['role']}, provide your analysis and perspective on this email. What do you think about this situation?"""

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

Based on the team discussion, you must make a final decision and provide clear recommendations."""

        user_prompt = f"""TEAM DISCUSSION SUMMARY:
{conversation_summary}

As {decision_maker['role']}, synthesize the team's input and provide:
1. Your final decision/recommendation (in 1-2 sentences)
2. Key action items (2-3 bullet points)
3. Any conditions or caveats

Be decisive and clear. This is the final word from {team_info['name']}."""

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
        max_rounds: int = 2
    ) -> Dict[str, Any]:
        """Run a full team discussion on an email"""

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

        # Each agent speaks in order (1 round)
        for round_num in range(max_rounds):
            for agent in team_info["agents"][:-1]:  # All except decision maker
                message = await self.agent_speaks(state, agent)
                state["messages"].append(message)
                all_messages.append(message)

                # Small delay for realistic pacing
                await asyncio.sleep(0.5)

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
    """Detect which team should handle an email based on content"""
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


# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE
# ============================================================================

orchestrator = AgenticTeamOrchestrator()
