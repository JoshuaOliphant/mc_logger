# ABOUTME: Data models for MC Logger - defines LogEntry structure
# ABOUTME: Provides serialization and deserialization for log entries

"""Data models for MC Logger."""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class LogEntry:
    """Represents a single log entry with metadata for AI-assisted debugging."""

    timestamp: float
    level: str
    message: str
    source: str = "app"
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        level: str,
        message: str,
        source: str = "app",
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "LogEntry":
        """Factory method to create a LogEntry with auto-timestamp and uppercased level."""
        return cls(
            timestamp=time.time(),
            level=level.upper(),
            message=message,
            source=source,
            request_id=request_id,
            session_id=session_id,
            correlation_id=correlation_id,
            confidence=confidence,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert LogEntry to dictionary."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert LogEntry to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        """Create LogEntry from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            level=data["level"],
            message=data["message"],
            source=data.get("source", "app"),
            request_id=data.get("request_id"),
            session_id=data.get("session_id"),
            correlation_id=data.get("correlation_id"),
            confidence=data.get("confidence"),
            metadata=data.get("metadata", {}),
        )
