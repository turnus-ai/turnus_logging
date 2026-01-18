"""
AWS Lambda Powertools integration for turnus_logging.

This module provides integration with AWS Lambda Powertools Logger,
allowing turnus_logging context to work seamlessly with Powertools.

The integration works in two modes:

1. **As a handler** (recommended): Add Powertools as a log handler alongside Sentry
   - Use setup_logging(powertools={'enabled': True})
   - Standard Python logger.info() routes to both console, Sentry, AND Powertools
   - Unified logging interface

2. **Standalone** (legacy): Use Powertools Logger directly
   - Use setup_powertools_logging() to get a Powertools Logger instance
   - Only routes to Powertools (not Sentry)

Installation:
    pip install "turnus-logging[powertools]"
    # OR
    pip install turnus-logging aws-lambda-powertools

Usage (Recommended - Unified):
    from turnus_logging import setup_logging, log_context
    
    # Enable both Sentry AND Powertools
    logger = setup_logging(
        service_name='my-service',
        sentry={'dsn': '...'},
        powertools={'enabled': True}
    )
    
    # Single logger.info() goes to console, Sentry, AND Powertools
    with log_context(user_id='123'):
        logger.info("Processing order")  # All destinations get the log

Usage (Legacy - Powertools only):
    from turnus_logging.aws_powertools_integration import setup_powertools_logging
    
    logger = setup_powertools_logging(service_name='my-service')
    with log_context(user_id='123'):
        logger.info("Processing order")  # Only Powertools gets it
"""

import logging
from typing import Optional, Dict, Any
from .context import get_context

try:
    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.logging import correlation_paths
    POWERTOOLS_AVAILABLE = True
except ImportError:
    POWERTOOLS_AVAILABLE = False
    Logger = None
    correlation_paths = None


class PowertoolsHandler(logging.Handler):
    """
    Logging handler that sends logs to AWS Lambda Powertools Logger.
    
    This allows a standard Python logger to route logs to Powertools,
    enabling unified logging across multiple destinations (console, Sentry, Powertools).
    """
    
    def __init__(self, powertools_logger: "Logger"):
        """
        Initialize handler with a Powertools Logger instance.
        
        Args:
            powertools_logger: Configured Powertools Logger to send logs to
        """
        super().__init__()
        self.powertools_logger = powertools_logger
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to Powertools Logger.
        
        Args:
            record: Log record to emit
        """
        try:
            # Extract turnus_logging context
            ctx = get_context() or {}
            
            # Map log level
            level_mapping = {
                logging.DEBUG: 'debug',
                logging.INFO: 'info',
                logging.WARNING: 'warning',
                logging.ERROR: 'error',
                logging.CRITICAL: 'critical',
            }
            log_method_name = level_mapping.get(record.levelno, 'info')
            log_method = getattr(self.powertools_logger, log_method_name)
            
            # Send to Powertools with context as additional fields
            log_method(
                record.getMessage(),
                **ctx  # Include all turnus_logging context
            )
        except Exception:
            self.handleError(record)


def setup_powertools_handler(
    root_logger: logging.Logger,
    service_name: str,
    config: Dict[str, Any]
) -> None:
    """
    Setup AWS Lambda Powertools as a logging handler.
    
    This adds Powertools as a destination for standard Python logging,
    allowing logs to go to console, Sentry, AND Powertools simultaneously.
    
    Args:
        root_logger: Root logger to attach handler to
        service_name: Service name for Powertools
        config: Powertools configuration dict with keys:
            - enabled: Must be True
            - log_level: Optional log level (defaults to root logger level)
            - correlation_id_path: Optional correlation ID path
            - log_event: Whether to log incoming events
    """
    if not POWERTOOLS_AVAILABLE:
        raise ImportError(
            "AWS Lambda Powertools is not installed. "
            "Install with: pip install 'turnus-logging[powertools]'"
        )
    
    # Create Powertools logger
    powertools_logger = Logger(
        service=service_name,
        level=config.get('log_level', 'INFO')
    )
    
    # CRITICAL: Prevent infinite loop by stopping propagation
    # The Powertools logger should NOT send logs back to root logger
    powertools_logger._logger.propagate = False
    
    # Add context filter to inject turnus_logging context
    context_filter = PowertoolsContextFilter()
    powertools_logger.addFilter(context_filter)
    
    # Create handler and add to root logger
    handler = PowertoolsHandler(powertools_logger)
    handler.setLevel(root_logger.level)
    root_logger.addHandler(handler)
    
    # Store Powertools logger for potential decorator use
    root_logger._powertools_logger = powertools_logger
    if config.get('correlation_id_path'):
        powertools_logger._correlation_id_path = config['correlation_id_path']
    powertools_logger._log_event = config.get('log_event', False)


class PowertoolsContextFilter(logging.Filter):
    """
    Logging filter that injects turnus_logging context into Powertools logs.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add turnus_logging context to log record."""
        ctx = get_context()
        if ctx:
            # Add all context fields to the log record
            for key, value in ctx.items():
                # Use setattr to add dynamic attributes
                setattr(record, key, value)
        return True


def setup_powertools_logging(
    service_name: str,
    log_level: str = "INFO",
    correlation_id_path: Optional[str] = None,
    inject_lambda_context: bool = True,
    **logger_kwargs
) -> "Logger":
    """
    Setup AWS Lambda Powertools Logger with turnus_logging context integration.
    
    Args:
        service_name: Name of the service/Lambda function
        log_level: Logging level (INFO, DEBUG, etc.)
        correlation_id_path: JSONPath to extract correlation ID from event
                            (e.g., correlation_paths.API_GATEWAY_REST)
        inject_lambda_context: Auto-inject Lambda context into logs
        **logger_kwargs: Additional arguments passed to Powertools Logger
    
    Returns:
        Configured Powertools Logger instance
    
    Example:
        from turnus_logging.aws_powertools_integration import setup_powertools_logging
        from aws_lambda_powertools.logging import correlation_paths
        
        logger = setup_powertools_logging(
            service_name='order-processor',
            correlation_id_path=correlation_paths.API_GATEWAY_REST
        )
        
        def lambda_handler(event, context):
            with log_context(user_id='123'):
                logger.info("Processing order")  # Includes user_id
            return {"statusCode": 200}
    """
    if not POWERTOOLS_AVAILABLE:
        raise ImportError(
            "AWS Lambda Powertools is not installed. "
            "Install with: pip install 'turnus-logging[powertools]' "
            "or: pip install aws-lambda-powertools"
        )
    
    # Create Powertools logger
    logger = Logger(
        service=service_name,
        level=log_level,
        **logger_kwargs
    )
    
    # Add our context filter to inject turnus_logging context
    context_filter = PowertoolsContextFilter()
    logger.addFilter(context_filter)
    
    # Store correlation ID path for decorator use
    if correlation_id_path:
        logger._correlation_id_path = correlation_id_path
    
    # Store whether to inject Lambda context
    logger._inject_lambda_context = inject_lambda_context
    
    return logger


def get_powertools_decorator(logger: "Logger"):
    """
    Get the appropriate Powertools decorator for the logger.
    
    Args:
        logger: Powertools Logger instance from setup_powertools_logging
    
    Returns:
        Decorator function to use on Lambda handler
    
    Example:
        logger = setup_powertools_logging(service_name='my-service')
        
        @get_powertools_decorator(logger)
        def lambda_handler(event, context):
            logger.info("Handler called")
            return {"statusCode": 200}
    """
    if not POWERTOOLS_AVAILABLE:
        raise ImportError("AWS Lambda Powertools is not installed")
    
    # Build decorator parameters
    decorator_kwargs = {}
    
    if hasattr(logger, '_correlation_id_path'):
        decorator_kwargs['correlation_id_path'] = logger._correlation_id_path
    
    if hasattr(logger, '_inject_lambda_context') and logger._inject_lambda_context:
        decorator_kwargs['log_event'] = True
    
    # Return the inject_lambda_context decorator
    return logger.inject_lambda_context(**decorator_kwargs)


def inject_turnus_context_to_powertools(
    event: Dict[str, Any],
    context: Any,
    extract_from_event: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Extract context from Lambda event and inject into turnus_logging context.
    
    This is useful when you want to extract specific fields from the Lambda event
    and make them available in all logs.
    
    Args:
        event: Lambda event dictionary
        context: Lambda context object
        extract_from_event: Mapping of context_key -> event_path
                           e.g., {'user_id': 'requestContext.authorizer.claims.sub'}
    
    Returns:
        Extracted context dictionary
    
    Example:
        from turnus_logging import log_context
        from turnus_logging.aws_powertools_integration import inject_turnus_context_to_powertools
        
        def lambda_handler(event, context):
            # Extract user_id from event
            ctx = inject_turnus_context_to_powertools(
                event, context,
                extract_from_event={
                    'user_id': 'requestContext.authorizer.claims.sub',
                    'api_id': 'requestContext.apiId'
                }
            )
            
            with log_context(**ctx):
                logger.info("Processing request")  # Includes user_id and api_id
    """
    from .context import set_context, get_context
    
    # Start with Lambda context
    lambda_ctx = {
        'request_id': context.request_id,
        'function_name': context.function_name,
        'function_version': context.function_version,
        'memory_limit_mb': context.memory_limit_in_mb,
    }
    
    # Extract fields from event if specified
    if extract_from_event:
        for key, path in extract_from_event.items():
            value = _get_nested_value(event, path)
            if value is not None:
                lambda_ctx[key] = value
    
    # Merge with existing context
    existing = get_context() or {}
    merged = {**existing, **lambda_ctx}
    set_context(merged)
    
    return lambda_ctx


def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """
    Get value from nested dictionary using dot notation.
    
    Example:
        data = {'a': {'b': {'c': 123}}}
        _get_nested_value(data, 'a.b.c')  # Returns 123
    """
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


# Example usage in Lambda
__example__ = """
# Example 1: Basic usage
from turnus_logging.aws_powertools_integration import setup_powertools_logging
from turnus_logging import log_context

logger = setup_powertools_logging(service_name='order-service')

def lambda_handler(event, context):
    # Context is automatically added
    with log_context(order_id='12345', user_id='user_123'):
        logger.info("Processing order")
        # Log will include: order_id, user_id, request_id, function_name, etc.
    
    return {"statusCode": 200}


# Example 2: With API Gateway correlation ID
from aws_lambda_powertools.logging import correlation_paths

logger = setup_powertools_logging(
    service_name='api-service',
    correlation_id_path=correlation_paths.API_GATEWAY_REST
)

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event, context):
    with log_context(user_id=event['requestContext']['authorizer']['claims']['sub']):
        logger.info("API request")
    
    return {"statusCode": 200, "body": "OK"}


# Example 3: Auto-extract from event
from turnus_logging.aws_powertools_integration import (
    setup_powertools_logging,
    inject_turnus_context_to_powertools
)

logger = setup_powertools_logging(service_name='auto-extract-service')

def lambda_handler(event, context):
    # Automatically extract and set context
    inject_turnus_context_to_powertools(
        event, context,
        extract_from_event={
            'user_id': 'requestContext.authorizer.claims.sub',
            'api_id': 'requestContext.apiId',
            'source_ip': 'requestContext.identity.sourceIp'
        }
    )
    
    # All logs now include extracted context
    logger.info("Request received")
    
    return {"statusCode": 200}
"""
