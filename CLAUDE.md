# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MC Logger is a unified semantic logging system optimized for AI-assisted debugging in local development environments. It provides zero-configuration FastAPI instrumentation with automatic request correlation tracking, async queue-based writes to SQLite, and MCP tools for AI assistants to independently query and analyze logs.

**Core Value Proposition**: AI assistants can investigate production issues by querying structured logs without requiring developers to manually grep through log files or aggregate data from multiple sources.

## Issue Tracking

We use bd (beads) for issue tracking instead of Markdown TODOs or external tools.

### Quick Reference

```bash
# Find ready work (no blockers)
bd ready --json

# Create new issue
bd create "Issue title" -t bug|feature|task -p 0-4 -d "Description" --json

# Create with explicit ID (for parallel workers)
bd create "Issue title" --id worker1-100 -p 1 --json

# Create multiple issues from markdown file
bd create -f feature-plan.md --json

# Update issue status
bd update <id> --status in_progress --json

# Link discovered work (old way)
bd dep add <discovered-id> <parent-id> --type discovered-from

# Create and link in one command (new way)
bd create "Issue title" -t bug -p 1 --deps discovered-from:<parent-id> --json

# Complete work
bd close <id> --reason "Done" --json

# Show dependency tree
bd dep tree <id>

# Get issue details
bd show <id> --json

# Import with collision detection
bd import -i .beads/issues.jsonl --dry-run             # Preview only
bd import -i .beads/issues.jsonl --resolve-collisions  # Auto-resolve
```

### Workflow

1. **Check for ready work**: Run `bd ready` to see what's unblocked
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work**: If you find bugs or TODOs, create issues:
   - Old way (two commands): `bd create "Found bug in auth" -t bug -p 1 --json` then `bd dep add <new-id> <current-id> --type discovered-from`
   - New way (one command): `bd create "Found bug in auth" -t bug -p 1 --deps discovered-from:<current-id> --json`
5. **Complete**: `bd close <id> --reason "Implemented"`
6. **Export**: Changes auto-sync to `.beads/issues.jsonl` (5-second debounce)

### Issue Types

- `bug` - Something broken that needs fixing
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature composed of multiple issues
- `chore` - Maintenance work (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (nice-to-have features, minor bugs)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Dependency Types

- `blocks` - Hard dependency (issue X blocks issue Y)
- `related` - Soft relationship (issues are connected)
- `parent-child` - Epic/subtask relationship
- `discovered-from` - Track issues discovered during work

Only `blocks` dependencies affect the ready work queue.

## Architecture

### High-Level Data Flow

```
FastAPI Request
    ↓
MCLoggerMiddleware (middleware.py)
    ├─ Sets request_id in contextvars
    ├─ Logs request.start
    ├─ Executes app
    ├─ Logs request.complete or request.error
    └─ Resets context
    ↓
Logger.log() (core.py)
    ├─ Auto-enriches with context (request_id, session_id, correlation_id)
    ├─ Creates LogEntry
    └─ Adds to Queue (async, non-blocking)
    ↓
Worker Thread (core.py._worker)
    ├─ Collects entries from queue every flush_interval
    └─ Batch writes to SQLiteStorage
    ↓
SQLite Database (storage.py)
    ├─ WAL mode for concurrent reads
    ├─ Indexed by timestamp, request_id, level, source
    └─ Efficient querying via storage.query()
```

### Key Design Patterns

**Singleton Logger**: `Logger` class uses double-checked locking to ensure only one instance exists. The singleton is shared across all requests but uses contextvars for isolation.

**Context Propagation**: `context.py` uses Python's `contextvars` module to propagate request_id, session_id, and correlation_id through async call chains. This is critical for maintaining correlation across async FastAPI requests.

**Async Queue Pattern**: Logging never blocks the request path. Entries go into a 10k-capacity queue, and a background worker thread does batch writes every 1 second (configurable via `flush_interval`).

**Automatic Context Enrichment**: When `logger.log()` is called, it automatically pulls request_id/session_id/correlation_id from contextvars and enriches the log entry. Application code doesn't need to manually pass these values.

## Development Commands

### Environment Setup

```bash
# Install dependencies (uses uv for fast resolution)
uv sync

# Install package in editable mode
uv pip install -e .
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_core.py -v

# Run single test
uv run pytest tests/test_core.py::test_singleton_pattern -v

# Run tests with coverage
uv run pytest tests/ --cov=mc_logger --cov-report=html
```

**Important Test Notes**:
- Tests use `force=True` when calling `logger.configure()` because the Logger is a singleton that persists across tests
- FastAPI integration tests require `ASGITransport` from httpx (not the deprecated `app=` parameter)
- Async tests may need `await asyncio.sleep(0.2)` after requests to allow background worker time to flush the queue before assertions

### Running Examples

```bash
# Start example FastAPI app
uv run python examples/fastapi_app.py

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/users/42
curl http://localhost:8000/error
curl "http://localhost:8000/debug/summary?time_range=5m"
```

### Package Build

```bash
# Build package for distribution
uv build
```

## Module Structure

### Core Components

**mc_logger/__init__.py**: Public API exports. Only exports: Logger, get_logger, configure, LogEntry, instrument_fastapi

**mc_logger/models.py**: `LogEntry` dataclass with serialization. Key method: `LogEntry.create()` auto-generates timestamp and uppercases level.

**mc_logger/context.py**: Async-safe context management. All context values are stored in `ContextVar` instances and can be set/get/reset independently. Context is automatically cleared after each request by middleware.

**mc_logger/storage.py**: SQLite backend with WAL mode. The `query()` method accepts multiple optional filters (time_range, request_id, session_id, level, source, limit) and returns List[LogEntry].

**mc_logger/core.py**:
- `Logger` class is the singleton that manages the queue and worker thread
- `configure()` initializes storage and starts worker (call with `force=True` to reconfigure)
- `log()` enriches entries with context and adds to queue (never blocks)
- `flush()` forces immediate queue drain (useful for tests)
- Worker thread runs in background, collecting entries and batch-writing every flush_interval seconds

**mc_logger/middleware.py**: `MCLoggerMiddleware` is a FastAPI BaseHTTPMiddleware that:
- Extracts or generates request_id from X-Request-ID header
- Sets request_id in contextvars for the request scope
- Logs request.start, request.complete, request.error
- Redacts sensitive headers (authorization, cookie, x-api-key, etc.)
- Excludes health check paths by default (/health, /healthz, /ping)
- Adds X-Request-ID to response headers
- Always clears context in finally block to prevent leakage

**mc_logger/mcp_tools.py**: Query and analysis tools for AI assistants:
- `parse_time_range()`: Converts "5m", "2h", "1d" to unix timestamps
- `query_logs()`: High-level query wrapper
- `get_request_trace()`: Returns markdown-formatted timeline with emoji indicators (❌ ERROR, ⚠️ WARNING, ℹ️ INFO, 🔍 DEBUG)
- `summarize_logs()`: Returns markdown summary with statistics by level and source
- `mark_session()`: Placeholder for marking important sessions (future feature)

## Critical Implementation Details

### Testing Singleton Behavior

The Logger singleton persists across tests. When writing tests that need a fresh logger configuration:

```python
logger = Logger()
logger.configure(db_path=temp_path, flush_interval=0.1, force=True)  # force=True is critical
```

### Context Isolation

Contextvars automatically isolate between async tasks. However, you must explicitly clear context after each request to prevent leakage:

```python
# In middleware finally block
reset_request_id(token)
clear_context()
```

### Async Write Behavior

Logs are written asynchronously. In tests, you must:

1. Wait for the worker thread to process the queue: `await asyncio.sleep(0.2)`
2. Force a flush: `logger.flush()`
3. Then query: `entries = logger.query()`

### Header Redaction

Sensitive headers are automatically redacted by checking if the lowercase header name is in the SENSITIVE_HEADERS set. Custom sensitive headers can't currently be added (would need to pass to middleware constructor).

### Request Correlation

All logs within a single request automatically share the same request_id because:
1. Middleware sets request_id in contextvars at request start
2. Logger.log() reads request_id from contextvars when creating LogEntry
3. Contextvars are isolated per async task, so concurrent requests don't interfere

## Common Pitfalls

**Don't pass request_id to logger.log()**: The logger automatically enriches entries with request_id from context. Passing it as a parameter will cause a TypeError.

```python
# WRONG
logger.log("INFO", "message", request_id="abc123")

# CORRECT
set_request_id("abc123")
logger.log("INFO", "message")
```

**Don't forget to use ASGITransport in tests**: The old httpx `app=` parameter is deprecated.

```python
# WRONG
async with AsyncClient(app=app, base_url="http://test") as client:

# CORRECT
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
```

**SQLite WAL mode requires proper shutdown**: Always call `logger.shutdown()` in test cleanup to ensure WAL files are properly closed.

## Performance Characteristics

- **Queue Capacity**: 10,000 entries. When full, drops oldest entry and retries.
- **Flush Interval**: Default 1 second. Configurable per logger instance.
- **Request Overhead**: < 1ms (queue.put_nowait is non-blocking)
- **Memory**: ~10MB base + queue depth (each LogEntry is ~1-2KB)
- **Storage**: ~100MB/day for typical workload (depends on request volume and metadata size)

## Extension Points

To add new MCP tools, add functions to `mcp_tools.py` that return formatted markdown strings. The pattern is:
1. Accept high-level parameters (time_range, request_id, etc.)
2. Call `logger.query()` to fetch LogEntry objects
3. Process and format results as markdown
4. Return string for AI assistant to parse

To add custom metadata to logs, pass a dict to the `metadata` parameter of `logger.log()`. Metadata is JSON-serialized in SQLite and can be queried but not filtered on (no index).

## Python Version Requirements

- Python 3.9+ (requires contextvars and dataclasses)
- FastAPI 0.100.0+
- pytest 7.0.0+ with pytest-asyncio 0.21.0+ for tests
- ALWAYS make sure all tests are passing, do not leave failing tests.
- Don't keep any test scripts unless they will be needed in the future