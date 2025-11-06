"""
SEC Tools for accessing company filings
Provides access to 10-Q, 10-K, and other SEC documents
"""

import os
import httpx
from typing import Optional, Dict, Any


class SECTools:
    """Tools for querying SEC filings and financial documents"""

    def __init__(self):
        self.sec_api_key = os.getenv("SEC_API_KEY", "")
        self.use_sec_api = bool(self.sec_api_key and self.sec_api_key.strip())
        self.base_url = "https://api.sec-api.io"

    async def get_10k(self, ticker: str) -> str:
        """
        Get the latest 10-K filing for a company

        Args:
            ticker: Stock ticker symbol

        Returns:
            10-K filing information
        """
        if self.use_sec_api:
            return await self._get_filing_with_api(ticker, "10-K")
        else:
            return await self._get_filing_fallback(ticker, "10-K")

    async def get_10q(self, ticker: str) -> str:
        """
        Get the latest 10-Q filing for a company

        Args:
            ticker: Stock ticker symbol

        Returns:
            10-Q filing information
        """
        if self.use_sec_api:
            return await self._get_filing_with_api(ticker, "10-Q")
        else:
            return await self._get_filing_fallback(ticker, "10-Q")

    async def _get_filing_with_api(self, ticker: str, form_type: str) -> str:
        """Get filing using SEC API"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Search for the latest filing
                response = await client.get(
                    f"{self.base_url}/filings",
                    params={
                        "token": self.sec_api_key,
                        "ticker": ticker,
                        "formType": form_type,
                        "limit": 1
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("filings"):
                        filing = data["filings"][0]
                        return self._format_filing(filing, ticker, form_type)
                    else:
                        return f"No {form_type} filing found for {ticker}"
                else:
                    return f"SEC API error: Status {response.status_code}"
        except Exception as e:
            return f"Error accessing SEC API: {str(e)}"

    def _format_filing(self, filing: Dict[str, Any], ticker: str, form_type: str) -> str:
        """Format SEC filing data"""
        filing_date = filing.get("filedAt", "Unknown")
        period_of_report = filing.get("periodOfReport", "Unknown")
        url = filing.get("linkToFilingDetails", "")

        result = f"""{form_type} Filing for {ticker.upper()}

Filing Date: {filing_date}
Period Ending: {period_of_report}
Document URL: {url}

Key Sections:
"""

        # Extract key financial data if available
        if "sections" in filing:
            sections = filing["sections"]
            for section in sections[:5]:  # First 5 sections
                result += f"- {section.get('name', 'Unknown')}\n"

        # Add financial highlights if available
        if "financialData" in filing:
            result += "\nFinancial Highlights:\n"
            fin_data = filing["financialData"]
            for key, value in list(fin_data.items())[:10]:
                result += f"- {key}: {value}\n"

        return result

    async def _get_filing_fallback(self, ticker: str, form_type: str) -> str:
        """Fallback method using free SEC EDGAR API"""
        try:
            # Use SEC's EDGAR API (no key required)
            async with httpx.AsyncClient(
                timeout=60.0,
                headers={"User-Agent": "Investment Research Tool research@example.com"}
            ) as client:
                # Get company CIK
                cik_response = await client.get(
                    f"https://www.sec.gov/cgi-bin/browse-edgar",
                    params={
                        "action": "getcompany",
                        "ticker": ticker,
                        "type": form_type,
                        "dateb": "",
                        "owner": "exclude",
                        "count": 1,
                        "output": "json"
                    }
                )

                if cik_response.status_code == 200:
                    return f"""{form_type} Filing Information for {ticker.upper()}

Source: SEC EDGAR Database
URL: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={ticker}&type={form_type}

Note: Using fallback SEC data access (SEC_API_KEY not configured).
For enhanced filing analysis, set SEC_API_KEY in environment variables.

To view the full {form_type} filing:
1. Visit https://www.sec.gov/edgar/searchedgar/companysearch.html
2. Search for ticker: {ticker}
3. Look for the latest {form_type} filing

Key sections to review:
- Business Overview
- Risk Factors
- Financial Statements
- Management Discussion & Analysis
- Notes to Financial Statements"""
                else:
                    return f"Could not access SEC EDGAR for {ticker}"
        except Exception as e:
            return f"Error accessing SEC EDGAR: {str(e)}"

    async def search_filings(self, query: str, form_types: Optional[list] = None) -> str:
        """
        Search for SEC filings matching a query

        Args:
            query: Search query (company name, ticker, or keywords)
            form_types: List of form types to search (e.g., ["10-K", "10-Q"])

        Returns:
            Search results
        """
        if not form_types:
            form_types = ["10-K", "10-Q", "8-K"]

        if self.use_sec_api:
            return await self._search_with_api(query, form_types)
        else:
            return f"""SEC Filing Search: {query}
Form Types: {', '.join(form_types)}

To search SEC filings, visit:
https://www.sec.gov/edgar/search/

Or set SEC_API_KEY for programmatic access."""

    async def _search_with_api(self, query: str, form_types: list) -> str:
        """Search using SEC API"""
        try:
            results = []
            for form_type in form_types[:3]:  # Limit to 3 form types
                filing = await self._get_filing_with_api(query, form_type)
                results.append(filing)

            return "\n\n".join(results)
        except Exception as e:
            return f"Search error: {str(e)}"
