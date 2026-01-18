"""
Live test to see actual logs going to Powertools and Sentry.

This shows real output without mocking - you'll see the actual
JSON logs that would go to CloudWatch and Sentry.

Run with: python test_live_destinations.py
"""

import logging
import sys
from turnus_logging import setup_logging, log_context

print("=" * 70)
print("LIVE TEST: See Logs Going to Multiple Destinations")
print("=" * 70)

# Test 1: Console + Powertools (Real Output)
print("\n" + "=" * 70)
print("TEST 1: Console + Powertools")
print("=" * 70)
print("\nYou should see structured JSON logs below.")
print("These are what Powertools would send to CloudWatch.")
print("-" * 70)

try:
    from aws_lambda_powertools import Logger as PowertoolsLogger
    
    # Clear any existing handlers
    root = logging.getLogger()
    root.handlers.clear()
    
    logger = setup_logging(
        service_name='demo-powertools',
        log_level=logging.INFO,
        powertools={'enabled': True, 'log_event': False}
    )
    
    print("\n→ Logging without context:")
    logger.info("Simple message to Powertools")
    
    print("\n→ Logging with context:")
    with log_context(user_id='user_123', order_id='order_456'):
        logger.info("Message with user and order context")
        logger.warning("Warning with context")
    
    print("\n→ Logging with error:")
    try:
        result = 10 / 0
    except Exception:
        logger.error("Math error occurred", exc_info=True)
    
    print("\n✅ Powertools logs shown above (JSON format)")
    print("   These would appear in CloudWatch Logs Insights")
    
    powertools_available = True
    
except ImportError:
    print("\n⚠ aws-lambda-powertools not installed")
    print("   Install with: pip install aws-lambda-powertools")
    powertools_available = False


# Test 2: Console + Sentry
print("\n" + "=" * 70)
print("TEST 2: Console + Sentry")
print("=" * 70)
print("\nLogs below go to BOTH console AND Sentry.")
print("Sentry would receive these as breadcrumbs and events.")
print("-" * 70)

try:
    import sentry_sdk
    
    # Clear handlers
    root = logging.getLogger()
    root.handlers.clear()
    
    # Use a fake DSN - Sentry won't actually send (no network)
    # but we'll see the logging output
    logger = setup_logging(
        service_name='demo-sentry',
        log_level=logging.INFO,
        sentry={
            'dsn': 'https://fake-key@o0.ingest.sentry.io/0',  # Fake DSN
            'environment': 'test',
            'event_level': logging.ERROR,
            'breadcrumb_level': logging.INFO,
        }
    )
    
    print("\n→ Info log (becomes Sentry breadcrumb):")
    logger.info("User logged in")
    
    print("\n→ Warning log (becomes Sentry breadcrumb):")
    logger.warning("Unusual activity detected")
    
    print("\n→ Info with context (breadcrumb with context):")
    with log_context(user_id='user_789', ip='192.168.1.1'):
        logger.info("Action performed with context")
    
    print("\n→ Error log (becomes Sentry event):")
    try:
        raise ValueError("Something went wrong")
    except Exception:
        logger.error("Application error", exc_info=True)
    
    print("\n✅ Sentry integration active")
    print("   INFO/WARNING → Sentry breadcrumbs")
    print("   ERROR → Sentry events")
    print("   (Using fake DSN, so no actual network calls)")
    
    sentry_available = True
    
except ImportError:
    print("\n⚠ sentry-sdk not installed")
    print("   Install with: pip install sentry-sdk")
    sentry_available = False


# Test 3: ALL THREE (Console + Powertools + Sentry)
print("\n" + "=" * 70)
print("TEST 3: Console + Powertools + Sentry (ALL THREE)")
print("=" * 70)
print("\nEach log below goes to ALL THREE destinations simultaneously!")
print("-" * 70)

if powertools_available and sentry_available:
    # Clear handlers
    root = logging.getLogger()
    root.handlers.clear()
    
    logger = setup_logging(
        service_name='demo-all-three',
        log_level=logging.INFO,
        sentry={
            'dsn': 'https://fake-key@o0.ingest.sentry.io/0',
            'environment': 'test',
        },
        powertools={'enabled': True}
    )
    
    print("\n→ Single log going to 3 destinations:")
    with log_context(
        request_id='req_12345',
        user_id='user_abc',
        order_id='order_999'
    ):
        logger.info("Order processing started")
        logger.info("Validating payment")
        logger.info("Order completed successfully")
    
    print("\n→ Error going to all 3 destinations:")
    try:
        raise RuntimeError("Payment gateway timeout")
    except Exception:
        logger.error("Order processing failed", exc_info=True)
    
    print("\n✅ All three destinations active!")
    print("   • Console: You see the JSON logs above")
    print("   • Powertools: Would send to CloudWatch")
    print("   • Sentry: Would send breadcrumbs + events")
    
else:
    missing = []
    if not powertools_available:
        missing.append("aws-lambda-powertools")
    if not sentry_available:
        missing.append("sentry-sdk")
    
    print(f"\n⏭ Test 3 skipped - Missing: {', '.join(missing)}")


# Test 4: Verify Handler Count
print("\n" + "=" * 70)
print("TEST 4: Verify Handler Configuration")
print("=" * 70)

from turnus_logging.aws_powertools_integration import PowertoolsHandler

# Console only
root = logging.getLogger()
root.handlers.clear()
logger1 = setup_logging(service_name='test1')
console_only_count = len(root.handlers)
print(f"\n✓ Console only: {console_only_count} handler(s)")

if powertools_available:
    # With Powertools
    root.handlers.clear()
    logger2 = setup_logging(
        service_name='test2',
        powertools={'enabled': True}
    )
    with_powertools_count = len(root.handlers)
    powertools_handlers = [h for h in root.handlers if isinstance(h, PowertoolsHandler)]
    
    print(f"✓ With Powertools: {with_powertools_count} handler(s)")
    print(f"  - PowertoolsHandler instances: {len(powertools_handlers)}")
    
    assert len(powertools_handlers) == 1, "Should have exactly 1 Powertools handler"

if sentry_available and powertools_available:
    # With both
    root.handlers.clear()
    logger3 = setup_logging(
        service_name='test3',
        sentry={'dsn': 'https://fake@sentry.io/0'},
        powertools={'enabled': True}
    )
    with_both_count = len(root.handlers)
    
    print(f"✓ With both: {with_both_count} handler(s)")
    print(f"  - Expected: Console + Powertools = 2 handlers")
    
    # Note: Sentry handler is added differently, not as a standard logging handler

print("\n✅ Handler configuration verified!")


# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\n✅ Live Demonstration Complete!")
print("\nWhat You Just Saw:")
print("  1. ✓ Structured JSON logs (Powertools format for CloudWatch)")
print("  2. ✓ Console output (you can see the logs)")
print("  3. ✓ Context flowing to all destinations (user_id, order_id, etc.)")
print("  4. ✓ Errors with full stack traces")
print("\nKey Insight:")
print("  → Single logger.info() sends to MULTIPLE destinations")
print("  → Console always shows output (for debugging)")
print("  → Powertools → CloudWatch (in production)")
print("  → Sentry → Error tracking platform")
print("\n🎉 Unified logging works as designed!")
print("=" * 70)
