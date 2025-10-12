# ABOUTME: Async-safe context management using contextvars
# ABOUTME: Tracks request_id, session_id, and correlation_id across async boundaries

"""Context management for request/session/correlation tracking."""

import secrets
from contextvars import ContextVar, Token
from typing import Optional


# Context variables for async-safe storage
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def generate_id() -> str:
    """Generate a unique 8-character ID."""
    return secrets.token_hex(4)


def set_request_id(request_id: Optional[str] = None) -> Token:
    """Set request ID in context, generating one if not provided."""
    if request_id is None:
        request_id = generate_id()
    return _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return _request_id.get()


def reset_request_id(token: Token) -> None:
    """Reset request ID to previous value using token."""
    _request_id.reset(token)


def set_session_id(session_id: Optional[str] = None) -> Token:
    """Set session ID in context, generating one if not provided."""
    if session_id is None:
        session_id = generate_id()
    return _session_id.set(session_id)


def get_session_id() -> Optional[str]:
    """Get current session ID from context."""
    return _session_id.get()


def reset_session_id(token: Token) -> None:
    """Reset session ID to previous value using token."""
    _session_id.reset(token)


def set_correlation_id(correlation_id: Optional[str] = None) -> Token:
    """Set correlation ID in context, generating one if not provided."""
    if correlation_id is None:
        correlation_id = generate_id()
    return _correlation_id.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return _correlation_id.get()


def reset_correlation_id(token: Token) -> None:
    """Reset correlation ID to previous value using token."""
    _correlation_id.reset(token)


def clear_context() -> None:
    """Clear all context variables for cleanup between tests."""
    _request_id.set(None)
    _session_id.set(None)
    _correlation_id.set(None)
