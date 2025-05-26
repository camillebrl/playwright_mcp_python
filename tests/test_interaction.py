"""Test interaction tools."""

from playwright_mcp.tools.interaction import InteractionTools


async def test_click(sample_page):
    """Test clicking elements."""
    tab, browser_manager = sample_page
    tools = InteractionTools(browser_manager)

    result = await tools._click({"selector": "#test-btn"})
    assert not result.is_error
    assert "Clicked on" in result.content[0].text


async def test_type_and_fill(sample_page):
    """Test typing and filling inputs."""
    tab, browser_manager = sample_page
    tools = InteractionTools(browser_manager)

    # Test typing
    result = await tools._type({"selector": "#test-input", "text": "Hello World"})
    assert not result.is_error

    # Test filling
    result = await tools._fill({"selector": "#test-input", "value": "New Value"})
    assert not result.is_error


async def test_select_option(sample_page):
    """Test selecting options."""
    tab, browser_manager = sample_page
    tools = InteractionTools(browser_manager)

    result = await tools._select_option({"selector": "#test-select", "value": "2"})
    assert not result.is_error
