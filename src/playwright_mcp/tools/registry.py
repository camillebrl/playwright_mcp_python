"""Tool registry and execution."""

import logging
from typing import Any

from mcp.types import TextContent

from .base import ToolInfo, ToolResult
from .capture import CaptureTools
from .interaction import InteractionTools
from .navigation import NavigationTools
from .utility import UtilityTools

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self, browser_manager) -> None:
        self.browser_manager = browser_manager
        self.tools: dict[str, ToolInfo] = {}

        # Register all tool categories
        self._register_tools(NavigationTools(browser_manager))
        self._register_tools(InteractionTools(browser_manager))
        self._register_tools(CaptureTools(browser_manager))
        self._register_tools(UtilityTools(browser_manager))

    def _register_tools(self, tool_class) -> None:
        """Register tools from a tool class."""
        for tool_name, tool_info in tool_class.get_tools().items():
            self.tools[tool_name] = tool_info

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get all registered tools."""
        return self.tools

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            return ToolResult(
                content=[TextContent(type="text", text=f"Tool '{tool_name}' not found")],
                is_error=True,
            )

        tool_info = self.tools[tool_name]
        try:
            # tool_info.execute is already async, so we await it directly
            return await tool_info.execute(arguments)
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error executing {tool_name}: {str(e)}",
                    )
                ],
                is_error=True,
            )
