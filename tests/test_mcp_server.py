"""Tests for MCP server implementation.

Tests tool registration, schemas, and basic functionality.
Requires fastmcp to be installed (skip tests otherwise).
"""

import pytest

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp")

from mc_logger.mcp import create_server, mcp


def test_create_server_returns_fastmcp_instance():
    """Test that create_server() returns a FastMCP instance."""
    server = create_server()
    assert server is not None
    assert hasattr(server, "tool")
    assert hasattr(server, "resource")
    assert hasattr(server, "prompt")


def test_mcp_server_has_query_logs_tool():
    """Test that query_logs tool is registered."""
    assert "query_logs" in mcp._tool_manager._tools


def test_mcp_server_has_get_request_trace_tool():
    """Test that get_request_trace tool is registered."""
    assert "get_request_trace" in mcp._tool_manager._tools


def test_mcp_server_has_summarize_logs_tool():
    """Test that summarize_logs tool is registered."""
    assert "summarize_logs" in mcp._tool_manager._tools


def test_mcp_server_has_mark_session_tool():
    """Test that mark_session tool is registered."""
    assert "mark_session" in mcp._tool_manager._tools


def test_mcp_server_has_configure_logger_tool():
    """Test that configure_logger tool is registered."""
    assert "configure_logger" in mcp._tool_manager._tools


def test_query_logs_tool_has_correct_parameters():
    """Test that query_logs tool has expected parameters."""
    query_logs_tool = mcp._tool_manager._tools["query_logs"]

    # Get the function signature
    import inspect
    sig = inspect.signature(query_logs_tool.fn)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    assert "time_range" in params
    assert "request_id" in params
    assert "session_id" in params
    assert "level" in params
    assert "source" in params
    assert "limit" in params


def test_get_request_trace_tool_has_correct_parameters():
    """Test that get_request_trace tool has expected parameters."""
    tool = mcp._tool_manager._tools["get_request_trace"]

    import inspect
    sig = inspect.signature(tool.fn)
    params = list(sig.parameters.keys())

    assert "request_id" in params


def test_configure_logger_tool_has_correct_parameters():
    """Test that configure_logger tool has expected parameters."""
    tool = mcp._tool_manager._tools["configure_logger"]

    import inspect
    sig = inspect.signature(tool.fn)
    params = list(sig.parameters.keys())

    assert "db_path" in params
    assert "flush_interval" in params
