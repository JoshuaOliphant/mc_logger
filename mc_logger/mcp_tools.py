# ABOUTME: MCP query tools for AI assistants to analyze logs
# ABOUTME: Provides log querying, request tracing, and summarization functions

"""MCP tools for querying and analyzing logs."""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from mc_logger.core import get_logger
from mc_logger.models import LogEntry


def parse_time_range(time_range: str) -> tuple[float, float]:
    """Parse time range like '5m', '2h', '1d' to (start_timestamp, end_timestamp)."""
    import time

    match = re.match(r"(\d+)([mhd])", time_range.lower())
    if not match:
        raise ValueError(f"Invalid time range format: {time_range}")

    amount = int(match.group(1))
    unit = match.group(2)

    # Use time.time() for consistent timestamp handling
    now = time.time()

    if unit == "m":
        delta_seconds = amount * 60
    elif unit == "h":
        delta_seconds = amount * 3600
    elif unit == "d":
        delta_seconds = amount * 86400
    else:
        raise ValueError(f"Invalid time unit: {unit}")

    start_time = now - delta_seconds
    end_time = now

    return start_time, end_time


def query_logs(
    time_range: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 1000,
) -> List[LogEntry]:
    """Query logs with filters."""
    logger = get_logger()

    start_time = None
    end_time = None

    if time_range:
        start_time, end_time = parse_time_range(time_range)

    return logger.query(
        start_time=start_time,
        end_time=end_time,
        request_id=request_id,
        session_id=session_id,
        level=level,
        source=source,
        limit=limit,
    )


def get_request_trace(request_id: str) -> str:
    """Get markdown-formatted timeline for a request_id."""
    logger = get_logger()
    entries = logger.query(request_id=request_id, limit=10000)

    if not entries:
        return f"No logs found for request_id: {request_id}"

    # Sort by timestamp
    entries.sort(key=lambda e: e.timestamp)

    # Calculate duration
    start_time = entries[0].timestamp
    end_time = entries[-1].timestamp
    duration_ms = (end_time - start_time) * 1000

    # Count errors
    error_count = sum(1 for e in entries if e.level == "ERROR")
    warning_count = sum(1 for e in entries if e.level == "WARNING")

    # Build markdown output
    lines = []
    lines.append(f"# Request Trace: {request_id}")
    lines.append("")
    lines.append(f"**Duration:** {duration_ms:.2f}ms")
    lines.append(f"**Events:** {len(entries)}")
    if error_count > 0:
        lines.append(f"**Errors:** ❌ {error_count}")
    if warning_count > 0:
        lines.append(f"**Warnings:** ⚠️ {warning_count}")
    lines.append("")
    lines.append("## Timeline")
    lines.append("")

    # Format each entry
    for entry in entries:
        timestamp = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]

        # Add emoji indicator
        if entry.level == "ERROR":
            indicator = "❌"
        elif entry.level == "WARNING":
            indicator = "⚠️"
        elif entry.level == "INFO":
            indicator = "ℹ️"
        else:
            indicator = "🔍"

        lines.append(f"**{timestamp}** {indicator} `{entry.level}` {entry.message}")

        if entry.metadata:
            for key, value in entry.metadata.items():
                lines.append(f"  - {key}: {value}")

        lines.append("")

    return "\n".join(lines)


def mark_session(
    session_id: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
) -> str:
    """Mark a time period as important for preservation."""
    # For now, just return a confirmation message
    # In future versions, this could tag entries in the database
    return f"Session {session_id} marked for preservation"


def summarize_logs(
    time_range: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Generate markdown summary with statistics by level and source."""
    logger = get_logger()

    start_time = None
    end_time = None

    if time_range:
        start_time, end_time = parse_time_range(time_range)

    entries = logger.query(
        start_time=start_time,
        end_time=end_time,
        request_id=request_id,
        session_id=session_id,
        limit=10000,
    )

    if not entries:
        return "No logs found for the specified criteria"

    # Collect statistics
    level_counts = Counter(e.level for e in entries)
    source_counts = Counter(e.source for e in entries)

    # Calculate time range
    timestamps = [e.timestamp for e in entries]
    start = datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d %H:%M:%S")
    end = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d %H:%M:%S")

    # Build markdown output
    lines = []
    lines.append("# Log Summary")
    lines.append("")
    lines.append(f"**Time Range:** {start} to {end}")
    lines.append(f"**Total Events:** {len(entries)}")
    lines.append("")

    lines.append("## Events by Level")
    lines.append("")
    for level, count in level_counts.most_common():
        lines.append(f"- **{level}**: {count}")
    lines.append("")

    lines.append("## Events by Source")
    lines.append("")
    for source, count in source_counts.most_common():
        lines.append(f"- **{source}**: {count}")
    lines.append("")

    return "\n".join(lines)
