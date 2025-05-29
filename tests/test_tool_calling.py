"""Test the corrected handle_call_tool implementation with pytest."""

import contextlib
import logging

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ImageContent, TextContent
from playwright_mcp.server import PlaywrightMCPServer

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.fixture
async def server():
    """Create a PlaywrightMCPServer instance."""
    server = PlaywrightMCPServer(headless=True)
    yield server
    # Cleanup
    with contextlib.suppress(Exception):
        await server.browser_manager.stop()


@pytest.fixture
async def handle_call_tool(server):
    """Get the handle_call_tool function from the server."""
    handlers = []

    # Capture the handler when it's registered
    original_decorator = server.server.call_tool

    def capture_decorator():
        def decorator(func):
            handlers.append(func)
            return original_decorator()(func)

        return decorator

    server.server.call_tool = capture_decorator

    # Re-setup to capture the handler
    server._setup_handlers()

    # Find handle_call_tool
    for handler in handlers:
        if handler.__name__ == "handle_call_tool":
            return handler

    raise ValueError("handle_call_tool not found")


class TestHandleCallToolDirect:
    """Test calling handle_call_tool directly."""

    @pytest.mark.asyncio
    async def test_valid_tool_call(self, handle_call_tool):
        """Test a valid tool call."""
        result = await handle_call_tool("browser_navigate", {"url": "https://example.com"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Navigated to: https://example.com" in result[0].text

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, handle_call_tool):
        """Test calling an invalid tool."""
        result = await handle_call_tool("invalid_tool", {})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Tool 'invalid_tool' not found" in result[0].text

    @pytest.mark.asyncio
    async def test_missing_required_arguments(self, handle_call_tool):
        """Test calling a tool with missing required arguments."""
        result = await handle_call_tool("browser_navigate", {})  # Missing 'url'

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error executing browser_navigate" in result[0].text


class TestMCPIntegration:
    """Test the full MCP integration."""

    @pytest.mark.asyncio
    async def test_mcp_handler_registration(self, server):
        """Test that the MCP handler is properly registered."""
        call_tool_handler = server.server.request_handlers.get(CallToolRequest)

        assert call_tool_handler is not None
        assert call_tool_handler.__code__.co_argcount == 1
        assert call_tool_handler.__code__.co_varnames[0] == "req"

    @pytest.mark.asyncio
    async def test_mcp_handler_execution(self, server):
        """Test executing the MCP handler with a proper request."""
        call_tool_handler = server.server.request_handlers.get(CallToolRequest)

        # Create a proper CallToolRequest
        request = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="browser_navigate", arguments={"url": "https://example.com"}),
        )

        result = await call_tool_handler(request)

        assert result is not None
        assert hasattr(result, "root")
        assert hasattr(result.root, "content")
        assert len(result.root.content) == 1
        assert isinstance(result.root.content[0], TextContent)
        assert not result.root.isError


class TestVariousTools:
    """Test various tools to ensure they all work."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name,args,expected_content_type",
        [
            ("browser_screenshot", {"full_page": False}, ImageContent),
            ("browser_wait", {"time": 0.1}, TextContent),
            ("browser_get_text", {"selector": "body"}, TextContent),
            ("browser_tab_list", {}, TextContent),
        ],
    )
    async def test_tool_execution(self, handle_call_tool, tool_name, args, expected_content_type):
        """Test execution of various tools."""
        result = await handle_call_tool(tool_name, args)

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], expected_content_type)


class TestErrorHandling:
    """Test error handling in handle_call_tool."""

    @pytest.mark.asyncio
    async def test_forced_error(self, server):
        """Test that errors are properly handled."""
        # Mock the tool registry to force an error
        original_execute = server.tool_registry.execute_tool

        async def mock_execute(name, args):
            if name == "force_error":
                raise RuntimeError("This is a test error")
            return await original_execute(name, args)

        server.tool_registry.execute_tool = mock_execute

        # Get handle_call_tool
        handlers = []
        original_decorator = server.server.call_tool

        def capture_decorator():
            def decorator(func):
                handlers.append(func)
                return original_decorator()(func)

            return decorator

        server.server.call_tool = capture_decorator
        server._setup_handlers()

        handle_call_tool = None
        for handler in handlers:
            if handler.__name__ == "handle_call_tool":
                handle_call_tool = handler
                break

        assert handle_call_tool is not None

        # Test forced error
        result = await handle_call_tool("force_error", {})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error executing tool 'force_error': This is a test error" in result[0].text

    @pytest.mark.asyncio
    async def test_exception_in_tool(self, handle_call_tool):
        """Test handling of exceptions raised by tools."""
        # Try to navigate without URL (should raise KeyError)
        result = await handle_call_tool("browser_navigate", {})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text