# ABOUTME: MCP server module entry point with import guards for optional FastMCP dependency.
# ABOUTME: Provides create_server() factory and mcp server instance when fastmcp is installed.

"""MC Logger MCP Server

This module provides Model Context Protocol (MCP) server integration for MC Logger,
allowing AI assistants to query and analyze logs through standardized MCP tools.

To use this module, install MC Logger with the MCP extra:
    uv add "mc-logger[mcp]"
    # or
    pip install "mc-logger[mcp]"
"""

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "MC Logger MCP server requires FastMCP. "
        "Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'"
    )

from mc_logger.mcp.server import mcp, create_server

# Import resources and prompts modules to register them with the server
import mc_logger.mcp.resources  # noqa: F401
import mc_logger.mcp.prompts  # noqa: F401

__all__ = ["mcp", "create_server", "FastMCP"]
