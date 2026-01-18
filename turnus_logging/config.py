"""
Logging setup and configuration.
"""

import logging
import sys
from typing import Optional, Dict, Any

from .formatters import ContextFormatter, get_default_format
from .context import set_context, get_context


def setup_logging(
    service_name: Optional[str] = None,
    log_level: Optional[int] = None,
    console_format: Optional[str] = None,
    enable_console: bool = True,
    sentry: Optional[Dict[str, Any]] = None,
    config_file: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logging with optional Sentry integration.
    
    Supports configuration from:
    1. Function parameters (highest priority)
    2. Config file (JSON)
    3. Environment variables (lowest priority)
    
    Args:
        service_name: Name of the service/logger
        log_level: Minimum log level
        console_format: Custom format string
        enable_console: Enable console output (useful to disable in production)
        sentry: Sentry configuration dict with keys:
            - dsn: Sentry DSN (or use SENTRY_DSN env var)
            - environment: Environment name (or use SENTRY_ENVIRONMENT env var)
            - event_level: Log level for Sentry events (default: ERROR)
            - breadcrumb_level: Log level for breadcrumbs (default: INFO)
        config_file: Path to JSON config file (optional, auto-discovers if not provided)
    
    Returns:
        Configured logger instance
    """
    # Load config from file/env if not all params provided
    if service_name is None or log_level is None or sentry is None:
        from .config_loader import load_logging_config
        config = load_logging_config(config_file)
        
        service_name = service_name or config.get('service_name', 'turnus_ai')
        log_level = log_level or getattr(logging, config.get('log_level', 'INFO'))
        sentry = sentry or config.get('sentry')
    
    # Default values if still None
    service_name = service_name or 'turnus_ai'
    log_level = log_level or logging.INFO
    # Set service_name in global context so it appears in all logs
    current_context = get_context() or {}
    current_context['service'] = service_name
    set_context(current_context)
    
    # Get or create the root logger to ensure all loggers inherit config
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Also configure the named logger
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)

    # Clear any existing handlers (idempotent setup)
    root_logger.handlers.clear()
    logger.handlers.clear()

    # Console handler with context formatting
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Use custom format or default
        format_string = console_format or get_default_format()
        console_formatter = ContextFormatter(format_string)
        console_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)

    # Sentry integration (if configured)
    if sentry:
        from .sentry_integration import setup_sentry
        setup_sentry(root_logger, sentry)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Logger instance
    
    Usage:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, **kwargs) -> None:
    logger.info(f'{method} {path}', extra={'event': 'http_request', **kwargs})


def log_response(
    logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float, **kwargs
) -> None:
    level = logging.INFO if status_code < 400 else logging.WARNING

    logger.log(
        level, f'{method} {path} - {status_code} ({duration_ms:.2f}ms)', extra={'event': 'http_response', **kwargs}
    )
