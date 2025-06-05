"""Capture and extraction tools."""

import asyncio
import base64
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from mcp.types import ImageContent, TextContent

from .base import BaseToolSet, ToolInfo, ToolResult


class CaptureTools(BaseToolSet):
    """Tools for capturing screenshots and extracting content."""

    def get_tools(self) -> dict[str, ToolInfo]:
        """Get available capture tools.

        Returns:
            dict[str, ToolInfo]: Dictionary mapping tool names to their info
        """
        return {
            "browser_screenshot": ToolInfo(
                name="browser_screenshot",
                description="Take a screenshot of the current page",
                input_schema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Optional filename to save screenshot",
                        },
                        "full_page": {
                            "type": "boolean",
                            "description": "Capture full page",
                            "default": False,
                        },
                        "element_selector": {
                            "type": "string",
                            "description": "CSS selector to screenshot specific element",
                        },
                    },
                },
                execute=self._screenshot,
            ),
            "browser_screenshot_pages": ToolInfo(
                name="browser_screenshot_pages",
                description="Take screenshots page by page (useful for long pages)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "description": "Folder to save screenshots",
                            "default": "screenshots",
                        },
                        "filename_prefix": {
                            "type": "string",
                            "description": "Prefix for screenshot filenames",
                            "default": "page",
                        },
                        "viewport_height": {
                            "type": "number",
                            "description": "Height of each page in pixels",
                            "default": 800,
                        },
                        "overlap": {
                            "type": "number",
                            "description": "Overlap between pages in pixels",
                            "default": 50,
                        },
                        "max_pages": {
                            "type": "number",
                            "description": "Maximum number of pages to capture",
                            "default": 20,
                        },
                        "format": {
                            "type": "string",
                            "description": "Image format",
                            "enum": ["png", "jpeg"],
                            "default": "png",
                        },
                        "quality": {
                            "type": "number",
                            "description": "Image quality (for jpeg only, 0-100)",
                            "default": 90,
                        },
                    },
                },
                execute=self._screenshot_pages,
            ),
            "browser_get_text": ToolInfo(
                name="browser_get_text",
                description="Extract text content from page or element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector (optional, defaults to body)",
                        }
                    },
                },
                execute=self._get_text,
            ),
            "browser_get_html": ToolInfo(
                name="browser_get_html",
                description="Get HTML content of page or element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector (optional, defaults to full page)",
                        }
                    },
                },
                execute=self._get_html,
            ),
            "browser_console_messages": ToolInfo(
                name="browser_console_messages",
                description="Get console messages from the page",
                input_schema={"type": "object", "properties": {}},
                execute=self._get_console_messages,
            ),
            "browser_download_pdf": ToolInfo(
                name="browser_download_pdf",
                description="Download the current page as PDF",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder": {
                            "type": "string",
                            "description": "Folder path where to save the PDF",
                            "default": "downloads",
                        },
                        "filename": {
                            "type": "string",
                            "description": "PDF filename (without extension)",
                        },
                        "format": {
                            "type": "string",
                            "description": "Paper format",
                            "enum": [
                                "Letter",
                                "Legal",
                                "Tabloid",
                                "Ledger",
                                "A0",
                                "A1",
                                "A2",
                                "A3",
                                "A4",
                                "A5",
                                "A6",
                            ],
                            "default": "A4",
                        },
                        "landscape": {
                            "type": "boolean",
                            "description": "Page orientation",
                            "default": False,
                        },
                        "scale": {
                            "type": "number",
                            "description": "Scale of the webpage rendering",
                            "default": 1.0,
                        },
                        "display_header_footer": {
                            "type": "boolean",
                            "description": "Display header and footer",
                            "default": False,
                        },
                        "print_background": {
                            "type": "boolean",
                            "description": "Print background graphics",
                            "default": True,
                        },
                        "margin": {
                            "type": "object",
                            "description": "Page margins",
                            "properties": {
                                "top": {"type": "string", "default": "0"},
                                "right": {"type": "string", "default": "0"},
                                "bottom": {"type": "string", "default": "0"},
                                "left": {"type": "string", "default": "0"},
                            },
                        },
                    },
                    "required": ["filename"],
                },
                execute=self._download_pdf_on_page,
            ),
            "browser_download_pdf_with_curl": ToolInfo(
                name="browser_download_pdf_with_curl",
                description="Download a PDF file from a specific URL using curl for maximum compatibility",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Direct URL of the PDF file to download",
                        },
                        "folder": {
                            "type": "string",
                            "description": "Destination folder path (default: 'downloads')",
                            "default": "downloads",
                        },
                        "filename": {
                            "type": "string",
                            "description": "Custom filename for the downloaded PDF (optional, will auto-generate if not provided)",
                        },
                        "follow_redirects": {
                            "type": "boolean",
                            "description": "Whether to follow HTTP redirects (default: true)",
                            "default": True,
                        },
                        "max_time": {
                            "type": "integer",
                            "description": "Maximum download time in seconds before timeout (default: 300)",
                            "default": 300,
                        },
                    },
                    "required": ["url"],
                },
                execute=self._download_pdf_with_curl,
            ),
        }

    async def _screenshot(self, args: dict[str, Any]) -> ToolResult:
        """Take screenshot."""
        try:
            tab = await self.browser_manager.get_current_tab()
            filename = args.get("filename")
            full_page = args.get("full_page", False)
            element_selector = args.get("element_selector")

            # Préparer les options de screenshot
            screenshot_options = {"full_page": full_page}

            if element_selector:
                # Screenshot specific element
                element = tab.page.locator(element_selector)
                screenshot_bytes = await element.screenshot()
                target = f"element '{element_selector}'"
            else:
                # Screenshot full page - utiliser ** pour unpacker le dict
                screenshot_bytes = await tab.page.screenshot(**screenshot_options)
                target = "page"

            # Save to file if filename provided
            if filename:
                Path(filename).write_bytes(screenshot_bytes)
                saved_msg = f" (saved as {filename})"
            else:
                saved_msg = ""

            # Return image content
            base64_image = base64.b64encode(screenshot_bytes).decode()

            return ToolResult(
                content=[
                    ImageContent(type="image", data=base64_image, mimeType="image/png"),
                    TextContent(
                        type="text",
                        text=f"📸 Screenshot of {target}{saved_msg}",
                    ),
                ]
            )
        except Exception as e:
            # Log l'erreur complète pour debugging
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Screenshot error: {str(e)}")
            logger.error(traceback.format_exc())

            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Screenshot failed: {str(e)}")],
                is_error=True,
            )

    async def _screenshot_pages(self, args: dict[str, Any]) -> ToolResult:
        """Take screenshots page by page."""
        try:
            tab = await self.browser_manager.get_current_tab()

            # Get parameters
            folder = args.get("folder", "screenshots")
            filename_prefix = args.get("filename_prefix", "page")
            viewport_height = args.get("viewport_height", 800)
            overlap = args.get("overlap", 50)
            max_pages = args.get("max_pages", 20)
            format_type = args.get("format", "png")
            quality = args.get("quality", 90)

            # Create folder if it doesn't exist
            folder_path = Path(folder)
            folder_path.mkdir(parents=True, exist_ok=True)

            # Get page dimensions
            page_height = await tab.page.evaluate("document.documentElement.scrollHeight")
            viewport_width = await tab.page.evaluate("window.innerWidth")

            # Calculate number of pages
            effective_height = viewport_height - overlap
            num_pages = min(
                max_pages,
                int((page_height + effective_height - 1) / effective_height),
            )

            # Store original scroll position
            original_scroll = await tab.page.evaluate("window.pageYOffset")

            screenshots = []
            filenames = []

            try:
                # Scroll to top first
                await tab.page.evaluate("window.scrollTo(0, 0)")
                await tab.page.wait_for_timeout(100)  # Small delay for rendering

                for page_num in range(num_pages):
                    # Calculate scroll position
                    scroll_y = page_num * effective_height

                    # Scroll to position
                    await tab.page.evaluate(f"window.scrollTo(0, {scroll_y})")
                    await tab.page.wait_for_timeout(100)  # Small delay for rendering

                    # Prepare screenshot options
                    screenshot_options: dict[str, Any] = {
                        "clip": {
                            "x": 0,
                            "y": 0,
                            "width": viewport_width,
                            "height": min(viewport_height, page_height - scroll_y),
                        }
                    }

                    if format_type == "jpeg":
                        screenshot_options["type"] = "jpeg"
                        screenshot_options["quality"] = quality
                    else:
                        screenshot_options["type"] = "png"

                    # Take screenshot
                    screenshot_bytes = await tab.page.screenshot(**screenshot_options)

                    # Save to file
                    filename = f"{filename_prefix}_{page_num + 1:03d}.{format_type}"
                    file_path = folder_path / filename
                    file_path.write_bytes(screenshot_bytes)
                    filenames.append(str(file_path))

                    # Add to results (only include first few pages as base64 to avoid huge responses)
                    if page_num < 3:  # Only include first 3 pages as base64
                        base64_image = base64.b64encode(screenshot_bytes).decode()
                        mime_type = f"image/{format_type}"
                        screenshots.append(
                            ImageContent(
                                type="image",
                                data=base64_image,
                                mimeType=mime_type,
                            )
                        )

                # Restore original scroll position
                await tab.page.evaluate(f"window.scrollTo(0, {original_scroll})")

            except Exception as e:
                # Restore scroll position even on error
                await tab.page.evaluate(f"window.scrollTo(0, {original_scroll})")
                raise e

            # Build result message
            result_text = "📸 Page-by-page screenshots captured:\n"
            result_text += f"📁 Folder: {folder_path}\n"
            result_text += f"📑 Pages captured: {num_pages}\n"
            result_text += f"📐 Page size: {viewport_width}x{viewport_height}px\n"
            result_text += f"📏 Total height: {page_height}px\n"
            result_text += "📄 Files saved:\n"
            for filename in filenames:
                result_text += f"  - {filename}\n"

            # Build content list with proper typing
            content: list[TextContent | ImageContent] = [TextContent(type="text", text=result_text)]
            content.extend(screenshots)

            return ToolResult(content=content)

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Page screenshot error: {str(e)}")
            logger.error(traceback.format_exc())

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Page screenshots failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _get_text(self, args: dict[str, Any]) -> ToolResult:
        """Extract text content."""
        selector = args.get("selector", "body")
        tab = await self.browser_manager.get_current_tab()

        try:
            if selector == "body":
                text = await tab.page.text_content("body")
                source = "page"
            else:
                element = tab.page.locator(selector)
                text = await element.text_content()
                source = f"element '{selector}'"

            if not text:
                text = "(no text content found)"

            return ToolResult(content=[TextContent(type="text", text=f"📄 Text from {source}:\n\n{text}")])
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Text extraction failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _get_html(self, args: dict[str, Any]) -> ToolResult:
        """Get HTML content."""
        selector = args.get("selector")
        tab = await self.browser_manager.get_current_tab()

        try:
            if selector:
                element = tab.page.locator(selector)
                html = await element.inner_html()
                source = f"element '{selector}'"
            else:
                html = await tab.page.content()
                source = "page"

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"🔖 HTML from {source}:\n\n```html\n{html}\n```",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ HTML extraction failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _get_console_messages(self, args: dict[str, Any]) -> ToolResult:
        """Get console messages."""
        tab = await self.browser_manager.get_current_tab()

        try:
            messages = tab.get_console_messages()
            if not messages:
                return ToolResult(content=[TextContent(type="text", text="📋 No console messages")])

            messages_text = "\n".join(messages)
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"📋 Console messages:\n\n{messages_text}",
                    )
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Console messages failed: {str(e)}",
                    )
                ],
                is_error=True,
            )

    async def _download_pdf_on_page(self, args: dict[str, Any]) -> ToolResult:
        """Trouve et télécharge tous les PDFs présents dans la page HTML."""
        try:
            tab = await self.browser_manager.get_current_tab()
            
            # Paramètres
            folder = args.get("folder", "downloads")
            
            # Créer le dossier si nécessaire
            folder_path = Path(folder)
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Rechercher tous les liens PDF dans la page
            pdf_links = await tab.page.evaluate("""
                () => {
                    const links = [];
                    
                    // Chercher dans les liens <a>
                    document.querySelectorAll('a[href]').forEach(link => {
                        const href = link.href;
                        if (href.toLowerCase().includes('.pdf') || 
                            href.toLowerCase().includes('pdf') ||
                            link.textContent.toLowerCase().includes('pdf')) {
                            links.push({
                                url: href,
                                text: link.textContent.trim(),
                                type: 'link'
                            });
                        }
                    });
                    
                    // Chercher dans les embed/object
                    document.querySelectorAll('embed[src], object[data]').forEach(embed => {
                        const src = embed.src || embed.data;
                        if (src && src.toLowerCase().includes('.pdf')) {
                            links.push({
                                url: src,
                                text: embed.title || 'PDF embed',
                                type: 'embed'
                            });
                        }
                    });
                    
                    // Chercher dans les iframes
                    document.querySelectorAll('iframe[src]').forEach(iframe => {
                        const src = iframe.src;
                        if (src && src.toLowerCase().includes('.pdf')) {
                            links.push({
                                url: src,
                                text: iframe.title || 'PDF iframe',
                                type: 'iframe'
                            });
                        }
                    });
                    
                    return links;
                }
            """)
            
            if not pdf_links:
                return ToolResult(
                    content=[TextContent(type="text", text="❌ Aucun PDF trouvé sur cette page")]
                )
            
            downloaded_files = []
            failed_downloads = []
            
            # Télécharger chaque PDF
            for i, pdf_info in enumerate(pdf_links):
                try:
                    url = pdf_info['url']
                    
                    # Résoudre l'URL relative si nécessaire
                    if not url.startswith(('http://', 'https://')):
                        base_url = tab.page.url
                        url = urljoin(base_url, url)
                    
                    # Générer un nom de fichier
                    filename = args.get("filename_pattern", f"pdf_{i+1}.pdf")
                    if "{index}" in filename:
                        filename = filename.replace("{index}", str(i+1))
                    if "{title}" in filename:
                        safe_title = "".join(c for c in pdf_info['text'][:50] if c.isalnum() or c in (' ', '-', '_')).strip()
                        filename = filename.replace("{title}", safe_title or f"pdf_{i+1}")
                    
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    file_path = folder_path / filename
                    
                    # Télécharger le PDF
                    response = await tab.page.goto(url)
                    if response and response.ok:
                        pdf_content = await response.body()
                        
                        with open(file_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        downloaded_files.append({
                            'path': str(file_path),
                            'url': url,
                            'title': pdf_info['text'],
                            'type': pdf_info['type']
                        })
                    else:
                        failed_downloads.append(f"{url} - Erreur de téléchargement")
                        
                except Exception as e:
                    failed_downloads.append(f"{url} - {str(e)}")
            
            # Retourner à la page originale
            await tab.page.go_back()
            
            # Préparer le message de résultat
            result_text = f"📄 {len(downloaded_files)} PDF(s) téléchargé(s):\n\n"
            
            for pdf in downloaded_files:
                result_text += f"✅ {pdf['title'][:50]}...\n"
                result_text += f"   📁 {pdf['path']}\n"
                result_text += f"   🔗 {pdf['url']}\n\n"
            
            if failed_downloads:
                result_text += f"\n❌ {len(failed_downloads)} échec(s):\n"
                for failure in failed_downloads:
                    result_text += f"   • {failure}\n"
            
            return ToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
            
        except Exception as e:
            import logging
            import traceback
            
            logger = logging.getLogger(__name__)
            logger.error(f"PDF download error: {str(e)}")
            logger.error(traceback.format_exc())
            
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Erreur lors du téléchargement des PDFs: {str(e)}")],
                is_error=True,
            )

    async def _download_pdf_with_curl(self, args: dict[str, Any]) -> ToolResult:
        """Télécharge un PDF en utilisant curl."""
        try:
            import subprocess
            import shlex
            
            # Paramètres requis
            url = args["url"]
            
            # Paramètres optionnels
            folder = args.get("folder", "downloads")
            filename = args.get("filename")
            follow_redirects = args.get("follow_redirects", True)
            max_time = args.get("max_time", 300)  # 5 minutes par défaut
            
            # Créer le dossier si nécessaire
            folder_path = Path(folder)
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Générer le nom de fichier si non fourni
            if not filename:
                from urllib.parse import urlparse, unquote
                import os
                parsed_url = urlparse(url)
                filename = unquote(os.path.basename(parsed_url.path))
                if not filename or not filename.endswith('.pdf'):
                    import time
                    filename = f"curl_download_{int(time.time())}.pdf"
            
            # S'assurer que le fichier a l'extension .pdf
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            file_path = folder_path / filename
            
            # Construire la commande curl
            curl_cmd = [
                'curl',
                '--silent',
                '--show-error',
                '--fail',
                '--location' if follow_redirects else '--no-location',
                '--max-time', str(max_time),
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--header', 'Accept: application/pdf,application/octet-stream,*/*',
                '--header', 'Accept-Language: fr-FR,fr;q=0.9,en;q=0.8',
                '--output', str(file_path),
                url
            ]
            
            # Exécuter la commande curl
            process = await asyncio.create_subprocess_exec(
                *curl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Vérifier que le fichier existe et n'est pas vide
                if file_path.exists() and file_path.stat().st_size > 0:
                    file_size = file_path.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    
                    return ToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"📄 PDF téléchargé avec curl:\n"
                                f"📁 Fichier: {file_path}\n"
                                f"🔗 URL: {url}\n"
                                f"📊 Taille: {file_size_mb:.2f} MB\n"
                                f"✅ Téléchargement réussi"
                            )
                        ]
                    )
                else:
                    return ToolResult(
                        content=[TextContent(type="text", text="❌ Le fichier téléchargé est vide ou inexistant")],
                        is_error=True
                    )
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Erreur inconnue"
                return ToolResult(
                    content=[TextContent(type="text", text=f"❌ Erreur curl (code {process.returncode}): {error_msg}")],
                    is_error=True
                )
        
        except subprocess.CalledProcessError as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Erreur de processus curl: {str(e)}")],
                is_error=True
            )
        except Exception as e:
            import logging
            import traceback
            
            logger = logging.getLogger(__name__)
            logger.error(f"Curl PDF download error: {str(e)}")
            logger.error(traceback.format_exc())
            
            return ToolResult(
                content=[TextContent(type="text", text=f"❌ Erreur lors du téléchargement avec curl: {str(e)}")],
                is_error=True,
            )