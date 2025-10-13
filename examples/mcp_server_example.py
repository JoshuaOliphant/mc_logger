"""Example: Running MC Logger as an MCP Server

This example demonstrates how to start MC Logger as an MCP server programmatically.
The server can be used by AI assistants to query and analyze logs.

Usage:
    uv run python examples/mcp_server_example.py

Note: This requires the MCP extra to be installed:
    uv add "mc-logger[mcp]"
"""

import sys

try:
    from mc_logger import configure
    from mc_logger.mcp import mcp
except ImportError:
    print("Error: MCP server requires FastMCP.")
    print("Install with: uv add 'mc-logger[mcp]'")
    sys.exit(1)


def main():
    """Start the MCP server with sample configuration."""

    # Configure MC Logger
    print("Configuring MC Logger...")
    configure(
        db_path="./example_logs.db",
        flush_interval=1.0,
    )

    print("MC Logger configured:")
    print("  Database: ./example_logs.db")
    print("  Flush interval: 1.0s")
    print()

    print("Starting MCP server with stdio transport...")
    print("The server will communicate via stdin/stdout.")
    print("Use Ctrl+C to stop the server.")
    print()

    # Start the MCP server
    # This will block until the server is stopped
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down MCP server...")


if __name__ == "__main__":
    main()
