"""
Base Tool Framework
Provides the foundation for all tools in the system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolType(Enum):
    """Types of tools available"""
    API = "api"
    PROPRIETARY = "proprietary"
    MCP = "mcp"
    PUBLIC = "public"


class ToolCapability(Enum):
    """Standard capabilities tools can provide"""
    SEARCH = "search"
    SCRAPE = "scrape"
    ANALYZE = "analyze"
    VALIDATE = "validate"
    CALCULATE = "calculate"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    REPORT = "report"


@dataclass
class ToolMetadata:
    """Metadata describing a tool"""
    name: str
    tool_type: ToolType
    description: str
    provider: str
    capabilities: List[ToolCapability]
    version: str = "1.0.0"
    category: Optional[str] = None

    # Configuration requirements
    required_env_vars: List[str] = None
    optional_env_vars: List[str] = None

    # API information
    api_endpoint: Optional[str] = None
    api_docs_url: Optional[str] = None

    # Rate limits and costs
    rate_limit: Optional[str] = None
    cost_per_call: Optional[float] = None

    # Dependencies
    requires_mcp: bool = False
    requires_database: bool = False

    def __post_init__(self):
        if self.required_env_vars is None:
            self.required_env_vars = []
        if self.optional_env_vars is None:
            self.optional_env_vars = []


class BaseTool(ABC):
    """
    Base class for all tools in the system.

    All tools must inherit from this class and implement:
    - get_metadata(): Return tool metadata
    - is_available(): Check if tool is configured and ready
    - get_methods(): Return available methods

    Optional:
    - validate_config(): Validate configuration
    - get_test_example(): Provide test case
    """

    def __init__(self):
        """Initialize the tool"""
        self._metadata = self.get_metadata()
        self._is_configured = self._check_configuration()

    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """
        Return metadata describing this tool

        Returns:
            ToolMetadata: Tool metadata
        """
        pass

    def is_available(self) -> bool:
        """
        Check if tool is available (configured with necessary API keys, etc.)

        Returns:
            bool: True if tool is ready to use
        """
        return self._is_configured

    def _check_configuration(self) -> bool:
        """
        Check if all required environment variables are set

        Returns:
            bool: True if properly configured
        """
        import os

        metadata = self.get_metadata()
        for env_var in metadata.required_env_vars:
            if not os.getenv(env_var):
                return False
        return True

    def get_methods(self) -> List[Dict[str, Any]]:
        """
        Get list of available methods this tool provides

        Returns:
            List of method information dicts
        """
        import inspect

        methods = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            # Skip private methods and base class methods
            if name.startswith('_') or name in ['get_metadata', 'is_available', 'get_methods', 'validate_config', 'get_test_example']:
                continue

            doc = inspect.getdoc(method) or "No description available"
            signature = inspect.signature(method)

            # Extract first line of docstring as description
            description = doc.split('\n\n')[0].replace('\n', ' ').strip()

            methods.append({
                "name": name,
                "description": description,
                "signature": str(signature),
                "full_doc": doc
            })

        return methods

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate tool configuration

        Returns:
            Dict with validation results
        """
        import os

        metadata = self.get_metadata()
        results = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "present": [],
            "is_configured": self._is_configured
        }

        # Check required
        for env_var in metadata.required_env_vars:
            if os.getenv(env_var):
                results["present"].append(env_var)
            else:
                results["missing_required"].append(env_var)
                results["valid"] = False

        # Check optional
        for env_var in metadata.optional_env_vars:
            if not os.getenv(env_var):
                results["missing_optional"].append(env_var)

        return results

    def get_readiness_status(self) -> Dict[str, Any]:
        """
        Get detailed readiness status showing what's configured and what's missing.
        This allows users to see if a tool is ready to use before plugging it in.

        Returns:
            Dict with detailed readiness information
        """
        import os

        metadata = self.get_metadata()

        # Check environment variables
        required_configured = []
        required_missing = []
        optional_configured = []
        optional_missing = []

        for env_var in metadata.required_env_vars:
            value = os.getenv(env_var)
            if value:
                required_configured.append({
                    "name": env_var,
                    "configured": True,
                    "value_preview": self._mask_value(value)
                })
            else:
                required_missing.append({
                    "name": env_var,
                    "configured": False,
                    "required": True
                })

        for env_var in metadata.optional_env_vars:
            value = os.getenv(env_var)
            if value:
                optional_configured.append({
                    "name": env_var,
                    "configured": True,
                    "value_preview": self._mask_value(value)
                })
            else:
                optional_missing.append({
                    "name": env_var,
                    "configured": False,
                    "required": False
                })

        # Determine overall status
        is_ready = len(required_missing) == 0

        # Build status message
        if is_ready:
            if len(optional_missing) == 0:
                status_message = "✅ Tool is fully configured and ready to use"
            else:
                status_message = f"✅ Tool is ready to use (optional: {', '.join([m['name'] for m in optional_missing])} not configured)"
        else:
            missing_names = [m['name'] for m in required_missing]
            status_message = f"⚠️ Tool requires configuration. Missing: {', '.join(missing_names)}"

        return {
            "is_ready": is_ready,
            "is_active": self.is_available(),
            "status_message": status_message,
            "required": {
                "configured": required_configured,
                "missing": required_missing,
                "total": len(metadata.required_env_vars),
                "configured_count": len(required_configured)
            },
            "optional": {
                "configured": optional_configured,
                "missing": optional_missing,
                "total": len(metadata.optional_env_vars),
                "configured_count": len(optional_configured)
            },
            "dependencies": {
                "requires_mcp": metadata.requires_mcp,
                "requires_database": metadata.requires_database
            }
        }

    def _mask_value(self, value: str) -> str:
        """
        Mask sensitive values for display

        Args:
            value: Value to mask

        Returns:
            Masked value showing only first and last few characters
        """
        if not value:
            return ""

        if len(value) <= 8:
            return "*" * len(value)

        # Show first 4 and last 4 characters
        return f"{value[:4]}...{value[-4:]}"

    def get_test_example(self) -> Optional[Dict[str, Any]]:
        """
        Get a test example for this tool (optional)

        Returns:
            Dict with test information, or None
        """
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary representation for API responses

        Returns:
            Dict representation of tool
        """
        metadata = self.get_metadata()
        readiness = self.get_readiness_status()

        return {
            "name": metadata.name,
            "type": metadata.tool_type.value,
            "description": metadata.description,
            "provider": metadata.provider,
            "version": metadata.version,
            "category": metadata.category,
            "isActive": self.is_available(),
            "capabilities": [cap.value for cap in metadata.capabilities],
            "configuration": {
                "api_endpoint": metadata.api_endpoint,
                "api_docs_url": metadata.api_docs_url,
                "required_env_vars": metadata.required_env_vars,
                "optional_env_vars": metadata.optional_env_vars,
                "rate_limit": metadata.rate_limit,
                "cost_per_call": metadata.cost_per_call,
            },
            "readiness": readiness,
            "methods": self.get_methods()
        }
