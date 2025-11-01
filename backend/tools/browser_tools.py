"""
Browser Tools for web scraping and content extraction
Provides website scraping and summarization capabilities
"""

import os
import httpx
from bs4 import BeautifulSoup
from typing import Optional


class BrowserTools:
    """Tools for scraping and analyzing web content"""

    def __init__(self):
        self.browserless_api_key = os.getenv("BROWSERLESS_API_KEY", "")
        self.use_browserless = bool(self.browserless_api_key and self.browserless_api_key.strip())

    async def scrape_website(self, url: str) -> str:
        """
        Scrape content from a website

        Args:
            url: URL to scrape

        Returns:
            Extracted text content
        """
        if self.use_browserless:
            return await self._scrape_with_browserless(url)
        else:
            return await self._scrape_with_httpx(url)

    async def _scrape_with_browserless(self, url: str) -> str:
        """Scrape using Browserless API (handles JavaScript)"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://chrome.browserless.io/content?token={self.browserless_api_key}",
                    json={
                        "url": url,
                        "waitFor": 2000  # Wait 2 seconds for page to load
                    }
                )

                if response.status_code == 200:
                    html_content = response.text
                    return self._extract_text_from_html(html_content)
                else:
                    return f"Failed to scrape {url}: Status {response.status_code}"
        except Exception as e:
            return f"Scraping error: {str(e)}"

    async def _scrape_with_httpx(self, url: str) -> str:
        """Scrape using simple HTTP requests (fallback)"""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return self._extract_text_from_html(response.text)
                else:
                    return f"Failed to fetch {url}: Status {response.status_code}"
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"

    def _extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Limit to first 3000 characters for LLM processing
            return text[:3000] if len(text) > 3000 else text
        except Exception as e:
            return f"Error parsing HTML: {str(e)}"

    async def scrape_and_summarize(self, url: str, objective: str = "summarize") -> str:
        """
        Scrape a website and provide a focused summary

        Args:
            url: URL to scrape
            objective: What to focus on when summarizing

        Returns:
            Summarized content
        """
        content = await self.scrape_website(url)

        if content.startswith("Failed") or content.startswith("Error"):
            return content

        # For now, return the content with a note
        # In a full implementation, this would call an LLM to summarize
        summary_header = f"Content from {url} (objective: {objective}):\n\n"

        # Truncate if too long
        if len(content) > 2000:
            content = content[:2000] + "\n\n... (content truncated)"

        return summary_header + content

    async def get_company_website_info(self, company_name: str) -> str:
        """
        Get information from a company's website

        Args:
            company_name: Name of the company

        Returns:
            Company information
        """
        # Construct likely company website URL
        company_slug = company_name.lower().replace(" ", "")
        url = f"https://www.{company_slug}.com/investor-relations"

        result = await self.scrape_website(url)

        # Try alternative if first attempt fails
        if result.startswith("Failed") or result.startswith("Error"):
            url = f"https://www.{company_slug}.com/about"
            result = await self.scrape_website(url)

        return f"Company Website Information for {company_name}:\n\n{result}"
