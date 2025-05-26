"""Test capture tools."""

from playwright_mcp.tools.capture import CaptureTools


async def test_screenshot(sample_page):
    """Test taking screenshots."""
    tab, browser_manager = sample_page
    tools = CaptureTools(browser_manager)

    result = await tools._screenshot({})
    assert not result.is_error
    assert len(result.content) == 2  # Image + text
    assert result.content[0].type == "image"


async def test_get_text(sample_page):
    """Test text extraction."""
    tab, browser_manager = sample_page
    tools = CaptureTools(browser_manager)

    result = await tools._get_text({"selector": "h1"})
    assert not result.is_error
    assert "Hello World" in result.content[0].text


async def test_get_html(sample_page):
    """Test HTML extraction."""
    tab, browser_manager = sample_page
    tools = CaptureTools(browser_manager)

    result = await tools._get_html({"selector": "body"})
    assert not result.is_error
    assert "<h1>" in result.content[0].text
