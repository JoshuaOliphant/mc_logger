# ABOUTME: SQLite storage backend with WAL mode for concurrent access
# ABOUTME: Provides efficient log storage with batch writes and flexible querying

"""SQLite storage backend for MC Logger."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from mc_logger.models import LogEntry


class SQLiteStorage:
    """Thread-safe SQLite storage for log entries with WAL mode."""

    def __init__(self, db_path: str = "mc_logger.db"):
        """Initialize SQLite storage with WAL mode enabled."""
        self.db_path = db_path
        self._lock = Lock()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create database schema with indices."""
        with self._get_connection() as conn:
            # Enable WAL mode for concurrent access
            conn.execute("PRAGMA journal_mode=WAL")

            # Create logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    request_id TEXT,
                    session_id TEXT,
                    correlation_id TEXT,
                    confidence REAL,
                    metadata TEXT
                )
            """)

            # Create indices for efficient queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_request_id ON logs(request_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_id ON logs(session_id)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_level ON logs(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON logs(source)")

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with timeout."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def write(self, entry: LogEntry) -> None:
        """Write a single log entry to the database."""
        self.write_batch([entry])

    def write_batch(self, entries: List[LogEntry]) -> None:
        """Write multiple log entries to the database with thread safety."""
        with self._lock:
            with self._get_connection() as conn:
                conn.executemany(
                    """
                    INSERT INTO logs (
                        timestamp, level, message, source,
                        request_id, session_id, correlation_id,
                        confidence, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            entry.timestamp,
                            entry.level,
                            entry.message,
                            entry.source,
                            entry.request_id,
                            entry.session_id,
                            entry.correlation_id,
                            entry.confidence,
                            json.dumps(entry.metadata),
                        )
                        for entry in entries
                    ],
                )
                conn.commit()

    def query(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 1000,
    ) -> List[LogEntry]:
        """Query log entries with filters."""
        conditions = []
        params = []

        if start_time is not None:
            conditions.append("timestamp >= ?")
            params.append(start_time)

        if end_time is not None:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        if request_id is not None:
            conditions.append("request_id = ?")
            params.append(request_id)

        if session_id is not None:
            conditions.append("session_id = ?")
            params.append(session_id)

        if level is not None:
            conditions.append("level = ?")
            params.append(level.upper())

        if source is not None:
            conditions.append("source = ?")
            params.append(source)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        entries = []
        for row in rows:
            entries.append(
                LogEntry(
                    timestamp=row["timestamp"],
                    level=row["level"],
                    message=row["message"],
                    source=row["source"],
                    request_id=row["request_id"],
                    session_id=row["session_id"],
                    correlation_id=row["correlation_id"],
                    confidence=row["confidence"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
            )

        return entries

    def count(self) -> int:
        """Return total number of log entries."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            return cursor.fetchone()[0]

    def clear(self) -> None:
        """Delete all log entries."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM logs")
                conn.commit()
