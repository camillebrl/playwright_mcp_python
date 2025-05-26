"""Interaction tools."""

from typing import Any

from mcp.types import TextContent

from .base import BaseToolSet, ToolInfo, ToolResult


class InteractionTools(BaseToolSet):
    """Page interaction tools."""

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get available interaction tools.

        Returns:
            dict[str, ToolInfo]: Dictionary mapping tool names to their info
        """
        return {
            "browser_click": ToolInfo(
                name="browser_click",
                description="Click on an element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or text to click",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in milliseconds",
                            "default": 30000,
                        },
                    },
                    "required": ["selector"],
                },
                execute=self._click,
            ),
            "browser_type": ToolInfo(
                name="browser_type",
                description="Type text into an input field",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of the input field",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type",
                        },
                        "clear": {
                            "type": "boolean",
                            "description": "Clear field before typing",
                            "default": True,
                        },
                    },
                    "required": ["selector", "text"],
                },
                execute=self._type,
            ),
            "browser_fill": ToolInfo(
                name="browser_fill",
                description="Fill an input field",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of the input field",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to fill",
                        },
                    },
                    "required": ["selector", "value"],
                },
                execute=self._fill,
            ),
            "browser_select_option": ToolInfo(
                name="browser_select_option",
                description="Select option from dropdown",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of the select element",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to select",
                        },
                    },
                    "required": ["selector", "value"],
                },
                execute=self._select_option,
            ),
        }

    async def _click(self, args: dict[str, Any]) -> ToolResult:
        """Click on element."""
        selector = args["selector"]
        timeout = args.get("timeout", 30000)
        tab = await self.browser_manager.get_current_tab()

        try:
            # Try CSS selector first, then text selector
            try:
                element = tab.page.locator(selector)
                await element.click(timeout=timeout)
                clicked_text = selector
            except Exception:
                # Try as text selector
                element = tab.page.get_by_text(selector)
                await element.click(timeout=timeout)
                clicked_text = f"text '{selector}'"

            return ToolResult(content=[TextContent(type="text", text=f"🖱️ Clicked on: {clicked_text}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Click failed: {str(e)}")],
                is_error=True,
            )

    async def _type(self, args: dict[str, Any]) -> ToolResult:
        """Type text into field."""
        selector = args["selector"]
        text = args["text"]
        clear = args.get("clear", True)
        tab = await self.browser_manager.get_current_tab()

        try:
            element = tab.page.locator(selector)
            if clear:
                await element.clear()
            await element.type(text)

            return ToolResult(content=[TextContent(type="text", text=f"⌨️ Typed '{text}' into: {selector}")])
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Typing failed: {str(e)}")],
                is_error=True,
            )

    async def _fill(self, args: dict[str, Any]) -> ToolResult:
        """Fill input field."""
        selector = args["selector"]
        value = args["value"]
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.fill(selector, value)
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"📝 Filled '{value}' into: {selector}",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Fill failed: {str(e)}")],
                is_error=True,
            )

    async def _select_option(self, args: dict[str, Any]) -> ToolResult:
        """Select option from dropdown."""
        selector = args["selector"]
        value = args["value"]
        tab = await self.browser_manager.get_current_tab()

        try:
            await tab.page.select_option(selector, value)
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"📋 Selected '{value}' in: {selector}",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Selection failed: {str(e)}")],
                is_error=True,
            )
