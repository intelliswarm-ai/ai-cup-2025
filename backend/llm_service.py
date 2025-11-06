import os
import json
import httpx
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama LLM"""

    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "ollama")
        self.port = os.getenv("OLLAMA_PORT", "11434")
        self.model = os.getenv("OLLAMA_MODEL", "phi3")
        self.base_url = f"http://{self.host}:{self.port}"
        self.model_loaded = False
        self.max_retries = 2

    async def check_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return True
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Is the service running?")
            return False
        except httpx.TimeoutException:
            logger.error(f"Ollama service at {self.base_url} timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False

    async def ensure_model_loaded(self):
        """Pull the model if it's not already available"""
        if self.model_loaded:
            return True

        try:
            # First check if Ollama is available
            if not await self.check_ollama_available():
                logger.error(f"Ollama service not available at {self.base_url}")
                return False

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model}
                )
                response.raise_for_status()
                logger.info(f"Model {self.model} is ready")
                self.model_loaded = True
                return True
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Is the service running?")
            return False
        except httpx.TimeoutException:
            logger.error(f"Model pull timed out for {self.model}")
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, retry_count: int = 0) -> str:
        """Generate text using Ollama with automatic retry logic"""
        # Ensure model is loaded before attempting to generate
        if not self.model_loaded:
            model_ready = await self.ensure_model_loaded()
            if not model_ready:
                raise ConnectionError(f"Ollama service not available at {self.base_url}")

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes for CPU-only Ollama
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except httpx.ConnectError as e:
            logger.error(f"Connection error to Ollama: {e}")
            if retry_count < self.max_retries:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                # Reset model loaded flag to force recheck
                self.model_loaded = False
                return await self.generate(prompt, system_prompt, retry_count + 1)
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error from Ollama: {e}")
            raise TimeoutError(f"Ollama request timed out after 300 seconds")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Ollama returned error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    async def summarize_email(self, subject: str, body: str) -> str:
        """Generate a concise summary of an email"""
        system_prompt = """Summarize emails concisely. Focus on the main point."""

        prompt = f"""Summarize this email in 1-2 sentences:

Subject: {subject}
Body: {body[:1200]}

Summary:"""

        try:
            summary = await self.generate(prompt, system_prompt)
            return summary.strip()
        except ConnectionError as e:
            logger.error(f"Connection error summarizing email: {e}")
            return "AI service unavailable - please check if Ollama is running"
        except TimeoutError as e:
            logger.error(f"Timeout error summarizing email: {e}")
            return "AI summary timed out - try again later"
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return f"Error generating summary: {type(e).__name__}"

    async def extract_call_to_actions(self, subject: str, body: str) -> List[str]:
        """Extract call-to-actions from an email"""
        system_prompt = """You extract action items from emails. Return only valid JSON array format."""

        prompt = f"""Email: {subject}

{body[:1000]}

List any actions the recipient should take. Return ONLY a JSON array like: ["action1", "action2"]
If no actions needed, return: []

JSON array:"""

        try:
            response = await self.generate(prompt, system_prompt)
            # Try to parse JSON from response
            response = response.strip()

            # Sometimes the LLM wraps it in markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            # Try to find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                ctas = json.loads(json_str)

                # Handle format: [{"action": "text"}] or [{"task": "text"}] -> ["text", ...]
                if isinstance(ctas, list) and len(ctas) > 0:
                    if isinstance(ctas[0], dict):
                        # Try different key names that LLM might use
                        result = []
                        for item in ctas:
                            if isinstance(item, dict):
                                # Try common keys: action, task, cta, description, text
                                value = item.get("action") or item.get("task") or item.get("cta") or item.get("description") or item.get("text")
                                if value and isinstance(value, str):
                                    result.append(value)
                        return result if result else []
                    elif isinstance(ctas[0], str):
                        return ctas

                return []

            return []
        except Exception as e:
            logger.error(f"Error extracting CTAs: {e}")
            return []

    async def process_email(self, subject: str, body: str) -> Dict:
        """Process an email: generate summary and extract CTAs"""
        try:
            # Check Ollama availability once before processing
            if not self.model_loaded and not await self.ensure_model_loaded():
                return {
                    "summary": "AI service unavailable - please check if Ollama is running",
                    "call_to_actions": []
                }

            summary = await self.summarize_email(subject, body)
            ctas = await self.extract_call_to_actions(subject, body)

            return {
                "summary": summary,
                "call_to_actions": ctas
            }
        except ConnectionError as e:
            logger.error(f"Connection error processing email: {e}")
            return {
                "summary": "AI service unavailable - please check if Ollama is running",
                "call_to_actions": []
            }
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {
                "summary": f"Error processing email: {type(e).__name__}",
                "call_to_actions": []
            }

    async def aggregate_summaries(self, summaries: List[str]) -> str:
        """Create a summary of summaries"""
        if not summaries:
            return "No emails to summarize"

        system_prompt = """You are an AI assistant that creates executive summaries.
Combine multiple email summaries into one cohesive overview.
Focus on the most important points and themes."""

        prompt = f"""Create an executive summary from these email summaries:

{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(summaries))}

Provide a brief overview (3-4 sentences) highlighting the main themes and important points."""

        try:
            aggregate = await self.generate(prompt, system_prompt)
            return aggregate.strip()
        except Exception as e:
            logger.error(f"Error aggregating summaries: {e}")
            return "Error creating aggregate summary"

    async def aggregate_call_to_actions(self, all_ctas: List[List[str]]) -> List[str]:
        """Aggregate and deduplicate call-to-actions"""
        flat_ctas = [cta for ctas in all_ctas for cta in ctas]

        if not flat_ctas:
            return []

        # Deduplicate similar CTAs using LLM
        system_prompt = """You are an AI assistant that consolidates similar action items.
Remove duplicates and similar items, keeping only unique actions.
Return ONLY a JSON array of unique action items."""

        prompt = f"""Consolidate these action items by removing duplicates and very similar items:

{chr(10).join(f'- {cta}' for cta in flat_ctas)}

Return ONLY a JSON array of unique, consolidated action items.
Format: ["action 1", "action 2", ...]"""

        try:
            response = await self.generate(prompt, system_prompt)
            response = response.strip()

            # Extract JSON array
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                consolidated = json.loads(json_str)
                return consolidated if isinstance(consolidated, list) else flat_ctas[:10]

            # Fallback: return top 10 unique
            return list(set(flat_ctas))[:10]
        except Exception as e:
            logger.error(f"Error consolidating CTAs: {e}")
            return list(set(flat_ctas))[:10]

    async def detect_email_badges(self, subject: str, body: str, sender: str, is_phishing: bool) -> List[str]:
        """Detect appropriate badges for an email

        Available badges: MEETING, RISK, EXTERNAL, AUTOMATED, VIP, FOLLOW_UP, NEWSLETTER, FINANCE

        IMPORTANT: For phishing emails, ONLY return RISK badge to keep UI clean and focused.
        """
        badges = []

        # RISK badge - if phishing detected
        # For phishing emails, ONLY show RISK badge - no other informational badges
        if is_phishing:
            badges.append("RISK")
            return badges  # Skip all other badge detection for phishing emails

        # For safe emails, detect informational badges
        system_prompt = """You are an email categorization assistant. Analyze emails and assign relevant badges.
Available badges: MEETING, EXTERNAL, AUTOMATED, VIP, FOLLOW_UP, NEWSLETTER, FINANCE
Return ONLY a JSON array of applicable badges."""

        prompt = f"""Analyze this email and determine which badges apply:

Subject: {subject}
Sender: {sender}
Body: {body[:800]}

Guidelines:
- MEETING: Contains meeting invites, calendar events, scheduling
- EXTERNAL: From external/unknown domains or partners
- AUTOMATED: Auto-generated, no-reply, system notifications
- VIP: From important contacts, executives, key stakeholders
- FOLLOW_UP: Follow-up emails, reminders, pending responses
- NEWSLETTER: Marketing emails, newsletters, bulk communications
- FINANCE: Financial transactions, invoices, payment-related

Return ONLY a JSON array like: ["MEETING", "EXTERNAL"] or []"""

        try:
            response = await self.generate(prompt, system_prompt)
            response = response.strip()

            # Extract JSON array
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                detected_badges = json.loads(json_str)
                if isinstance(detected_badges, list):
                    badges.extend(detected_badges)
        except Exception as e:
            logger.error(f"Error detecting badges: {e}")

        # Remove duplicates and return
        return list(set(badges))

    async def generate_quick_reply_drafts(self, subject: str, body: str, sender: str) -> Dict[str, str]:
        """Generate 3 quick reply drafts as responses TO the received email"""

        system_prompt = """You are an email reply assistant. Generate appropriate REPLY emails responding to the received email.
Each reply should directly address the content, questions, or requests in the original email.
Be helpful, professional, and concise. You MUST return valid JSON only."""

        prompt = f"""You received this email:

Subject: {subject}
From: {sender}
Email Body:
{body[:1000]}

Generate 3 different REPLY emails that respond to this email. Each reply should:
- Acknowledge the email and its content
- Address any questions, requests, or action items
- Be appropriate for replying to the sender

Create 3 reply versions in different tones:

1. FORMAL - Professional, corporate tone. Start with "Dear [Name]" or "Hello". End with professional closing.
2. FRIENDLY - Warm, conversational tone. Start with "Hi" or "Hey". Be personable but professional.
3. BRIEF - Very short, to-the-point reply. 1-2 sentences acknowledging and responding to key points.

Return ONLY a valid JSON object with this exact format (no other text):
{{
  "formal": "Dear [Name],\n\n[Professional reply addressing the email content]\n\nBest regards",
  "friendly": "Hi [Name]!\n\n[Friendly reply addressing the email content]\n\nCheers",
  "brief": "[Short 1-2 sentence response]"
}}"""

        try:
            response = await self.generate(prompt, system_prompt)
            logger.info(f"Raw LLM response for quick reply drafts (length: {len(response)})")
            logger.debug(f"Full response: {response[:500]}")

            response = response.strip()

            # Strategy 1: Remove markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]).strip()

            # Strategy 2: Find JSON object boundaries
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]

                # Strategy 3: Try to fix common JSON issues
                # Replace smart quotes with regular quotes
                json_str = json_str.replace('\u201c', '"').replace('\u201d', '"')
                json_str = json_str.replace('\u2018', "'").replace('\u2019', "'")

                # Try parsing
                try:
                    drafts = json.loads(json_str)

                    # Validate structure
                    if isinstance(drafts, dict) and all(k in drafts for k in ["formal", "friendly", "brief"]):
                        logger.info("Successfully parsed quick reply drafts")
                        return drafts
                    else:
                        logger.warning(f"Parsed JSON but missing required keys. Got: {list(drafts.keys())}")
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error at position {je.pos}: {je.msg}")
                    logger.error(f"Problematic JSON substring: {json_str[max(0, je.pos-50):je.pos+50]}")

                    # Strategy 4: Try regex extraction as fallback
                    import re
                    formal_match = re.search(r'"formal"\s*:\s*"([^"]+)"', json_str)
                    friendly_match = re.search(r'"friendly"\s*:\s*"([^"]+)"', json_str)
                    brief_match = re.search(r'"brief"\s*:\s*"([^"]+)"', json_str)

                    if formal_match and friendly_match and brief_match:
                        logger.info("Extracted drafts using regex fallback")
                        return {
                            "formal": formal_match.group(1),
                            "friendly": friendly_match.group(1),
                            "brief": brief_match.group(1)
                        }

            logger.warning("Could not extract valid JSON from LLM response, using fallback")

        except Exception as e:
            logger.error(f"Error generating reply drafts: {e}", exc_info=True)

        # Fallback drafts - generic replies when LLM fails
        logger.info("Using fallback quick reply drafts")
        return {
            "formal": f"Dear {sender.split('@')[0].title()},\n\nThank you for your email regarding '{subject}'. I have received your message and will review the details carefully. I will respond with a complete answer shortly.\n\nBest regards",
            "friendly": f"Hi {sender.split('@')[0].title()}!\n\nThanks for reaching out about '{subject}'. I got your message and I'll look into this for you. I'll get back to you soon with more info!\n\nCheers",
            "brief": f"Thanks for your email about '{subject}'. I'll respond shortly."
        }

# Global instance
ollama_service = OllamaService()
