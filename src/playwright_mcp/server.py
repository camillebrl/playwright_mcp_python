"""Main MCP Server implementation - Version corrigée."""

import logging
import sys

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import ImageContent, TextContent

from .context import BrowserManager
from .tools import ToolRegistry

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


class PlaywrightMCPServer:
    """Main Playwright MCP Server class."""

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout: int = 30000,
    ):
        logger.info("🚀 Initializing Playwright MCP Server...")
        logger.info(f"Browser: {browser_type}, Headless: {headless}")

        self.browser_type = browser_type
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout

        self.server: Server = Server("playwright-mcp-python")

        try:
            logger.info("📦 Creating BrowserManager...")
            self.browser_manager = BrowserManager(
                browser_type=browser_type,
                headless=headless,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
                timeout=timeout,
            )

            logger.info("🔧 Creating ToolRegistry...")
            self.tool_registry = ToolRegistry(self.browser_manager)

            tools = self.tool_registry.get_tools()
            logger.info(f"✅ {len(tools)} tools registered")

        except Exception as e:
            logger.error(f"❌ Error in initialization: {e}")
            import traceback

            logger.error(traceback.format_exc())
            raise

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup MCP request handlers."""
        logger.info("🔌 Setting up MCP handlers...")

        @self.server.list_tools()
        async def handle_list_tools() -> list:
            """Return list of available tools."""
            logger.info("📋 handle_list_tools called")

            try:
                tools_list = []
                registry_tools = self.tool_registry.get_tools()
                logger.info(f"🔍 Processing {len(registry_tools)} tools from registry")

                # Iterate through items() properly
                for tool_name, tool_info in registry_tools.items():
                    try:
                        # Validate the schema structure
                        if not isinstance(tool_info.input_schema, dict):
                            logger.warning(f"⚠️ Invalid schema type for {tool_name}: {type(tool_info.input_schema)}")
                            continue

                        # Ensure required schema fields
                        schema = tool_info.input_schema.copy()
                        if "type" not in schema:
                            schema["type"] = "object"
                        if "properties" not in schema and schema["type"] == "object":
                            schema["properties"] = {}

                        # Create the Tool object as a dictionary (not as a Pydantic object)
                        tool_dict = {
                            "name": tool_name,
                            "description": tool_info.description,
                            "inputSchema": schema,
                        }

                        tools_list.append(tool_dict)
                        logger.debug(f"✅ Created tool: {tool_name}")

                    except Exception as e:
                        logger.warning(f"⚠️ Error creating Tool {tool_name}: {e}")
                        continue

                logger.info(f"✅ Successfully created {len(tools_list)} tools")

                # Return directly the list of tools (not wrapped in a dict)
                return tools_list

            except Exception as e:
                logger.error(f"❌ Error in handle_list_tools: {e}")
                import traceback

                logger.error(traceback.format_exc())
                # Return empty list rather than crashing
                return []

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
            """Execute a tool.

            The MCP decorator expects this signature:
            - name: str - The name of the tool to execute
            - arguments: dict - The arguments for the tool

            Returns a list of content items (not CallToolResult).
            The decorator handles wrapping in CallToolResult and error handling.
            """
            logger.info(f"🔧 handle_call_tool called: {name}")
            logger.debug(f"📋 Arguments: {arguments}")

            try:
                # Execute the tool using the registry
                result = await self.tool_registry.execute_tool(name, arguments)

                # Log the result status
                if result.is_error:
                    logger.warning(f"⚠️ Tool {name} returned an error")
                else:
                    logger.info(f"✅ Tool {name} executed successfully")

                # Return the content list directly
                # The MCP decorator will wrap this in CallToolResult
                return result.content

            except Exception as e:
                # Log the full exception
                logger.exception(f"❌ Error executing tool {name}: {str(e)}")

                # Return error as a list with a single TextContent
                # The MCP decorator will set isError=True because an exception was raised
                return [
                    TextContent(
                        type="text",
                        text=f"Error executing tool '{name}': {str(e)}",
                    )
                ]

    async def run(self, read_stream, write_stream) -> None:
        """Run the MCP server."""
        logger.info("🌐 Starting MCP server run loop...")

        try:
            # Create initialization options
            init_options = InitializationOptions(
                server_name="playwright-mcp-python",
                server_version="1.0.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )

            logger.info("🚀 Server ready to handle requests")

            # Run the server
            await self.server.run(
                read_stream,
                write_stream,
                init_options,
            )

        except Exception as e:
            logger.error(f"❌ Server run error: {e}")
            import traceback

            logger.error(traceback.format_exc())
            raise
        finally:
            # Cleanup
            logger.info("🧹 Server shutting down...")
            try:
                await self.browser_manager.stop()
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
