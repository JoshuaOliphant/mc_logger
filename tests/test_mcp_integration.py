"""Integration tests for MCP server with actual log data.

Tests end-to-end functionality with a temporary database.
Requires fastmcp to be installed (skip tests otherwise).
"""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp")

from mc_logger import Logger, configure
from mc_logger.context import set_request_id
from mc_logger import mcp_tools


@pytest.fixture
async def temp_db():
    """Create a temporary database with sample log entries."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # Configure logger with temp database
    logger = Logger()
    logger.configure(db_path=temp_path, flush_interval=0.1, force=True)

    # Add some sample log entries
    set_request_id("req-001")
    logger.log("INFO", "User login started", source="auth")
    logger.log("INFO", "Database query executed", source="database")
    logger.log("ERROR", "Invalid credentials", source="auth")

    set_request_id("req-002")
    logger.log("INFO", "API call received", source="api")
    logger.log("WARNING", "Rate limit approaching", source="api")
    logger.log("INFO", "Response sent", source="api")

    set_request_id("req-003")
    logger.log("DEBUG", "Cache hit", source="cache")
    logger.log("INFO", "Data retrieved", source="application")

    # Flush and wait for writes
    logger.flush()
    await asyncio.sleep(0.3)

    yield temp_path

    # Cleanup
    logger.shutdown()
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_query_logs_returns_all_entries(temp_db):
    """Test that query_logs returns all entries when no filters applied."""
    result = mcp_tools.query_logs(limit=100)

    assert isinstance(result, list)
    assert len(result) >= 8  # We added 8 log entries


@pytest.mark.asyncio
async def test_query_logs_filters_by_request_id(temp_db):
    """Test that query_logs correctly filters by request_id."""
    result = mcp_tools.query_logs(request_id="req-001")

    assert isinstance(result, list)
    assert len(result) == 3
    # Verify all entries have the correct request_id
    assert all(entry.request_id == "req-001" for entry in result)


@pytest.mark.asyncio
async def test_query_logs_filters_by_level(temp_db):
    """Test that query_logs correctly filters by level."""
    result = mcp_tools.query_logs(level="ERROR")

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(entry.level == "ERROR" for entry in result)


@pytest.mark.asyncio
async def test_query_logs_filters_by_source(temp_db):
    """Test that query_logs correctly filters by source."""
    result = mcp_tools.query_logs(source="auth")

    assert isinstance(result, list)
    assert len(result) >= 2
    assert all(entry.source == "auth" for entry in result)


@pytest.mark.asyncio
async def test_query_logs_respects_limit(temp_db):
    """Test that query_logs respects the limit parameter."""
    result = mcp_tools.query_logs(limit=3)

    assert isinstance(result, list)
    assert len(result) <= 3


@pytest.mark.asyncio
async def test_get_request_trace_returns_markdown(temp_db):
    """Test that get_request_trace returns markdown-formatted trace."""
    result = mcp_tools.get_request_trace("req-001")

    assert isinstance(result, str)
    assert "Request Trace: req-001" in result
    assert "Duration:" in result
    assert "Events:" in result
    # Should include error indicator
    assert "❌" in result or "ERROR" in result


@pytest.mark.asyncio
async def test_get_request_trace_nonexistent_request(temp_db):
    """Test that get_request_trace handles nonexistent request_id."""
    result = mcp_tools.get_request_trace("req-nonexistent")

    assert isinstance(result, str)
    assert "No logs found" in result


@pytest.mark.asyncio
async def test_summarize_logs_returns_markdown(temp_db):
    """Test that summarize_logs returns markdown summary."""
    result = mcp_tools.summarize_logs()

    assert isinstance(result, str)
    assert "Log Summary" in result
    assert "Time Range:" in result
    assert "Total Events:" in result
    assert "Events by Level" in result
    assert "Events by Source" in result


@pytest.mark.asyncio
async def test_summarize_logs_filters_by_request_id(temp_db):
    """Test that summarize_logs correctly filters by request_id."""
    result = mcp_tools.summarize_logs(request_id="req-002")

    assert isinstance(result, str)
    assert "Log Summary" in result
    # Should only include the 3 events from req-002 (markdown formatted)
    assert "**Total Events:** 3" in result


@pytest.mark.asyncio
async def test_summarize_logs_no_results(temp_db):
    """Test that summarize_logs handles no results gracefully."""
    result = mcp_tools.summarize_logs(request_id="req-nonexistent")

    assert isinstance(result, str)
    assert "No logs found" in result


@pytest.mark.asyncio
async def test_mark_session_returns_confirmation(temp_db):
    """Test that mark_session returns confirmation message."""
    result = mcp_tools.mark_session(session_id="session-123")

    assert isinstance(result, str)
    assert "session-123" in result
    assert "marked" in result.lower()


@pytest.mark.asyncio
async def test_configure_logger_updates_settings(temp_db):
    """Test that configure function updates logger configuration."""
    new_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_f:
            new_path = temp_f.name

        # Use the core configure function, not the MCP tool
        configure(db_path=new_path, flush_interval=2.0, force=True)

        # Verify logger was configured
        logger = Logger()
        logger.log("INFO", "test message")
        logger.flush()
        await asyncio.sleep(0.2)

        # Query to verify the message was written to new DB
        results = logger.query(limit=1)
        assert len(results) >= 1
    finally:
        # Cleanup
        if new_path:
            Path(new_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_query_logs_with_time_range(temp_db):
    """Test that query_logs works with time_range parameter."""
    # Query logs from last 5 minutes
    result = mcp_tools.query_logs(time_range="5m")

    assert isinstance(result, list)
    # Should include all recently added logs
    assert len(result) >= 8


@pytest.mark.asyncio
async def test_query_logs_combines_multiple_filters(temp_db):
    """Test that query_logs correctly combines multiple filters."""
    result = mcp_tools.query_logs(request_id="req-001", level="ERROR")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].request_id == "req-001"
    assert result[0].level == "ERROR"


@pytest.mark.asyncio
async def test_query_logs_returns_correct_structure(temp_db):
    """Test that query_logs returns entries with correct structure."""
    result = mcp_tools.query_logs(limit=1)

    assert len(result) >= 1
    entry = result[0]

    # Verify all expected attributes are present
    assert hasattr(entry, "timestamp")
    assert hasattr(entry, "level")
    assert hasattr(entry, "message")
    assert hasattr(entry, "source")
    assert hasattr(entry, "request_id")
    assert hasattr(entry, "session_id")
    assert hasattr(entry, "correlation_id")
    assert hasattr(entry, "metadata")


@pytest.mark.asyncio
async def test_get_request_trace_includes_all_log_levels(temp_db):
    """Test that get_request_trace includes emoji indicators for all levels."""
    result = mcp_tools.get_request_trace("req-002")

    # req-002 has INFO and WARNING entries
    assert "ℹ️" in result or "INFO" in result
    assert "⚠️" in result or "WARNING" in result
