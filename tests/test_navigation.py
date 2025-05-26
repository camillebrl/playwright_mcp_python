"""Test navigation tools."""

from playwright_mcp.tools.navigation import NavigationTools


async def test_navigate(browser_manager):
    """Test navigation to URL."""
    tools = NavigationTools(browser_manager)

    result = await tools._navigate({"url": "https://example.com"})
    assert not result.is_error
    assert "example.com" in result.content[0].text


async def test_navigate_back_forward(browser_manager):
    """Test back and forward navigation."""
    tools = NavigationTools(browser_manager)

    # Navigate to first page
    await tools._navigate({"url": "https://example.com"})
    # Navigate to second page
    await tools._navigate({"url": "https://httpbin.org"})

    # Go back
    result = await tools._navigate_back({})
    assert not result.is_error

    # Go forward
    result = await tools._navigate_forward({})
    assert not result.is_error
