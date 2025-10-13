# ABOUTME: MCP prompts providing debugging workflow templates for AI assistants.
# ABOUTME: Provides 5 prompts for common debugging scenarios: error investigation, performance analysis, pattern finding, etc.

"""MCP prompts for MC Logger

Provides debugging workflow templates that guide AI assistants through
common log analysis scenarios. Each prompt returns structured messages
with instructions and example queries.
"""

from typing import List

from fastmcp.prompts import Message

from mc_logger.mcp.server import mcp


@mcp.prompt()
def debug_error_in_request(request_id: str) -> List[Message]:
    """Multi-step debugging workflow for investigating an error in a specific request.

    Args:
        request_id: The request ID that encountered an error

    Returns:
        List of messages guiding the debugging process
    """
    return [
        Message(
            role="user",
            content=f"""I need to debug an error in request {request_id}. Let's investigate systematically:

1. First, get the complete request trace:
   get_request_trace("{request_id}")

2. Look for ERROR level entries and examine their metadata for:
   - Stack traces
   - Error messages
   - Request parameters that might have caused the issue

3. Check for WARNING entries immediately before the error:
   query_logs(request_id="{request_id}", level="WARNING")

4. If there are related requests (same session_id), check those for patterns:
   summarize_logs(session_id="<session_id_from_trace>")

5. Finally, suggest the root cause and potential fixes based on the log evidence.
""",
        )
    ]


@mcp.prompt()
def investigate_slow_requests(time_range: str = "10m", threshold_ms: int = 1000) -> List[Message]:
    """Performance analysis workflow for finding and diagnosing slow requests.

    Args:
        time_range: Time range to analyze (default: "10m")
        threshold_ms: Threshold in milliseconds to consider a request slow (default: 1000)

    Returns:
        List of messages guiding the performance analysis
    """
    return [
        Message(
            role="user",
            content=f"""I need to investigate slow requests in the last {time_range}. Performance threshold: {threshold_ms}ms.

1. First, get all requests from the time range:
   summarize_logs(time_range="{time_range}")

2. Look for request.complete entries and check their metadata for duration:
   query_logs(time_range="{time_range}", source="middleware", limit=500)

3. For each request that took longer than {threshold_ms}ms:
   - Get the full trace: get_request_trace("<request_id>")
   - Look for slow operations (database queries, API calls, etc.)
   - Check if there are multiple requests to the same endpoint

4. Identify patterns:
   - Are slow requests hitting the same endpoint?
   - Are they happening at the same time (load spike)?
   - Do they have common parameters or headers?

5. Summarize findings with recommendations for optimization.
""",
        )
    ]


@mcp.prompt()
def find_error_patterns(time_range: str = "1h") -> List[Message]:
    """Error correlation analysis workflow for identifying patterns in failures.

    Args:
        time_range: Time range to analyze (default: "1h")

    Returns:
        List of messages guiding the pattern analysis
    """
    return [
        Message(
            role="user",
            content=f"""I need to find error patterns in the last {time_range}.

1. First, get all ERROR level logs:
   query_logs(time_range="{time_range}", level="ERROR", limit=1000)

2. Group errors by:
   - Error message (similar messages indicate same root cause)
   - Source (which component is failing)
   - Time distribution (are errors clustered or spread out)

3. For the most common error type:
   - Get a sample request trace: get_request_trace("<request_id>")
   - Look for common metadata or request parameters

4. Check if there are correlated WARNING messages:
   query_logs(time_range="{time_range}", level="WARNING", limit=1000)

5. Summarize:
   - Most frequent error types
   - Affected endpoints/sources
   - Potential root causes
   - Recommended fixes

6. If errors are clustered in time, check for:
   - Deployment events
   - Infrastructure issues
   - Sudden load spikes
""",
        )
    ]


@mcp.prompt()
def trace_request_flow(request_id: str) -> List[Message]:
    """Complete request journey visualization from entry to completion.

    Args:
        request_id: The request ID to trace

    Returns:
        List of messages guiding the trace visualization
    """
    return [
        Message(
            role="user",
            content=f"""I need to visualize the complete flow for request {request_id}.

1. Get the full timeline:
   get_request_trace("{request_id}")

2. Analyze the flow:
   - Entry point (request.start)
   - Middleware processing
   - Application logic
   - Database/API calls
   - Response generation
   - Exit point (request.complete or request.error)

3. Calculate timing for each phase:
   - Time between request.start and first application log
   - Time for each major operation
   - Total request duration

4. Identify bottlenecks:
   - Which operations took the longest?
   - Are there unnecessary sequential operations that could be parallel?
   - Any redundant database queries?

5. Create a visual timeline showing:
   - Each event with timestamp offset from request start
   - Duration of key operations
   - Warnings or errors encountered

6. Provide optimization recommendations if applicable.
""",
        )
    ]


@mcp.prompt()
def compare_sessions(session_id_1: str, session_id_2: str) -> List[Message]:
    """Session diff analysis guide for comparing two user sessions.

    Args:
        session_id_1: First session ID to compare
        session_id_2: Second session ID to compare

    Returns:
        List of messages guiding the session comparison
    """
    return [
        Message(
            role="user",
            content=f"""I need to compare two sessions to understand their differences.

Session 1: {session_id_1}
Session 2: {session_id_2}

1. Get summaries for both sessions:
   summarize_logs(session_id="{session_id_1}")
   summarize_logs(session_id="{session_id_2}")

2. Compare high-level metrics:
   - Total number of requests
   - Error rate
   - Most common log sources
   - Duration of session

3. Identify behavioral differences:
   - Did one session hit different endpoints?
   - Did one encounter errors the other didn't?
   - Are there timing differences?

4. For any significant differences, drill down:
   - Get example traces from each session
   - Compare request parameters and metadata
   - Look for environmental differences

5. Summarize:
   - Key differences between sessions
   - Possible reasons for differences
   - Whether one session represents expected behavior
   - Recommendations for investigation
""",
        )
    ]
