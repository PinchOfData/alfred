#!/usr/bin/env python3
"""
Initialize Overleaf credentials for the MCP server.

This script prompts for your Overleaf email and password/token,
then stores them in memory/overleaf_config.json.

To get your Overleaf Git credentials:
1. Go to https://www.overleaf.com/user/settings
2. Scroll to "Git Integration"
3. Use your Overleaf email and the password shown there
"""

import getpass
from pathlib import Path
import json

CONFIG_PATH = Path(__file__).parent / "memory" / "overleaf_config.json"


def main():
    print("=" * 50)
    print("Overleaf MCP Server Setup")
    print("=" * 50)
    print()
    print("To find your Git credentials:")
    print("1. Go to https://www.overleaf.com/user/settings")
    print("2. Scroll to 'Git Integration'")
    print("3. Use your Overleaf email and the password shown there")
    print()

    email = input("Overleaf email: ").strip()
    if not email:
        print("Error: Email is required")
        return

    password = getpass.getpass("Overleaf Git password/token: ").strip()
    if not password:
        print("Error: Password is required")
        return

    # Load existing config or create new
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    config["credentials"] = {
        "email": email,
        "password": password
    }
    config.setdefault("projects", {})

    # Save config
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print()
    print(f"Credentials saved to {CONFIG_PATH}")
    print()
    print("Next steps:")
    print("1. Add the Overleaf MCP server to your Claude Code settings")
    print("2. Use overleaf_add_project to add your first project")
    print("3. Use overleaf_pull to clone it locally")


if __name__ == "__main__":
    main()
