# ABOUTME: Unit tests for MCP query tools
# ABOUTME: Tests time parsing, query filters, trace formatting, and summaries

"""Tests for mc_logger.mcp_tools."""

import os
import tempfile
import time

import pytest

from mc_logger.core import Logger
from mc_logger.mcp_tools import (
    get_request_trace,
    mark_session,
    parse_time_range,
    query_logs,
    summarize_logs,
)


@pytest.fixture
def temp_logger():
    """Create a logger with temporary database and sample data."""
    from mc_logger.context import set_request_id, clear_context

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    logger = Logger()
    logger.configure(db_path=path, flush_interval=0.1, force=True)

    # Add sample log entries with proper context
    clear_context()
    set_request_id("req1")
    logger.log("INFO", "Test message 1", source="api")
    logger.log("ERROR", "Test error", source="api")

    clear_context()
    set_request_id("req2")
    logger.log("INFO", "Test message 2", source="worker")
    logger.log("WARNING", "Test warning", source="api")

    clear_context()

    # Give worker thread time to process entries
    # flush_interval is 0.1s, so sleep slightly longer to ensure worker completes
    time.sleep(0.2)
    logger.flush()

    yield logger

    logger.shutdown()

    if os.path.exists(path):
        os.remove(path)


def test_parse_time_range_minutes():
    """Test parsing time range in minutes."""
    now = time.time()
    start, end = parse_time_range("5m")
    expected_start = now - (5 * 60)

    assert abs(start - expected_start) < 2  # Within 2 seconds
    assert abs(end - now) < 2


def test_parse_time_range_hours():
    """Test parsing time range in hours."""
    now = time.time()
    start, end = parse_time_range("2h")
    expected_start = now - (2 * 3600)

    assert abs(start - expected_start) < 2
    assert abs(end - now) < 2


def test_parse_time_range_days():
    """Test parsing time range in days."""
    now = time.time()
    start, end = parse_time_range("1d")
    expected_start = now - (1 * 86400)

    assert abs(start - expected_start) < 2
    assert abs(end - now) < 2


def test_parse_time_range_invalid():
    """Test that invalid time ranges raise errors."""
    with pytest.raises(ValueError):
        parse_time_range("invalid")

    with pytest.raises(ValueError):
        parse_time_range("5x")


def test_query_logs_all(temp_logger):
    """Test querying all logs."""
    entries = query_logs()

    assert len(entries) >= 4


def test_query_logs_by_level(temp_logger):
    """Test querying logs by level."""
    info_entries = query_logs(level="INFO")
    error_entries = query_logs(level="ERROR")

    assert len(info_entries) >= 2
    assert len(error_entries) >= 1


def test_query_logs_by_request_id(temp_logger):
    """Test querying logs by request_id."""
    entries = query_logs(request_id="req1")

    assert len(entries) >= 2
    assert all(e.request_id == "req1" for e in entries)


def test_query_logs_by_source(temp_logger):
    """Test querying logs by source."""
    api_entries = query_logs(source="api")
    worker_entries = query_logs(source="worker")

    assert len(api_entries) >= 3
    assert len(worker_entries) >= 1


def test_query_logs_by_time_range(temp_logger):
    """Test querying logs by time range."""
    entries = query_logs(time_range="5m")

    assert len(entries) >= 4  # All recent entries


def test_query_logs_with_limit(temp_logger):
    """Test querying logs with limit."""
    entries = query_logs(limit=2)

    assert len(entries) == 2


def test_get_request_trace(temp_logger):
    """Test getting request trace."""
    trace = get_request_trace("req1")

    assert isinstance(trace, str)
    assert "req1" in trace
    assert "Request Trace" in trace
    assert "Timeline" in trace
    assert "Duration" in trace
    assert "Events" in trace


def test_get_request_trace_includes_errors(temp_logger):
    """Test that request trace shows error count."""
    trace = get_request_trace("req1")

    assert "Errors" in trace or "❌" in trace


def test_get_request_trace_not_found(temp_logger):
    """Test request trace for non-existent request_id."""
    trace = get_request_trace("nonexistent")

    assert "No logs found" in trace


def test_get_request_trace_formatting(temp_logger):
    """Test that request trace includes emoji indicators."""
    trace = get_request_trace("req1")

    # Should have emoji indicators
    assert "ℹ️" in trace or "❌" in trace or "⚠️" in trace or "🔍" in trace


def test_mark_session(temp_logger):
    """Test marking a session."""
    result = mark_session("sess1")

    assert isinstance(result, str)
    assert "sess1" in result
    assert "marked" in result.lower()


def test_summarize_logs(temp_logger):
    """Test log summarization."""
    summary = summarize_logs()

    assert isinstance(summary, str)
    assert "Log Summary" in summary
    assert "Total Events" in summary
    assert "Events by Level" in summary
    assert "Events by Source" in summary


def test_summarize_logs_by_request_id(temp_logger):
    """Test summarizing logs for specific request."""
    summary = summarize_logs(request_id="req1")

    assert "Log Summary" in summary
    assert "Total Events" in summary


def test_summarize_logs_by_time_range(temp_logger):
    """Test summarizing logs by time range."""
    summary = summarize_logs(time_range="5m")

    assert "Log Summary" in summary
    assert "Time Range" in summary


def test_summarize_logs_no_results(temp_logger):
    """Test summarizing when no logs match."""
    summary = summarize_logs(request_id="nonexistent")

    assert "No logs found" in summary


def test_summarize_logs_includes_counts(temp_logger):
    """Test that summary includes count statistics."""
    summary = summarize_logs()

    # Should include level counts
    assert "INFO" in summary
    assert "ERROR" in summary or "WARNING" in summary

    # Should include source counts
    assert "api" in summary
    assert "worker" in summary
