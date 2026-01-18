"""
Sentry integration for logging.
"""

import logging
import os
from typing import Optional, Dict, Any


def setup_sentry(logger: logging.Logger, sentry_config: Dict[str, Any]) -> None:
    """
    Setup Sentry integration with context enrichment.
    
    Args:
        logger: Logger instance to attach Sentry to
        sentry_config: Sentry configuration dict with keys:
            - dsn: Sentry DSN (or use SENTRY_DSN env var)
            - environment: Environment name (or use SENTRY_ENVIRONMENT env var)
            - event_level: Log level for Sentry events (default: ERROR)
            - breadcrumb_level: Log level for breadcrumbs (default: INFO)
    """
    sentry_dsn = sentry_config.get('dsn') or os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        return
    
    sentry_environment = sentry_config.get('environment') or os.getenv('SENTRY_ENVIRONMENT', 'development')
    sentry_event_level = sentry_config.get('event_level', logging.ERROR)
    sentry_breadcrumb_level = sentry_config.get('breadcrumb_level', logging.INFO)
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning('Sentry DSN provided but sentry-sdk not installed. Install with: pip install sentry-sdk>=2.35.0')
        return

    try:
        from .context import get_context

        # Initialize Sentry first
        if not sentry_sdk.Hub.current.client:
            # Callback to enrich events with context as individual tags
            def before_send(event, hint):
                try:
                    context = get_context()
                    if context:
                        # Add all context fields as individual tags (queryable in Sentry)
                        tags = event.setdefault('tags', {})
                        for key, value in context.items():
                            if value is not None:
                                tags[key] = str(value)
                        
                        # Also add to contexts for detailed view
                        contexts = event.setdefault('contexts', {})
                        contexts['log_context'] = context

                except Exception:
                    pass

                return event
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=sentry_environment,
                send_default_pii=True,
                traces_sample_rate=1.0,
                enable_logs=True,
                before_send=before_send,
                integrations=[
                    LoggingIntegration(
                        level=sentry_breadcrumb_level,
                        event_level=sentry_event_level,
                    ),
                ],
            )

            logger.info('Sentry logging enabled', extra={'sentry_environment': sentry_environment})
    except Exception as e:
        logger.warning(f'Failed to configure Sentry: {e}')
