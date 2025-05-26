"""CLI entry point for Playwright MCP Server"""

import argparse
import asyncio
import sys
from typing import Optional

from mcp.server.stdio import stdio_server
from .server import PlaywrightMCPServer


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Playwright MCP Server")
    
    parser.add_argument(
        "--browser", 
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--viewport-width",
        type=int,
        default=1280,
        help="Browser viewport width"
    )
    
    parser.add_argument(
        "--viewport-height", 
        type=int,
        default=720,
        help="Browser viewport height"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Default timeout in milliseconds"
    )
    
    return parser


async def main():
    parser = create_parser()
    args = parser.parse_args()
    
    server = PlaywrightMCPServer(
        browser_type=args.browser,
        headless=args.headless,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
        timeout=args.timeout
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())