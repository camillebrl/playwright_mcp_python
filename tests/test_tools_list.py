"""Test listing all available tools from Playwright server with pytest."""

import asyncio
import json
import os
import subprocess
import sys

import pytest


@pytest.fixture
async def playwright_server_process():
    """Start and manage the Playwright MCP server process."""
    process = None
    try:
        # Change to src directory
        src_path = os.path.join(os.getcwd(), "src")

        # Start the server
        cmd = [sys.executable, "-m", "playwright_mcp.cli", "--headless"]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=src_path,
        )

        # Wait for startup
        await asyncio.sleep(2)

        yield process

    finally:
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                process.kill()


async def send_request(process, request_data: dict) -> dict:
    """Send a request to the server and get the response."""
    process.stdin.write(json.dumps(request_data) + "\n")
    process.stdin.flush()

    response_line = await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), timeout=10.0)

    return json.loads(response_line.strip())


class TestPlaywrightToolsList:
    """Test the Playwright MCP server tools listing."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, playwright_server_process):
        """Test that the server initializes correctly."""
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest-tools-lister", "version": "1.0.0"},
            },
        }

        response = await send_request(playwright_server_process, init_request)

        assert "result" in response
        assert "capabilities" in response["result"]
        assert response["id"] == 1

        # Send initialized notification
        initialized_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        playwright_server_process.stdin.write(json.dumps(initialized_notif) + "\n")
        playwright_server_process.stdin.flush()

        await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_list_tools(self, playwright_server_process):
        """Test listing all available tools."""
        # Initialize first
        await self.test_server_initialization(playwright_server_process)

        # Request tools list
        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = await send_request(playwright_server_process, tools_request)

        assert "result" in response
        assert "tools" in response["result"]

        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 21  # Should have 21 tools including browser_screenshot_pages and browser_download_pdf

        # Verify all tools have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert isinstance(tool["inputSchema"], dict)

    @pytest.mark.asyncio
    async def test_tools_categorization(self, playwright_server_process):
        """Test that tools can be properly categorized."""
        # Initialize and get tools
        await self.test_server_initialization(playwright_server_process)

        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = await send_request(playwright_server_process, tools_request)

        tools = response["result"]["tools"]

        # Categorize tools
        categories = {"Navigation": [], "Interaction": [], "Capture": [], "Utility": []}

        for tool in tools:
            name = tool["name"]
            if name.startswith("browser_navigate"):
                categories["Navigation"].append(tool)
            elif name in ["browser_click", "browser_type", "browser_fill", "browser_select_option"]:
                categories["Interaction"].append(tool)
            elif name in [
                "browser_screenshot",
                "browser_screenshot_pages",
                "browser_get_text",
                "browser_get_html",
                "browser_console_messages",
                "browser_download_pdf",
            ]:
                categories["Capture"].append(tool)
            else:
                categories["Utility"].append(tool)

        # Verify we have tools in each category
        assert len(categories["Navigation"]) >= 3  # navigate, back, forward
        assert len(categories["Interaction"]) == 4
        assert len(categories["Capture"]) == 6  # Now includes browser_screenshot_pages and browser_download_pdf
        assert len(categories["Utility"]) >= 8

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name,required_params",
        [
            ("browser_navigate", ["url"]),
            ("browser_click", ["selector"]),
            ("browser_type", ["selector", "text"]),
            ("browser_screenshot", []),  # No required params
            ("browser_screenshot_pages", []),  # No required params
            ("browser_tab_switch", ["tab_id"]),
        ],
    )
    async def test_tool_schema(self, playwright_server_process, tool_name, required_params):
        """Test that specific tools have correct schemas."""
        # Initialize and get tools
        await self.test_server_initialization(playwright_server_process)

        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = await send_request(playwright_server_process, tools_request)

        tools = response["result"]["tools"]

        # Find the specific tool
        tool = next((t for t in tools if t["name"] == tool_name), None)
        assert tool is not None, f"Tool {tool_name} not found"

        # Check schema
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema

        # Check required parameters
        if required_params:
            assert "required" in schema
            for param in required_params:
                assert param in schema["required"]
                assert param in schema["properties"]

    @pytest.mark.asyncio
    async def test_tool_descriptions(self, playwright_server_process):
        """Test that all tools have meaningful descriptions."""
        # Initialize and get tools
        await self.test_server_initialization(playwright_server_process)

        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = await send_request(playwright_server_process, tools_request)

        tools = response["result"]["tools"]

        for tool in tools:
            assert tool["description"]
            assert len(tool["description"]) > 10  # Not just a placeholder
            assert not tool["description"].startswith("TODO")  # No unfinished descriptions

    @pytest.mark.asyncio
    async def test_browser_screenshot_pages_tool(self, playwright_server_process):
        """Test that browser_screenshot_pages tool is properly registered."""
        # Initialize and get tools
        await self.test_server_initialization(playwright_server_process)

        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = await send_request(playwright_server_process, tools_request)

        tools = response["result"]["tools"]

        # Find browser_screenshot_pages tool
        screenshot_pages_tool = next((t for t in tools if t["name"] == "browser_screenshot_pages"), None)
        assert screenshot_pages_tool is not None, "browser_screenshot_pages tool not found"

        # Verify tool properties
        assert screenshot_pages_tool["description"] == "Take screenshots page by page (useful for long pages)"

        # Check schema properties
        schema = screenshot_pages_tool["inputSchema"]
        assert schema["type"] == "object"

        expected_properties = [
            "folder",
            "filename_prefix",
            "viewport_height",
            "overlap",
            "max_pages",
            "format",
            "quality",
        ]
        for prop in expected_properties:
            assert prop in schema["properties"], f"Property {prop} not found in schema"

        # Verify default values
        assert schema["properties"]["folder"]["default"] == "screenshots"
        assert schema["properties"]["filename_prefix"]["default"] == "page"
        assert schema["properties"]["viewport_height"]["default"] == 800
        assert schema["properties"]["overlap"]["default"] == 50
        assert schema["properties"]["max_pages"]["default"] == 20
        assert schema["properties"]["format"]["default"] == "png"
        assert schema["properties"]["quality"]["default"] == 90