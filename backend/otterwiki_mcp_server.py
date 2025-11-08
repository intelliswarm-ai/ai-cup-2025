"""
OtterWiki MCP Server
Custom MCP server for querying OtterWiki knowledge base
Provides fraud and compliance related information from wiki pages
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK not installed for server. Install with: pip install mcp")

# Import wiki enrichment from existing code
import sys
sys.path.append(str(Path(__file__).parent))

from email_enrichment import WikiEnrichment


logger = logging.getLogger(__name__)


class OtterWikiMCPServer:
    """
    MCP Server for OtterWiki knowledge base

    Provides tools for:
    - Searching wiki pages by topic
    - Getting fraud-related policies
    - Getting compliance procedures
    - Querying risk management guidelines
    """

    def __init__(self, wiki_data_path: str = None):
        if not wiki_data_path:
            wiki_data_path = os.getenv("OTTERWIKI_DATA_PATH", "/app/otterwiki_data/repository")

        self.wiki_data_path = wiki_data_path
        self.wiki_enrichment = None
        self.server = None

        if MCP_AVAILABLE:
            self.server = Server("otterwiki")
            self._register_tools()

    def _register_tools(self):
        """Register all available tools with the MCP server"""
        if not self.server:
            return

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available OtterWiki tools"""
            return [
                Tool(
                    name="search_wiki",
                    description="Search OtterWiki pages for specific topics or keywords. Returns relevant wiki pages with content.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for wiki pages (e.g., 'fraud detection', 'compliance procedures')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_fraud_policies",
                    description="Get fraud detection policies and procedures from wiki",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_compliance_procedures",
                    description="Get compliance procedures and regulatory guidelines from wiki",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_risk_guidelines",
                    description="Get risk management and assessment guidelines from wiki",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_page_by_title",
                    description="Get a specific wiki page by its title",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Exact title of the wiki page"
                            }
                        },
                        "required": ["title"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls"""
            # Initialize wiki enrichment if not already done
            if not self.wiki_enrichment:
                self.wiki_enrichment = WikiEnrichment()
                await self.wiki_enrichment.initialize()

            if name == "search_wiki":
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 5)
                results = await self._search_wiki(query, max_results)
                return [TextContent(type="text", text=results)]

            elif name == "get_fraud_policies":
                results = await self._get_fraud_policies()
                return [TextContent(type="text", text=results)]

            elif name == "get_compliance_procedures":
                results = await self._get_compliance_procedures()
                return [TextContent(type="text", text=results)]

            elif name == "get_risk_guidelines":
                results = await self._get_risk_guidelines()
                return [TextContent(type="text", text=results)]

            elif name == "get_page_by_title":
                title = arguments.get("title", "")
                results = await self._get_page_by_title(title)
                return [TextContent(type="text", text=results)]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _search_wiki(self, query: str, max_results: int = 5) -> str:
        """Search wiki pages for query"""
        if not self.wiki_enrichment or not self.wiki_enrichment.pages:
            return "Wiki not initialized or no pages available."

        # Use ChromaDB to search for relevant pages
        try:
            # Search using semantic similarity
            if self.wiki_enrichment.collection:
                results = self.wiki_enrichment.collection.query(
                    query_texts=[query],
                    n_results=min(max_results, len(self.wiki_enrichment.pages))
                )

                if results and results['documents']:
                    formatted_results = []
                    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                        page_title = metadata.get('title', 'Unknown')
                        formatted_results.append(f"**Page {i+1}: {page_title}**\n{doc}\n")

                    return "\n\n".join(formatted_results)
                else:
                    return "No matching wiki pages found."
            else:
                # Fallback to keyword search
                matching_pages = []
                query_lower = query.lower()
                for page in self.wiki_enrichment.pages:
                    if query_lower in page.get('title', '').lower() or query_lower in page.get('content', '').lower():
                        matching_pages.append(page)
                        if len(matching_pages) >= max_results:
                            break

                if matching_pages:
                    formatted_results = []
                    for i, page in enumerate(matching_pages):
                        title = page.get('title', 'Unknown')
                        content = page.get('content', '')[:500]  # First 500 chars
                        formatted_results.append(f"**Page {i+1}: {title}**\n{content}...\n")

                    return "\n\n".join(formatted_results)
                else:
                    return "No matching wiki pages found."

        except Exception as e:
            logger.error(f"Error searching wiki: {e}")
            return f"Error searching wiki: {str(e)}"

    async def _get_fraud_policies(self) -> str:
        """Get fraud detection policies from wiki"""
        # Search for fraud-related pages
        results = await self._search_wiki("fraud detection policy procedure", max_results=3)
        if results and "No matching" not in results:
            return f"## Fraud Detection Policies\n\n{results}"
        else:
            return "No fraud detection policies found in wiki. Please add relevant policies to OtterWiki."

    async def _get_compliance_procedures(self) -> str:
        """Get compliance procedures from wiki"""
        # Search for compliance-related pages
        results = await self._search_wiki("compliance procedure regulatory guideline", max_results=3)
        if results and "No matching" not in results:
            return f"## Compliance Procedures\n\n{results}"
        else:
            return "No compliance procedures found in wiki. Please add relevant procedures to OtterWiki."

    async def _get_risk_guidelines(self) -> str:
        """Get risk management guidelines from wiki"""
        # Search for risk-related pages
        results = await self._search_wiki("risk management assessment guideline", max_results=3)
        if results and "No matching" not in results:
            return f"## Risk Management Guidelines\n\n{results}"
        else:
            return "No risk management guidelines found in wiki. Please add relevant guidelines to OtterWiki."

    async def _get_page_by_title(self, title: str) -> str:
        """Get a specific wiki page by title"""
        if not self.wiki_enrichment or not self.wiki_enrichment.pages:
            return "Wiki not initialized or no pages available."

        # Find page with matching title
        for page in self.wiki_enrichment.pages:
            if page.get('title', '').lower() == title.lower():
                page_title = page.get('title', 'Unknown')
                page_content = page.get('content', 'No content')
                return f"## {page_title}\n\n{page_content}"

        return f"Page '{title}' not found in wiki."

    async def run(self):
        """Run the MCP server"""
        if not MCP_AVAILABLE:
            logger.error("MCP SDK not available. Cannot start server.")
            return

        if not self.server:
            logger.error("Server not initialized.")
            return

        # Initialize wiki enrichment
        logger.info(f"Initializing OtterWiki MCP server with data path: {self.wiki_data_path}")
        self.wiki_enrichment = WikiEnrichment()
        await self.wiki_enrichment.initialize()
        logger.info(f"Loaded {len(self.wiki_enrichment.pages) if self.wiki_enrichment.pages else 0} wiki pages")

        # Start the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


# Standalone server entry point
if __name__ == "__main__":
    import asyncio

    async def main():
        server = OtterWikiMCPServer()
        await server.run()

    asyncio.run(main())
