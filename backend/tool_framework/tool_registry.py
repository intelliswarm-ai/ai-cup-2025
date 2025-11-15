"""
Tool Registry
Central registry for all available tools with dynamic discovery
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from tool_framework.base_tool import BaseTool, ToolCapability

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all tools in the system.

    Features:
    - Auto-discovery of tools from tools/ directory
    - Tool registration and lookup
    - Capability-based tool search
    - Tool assignment to workflows/teams
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._team_assignments: Dict[str, List[str]] = {}

    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class

        Args:
            tool_class: Tool class to register
        """
        try:
            # Instantiate tool
            tool_instance = tool_class()
            metadata = tool_instance.get_metadata()

            tool_name = metadata.name
            self._tools[tool_name] = tool_instance
            self._tool_classes[tool_name] = tool_class

            logger.info(f"Registered tool: {tool_name} ({metadata.provider})")

        except Exception as e:
            logger.error(f"Failed to register tool {tool_class.__name__}: {e}")

    def auto_discover_tools(self, tools_directory: str = "tools") -> None:
        """
        Automatically discover and register all tools in the tools directory

        Args:
            tools_directory: Directory containing tool modules
        """
        logger.info(f"Auto-discovering tools from: {tools_directory}")

        tools_path = Path(tools_directory)
        if not tools_path.exists():
            logger.warning(f"Tools directory not found: {tools_directory}")
            return

        # Import all Python files in tools directory
        for file_path in tools_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            module_name = file_path.stem
            try:
                # Import module
                module = importlib.import_module(f"{tools_directory}.{module_name}")

                # Find all classes that inherit from BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        # Found a tool class
                        logger.info(f"Discovered tool class: {name} in {module_name}")
                        self.register_tool(obj)

            except Exception as e:
                logger.error(f"Error importing {module_name}: {e}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None
        """
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools

        Returns:
            List of all tool instances
        """
        return list(self._tools.values())

    def get_available_tools(self) -> List[BaseTool]:
        """
        Get all available (configured) tools

        Returns:
            List of available tool instances
        """
        return [tool for tool in self._tools.values() if tool.is_available()]

    def search_by_capability(self, capability: ToolCapability) -> List[BaseTool]:
        """
        Search for tools by capability

        Args:
            capability: Capability to search for

        Returns:
            List of tools with that capability
        """
        matching_tools = []
        for tool in self._tools.values():
            metadata = tool.get_metadata()
            if capability in metadata.capabilities:
                matching_tools.append(tool)

        return matching_tools

    def search_by_category(self, category: str) -> List[BaseTool]:
        """
        Search for tools by category

        Args:
            category: Category to search for (e.g., "fraud", "investment")

        Returns:
            List of tools in that category
        """
        matching_tools = []
        for tool in self._tools.values():
            metadata = tool.get_metadata()
            if metadata.category and metadata.category.lower() == category.lower():
                matching_tools.append(tool)

        return matching_tools

    def assign_tools_to_team(self, team_key: str, tool_names: List[str]) -> None:
        """
        Assign specific tools to a team

        Args:
            team_key: Team identifier
            tool_names: List of tool names to assign
        """
        self._team_assignments[team_key] = tool_names
        logger.info(f"Assigned {len(tool_names)} tools to team '{team_key}'")

    def get_team_tools(self, team_key: str) -> List[BaseTool]:
        """
        Get tools assigned to a specific team

        Args:
            team_key: Team identifier

        Returns:
            List of tools assigned to that team
        """
        tool_names = self._team_assignments.get(team_key, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def auto_assign_by_category(self) -> None:
        """
        Automatically assign tools to teams based on their category
        """
        for tool in self._tools.values():
            metadata = tool.get_metadata()
            if metadata.category:
                team_key = metadata.category.lower()
                if team_key not in self._team_assignments:
                    self._team_assignments[team_key] = []
                if metadata.name not in self._team_assignments[team_key]:
                    self._team_assignments[team_key].append(metadata.name)

        logger.info("Auto-assigned tools to teams based on categories")

    def get_registry_stats(self) -> Dict:
        """
        Get statistics about the registry

        Returns:
            Dict with registry statistics
        """
        total_tools = len(self._tools)
        available_tools = len(self.get_available_tools())
        tools_by_type = {}
        tools_by_category = {}

        for tool in self._tools.values():
            metadata = tool.get_metadata()

            # Count by type
            tool_type = metadata.tool_type.value
            tools_by_type[tool_type] = tools_by_type.get(tool_type, 0) + 1

            # Count by category
            if metadata.category:
                tools_by_category[metadata.category] = tools_by_category.get(metadata.category, 0) + 1

        return {
            "total_tools": total_tools,
            "available_tools": available_tools,
            "unavailable_tools": total_tools - available_tools,
            "tools_by_type": tools_by_type,
            "tools_by_category": tools_by_category,
            "teams": list(self._team_assignments.keys()),
            "team_assignments": {k: len(v) for k, v in self._team_assignments.items()}
        }

    def to_dict(self) -> Dict:
        """
        Convert registry to dictionary representation

        Returns:
            Dict representation of registry
        """
        return {
            "tools": [tool.to_dict() for tool in self._tools.values()],
            "stats": self.get_registry_stats()
        }


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance (singleton)

    Returns:
        ToolRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()
        # Auto-discover tools on first access
        _global_registry.auto_discover_tools()
        # Auto-assign tools to teams based on categories
        _global_registry.auto_assign_by_category()

    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)"""
    global _global_registry
    _global_registry = None
