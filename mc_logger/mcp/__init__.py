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
except ImportError as e:
    raise ImportError(
        "MC Logger MCP server requires FastMCP. "
        "Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'"
    ) from e

# Import after FastMCP check to ensure dependency is available
from mc_logger.mcp.server import mcp, create_server

# Register resources and prompts with the server
# This must happen after the mcp instance is created to avoid circular imports
from mc_logger.mcp.resources import register_resources
from mc_logger.mcp.prompts import register_prompts

register_resources(mcp)
register_prompts(mcp)

__all__ = ["mcp", "create_server", "FastMCP"]
