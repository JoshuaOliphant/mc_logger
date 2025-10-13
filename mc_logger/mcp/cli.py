# ABOUTME: CLI entry point for MC Logger MCP server with environment variable support.
# ABOUTME: Provides mc-logger-mcp command with configurable transport, database path, and flush interval.

"""CLI for MC Logger MCP Server

Command-line interface for starting the MC Logger MCP server with support
for environment variables and multiple transport modes (stdio, HTTP).

Environment Variables:
    MC_LOGGER_DB_PATH: Path to SQLite database (default: ./mc_logger.db)
    MC_LOGGER_FLUSH_INTERVAL: Seconds between queue flushes (default: 1.0)
    MC_LOGGER_TRANSPORT: Transport mode - stdio or http (default: stdio)
    MC_LOGGER_PORT: Port for HTTP transport (default: 8000)

Usage:
    # Start with stdio transport (for Claude Desktop)
    mc-logger-mcp

    # Start with HTTP transport
    mc-logger-mcp --transport http --port 8000

    # Use environment variables
    export MC_LOGGER_DB_PATH=/var/log/app.db
    export MC_LOGGER_FLUSH_INTERVAL=2.0
    mc-logger-mcp
"""

import argparse
import os
import sys


def main():
    """Main entry point for the MCP server CLI."""
    # Try to import MCP module with helpful error message
    try:
        from mc_logger.mcp import mcp
        from mc_logger.mcp.server import configure_logger
    except ImportError as e:
        print(
            "Error: MC Logger MCP server requires FastMCP.",
            file=sys.stderr,
        )
        print(
            "Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="MC Logger MCP Server - Semantic logging for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  MC_LOGGER_DB_PATH          Path to SQLite database (default: ./mc_logger.db)
  MC_LOGGER_FLUSH_INTERVAL   Seconds between queue flushes (default: 1.0)
  MC_LOGGER_TRANSPORT        Transport mode - stdio or http (default: stdio)
  MC_LOGGER_PORT            Port for HTTP transport (default: 8000)

Examples:
  # Start with stdio transport (for Claude Desktop)
  mc-logger-mcp

  # Start with HTTP transport
  mc-logger-mcp --transport http --port 8000

  # Use environment variables
  export MC_LOGGER_DB_PATH=/var/log/app.db
  mc-logger-mcp
        """,
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default=os.environ.get("MC_LOGGER_DB_PATH", "./mc_logger.db"),
        help="Path to SQLite database (env: MC_LOGGER_DB_PATH)",
    )

    parser.add_argument(
        "--flush-interval",
        type=float,
        default=float(os.environ.get("MC_LOGGER_FLUSH_INTERVAL", "1.0")),
        help="Seconds between queue flushes (env: MC_LOGGER_FLUSH_INTERVAL)",
    )

    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default=os.environ.get("MC_LOGGER_TRANSPORT", "stdio"),
        help="Transport mode - stdio or http (env: MC_LOGGER_TRANSPORT)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MC_LOGGER_PORT", "8000")),
        help="Port for HTTP transport (env: MC_LOGGER_PORT)",
    )

    args = parser.parse_args()

    # Configure logger
    print(f"Configuring MC Logger:", file=sys.stderr)
    print(f"  Database: {args.db_path}", file=sys.stderr)
    print(f"  Flush interval: {args.flush_interval}s", file=sys.stderr)
    print(f"  Transport: {args.transport}", file=sys.stderr)

    if args.transport == "http":
        print(f"  Port: {args.port}", file=sys.stderr)

    configure_logger(db_path=args.db_path, flush_interval=args.flush_interval)

    # Start MCP server
    print("Starting MC Logger MCP server...", file=sys.stderr)

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="http", port=args.port)


if __name__ == "__main__":
    main()
