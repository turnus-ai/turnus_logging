"""
Turnus Logging - Standalone logging library with context propagation

A flexible Python logging library with automatic context propagation and optional Sentry integration.

Features:
- Zero dependencies (core functionality)
- Thread & async safe context management via contextvars
- Custom log context injection with log_context()
- Optional Sentry integration with automatic enrichment
- Payload sanitization for safe logging

Quick Start:
    from turnus_logging import setup_logging, log_context

    # Setup once
    logger = setup_logging(
        service_name="my-app",
        log_level=logging.INFO,
    )

    # Use anywhere
    logger.info("Application started")

    # Add custom context
    with log_context(order_id='12345', step='payment'):
        logger.info("Processing order")  # Includes order_id and step
"""

# Re-export core context functions
from .context import (
    append_context,
    clear_context,
    get_context,
    log_context,
    set_context,
)

# Formatters and helpers
from .formatters import (
    ContextFormatter,
    get_compact_format,
    get_default_format,
    get_verbose_format,
)

# Sanitization
from .sanitizer import (
    get_payload_summary,
    sanitize_payload,
    sanitize_request_payload,
    sanitize_response_metadata,
)

# Setup
from .config import (
    setup_logging,
    get_logger,
)

# Note: These will be added in subsequent steps
# from .middleware import RequestContextMiddleware, UserContextMiddleware
# from .integrations import send_sqs_message, put_events

__all__ = [
    # Context management
    'get_context',
    'set_context',
    'append_context',
    'clear_context',
    'log_context',
    # Formatters
    'ContextFormatter',
    'get_default_format',
    'get_compact_format',
    'get_verbose_format',
    # Setup
    'setup_logging',
    'get_logger',
    # Sanitization
    'sanitize_payload',
    'sanitize_request_payload',
    'sanitize_response_metadata',
    'get_payload_summary',
    # Middleware (optional, will fail gracefully if framework not installed)
]

# Middleware is imported on-demand to avoid requiring web frameworks

__version__ = '0.1.0'
