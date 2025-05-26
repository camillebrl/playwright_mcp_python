"""Main MCP Server implementation"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from mcp import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    ImageContent,
    Tool,
)
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pydantic import BaseModel

from .tools import ToolRegistry
from .context import BrowserManager


logger = logging.getLogger(__name__)


class PlaywrightMCPServer:
    """Main Playwright MCP Server class"""
    
    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout: int = 30000,
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout
        
        self.server = Server("playwright-mcp-python")
        self.browser_manager = BrowserManager(
            browser_type=browser_type,
            headless=headless,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            timeout=timeout,
        )
        self.tool_registry = ToolRegistry(self.browser_manager)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return list of available tools"""
            tools = []
            for tool_name, tool_info in self.tool_registry.get_tools().items():
                tools.append(Tool(
                    name=tool_name,
                    description=tool_info.description,
                    inputSchema=tool_info.input_schema,
                ))
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Execute a tool"""
            try:
                result = await self.tool_registry.execute_tool(
                    request.params.name,
                    request.params.arguments or {}
                )
                return CallToolResult(content=result.content, isError=result.is_error)
            except Exception as e:
                logger.exception(f"Error executing tool {request.params.name}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def run(self, read_stream, write_stream):
        """Run the MCP server"""
        async with self.server.run_server(
            read_stream, 
            write_stream,
            InitializationOptions(
                server_name="playwright-mcp-python",
                server_version="1.0.0",
                capabilities=self.server.get_capabilities()
            )
        ):
            await asyncio.Event().wait()