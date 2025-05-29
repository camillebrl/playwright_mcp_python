# Playwright MCP Server - Python

A Python implementation of the [Playwright MCP server](https://github.com/microsoft/playwright-mcp).

## Features

- 🌐 **Navigation**: Navigate to URLs, go back/forward
- 🖱️ **Interactions**: Click, type, fill forms, select options
- 📸 **Capture**: Take screenshots, extract text/HTML content
- 🔧 **Utilities**: Wait for elements, scroll, execute JavaScript
- 📑 **Tab Management**: Open/close/switch between tabs
- 🖥️ **Multi-browser**: Support for Chromium, Firefox, and WebKit

## Installation

```bash
git clone https://github.com/camillebrl/playwright_mcp_python.git
make install
make test
```
If all tests passed, you can now use this MCP server.

## Usage

### As MCP Server
Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "playwright-python": {
      "command": "playwright-mcp-python",
      "args": ["--headless"]
    }
  }
}
```

Or find root for playwright-mcp-python:
```sbatch
which playwright-mcp-python
```
And add this root as command directly:
```json
{
  "mcpServers": {
    "playwright-python": {
      "command": "/home/camil/.cache/pypoetry/virtualenvs/playwright-mcp-q9z6m5j4-py3.10/bin/playwright-mcp",
      "args": ["--headless"]
    }
  }
}
```

### Command Line Options
- `--browser`: Choose browser (chromium, firefox, webkit)
- `--headless`: Run in headless mode
- `--viewport-width`: Set viewport width (default: 1280)
- `--viewport-height`: Set viewport height (default: 720)
- `--timeout`: Set default timeout in ms (default: 30000)

### Available Tools

#### Navigation
- `browser_navigate`: Navigate to a URL
- `browser_navigate_back`: Go back
- `browser_navigate_forward`: Go forward

#### Interactions
- `browser_click`: Click on elements
- `browser_type`: Type text into fields
- `browser_fill`: Fill input fields
- `browser_select_option`: Select from dropdowns

#### Capture & Extraction
- `browser_screenshot`: Take screenshots
- `browser_get_text`: Extract text content
- `browser_get_html`: Get HTML content
- `browser_console_messages`: Get console logs

#### Utilities
- `browser_wait`: Wait for time/elements/text
- `browser_reload`: Reload page
- `browser_scroll`: Scroll page
- `browser_evaluate`: Execute JavaScript
- `browser_tab_*`: Tab management

## License
MIT License