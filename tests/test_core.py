# ABOUTME: Unit tests for core Logger singleton
# ABOUTME: Tests singleton pattern, async writes, context enrichment, and shutdown

"""Tests for mc_logger.core."""

import os
import tempfile
import time

import pytest

from mc_logger.context import clear_context, set_request_id, set_session_id
from mc_logger.core import Logger, get_logger


@pytest.fixture
def temp_logger():
    """Create a logger with temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    logger = Logger()
    logger.configure(db_path=path, flush_interval=0.1, force=True)

    yield logger

    logger.shutdown()
    clear_context()

    if os.path.exists(path):
        os.remove(path)


def test_singleton_pattern():
    """Test that Logger follows singleton pattern."""
    logger1 = Logger()
    logger2 = Logger()

    assert logger1 is logger2


def test_get_logger():
    """Test get_logger() helper function."""
    logger = get_logger()

    assert isinstance(logger, Logger)
    assert logger is get_logger()  # Should return same instance


def test_basic_logging(temp_logger):
    """Test basic log message."""
    temp_logger.log("INFO", "Test message")

    # Give worker time to flush
    time.sleep(0.2)

    entries = temp_logger.query(limit=10)
    assert len(entries) >= 1
    assert any(e.message == "Test message" for e in entries)


def test_context_enrichment(temp_logger):
    """Test that context variables are enriched in log entries."""
    clear_context()
    req_token = set_request_id("req123")
    sess_token = set_session_id("sess456")

    temp_logger.log("INFO", "Test with context")

    time.sleep(0.2)

    entries = temp_logger.query(request_id="req123")
    assert len(entries) >= 1
    assert entries[0].request_id == "req123"
    assert entries[0].session_id == "sess456"


def test_log_with_metadata(temp_logger):
    """Test logging with metadata."""
    temp_logger.log(
        "INFO",
        "Test message",
        metadata={"key": "value", "count": 42},
    )

    time.sleep(0.2)

    entries = temp_logger.query(limit=10)
    assert len(entries) >= 1
    entry = next(e for e in entries if e.message == "Test message")
    assert entry.metadata == {"key": "value", "count": 42}


def test_log_with_confidence(temp_logger):
    """Test logging with confidence score."""
    temp_logger.log(
        "INFO",
        "Confident prediction",
        confidence=0.95,
    )

    time.sleep(0.2)

    entries = temp_logger.query(limit=10)
    assert len(entries) >= 1
    entry = next(e for e in entries if e.message == "Confident prediction")
    assert entry.confidence == 0.95


def test_log_with_source(temp_logger):
    """Test logging with custom source."""
    temp_logger.log("INFO", "API message", source="api")
    temp_logger.log("INFO", "Worker message", source="worker")

    time.sleep(0.2)

    api_entries = temp_logger.query(source="api")
    worker_entries = temp_logger.query(source="worker")

    assert len(api_entries) >= 1
    assert len(worker_entries) >= 1


def test_async_writes(temp_logger):
    """Test that writes are async (don't block)."""
    start = time.time()

    # Log many messages
    for i in range(100):
        temp_logger.log("INFO", f"Message {i}")

    duration = time.time() - start

    # Should complete very quickly (< 100ms) if async
    assert duration < 0.1


def test_flush(temp_logger):
    """Test manual flush."""
    temp_logger.log("INFO", "Test flush")

    # Flush immediately instead of waiting
    temp_logger.flush()

    entries = temp_logger.query(limit=10)
    assert len(entries) >= 1
    assert any(e.message == "Test flush" for e in entries)


def test_auto_configuration():
    """Test that logger auto-configures on first use."""
    logger = Logger()

    # Should auto-configure when logging
    logger.log("INFO", "Test auto-config")

    assert logger._configured


def test_level_uppercasing(temp_logger):
    """Test that log levels are uppercased."""
    temp_logger.log("info", "Test message")

    temp_logger.flush()

    entries = temp_logger.query(limit=10)
    entry = next(e for e in entries if e.message == "Test message")
    assert entry.level == "INFO"


def test_query_filters(temp_logger):
    """Test query with various filters."""
    clear_context()
    set_request_id("req1")
    temp_logger.log("INFO", "Message 1")

    clear_context()
    set_request_id("req2")
    temp_logger.log("ERROR", "Message 2")

    temp_logger.flush()

    # Query by level
    info_entries = temp_logger.query(level="INFO")
    error_entries = temp_logger.query(level="ERROR")

    assert len(info_entries) >= 1
    assert len(error_entries) >= 1

    # Query by request_id
    req1_entries = temp_logger.query(request_id="req1")
    assert len(req1_entries) >= 1
    assert all(e.request_id == "req1" for e in req1_entries)
