import httpx
import os
from typing import List, Dict, Optional
from datetime import datetime

class MailPitClient:
    def __init__(self):
        self.host = os.getenv("MAILPIT_HOST", "mailpit")
        self.port = os.getenv("MAILPIT_PORT", "8025")
        self.base_url = f"http://{self.host}:{self.port}/api/v1"

    async def get_messages(self, limit: int = 100, start: int = 0) -> Dict:
        """Fetch messages from MailPit API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/messages",
                params={"limit": limit, "start": start}
            )
            response.raise_for_status()
            return response.json()

    async def get_message(self, message_id: str) -> Dict:
        """Fetch a single message by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/message/{message_id}")
            response.raise_for_status()
            return response.json()

    async def get_message_text(self, message_id: str) -> str:
        """Get message text content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/message/{message_id}/text")
            response.raise_for_status()
            return response.text

    async def get_message_html(self, message_id: str) -> str:
        """Get message HTML content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/message/{message_id}/html")
            response.raise_for_status()
            return response.text

    async def search_messages(self, query: str) -> Dict:
        """Search messages"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={"query": query}
            )
            response.raise_for_status()
            return response.json()

    async def get_statistics(self) -> Dict:
        """Get MailPit statistics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/info")
            response.raise_for_status()
            return response.json()
