# MC Logger Examples

## Running the Example App

### Install dependencies (including uvicorn)

```bash
uv sync --all-extras
```

### Start the server

```bash
uv run python examples/fastapi_app.py
```

The server will start on http://localhost:8000

### Test the endpoints

```bash
# Test root endpoint
curl http://localhost:8000/

# Test user endpoint (success)
curl http://localhost:8000/users/42

# Test user endpoint (not found)
curl http://localhost:8000/users/999

# Create a new user
curl -X POST "http://localhost:8000/users?name=Alice"

# Trigger an error (for testing)
curl http://localhost:8000/error

# Get log summary
curl "http://localhost:8000/debug/summary?time_range=5m"

# List recent request IDs
curl http://localhost:8000/debug/requests

# Get request trace (use a request_id from the list above)
curl http://localhost:8000/debug/trace/REQUEST_ID_HERE
```

## What to Observe

1. **Automatic Request Logging**: Every request is automatically logged with method, path, headers, and timing
2. **Error Capture**: Errors include full traceback information
3. **Request Correlation**: All logs for a request share the same request_id
4. **Header Redaction**: Sensitive headers like Authorization are automatically redacted
5. **Performance Metrics**: Slow requests (>1000ms) are flagged
6. **Debug Endpoints**: Query and analyze logs through the API

## Viewing Logs

Logs are stored in `example_logs.db`. You can query them using:

```python
from mc_logger import get_logger

logger = get_logger()
entries = logger.query(limit=10)

for entry in entries:
    print(f"{entry.timestamp} [{entry.level}] {entry.message}")
```

Or use the MCP tools:

```python
from mc_logger.mcp_tools import summarize_logs, get_request_trace

# Get summary
summary = summarize_logs(time_range="5m")
print(summary)

# Get trace for specific request
trace = get_request_trace("abc12345")
print(trace)
```
