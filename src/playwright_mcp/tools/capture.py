"""Capture and extraction tools."""

import base64
from pathlib import Path
from typing import Any

from mcp.types import ImageContent, TextContent

from .base import BaseToolSet, ToolInfo, ToolResult


class CaptureTools(BaseToolSet):
    """Tools for capturing screenshots and extracting content."""

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get available capture tools.

        Returns:
            dict[str, ToolInfo]: Dictionary mapping tool names to their info
        """
        return {
            "browser_screenshot": ToolInfo(
                name="browser_screenshot",
                description="Take a screenshot of the current page",
                input_schema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Optional filename to save screenshot",
                        },
                        "full_page": {
                            "type": "boolean",
                            "description": "Capture full page",
                            "default": False,
                        },
                        "element_selector": {
                            "type": "string",
                            "description": "CSS selector to screenshot specific element",
                        },
                    },
                },
                execute=self._screenshot,
            ),
            "browser_get_text": ToolInfo(
                name="browser_get_text",
                description="Extract text content from page or element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector (optional, defaults to body)",
                        }
                    },
                },
                execute=self._get_text,
            ),
            "browser_get_html": ToolInfo(
                name="browser_get_html",
                description="Get HTML content of page or element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector (optional, defaults to full page)",
                        }
                    },
                },
                execute=self._get_html,
            ),
            "browser_console_messages": ToolInfo(
                name="browser_console_messages",
                description="Get console messages from the page",
                input_schema={"type": "object", "properties": {}},
                execute=self._get_console_messages,
            ),
        }

    async def _screenshot(self, args: dict[str, Any]) -> ToolResult:
        """Take screenshot."""
        try:
            tab = await self.browser_manager.get_current_tab()
            filename = args.get("filename")
            full_page = args.get("full_page", False)
            element_selector = args.get("element_selector")

            # Préparer les options de screenshot
            screenshot_options = {"full_page": full_page}

            if element_selector:
                # Screenshot specific element
                element = tab.page.locator(element_selector)
                screenshot_bytes = await element.screenshot()
                target = f"element '{element_selector}'"
            else:
                # Screenshot full page - utiliser ** pour unpacker le dict
                screenshot_bytes = await tab.page.screenshot(**screenshot_options)
                target = "page"

            # Save to file if filename provided
            if filename:
                Path(filename).write_bytes(screenshot_bytes)
                saved_msg = f" (saved as {filename})"
            else:
                saved_msg = ""

            # Return image content
            base64_image = base64.b64encode(screenshot_bytes).decode()

            return ToolResult(
                content=[
                    ImageContent(type="image", data=base64_image, mimeType="image/png"),
                    TextContent(
                        type="text",
                        text=f"📸 Screenshot of {target}{saved_msg}",
                    ),
                ]
            )
        except Exception as e:
            # Log l'erreur complète pour debugging
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Screenshot error: {str(e)}")
            logger.error(traceback.format_exc())

            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Screenshot failed: {str(e)}")],
                is_error=True,
            )

    async def _get_text(self, args: dict[str, Any]) -> ToolResult:
        """Extract text content."""
        selector = args.get("selector", "body")
        tab = await self.browser_manager.get_current_tab()

        try:
            if selector == "body":
                text = await tab.page.text_content("body")
                source = "page"
            else:
                element = tab.page.locator(selector)
                text = await element.text_content()
                source = f"element '{selector}'"

            if not text:
                text = "(no text content found)"

            return ToolResult(content=[TextContent(type="text", text=f"📄 Text from {source}:\n\n{text}")])
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Text extraction failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _get_html(self, args: dict[str, Any]) -> ToolResult:
        """Get HTML content."""
        selector = args.get("selector")
        tab = await self.browser_manager.get_current_tab()

        try:
            if selector:
                element = tab.page.locator(selector)
                html = await element.inner_html()
                source = f"element '{selector}'"
            else:
                html = await tab.page.content()
                source = "page"

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"🔖 HTML from {source}:\n\n```html\n{html}\n```",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ HTML extraction failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _get_console_messages(self, args: dict[str, Any]) -> ToolResult:
        """Get console messages."""
        tab = await self.browser_manager.get_current_tab()

        try:
            messages = tab.get_console_messages()
            if not messages:
                return ToolResult(content=[TextContent(type="text", text="📋 No console messages")])

            messages_text = "\n".join(messages)
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"📋 Console messages:\n\n{messages_text}",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Console messages failed: {str(e)}",
                    )
                ],
                is_error=True,
            )
