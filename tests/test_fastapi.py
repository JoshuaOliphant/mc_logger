# ABOUTME: Unit tests for FastAPI middleware
# ABOUTME: Tests automatic logging, error capture, and header redaction

"""Tests for mc_logger.middleware."""

import os
import tempfile

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from mc_logger.core import Logger
from mc_logger.middleware import instrument_fastapi


@pytest.fixture
async def test_app():
    """Create a test FastAPI app with MC Logger."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = FastAPI()
    logger = Logger()
    logger.configure(db_path=db_path, flush_interval=0.1, force=True)

    instrument_fastapi(app, logger=logger)

    @app.get("/")
    async def root():
        return {"message": "Hello"}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"id": user_id, "name": "Test User"}

    @app.get("/error")
    async def trigger_error():
        raise ValueError("Test error")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    yield app, logger

    logger.shutdown()

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_basic_request_logging(test_app):
    """Test that requests are automatically logged."""
    import asyncio

    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    # Give the async queue time to process
    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(limit=100)

    # Should have request.start and request.complete
    messages = [e.message for e in entries]
    assert "request.start" in messages
    assert "request.complete" in messages


@pytest.mark.asyncio
async def test_request_correlation(test_app):
    """Test that all logs for a request share the same request_id."""
    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    logger.flush()

    entries = logger.query(limit=100)

    # Get request_id from first entry
    request_entries = [e for e in entries if e.request_id]
    if request_entries:
        request_id = request_entries[0].request_id

        # All entries with request_id should have the same one
        for entry in request_entries:
            assert entry.request_id == request_id


@pytest.mark.asyncio
async def test_error_capture(test_app):
    """Test that errors are captured with traceback."""
    import asyncio

    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with pytest.raises(Exception):
            await client.get("/error")

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(level="ERROR")

    assert len(entries) >= 1
    error_entry = entries[0]
    assert error_entry.message == "request.error"
    assert "error_type" in error_entry.metadata
    assert error_entry.metadata["error_type"] == "ValueError"
    assert "traceback" in error_entry.metadata


@pytest.mark.asyncio
async def test_request_metadata(test_app):
    """Test that request metadata is captured."""
    import asyncio

    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/42?filter=active")

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(limit=100)
    start_entries = [e for e in entries if e.message == "request.start"]

    assert len(start_entries) >= 1
    entry = start_entries[0]

    assert "method" in entry.metadata
    assert entry.metadata["method"] == "GET"
    assert "path" in entry.metadata
    assert "/users/42" in entry.metadata["path"]
    assert "query_params" in entry.metadata


@pytest.mark.asyncio
async def test_response_metadata(test_app):
    """Test that response metadata is captured."""
    import asyncio

    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(limit=100)
    complete_entries = [e for e in entries if e.message == "request.complete"]

    assert len(complete_entries) >= 1
    entry = complete_entries[0]

    assert "status_code" in entry.metadata
    assert entry.metadata["status_code"] == 200
    assert "duration_ms" in entry.metadata
    assert isinstance(entry.metadata["duration_ms"], float)


@pytest.mark.asyncio
async def test_slow_request_flag(test_app):
    """Test that slow requests are flagged."""
    import asyncio

    app, logger = test_app

    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(1.1)  # Longer than 1000ms threshold
        return {"message": "slow"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/slow")

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(limit=100)
    complete_entries = [e for e in entries if e.message == "request.complete"]

    assert len(complete_entries) >= 1
    entry = complete_entries[0]

    assert "slow_request" in entry.metadata
    assert entry.metadata["slow_request"] is True


@pytest.mark.asyncio
async def test_header_redaction(test_app):
    """Test that sensitive headers are redacted."""
    import asyncio

    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/",
            headers={
                "Authorization": "Bearer secret-token",
                "X-API-Key": "secret-key",
                "Cookie": "session=secret",
                "X-Custom-Header": "public-value",
            },
        )

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(limit=100)
    start_entries = [e for e in entries if e.message == "request.start"]

    assert len(start_entries) >= 1
    entry = start_entries[0]

    headers = entry.metadata.get("headers", {})

    # Sensitive headers should be redacted
    assert headers.get("authorization") == "[REDACTED]"
    assert headers.get("x-api-key") == "[REDACTED]"
    assert headers.get("cookie") == "[REDACTED]"

    # Non-sensitive headers should be preserved
    assert headers.get("x-custom-header") == "public-value"


@pytest.mark.asyncio
async def test_exclude_paths(test_app):
    """Test that excluded paths are not logged."""
    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Health endpoint should be excluded by default
        response = await client.get("/health")

    logger.flush()

    entries = logger.query(limit=100)

    # Should not have logs for /health endpoint
    messages = [e.message for e in entries]
    # If there are any entries, they shouldn't be about /health
    for entry in entries:
        if "path" in entry.metadata:
            assert "/health" not in entry.metadata["path"]


@pytest.mark.asyncio
async def test_request_id_header(test_app):
    """Test that request_id can be provided via header."""
    import asyncio

    app, logger = test_app

    custom_request_id = "custom-req-123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Request-ID": custom_request_id})

    await asyncio.sleep(0.2)
    logger.flush()

    entries = logger.query(request_id=custom_request_id)

    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_response_includes_request_id(test_app):
    """Test that response includes X-Request-ID header."""
    app, logger = test_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    # Response should include X-Request-ID header
    assert "x-request-id" in response.headers
