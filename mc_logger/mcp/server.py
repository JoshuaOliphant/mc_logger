# ABOUTME: FastMCP server implementation wrapping existing mcp_tools functions as MCP tools.
# ABOUTME: Provides 5 MCP tools: query_logs, get_request_trace, summarize_logs, mark_session, configure_logger.

"""FastMCP server for MC Logger

This module wraps existing mcp_tools.py functions as MCP tools, allowing AI assistants
to query and analyze logs through the Model Context Protocol.
"""

from typing import List, Optional

from fastmcp import FastMCP

from mc_logger import mcp_tools
from mc_logger.core import Logger, configure
from mc_logger.models import LogEntry

# Create FastMCP server instance
mcp = FastMCP(
    "MC Logger",
    instructions="Semantic logging system optimized for AI-assisted debugging. "
    "Query logs by time range, request ID, session ID, level, or source. "
    "Get request traces, summarize log statistics, and mark important sessions.",
)


@mcp.tool()
def query_logs(
    time_range: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 1000,
) -> List[dict]:
    """Query logs with optional filters.

    Args:
        time_range: Time range like '5m', '2h', '1d' (optional)
        request_id: Filter by request ID (optional)
        session_id: Filter by session ID (optional)
        level: Filter by log level: DEBUG, INFO, WARNING, ERROR (optional)
        source: Filter by source name (optional)
        limit: Maximum number of entries to return (default: 1000)

    Returns:
        List of log entries as dictionaries with timestamp, level, message, etc.
    """
    entries = mcp_tools.query_logs(
        time_range=time_range,
        request_id=request_id,
        session_id=session_id,
        level=level,
        source=source,
        limit=limit,
    )

    # Convert LogEntry objects to dictionaries
    return [
        {
            "timestamp": entry.timestamp,
            "level": entry.level,
            "message": entry.message,
            "source": entry.source,
            "request_id": entry.request_id,
            "session_id": entry.session_id,
            "correlation_id": entry.correlation_id,
            "metadata": entry.metadata,
        }
        for entry in entries
    ]


@mcp.tool()
def get_request_trace(request_id: str) -> str:
    """Get markdown-formatted timeline for a specific request.

    Args:
        request_id: The request ID to trace

    Returns:
        Markdown-formatted trace with timeline, duration, and event details.
        Includes emoji indicators: ❌ ERROR, ⚠️ WARNING, ℹ️ INFO, 🔍 DEBUG
    """
    return mcp_tools.get_request_trace(request_id)


@mcp.tool()
def summarize_logs(
    time_range: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Generate markdown summary with statistics by level and source.

    Args:
        time_range: Time range like '5m', '2h', '1d' (optional)
        request_id: Filter by request ID (optional)
        session_id: Filter by session ID (optional)

    Returns:
        Markdown-formatted summary with event counts by level and source
    """
    return mcp_tools.summarize_logs(
        time_range=time_range,
        request_id=request_id,
        session_id=session_id,
    )


@mcp.tool()
def mark_session(
    session_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> str:
    """Mark a session as important for preservation.

    Args:
        session_id: The session ID to mark
        start_time: Start time in format '5m', '2h', '1d' ago (optional)
        end_time: End time in format '5m', '2h', '1d' ago (optional)

    Returns:
        Confirmation message
    """
    # Convert time strings to timestamps if provided
    start_ts = None
    end_ts = None

    if start_time:
        start_ts, _ = mcp_tools.parse_time_range(start_time)

    if end_time:
        _, end_ts = mcp_tools.parse_time_range(end_time)

    return mcp_tools.mark_session(
        session_id=session_id,
        start_time=start_ts,
        end_time=end_ts,
    )


@mcp.tool()
def configure_logger(
    db_path: str = "./mc_logger.db",
    flush_interval: float = 1.0,
) -> str:
    """Configure the MC Logger instance.

    Args:
        db_path: Path to SQLite database file (default: ./mc_logger.db)
        flush_interval: Seconds between queue flushes (default: 1.0)

    Returns:
        Confirmation message
    """
    configure(db_path=db_path, flush_interval=flush_interval, force=True)
    return f"Logger configured: db_path={db_path}, flush_interval={flush_interval}s"


def create_server() -> FastMCP:
    """Factory function to create a new FastMCP server instance.

    Returns:
        Configured FastMCP server instance with all tools registered
    """
    return mcp


# Allow running directly with: python -m mc_logger.mcp.server
# Or with FastMCP CLI: fastmcp run mc_logger/mcp/server.py
if __name__ == "__main__":
    mcp.run()
