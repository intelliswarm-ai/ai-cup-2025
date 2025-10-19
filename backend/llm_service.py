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

    async def ensure_model_loaded(self):
        """Pull the model if it's not already available"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model}
                )
                response.raise_for_status()
                logger.info(f"Model {self.model} is ready")
                return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
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
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return "Error generating summary"

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

                # Handle format: [{"action": "text"}] -> ["text", ...]
                if isinstance(ctas, list) and len(ctas) > 0:
                    if isinstance(ctas[0], dict) and "action" in ctas[0]:
                        return [item["action"] for item in ctas if isinstance(item, dict) and "action" in item]
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
            summary = await self.summarize_email(subject, body)
            ctas = await self.extract_call_to_actions(subject, body)

            return {
                "summary": summary,
                "call_to_actions": ctas
            }
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {
                "summary": "Error processing email",
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

# Global instance
ollama_service = OllamaService()
