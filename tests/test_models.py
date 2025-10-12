# ABOUTME: Unit tests for LogEntry data model
# ABOUTME: Tests creation, serialization, and edge cases

"""Tests for mc_logger.models."""

import json
from datetime import datetime

import pytest

from mc_logger.models import LogEntry


def test_log_entry_creation():
    """Test basic LogEntry creation."""
    entry = LogEntry.create(
        level="info",
        message="Test message",
        source="test",
    )

    assert entry.level == "INFO"  # Should be uppercased
    assert entry.message == "Test message"
    assert entry.source == "test"
    assert isinstance(entry.timestamp, float)
    assert entry.timestamp > 0


def test_log_entry_with_all_fields():
    """Test LogEntry with all optional fields."""
    entry = LogEntry.create(
        level="error",
        message="Test error",
        source="api",
        request_id="req123",
        session_id="sess456",
        correlation_id="corr789",
        confidence=0.95,
        metadata={"key": "value", "count": 42},
    )

    assert entry.level == "ERROR"
    assert entry.message == "Test error"
    assert entry.source == "api"
    assert entry.request_id == "req123"
    assert entry.session_id == "sess456"
    assert entry.correlation_id == "corr789"
    assert entry.confidence == 0.95
    assert entry.metadata == {"key": "value", "count": 42}


def test_log_entry_none_values():
    """Test LogEntry with None values for optional fields."""
    entry = LogEntry.create(
        level="info",
        message="Test",
    )

    assert entry.request_id is None
    assert entry.session_id is None
    assert entry.correlation_id is None
    assert entry.confidence is None
    assert entry.metadata == {}


def test_log_entry_empty_metadata():
    """Test LogEntry with empty metadata."""
    entry = LogEntry.create(
        level="info",
        message="Test",
        metadata={},
    )

    assert entry.metadata == {}


def test_log_entry_to_dict():
    """Test LogEntry serialization to dictionary."""
    entry = LogEntry.create(
        level="info",
        message="Test",
        source="test",
        request_id="req123",
        metadata={"key": "value"},
    )

    data = entry.to_dict()

    assert isinstance(data, dict)
    assert data["level"] == "INFO"
    assert data["message"] == "Test"
    assert data["source"] == "test"
    assert data["request_id"] == "req123"
    assert data["metadata"] == {"key": "value"}
    assert "timestamp" in data


def test_log_entry_to_json():
    """Test LogEntry serialization to JSON."""
    entry = LogEntry.create(
        level="info",
        message="Test",
        source="test",
    )

    json_str = entry.to_json()

    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["level"] == "INFO"
    assert data["message"] == "Test"


def test_log_entry_from_dict():
    """Test LogEntry deserialization from dictionary."""
    data = {
        "timestamp": 1234567890.0,
        "level": "INFO",
        "message": "Test",
        "source": "test",
        "request_id": "req123",
        "session_id": "sess456",
        "correlation_id": "corr789",
        "confidence": 0.95,
        "metadata": {"key": "value"},
    }

    entry = LogEntry.from_dict(data)

    assert entry.timestamp == 1234567890.0
    assert entry.level == "INFO"
    assert entry.message == "Test"
    assert entry.source == "test"
    assert entry.request_id == "req123"
    assert entry.session_id == "sess456"
    assert entry.correlation_id == "corr789"
    assert entry.confidence == 0.95
    assert entry.metadata == {"key": "value"}


def test_log_entry_json_round_trip():
    """Test JSON serialization and deserialization round trip."""
    original = LogEntry.create(
        level="warning",
        message="Test warning",
        source="api",
        request_id="req123",
        metadata={"count": 42, "flag": True},
    )

    # Convert to JSON and back
    json_str = original.to_json()
    data = json.loads(json_str)
    restored = LogEntry.from_dict(data)

    assert restored.level == original.level
    assert restored.message == original.message
    assert restored.source == original.source
    assert restored.request_id == original.request_id
    assert restored.metadata == original.metadata


def test_log_entry_level_uppercasing():
    """Test that log levels are uppercased."""
    for level in ["debug", "info", "warning", "error"]:
        entry = LogEntry.create(level=level, message="Test")
        assert entry.level == level.upper()
