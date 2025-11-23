"""
Entity Resolver Tools for compliance analysis
Resolves ticker symbols to company names, gets company information
"""

import httpx
from typing import Dict, Any, Optional


class EntityResolver:
    """Tools for resolving entity information"""

    def __init__(self):
        # Yahoo Finance alternative API (free, no API key needed)
        self.ticker_api_url = "https://query1.finance.yahoo.com/v1/finance/search"

    async def resolve_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Resolve a ticker symbol to company information

        Args:
            ticker: Stock ticker symbol (e.g., "IMPP", "TSLA", "AAPL")

        Returns:
            Dictionary with company information
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.ticker_api_url,
                    params={
                        "q": ticker,
                        "quotesCount": 1,
                        "newsCount": 0
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    quotes = data.get("quotes", [])

                    if quotes and len(quotes) > 0:
                        quote = quotes[0]

                        # Extract company information
                        company_name = quote.get("longname") or quote.get("shortname", ticker)
                        exchange = quote.get("exchDisp", "Unknown")
                        ticker_type = quote.get("quoteType", "Unknown")

                        return {
                            "ticker": ticker,
                            "company_name": company_name,
                            "exchange": exchange,
                            "type": ticker_type,
                            "symbol": quote.get("symbol", ticker),
                            "resolved": True,
                            "data_source": "Yahoo Finance API"
                        }

                    else:
                        return {
                            "ticker": ticker,
                            "resolved": False,
                            "error": "Ticker not found",
                            "message": f"No company found for ticker symbol '{ticker}'"
                        }

                else:
                    return {
                        "ticker": ticker,
                        "resolved": False,
                        "error": "API_ERROR",
                        "message": f"Ticker resolution API returned error: HTTP {response.status_code}"
                    }

        except Exception as e:
            print(f"Error resolving ticker {ticker}: {e}")
            return {
                "ticker": ticker,
                "resolved": False,
                "error": "API_ERROR",
                "message": f"Failed to resolve ticker: {str(e)}"
            }

    async def resolve_entity(self, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """
        Resolve entity information
        If it looks like a ticker, resolve it to company name

        Args:
            entity_name: Entity name or ticker
            entity_type: Type of entity

        Returns:
            Resolved entity information
        """
        # Check if this looks like a ticker (2-5 capital letters)
        is_potential_ticker = (
            len(entity_name) >= 2 and
            len(entity_name) <= 5 and
            entity_name.isupper() and
            entity_name.isalpha()
        )

        if is_potential_ticker and entity_type == "company":
            # Try to resolve as ticker
            ticker_info = await self.resolve_ticker(entity_name)

            if ticker_info.get("resolved"):
                return {
                    "original_input": entity_name,
                    "resolved_name": ticker_info["company_name"],
                    "entity_type": "company",
                    "ticker": entity_name,
                    "exchange": ticker_info.get("exchange"),
                    "resolution_method": "ticker_lookup",
                    "additional_info": {
                        "symbol": ticker_info.get("symbol"),
                        "type": ticker_info.get("type")
                    }
                }
            else:
                # Ticker resolution failed, use original name
                return {
                    "original_input": entity_name,
                    "resolved_name": entity_name,
                    "entity_type": entity_type,
                    "resolution_method": "no_resolution",
                    "warning": f"Could not resolve ticker '{entity_name}' - using as-is"
                }

        # Not a ticker, return original name
        return {
            "original_input": entity_name,
            "resolved_name": entity_name,
            "entity_type": entity_type,
            "resolution_method": "no_resolution"
        }

    async def enrich_entity_info(
        self,
        entity_name: str,
        entity_type: str
    ) -> Dict[str, Any]:
        """
        Enrich entity information with additional context

        Args:
            entity_name: Entity name
            entity_type: Entity type

        Returns:
            Enriched entity information
        """
        resolved = await self.resolve_entity(entity_name, entity_type)

        enriched = {
            "input_name": entity_name,
            "resolved_name": resolved.get("resolved_name", entity_name),
            "entity_type": entity_type,
            "is_ticker": resolved.get("resolution_method") == "ticker_lookup",
            "additional_context": {}
        }

        if resolved.get("ticker"):
            enriched["additional_context"]["ticker_symbol"] = resolved["ticker"]
            enriched["additional_context"]["exchange"] = resolved.get("exchange")

        return enriched
