"""Example: Using MC Logger MCP Server from a Client

This example demonstrates how to interact with MC Logger's MCP server
from a Python client application.

Note: This is a conceptual example. In practice, MCP clients are typically
AI assistants (Claude Desktop, Cursor, etc.) that connect to the server
automatically through their MCP integration.

Usage:
    # Start the server first (in another terminal):
    mc-logger-mcp --transport http --port 8000

    # Then run this client:
    uv run python examples/mcp_client_example.py
"""

import json

import requests


def main():
    """Demonstrate MCP client usage."""

    # Base URL for the MCP server (HTTP transport)
    base_url = "http://localhost:8000"

    print("MC Logger MCP Client Example")
    print("=" * 50)
    print()

    # Example 1: Query recent logs
    print("1. Querying recent logs...")
    try:
        # In a real MCP implementation, you would use the MCP protocol
        # This is a simplified example showing the concept
        response = requests.post(
            f"{base_url}/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "query_logs",
                    "arguments": {
                        "time_range": "5m",
                        "level": "ERROR",
                        "limit": 10,
                    },
                },
            },
        )
        result = response.json()
        print(f"Found {len(result.get('result', []))} ERROR logs in last 5 minutes")
        print()
    except Exception as e:
        print(f"Error querying logs: {e}")
        print()

    # Example 2: Get request trace
    print("2. Getting request trace...")
    try:
        response = requests.post(
            f"{base_url}/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_request_trace",
                    "arguments": {"request_id": "req-001"},
                },
            },
        )
        result = response.json()
        print("Request trace:")
        print(result.get("result", "No trace found"))
        print()
    except Exception as e:
        print(f"Error getting trace: {e}")
        print()

    # Example 3: Summarize logs
    print("3. Summarizing logs...")
    try:
        response = requests.post(
            f"{base_url}/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "summarize_logs",
                    "arguments": {"time_range": "1h"},
                },
            },
        )
        result = response.json()
        print("Log summary:")
        print(result.get("result", "No summary available"))
        print()
    except Exception as e:
        print(f"Error summarizing logs: {e}")
        print()

    # Example 4: Access resource
    print("4. Accessing logs://recent resource...")
    try:
        response = requests.post(
            f"{base_url}/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "logs://recent"},
            },
        )
        result = response.json()
        logs = json.loads(result.get("result", "[]"))
        print(f"Found {len(logs)} recent log entries")
        print()
    except Exception as e:
        print(f"Error accessing resource: {e}")
        print()

    print("=" * 50)
    print("Examples complete!")
    print()
    print("Note: This is a simplified example.")
    print("Real MCP clients (like Claude Desktop) handle the")
    print("protocol details automatically.")


if __name__ == "__main__":
    print()
    print("IMPORTANT: This is a conceptual example.")
    print("Make sure the MCP server is running first:")
    print("  mc-logger-mcp --transport http --port 8000")
    print()
    input("Press Enter to continue...")
    print()

    main()
