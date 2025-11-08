"""
MCP (Model Context Protocol) Client
Connects to official MCP servers for fraud detection workflows
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK not installed. Install with: pip install mcp")


logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for connecting to Model Context Protocol servers

    Supports official MCP servers:
    - Memory: Knowledge graph-based persistent memory for fraud patterns
    - Filesystem: Secure file operations for fraud case files
    - Fetch: Web content fetching for external fraud intelligence
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.enabled = MCP_AVAILABLE and os.getenv("MCP_ENABLED", "false").lower() == "true"

        if not MCP_AVAILABLE and self.enabled:
            logger.error("MCP is enabled but SDK is not installed. Install with: pip install mcp")
            self.enabled = False

    async def connect_memory_server(self) -> bool:
        """
        Connect to Memory MCP server for fraud pattern storage

        Memory server provides knowledge graph capabilities:
        - Store fraud patterns
        - Query historical fraud signatures
        - Build relationship graphs between entities
        """
        if not self.enabled:
            logger.info("MCP not enabled, skipping Memory server connection")
            return False

        try:
            # Memory server configuration
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-memory"
                ],
                env=None
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize connection
            await session.initialize()

            self.sessions["memory"] = session
            logger.info("Connected to Memory MCP server")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Memory MCP server: {e}")
            return False

    async def connect_filesystem_server(self, allowed_path: str = None) -> bool:
        """
        Connect to Filesystem MCP server for fraud case files

        Args:
            allowed_path: Path to fraud case files directory

        Filesystem server provides:
        - Read fraud case files
        - Access audit logs
        - Inspect transaction records
        """
        if not self.enabled:
            logger.info("MCP not enabled, skipping Filesystem server connection")
            return False

        if not allowed_path:
            allowed_path = os.getenv("MCP_FRAUD_CASES_PATH", "/app/fraud_cases")

        try:
            # Filesystem server configuration
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    allowed_path
                ],
                env=None
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize connection
            await session.initialize()

            self.sessions["filesystem"] = session
            logger.info(f"Connected to Filesystem MCP server (path: {allowed_path})")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Filesystem MCP server: {e}")
            return False

    async def connect_fetch_server(self) -> bool:
        """
        Connect to Fetch MCP server for external fraud intelligence

        Fetch server provides:
        - Retrieve fraud reports from web sources
        - Access public fraud databases
        - Fetch merchant reputation data
        """
        if not self.enabled:
            logger.info("MCP not enabled, skipping Fetch server connection")
            return False

        try:
            # Fetch server configuration
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-fetch"
                ],
                env=None
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize connection
            await session.initialize()

            self.sessions["fetch"] = session
            logger.info("Connected to Fetch MCP server")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Fetch MCP server: {e}")
            return False

    async def connect_otterwiki_server(self) -> bool:
        """
        Connect to OtterWiki MCP server for wiki knowledge

        OtterWiki server provides:
        - Search wiki pages for fraud/compliance topics
        - Get fraud detection policies
        - Get compliance procedures
        - Get risk management guidelines
        """
        if not self.enabled:
            logger.info("MCP not enabled, skipping OtterWiki server connection")
            return False

        try:
            # OtterWiki server configuration
            # This is our custom server, so we run it as a Python script
            server_script_path = os.path.join(
                os.path.dirname(__file__),
                "otterwiki_mcp_server.py"
            )

            server_params = StdioServerParameters(
                command="python3",
                args=[server_script_path],
                env=None
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize connection
            await session.initialize()

            self.sessions["otterwiki"] = session
            logger.info("Connected to OtterWiki MCP server")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to OtterWiki MCP server: {e}")
            return False

    async def connect_duckduckgo_server(self) -> bool:
        """
        Connect to DuckDuckGo MCP server for web search (fallback to Serper)

        DuckDuckGo server provides:
        - Web search without API key
        - Unlimited free searches
        - Privacy-focused search
        - Merchant reputation research
        - Fraud report discovery
        """
        if not self.enabled:
            logger.info("MCP not enabled, skipping DuckDuckGo server connection")
            return False

        try:
            # DuckDuckGo server configuration
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "duckduckgo-mcp-server"
                ],
                env=None
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )

            # Initialize connection
            await session.initialize()

            self.sessions["duckduckgo"] = session
            logger.info("Connected to DuckDuckGo MCP server")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to DuckDuckGo MCP server: {e}")
            return False

    async def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """
        List available tools from an MCP server

        Args:
            server: Server name (memory, filesystem, fetch)

        Returns:
            List of available tools with their schemas
        """
        if server not in self.sessions:
            logger.warning(f"Server '{server}' not connected")
            return []

        try:
            response = await self.sessions[server].list_tools()
            return response.tools if hasattr(response, 'tools') else []
        except Exception as e:
            logger.error(f"Failed to list tools from {server}: {e}")
            return []

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on an MCP server

        Args:
            server: Server name (memory, filesystem, fetch)
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if server not in self.sessions:
            logger.warning(f"Server '{server}' not connected")
            return None

        try:
            response = await self.sessions[server].call_tool(tool_name, arguments)
            return response
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}' on {server}: {e}")
            return None

    async def store_fraud_pattern(
        self,
        pattern_id: str,
        pattern_data: Dict[str, Any]
    ) -> bool:
        """
        Store a fraud pattern in Memory server

        Args:
            pattern_id: Unique identifier for the pattern
            pattern_data: Pattern details (indicators, risk score, etc.)

        Returns:
            Success status
        """
        if "memory" not in self.sessions:
            logger.debug("Memory server not connected, pattern not stored")
            return False

        try:
            # Store pattern using Memory server's knowledge graph
            await self.call_tool(
                "memory",
                "create_entities",
                {
                    "entities": [{
                        "name": pattern_id,
                        "entityType": "fraud_pattern",
                        "observations": [str(pattern_data)]
                    }]
                }
            )
            logger.info(f"Stored fraud pattern: {pattern_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store fraud pattern: {e}")
            return False

    async def query_fraud_patterns(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Query fraud patterns from Memory server

        Args:
            query: Search query for patterns

        Returns:
            Matching fraud patterns
        """
        if "memory" not in self.sessions:
            logger.debug("Memory server not connected, returning empty patterns")
            return []

        try:
            # Query patterns using Memory server
            result = await self.call_tool(
                "memory",
                "search_nodes",
                {"query": query}
            )
            return result if result else []
        except Exception as e:
            logger.error(f"Failed to query fraud patterns: {e}")
            return []

    async def read_fraud_case(
        self,
        case_file_path: str
    ) -> Optional[str]:
        """
        Read a fraud case file from Filesystem server

        Args:
            case_file_path: Path to the case file

        Returns:
            Case file contents
        """
        if "filesystem" not in self.sessions:
            logger.debug("Filesystem server not connected, cannot read case file")
            return None

        try:
            # Read file using Filesystem server
            result = await self.call_tool(
                "filesystem",
                "read_file",
                {"path": case_file_path}
            )
            return result if result else None
        except Exception as e:
            logger.error(f"Failed to read fraud case file: {e}")
            return None

    async def fetch_fraud_intelligence(
        self,
        url: str
    ) -> Optional[str]:
        """
        Fetch external fraud intelligence using Fetch server

        Args:
            url: URL to fetch fraud data from

        Returns:
            Fetched content
        """
        if "fetch" not in self.sessions:
            logger.debug("Fetch server not connected, cannot fetch intelligence")
            return None

        try:
            # Fetch content using Fetch server
            result = await self.call_tool(
                "fetch",
                "fetch",
                {"url": url}
            )
            return result if result else None
        except Exception as e:
            logger.error(f"Failed to fetch fraud intelligence: {e}")
            return None

    async def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search using DuckDuckGo MCP server (fallback to Serper)

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, link, snippet
        """
        if "duckduckgo" not in self.sessions:
            logger.debug("DuckDuckGo server not connected, cannot search")
            return None

        try:
            # Search using DuckDuckGo MCP server
            result = await self.call_tool(
                "duckduckgo",
                "duckduckgo_search",
                {
                    "query": query,
                    "max_results": max_results
                }
            )

            # Parse results from MCP response
            if result and hasattr(result, 'content'):
                # MCP servers return content as a list of content blocks
                content_blocks = result.content if isinstance(result.content, list) else [result.content]

                # Extract text from content blocks
                search_results = []
                for block in content_blocks:
                    if hasattr(block, 'text'):
                        # Try to parse as JSON if it looks like structured data
                        import json
                        try:
                            parsed = json.loads(block.text)
                            if isinstance(parsed, list):
                                search_results.extend(parsed)
                            elif isinstance(parsed, dict):
                                search_results.append(parsed)
                        except json.JSONDecodeError:
                            # Return as plain text result
                            search_results.append({
                                "title": f"Result for: {query}",
                                "snippet": block.text,
                                "link": ""
                            })

                return search_results[:max_results] if search_results else None

            return result if result else None

        except Exception as e:
            logger.error(f"Failed to search with DuckDuckGo: {e}")
            return None

    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        try:
            await self.exit_stack.aclose()
            self.sessions.clear()
            logger.info("Disconnected from all MCP servers")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP servers: {e}")

    def is_connected(self, server: str) -> bool:
        """Check if connected to a specific server"""
        return server in self.sessions


# Global MCP client instance
mcp_client = MCPClient()


# Initialization function for FastAPI startup
async def initialize_mcp_servers():
    """
    Initialize MCP server connections at application startup
    Call this from FastAPI's startup event
    """
    if not mcp_client.enabled:
        logger.info("MCP integration is disabled")
        return

    logger.info("Initializing MCP servers for fraud detection...")

    # Connect to Memory server for fraud pattern storage
    await mcp_client.connect_memory_server()

    # Connect to Filesystem server for fraud case files
    await mcp_client.connect_filesystem_server()

    # Connect to Fetch server for external intelligence
    await mcp_client.connect_fetch_server()

    # Connect to OtterWiki server for wiki knowledge
    await mcp_client.connect_otterwiki_server()

    # Connect to DuckDuckGo server for web search (fallback to Serper)
    await mcp_client.connect_duckduckgo_server()

    # List available tools from each server
    for server_name in ["memory", "filesystem", "fetch", "otterwiki", "duckduckgo"]:
        if mcp_client.is_connected(server_name):
            tools = await mcp_client.list_tools(server_name)
            logger.info(f"{server_name.capitalize()} server tools: {[t.get('name', 'unknown') for t in tools]}")


# Cleanup function for FastAPI shutdown
async def shutdown_mcp_servers():
    """
    Disconnect from MCP servers at application shutdown
    Call this from FastAPI's shutdown event
    """
    await mcp_client.disconnect_all()
