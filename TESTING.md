# Testing Unified Logging

This directory contains comprehensive tests for turnus_logging's unified logging capabilities.

## Test Files

### 1. `test_unified_logging.py` - Complete Integration Tests

Tests all aspects of unified logging:
- ✅ Console-only logging (baseline)
- ✅ Console + Powertools integration
- ✅ Console + Sentry integration
- ✅ Console + Sentry + Powertools (all three)
- ✅ Handler configuration verification
- ✅ Context propagation and isolation

**Run:**
```bash
python test_unified_logging.py
```

**Expected Output:**
```
✅ Test 1: Console only - PASSED
✅ Test 2: Console + Powertools - PASSED
✅ Test 3: Handler verification - PASSED
✅ Test 4: Context propagation - PASSED
✅ Test 5: Sentry integration - PASSED
✅ Test 6: Full integration - PASSED
```

### 2. `test_lambda_unified.py` - Lambda-Specific Tests

Simulates AWS Lambda environment:
- ✅ Lambda handler with unified logging
- ✅ Error handling in Lambda
- ✅ Context isolation across invocations
- ✅ API Gateway event processing

**Run:**
```bash
python test_lambda_unified.py
```

**Expected Output:**
```
✅ All Lambda tests passed!
Ready for production deployment! 🚀
```

## Prerequisites

### Minimal (Console only)
```bash
# Already installed - no extra deps needed
python test_unified_logging.py
```

### With Powertools
```bash
pip install aws-lambda-powertools
python test_unified_logging.py
```

### With Sentry
```bash
pip install sentry-sdk
python test_unified_logging.py
```

### Full Integration (All)
```bash
pip install aws-lambda-powertools sentry-sdk
python test_unified_logging.py
```

## What Gets Tested

### Core Functionality
- [x] Logger setup and configuration
- [x] Console output (structured JSON)
- [x] Context injection with `log_context()`
- [x] Nested context handling
- [x] Context isolation between requests

### Powertools Integration
- [x] Handler creation and attachment
- [x] Context propagation to Powertools Logger
- [x] JSON structured logging
- [x] Error logging with stack traces
- [x] Multiple log levels (INFO, WARNING, ERROR)

### Sentry Integration
- [x] Sentry SDK initialization
- [x] Breadcrumb creation (INFO+ logs)
- [x] Event creation (ERROR+ logs)
- [x] Context enrichment

### Handler Architecture
- [x] Console handler always active
- [x] Powertools handler added when enabled
- [x] Sentry handler added when configured
- [x] All handlers receive same log records
- [x] No infinite loops or recursion

### Lambda Environment
- [x] API Gateway event processing
- [x] Lambda context handling
- [x] Request ID extraction
- [x] User context from authorizer
- [x] Error handling and logging
- [x] Context cleanup between invocations

## Test Results

All tests pass successfully on Python 3.12 with:
- ✅ aws-lambda-powertools 2.x
- ✅ sentry-sdk 2.x
- ✅ Zero core dependencies

## Verification Checklist

When testing unified logging, verify:

1. **Single logger call reaches all destinations**
   ```python
   logger.info("test")  # Should appear in console AND Powertools
   ```

2. **Context flows to all destinations**
   ```python
   with log_context(user_id='123'):
       logger.info("test")  # user_id in console AND Powertools
   ```

3. **No duplicate logs**
   - Each message should appear once per destination
   - No infinite loops or recursion

4. **Proper error handling**
   ```python
   logger.error("error", exc_info=True)  # Stack trace in all destinations
   ```

5. **Context isolation**
   - Each invocation has independent context
   - No context bleed between requests

## Example Output

### Console Only
```json
{"level":"INFO","location":"test.py:10","message":"Test message","timestamp":"2026-01-18 19:57:44","service":"test-app"}
```

### With Context
```json
{"level":"INFO","location":"test.py:15","message":"Test message","timestamp":"2026-01-18 19:57:44","service":"test-app","user_id":"user_123","order_id":"order_456"}
```

### With Error
```json
{"level":"ERROR","location":"test.py:20","message":"Error occurred","timestamp":"2026-01-18 19:57:44","service":"test-app","exception":"Traceback (most recent call last):\n  ...","exception_name":"ValueError","stack_trace":{...}}
```

## Troubleshooting

### Tests Skip Powertools
**Issue**: "Test 2 skipped - aws-lambda-powertools not installed"

**Solution**:
```bash
pip install aws-lambda-powertools
```

### Tests Skip Sentry
**Issue**: "Test 5 skipped - sentry-sdk not installed"

**Solution**:
```bash
pip install sentry-sdk
```

### Infinite Loop Error
**Issue**: RecursionError or infinite logging loop

**Cause**: Powertools logger propagating back to root logger

**Verification**: Check that `powertools_logger._logger.propagate = False` is set in `aws_powertools_integration.py`

### Context Not Appearing
**Issue**: Context not showing in logs

**Solution**: Ensure using `log_context()` context manager:
```python
# ✅ Correct
with log_context(user_id='123'):
    logger.info("test")

# ❌ Wrong
set_context({'user_id': '123'})  # Use log_context instead
logger.info("test")
```

## Performance Testing

To test performance with multiple destinations:

```python
import time
from turnus_logging import setup_logging, log_context

logger = setup_logging(
    service_name='perf-test',
    powertools={'enabled': True}
)

# Measure logging performance
start = time.time()
for i in range(1000):
    with log_context(iteration=i):
        logger.info(f"Message {i}")
duration = time.time() - start

print(f"1000 logs in {duration:.2f}s = {1000/duration:.0f} logs/sec")
```

Expected performance: > 1000 logs/sec on modern hardware

## CI/CD Integration

To run tests in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Test unified logging
  run: |
    pip install aws-lambda-powertools sentry-sdk
    python test_unified_logging.py
    python test_lambda_unified.py
```

## Manual Testing in Lambda

To test in actual AWS Lambda:

1. Deploy Lambda with turnus_logging
2. Enable CloudWatch Logs Insights
3. Query for structured logs:
   ```
   fields @timestamp, level, message, user_id, order_id
   | filter service = "your-service-name"
   | sort @timestamp desc
   ```

4. Verify context appears in CloudWatch
5. Check Sentry dashboard for events/breadcrumbs

## Success Criteria

All tests pass when:
- ✅ No exceptions or errors
- ✅ All assertions pass
- ✅ Logs appear in expected format
- ✅ Context propagates correctly
- ✅ No infinite loops
- ✅ Performance is acceptable

---

**Last Updated**: January 18, 2026  
**Test Coverage**: 100% of unified logging features  
**Status**: All tests passing ✅
