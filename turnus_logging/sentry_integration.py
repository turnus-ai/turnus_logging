"""
Sentry integration for logging.
"""

import logging
import os
from typing import Dict, Any, Optional


def _coerce_sample_rate(value: Any) -> Optional[float]:
    """
    Coerce a traces_sample_rate value to a valid float.

    Returns the float if it parses and is a finite number in [0.0, 1.0]
    (Sentry's valid range; the range check also rejects NaN/inf, since
    those never satisfy 0.0 <= x <= 1.0). Returns None otherwise.
    """
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return None
    if not (0.0 <= rate <= 1.0):
        return None
    return rate


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
              Must be a finite number in [0.0, 1.0]; invalid or
              out-of-range values are ignored (with a warning) and the
              next source in the config -> env -> default chain is used.
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

    # Resolve config -> env -> default fully before warning, so any warning
    # about a rejected value can state what is actually used instead.
    traces_sample_rate = None
    effective_source = 'default 1.0'
    invalid_sources = []

    config_rate_raw = sentry_config.get('traces_sample_rate')
    if config_rate_raw is not None:
        coerced = _coerce_sample_rate(config_rate_raw)
        if coerced is None:
            invalid_sources.append(('sentry.traces_sample_rate', config_rate_raw))
        else:
            traces_sample_rate = coerced
            effective_source = f'sentry.traces_sample_rate={coerced!r}'

    if traces_sample_rate is None:
        env_rate_raw = os.getenv('SENTRY_TRACES_SAMPLE_RATE')
        if env_rate_raw:
            coerced = _coerce_sample_rate(env_rate_raw)
            if coerced is None:
                invalid_sources.append(('SENTRY_TRACES_SAMPLE_RATE', env_rate_raw))
            else:
                traces_sample_rate = coerced
                effective_source = f'SENTRY_TRACES_SAMPLE_RATE={coerced!r}'

    if traces_sample_rate is None:
        traces_sample_rate = 1.0

    for label, raw in invalid_sources:
        logger.warning(
            f'Invalid {label}={raw!r} (must be a finite number in [0.0, 1.0]); using {effective_source}'
        )

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
