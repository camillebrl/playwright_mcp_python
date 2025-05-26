"""CLI entry point for Playwright MCP Server - Version corrigée."""

import argparse
import asyncio
import logging
import signal
import sys

from mcp.server.stdio import stdio_server

from .server import PlaywrightMCPServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Playwright MCP Server")

    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use",
    )

    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    parser.add_argument(
        "--viewport-width",
        type=int,
        default=1280,
        help="Browser viewport width",
    )

    parser.add_argument(
        "--viewport-height",
        type=int,
        default=720,
        help="Browser viewport height",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Default timeout in milliseconds",
    )

    return parser


async def async_main():
    """Async main entry point for the CLI application."""
    logger.info("🚀 Starting Playwright MCP Server CLI...")

    parser = create_parser()
    args = parser.parse_args()

    # Créer le serveur
    server = PlaywrightMCPServer(
        browser_type=args.browser,
        headless=args.headless,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
        timeout=args.timeout,
    )

    # Gestion des signaux
    def signal_handler():
        logger.info("📡 Signal received, shutting down...")
        sys.exit(0)

    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    # Run avec stdio
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)
    except Exception as e:
        logger.error(f"❌ Fatal server error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


def main():
    """Synchronous main entry point that runs the async main."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
