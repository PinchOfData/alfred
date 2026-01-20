#!/usr/bin/env python3
"""
OAuth Setup Script for Alfred MCP Server

Run this script once to authorize Google API access.
It will open a browser window for you to log in and grant permissions.
The token will be saved to memory/token.json for future use.

Usage:
    python init_oauth.py
"""

import os
import sys

# Add script directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from google_utils import get_google_service, TOKEN_PATH, CREDENTIALS_PATH

def main():
    print("Alfred OAuth Setup")
    print("=" * 40)

    # Check for credentials file
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\nError: Credentials file not found at:")
        print(f"  {CREDENTIALS_PATH}")
        print("\nPlease download your OAuth credentials from Google Cloud Console")
        print("and save them as 'google_credentials.json' in the memory/ folder.")
        sys.exit(1)

    print(f"\nCredentials file found: {CREDENTIALS_PATH}")

    # Check if already authorized
    if os.path.exists(TOKEN_PATH):
        print(f"Token already exists: {TOKEN_PATH}")
        response = input("\nRe-authorize? This will replace the existing token. (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing token. Exiting.")
            sys.exit(0)
        os.remove(TOKEN_PATH)

    print("\nStarting OAuth flow...")
    print("A browser window will open for you to authorize access.")
    print()

    try:
        # This will trigger the OAuth flow
        service = get_google_service('gmail', 'v1')
        print("\nSuccess! Token saved to:", TOKEN_PATH)
        print("\nYou can now use the Alfred MCP server with Claude Code.")
        print("\nTo test, run: fastmcp dev mcp_server.py")
    except Exception as e:
        print(f"\nError during OAuth flow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
