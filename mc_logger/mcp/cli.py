# ABOUTME: Minimal CLI wrapper for MC Logger MCP server using FastMCP's built-in CLI.
# ABOUTME: Configures logger from environment variables and delegates to mcp.run().

"""CLI for MC Logger MCP Server

Minimal wrapper around FastMCP's built-in CLI. For most use cases, use FastMCP directly:

    # Recommended: Use FastMCP CLI directly
    fastmcp run mc_logger/mcp/server.py
    fastmcp run mc_logger/mcp/server.py --transport http --port 8080
    fastmcp dev mc_logger/mcp/server.py  # With MCP Inspector

    # Or use this wrapper for environment-based configuration
    mc-logger-mcp

Environment Variables:
    MC_LOGGER_DB_PATH: Path to SQLite database (default: ./mc_logger.db)
    MC_LOGGER_FLUSH_INTERVAL: Seconds between queue flushes (default: 1.0)
"""

import os
import sys


def main():
    """Entry point that configures logger from env vars and runs the server."""
    try:
        from mc_logger import configure
        from mc_logger.mcp import mcp
    except ImportError:
        print(
            "Error: MC Logger MCP server requires FastMCP.",
            file=sys.stderr,
        )
        print(
            "Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Configure logger from environment variables
    db_path = os.environ.get("MC_LOGGER_DB_PATH", "./mc_logger.db")
    flush_interval = float(os.environ.get("MC_LOGGER_FLUSH_INTERVAL", "1.0"))

    print(f"MC Logger Configuration:", file=sys.stderr)
    print(f"  Database: {db_path}", file=sys.stderr)
    print(f"  Flush interval: {flush_interval}s", file=sys.stderr)

    configure(db_path=db_path, flush_interval=flush_interval, force=True)

    # Delegate to FastMCP's built-in CLI
    # This handles --transport, --port, and other FastMCP arguments
    mcp.run()


if __name__ == "__main__":
    main()
