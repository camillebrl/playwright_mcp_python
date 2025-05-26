"""Utility tools."""

import asyncio
from typing import Any

from mcp.types import TextContent

from .base import BaseToolSet, ToolInfo, ToolResult


class UtilityTools(BaseToolSet):
    """Utility tools for browser management."""

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get available utility tools.

        Returns:
            dict[str, ToolInfo]: Dictionary mapping tool names to their info
        """
        return {
            "browser_wait": ToolInfo(
                name="browser_wait",
                description="Wait for a specified time or element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "time": {
                            "type": "number",
                            "description": "Time to wait in seconds",
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to wait for",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text content to wait for",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in milliseconds",
                            "default": 30000,
                        },
                    },
                },
                execute=self._wait,
            ),
            "browser_reload": ToolInfo(
                name="browser_reload",
                description="Reload the current page",
                input_schema={"type": "object", "properties": {}},
                execute=self._reload,
            ),
            "browser_scroll": ToolInfo(
                name="browser_scroll",
                description="Scroll the page",
                input_schema={
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right"],
                            "description": "Scroll direction",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Scroll amount in pixels",
                            "default": 500,
                        },
                    },
                    "required": ["direction"],
                },
                execute=self._scroll,
            ),
            "browser_evaluate": ToolInfo(
                name="browser_evaluate",
                description="Execute JavaScript code in the browser",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "JavaScript code to execute",
                        }
                    },
                    "required": ["code"],
                },
                execute=self._evaluate,
            ),
            "browser_tab_new": ToolInfo(
                name="browser_tab_new",
                description="Open a new browser tab",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to open in new tab",
                        }
                    },
                },
                execute=self._new_tab,
            ),
            "browser_tab_close": ToolInfo(
                name="browser_tab_close",
                description="Close current or specified tab",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tab_id": {
                            "type": "string",
                            "description": "ID of tab to close (current tab if not specified)",
                        }
                    },
                },
                execute=self._close_tab,
            ),
            "browser_tab_list": ToolInfo(
                name="browser_tab_list",
                description="List all open browser tabs",
                input_schema={"type": "object", "properties": {}},
                execute=self._list_tabs,
            ),
            "browser_tab_switch": ToolInfo(
                name="browser_tab_switch",
                description="Switch to a specific tab",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tab_id": {
                            "type": "string",
                            "description": "ID of tab to switch to",
                        }
                    },
                    "required": ["tab_id"],
                },
                execute=self._switch_tab,
            ),
        }

    async def _wait(self, args: dict[str, Any]) -> ToolResult:
        """Wait for time, element or text."""
        time_seconds = args.get("time")
        selector = args.get("selector")
        text = args.get("text")
        timeout = args.get("timeout", 30000)

        tab = await self.browser_manager.get_current_tab()

        try:
            if time_seconds:
                await asyncio.sleep(time_seconds)
                return ToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"⏱️ Waited {time_seconds} seconds",
                        )
                    ]
                )
            elif selector:
                await tab.page.wait_for_selector(selector, timeout=timeout)
                return ToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"✅ Element appeared: {selector}",
                        )
                    ]
                )
            elif text:
                await tab.page.wait_for_function(
                    f"document.body.textContent.includes('{text}')",
                    timeout=timeout,
                )
                return ToolResult(content=[TextContent(type="text", text=f"✅ Text appeared: {text}")])
            else:
                return ToolResult(
                    content=[TextContent(type="text", text="❌ No wait condition specified")],
                    is_error=True,
                )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Wait failed: {str(e)}")],
                is_error=True,
            )

    async def _reload(self, args: dict[str, Any]) -> ToolResult:
        """Reload current page."""
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.reload(wait_until="domcontentloaded")
            title = await tab.get_title()
            return ToolResult(content=[TextContent(type="text", text=f"🔄 Page reloaded: {title}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Reload failed: {str(e)}")],
                is_error=True,
            )

    async def _scroll(self, args: dict[str, Any]) -> ToolResult:
        """Scroll the page."""
        direction = args["direction"]
        amount = args.get("amount", 500)

        tab = await self.browser_manager.get_current_tab()

        try:
            if direction == "down":
                await tab.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await tab.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "right":
                await tab.page.evaluate(f"window.scrollBy({amount}, 0)")
            elif direction == "left":
                await tab.page.evaluate(f"window.scrollBy(-{amount}, 0)")

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"📜 Scrolled {direction} by {amount}px",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Scroll failed: {str(e)}")],
                is_error=True,
            )

    async def _evaluate(self, args: dict[str, Any]) -> ToolResult:
        """Execute JavaScript."""
        code = args["code"]
        tab = await self.browser_manager.get_current_tab()

        try:
            result = await tab.page.evaluate(code)
            return ToolResult(content=[TextContent(type="text", text=f"🔧 JavaScript result: {result}")])
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ JavaScript execution failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _new_tab(self, args: dict[str, Any]) -> ToolResult:
        """Open new tab."""
        url = args.get("url")

        try:
            tab = await self.browser_manager.new_tab(url)
            return ToolResult(content=[TextContent(type="text", text=f"🆕 New tab opened: {tab.tab_id}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ New tab failed: {str(e)}")],
                is_error=True,
            )

    async def _close_tab(self, args: dict[str, Any]) -> ToolResult:
        """Close tab."""
        tab_id = args.get("tab_id") or self.browser_manager.current_tab_id

        try:
            await self.browser_manager.close_tab(tab_id)
            return ToolResult(content=[TextContent(type="text", text=f"❌ Tab closed: {tab_id}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Close tab failed: {str(e)}")],
                is_error=True,
            )

    async def _list_tabs(self, args: dict[str, Any]) -> ToolResult:
        """List all tabs."""
        try:
            tabs = self.browser_manager.list_tabs()
            if not tabs:
                return ToolResult(content=[TextContent(type="text", text="📋 No tabs open")])

            tabs_text = "📋 Open tabs:\n"
            for tab in tabs:
                active_marker = "🔹" if tab["active"] else "   "
                tabs_text += f"{active_marker} {tab['id']}: {tab['title']} ({tab['url']})\n"

            return ToolResult(content=[TextContent(type="text", text=tabs_text)])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ List tabs failed: {str(e)}")],
                is_error=True,
            )

    async def _switch_tab(self, args: dict[str, Any]) -> ToolResult:
        """Switch to tab."""
        tab_id = args["tab_id"]

        try:
            await self.browser_manager.switch_tab(tab_id)
            return ToolResult(content=[TextContent(type="text", text=f"🔄 Switched to tab: {tab_id}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Switch tab failed: {str(e)}")],
                is_error=True,
            )
