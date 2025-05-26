"""Test configuration."""

import pytest_asyncio
from playwright_mcp.context import BrowserManager


@pytest_asyncio.fixture
async def browser_manager():
    """Create a browser manager for testing."""
    manager = BrowserManager(headless=True)
    yield manager
    await manager.stop()


@pytest_asyncio.fixture
async def sample_page(browser_manager):
    """Create a sample page for testing."""
    tab = await browser_manager.new_tab()
    await tab.page.set_content(
        """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <button id="test-btn">Click Me</button>
            <input id="test-input" type="text" placeholder="Enter text">
            <select id="test-select">
                <option value="1">Option 1</option>
                <option value="2">Option 2</option>
            </select>
            <div id="content">Initial content</div>
        </body>
    </html>
    """
    )
    return tab, browser_manager
