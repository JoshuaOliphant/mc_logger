# MC Logger MCP Server Guide

Comprehensive guide for running MC Logger as a Model Context Protocol (MCP) server.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Server Setup](#server-setup)
- [Integration Guides](#integration-guides)
- [Environment Variables](#environment-variables)
- [Security Considerations](#security-considerations)
- [Tools Reference](#tools-reference)
- [Resources Reference](#resources-reference)
- [Prompts Reference](#prompts-reference)
- [Troubleshooting](#troubleshooting)

## Overview

MC Logger's MCP server provides standardized tools, resources, and prompts that AI assistants can use to query and analyze logs. This enables AI assistants to independently investigate production issues without requiring developers to manually aggregate data.

**Key Benefits:**

- AI assistants can directly query your logs
- Standardized protocol works with Claude Desktop, Cursor, and other MCP clients
- Optional feature - zero impact on core logging functionality
- Environment variable configuration for Docker and desktop integration

## Installation

### Install with MCP Extra

```bash
# Using uv (recommended)
uv add "mc-logger[mcp]"

# Using pip
pip install "mc-logger[mcp]"
```

### Verify Installation

```bash
# Check that FastMCP is installed
python -c "from mc_logger.mcp import create_server; print('MCP server installed successfully')"

# Check CLI command
mc-logger-mcp --help
```

## Server Setup

### CLI Usage (Stdio Transport)

The stdio transport is ideal for Claude Desktop and other desktop AI assistants:

```bash
# Start with default settings
mc-logger-mcp

# Specify database path
mc-logger-mcp --db-path /var/log/app.db

# Configure flush interval
mc-logger-mcp --flush-interval 2.0
```

### CLI Usage (HTTP Transport)

The HTTP transport allows network access for remote MCP clients:

```bash
# Start HTTP server on port 8000
mc-logger-mcp --transport http --port 8000

# Start on custom port
mc-logger-mcp --transport http --port 3000
```

### Programmatic Usage

For advanced use cases, you can start the server programmatically:

```python
from mc_logger import configure
from mc_logger.mcp import mcp

# Configure logger first
configure(db_path="./logs.db", flush_interval=1.0)

# Run MCP server with stdio transport
mcp.run()

# Or with HTTP transport
# mcp.run(transport="http", port=8000)
```

### FastMCP Run Command

You can also use FastMCP's CLI directly:

```bash
# Stdio transport
fastmcp run mc_logger.mcp:mcp

# HTTP transport
fastmcp run mc_logger.mcp:mcp --transport http --port 8000
```

## Integration Guides

### Claude Desktop

Claude Desktop is the primary use case for the stdio transport.

#### Step 1: Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "mc-logger": {
      "command": "mc-logger-mcp",
      "env": {
        "MC_LOGGER_DB_PATH": "/path/to/your/logs.db",
        "MC_LOGGER_FLUSH_INTERVAL": "1.0"
      }
    }
  }
}
```

#### Step 2: Restart Claude Desktop

Close and reopen Claude Desktop. The MCP server will start automatically.

#### Step 3: Verify Integration

In Claude Desktop:

1. Look for the MCP tools icon (🔌) in the interface
2. You should see "mc-logger" listed as an available server
3. Available tools: query_logs, get_request_trace, summarize_logs, mark_session, configure_logger

#### Step 4: Test the Integration

Ask Claude:

> "Can you query the mc-logger database for any ERROR level logs in the last hour?"

Claude should use the `query_logs` tool to fetch and analyze the errors.

### Cursor IDE

Cursor supports MCP servers similarly to Claude Desktop.

#### Configuration

Add to Cursor's MCP configuration:

```json
{
  "mcpServers": {
    "mc-logger": {
      "command": "mc-logger-mcp",
      "env": {
        "MC_LOGGER_DB_PATH": "${workspaceFolder}/logs.db"
      }
    }
  }
}
```

### Generic MCP Clients

For other MCP clients that support stdio transport:

```bash
# Start the server
mc-logger-mcp

# The server will communicate via stdin/stdout using JSON-RPC
```

For HTTP-based clients:

```bash
# Start HTTP server
mc-logger-mcp --transport http --port 8000

# Connect to http://localhost:8000
```

## Environment Variables

MC Logger MCP server supports configuration via environment variables, which is especially useful for Docker containers and desktop integration.

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MC_LOGGER_DB_PATH` | Path to SQLite database file | `./mc_logger.db` | `/var/log/app.db` |
| `MC_LOGGER_FLUSH_INTERVAL` | Seconds between queue flushes | `1.0` | `2.0` |
| `MC_LOGGER_TRANSPORT` | Transport mode (stdio or http) | `stdio` | `http` |
| `MC_LOGGER_PORT` | Port for HTTP transport | `8000` | `3000` |

### Precedence

Configuration follows this precedence (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Default values

### Examples

```bash
# Set via environment
export MC_LOGGER_DB_PATH=/var/log/app.db
export MC_LOGGER_FLUSH_INTERVAL=2.0
mc-logger-mcp

# Override with CLI arguments
mc-logger-mcp --db-path /tmp/logs.db  # Overrides env var

# Docker example
docker run -e MC_LOGGER_DB_PATH=/data/logs.db myapp
```

## Security Considerations

### Transport Security

MC Logger MCP server supports two transport modes with different security profiles:

#### Stdio Transport (Default - Recommended for Local Use)

The stdio transport communicates via standard input/output and is designed for **local desktop use only**:

- **Use cases**: Claude Desktop, Cursor IDE, local development
- **Security**: Process-level isolation, no network exposure
- **Authentication**: Managed by the parent application (Claude Desktop, etc.)
- **Recommended for**: Development, local debugging, desktop AI assistants

```bash
# Safe for local use
mc-logger-mcp  # Uses stdio by default
```

#### HTTP Transport (Network Exposure)

The HTTP transport exposes the server over the network and requires additional security measures:

**⚠️ WARNING**: HTTP transport has NO built-in authentication or encryption. Only use in trusted networks.

**Recommended deployment patterns**:

1. **Localhost only** (Development/Testing):
   ```bash
   # Bind to localhost only
   mc-logger-mcp --transport http --port 8000
   ```
   - Access: `http://localhost:8000`
   - Security: Only accessible from the same machine
   - Use case: Local development, testing

2. **Private network** (Internal tools):
   ```bash
   # Behind a firewall or VPN
   mc-logger-mcp --transport http --port 8000
   ```
   - Access: Within private network only
   - Security: Network-level isolation (firewall, VPN)
   - Use case: Internal debugging tools, team collaboration
   - **Required**: Firewall rules, VPN, or network segmentation

3. **Production deployment** (NOT RECOMMENDED without additional security):

   If you must expose the HTTP server in production:

   - **Use a reverse proxy** (nginx, Caddy) with:
     - TLS/HTTPS encryption
     - Authentication (API keys, OAuth, mTLS)
     - Rate limiting
     - IP allowlisting

   - **Example nginx configuration**:
     ```nginx
     server {
         listen 443 ssl;
         server_name logs.internal.example.com;

         ssl_certificate /path/to/cert.pem;
         ssl_certificate_key /path/to/key.pem;

         # Require API key
         if ($http_x_api_key != "your-secret-key") {
             return 401;
         }

         location / {
             proxy_pass http://localhost:8000;
         }
     }
     ```

### Data Exposure Risks

MC Logger provides **read-only** access to log data, which may contain sensitive information:

**Potential sensitive data in logs**:
- Request IDs and session IDs
- User metadata (IPs, user agents, etc.)
- Error stack traces (may expose code structure)
- Request parameters (may contain PII)
- API endpoint paths and timing information

**Mitigation strategies**:

1. **Sanitize logs before writing**:
   ```python
   # In your application, redact sensitive data
   from mc_logger import get_logger

   logger = get_logger()
   # Don't log raw passwords, tokens, etc.
   logger.log("INFO", "User login", metadata={
       "user_id": user_id,  # OK
       "ip": anonymize_ip(request.ip),  # Anonymized
       # "password": password  # NEVER log this!
   })
   ```

2. **Restrict database file access**:
   ```bash
   # Set restrictive permissions
   chmod 640 /var/log/app.db
   chown app:app /var/log/app.db
   ```

3. **Use separate databases for different sensitivity levels**:
   ```json
   {
     "mcpServers": {
       "mc-logger-app": {
         "command": "mc-logger-mcp",
         "env": {"MC_LOGGER_DB_PATH": "/var/log/app.db"}
       },
       "mc-logger-audit": {
         "command": "mc-logger-mcp",
         "env": {"MC_LOGGER_DB_PATH": "/var/log/audit.db"}
       }
     }
   }
   ```

### Desktop Integration Security

When integrating with Claude Desktop or Cursor IDE:

**✅ Security benefits**:
- No network exposure (stdio transport)
- Application-managed authentication
- Process-level isolation

**⚠️ Considerations**:
- AI assistant has **read access** to all logs in the database
- Ensure log database doesn't contain credentials or secrets
- Consider using time-limited database files (rotate/archive old logs)

### Environment Variable Security

**Best practices for environment variables**:

1. **Don't commit secrets to version control**:
   ```bash
   # Use .env files (add to .gitignore)
   echo "MC_LOGGER_DB_PATH=/secure/path/logs.db" >> .env.local
   ```

2. **Use absolute paths to prevent path traversal**:
   ```bash
   # Good
   export MC_LOGGER_DB_PATH=/var/log/app.db

   # Avoid (relative paths can be unpredictable)
   export MC_LOGGER_DB_PATH=../../logs.db
   ```

3. **In Docker, use secrets management**:
   ```bash
   # Docker secrets (Swarm)
   docker secret create mc_logger_db_path /path/to/db

   # Or environment variables from secure store
   docker run --env-file <(vault kv get -format=env mc-logger) myapp
   ```

### Deployment Checklist

Before deploying the MCP server:

- [ ] **Transport mode**: Use stdio for local, HTTP only in trusted networks
- [ ] **Authentication**: If using HTTP, implement authentication via reverse proxy
- [ ] **Encryption**: Use TLS/HTTPS for any network transport
- [ ] **Database permissions**: Restrict file access (chmod 640)
- [ ] **Log sanitization**: Ensure logs don't contain passwords, tokens, or PII
- [ ] **Network isolation**: Use firewall rules or VPN for HTTP transport
- [ ] **Monitoring**: Track MCP server access and query patterns
- [ ] **Rate limiting**: Implement rate limits to prevent abuse
- [ ] **Audit logging**: Log MCP server access for security auditing

### Reporting Security Issues

If you discover a security vulnerability in MC Logger's MCP server:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [your-security-email]
3. Include: Description, reproduction steps, potential impact
4. We will respond within 48 hours

## Tools Reference

### query_logs

Query logs with optional filters.

**Parameters:**

- `time_range` (optional): Time range like "5m", "2h", "1d"
- `request_id` (optional): Filter by request ID
- `session_id` (optional): Filter by session ID
- `level` (optional): Filter by log level (DEBUG, INFO, WARNING, ERROR)
- `source` (optional): Filter by source name
- `limit` (default: 1000): Maximum number of entries

**Returns:** List of log entry dictionaries

**Example:**

```python
# Query ERROR logs from last hour
query_logs(time_range="1h", level="ERROR")

# Query specific request
query_logs(request_id="abc123")

# Combined filters
query_logs(time_range="10m", source="api", level="WARNING", limit=50)
```

### get_request_trace

Get markdown-formatted timeline for a specific request.

**Parameters:**

- `request_id` (required): The request ID to trace

**Returns:** Markdown-formatted trace with timeline, duration, and events

**Example:**

```python
trace = get_request_trace("abc123")
# Returns:
# # Request Trace: abc123
# **Duration:** 245.67ms
# **Events:** 8
# ...
```

### summarize_logs

Generate markdown summary with statistics by level and source.

**Parameters:**

- `time_range` (optional): Time range like "5m", "2h", "1d"
- `request_id` (optional): Filter by request ID
- `session_id` (optional): Filter by session ID

**Returns:** Markdown-formatted summary with event counts

**Example:**

```python
summary = summarize_logs(time_range="1h")
# Returns:
# # Log Summary
# **Total Events:** 1,234
# ## Events by Level
# - **INFO**: 1,000
# ...
```

### mark_session

Mark a session as important for preservation.

**Parameters:**

- `session_id` (required): The session ID to mark
- `start_time` (optional): Start time in format "5m", "2h", "1d" ago
- `end_time` (optional): End time in format "5m", "2h", "1d" ago

**Returns:** Confirmation message

**Example:**

```python
mark_session("sess123", start_time="1h", end_time="30m")
```

### configure_logger

Configure the MC Logger instance.

**Parameters:**

- `db_path` (default: "./mc_logger.db"): Path to SQLite database
- `flush_interval` (default: 1.0): Seconds between queue flushes

**Returns:** Confirmation message

**Example:**

```python
configure_logger(db_path="/var/log/app.db", flush_interval=2.0)
```

## Resources Reference

Resources provide streaming/templated access to log data via URI patterns.

### logs://recent

Get logs from the last 5 minutes as JSON array.

**Example:**

```
logs://recent
```

### logs://request/{request_id}

Get all logs for a specific request ID as JSON array.

**Example:**

```
logs://request/abc123
```

### logs://session/{session_id}

Get all logs for a specific session ID as JSON array.

**Example:**

```
logs://session/sess123
```

### logs://errors

Get ERROR level logs from the last 5 minutes as JSON array.

**Example:**

```
logs://errors
```

### logs://source/{source}

Get logs from a specific source in the last 5 minutes as JSON array.

**Example:**

```
logs://source/api
logs://source/middleware
```

## Prompts Reference

Prompts provide debugging workflow templates that guide AI assistants through common scenarios.

### debug_error_in_request

Multi-step workflow for investigating an error in a specific request.

**Parameters:**

- `request_id` (required): The request ID with the error

**Workflow:**

1. Get complete request trace
2. Examine ERROR entries and metadata
3. Check for WARNING entries before the error
4. Look for patterns in related requests
5. Suggest root cause and fixes

### investigate_slow_requests

Performance analysis workflow for finding and diagnosing slow requests.

**Parameters:**

- `time_range` (default: "10m"): Time range to analyze
- `threshold_ms` (default: 1000): Threshold to consider request slow

**Workflow:**

1. Get all requests from time range
2. Filter for requests exceeding threshold
3. Get full traces for slow requests
4. Identify patterns (same endpoint, load spikes, etc.)
5. Provide optimization recommendations

### find_error_patterns

Error correlation analysis for identifying patterns in failures.

**Parameters:**

- `time_range` (default: "1h"): Time range to analyze

**Workflow:**

1. Get all ERROR level logs
2. Group by message, source, and time distribution
3. Get sample traces for common errors
4. Check for correlated WARNING messages
5. Summarize patterns and root causes

### trace_request_flow

Complete request journey visualization from entry to completion.

**Parameters:**

- `request_id` (required): The request ID to trace

**Workflow:**

1. Get full timeline
2. Analyze flow phases (middleware, application, database, etc.)
3. Calculate timing for each phase
4. Identify bottlenecks
5. Create visual timeline
6. Provide optimization recommendations

### compare_sessions

Session diff analysis for comparing two user sessions.

**Parameters:**

- `session_id_1` (required): First session ID
- `session_id_2` (required): Second session ID

**Workflow:**

1. Get summaries for both sessions
2. Compare high-level metrics
3. Identify behavioral differences
4. Drill down into specific differences
5. Summarize findings

## Troubleshooting

### Import Error: FastMCP Not Installed

**Error:**

```
ImportError: MC Logger MCP server requires FastMCP.
Install with: uv add 'mc-logger[mcp]' or pip install 'mc-logger[mcp]'
```

**Solution:**

```bash
uv add "mc-logger[mcp]"
# or
pip install "mc-logger[mcp]"
```

### Claude Desktop Not Detecting Server

**Symptoms:**

- MCP tools icon doesn't show mc-logger
- Server not listed in available servers

**Solutions:**

1. Check config file path:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Verify JSON syntax is valid (use a JSON validator)

3. Check that `mc-logger-mcp` command works:
   ```bash
   mc-logger-mcp --help
   ```

4. Check Claude Desktop logs (usually in `~/Library/Logs/Claude/`)

5. Restart Claude Desktop completely (quit and reopen)

### Database Path Issues

**Symptoms:**

- Server starts but can't find database
- Permission denied errors

**Solutions:**

1. Use absolute paths in configuration:
   ```json
   "MC_LOGGER_DB_PATH": "/full/path/to/logs.db"
   ```

2. Ensure directory exists:
   ```bash
   mkdir -p /path/to/logs
   ```

3. Check permissions:
   ```bash
   ls -la /path/to/logs.db
   chmod 644 /path/to/logs.db  # If needed
   ```

### Connection Refused (HTTP Transport)

**Symptoms:**

- Can't connect to HTTP server
- Connection refused errors

**Solutions:**

1. Check server is running:
   ```bash
   mc-logger-mcp --transport http --port 8000
   ```

2. Verify port is not in use:
   ```bash
   lsof -i :8000
   ```

3. Check firewall settings

4. Try different port:
   ```bash
   mc-logger-mcp --transport http --port 3000
   ```

### Empty Results from Tools

**Symptoms:**

- Tools return "No logs found"
- Empty arrays from resources

**Solutions:**

1. Verify database has data:
   ```python
   from mc_logger import get_logger
   logger = get_logger()
   entries = logger.query(limit=10)
   print(f"Found {len(entries)} entries")
   ```

2. Check time range (logs might be older):
   ```python
   query_logs(time_range="24h")  # Try larger range
   ```

3. Verify database path is correct:
   ```bash
   echo $MC_LOGGER_DB_PATH
   ls -la $MC_LOGGER_DB_PATH
   ```

4. Check that logger is configured:
   ```python
   from mc_logger import configure
   configure(db_path="/path/to/logs.db", force=True)
   ```

### Performance Issues

**Symptoms:**

- Slow query responses
- High memory usage

**Solutions:**

1. Reduce query limits:
   ```python
   query_logs(limit=100)  # Instead of 1000
   ```

2. Use more specific filters:
   ```python
   query_logs(request_id="abc", level="ERROR")  # Instead of no filters
   ```

3. Increase flush interval to reduce disk writes:
   ```bash
   mc-logger-mcp --flush-interval 5.0
   ```

4. Check database size:
   ```bash
   du -h /path/to/logs.db
   ```

5. Consider database cleanup/archival for very large databases

## Advanced Configuration

### Custom Transport

For custom transport implementations:

```python
from mc_logger.mcp import create_server

server = create_server()
# Use FastMCP's custom transport options
```

### Multiple Databases

To query multiple databases, start multiple MCP servers:

```json
{
  "mcpServers": {
    "mc-logger-prod": {
      "command": "mc-logger-mcp",
      "env": {
        "MC_LOGGER_DB_PATH": "/var/log/prod.db"
      }
    },
    "mc-logger-staging": {
      "command": "mc-logger-mcp",
      "env": {
        "MC_LOGGER_DB_PATH": "/var/log/staging.db"
      }
    }
  }
}
```

### Docker Integration

Example Dockerfile:

```dockerfile
FROM python:3.11-slim

RUN pip install "mc-logger[mcp]"

ENV MC_LOGGER_DB_PATH=/data/logs.db
ENV MC_LOGGER_FLUSH_INTERVAL=2.0

CMD ["mc-logger-mcp", "--transport", "http", "--port", "8000"]
```

Run container:

```bash
docker run -v /path/to/logs:/data -p 8000:8000 mc-logger-mcp
```

## Support

For issues, questions, or feature requests:

- GitHub Issues: https://github.com/your-org/mc-logger/issues
- Documentation: https://github.com/your-org/mc-logger/docs

## Related Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)
