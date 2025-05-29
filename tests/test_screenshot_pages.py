"""Test for testing screenshot page tools."""

import shutil
import tempfile
from pathlib import Path

import pytest
from playwright_mcp.tools.capture import CaptureTools


@pytest.fixture
async def long_page(browser_manager):
    """Create a long page for testing page-by-page screenshots."""
    tab = await browser_manager.new_tab()

    # Create a long page with multiple sections
    await tab.page.set_content("""
    <html>
        <head>
            <title>Long Test Page</title>
            <style>
                body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
                .section { 
                    height: 600px; 
                    padding: 20px;
                    border: 2px solid #ccc;
                    margin-bottom: 20px;
                    background: linear-gradient(to bottom, #f0f0f0, #ffffff);
                }
                h1 { margin: 0 0 20px 0; }
            </style>
        </head>
        <body>
            <div class="section" style="background-color: #ffcccc;">
                <h1>Section 1 - Red</h1>
                <p>This is the first section of the page.</p>
                <p>It has a red background.</p>
            </div>
            <div class="section" style="background-color: #ccffcc;">
                <h1>Section 2 - Green</h1>
                <p>This is the second section of the page.</p>
                <p>It has a green background.</p>
            </div>
            <div class="section" style="background-color: #ccccff;">
                <h1>Section 3 - Blue</h1>
                <p>This is the third section of the page.</p>
                <p>It has a blue background.</p>
            </div>
            <div class="section" style="background-color: #ffffcc;">
                <h1>Section 4 - Yellow</h1>
                <p>This is the fourth section of the page.</p>
                <p>It has a yellow background.</p>
            </div>
            <div class="section" style="background-color: #ffccff;">
                <h1>Section 5 - Pink</h1>
                <p>This is the fifth section of the page.</p>
                <p>It has a pink background.</p>
            </div>
        </body>
    </html>
    """)

    # Set viewport size
    await tab.page.set_viewport_size({"width": 1280, "height": 800})

    return tab, browser_manager


@pytest.fixture
def temp_folder():
    """Create a temporary folder for screenshots."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


class TestScreenshotPages:
    """Test the browser_screenshot_pages tool."""

    @pytest.mark.asyncio
    async def test_basic_page_screenshots(self, long_page, temp_folder):
        """Test basic page-by-page screenshot functionality."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        result = await tools._screenshot_pages(
            {"folder": temp_folder, "filename_prefix": "test_page", "viewport_height": 600, "overlap": 50}
        )

        assert not result.is_error

        # Check that files were created
        folder_path = Path(temp_folder)
        png_files = list(folder_path.glob("test_page_*.png"))
        assert len(png_files) > 0

        # Check content
        assert len(result.content) > 1  # Should have text + some images
        assert result.content[0].type == "text"
        assert "Page-by-page screenshots captured" in result.content[0].text

        # Verify file names in the output
        for png_file in png_files:
            assert str(png_file) in result.content[0].text

    @pytest.mark.asyncio
    async def test_jpeg_format(self, long_page, temp_folder):
        """Test JPEG format screenshots."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        result = await tools._screenshot_pages(
            {
                "folder": temp_folder,
                "filename_prefix": "jpeg_test",
                "format": "jpeg",
                "quality": 80,
                "viewport_height": 800,
            }
        )

        assert not result.is_error

        # Check JPEG files
        folder_path = Path(temp_folder)
        jpeg_files = list(folder_path.glob("jpeg_test_*.jpeg"))
        assert len(jpeg_files) > 0

        # Verify all files exist and have content
        for jpeg_file in jpeg_files:
            assert jpeg_file.exists()
            assert jpeg_file.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_max_pages_limit(self, long_page, temp_folder):
        """Test max_pages parameter limits the number of screenshots."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        max_pages = 2
        result = await tools._screenshot_pages(
            {"folder": temp_folder, "filename_prefix": "limited", "viewport_height": 400, "max_pages": max_pages}
        )

        assert not result.is_error

        # Check that only max_pages files were created
        folder_path = Path(temp_folder)
        png_files = list(folder_path.glob("limited_*.png"))
        assert len(png_files) == max_pages

    @pytest.mark.asyncio
    async def test_overlap_setting(self, long_page, temp_folder):
        """Test overlap between pages."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        # Test with different overlap values
        for overlap in [0, 100, 200]:
            result = await tools._screenshot_pages(
                {
                    "folder": temp_folder,
                    "filename_prefix": f"overlap_{overlap}",
                    "viewport_height": 600,
                    "overlap": overlap,
                }
            )

            assert not result.is_error

            # Files should be created
            folder_path = Path(temp_folder)
            files = list(folder_path.glob(f"overlap_{overlap}_*.png"))
            assert len(files) > 0

    @pytest.mark.asyncio
    async def test_scroll_restoration(self, long_page, temp_folder):
        """Test that scroll position is restored after screenshots."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        # Scroll to middle of page first
        await tab.page.evaluate("window.scrollTo(0, 1000)")
        original_scroll = await tab.page.evaluate("window.pageYOffset")

        # Take screenshots
        result = await tools._screenshot_pages({"folder": temp_folder, "filename_prefix": "scroll_test"})

        assert not result.is_error

        # Check scroll position is restored
        final_scroll = await tab.page.evaluate("window.pageYOffset")
        assert final_scroll == original_scroll

    @pytest.mark.asyncio
    async def test_single_page_document(self, browser_manager, temp_folder):
        """Test with a short page that fits in one screenshot."""
        tab = await browser_manager.new_tab()
        await tab.page.set_content("""
        <html>
            <body>
                <h1>Short Page</h1>
                <p>This page fits in a single viewport.</p>
            </body>
        </html>
        """)

        tools = CaptureTools(browser_manager)
        result = await tools._screenshot_pages({"folder": temp_folder, "filename_prefix": "single_page"})

        assert not result.is_error

        # Should create exactly one file
        folder_path = Path(temp_folder)
        png_files = list(folder_path.glob("single_page_*.png"))
        assert len(png_files) == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, long_page):
        """Test error handling with invalid folder."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        # Try to save to an invalid path
        result = await tools._screenshot_pages(
            {"folder": "/invalid/path/that/does/not/exist", "filename_prefix": "error_test"}
        )

        assert result.is_error
        assert "failed" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_included_images_limit(self, long_page, temp_folder):
        """Test that only first 3 pages are included as base64 images."""
        tab, browser_manager = long_page
        tools = CaptureTools(browser_manager)

        result = await tools._screenshot_pages(
            {
                "folder": temp_folder,
                "filename_prefix": "image_limit",
                "viewport_height": 400,
                "max_pages": 5,  # Request 5 pages
            }
        )

        assert not result.is_error

        # Count ImageContent items (should be max 3)
        image_contents = [c for c in result.content if c.type == "image"]
        assert len(image_contents) <= 3

        # But all 5 files should exist
        folder_path = Path(temp_folder)
        png_files = list(folder_path.glob("image_limit_*.png"))
        assert len(png_files) == 5