"""Base classes for tools."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp.types import ImageContent, TextContent


@dataclass
class ToolResult:
    """Result from a tool execution."""

    content: list[TextContent | ImageContent]
    is_error: bool = False


@dataclass
class ToolInfo:
    """Information about a tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    execute: Callable[[dict[str, Any]], Awaitable[ToolResult]]


class BaseToolSet(ABC):
    """Base class for tool sets."""

    def __init__(self, browser_manager):
        self.browser_manager = browser_manager

    @abstractmethod
    def get_tools(self) -> dict[str, ToolInfo]:
        """Get tools provided by this tool set."""
        pass
