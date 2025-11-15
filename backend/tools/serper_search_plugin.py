"""
Serper Search Plugin Tool
Real implementation using Serper API
"""

import os
import requests
from typing import Dict, Any

from tool_framework import BaseTool, ToolMetadata, ToolType, ToolCapability


class SerperSearchPlugin(BaseTool):
    """
    Serper Search API plugin tool for internet searches.

    Provides access to Google search results via the Serper API.
    """

    def get_metadata(self) -> ToolMetadata:
        """Declare tool metadata"""
        return ToolMetadata(
            name="Serper Internet Search",
            tool_type=ToolType.API,
            description="Search the internet using Serper API (Google search results)",
            provider="Serper.dev",
            capabilities=[
                ToolCapability.SEARCH,
                ToolCapability.INVESTIGATE
            ],
            version="1.0.0",
            category="investment",  # Auto-assigns to investment team

            # Configuration
            required_env_vars=["SERPER_API_KEY"],
            optional_env_vars=[],

            # API Information
            api_endpoint="https://google.serper.dev/search",
            api_docs_url="https://serper.dev/docs",

            # Costs and Limits
            rate_limit="2,500 searches/month (free tier)",
            cost_per_call=0.001,  # $0.001 per search
        )

    def __init__(self):
        """Initialize the tool"""
        super().__init__()  # Must call parent init

        # Load configuration if available
        if self.is_available():
            self.api_key = os.getenv("SERPER_API_KEY")
            self.api_endpoint = "https://google.serper.dev/search"

    def search_internet(self, query: str, num_results: int = 10) -> str:
        """
        Search the internet using Serper API

        Args:
            query: Search query
            num_results: Maximum number of results to return (default: 10)

        Returns:
            Formatted search results
        """
        if not self.is_available():
            return "❌ Tool not configured. Please set SERPER_API_KEY environment variable."

        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": num_results
            }

            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                return self._format_results(data, query)
            else:
                return f"❌ API Error (Status {response.status_code}): {response.text}"

        except Exception as e:
            return f"❌ Search failed: {str(e)}"

    def _format_results(self, data: Dict[str, Any], query: str) -> str:
        """Format search results into readable text"""
        results_text = f"🔍 **Search Results for: {query}**\n\n"

        # Organic results
        if "organic" in data and data["organic"]:
            results_text += "**Top Results:**\n\n"
            for idx, result in enumerate(data["organic"][:10], 1):
                title = result.get("title", "No title")
                link = result.get("link", "")
                snippet = result.get("snippet", "No description")

                results_text += f"{idx}. **{title}**\n"
                results_text += f"   {snippet}\n"
                results_text += f"   🔗 {link}\n\n"

        # Knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            results_text += "\n**Knowledge Graph:**\n"
            if "title" in kg:
                results_text += f"**{kg['title']}**\n"
            if "description" in kg:
                results_text += f"{kg['description']}\n"
            if "website" in kg:
                results_text += f"🔗 {kg['website']}\n"

        return results_text

    def get_test_example(self) -> Dict[str, Any]:
        """Provide a test example for this tool"""
        return {
            "method": "search_internet",
            "params": {
                "query": "latest technology news",
                "num_results": 5
            },
            "expected_type": "string",
            "description": "Test internet search with recent tech news"
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        Custom configuration validation
        """
        # Get base validation results
        results = super().validate_config()

        # Add custom validation - test API connection
        if self.is_available():
            results["api_connection"] = {
                "endpoint": self.api_endpoint,
                "status": "configured",
                "note": "API key present and ready to use"
            }
        else:
            results["api_connection"] = {
                "status": "not_configured",
                "note": "SERPER_API_KEY not set in environment"
            }

        return results
