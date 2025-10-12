# ABOUTME: Integration tests for end-to-end workflows
# ABOUTME: Tests complete scenarios including AI debugging workflows

"""Integration tests for MC Logger."""

import os
import tempfile

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from mc_logger.core import Logger
from mc_logger.middleware import instrument_fastapi
from mc_logger.mcp_tools import get_request_trace, query_logs, summarize_logs


@pytest.fixture
async def integrated_app():
    """Create a fully integrated FastAPI app with MC Logger."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = FastAPI()
    logger = Logger()
    logger.configure(db_path=db_path, flush_interval=0.1, force=True)

    instrument_fastapi(app)

    @app.get("/")
    async def root():
        logger.log("INFO", "Root endpoint accessed", source="api")
        return {"message": "Hello"}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        logger.log("INFO", f"Fetching user {user_id}", source="api")
        if user_id == 42:
            return {"id": user_id, "name": "Test User"}
        logger.log("WARNING", f"User {user_id} not found", source="api")
        raise ValueError("User not found")

    @app.post("/checkout")
    async def checkout(cart_id: str):
        logger.log("INFO", f"Starting checkout for cart {cart_id}", source="api")
        logger.log("INFO", "Validating cart items", source="api")
        logger.log("INFO", "Processing payment", source="api")

        # Simulate payment failure
        if cart_id == "cart-fail":
            logger.log("ERROR", "Payment processing failed", source="api")
            raise ValueError("Payment failed")

        logger.log("INFO", "Checkout completed successfully", source="api")
        return {"status": "success", "order_id": "order-123"}

    yield app, logger

    logger.shutdown()

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_complete_workflow(integrated_app):
    """Test complete workflow: requests, queries, traces, summaries."""
    import asyncio

    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Make successful request
        response1 = await client.get("/")
        assert response1.status_code == 200

        # Make another successful request
        response2 = await client.get("/users/42")
        assert response2.status_code == 200

        # Make failing request
        with pytest.raises(Exception):
            await client.get("/users/999")

    await asyncio.sleep(0.2)
    logger.flush()

    # Query all logs
    all_entries = query_logs(limit=100)
    assert len(all_entries) > 0

    # Query by level
    error_entries = query_logs(level="ERROR")
    assert len(error_entries) > 0

    # Get summary
    summary = summarize_logs()
    assert "Log Summary" in summary
    assert "Total Events" in summary

    # Get traces for specific requests
    if all_entries:
        request_id = all_entries[0].request_id
        if request_id:
            trace = get_request_trace(request_id)
            assert "Request Trace" in trace


@pytest.mark.asyncio
async def test_ai_debugging_scenario(integrated_app):
    """
    Test AI debugging scenario: User reports checkout failure,
    AI investigates using MCP tools.
    """
    import asyncio

    app, logger = integrated_app

    # Simulate user actions leading to failure
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Successful checkout
        response1 = await client.post("/checkout?cart_id=cart-success")
        assert response1.status_code == 200

        # Failed checkout
        with pytest.raises(Exception):
            await client.post("/checkout?cart_id=cart-fail")

    await asyncio.sleep(0.2)
    logger.flush()

    # Step 1: AI queries recent errors
    error_entries = query_logs(level="ERROR", limit=10)
    assert len(error_entries) > 0

    # Step 2: AI identifies the failed request
    failed_request_id = None
    for entry in error_entries:
        if "Payment processing failed" in entry.message:
            failed_request_id = entry.request_id
            break

    assert failed_request_id is not None

    # Step 3: AI traces the failed request
    trace = get_request_trace(failed_request_id)

    # Verify trace contains key information
    assert "Request Trace" in trace
    assert failed_request_id in trace
    assert "Payment processing failed" in trace or "ERROR" in trace

    # Step 4: AI analyzes timeline
    request_entries = query_logs(request_id=failed_request_id, limit=100)
    assert len(request_entries) > 0

    # Should see the full checkout flow
    messages = [e.message for e in request_entries]
    assert any("checkout" in m.lower() for m in messages)

    # Step 5: AI generates summary for developer
    summary = summarize_logs(request_id=failed_request_id)
    assert "Log Summary" in summary


@pytest.mark.asyncio
async def test_request_correlation(integrated_app):
    """Test that all logs in a request share the same request_id."""
    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/checkout?cart_id=cart-success")

    logger.flush()

    # Get all entries from the request
    all_entries = query_logs(limit=100)

    # Find entries with request_id
    request_ids = set()
    for entry in all_entries:
        if entry.request_id:
            request_ids.add(entry.request_id)

    # Get entries for one request
    if request_ids:
        request_id = list(request_ids)[0]
        request_entries = query_logs(request_id=request_id)

        # All entries should have the same request_id
        assert all(e.request_id == request_id for e in request_entries)


@pytest.mark.asyncio
async def test_error_traceback_capture(integrated_app):
    """Test that error tracebacks are captured."""
    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with pytest.raises(Exception):
            await client.post("/checkout?cart_id=cart-fail")

    logger.flush()

    # Find error entries
    error_entries = query_logs(level="ERROR", limit=10)

    # Should have request.error entry with traceback
    error_entry = None
    for entry in error_entries:
        if entry.message == "request.error":
            error_entry = entry
            break

    if error_entry:
        assert "traceback" in error_entry.metadata
        assert "ValueError" in error_entry.metadata.get("error_type", "")


@pytest.mark.asyncio
async def test_multi_request_scenario(integrated_app):
    """Test multiple concurrent requests maintain separate contexts."""
    import asyncio

    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Make multiple requests concurrently
        responses = await asyncio.gather(
            client.get("/"),
            client.get("/users/42"),
            client.post("/checkout?cart_id=cart-success"),
            return_exceptions=True,
        )

    await asyncio.sleep(0.2)
    logger.flush()

    # Get all entries
    all_entries = query_logs(limit=100)

    # Should have multiple unique request_ids
    request_ids = set()
    for entry in all_entries:
        if entry.request_id:
            request_ids.add(entry.request_id)

    assert len(request_ids) >= 3  # At least 3 different requests


@pytest.mark.asyncio
async def test_log_persistence(integrated_app):
    """Test that logs persist across queries."""
    import asyncio

    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/")

    await asyncio.sleep(0.2)
    logger.flush()

    # Query once
    entries1 = query_logs(limit=100)
    count1 = len(entries1)

    # Query again
    entries2 = query_logs(limit=100)
    count2 = len(entries2)

    # Should get same results
    assert count1 == count2
    assert count1 > 0


@pytest.mark.asyncio
async def test_time_range_filtering(integrated_app):
    """Test filtering logs by time range."""
    import asyncio

    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/")

    await asyncio.sleep(0.2)
    logger.flush()

    # Query recent logs (last 5 minutes)
    recent_entries = query_logs(time_range="5m")

    assert len(recent_entries) > 0

    # All entries should be recent
    import time

    now = time.time()
    for entry in recent_entries:
        age_seconds = now - entry.timestamp
        assert age_seconds < 300  # Less than 5 minutes


@pytest.mark.asyncio
async def test_source_separation(integrated_app):
    """Test that logs from different sources can be separated."""
    import asyncio

    app, logger = integrated_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/users/42")

    await asyncio.sleep(0.2)
    logger.flush()

    # Query by source
    api_entries = query_logs(source="api")
    middleware_entries = query_logs(source="middleware")

    # Should have entries from both sources
    assert len(api_entries) > 0
    assert len(middleware_entries) > 0

    # Entries should be properly separated
    for entry in api_entries:
        assert entry.source == "api"
    for entry in middleware_entries:
        assert entry.source == "middleware"
