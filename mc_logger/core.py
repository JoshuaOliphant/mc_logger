# ABOUTME: Core Logger singleton with async queue-based writes
# ABOUTME: Provides graceful shutdown and automatic context enrichment

"""Core Logger implementation for MC Logger."""

import atexit
import sys
import threading
import time
from queue import Empty, Full, Queue
from threading import Lock
from typing import Any, Dict, List, Optional

from mc_logger.context import get_correlation_id, get_request_id, get_session_id
from mc_logger.models import LogEntry
from mc_logger.storage import SQLiteStorage


class Logger:
    """Thread-safe singleton Logger with async queue-based writes."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Implement singleton pattern with double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Logger (only runs once due to singleton)."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._configured = False
        self._storage: Optional[SQLiteStorage] = None
        self._queue: Queue = Queue(maxsize=10000)
        self._worker_thread: Optional[threading.Thread] = None
        self._shutdown_flag = threading.Event()
        self._flush_interval = 1.0

        # Register shutdown handler
        atexit.register(self.shutdown)

    def configure(self, db_path: str = "mc_logger.db", flush_interval: float = 1.0, force: bool = False):
        """Configure the logger and start the worker thread."""
        with self._lock:
            if self._configured and not force:
                return

            # Shutdown existing configuration if forcing reconfiguration
            if force and self._configured:
                self._shutdown_flag.set()
                if self._worker_thread and self._worker_thread.is_alive():
                    self._worker_thread.join(timeout=1.0)
                self._shutdown_flag.clear()

            self._storage = SQLiteStorage(db_path)
            self._flush_interval = flush_interval
            self._configured = True

            # Start background worker thread
            self._worker_thread = threading.Thread(
                target=self._worker, daemon=True, name="mc_logger_worker"
            )
            self._worker_thread.start()

    def _worker(self):
        """Background worker that flushes queue periodically."""
        while not self._shutdown_flag.is_set():
            entries = []

            # Collect entries for batch write
            deadline = time.time() + self._flush_interval
            while time.time() < deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break

                try:
                    entry = self._queue.get(timeout=min(remaining, 0.1))
                    entries.append(entry)
                except Empty:
                    continue

            # Write collected entries
            if entries and self._storage:
                try:
                    self._storage.write_batch(entries)
                except Exception as e:
                    print(f"MC Logger: Failed to write batch: {e}", file=sys.stderr)

    def log(
        self,
        level: str,
        message: str,
        source: str = "app",
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a message with automatic context enrichment."""
        # Auto-configure on first use
        if not self._configured:
            self.configure()

        # Create entry with context enrichment
        entry = LogEntry.create(
            level=level,
            message=message,
            source=source,
            request_id=get_request_id(),
            session_id=get_session_id(),
            correlation_id=get_correlation_id(),
            confidence=confidence,
            metadata=metadata,
        )

        # Add to queue with overflow handling
        try:
            self._queue.put_nowait(entry)
        except Full:
            # Queue is full, drop oldest and retry
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(entry)
            except (Empty, Full):
                # Still can't add, log to stderr
                print(
                    f"MC Logger: Queue overflow, dropping log: {message}",
                    file=sys.stderr,
                )

    def flush(self):
        """Force immediate queue drain."""
        if not self._storage:
            return

        entries = []
        while not self._queue.empty():
            try:
                entries.append(self._queue.get_nowait())
            except Empty:
                break

        if entries:
            try:
                self._storage.write_batch(entries)
            except Exception as e:
                print(f"MC Logger: Failed to flush: {e}", file=sys.stderr)

    def shutdown(self):
        """Graceful shutdown with final flush."""
        if not self._configured:
            return

        # Signal worker to stop
        self._shutdown_flag.set()

        # Final flush
        self.flush()

        # Wait for worker thread
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)

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
        """Query logs from storage."""
        if not self._storage:
            self.configure()

        return self._storage.query(
            start_time=start_time,
            end_time=end_time,
            request_id=request_id,
            session_id=session_id,
            level=level,
            source=source,
            limit=limit,
        )


# Module-level helpers
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """Get the singleton Logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def configure(db_path: str = "mc_logger.db", flush_interval: float = 1.0):
    """Configure the global logger."""
    logger = get_logger()
    logger.configure(db_path=db_path, flush_interval=flush_interval)
