"""Tests for MCP prompts implementation.

Tests prompt registration, argument handling, and message generation.
Requires fastmcp to be installed (skip tests otherwise).
"""

import pytest

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp")

from mc_logger.mcp import mcp


def test_mcp_server_has_prompts():
    """Test that prompts are registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    assert len(prompts) >= 5


def test_debug_error_in_request_prompt_registered():
    """Test that debug_error_in_request prompt is registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt_names = [p.name for p in prompts]
    assert "debug_error_in_request" in prompt_names


def test_investigate_slow_requests_prompt_registered():
    """Test that investigate_slow_requests prompt is registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt_names = [p.name for p in prompts]
    assert "investigate_slow_requests" in prompt_names


def test_find_error_patterns_prompt_registered():
    """Test that find_error_patterns prompt is registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt_names = [p.name for p in prompts]
    assert "find_error_patterns" in prompt_names


def test_trace_request_flow_prompt_registered():
    """Test that trace_request_flow prompt is registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt_names = [p.name for p in prompts]
    assert "trace_request_flow" in prompt_names


def test_compare_sessions_prompt_registered():
    """Test that compare_sessions prompt is registered."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt_names = [p.name for p in prompts]
    assert "compare_sessions" in prompt_names


def test_debug_error_prompt_requires_request_id():
    """Test that debug_error_in_request prompt requires request_id parameter."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "debug_error_in_request")

    import inspect
    sig = inspect.signature(prompt.fn)
    params = list(sig.parameters.keys())

    assert "request_id" in params


def test_debug_error_prompt_returns_messages():
    """Test that debug_error_in_request prompt returns list of messages."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "debug_error_in_request")

    result = prompt.fn(request_id="test-123")

    assert isinstance(result, list)
    assert len(result) > 0
    # FastMCP Message objects have role and content
    assert hasattr(result[0], "role")
    assert hasattr(result[0], "content")


def test_investigate_slow_requests_prompt_has_optional_params():
    """Test that investigate_slow_requests has optional parameters."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "investigate_slow_requests")

    import inspect
    sig = inspect.signature(prompt.fn)

    # Check for time_range parameter
    assert "time_range" in sig.parameters
    # Check it has a default value
    assert sig.parameters["time_range"].default != inspect.Parameter.empty


def test_investigate_slow_requests_prompt_returns_messages():
    """Test that investigate_slow_requests returns messages."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "investigate_slow_requests")

    result = prompt.fn()

    assert isinstance(result, list)
    assert len(result) > 0


def test_find_error_patterns_prompt_returns_messages():
    """Test that find_error_patterns returns messages."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "find_error_patterns")

    result = prompt.fn()

    assert isinstance(result, list)
    assert len(result) > 0


def test_trace_request_flow_prompt_requires_request_id():
    """Test that trace_request_flow requires request_id parameter."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "trace_request_flow")

    import inspect
    sig = inspect.signature(prompt.fn)
    params = list(sig.parameters.keys())

    assert "request_id" in params


def test_trace_request_flow_prompt_returns_messages():
    """Test that trace_request_flow returns messages."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "trace_request_flow")

    result = prompt.fn(request_id="test-456")

    assert isinstance(result, list)
    assert len(result) > 0


def test_compare_sessions_prompt_requires_two_session_ids():
    """Test that compare_sessions requires two session_id parameters."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "compare_sessions")

    import inspect
    sig = inspect.signature(prompt.fn)
    params = list(sig.parameters.keys())

    assert "session_id_1" in params
    assert "session_id_2" in params


def test_compare_sessions_prompt_returns_messages():
    """Test that compare_sessions returns messages."""
    prompts = list(mcp._prompt_manager._prompts.values())
    prompt = next(p for p in prompts if p.name == "compare_sessions")

    result = prompt.fn(session_id_1="session-a", session_id_2="session-b")

    assert isinstance(result, list)
    assert len(result) > 0


def test_prompt_messages_have_content():
    """Test that all prompts return messages with non-empty content."""
    prompts = list(mcp._prompt_manager._prompts.values())
    for prompt in prompts:
        # Get the function signature to determine required params
        import inspect
        sig = inspect.signature(prompt.fn)

        # Create mock arguments for required parameters
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.default == inspect.Parameter.empty:
                # Required parameter - provide a test value
                kwargs[param_name] = f"test-{param_name}"

        # Call the prompt
        result = prompt.fn(**kwargs)

        assert isinstance(result, list)
        assert len(result) > 0

        # Check that messages have content
        for message in result:
            assert hasattr(message, "content")
            # FastMCP now uses TextContent objects instead of plain strings
            if isinstance(message.content, str):
                assert len(message.content) > 0
            else:
                # TextContent object has a text attribute
                assert hasattr(message.content, "text")
                assert isinstance(message.content.text, str)
                assert len(message.content.text) > 0
