# ABOUTME: Unit tests for async-safe context management
# ABOUTME: Tests context isolation, auto-generation, and token reset

"""Tests for mc_logger.context."""

import asyncio

import pytest

from mc_logger.context import (
    clear_context,
    generate_id,
    get_correlation_id,
    get_request_id,
    get_session_id,
    reset_correlation_id,
    reset_request_id,
    reset_session_id,
    set_correlation_id,
    set_request_id,
    set_session_id,
)


def test_generate_id():
    """Test ID generation."""
    id1 = generate_id()
    id2 = generate_id()

    assert isinstance(id1, str)
    assert len(id1) == 8
    assert id1 != id2  # Should be unique


def test_request_id_auto_generation():
    """Test that request_id is auto-generated if not provided."""
    clear_context()
    token = set_request_id()
    request_id = get_request_id()

    assert request_id is not None
    assert isinstance(request_id, str)
    assert len(request_id) == 8

    reset_request_id(token)


def test_request_id_explicit_value():
    """Test setting explicit request_id."""
    clear_context()
    token = set_request_id("custom123")
    request_id = get_request_id()

    assert request_id == "custom123"

    reset_request_id(token)


def test_request_id_isolation():
    """Test that request_id is isolated between contexts."""
    clear_context()

    token1 = set_request_id("req1")
    assert get_request_id() == "req1"

    token2 = set_request_id("req2")
    assert get_request_id() == "req2"

    reset_request_id(token2)
    assert get_request_id() == "req1"

    reset_request_id(token1)
    assert get_request_id() is None


def test_session_id_auto_generation():
    """Test that session_id is auto-generated if not provided."""
    clear_context()
    token = set_session_id()
    session_id = get_session_id()

    assert session_id is not None
    assert isinstance(session_id, str)
    assert len(session_id) == 8

    reset_session_id(token)


def test_session_id_explicit_value():
    """Test setting explicit session_id."""
    clear_context()
    token = set_session_id("sess456")
    session_id = get_session_id()

    assert session_id == "sess456"

    reset_session_id(token)


def test_correlation_id_auto_generation():
    """Test that correlation_id is auto-generated if not provided."""
    clear_context()
    token = set_correlation_id()
    correlation_id = get_correlation_id()

    assert correlation_id is not None
    assert isinstance(correlation_id, str)
    assert len(correlation_id) == 8

    reset_correlation_id(token)


def test_correlation_id_explicit_value():
    """Test setting explicit correlation_id."""
    clear_context()
    token = set_correlation_id("corr789")
    correlation_id = get_correlation_id()

    assert correlation_id == "corr789"

    reset_correlation_id(token)


def test_clear_context():
    """Test clearing all context variables."""
    set_request_id("req1")
    set_session_id("sess1")
    set_correlation_id("corr1")

    assert get_request_id() == "req1"
    assert get_session_id() == "sess1"
    assert get_correlation_id() == "corr1"

    clear_context()

    assert get_request_id() is None
    assert get_session_id() is None
    assert get_correlation_id() is None


@pytest.mark.asyncio
async def test_async_context_isolation():
    """Test that context is isolated between async tasks."""
    clear_context()
    results = []

    async def task(task_id: str):
        token = set_request_id(task_id)
        await asyncio.sleep(0.01)  # Simulate async work
        results.append((task_id, get_request_id()))
        reset_request_id(token)

    # Run multiple tasks concurrently
    await asyncio.gather(
        task("task1"),
        task("task2"),
        task("task3"),
    )

    # Each task should see its own request_id
    assert len(results) == 3
    for task_id, request_id in results:
        assert task_id == request_id


@pytest.mark.asyncio
async def test_async_nested_contexts():
    """Test nested async contexts."""
    clear_context()

    token1 = set_request_id("outer")
    assert get_request_id() == "outer"

    async def inner_task():
        token2 = set_request_id("inner")
        assert get_request_id() == "inner"
        await asyncio.sleep(0.01)
        assert get_request_id() == "inner"
        reset_request_id(token2)
        assert get_request_id() == "outer"

    await inner_task()
    assert get_request_id() == "outer"

    reset_request_id(token1)
