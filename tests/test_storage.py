# ABOUTME: Unit tests for SQLite storage backend
# ABOUTME: Tests database initialization, writes, queries, and concurrency

"""Tests for mc_logger.storage."""

import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from mc_logger.models import LogEntry
from mc_logger.storage import SQLiteStorage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    storage = SQLiteStorage(path)

    yield storage

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


def test_storage_initialization(temp_db):
    """Test that storage initializes correctly."""
    assert os.path.exists(temp_db.db_path)
    assert temp_db.count() == 0


def test_single_write(temp_db):
    """Test writing a single log entry."""
    entry = LogEntry.create(level="INFO", message="Test message")
    temp_db.write(entry)

    assert temp_db.count() == 1


def test_batch_write(temp_db):
    """Test writing multiple entries in a batch."""
    entries = [
        LogEntry.create(level="INFO", message=f"Message {i}") for i in range(10)
    ]

    temp_db.write_batch(entries)

    assert temp_db.count() == 10


def test_query_all(temp_db):
    """Test querying all entries."""
    entries = [
        LogEntry.create(level="INFO", message=f"Message {i}") for i in range(5)
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(limit=100)

    assert len(results) == 5


def test_query_by_level(temp_db):
    """Test querying by log level."""
    entries = [
        LogEntry.create(level="INFO", message="Info message"),
        LogEntry.create(level="ERROR", message="Error message"),
        LogEntry.create(level="INFO", message="Another info"),
    ]
    temp_db.write_batch(entries)

    info_results = temp_db.query(level="INFO")
    error_results = temp_db.query(level="ERROR")

    assert len(info_results) == 2
    assert len(error_results) == 1


def test_query_by_request_id(temp_db):
    """Test querying by request_id."""
    entries = [
        LogEntry.create(level="INFO", message="Msg 1", request_id="req1"),
        LogEntry.create(level="INFO", message="Msg 2", request_id="req2"),
        LogEntry.create(level="INFO", message="Msg 3", request_id="req1"),
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(request_id="req1")

    assert len(results) == 2
    assert all(e.request_id == "req1" for e in results)


def test_query_by_session_id(temp_db):
    """Test querying by session_id."""
    entries = [
        LogEntry.create(level="INFO", message="Msg 1", session_id="sess1"),
        LogEntry.create(level="INFO", message="Msg 2", session_id="sess2"),
        LogEntry.create(level="INFO", message="Msg 3", session_id="sess1"),
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(session_id="sess1")

    assert len(results) == 2
    assert all(e.session_id == "sess1" for e in results)


def test_query_by_source(temp_db):
    """Test querying by source."""
    entries = [
        LogEntry.create(level="INFO", message="Msg 1", source="api"),
        LogEntry.create(level="INFO", message="Msg 2", source="worker"),
        LogEntry.create(level="INFO", message="Msg 3", source="api"),
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(source="api")

    assert len(results) == 2
    assert all(e.source == "api" for e in results)


def test_query_time_range(temp_db):
    """Test querying by time range."""
    now = time.time()

    entries = [
        LogEntry(
            timestamp=now - 100,
            level="INFO",
            message="Old message",
            source="test",
        ),
        LogEntry(
            timestamp=now - 50,
            level="INFO",
            message="Recent message",
            source="test",
        ),
        LogEntry(
            timestamp=now,
            level="INFO",
            message="Current message",
            source="test",
        ),
    ]
    temp_db.write_batch(entries)

    # Query last 60 seconds
    results = temp_db.query(start_time=now - 60, end_time=now + 1)

    assert len(results) == 2
    assert all(e.timestamp >= now - 60 for e in results)


def test_query_limit(temp_db):
    """Test query limit parameter."""
    entries = [
        LogEntry.create(level="INFO", message=f"Message {i}") for i in range(20)
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(limit=5)

    assert len(results) == 5


def test_query_multiple_filters(temp_db):
    """Test querying with multiple filters."""
    now = time.time()

    entries = [
        LogEntry(
            timestamp=now,
            level="INFO",
            message="Match",
            source="api",
            request_id="req1",
        ),
        LogEntry(
            timestamp=now,
            level="ERROR",
            message="No match - level",
            source="api",
            request_id="req1",
        ),
        LogEntry(
            timestamp=now,
            level="INFO",
            message="No match - source",
            source="worker",
            request_id="req1",
        ),
        LogEntry(
            timestamp=now,
            level="INFO",
            message="No match - request",
            source="api",
            request_id="req2",
        ),
    ]
    temp_db.write_batch(entries)

    results = temp_db.query(level="INFO", source="api", request_id="req1")

    assert len(results) == 1
    assert results[0].message == "Match"


def test_clear(temp_db):
    """Test clearing all entries."""
    entries = [
        LogEntry.create(level="INFO", message=f"Message {i}") for i in range(5)
    ]
    temp_db.write_batch(entries)

    assert temp_db.count() == 5

    temp_db.clear()

    assert temp_db.count() == 0


def test_concurrent_writes(temp_db):
    """Test thread-safe concurrent writes."""

    def write_entries(start_idx):
        entries = [
            LogEntry.create(level="INFO", message=f"Message {start_idx + i}")
            for i in range(10)
        ]
        temp_db.write_batch(entries)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(write_entries, i * 10) for i in range(5)]
        for future in futures:
            future.result()

    assert temp_db.count() == 50


def test_metadata_serialization(temp_db):
    """Test that metadata is properly serialized and deserialized."""
    entry = LogEntry.create(
        level="INFO",
        message="Test",
        metadata={"key": "value", "count": 42, "flag": True},
    )
    temp_db.write(entry)

    results = temp_db.query(limit=1)

    assert len(results) == 1
    assert results[0].metadata == {"key": "value", "count": 42, "flag": True}
