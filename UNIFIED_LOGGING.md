# Unified Logging Architecture

## Overview

turnus_logging now supports **unified logging** - a single `logger.info()` call can route to multiple destinations simultaneously:

- **Console** (structured JSON output)
- **Sentry** (error tracking and breadcrumbs)
- **AWS Lambda Powertools** (CloudWatch Logs with structured logging)

## Architecture

```
Developer Code:
  logger.info("Processing order")
           ↓
┌──────────────────────────┐
│   Root Python Logger     │
│  (turnus_logging context)│
└────────────┬─────────────┘
             ↓
   ┌─────────┼─────────┐
   ↓         ↓         ↓
Console   Sentry   Powertools
Handler   Handler  Handler
   ↓         ↓         ↓
stdout   Sentry    CloudWatch
         API       (via Powertools)
```

## Key Benefits

### 1. Write Once, Log Everywhere
```python
logger.info("Order processed")  # Goes to ALL enabled destinations
```

### 2. Unified Context
```python
with log_context(user_id='123', order_id='456'):
    logger.info("Processing")  # Context included in ALL destinations
```

### 3. Configuration-Driven
```python
# Enable just console
logger = setup_logging(service_name='app')

# Enable console + Sentry
logger = setup_logging(
    service_name='app',
    sentry={'dsn': '...'}
)

# Enable console + Sentry + Powertools
logger = setup_logging(
    service_name='app',
    sentry={'dsn': '...'},
    powertools={'enabled': True}
)
```

### 4. Standard Interface
Uses Python's standard logging API - no vendor lock-in:
```python
logger.info("message")
logger.error("error", exc_info=True)
logger.warning("warning")
```

## Implementation Details

### Handler-Based Routing

Each destination is implemented as a Python `logging.Handler`:

1. **ConsoleHandler**: Built-in, outputs structured JSON
2. **SentryHandler**: From sentry-sdk, sends to Sentry API
3. **PowertoolsHandler**: Custom handler that wraps Powertools Logger

### Infinite Loop Prevention

Critical fix for Powertools integration:
```python
# The Powertools logger must NOT propagate back to root logger
powertools_logger._logger.propagate = False
```

Without this, logs would infinitely cycle:
```
root → PowertoolsHandler → Powertools Logger → root → PowertoolsHandler → ...
```

### Context Propagation

Context flows from `contextvars` → all handlers:

```python
# Set context once
with log_context(user_id='123'):
    logger.info("Test")  # All handlers get user_id
```

Each handler accesses context via `get_context()` and includes it in the output format appropriate for that destination.

## Configuration Options

```python
setup_logging(
    service_name='my-app',
    log_level=logging.INFO,
    
    # Optional: Sentry
    sentry={
        'dsn': 'https://...',
        'environment': 'production',
        'event_level': logging.ERROR,
        'breadcrumb_level': logging.INFO,
    },
    
    # Optional: AWS Powertools
    powertools={
        'enabled': True,
        'log_level': 'INFO',
        'correlation_id_path': None,
        'log_event': False,
    },
)
```

## Example Usage

```python
import logging
from turnus_logging import setup_logging, log_context

# Enable ALL destinations
logger = setup_logging(
    service_name='order-processor',
    log_level=logging.INFO,
    sentry={
        'dsn': 'https://your-sentry-dsn@sentry.io/project',
        'environment': 'production',
    },
    powertools={
        'enabled': True,
    }
)

def lambda_handler(event, context):
    user_id = event.get('userId')
    
    # Single context applies everywhere
    with log_context(user_id=user_id, order_id=event.get('orderId')):
        # This one line logs to:
        # 1. Console (JSON)
        # 2. Sentry (breadcrumb)
        # 3. CloudWatch via Powertools
        logger.info("Processing order")
        
        try:
            process_order(event)
            logger.info("Order completed")  # All destinations
            return {'statusCode': 200}
            
        except Exception as e:
            # Error goes to console, Sentry (event), AND CloudWatch
            logger.error(f"Failed: {e}", exc_info=True)
            return {'statusCode': 500}
```

## Testing

### Console Only (Default)
```python
logger = setup_logging(service_name='test')
logger.info("Test")  # Only console output
```

### With Sentry (No Powertools)
```python
logger = setup_logging(
    service_name='test',
    sentry={'dsn': '...'}
)
logger.error("Error")  # Console + Sentry
```

### With Powertools (No Sentry)
```python
logger = setup_logging(
    service_name='test',
    powertools={'enabled': True}
)
logger.info("Test")  # Console + CloudWatch
```

### With Both
```python
logger = setup_logging(
    service_name='test',
    sentry={'dsn': '...'},
    powertools={'enabled': True}
)
logger.error("Error")  # Console + Sentry + CloudWatch
```

## Advantages Over Separate Loggers

### ❌ Old Approach (Separate)
```python
# Have to call multiple loggers
logger.info("Processing")
sentry_logger.info("Processing")
powertools_logger.info("Processing")

# Have to set context multiple places
with log_context(user_id='123'):
    with sentry_context(user_id='123'):
        with powertools_context(user_id='123'):
            # Finally log...
```

### ✅ New Approach (Unified)
```python
# Single logger call
logger.info("Processing")  # Automatically goes everywhere

# Single context
with log_context(user_id='123'):
    logger.info("Processing")  # Context included everywhere
```

## Performance Considerations

- **Minimal overhead**: Handlers only active if configured
- **No duplication**: Context read once, passed to all handlers
- **Async-safe**: Uses contextvars for proper isolation
- **Lazy evaluation**: Destinations only called if log level matches

## Migration Guide

Existing code doesn't need changes! Just update configuration:

```python
# Before (console only)
logger = setup_logging(service_name='app')

# After (add Powertools)
logger = setup_logging(
    service_name='app',
    powertools={'enabled': True}  # Just add this
)
```

All existing `logger.info()` calls now automatically go to Powertools too!

## Future Extensions

This architecture makes it easy to add more destinations:

- DataDog handler
- Elasticsearch handler
- Custom webhook handler
- etc.

Just implement a `logging.Handler` subclass and add it in `setup_logging()`.
