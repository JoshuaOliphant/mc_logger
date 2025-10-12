# ABOUTME: Public API exports for MC Logger package
# ABOUTME: Provides Logger, configuration, and instrumentation utilities

"""MC Logger - Unified semantic logging system optimized for AI-assisted debugging."""

__version__ = "0.1.0"

from mc_logger.core import Logger, get_logger, configure
from mc_logger.models import LogEntry
from mc_logger.middleware import instrument_fastapi

__all__ = [
    "Logger",
    "get_logger",
    "configure",
    "LogEntry",
    "instrument_fastapi",
    "__version__",
]
