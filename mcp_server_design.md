# MC Logger MCP Server Design

## Executive Summary

This document outlines the design for integrating FastMCP into the MC Logger project as an **optional feature** using Python's extras mechanism. This allows users to install the minimal logging library or optionally add MCP server capabilities.

## Installation Patterns

### Core Library (Current)
```bash
uv add mc-logger
```
Includes: FastAPI middleware, SQLite storage, logging core, basic query tools

### With MCP Server Support (Proposed)
```bash
uv add "mc-logger[mcp]"
```
Includes: Everything above + FastMCP server with exposed tools

### Development Install (Proposed)
```bash
uv add "mc-logger[dev,mcp]"
```
Includes: Everything + pytest, httpx, uvicorn, and MCP dependencies

## Architecture Design

### Option 1: Separate Module (RECOMMENDED)
Create a new module `mc_logger.mcp` that is only imported when FastMCP is available.

**Pros:**
- Clean separation of concerns
- No import errors if fastmcp not installed
- Easy to maintain and test independently
- Users who don't need MCP don't pay any overhead
- Follows single-responsibility principle

**Cons:**
- Slightly more complex project structure
- Need to handle conditional imports

**Structure:**
```
mc_logger/
├── __init__.py           # Core exports (no MCP)
├── models.py
├── storage.py
├── context.py
├── core.py
├── middleware.py
├── mcp_tools.py          # Query functions (no MCP dependency)
└── mcp/                  # NEW: MCP server module
    ├── __init__.py       # MCP server exports
    ├── server.py         # FastMCP server implementation
    └── tools.py          # MCP tool wrappers around mcp_tools functions
```

### Option 2: Single Module with Conditional Import
Keep everything in one place but check for FastMCP availability.

**Pros:**
- Simpler structure
- All MCP code in one file

**Cons:**
- Mixing concerns
- More complex error handling
- Harder to test in isolation

## Recommended Implementation

### Step 1: Update pyproject.toml

```toml
[project]
name = "mc-logger"
version = "0.1.0"
description = "Unified semantic logging system optimized for AI-assisted debugging"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "MC Logger Contributors"}
]
dependencies = [
    "fastapi>=0.100.0",
]

[project.optional-dependencies]
# MCP server support
mcp = [
    "fastmcp>=2.11.0",
]

# Development dependencies
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
    "uvicorn>=0.23.0",
]

# All optional dependencies
all = [
    "fastmcp>=2.11.0",
]

[project.scripts]
# Optional: CLI entry point for MCP server
mc-logger-mcp = "mc_logger.mcp.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Step 2: Create mc_logger/mcp/server.py

```python
# ABOUTME: FastMCP server implementation for MC Logger
# ABOUTME: Exposes log querying, tracing, and analysis tools via MCP

"""FastMCP server for MC Logger."""

from typing import Optional, List, Dict, Any

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required for MCP server support. "
        "Install with: uv add 'mc-logger[mcp]'"
    )

from ..mcp_tools import (
    query_logs as _query_logs,
    get_request_trace as _get_request_trace,
    summarize_logs as _summarize_logs,
    mark_session as _mark_session,
)
from ..core import configure

# Create MCP server instance
mcp = FastMCP(
    name="MC Logger",
    instructions="""
    MC Logger provides unified semantic logging for AI-assisted debugging.

    Available capabilities:
    - Query logs with filters (time range, level, source, request_id)
    - Get complete request traces with timeline
    - Summarize logs with statistics
    - Mark important debug sessions

    Use these tools to investigate production issues, trace requests,
    and analyze system behavior.
    """,
)


@mcp.tool
def query_logs(
    time_range: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Query logs with various filters.

    Args:
        time_range: Time range like "5m", "2h", "1d" (minutes, hours, days ago)
        request_id: Filter by request ID for request correlation
        session_id: Filter by debug session ID
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: Filter by source component (fastapi, app, database, etc.)
        limit: Maximum number of results to return (default: 100)

    Returns:
        List of log entries matching the filters

    Examples:
        - Get all errors in last 5 minutes: query_logs(time_range="5m", level="ERROR")
        - Get logs for specific request: query_logs(request_id="abc12345")
        - Get recent database logs: query_logs(source="database", time_range="10m")
    """
    return _query_logs(
        time_range=time_range,
        request_id=request_id,
        session_id=session_id,
        level=level,
        source=source,
        limit=limit,
    )


@mcp.tool
def get_request_trace(request_id: str) -> str:
    """
    Get complete trace for a request with formatted timeline.

    Shows the full flow of a request through the system, including:
    - All log entries for the request
    - Timeline with timestamps and emojis
    - Duration and error summary
    - Detailed error information with tracebacks

    Args:
        request_id: The request ID to trace (from X-Request-ID header or logs)

    Returns:
        Markdown-formatted trace report with timeline and error details

    Example:
        trace = get_request_trace("a1b2c3d4")
        # Returns a detailed markdown report showing the request flow
    """
    return _get_request_trace(request_id)


@mcp.tool
def summarize_logs(
    time_range: str = "5m",
    source: Optional[str] = None,
) -> str:
    """
    Generate summary statistics for logs in a time period.

    Provides:
    - Total event count
    - Breakdown by log level (ERROR, WARNING, INFO, DEBUG)
    - Breakdown by source component
    - Recent errors with details

    Args:
        time_range: Time range to summarize like "5m", "1h", "1d" (default: "5m")
        source: Optional filter by source component

    Returns:
        Markdown-formatted summary with statistics and error details

    Examples:
        - Last 5 minutes: summarize_logs("5m")
        - Last hour of API logs: summarize_logs("1h", source="fastapi")
    """
    return _summarize_logs(time_range=time_range, source=source)


@mcp.tool
def mark_session(
    start_time: str,
    end_time: Optional[str] = None,
    label: str = "debug_session",
) -> str:
    """
    Mark a time period as an important debug session for preservation.

    Useful for tagging important investigation periods so they can be
    easily referenced later.

    Args:
        start_time: Start time like "10m" (ago) or ISO timestamp
        end_time: End time (defaults to now) like "5m" or ISO timestamp
        label: Descriptive label for the session (e.g., "payment_bug_investigation")

    Returns:
        Session information including session ID and captured log count

    Example:
        mark_session("10m", label="checkout_error_investigation")
    """
    return _mark_session(
        start_time=start_time,
        end_time=end_time,
        label=label,
    )


@mcp.tool
def configure_logger(
    db_path: str = "./mc_logger.db",
    flush_interval: float = 1.0,
) -> str:
    """
    Configure the MC Logger database and settings.

    Args:
        db_path: Path to SQLite database file (default: "./mc_logger.db")
        flush_interval: Seconds between queue flushes (default: 1.0)

    Returns:
        Configuration confirmation message
    """
    configure(db_path=db_path, flush_interval=flush_interval)
    return f"MC Logger configured: db_path={db_path}, flush_interval={flush_interval}s"


def create_server(**kwargs) -> FastMCP:
    """
    Create a configured FastMCP server instance.

    This is the main entry point for programmatic server creation.

    Args:
        **kwargs: Additional FastMCP server options (auth, tags, etc.)

    Returns:
        Configured FastMCP server instance

    Example:
        from mc_logger.mcp import create_server

        server = create_server()
        server.run()  # Run with stdio transport
    """
    # Update server with any additional options
    if kwargs:
        # This would reinitialize with new options if needed
        pass
    return mcp
```

### Step 3: Create mc_logger/mcp/__init__.py

```python
# ABOUTME: MCP server module for MC Logger
# ABOUTME: Optional module that requires fastmcp to be installed

"""
MCP Server for MC Logger.

This module provides Model Context Protocol (MCP) server capabilities
for MC Logger, allowing AI assistants to query and analyze logs.

Installation:
    uv add "mc-logger[mcp]"

Usage:
    from mc_logger.mcp import create_server

    server = create_server()
    server.run()  # stdio transport

    # Or via CLI:
    # fastmcp run mc_logger.mcp:mcp
"""

try:
    from .server import mcp, create_server

    __all__ = ["mcp", "create_server"]
except ImportError as e:
    raise ImportError(
        "FastMCP is required for MCP server support. "
        "Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'"
    ) from e
```

### Step 4: Create mc_logger/mcp/cli.py (Optional)

```python
# ABOUTME: CLI entry point for MC Logger MCP server
# ABOUTME: Allows running server via 'mc-logger-mcp' command

"""CLI for running MC Logger MCP server."""

import argparse
import sys

from .server import mcp


def main():
    """Main CLI entry point for MC Logger MCP server."""
    parser = argparse.ArgumentParser(
        description="MC Logger MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio transport (for MCP clients)
  mc-logger-mcp

  # Run with HTTP transport on custom port
  mc-logger-mcp --transport http --port 8080

  # Configure database path
  mc-logger-mcp --db-path /path/to/logs.db
        """,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="./mc_logger.db",
        help="Path to SQLite database (default: ./mc_logger.db)",
    )

    parser.add_argument(
        "--flush-interval",
        type=float,
        default=1.0,
        help="Flush interval in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    # Configure logger
    from ..core import configure
    configure(db_path=args.db_path, flush_interval=args.flush_interval)

    # Run server
    try:
        if args.transport == "http":
            print(f"Starting MC Logger MCP server on http://localhost:{args.port}")
            mcp.run(transport="http", port=args.port)
        else:
            print("Starting MC Logger MCP server with stdio transport", file=sys.stderr)
            mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down MC Logger MCP server", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
```

## Usage Examples

### As MCP Server via FastMCP CLI

```bash
# Install with MCP support
uv add "mc-logger[mcp]"

# Run via fastmcp CLI (stdio transport for MCP clients)
fastmcp run mc_logger.mcp:mcp

# Run via fastmcp CLI (HTTP transport)
fastmcp run mc_logger.mcp:mcp --transport http --port 8000
```

### As MCP Server via Custom CLI

```bash
# Install with MCP support
uv add "mc-logger[mcp]"

# Run via custom CLI
mc-logger-mcp

# Or with HTTP transport
mc-logger-mcp --transport http --port 8080
```

### Programmatic Usage

```python
from mc_logger.mcp import create_server

# Create and run server
server = create_server()
server.run()  # stdio transport by default
```

### Integration with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mc-logger": {
      "command": "uv",
      "args": ["run", "mc-logger-mcp"],
      "env": {
        "DB_PATH": "/path/to/logs.db"
      }
    }
  }
}
```

Or using fastmcp directly:

```json
{
  "mcpServers": {
    "mc-logger": {
      "command": "uvx",
      "args": ["fastmcp", "run", "mc_logger.mcp:mcp"]
    }
  }
}
```

## Testing Strategy

### Unit Tests for MCP Module

```python
# tests/test_mcp_server.py
import pytest

pytest.importorskip("fastmcp")  # Skip if fastmcp not installed

from mc_logger.mcp import create_server


def test_mcp_server_creation():
    """Test that MCP server can be created."""
    server = create_server()
    assert server is not None
    assert server.name == "MC Logger"


def test_mcp_tools_registered():
    """Test that all tools are registered."""
    server = create_server()
    tools = server.list_tools()

    expected_tools = [
        "query_logs",
        "get_request_trace",
        "summarize_logs",
        "mark_session",
        "configure_logger",
    ]

    tool_names = [t.name for t in tools]
    for expected in expected_tools:
        assert expected in tool_names
```

### Integration Tests

```python
# tests/test_mcp_integration.py
import pytest

pytest.importorskip("fastmcp")

from mc_logger.mcp import mcp
from mc_logger import configure, get_logger
import tempfile


@pytest.mark.asyncio
async def test_query_logs_tool():
    """Test query_logs tool via MCP."""
    with tempfile.TemporaryDirectory() as tmpdir:
        configure(db_path=f"{tmpdir}/test.db")
        logger = get_logger()

        # Create test logs
        logger.log("INFO", "test message", "app")
        logger.flush()

        # Query via MCP tool
        result = await mcp.call_tool("query_logs", {"level": "INFO"})

        assert len(result) > 0
        assert result[0]["message"] == "test message"
```

## Documentation Updates

### README.md Addition

```markdown
## MCP Server Support (Optional)

MC Logger can optionally run as an MCP (Model Context Protocol) server,
allowing AI assistants to query and analyze logs.

### Installation

```bash
# Install with MCP support
uv add "mc-logger[mcp]"
```

### Running the MCP Server

```bash
# Run with stdio transport (for MCP clients)
mc-logger-mcp

# Run with HTTP transport
mc-logger-mcp --transport http --port 8080
```

### Integration with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mc-logger": {
      "command": "mc-logger-mcp"
    }
  }
}
```

### Available MCP Tools

- **query_logs**: Query logs with filters (time, level, source, request_id)
- **get_request_trace**: Get complete request trace with timeline
- **summarize_logs**: Generate log statistics and summaries
- **mark_session**: Mark important debug sessions for preservation
- **configure_logger**: Configure database path and settings
```

## Migration Path

### Phase 1: Add Optional MCP Module (Current PR)
- Add `[project.optional-dependencies]` with mcp extra
- Create `mc_logger/mcp/` module
- Implement FastMCP server
- Add tests with conditional imports
- Update documentation

### Phase 2: Future Enhancements
- Add more MCP resources (log streams, real-time updates)
- Implement MCP prompts for common debugging workflows
- Add authentication support for remote MCP servers
- Create FastMCP Cloud deployment guide

## Benefits of This Approach

1. **Zero Breaking Changes**: Existing users get no new dependencies
2. **Clear Separation**: MCP code is isolated in its own module
3. **Easy to Install**: Standard Python extras pattern (`[mcp]`)
4. **Professional**: Follows best practices from projects like pydantic-ai
5. **Testable**: Can test with and without fastmcp installed
6. **Maintainable**: Each module has clear responsibilities
7. **Future-Proof**: Easy to add more optional features later

## Alternative Considered: Everything in One Module

We could have added fastmcp to core dependencies and put everything in `mc_logger/mcp_tools.py`:

**Rejected because:**
- Forces fastmcp on all users (unnecessary dependency)
- Mixes logging and server concerns
- Harder to test and maintain
- Less professional package structure

## Conclusion

The recommended approach creates a clean, optional MCP module that:
- Uses Python's standard extras mechanism
- Provides clear error messages when fastmcp isn't installed
- Maintains backward compatibility
- Follows industry best practices
- Scales well for future enhancements

**Recommended Next Steps:**
1. Update pyproject.toml with `mcp` extra
2. Create `mc_logger/mcp/` module with server.py, __init__.py, cli.py
3. Add conditional tests
4. Update README with MCP installation instructions
5. Test with Claude Desktop integration
