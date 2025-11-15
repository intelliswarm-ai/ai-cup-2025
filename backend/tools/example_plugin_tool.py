"""
Example Plugin Tool
Demonstrates how to create a new tool using the plugin architecture
"""

import os
from typing import Dict, Any

from tool_framework import BaseTool, ToolMetadata, ToolType, ToolCapability


class ExamplePluginTool(BaseTool):
    """
    Example tool showing the plugin architecture.

    This tool demonstrates:
    - How to inherit from BaseTool
    - How to declare metadata
    - How to implement methods
    - How to handle configuration
    - How to provide test examples
    """

    def get_metadata(self) -> ToolMetadata:
        """Declare tool metadata"""
        return ToolMetadata(
            name="Example Plugin Tool",
            tool_type=ToolType.API,
            description="Example tool demonstrating the plugin architecture with search and analysis capabilities",
            provider="Example Provider Inc.",
            capabilities=[
                ToolCapability.SEARCH,
                ToolCapability.ANALYZE,
                ToolCapability.VALIDATE
            ],
            version="1.0.0",
            category="fraud",  # Auto-assigns to fraud team

            # Configuration
            required_env_vars=["EXAMPLE_API_KEY"],
            optional_env_vars=["EXAMPLE_API_ENDPOINT", "EXAMPLE_RATE_LIMIT"],

            # API Information
            api_endpoint="https://api.example.com/v1",
            api_docs_url="https://docs.example.com",

            # Costs and Limits
            rate_limit="1000 requests/day",
            cost_per_call=0.001,  # $0.001 per call
        )

    def __init__(self):
        """Initialize the tool"""
        super().__init__()  # Must call parent init

        # Load configuration if available
        if self.is_available():
            self.api_key = os.getenv("EXAMPLE_API_KEY")
            self.api_endpoint = os.getenv("EXAMPLE_API_ENDPOINT", "https://api.example.com/v1")
            self.rate_limit = int(os.getenv("EXAMPLE_RATE_LIMIT", "1000"))

    async def search_data(self, query: str, limit: int = 10) -> str:
        """
        Search for data using the Example API

        This method demonstrates how to:
        - Document your method (shown in API)
        - Accept parameters
        - Return results

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results as formatted string
        """
        if not self.is_available():
            return "Tool not configured. Please set EXAMPLE_API_KEY environment variable."

        # Simulate API call
        results = f"""Example Search Results for: "{query}"

Found {limit} results:

1. Result One - Relevant information about {query}
2. Result Two - More details on {query}
3. Result Three - Additional context for {query}

API Endpoint Used: {self.api_endpoint}
Rate Limit Remaining: {self.rate_limit - 1}/day

This is a mock result. In production, this would call:
{self.api_endpoint}/search?q={query}&limit={limit}
"""

        return results

    async def analyze_pattern(self, data: Dict[str, Any]) -> str:
        """
        Analyze a pattern in the provided data

        Args:
            data: Data to analyze (dict with keys: transactions, user_id, etc.)

        Returns:
            Analysis results
        """
        if not self.is_available():
            return "Tool not configured."

        user_id = data.get("user_id", "unknown")
        transaction_count = data.get("transaction_count", 0)

        analysis = f"""Pattern Analysis Results:

**User ID**: {user_id}
**Transactions Analyzed**: {transaction_count}

**Findings**:
- Pattern Type: Normal
- Risk Score: 12/100 (Low)
- Anomalies Detected: 0

**Recommendations**:
- Continue monitoring
- No immediate action required

This is a mock analysis. Real implementation would use:
{self.api_endpoint}/analyze
"""

        return analysis

    async def validate_entity(self, entity_type: str, entity_value: str) -> str:
        """
        Validate an entity (email, phone, IP, etc.)

        Args:
            entity_type: Type of entity (email, phone, ip, etc.)
            entity_value: Value to validate

        Returns:
            Validation results
        """
        if not self.is_available():
            return "Tool not configured."

        validation = f"""Entity Validation Results:

**Type**: {entity_type}
**Value**: {entity_value}

**Validation Status**: ✓ Valid
**Exists**: Yes
**Risk Level**: Low
**Additional Info**:
- Format: Valid
- Blacklisted: No
- Reputation: Good

This is a mock validation. Real implementation would call:
{self.api_endpoint}/validate/{entity_type}
"""

        return validation

    def get_test_example(self) -> Dict[str, Any]:
        """Provide a test example for this tool"""
        return {
            "method": "search_data",
            "params": {
                "query": "fraud detection",
                "limit": 5
            },
            "expected_type": "string",
            "description": "Test the search functionality with a sample query"
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        Custom configuration validation

        Extends the base validation with custom checks
        """
        # Get base validation results
        results = super().validate_config()

        # Add custom validation
        if self.is_available():
            # Test API connection (mock)
            results["api_test"] = {
                "endpoint": self.api_endpoint,
                "status": "reachable",
                "latency_ms": 45
            }

            # Check rate limit configuration
            if self.rate_limit < 100:
                results["warnings"] = results.get("warnings", [])
                results["warnings"].append("Rate limit is very low (< 100/day)")

        return results
