"""
Sentry integration for logging.
"""

import logging
import os
from typing import Dict, Any


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
            - release: Release identifier tagged on every event, enables
              regression detection and "Fixes SENTRY-ID" auto-resolve
              (or use SENTRY_RELEASE / RELEASE env var, in that precedence;
              deploy pipelines already set RELEASE to the short git sha, see
              e.g. turnus-question-answering-service/.github/workflows/deploy.yaml)
            - traces_sample_rate: Fraction of transactions sent for
              performance tracing (or use SENTRY_TRACES_SAMPLE_RATE env var).
              Defaults to 1.0 for backward compatibility; recommended
              production value is 0.1-0.2 to control event volume/cost.
    """
    sentry_dsn = sentry_config.get('dsn') or os.getenv('SENTRY_DSN')

    if not sentry_dsn:
        return

    sentry_environment = sentry_config.get('environment') or os.getenv('SENTRY_ENVIRONMENT', 'development')
    sentry_event_level = sentry_config.get('event_level', logging.ERROR)
    sentry_breadcrumb_level = sentry_config.get('breadcrumb_level', logging.INFO)
    sentry_release = sentry_config.get('release') or os.getenv('SENTRY_RELEASE') or os.getenv('RELEASE')

    traces_sample_rate = sentry_config.get('traces_sample_rate')
    if traces_sample_rate is None:
        env_rate = os.getenv('SENTRY_TRACES_SAMPLE_RATE')
        if env_rate:
            try:
                traces_sample_rate = float(env_rate)
            except ValueError:
                logger.warning(f'Invalid SENTRY_TRACES_SAMPLE_RATE={env_rate!r}, falling back to 1.0')
        if traces_sample_rate is None:
            traces_sample_rate = 1.0

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning('Sentry DSN provided but sentry-sdk not installed. Install with: pip install sentry-sdk>=2.35.0')
        return

    # AwsLambdaIntegration only activates when running inside an actual
    # Lambda invocation (detected via the AWS Lambda runtime); it is a
    # no-op elsewhere, so it is safe to always include when available.
    try:
        from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
        aws_lambda_integration = AwsLambdaIntegration()
    except ImportError:
        aws_lambda_integration = None

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
            
            integrations = [
                LoggingIntegration(
                    level=sentry_breadcrumb_level,
                    event_level=sentry_event_level,
                ),
            ]
            if aws_lambda_integration is not None:
                integrations.append(aws_lambda_integration)

            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=sentry_environment,
                release=sentry_release,
                send_default_pii=True,
                traces_sample_rate=traces_sample_rate,
                enable_logs=True,
                before_send=before_send,
                integrations=integrations,
            )

            logger.info('Sentry logging enabled', extra={'sentry_environment': sentry_environment})
    except Exception as e:
        logger.warning(f'Failed to configure Sentry: {e}')
