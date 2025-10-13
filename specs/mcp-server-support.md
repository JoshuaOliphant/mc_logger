# Feature: Optional MCP Server Support with FastMCP

## Feature Description
Implement MC Logger as a Model Context Protocol (MCP) server using FastMCP, allowing AI assistants (Claude Desktop, Cursor, ChatGPT, etc.) to query and analyze logs through standardized MCP tools, resources, and prompts. The MCP server will be an **optional feature** using Python's extras mechanism (`mc-logger[mcp]`) to avoid adding dependencies for users who only need core logging functionality. This follows industry best practices similar to `pydantic-ai[anthropic]` and `httpx[http2]`.

The feature will provide:
- **5 MCP Tools**: query_logs, get_request_trace, summarize_logs, mark_session, configure_logger
- **5 MCP Resources**: logs://recent, logs://request/{id}, logs://session/{id}, logs://errors, logs://source/{name}
- **5 MCP Prompts**: Debug templates for common debugging workflows
- **CLI Command**: `mc-logger-mcp` for easy server startup
- **Environment Variable Configuration**: Docker and Claude Desktop friendly
- **Zero Breaking Changes**: Existing users completely unaffected

## User Story
As an AI assistant (Claude, Cursor, etc.)
I want to independently query and analyze MC Logger databases through standardized MCP tools
So that I can help developers debug production issues without requiring them to manually grep log files or aggregate data

## Problem Statement
MC Logger is already optimized for AI-assisted debugging with query functions in `mcp_tools.py`, but currently requires manual function calls in Python. AI assistants cannot independently access logs without explicit developer code. The Model Context Protocol (MCP) is the emerging standard for AI tool integration, but adding FastMCP as a required dependency would add overhead for users who only need basic logging functionality.

## Solution Statement
Create a new optional module `mc_logger/mcp/` that wraps existing `mcp_tools.py` functions as FastMCP tools, resources, and prompts. Use Python's optional dependencies mechanism (`[mcp]` extra) to keep FastMCP isolated from core functionality. Provide import guards with helpful error messages, environment variable configuration for container/desktop integration, and a CLI command for easy server startup. This maintains zero breaking changes while providing professional MCP integration following industry best practices.

## Relevant Files

### Existing Files to Modify
- **pyproject.toml** - Add optional dependencies section with `[mcp]` extra and CLI script entry point
- **README.md** - Add MCP server section with installation, usage, and Claude Desktop integration examples
- **mc_logger/mcp_tools.py** - Reference existing query functions that will be wrapped by MCP server (no modifications needed)

### New Files to Create

#### Core MCP Module Files
- **mc_logger/mcp/__init__.py** - Import guard with helpful error message, exports `mcp` and `create_server()`
- **mc_logger/mcp/server.py** - FastMCP server implementation with 5 tools wrapping existing `mcp_tools.py` functions
- **mc_logger/mcp/resources.py** - 5 MCP resources for streaming/templated log access
- **mc_logger/mcp/prompts.py** - 5 MCP prompts providing debugging workflow templates
- **mc_logger/mcp/cli.py** - CLI entry point with argparse and environment variable support

#### Test Files
- **tests/test_mcp_server.py** - Test server creation, tool registration, and schemas with conditional imports
- **tests/test_mcp_resources.py** - Test resource URI patterns, content generation, and templated resources
- **tests/test_mcp_prompts.py** - Test prompt registration, argument handling, and message generation
- **tests/test_mcp_integration.py** - End-to-end tests with actual tool execution and temp database

#### Documentation Files
- **docs/mcp_server.md** - Comprehensive guide: setup, integration, env vars, configuration, troubleshooting
- **examples/mcp_server_example.py** - Standalone MCP server example
- **examples/claude_desktop_config.json** - Claude Desktop configuration with environment variables
- **examples/mcp_client_example.py** - Example MCP client usage

## Implementation Plan

### Phase 1: Foundation
Set up the optional dependency infrastructure and create the MCP module skeleton with import guards. This establishes the professional pattern for optional features and ensures helpful error messages when FastMCP is not installed. Update pyproject.toml with the `[mcp]` extra and CLI script entry point.

### Phase 2: Core Implementation
Implement the FastMCP server with tools, resources, and prompts. Wrap existing `mcp_tools.py` functions as MCP tools to avoid code duplication. Create resources for streaming log access and prompts for debugging workflows. Implement the CLI with environment variable support and argument parsing.

### Phase 3: Integration
Add comprehensive tests with conditional imports (pytest.importorskip), update documentation with examples, create integration examples for Claude Desktop and other MCP clients, and validate end-to-end functionality with manual testing.

## Step by Step Tasks

### Step 1: Update pyproject.toml with Optional Dependencies
- Add `[project.optional-dependencies]` section with `mcp = ["fastmcp>=2.11.0"]` and `all = ["fastmcp>=2.11.0"]`
- Add `[project.scripts]` section with `mc-logger-mcp = "mc_logger.mcp.cli:main"`
- This follows the industry standard pattern (similar to pydantic-ai, httpx) for optional features

### Step 2: Create mc_logger/mcp/ Directory Structure
- Create `mc_logger/mcp/` directory to house all MCP-related code
- This separation maintains clean architecture and makes it easy to test with/without MCP

### Step 3: Implement mc_logger/mcp/__init__.py with Import Guard
- Try to import FastMCP in a try/except block
- If import fails, raise ImportError with message: `"MC Logger MCP server requires FastMCP. Install with: uv add 'mc-logger[mcp]'"`
- Export `mcp` server instance and `create_server()` factory function
- Add ABOUTME comments explaining this is the MCP server module entry point with import guards

### Step 4: Implement mc_logger/mcp/server.py with FastMCP Server
- Import FastMCP and create server instance: `mcp = FastMCP("MC Logger", instructions="Semantic logging system optimized for AI-assisted debugging")`
- Define 5 tools using `@mcp.tool()` decorator:
  - `query_logs(time_range, request_id, session_id, level, source, limit)` - Wraps `mcp_tools.query_logs()`
  - `get_request_trace(request_id)` - Wraps `mcp_tools.get_request_trace()`
  - `summarize_logs(time_range, source)` - Wraps `mcp_tools.summarize_logs()`
  - `mark_session(start_time, end_time, label)` - Wraps `mcp_tools.mark_session()`, converts time strings
  - `configure_logger(db_path, flush_interval)` - Wraps `core.configure()`
- Each tool should have proper docstrings that FastMCP uses for schema generation
- Export `mcp` instance and `create_server()` factory function
- Add ABOUTME comments explaining this wraps existing mcp_tools functions as MCP tools

### Step 5: Implement mc_logger/mcp/resources.py with MCP Resources
- Define 5 resources using `@mcp.resource()` decorator:
  - `logs://recent` - Query logs from last 5 minutes, return JSON array
  - `logs://request/{request_id}` - Template resource for specific request logs
  - `logs://session/{session_id}` - Template resource for specific session logs
  - `logs://errors` - Query ERROR level logs from last 5 minutes
  - `logs://source/{source}` - Template resource for logs from specific source
- Each resource handler should call `mcp_tools.query_logs()` with appropriate filters
- Return JSON-serialized list of log entry dictionaries
- Add ABOUTME comments explaining these provide streaming/templated log access

### Step 6: Implement mc_logger/mcp/prompts.py with MCP Prompts
- Define 5 prompts using `@mcp.prompt()` decorator:
  - `debug_error_in_request(request_id: str)` - Multi-step debugging workflow for specific request error
  - `investigate_slow_requests(time_range: str = "10m", threshold_ms: int = 1000)` - Performance analysis guide
  - `find_error_patterns(time_range: str = "1h")` - Error correlation analysis workflow
  - `trace_request_flow(request_id: str)` - Complete request journey visualization
  - `compare_sessions(session_id_1: str, session_id_2: str)` - Session diff analysis guide
- Each prompt returns a list of messages with system instructions and example queries
- Add ABOUTME comments explaining these provide debugging workflow templates

### Step 7: Implement mc_logger/mcp/cli.py with Environment Variable Support
- Import argparse, os, sys, and mc_logger.mcp
- Define `main()` function as CLI entry point
- Add argument parser with options:
  - `--db-path` (env: MC_LOGGER_DB_PATH, default: "./mc_logger.db")
  - `--flush-interval` (env: MC_LOGGER_FLUSH_INTERVAL, default: "1.0")
  - `--transport` (env: MC_LOGGER_TRANSPORT, default: "stdio", choices: ["stdio", "http"])
  - `--port` (env: MC_LOGGER_PORT, default: "8000") - only for HTTP transport
- Priority: CLI args > environment variables > defaults
- Call `configure_logger()` with db_path and flush_interval
- Call `mcp.run(transport=transport, port=port)` to start server
- Add ABOUTME comments explaining CLI entry point with env var support
- Handle import errors gracefully with helpful message

### Step 8: Write Unit Tests for test_mcp_server.py
- Use `pytest.importorskip("fastmcp")` at module level to skip if FastMCP not installed
- Test `create_server()` returns FastMCP instance
- Test all 5 tools are registered (query_logs, get_request_trace, summarize_logs, mark_session, configure_logger)
- Test tool schemas have correct parameters and descriptions
- Test tool execution doesn't raise errors (integration tests will validate outputs)

### Step 9: Write Unit Tests for test_mcp_resources.py
- Use `pytest.importorskip("fastmcp")` at module level
- Test all 5 resources are registered
- Test static resource URI patterns (logs://recent, logs://errors)
- Test templated resource URI patterns (logs://request/{request_id}, logs://session/{session_id}, logs://source/{source})
- Test resource content generation returns valid JSON
- Test resources with parameters correctly substitute values

### Step 10: Write Unit Tests for test_mcp_prompts.py
- Use `pytest.importorskip("fastmcp")` at module level
- Test all 5 prompts are registered
- Test prompt argument handling (required vs optional)
- Test prompt message generation returns list of messages
- Test prompts generate valid debugging workflows with example queries

### Step 11: Write Integration Tests for test_mcp_integration.py
- Use `pytest.importorskip("fastmcp")` at module level
- Create temp database with sample log entries
- Test `query_logs` tool returns correct results with various filters
- Test `get_request_trace` tool returns markdown-formatted trace
- Test `summarize_logs` tool returns markdown summary
- Test `mark_session` tool returns confirmation
- Test `configure_logger` tool updates configuration
- Test resources provide correct data for temp database
- Test prompts generate useful messages with actual request_ids
- Test error handling for invalid parameters

### Step 12: Update README.md with MCP Section
- Add "MCP Server (Optional)" section after "Querying Logs"
- Document installation: `uv add "mc-logger[mcp]"` and `pip install "mc-logger[mcp]"`
- Add CLI usage examples: stdio transport, HTTP transport, environment variables
- Add programmatic usage example: `from mc_logger.mcp import create_server`
- Add Claude Desktop integration example with JSON config and env vars
- Document all 5 MCP tools with parameters and return types
- Document all 5 MCP resources with URI patterns
- Document all 5 MCP prompts with arguments
- Add note about zero breaking changes and optional nature

### Step 13: Create docs/mcp_server.md Comprehensive Guide
- Add detailed server setup instructions for both CLI and programmatic usage
- Document integration guides for Claude Desktop, Cursor, and generic MCP clients
- Create environment variable reference table with descriptions and defaults
- Document advanced configuration options (custom transports, ports, database paths)
- Add troubleshooting section:
  - Import errors when fastmcp not installed
  - Connection issues with Claude Desktop
  - Database path problems
  - Permission issues
- Add examples of using tools, resources, and prompts from AI assistants

### Step 14: Create examples/mcp_server_example.py
- Standalone example showing programmatic MCP server usage
- Configure logger with temp database
- Create and run MCP server
- Add comments explaining each step

### Step 15: Create examples/claude_desktop_config.json
- Complete Claude Desktop configuration example
- Show environment variable usage for MC_LOGGER_DB_PATH and MC_LOGGER_FLUSH_INTERVAL
- Add comments (as JSON allows) explaining configuration options

### Step 16: Create examples/mcp_client_example.py
- Example showing how to use MC Logger MCP server from a client
- Demonstrate calling tools, reading resources, and using prompts
- Show error handling and connection management

### Step 17: Update CHANGELOG.md
- Add new version section (e.g., "## [0.2.0] - 2025-01-XX")
- Document new optional feature: MCP server support via `[mcp]` extra
- List all 5 MCP tools, 5 resources, and 5 prompts
- Emphasize zero breaking changes
- Add installation examples and usage examples
- Note CLI command `mc-logger-mcp` added

### Step 18: Manual Testing with Claude Desktop
- Install mc-logger with `[mcp]` extra: `uv add ".[mcp]"`
- Add to `~/Library/Application Support/Claude/claude_desktop_config.json` with environment variables
- Restart Claude Desktop and verify server appears in MCP section
- Test each of the 5 tools with various parameters
- Test each of the 5 resources with valid URIs
- Test prompts generate useful debugging workflows
- Verify error messages are helpful when things go wrong
- Test that logs are correctly queried and displayed

### Step 19: Manual Testing with FastMCP CLI
- Test stdio transport: `fastmcp run mc_logger.mcp:mcp`
- Test HTTP transport: `fastmcp run mc_logger.mcp:mcp --transport http --port 8000`
- Test CLI command: `mc-logger-mcp --db-path ./test.db`
- Test environment variables: `export MC_LOGGER_DB_PATH=/tmp/logs.db && mc-logger-mcp`
- Verify tools are callable and return expected results
- Test resources are accessible via URI patterns
- Test prompts generate valid message lists

### Step 20: Validate Import Guard Behavior
- Test that importing mc_logger.mcp without fastmcp installed raises helpful ImportError
- Test that error message includes installation instructions
- Test that core mc_logger functionality works without `[mcp]` extra
- Verify no FastMCP code is imported when using only core features

### Step 21: Run All Validation Commands
- Run core tests without MCP: `uv run pytest tests/ -v --ignore=tests/test_mcp_*.py`
- Install MCP extra: `uv add ".[mcp]"`
- Run all tests including MCP: `uv run pytest tests/ -v`
- Verify all tests pass with zero failures
- Test example app: `uv run python examples/fastapi_app.py` (verify no regressions)
- Test MCP server example: `uv run python examples/mcp_server_example.py`
- Run linting: `uv run ruff check mc_logger/` (if ruff is available)
- Verify package builds: `uv build`

## Testing Strategy

### Unit Tests
- **test_mcp_server.py**: Test server creation, tool registration, and schema validation
- **test_mcp_resources.py**: Test resource registration, URI patterns, and content generation
- **test_mcp_prompts.py**: Test prompt registration, argument handling, and message generation
- All tests use `pytest.importorskip("fastmcp")` to gracefully skip when FastMCP not installed

### Integration Tests
- **test_mcp_integration.py**: End-to-end tests with temp database
  - Test all 5 tools return correct results with real data
  - Test all 5 resources provide correct data
  - Test all 5 prompts generate useful messages
  - Test error handling for invalid parameters
  - Test configuration updates via `configure_logger` tool

### Edge Cases
- **Import without FastMCP**: Verify helpful error message when importing `mc_logger.mcp` without fastmcp installed
- **Empty database**: Test tools/resources handle empty database gracefully
- **Invalid time ranges**: Test `parse_time_range()` handles malformed input
- **Non-existent request IDs**: Test `get_request_trace` returns "No logs found" message
- **Invalid resource URIs**: Test resources return appropriate errors for malformed URIs
- **Concurrent access**: Verify MCP server can handle multiple concurrent tool calls
- **Large result sets**: Test resources handle databases with 10,000+ log entries
- **Missing environment variables**: Test CLI uses defaults when env vars not set
- **CLI argument precedence**: Verify CLI args override environment variables

## Acceptance Criteria
- [ ] Users can install with `uv add "mc-logger[mcp]"` or `pip install "mc-logger[mcp]"`
- [ ] Import guard raises helpful ImportError with installation instructions when fastmcp not installed
- [ ] All 5 MCP tools are registered and work correctly (query_logs, get_request_trace, summarize_logs, mark_session, configure_logger)
- [ ] All 5 MCP resources are accessible and return valid data (logs://recent, logs://request/{id}, logs://session/{id}, logs://errors, logs://source/{source})
- [ ] All 5 MCP prompts generate useful debugging workflows
- [ ] Environment variables configure server correctly (MC_LOGGER_DB_PATH, MC_LOGGER_FLUSH_INTERVAL, MC_LOGGER_TRANSPORT, MC_LOGGER_PORT)
- [ ] CLI command `mc-logger-mcp` runs server with stdio and HTTP transports
- [ ] CLI arguments override environment variables (correct precedence)
- [ ] Works with Claude Desktop when added to config file
- [ ] All tests pass with `[mcp]` extra installed
- [ ] All core tests pass without `[mcp]` extra (no regressions)
- [ ] Documentation complete and accurate (README, docs/mcp_server.md, CHANGELOG)
- [ ] No new required dependencies added to core package
- [ ] Zero breaking changes for existing users
- [ ] Examples work correctly (mcp_server_example.py, claude_desktop_config.json, mcp_client_example.py)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd /Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/mc_logger` - Change to project directory
- `uv run pytest tests/ -v --ignore=tests/test_mcp_*.py` - Run core tests WITHOUT MCP (verify no regressions)
- `uv add ".[mcp]"` - Install MCP extra for testing
- `uv run pytest tests/ -v` - Run ALL tests including MCP tests (should all pass)
- `uv run pytest tests/test_mcp_server.py -v` - Run MCP server tests specifically
- `uv run pytest tests/test_mcp_resources.py -v` - Run MCP resources tests specifically
- `uv run pytest tests/test_mcp_prompts.py -v` - Run MCP prompts tests specifically
- `uv run pytest tests/test_mcp_integration.py -v` - Run MCP integration tests specifically
- `uv run python examples/fastapi_app.py &` - Start example app in background (verify no regressions)
- `sleep 2 && curl http://localhost:8000/` - Test example app endpoint
- `pkill -f "python examples/fastapi_app.py"` - Stop example app
- `uv run python examples/mcp_server_example.py` - Test MCP server example (should not crash)
- `mc-logger-mcp --help` - Verify CLI command installed correctly
- `uv build` - Verify package builds without errors
- `python -c "import mc_logger; print(mc_logger.__version__)"` - Verify core import works
- `python -c "from mc_logger.mcp import create_server; print('MCP import successful')"` - Verify MCP import works with extra installed

## Notes

### Design Decisions
1. **Separate Module Approach**: All MCP code lives in `mc_logger/mcp/` to maintain clean separation from core logging functionality. This makes testing easier and prevents accidental dependencies.

2. **Wrapper Pattern**: MCP tools wrap existing `mcp_tools.py` functions rather than duplicating logic. This ensures consistency and reduces maintenance burden.

3. **Import Guards**: Use try/except to catch ImportError when fastmcp not installed, with helpful error messages directing users to install the `[mcp]` extra.

4. **Environment Variable Support**: Critical for Docker containers and Claude Desktop integration. CLI arguments override env vars for flexibility.

5. **Professional Pattern**: Follows the same optional dependency pattern as popular libraries like `pydantic-ai[anthropic]`, `httpx[http2]`, and `sqlalchemy[asyncio]`.

### Future Enhancements
- **Custom Resources**: Allow users to register custom resource URIs for application-specific log views
- **Authentication**: Add optional authentication for HTTP transport (API keys, JWT)
- **Streaming Resources**: Support server-sent events for real-time log streaming
- **Advanced Prompts**: Add more sophisticated debugging workflows (e.g., anomaly detection, correlation analysis)
- **Metrics**: Add MCP tools for querying performance metrics and statistics
- **Multi-Database**: Support querying multiple log databases simultaneously

### Dependencies Added
- **fastmcp>=2.11.0** (optional, only with `[mcp]` extra)
- No new required dependencies

### Known Limitations
- MCP server currently reads from SQLite only (no support for other backends yet)
- Resources are read-only (no write operations via MCP)
- HTTP transport doesn't include authentication (use stdio for Claude Desktop)
- Large result sets may cause performance issues (use `limit` parameter)

### Related Documentation
- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Python Packaging - Optional Dependencies](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [FastMCP Resources](https://gofastmcp.com/servers/resources.md)
- [FastMCP Prompts](https://gofastmcp.com/servers/prompts.md)
