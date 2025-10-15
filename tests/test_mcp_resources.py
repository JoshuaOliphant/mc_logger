"""Tests for MCP resources implementation.

Tests resource registration, URI patterns, and content generation.
Requires fastmcp to be installed (skip tests otherwise).
"""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp")

from mc_logger import Logger
from mc_logger.context import set_request_id
from mc_logger.mcp import mcp


@pytest.fixture
async def temp_db():
    """Create a temporary database with sample log entries."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # Configure logger, write initial data, and shut down to ensure flush
    logger = Logger()
    logger.configure(db_path=temp_path, flush_interval=0.1, force=True)
    set_request_id("test-request-123")
    logger.log("INFO", "Test log entry", source="test")
    logger.shutdown()

    # Re-configure the logger for the test to use
    logger.configure(db_path=temp_path, flush_interval=0.1, force=True)

    yield temp_path

    # Cleanup
    logger.shutdown()
    Path(temp_path).unlink(missing_ok=True)


def test_mcp_server_has_resources():
    """Test that resources are registered."""
    # Resources include both static resources and templates
    resources = list(mcp._resource_manager._resources.values())
    templates = list(mcp._resource_manager._templates.values())
    total_resources = resources + templates
    assert len(total_resources) >= 5


def test_logs_recent_resource_registered():
    """Test that logs://recent resource is registered."""
    resources = list(mcp._resource_manager._resources.values())
    resource_uris = [str(res.uri) for res in resources]
    assert "logs://recent" in resource_uris


def test_logs_request_resource_registered():
    """Test that logs://request/{request_id} resource is registered."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template_uris = [str(t.uri_template) for t in templates]
    assert "logs://request/{request_id}" in template_uris


def test_logs_session_resource_registered():
    """Test that logs://session/{session_id} resource is registered."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template_uris = [str(t.uri_template) for t in templates]
    assert "logs://session/{session_id}" in template_uris


def test_logs_errors_resource_registered():
    """Test that logs://errors resource is registered."""
    resources = list(mcp._resource_manager._resources.values())
    resource_uris = [str(res.uri) for res in resources]
    assert "logs://errors" in resource_uris


def test_logs_source_resource_registered():
    """Test that logs://source/{source} resource is registered."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template_uris = [str(t.uri_template) for t in templates]
    assert "logs://source/{source}" in template_uris


@pytest.mark.asyncio
async def test_recent_logs_resource_returns_json(temp_db):
    """Test that logs://recent resource returns valid JSON."""
    resources = list(mcp._resource_manager._resources.values())
    resource = next(res for res in resources if str(res.uri) == "logs://recent")

    # Call the resource function
    result = resource.fn()

    # Should return valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, list)


@pytest.mark.asyncio
async def test_error_logs_resource_returns_json(temp_db):
    """Test that logs://errors resource returns valid JSON."""
    resources = list(mcp._resource_manager._resources.values())
    resource = next(res for res in resources if str(res.uri) == "logs://errors")

    result = resource.fn()

    # Should return valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, list)


def test_request_resource_accepts_request_id():
    """Test that logs://request/{request_id} resource accepts request_id parameter."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template = next(
        t for t in templates if str(t.uri_template) == "logs://request/{request_id}"
    )

    # Check function signature
    import inspect
    sig = inspect.signature(template.fn)
    params = list(sig.parameters.keys())

    assert "request_id" in params


def test_session_resource_accepts_session_id():
    """Test that logs://session/{session_id} resource accepts session_id parameter."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template = next(
        t for t in templates if str(t.uri_template) == "logs://session/{session_id}"
    )

    import inspect
    sig = inspect.signature(template.fn)
    params = list(sig.parameters.keys())

    assert "session_id" in params


def test_source_resource_accepts_source():
    """Test that logs://source/{source} resource accepts source parameter."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template = next(
        t for t in templates if str(t.uri_template) == "logs://source/{source}"
    )

    import inspect
    sig = inspect.signature(template.fn)
    params = list(sig.parameters.keys())

    assert "source" in params


@pytest.mark.asyncio
async def test_request_resource_returns_json_with_test_id(temp_db):
    """Test that logs://request/{request_id} returns valid JSON with test request_id."""
    # Templates are stored separately from static resources
    templates = list(mcp._resource_manager._templates.values())
    template = next(
        t for t in templates if str(t.uri_template) == "logs://request/{request_id}"
    )

    result = template.fn(request_id="test-request-123")

    # Should return valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, list)
