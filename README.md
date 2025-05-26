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
git clone <repository>
make install
make test
```

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

# A corriger:
⚠️ Quand l'agent appelle "browser_screenshot", ça retourne : `PlaywrightMCPServer._setup_handlers.<locals>.handle_call_tool() takes 1 positional argument but 2 were given`

## License
MIT License