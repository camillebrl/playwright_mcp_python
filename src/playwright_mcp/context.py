"""Browser context management"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class Tab:
    """Represents a browser tab"""
    
    def __init__(self, page: Page, tab_id: str):
        self.page = page
        self.tab_id = tab_id
        self._console_messages: List[str] = []
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Setup page event listeners"""
        self.page.on("console", self._on_console)
    
    def _on_console(self, msg):
        """Handle console messages"""
        self._console_messages.append(f"[{msg.type.upper()}] {msg.text}")
    
    async def get_title(self) -> str:
        """Get page title"""
        return await self.page.title()
    
    async def get_url(self) -> str:
        """Get page URL"""
        return self.page.url
    
    def get_console_messages(self) -> List[str]:
        """Get collected console messages"""
        return self._console_messages.copy()
    
    def clear_console_messages(self):
        """Clear console messages"""
        self._console_messages.clear()


class BrowserManager:
    """Manages browser context and tabs"""
    
    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout: int = 30000,
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.tabs: Dict[str, Tab] = {}
        self.current_tab_id: Optional[str] = None
        
    async def start(self):
        """Start browser context"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            self.context = await self.browser.new_context(
                viewport={
                    "width": self.viewport_width, 
                    "height": self.viewport_height
                }
            )
            self.context.set_default_timeout(self.timeout)
    
    async def stop(self):
        """Stop browser context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        self.context = None
        self.browser = None
        self.playwright = None
        self.tabs.clear()
        self.current_tab_id = None
    
    async def get_current_tab(self) -> Tab:
        """Get current active tab"""
        if not self.current_tab_id or self.current_tab_id not in self.tabs:
            await self.new_tab()
        return self.tabs[self.current_tab_id]
    
    async def new_tab(self, url: Optional[str] = None) -> Tab:
        """Create new tab"""
        await self.start()
        
        page = await self.context.new_page()
        tab_id = f"tab_{len(self.tabs) + 1}"
        tab = Tab(page, tab_id)
        
        self.tabs[tab_id] = tab
        self.current_tab_id = tab_id
        
        if url:
            await page.goto(url)
            
        return tab
    
    async def close_tab(self, tab_id: str):
        """Close a tab"""
        if tab_id in self.tabs:
            await self.tabs[tab_id].page.close()
            del self.tabs[tab_id]
            
            if self.current_tab_id == tab_id:
                self.current_tab_id = next(iter(self.tabs.keys())) if self.tabs else None
    
    async def switch_tab(self, tab_id: str):
        """Switch to a tab"""
        if tab_id in self.tabs:
            self.current_tab_id = tab_id
            await self.tabs[tab_id].page.bring_to_front()
    
    def list_tabs(self) -> List[Dict[str, Any]]:
        """List all tabs"""
        tabs_info = []
        for tab_id, tab in self.tabs.items():
            tabs_info.append({
                "id": tab_id,
                "title": tab.page.title() if hasattr(tab.page, 'title') else "Loading...",
                "url": tab.page.url,
                "active": tab_id == self.current_tab_id
            })
        return tabs_info
