# ABOUTME: MCP resources providing streaming/templated log access via URI patterns.
# ABOUTME: Provides 5 resources: logs://recent, logs://request/{id}, logs://session/{id}, logs://errors, logs://source/{name}.

"""MCP resources for MC Logger

Provides resource URIs that AI assistants can use to access log data in structured formats.
Resources support both static URIs (logs://recent) and templated URIs (logs://request/{request_id}).
"""

import json
from typing import List

from mc_logger import mcp_tools
from mc_logger.mcp.server import mcp


@mcp.resource("logs://recent")
def get_recent_logs() -> str:
    """Get logs from the last 5 minutes as JSON array.

    Returns:
        JSON array of log entries from the last 5 minutes
    """
    entries = mcp_tools.query_logs(time_range="5m", limit=1000)

    # Convert LogEntry objects to dictionaries
    log_dicts = [
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

    return json.dumps(log_dicts, indent=2)


@mcp.resource("logs://request/{request_id}")
def get_request_logs(request_id: str) -> str:
    """Get all logs for a specific request ID as JSON array.

    Args:
        request_id: The request ID to query

    Returns:
        JSON array of log entries for the specified request
    """
    entries = mcp_tools.query_logs(request_id=request_id, limit=10000)

    # Convert LogEntry objects to dictionaries
    log_dicts = [
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

    return json.dumps(log_dicts, indent=2)


@mcp.resource("logs://session/{session_id}")
def get_session_logs(session_id: str) -> str:
    """Get all logs for a specific session ID as JSON array.

    Args:
        session_id: The session ID to query

    Returns:
        JSON array of log entries for the specified session
    """
    entries = mcp_tools.query_logs(session_id=session_id, limit=10000)

    # Convert LogEntry objects to dictionaries
    log_dicts = [
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

    return json.dumps(log_dicts, indent=2)


@mcp.resource("logs://errors")
def get_error_logs() -> str:
    """Get ERROR level logs from the last 5 minutes as JSON array.

    Returns:
        JSON array of ERROR level log entries from the last 5 minutes
    """
    entries = mcp_tools.query_logs(time_range="5m", level="ERROR", limit=1000)

    # Convert LogEntry objects to dictionaries
    log_dicts = [
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

    return json.dumps(log_dicts, indent=2)


@mcp.resource("logs://source/{source}")
def get_source_logs(source: str) -> str:
    """Get logs from a specific source in the last 5 minutes as JSON array.

    Args:
        source: The source name to query (e.g., 'middleware', 'application')

    Returns:
        JSON array of log entries from the specified source
    """
    entries = mcp_tools.query_logs(time_range="5m", source=source, limit=1000)

    # Convert LogEntry objects to dictionaries
    log_dicts = [
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

    return json.dumps(log_dicts, indent=2)
