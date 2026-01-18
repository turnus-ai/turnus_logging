# Quick Test Reference

## Run All Tests
```bash
# Basic test (no optional deps)
python test_unified_logging.py

# With Powertools
pip install aws-lambda-powertools
python test_unified_logging.py

# With everything
pip install aws-lambda-powertools sentry-sdk
python test_unified_logging.py
python test_lambda_unified.py
```

## Expected Results
```
✅ Test 1: Console only - PASSED
✅ Test 2: Console + Powertools - PASSED
✅ Test 3: Handler verification - PASSED
✅ Test 4: Context propagation - PASSED
✅ Test 5: Sentry integration - PASSED
✅ Test 6: Full integration - PASSED

🎉 All integrations available and tested!
```

## Quick Verification

### 1. Basic Logging Works
```python
from turnus_logging import setup_logging
logger = setup_logging(service_name='test')
logger.info("Hello")  # Should see JSON output
```

### 2. Context Works
```python
from turnus_logging import log_context
with log_context(user_id='123'):
    logger.info("Test")  # Should include user_id
```

### 3. Powertools Works
```python
logger = setup_logging(
    service_name='test',
    powertools={'enabled': True}
)
logger.info("Test")  # Should see structured JSON
```

### 4. Multiple Destinations Work
```python
logger = setup_logging(
    service_name='test',
    sentry={'dsn': '...'},
    powertools={'enabled': True}
)
logger.info("Test")  # Goes to console + Sentry + Powertools
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests skip Powertools | `pip install aws-lambda-powertools` |
| Tests skip Sentry | `pip install sentry-sdk` |
| Infinite loop | Check propagate=False in handler |
| Context not appearing | Use `log_context()` context manager |

## Test File Locations
- `test_unified_logging.py` - Full integration tests
- `test_lambda_unified.py` - Lambda-specific tests
- `examples/unified_logging_example.py` - Usage examples
