"""
Search Tools for investment research
Provides internet search capabilities for gathering market data and news
"""

import os
import json
import httpx
from typing import List, Dict, Any


class SearchTools:
    """Tools for searching the internet for investment information"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")
        self.use_serper = bool(self.serper_api_key and self.serper_api_key.strip())

    async def search_internet(self, query: str, num_results: int = 5) -> str:
        """
        Search the internet for information

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            Formatted search results as a string
        """
        if self.use_serper:
            return await self._search_with_serper(query, num_results)
        else:
            return await self._search_fallback(query, num_results)

    async def _search_with_serper(self, query: str, num_results: int) -> str:
        """Search using Serper API (Google Search)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._format_serper_results(data)
                else:
                    return f"Search failed with status {response.status_code}"
        except Exception as e:
            return f"Search error: {str(e)}"

    def _format_serper_results(self, data: Dict[str, Any]) -> str:
        """Format Serper API results"""
        results = []

        # Add organic results
        for i, result in enumerate(data.get("organic", [])[:5], 1):
            title = result.get("title", "")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            results.append(f"{i}. {title}\n   {snippet}\n   {link}\n")

        # Add knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            results.insert(0, f"Knowledge Graph: {kg.get('title', '')}\n{kg.get('description', '')}\n")

        return "\n".join(results) if results else "No results found"

    async def _search_fallback(self, query: str, num_results: int) -> str:
        """Fallback search method (mock results for demo)"""
        return f"""Search Results for: {query}

1. Recent Market Analysis - {query}
   Latest market trends and analysis for {query}. Comprehensive financial data and expert opinions.
   https://finance.example.com/analysis/{query.replace(' ', '-')}

2. Stock Performance Report
   Detailed performance metrics and historical data for {query}.
   https://investing.example.com/stocks/{query.replace(' ', '-')}

3. Industry News - {query}
   Breaking news and updates affecting {query} and related sectors.
   https://news.example.com/markets/{query.replace(' ', '-')}

Note: Using mock search results (SERPER_API_KEY not configured).
To enable real search, set SERPER_API_KEY in environment variables."""

    async def search_news(self, query: str, days: int = 7) -> str:
        """
        Search for recent news articles

        Args:
            query: News search query
            days: Number of days back to search

        Returns:
            Formatted news results
        """
        news_query = f"{query} news last {days} days"
        return await self.search_internet(news_query, num_results=5)

    async def search_financial_data(self, symbol: str) -> str:
        """
        Search for financial data about a stock

        Args:
            symbol: Stock ticker symbol

        Returns:
            Financial information
        """
        query = f"{symbol} stock price financials revenue earnings"
        return await self.search_internet(query, num_results=5)
