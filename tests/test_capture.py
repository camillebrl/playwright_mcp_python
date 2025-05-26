"""Test capture tools"""
import pytest
from playwright_mcp.tools.capture import CaptureTools


@pytest.mark.asyncio
async def test_screenshot(sample_page):
    """Test taking screenshots"""
    browser_manager = sample_page.page.context.browser.contexts[0]._browser_manager
    tools = CaptureTools(browser_manager)
    
    result = await tools._screenshot({})
    assert not result.is_error
    assert len(result.content) == 2  # Image + text
    assert result.content[0].type == "image"


@pytest.mark.asyncio
async def test_get_text(sample_page):
    """Test text extraction"""
    browser_manager = sample_page.page.context.browser.contexts[0]._browser_manager
    tools = CaptureTools(browser_manager)
    
    result = await tools._get_text({"selector": "h1"})
    assert not result.is_error
    assert "Hello World" in result.content[0].text


@pytest.mark.asyncio
async def test_get_html(sample_page):
    """Test HTML extraction"""
    browser_manager = sample_page.page.context.browser.contexts[0]._browser_manager
    tools = CaptureTools(browser_manager)
    
    result = await tools._get_html({"selector": "body"})
    assert not result.is_error
    assert "<h1>" in result.content[0].text