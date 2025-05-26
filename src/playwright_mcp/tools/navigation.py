"""Navigation tools."""

from typing import Any

from mcp.types import TextContent

from .base import BaseToolSet, ToolInfo, ToolResult


class NavigationTools(BaseToolSet):
    """Navigation-related tools."""

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get available navigation tools.

        Returns:
            dict[str, ToolInfo]: Dictionary mapping tool names to their info
        """
        return {
            "browser_navigate": ToolInfo(
                name="browser_navigate",
                description="Navigate to a URL",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to",
                        }
                    },
                    "required": ["url"],
                },
                execute=self._navigate,
            ),
            "browser_navigate_back": ToolInfo(
                name="browser_navigate_back",
                description="Go back to the previous page",
                input_schema={"type": "object", "properties": {}},
                execute=self._navigate_back,
            ),
            "browser_navigate_forward": ToolInfo(
                name="browser_navigate_forward",
                description="Go forward to the next page",
                input_schema={"type": "object", "properties": {}},
                execute=self._navigate_forward,
            ),
        }

    async def _navigate(self, args: dict[str, Any]) -> ToolResult:
        """Navigate to URL."""
        url = args["url"]
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.goto(url, wait_until="domcontentloaded")
            title = await tab.get_title()

            result_text = f"""✅ Navigated to: {url}
📄 Page title: {title}
🔗 Current URL: {tab.page.url}"""

            return ToolResult(content=[TextContent(type="text", text=result_text)])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Navigation failed: {str(e)}")],
                is_error=True,
            )

    async def _navigate_back(self, args: dict[str, Any]) -> ToolResult:
        """Navigate back."""
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.go_back(wait_until="domcontentloaded")
            title = await tab.get_title()

            return ToolResult(content=[TextContent(type="text", text=f"⬅️ Navigated back to: {title}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Cannot go back: {str(e)}")],
                is_error=True,
            )

    async def _navigate_forward(self, args: dict[str, Any]) -> ToolResult:
        """Navigate forward."""
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.go_forward(wait_until="domcontentloaded")
            title = await tab.get_title()

            return ToolResult(content=[TextContent(type="text", text=f"➡️ Navigated forward to: {title}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Cannot go forward: {str(e)}")],
                is_error=True,
            )
