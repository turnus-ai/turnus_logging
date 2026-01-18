"""
Example: Unified logging with multiple destinations

This example shows how to use turnus_logging with BOTH Sentry and Powertools
enabled simultaneously. A single logger.info() call routes to:
  - Console output (structured JSON)
  - Sentry (for error tracking)
  - AWS Lambda Powertools (for CloudWatch)

Benefits:
  - Write once: logger.info() goes everywhere
  - Single context: log_context() applies to all destinations
  - Consistent interface: Standard Python logging API
"""

import logging
from turnus_logging import setup_logging, log_context

# Option 1: Enable both Sentry AND Powertools
logger = setup_logging(
    service_name='order-processor',
    log_level=logging.INFO,
    sentry={
        'dsn': 'https://your-sentry-dsn@sentry.io/project-id',
        'environment': 'production',
        'event_level': logging.ERROR,  # Send errors to Sentry
    },
    powertools={
        'enabled': True,  # Enable Powertools
        'log_event': False,  # Don't log full event (can be noisy)
    }
)

# Lambda handler with unified logging
def lambda_handler(event, context):
    """
    Example Lambda handler with unified logging.
    
    Every logger.info() call routes to:
    1. Console (structured JSON)
    2. Sentry (if error level)
    3. CloudWatch via Powertools
    """
    
    # Extract user context
    user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    request_id = event.get('requestContext', {}).get('requestId')
    
    # Set context once - applies to ALL destinations
    with log_context(
        user_id=user_id,
        request_id=request_id,
        order_id=event.get('orderId'),
        action='process_order'
    ):
        # This goes to console, Sentry breadcrumb, AND Powertools/CloudWatch
        logger.info("Processing order", extra={'order_value': event.get('orderValue')})
        
        try:
            # Business logic here
            result = process_order(event)
            
            # Success log - goes to all destinations
            logger.info("Order processed successfully", extra={'result': result})
            
            return {
                'statusCode': 200,
                'body': {'success': True, 'result': result}
            }
            
        except Exception as e:
            # Error log - goes to console, Sentry (as event), AND Powertools
            logger.error(f"Order processing failed: {e}", exc_info=True)
            
            return {
                'statusCode': 500,
                'body': {'success': False, 'error': str(e)}
            }


def process_order(event):
    """Simulate order processing"""
    order_id = event.get('orderId')
    
    # Nested context - still applies everywhere
    with log_context(step='validation'):
        logger.debug("Validating order")
    
    with log_context(step='payment'):
        logger.info("Processing payment")
    
    with log_context(step='fulfillment'):
        logger.info("Scheduling fulfillment")
    
    return {'order_id': order_id, 'status': 'completed'}


# Example: Console-only logging (no external services)
def example_console_only():
    """Example without Sentry or Powertools - just console"""
    simple_logger = setup_logging(
        service_name='local-dev',
        log_level=logging.DEBUG
    )
    
    with log_context(environment='local', user='developer'):
        simple_logger.info("Running local tests")


# Example: Sentry-only (no Powertools)
def example_sentry_only():
    """Example with Sentry but no Powertools"""
    sentry_logger = setup_logging(
        service_name='web-app',
        sentry={
            'dsn': 'https://your-sentry-dsn@sentry.io/project-id',
            'environment': 'staging',
        }
        # Note: no powertools config
    )
    
    with log_context(user_id='123', action='login'):
        sentry_logger.info("User login")


# Example: Powertools-only (no Sentry)
def example_powertools_only():
    """Example with Powertools but no Sentry"""
    powertools_logger = setup_logging(
        service_name='lambda-function',
        powertools={'enabled': True}
        # Note: no sentry config
    )
    
    with log_context(function='data-processor'):
        powertools_logger.info("Processing batch")


if __name__ == '__main__':
    # Test locally (will warn that Powertools isn't available)
    logger.info("Testing unified logging")
    
    with log_context(test='example', environment='local'):
        logger.info("This log has context")
        logger.warning("This is a warning")
    
    # Simulate an error
    try:
        raise ValueError("Example error for Sentry")
    except Exception:
        logger.error("Caught exception", exc_info=True)
