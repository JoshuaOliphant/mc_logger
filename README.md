# MC Logger

Unified semantic logging system optimized for AI-assisted debugging.

## Features

- **Zero-Configuration FastAPI Instrumentation**: Add one line to automatically log all requests, responses, and errors
- **Automatic Correlation Tracking**: Request IDs propagated through async contexts
- **AI-Optimized Query Tools**: MCP tools for Claude and other AI assistants to independently investigate issues
- **Efficient SQLite Storage**: WAL mode for concurrent access, ~100MB/day for typical workloads
- **Minimal Overhead**: < 1ms per request, < 10MB base memory usage
- **Semantic Structure**: Consistent metadata format for machine parsing while preserving original log messages

## Installation

```bash
uv add mc-logger
```

Or with pip:

```bash
pip install mc-logger
```

## Quick Start

### FastAPI Integration

```python
from fastapi import FastAPI
from mc_logger import configure, instrument_fastapi

# Configure MC Logger (optional - uses defaults if not called)
configure(db_path="./logs.db")

# Create your FastAPI app
app = FastAPI()

# Instrument with MC Logger (one line!)
instrument_fastapi(app)

# All requests are now automatically logged!
@app.get("/")
async def root():
    return {"message": "Hello"}
```

### Manual Logging

```python
from mc_logger import get_logger

logger = get_logger()

logger.log("INFO", "User action completed", source="api")
logger.log("ERROR", "Payment failed", source="payment", metadata={"amount": 100})
```

## Configuration

```python
from mc_logger import configure

configure(
    db_path="./logs.db",        # SQLite database path
    flush_interval=1.0,         # Flush queue every N seconds
)
```

## Querying Logs

### Using the Logger API

```python
from mc_logger import get_logger

logger = get_logger()

# Query recent logs
entries = logger.query(limit=100)

# Filter by level
errors = logger.query(level="ERROR", limit=50)

# Filter by request ID
request_logs = logger.query(request_id="abc12345")

# Filter by time range (unix timestamps)
import time
recent = logger.query(
    start_time=time.time() - 300,  # Last 5 minutes
    limit=100
)
```

### Using MCP Tools (for AI Assistants)

```python
from mc_logger.mcp_tools import query_logs, get_request_trace, summarize_logs

# Query with time range
entries = query_logs(time_range="5m", level="ERROR")

# Get complete trace for a request
trace = get_request_trace("abc12345")
print(trace)  # Markdown-formatted timeline with emoji indicators

# Get summary statistics
summary = summarize_logs(time_range="1h")
print(summary)  # Events by level and source
```

## What Gets Logged

### Automatic Middleware Logs

For every request:

- `request.start`: Method, path, query params, headers (redacted), client IP
- `request.complete`: Status code, duration, slow request flag (>1s)
- `request.error`: Error type, message, full traceback

### Manual Logs

Your application code logs with automatic enrichment:

- Timestamp (auto)
- Level (uppercased)
- Message
- Source (default: "app")
- Request ID (from context)
- Session ID (from context)
- Correlation ID (from context)
- Confidence score (optional)
- Metadata dict (optional)

## Architecture

```
FastAPI App
    ↓
Middleware (captures requests/responses)
    ↓
Logger (enriches with context)
    ↓
Queue (async, max 10k entries)
    ↓
Worker Thread (batch writes every 1s)
    ↓
SQLite with WAL mode
```

## Performance

- **Request Overhead**: < 1ms per request (async queue)
- **Memory Usage**: < 10MB base, grows with queue depth
- **Storage**: ~100MB/day for typical workloads
- **Concurrency**: WAL mode enables concurrent reads during writes

## MCP Tools for AI Assistants

MC Logger provides tools for AI assistants to independently investigate issues:

### `query_logs`

```python
query_logs(
    time_range="5m",           # "5m", "2h", "1d"
    request_id=None,
    session_id=None,
    level=None,                # "INFO", "ERROR", etc.
    source=None,               # "api", "worker", etc.
    limit=1000
)
```

### `get_request_trace`

Returns markdown-formatted timeline for a request:

```markdown
# Request Trace: abc12345

**Duration:** 245.67ms
**Events:** 8
**Errors:** ❌ 1

## Timeline

**14:23:45.123** ℹ️ `INFO` request.start
  - method: POST
  - path: /checkout

**14:23:45.234** ℹ️ `INFO` Processing payment
  - amount: 100

**14:23:45.345** ❌ `ERROR` Payment failed
  - error: insufficient_funds
```

### `summarize_logs`

Returns markdown summary with statistics:

```markdown
# Log Summary

**Time Range:** 2025-01-15 14:00:00 to 2025-01-15 15:00:00
**Total Events:** 1,234

## Events by Level

- **INFO**: 1,000
- **ERROR**: 150
- **WARNING**: 84

## Events by Source

- **api**: 800
- **middleware**: 400
- **worker**: 34
```

### `mark_session`

Mark a time period as important for preservation:

```python
mark_session("sess123", start_time=..., end_time=...)
```

## Header Redaction

Sensitive headers are automatically redacted:

- `authorization`
- `cookie`
- `x-api-key`
- `x-csrf-token`
- `x-auth-token`

## Excluded Paths

Health check endpoints are excluded by default:

- `/health`
- `/healthz`
- `/ping`
- `/_health`

Customize with:

```python
from mc_logger import instrument_fastapi

instrument_fastapi(app, exclude_paths={"/custom", "/health"})
```

## Examples

See `examples/fastapi_app.py` for a complete working application.

Run the example:

```bash
uv run python examples/fastapi_app.py
```

Test it:

```bash
curl http://localhost:8000/
curl http://localhost:8000/users/42
curl http://localhost:8000/error
curl "http://localhost:8000/debug/summary?time_range=5m"
```

## Requirements

- Python 3.9+
- FastAPI 0.100.0+

## License

MIT
