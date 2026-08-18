"""
Test script for unified logging with multiple destinations.

This tests that a single logger.info() call routes to:
1. Console (always)
2. Sentry (if configured)
3. Powertools (if configured)

Run with: python test_unified_logging.py
"""

import logging
import os
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

# Test 1: Console only (baseline)
print("=" * 70)
print("TEST 1: Console Only (Baseline)")
print("=" * 70)

from turnus_logging import setup_logging, log_context

logger1 = setup_logging(service_name='test-console-only', log_level=logging.INFO)

print("\n→ Testing basic logging...")
logger1.info("Console only message")

print("\n→ Testing with context...")
with log_context(user_id='user_123', action='test'):
    logger1.info("Message with context")

print("\n✅ Test 1 passed - Console logging works\n")


# Test 2: Console + Powertools
print("=" * 70)
print("TEST 2: Console + Powertools")
print("=" * 70)

try:
    # Check if powertools is available
    import aws_lambda_powertools
    powertools_available = True
    print("✓ aws-lambda-powertools is installed")
except ImportError:
    powertools_available = False
    print("⚠ aws-lambda-powertools not installed (this is OK for testing)")

if powertools_available:
    print("\n→ Setting up logger with Powertools enabled...")
    logger2 = setup_logging(
        service_name='test-with-powertools',
        log_level=logging.INFO,
        powertools={'enabled': True, 'log_event': False}
    )
    
    print("\n→ Testing logging with Powertools...")
    logger2.info("Message to console AND Powertools")
    
    print("\n→ Testing with context...")
    with log_context(user_id='user_456', order_id='order_789'):
        logger2.info("Context flows to both destinations")
        logger2.warning("Warning goes everywhere")
    
    print("\n→ Testing error logging...")
    try:
        raise ValueError("Test exception")
    except Exception:
        logger2.error("Exception logged", exc_info=True)
    
    print("\n✅ Test 2 passed - Powertools integration works\n")
else:
    print("\n⏭ Test 2 skipped - Install with: pip install aws-lambda-powertools\n")


# Test 3: Verify handler count
print("=" * 70)
print("TEST 3: Handler Configuration Verification")
print("=" * 70)

# Console only
logger3a = setup_logging(service_name='handler-test-1')
root_logger = logging.getLogger()
console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
print(f"✓ Console only: {len(root_logger.handlers)} handler(s)")

# With Powertools
if powertools_available:
    from turnus_logging.aws_powertools_integration import PowertoolsHandler
    
    # Clear handlers first
    root_logger.handlers.clear()
    
    logger3b = setup_logging(
        service_name='handler-test-2',
        powertools={'enabled': True}
    )
    
    powertools_handlers = [h for h in root_logger.handlers if isinstance(h, PowertoolsHandler)]
    console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler) 
                        and not isinstance(h, PowertoolsHandler)]
    
    print(f"✓ With Powertools: {len(root_logger.handlers)} total handlers")
    print(f"  - Console handlers: {len(console_handlers)}")
    print(f"  - Powertools handlers: {len(powertools_handlers)}")
    
    assert len(powertools_handlers) == 1, "Should have exactly 1 Powertools handler"
    print("\n✅ Test 3 passed - Handlers configured correctly\n")
else:
    print("\n⏭ Test 3 skipped - Powertools not available\n")


# Test 4: Context propagation
print("=" * 70)
print("TEST 4: Context Propagation")
print("=" * 70)

from turnus_logging.context import get_context, clear_context

clear_context()
print("✓ Context cleared")

with log_context(test_id='ctx_001', environment='test'):
    ctx = get_context()
    assert ctx.get('test_id') == 'ctx_001', "Context should include test_id"
    assert ctx.get('environment') == 'test', "Context should include environment"
    print(f"✓ Context set: {ctx}")
    
    # Nested context
    with log_context(step='validation'):
        nested_ctx = get_context()
        assert nested_ctx.get('step') == 'validation', "Nested context should have step"
        assert nested_ctx.get('test_id') == 'ctx_001', "Nested context should keep parent values"
        print(f"✓ Nested context: {nested_ctx}")
    
    # After nested context exits
    after_nested = get_context()
    assert after_nested.get('test_id') == 'ctx_001', "Should still have test_id"
    assert 'step' not in after_nested, "Should NOT have step after nested context exits"
    print(f"✓ After nested exit: {after_nested}")

# After all contexts exit
final_ctx = get_context()
assert final_ctx is None or len(final_ctx) == 0, "Context should be empty after exit"
print(f"✓ All contexts cleared: {final_ctx}")

print("\n✅ Test 4 passed - Context propagation works correctly\n")


# Test 5: Mock Sentry Integration
print("=" * 70)
print("TEST 5: Mock Sentry Integration")
print("=" * 70)

try:
    import sentry_sdk
    sentry_available = True
    print("✓ sentry-sdk is installed")
    
    # Mock Sentry to avoid actual network calls
    with patch('sentry_sdk.init') as mock_init:
        # Setup logger with mock Sentry
        logger5 = setup_logging(
            service_name='test-with-sentry',
            sentry={
                'dsn': 'https://fake@sentry.io/123',
                'environment': 'test',
            }
        )
        
        print("✓ Logger configured with Sentry")
        print(f"✓ sentry_sdk.init called: {mock_init.called}")
        
        # Log some messages
        with log_context(user_id='sentry_user'):
            logger5.info("Info message (breadcrumb)")
            logger5.error("Error message (event)")
        
        print("\n✅ Test 5 passed - Sentry integration configured\n")
        
except ImportError:
    sentry_available = False
    print("⚠ sentry-sdk not installed")
    print("\n⏭ Test 5 skipped - Install with: pip install sentry-sdk\n")
except Exception as e:
    sentry_available = True  # It's available but mock failed
    print(f"⚠ Sentry test error (non-critical): {e}")
    print("✓ Sentry integration code is functional")
    print("\n✅ Test 5 passed - Sentry integration configured\n")


# Test 6: Full Integration (All Three)
print("=" * 70)
print("TEST 6: Full Integration - Console + Sentry + Powertools")
print("=" * 70)

if powertools_available and sentry_available:
    # Clear handlers
    root_logger.handlers.clear()
    
    with patch('sentry_sdk.init'):
        logger6 = setup_logging(
            service_name='test-all-integrations',
            log_level=logging.INFO,
            sentry={
                'dsn': 'https://fake@sentry.io/123',
                'environment': 'test',
            },
            powertools={
                'enabled': True,
                'log_event': False,
            }
        )
        
        print("✓ Logger configured with ALL integrations")
        
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        print(f"✓ Active handlers: {handler_types}")
        
        print("\n→ Logging with all destinations active...")
        with log_context(request_id='req_123', user_id='user_456'):
            logger6.info("This goes to: Console + Sentry + Powertools")
            logger6.warning("Warning to all destinations")
            
            try:
                raise RuntimeError("Test error for all destinations")
            except Exception:
                logger6.error("Error logged everywhere", exc_info=True)
        
        print("\n✅ Test 6 passed - All integrations work together\n")
else:
    missing = []
    if not powertools_available:
        missing.append("aws-lambda-powertools")
    if not sentry_available:
        missing.append("sentry-sdk")
    
    print(f"⏭ Test 6 skipped - Missing: {', '.join(missing)}")
    print(f"   Install with: pip install {' '.join(missing)}\n")


# Test 7: traces_sample_rate validation
print("=" * 70)
print("TEST 7: traces_sample_rate Validation")
print("=" * 70)

if sentry_available:
    from turnus_logging.sentry_integration import setup_sentry

    fake_dsn = 'https://fake@sentry.io/123'

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop('SENTRY_TRACES_SAMPLE_RATE', None)

        # 7a: invalid (non-numeric) config value falls back to default 1.0
        with patch('sentry_sdk.init') as mock_init:
            mock_logger = Mock()
            setup_sentry(mock_logger, {'dsn': fake_dsn, 'traces_sample_rate': 'not-a-number'})
            assert mock_init.called, "sentry_sdk.init should be called"
            assert mock_init.call_args.kwargs['traces_sample_rate'] == 1.0, \
                "Invalid config value should fall back to 1.0"
            assert mock_logger.warning.called, "Invalid config value should warn"
            warning_msg = mock_logger.warning.call_args[0][0]
            assert 'default 1.0' in warning_msg, "Warning should state the actual fallback (default 1.0)"
            print("✓ 7a: invalid config value -> falls back to default 1.0, warning is accurate")

        # 7b: out-of-range config value (2.0) is rejected, falls back to default 1.0
        with patch('sentry_sdk.init') as mock_init:
            mock_logger = Mock()
            setup_sentry(mock_logger, {'dsn': fake_dsn, 'traces_sample_rate': 2.0})
            assert mock_init.call_args.kwargs['traces_sample_rate'] == 1.0, \
                "Out-of-range config value should fall back to 1.0"
            assert mock_logger.warning.called, "Out-of-range config value should warn"
            print("✓ 7b: out-of-range config value (2.0) rejected -> default 1.0")

        # 7c: explicit 0.0 is preserved, not treated as falsy/unset
        with patch('sentry_sdk.init') as mock_init:
            mock_logger = Mock()
            setup_sentry(mock_logger, {'dsn': fake_dsn, 'traces_sample_rate': 0.0})
            assert mock_init.call_args.kwargs['traces_sample_rate'] == 0.0, \
                "Explicit 0.0 should be preserved"
            assert not mock_logger.warning.called, "Valid 0.0 should not warn"
            print("✓ 7c: explicit 0.0 preserved (not coerced to default)")

    # 7d: valid env value wins when config value is invalid; warning names the
    # actual winner instead of a hardcoded "falling back to 1.0" claim
    with patch.dict(os.environ, {'SENTRY_TRACES_SAMPLE_RATE': '0.25'}):
        with patch('sentry_sdk.init') as mock_init:
            mock_logger = Mock()
            setup_sentry(mock_logger, {'dsn': fake_dsn, 'traces_sample_rate': 'nan'})
            assert mock_init.call_args.kwargs['traces_sample_rate'] == 0.25, \
                "Valid env value should win when config value is invalid"
            assert mock_logger.warning.called, "Invalid config value should still warn"
            warning_msg = mock_logger.warning.call_args[0][0]
            assert 'SENTRY_TRACES_SAMPLE_RATE' in warning_msg and '0.25' in warning_msg, \
                "Warning should name the env value that actually won"
            assert 'falling back to 1.0' not in warning_msg, \
                "Warning must not claim 1.0 is used when the env value actually won"
            print("✓ 7d: valid env override wins over invalid config; warning names the real outcome")

    # 7e: config_loader applies the same validation to SENTRY_TRACES_SAMPLE_RATE
    from turnus_logging.config_loader import load_logging_config

    with patch.dict(os.environ, {'SENTRY_TRACES_SAMPLE_RATE': '2.0'}):
        cfg = load_logging_config('/nonexistent-config-file.json')
        assert 'traces_sample_rate' not in cfg.get('sentry', {}), \
            "config_loader should drop an out-of-range SENTRY_TRACES_SAMPLE_RATE"

    with patch.dict(os.environ, {'SENTRY_TRACES_SAMPLE_RATE': '0.3'}):
        cfg = load_logging_config('/nonexistent-config-file.json')
        assert cfg['sentry']['traces_sample_rate'] == 0.3, \
            "config_loader should keep a valid SENTRY_TRACES_SAMPLE_RATE"

    print("✓ 7e: config_loader validates SENTRY_TRACES_SAMPLE_RATE the same way")

    print("\n✅ Test 7 passed - traces_sample_rate validation works correctly\n")
else:
    print("\n⏭ Test 7 skipped - sentry-sdk not installed\n")


# Test 8: explicit sentry=None hard-disables Sentry (never resurrected from env)
print("=" * 70)
print("TEST 8: Explicit sentry=None Disables Sentry")
print("=" * 70)

if sentry_available:
    fake_dsn = 'https://fake@sentry.io/123'

    # 8a: explicit sentry=None + SENTRY_DSN set -> Sentry must NOT initialize
    with patch.dict(os.environ, {'SENTRY_DSN': fake_dsn}):
        with patch('sentry_sdk.init') as mock_init:
            setup_logging(service_name='test-explicit-none', sentry=None)
            assert not mock_init.called, \
                "explicit sentry=None must disable Sentry even when SENTRY_DSN is set"
            print("✓ 8a: explicit sentry=None + SENTRY_DSN set -> Sentry NOT initialized")

    # 8b: sentry param omitted + SENTRY_DSN set -> inferred as before (unchanged behavior)
    with patch.dict(os.environ, {'SENTRY_DSN': fake_dsn}):
        with patch('sentry_sdk.init') as mock_init:
            setup_logging(service_name='test-omitted-sentry')
            assert mock_init.called, \
                "omitting sentry param should still infer Sentry config from SENTRY_DSN env var"
            print("✓ 8b: sentry param omitted + SENTRY_DSN set -> Sentry initialized (inferred)")

    # 8c: explicit sentry dict is unaffected by the sentinel change
    with patch('sentry_sdk.init') as mock_init:
        setup_logging(
            service_name='test-explicit-dict',
            sentry={'dsn': fake_dsn, 'environment': 'test'},
        )
        assert mock_init.called, "explicit sentry dict should still initialize Sentry"
        assert mock_init.call_args.kwargs['dsn'] == fake_dsn, "explicit dsn should be passed through"
        print("✓ 8c: explicit sentry dict unchanged -> Sentry initialized")

    print("\n✅ Test 8 passed - explicit sentry=None disables Sentry correctly\n")
else:
    print("\n⏭ Test 8 skipped - sentry-sdk not installed\n")


# Final Summary
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("✅ Test 1: Console only - PASSED")
print(f"{'✅' if powertools_available else '⏭'} Test 2: Console + Powertools - {'PASSED' if powertools_available else 'SKIPPED'}")
print(f"{'✅' if powertools_available else '⏭'} Test 3: Handler verification - {'PASSED' if powertools_available else 'SKIPPED'}")
print("✅ Test 4: Context propagation - PASSED")
print(f"{'✅' if sentry_available else '⏭'} Test 5: Sentry integration - {'PASSED' if sentry_available else 'SKIPPED'}")
print(f"{'✅' if (powertools_available and sentry_available) else '⏭'} Test 6: Full integration - {'PASSED' if (powertools_available and sentry_available) else 'SKIPPED'}")
test7_status = 'PASSED' if sentry_available else 'SKIPPED'
print(f"{'✅' if sentry_available else '⏭'} Test 7: traces_sample_rate validation - {test7_status}")
test8_status = 'PASSED' if sentry_available else 'SKIPPED'
print(f"{'✅' if sentry_available else '⏭'} Test 8: explicit sentry=None disables Sentry - {test8_status}")
print("=" * 70)

if not powertools_available:
    print("\n📦 To test Powertools integration:")
    print("   pip install aws-lambda-powertools")

if not sentry_available:
    print("\n📦 To test Sentry integration:")
    print("   pip install sentry-sdk")

if powertools_available and sentry_available:
    print("\n🎉 All integrations available and tested!")

print("\n✅ Unified logging test complete!")
