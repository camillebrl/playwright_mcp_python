#!/usr/bin/env python3
"""Test pour lister tous les outils disponibles du serveur Playwright."""

import asyncio
import json
import os
import subprocess
import sys


async def list_playwright_tools():
    """Liste tous les outils disponibles."""
    try:
        print("🎭 Connexion au serveur Playwright...")

        # Changer vers le dossier src
        src_path = os.path.join(os.getcwd(), "src")

        # Démarrer le serveur
        cmd = [sys.executable, "-m", "playwright_mcp.cli", "--headless"]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=src_path,
        )

        # Attendre le démarrage
        await asyncio.sleep(2)

        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tools-lister", "version": "1.0.0"},
            },
        }

        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Lire réponse init
        await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), timeout=10.0)
        print("✅ Serveur initialisé")

        # Notification initialized
        initialized_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        process.stdin.write(json.dumps(initialized_notif) + "\n")
        process.stdin.flush()

        await asyncio.sleep(0.5)

        # Demander la liste des outils
        print("\n📋 Demande de la liste des outils...")
        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()

        # Lire la réponse
        tools_response = await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), timeout=15.0)

        response_data = json.loads(tools_response.strip())

        if "error" in response_data:
            print(f"❌ Erreur: {response_data['error']['message']}")
            return

        tools = response_data["result"]["tools"]
        print(f"\n🎉 {len(tools)} outils disponibles:")
        print("=" * 80)

        # Organiser les outils par catégorie
        categories = {"Navigation": [], "Interaction": [], "Capture": [], "Utility": []}

        for tool in tools:
            name = tool["name"]
            if name.startswith("browser_navigate"):
                categories["Navigation"].append(tool)
            elif name in ["browser_click", "browser_type", "browser_fill", "browser_select_option"]:
                categories["Interaction"].append(tool)
            elif name in ["browser_screenshot", "browser_get_text", "browser_get_html", "browser_console_messages"]:
                categories["Capture"].append(tool)
            else:
                categories["Utility"].append(tool)

        # Afficher par catégorie
        for category, category_tools in categories.items():
            if category_tools:
                print(f"\n🔧 {category} ({len(category_tools)} outils):")
                print("-" * 50)

                for tool in category_tools:
                    print(f"  📌 {tool['name']}")
                    print(f"     📝 {tool['description']}")

                    # Afficher les paramètres principaux
                    schema = tool.get("inputSchema", {})
                    properties = schema.get("properties", {})

                    if properties:
                        required = schema.get("required", [])
                        params = []

                        for param_name, param_info in properties.items():
                            param_type = param_info.get("type", "unknown")
                            is_required = param_name in required
                            req_marker = "🔴" if is_required else "⚪"
                            params.append(f"{req_marker} {param_name} ({param_type})")

                        if params:
                            print(f"     📊 Paramètres: {', '.join(params)}")

                    print()

        # Quelques exemples d'utilisation
        print("\n💡 Exemples d'utilisation:")
        print("=" * 50)

        examples = [
            ("Naviguer vers une page", "browser_navigate", '{"url": "https://example.com"}'),
            ("Prendre une capture", "browser_screenshot", '{"full_page": true}'),
            ("Cliquer sur un élément", "browser_click", '{"selector": "button"}'),
            ("Saisir du texte", "browser_type", '{"selector": "input", "text": "Hello"}'),
            ("Lister les onglets", "browser_tab_list", "{}"),
        ]

        for desc, tool_name, params in examples:
            print(f"  🚀 {desc}:")
            print(f"     Outil: {tool_name}")
            print(f"     Paramètres: {params}")
            print()

        return tools

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if process:
            try:
                process.terminate()
                process.wait()
            except Exception:
                pass


async def main():
    """Fonction principale."""
    print("🎭 Playwright MCP - Liste des outils")
    print("=" * 60)

    tools = await list_playwright_tools()

    if tools:
        print(f"\n✅ Serveur opérationnel avec {len(tools)} outils!")
        print("\n💡 Vous pouvez maintenant utiliser ces outils avec un client MCP")
        print("   ou les intégrer dans Claude Desktop, VS Code, etc.")


if __name__ == "__main__":
    asyncio.run(main())
