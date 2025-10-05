"""
GADK Tool Adapters

Wraps heuristics, memory services, LLM manager as GADK tools.
Provides the bridge between existing analysis tools and GADK runtime.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GADKToolAdapter:
    """Base adapter for converting analysis tools to GADK format."""
    
    def __init__(self, tool_name: str, tool_instance: Any):
        """Initialize the tool adapter."""
        self.tool_name = tool_name
        self.tool_instance = tool_instance
        
    def adapt_for_gadk(self) -> Dict[str, Any]:
        """Adapt the tool for GADK runtime."""
        # TODO: Implement GADK tool adaptation
        return {
            "name": self.tool_name,
            "instance": self.tool_instance,
            "adapted": True
        }


class ToolRegistry:
    """Registry for managing GADK tool adapters."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, GADKToolAdapter] = {}
        
    def register_tool(self, tool_name: str, tool_instance: Any):
        """Register a tool with the GADK runtime."""
        adapter = GADKToolAdapter(tool_name, tool_instance)
        self.tools[tool_name] = adapter
        logger.info(f"Registered tool: {tool_name}")
        
    def get_tool(self, tool_name: str) -> Optional[GADKToolAdapter]:
        """Get a registered tool adapter."""
        return self.tools.get(tool_name)
        
    def get_all_tools(self) -> Dict[str, GADKToolAdapter]:
        """Get all registered tool adapters."""
        return self.tools.copy()
        
    def unregister_tool(self, tool_name: str):
        """Unregister a tool from the registry."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")


# Global tool registry instance
tool_registry = ToolRegistry()