# Feature: MC Logger - Project Foundation and Core Implementation

## Feature Description
Initialize and implement the complete MC Logger project foundation, including project structure, data models, context management, storage backend, core logger, FastAPI middleware, MCP query tools, and comprehensive documentation. This feature builds a unified semantic logging system optimized for AI-assisted debugging with zero-code FastAPI instrumentation, automatic correlation tracking, and efficient SQLite storage.

## User Story
As a developer building FastAPI applications
I want a zero-configuration logging system that automatically captures requests, errors, and correlations
So that AI assistants can independently investigate and debug issues without manual log aggregation

## Problem Statement
Currently, debugging multi-service local development environments requires:
- Manually checking multiple terminal windows and log files
- Copy-pasting log snippets to AI assistants for analysis
- Losing context and correlation between different services
- Reconstructing event sequences across disparate sources

This creates friction in the debugging workflow and prevents AI assistants from independently investigating issues.

## Solution Statement
Create MC Logger, a local-first unified logging system that:
1. Automatically instruments FastAPI applications with zero code changes (just add middleware)
2. Preserves original log formats while adding consistent metadata for machine parsing
3. Provides automatic correlation detection via request IDs propagated through async contexts
4. Stores logs efficiently in SQLite with WAL mode for concurrent access
5. Offers MCP tools for AI assistants to query, analyze, and trace requests

## Relevant Files
This is a greenfield implementation with the following structure:

### Core Package Files
- **mc_logger/__init__.py** - Public API exports for Logger, configure, instrument_fastapi, LogEntry
- **mc_logger/models.py** - LogEntry dataclass with serialization/deserialization
- **mc_logger/context.py** - Async-safe context management using contextvars for request/session/correlation IDs
- **mc_logger/storage.py** - SQLite backend with WAL mode, batch writes, and efficient querying
- **mc_logger/core.py** - Logger singleton with async queue-based writes and graceful shutdown
- **mc_logger/middleware.py** - FastAPI ASGI middleware for automatic request/response logging
- **mc_logger/mcp_tools.py** - Query API, request tracing, session management, and log summarization

### Test Files
- **tests/__init__.py** - Empty package marker
- **tests/test_models.py** - LogEntry creation, serialization, JSON round-trips
- **tests/test_context.py** - Context isolation, request ID propagation, async safety
- **tests/test_storage.py** - Database initialization, batch writes, query filters, time ranges
- **tests/test_core.py** - Singleton pattern, async writes, context enrichment, flush behavior
- **tests/test_fastapi.py** - Middleware integration, error capture, correlation, header redaction
- **tests/test_mcp_tools.py** - Query tools, request traces, summaries, time parsing
- **tests/test_integration.py** - End-to-end workflows, AI debugging scenarios

### Documentation & Examples
- **README.md** - Installation, quick start, configuration, MCP tools overview
- **examples/fastapi_app.py** - Complete working FastAPI application with MC Logger
- **examples/README.md** - How to run examples and test the system

### New Files
- **pyproject.toml** - Package configuration with dependencies (fastapi, pytest, pytest-asyncio, httpx, uvicorn)

## Implementation Plan

### Phase 1: Foundation
Set up the basic project structure, package configuration, and core data models that all other components will depend on. This includes the LogEntry model for representing logs, context management for async-safe request tracking, and SQLite storage for persistence.

### Phase 2: Core Implementation
Build the Logger singleton with async queue-based writes, graceful shutdown handling, and automatic context enrichment. Implement FastAPI middleware for zero-configuration instrumentation that captures all requests, responses, and errors with proper correlation.

### Phase 3: Integration
Create MCP query tools for AI assistants, complete working examples, comprehensive documentation, and integration tests that validate the entire system end-to-end.

## Step by Step Tasks

### Initialize Project Structure
- Create `mc_logger/` directory for the main package
- Create `tests/` directory for test suite
- Create `examples/` directory for demonstration code
- Write `pyproject.toml` with project metadata, dependencies (fastapi>=0.100.0), and dev dependencies (pytest>=7.0.0, pytest-asyncio>=0.21.0, httpx>=0.24.0, uvicorn>=0.23.0)
- Write `mc_logger/__init__.py` to export Logger, get_logger, configure, LogEntry, instrument_fastapi
- Write `tests/__init__.py` as empty package marker
- Validate with `uv add fastapi pytest pytest-asyncio httpx uvicorn --dev`
- Validate with `python -c "import mc_logger; print(mc_logger.__version__)"` outputs "0.1.0"

### Implement Data Models
- Write `mc_logger/models.py` with LogEntry dataclass
- Include fields: timestamp, level, message, source, request_id, session_id, correlation_id, confidence, metadata
- Implement to_dict(), to_json(), from_dict() for serialization
- Implement create() factory method with auto-timestamp and uppercased levels
- Write `tests/test_models.py` covering creation, serialization, JSON round-trips, edge cases (None values, empty metadata)
- Validate with `uv run pytest tests/test_models.py -v`

### Implement Context Management
- Write `mc_logger/context.py` using contextvars for async-safe storage
- Implement request_id, session_id, correlation_id ContextVars with None defaults
- Implement generate_id() for 8-character unique IDs
- Implement set/get/reset functions for each context variable with Token returns
- Implement clear_context() for cleanup between tests
- Write `tests/test_context.py` covering auto-generation, context isolation, async safety, Token reset
- Validate with `uv run pytest tests/test_context.py -v`

### Implement SQLite Storage Backend
- Write `mc_logger/storage.py` with SQLiteStorage class
- Enable WAL mode via `PRAGMA journal_mode=WAL` for concurrent access
- Create logs table with all LogEntry fields plus auto-incrementing ID
- Create indices on timestamp DESC, request_id, session_id, level, source
- Implement write() and write_batch() with thread-safe Lock
- Implement query() with filters for time range, request_id, session_id, level, source, limit
- Implement count() and clear() methods
- Use context manager for connection management with 30s timeout
- Write `tests/test_storage.py` covering initialization, single/batch writes, query filters, time ranges, concurrency
- Validate with `uv run pytest tests/test_storage.py -v`

### Implement Core Logger
- Write `mc_logger/core.py` with Logger singleton class
- Use double-checked locking pattern for thread-safe singleton
- Initialize with Queue(maxsize=10000) for async writes
- Create background worker thread that flushes queue every flush_interval seconds
- Implement configure() to set db_path and flush_interval, start worker
- Implement log() that auto-configures on first use, enriches with context (request_id, session_id, correlation_id), and adds to queue
- Handle queue overflow by dropping oldest entry and retrying
- Implement flush() to force immediate queue drain
- Implement shutdown() via atexit for graceful cleanup
- Implement query() wrapper to storage.query()
- Provide get_logger() and configure() helper functions
- Write `tests/test_core.py` covering singleton, basic logging, context enrichment, async writes, auto-configuration
- Validate with `uv run pytest tests/test_core.py -v`

### Implement FastAPI Middleware
- Write `mc_logger/middleware.py` with MCLoggerMiddleware extending BaseHTTPMiddleware
- Define SENSITIVE_HEADERS (authorization, cookie, x-api-key, x-csrf-token, x-auth-token)
- Define DEFAULT_EXCLUDE_PATHS (/health, /healthz, /ping, /_health)
- In dispatch(), set request_id in context (from header or generate)
- Log request.start with method, path, query params, redacted headers, client IP
- Execute call_next() and capture response or exception
- Log request.complete with status code, duration_ms, slow_request flag (>1000ms)
- Log request.error with error type, message, traceback on exceptions
- Add X-Request-ID to response headers
- Reset context after request completes
- Implement _redact_headers() to replace sensitive header values with "[REDACTED]"
- Provide instrument_fastapi(app, **kwargs) helper function
- Update `mc_logger/__init__.py` to export instrument_fastapi
- Write `tests/test_fastapi.py` covering basic logging, error capture, correlation, exclude paths, header redaction
- Validate with `uv run pytest tests/test_fastapi.py -v`

### Implement MCP Query Tools
- Write `mc_logger/mcp_tools.py` with query and analysis functions
- Implement parse_time_range() to convert "5m", "2h", "1d" to unix timestamps
- Implement query_logs() with filters for time_range, request_id, session_id, level, source, limit
- Implement get_request_trace() to return markdown-formatted timeline for a request_id
- Include emoji indicators (❌ ERROR, ⚠️ WARNING, ℹ️ INFO, 🔍 DEBUG)
- Show duration, event count, and error summary in trace
- Implement mark_session() to label a time period as important for preservation
- Implement summarize_logs() to generate markdown summary with statistics by level and source
- Write `tests/test_mcp_tools.py` covering time parsing, query filters, trace formatting, summaries
- Validate with `uv run pytest tests/test_mcp_tools.py -v`

### Create Complete Example
- Write `examples/fastapi_app.py` with FastAPI app demonstrating MC Logger
- Include endpoints: GET /, GET /users/{user_id}, POST /users, GET /error, GET /debug/summary, GET /debug/trace/{request_id}
- Configure MC Logger with configure(db_path="./example_logs.db")
- Instrument app with instrument_fastapi(app)
- Add manual logger.log() calls in business logic
- Include error endpoint that raises ValueError for testing
- Write `examples/README.md` with running instructions and curl examples
- Validate by running `uv run uvicorn examples.fastapi_app:app` and making test requests

### Write Project Documentation
- Write root `README.md` with features, installation, quick start, FastAPI integration, querying examples
- Include configuration options (db_path, flush_interval)
- Document MCP tools (query_logs, get_request_trace, mark_session, summarize_logs)
- Show architecture diagram (FastAPI App → Middleware → Logger → Queue → SQLite)
- List performance metrics (< 1ms overhead, < 10MB memory, ~100MB/day storage)
- Add license (MIT)

### Write Integration Tests
- Write `tests/test_integration.py` with end-to-end scenarios
- Test complete_workflow: successful request, error request, query all logs, get traces, summarize
- Test ai_debugging_scenario: simulate user report, query errors, trace failed request, analyze timeline
- Verify request correlation across all logs in same request
- Verify error capture includes traceback
- Validate with `uv run pytest tests/test_integration.py -v`

### Run Validation Commands
- Execute `uv sync` to ensure all dependencies installed
- Execute `uv run pytest tests/ -v` to run full test suite with zero failures
- Execute `python -c "import mc_logger; print(mc_logger.__version__)"` to verify imports work
- Execute `uv run python examples/fastapi_app.py` to start example server
- Execute curl tests against example endpoints to verify end-to-end functionality
- Verify logs written to example_logs.db
- Verify /debug/summary returns formatted summary
- Verify /debug/trace/{request_id} returns formatted trace

## Testing Strategy

### Unit Tests
- **test_models.py**: LogEntry creation with all field combinations, serialization round-trips, edge cases (None, empty metadata, level uppercasing)
- **test_context.py**: Context variable isolation, async safety with concurrent tasks, auto-generation, token reset
- **test_storage.py**: Database initialization, WAL mode enabled, batch writes, query filters (time, request_id, level, source), concurrent access
- **test_core.py**: Singleton enforcement, async queue writes, auto-configuration, context enrichment, graceful shutdown
- **test_middleware.py**: Request/response logging, error capture with traceback, header redaction, path exclusion, correlation via request_id
- **test_mcp_tools.py**: Time range parsing, query with all filter combinations, trace formatting, summary statistics

### Integration Tests
- **test_integration.py**: Complete workflow with real FastAPI app, multiple requests, error handling, trace retrieval, summary generation
- **AI debugging scenario**: Simulate investigating failed checkout, querying errors, analyzing request trace

### Edge Cases
- Queue overflow when maxsize exceeded (drops oldest, retries)
- None values in all optional LogEntry fields
- Empty metadata dictionary serialization
- Context isolation between concurrent async requests
- Database write failures (log to stderr, continue)
- Missing request_id in trace query (return helpful message)
- Sensitive headers in various cases (case-insensitive matching)
- Health check paths excluded from logging
- Final flush on shutdown via atexit
- Large result sets (limit parameter enforced)

## Acceptance Criteria
- Package installs successfully with `uv sync`
- Importing `mc_logger` works and exposes Logger, get_logger, configure, LogEntry, instrument_fastapi
- Version is "0.1.0"
- All unit tests pass with `pytest tests/ -v`
- FastAPI app can be instrumented with single line: `instrument_fastapi(app)`
- All requests automatically logged with request_id, timing, status
- Errors captured with full traceback
- Sensitive headers redacted (authorization, cookie, x-api-key)
- Health check paths excluded (/health, /healthz, /ping)
- Logs queryable by time range, request_id, session_id, level, source
- Request traces show complete timeline with emoji indicators
- Log summaries show statistics by level and source
- Example app runs and demonstrates all features
- Logging overhead < 1ms per request
- Memory overhead < 10MB base
- Documentation complete and accurate

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv sync` - Install all dependencies
- `uv run pytest tests/ -v --tb=short` - Run full test suite with zero failures
- `python -c "import mc_logger; print(mc_logger.__version__)"` - Verify version is 0.1.0
- `python -c "from mc_logger import Logger, get_logger, configure, LogEntry, instrument_fastapi; print('✓ All imports work')"` - Verify exports
- `uv run python examples/fastapi_app.py &` - Start example server in background
- `sleep 2 && curl -s http://localhost:8000/ | grep -q "Hello" && echo "✓ Root endpoint works"` - Test root
- `curl -s http://localhost:8000/users/42 | grep -q "Test User" && echo "✓ User endpoint works"` - Test parameterized endpoint
- `curl -s -X POST "http://localhost:8000/users?name=Alice" | grep -q "Alice" && echo "✓ POST endpoint works"` - Test POST
- `curl -s http://localhost:8000/error 2>&1 | grep -q "500" && echo "✓ Error endpoint captured"` - Test error capture
- `curl -s "http://localhost:8000/debug/summary?time_range=5m" | grep -q "Total Events" && echo "✓ Summary works"` - Test summary
- `pkill -f "uvicorn examples.fastapi_app"` - Stop example server
- `test -f example_logs.db && echo "✓ Logs persisted to database"` - Verify DB created
- `sqlite3 example_logs.db "SELECT COUNT(*) FROM logs" | grep -q "[0-9]" && echo "✓ Logs written to DB"` - Verify logs exist

## Notes
- **Performance**: Async writes via Queue ensure < 1ms overhead per request
- **Concurrency**: SQLite WAL mode allows concurrent reads while writing
- **Context Safety**: contextvars ensure proper isolation in async FastAPI
- **Error Handling**: Logger failures never crash application (best-effort logging)
- **Future Extensions**: After v0.1.0 ships, extend to Docker logs, SQLite query logging, Redis monitoring, file watching
- **Dependencies Added**: fastapi, pytest, pytest-asyncio, httpx, uvicorn (all via uv)
- **Python Version**: Requires Python 3.9+ for contextvars and dataclasses
