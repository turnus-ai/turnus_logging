# Turnus Logging

A flexible, standalone Python logging library with automatic context propagation, custom log context injection, and optional Sentry integration.

## Features

✅ **Zero Dependencies** - Core functionality uses only Python stdlib  
✅ **Automatic Context** - Request ID and user info attached to every log  
✅ **Custom Context Injection** - Add temporary context with `log_context()`  
✅ **Thread & Async Safe** - Uses `contextvars` for proper isolation  
✅ **Non-Obtrusive** - Just use `logger.info()` - everything else is automatic  
✅ **Sentry Integration** - Optional, with automatic context enrichment  
✅ **Payload Sanitization** - Built-in tools to redact sensitive data  

## Installation

```bash
# From PyPI (once published)
pip install turnus-logging

# With Sentry support
pip install turnus-logging[sentry]

# From GitHub (latest)
pip install git+https://github.com/turnus-ai/turnus-logging.git

# For development
git clone https://github.com/turnus-ai/turnus-logging.git
cd turnus-logging
pip install -e ".[dev,sentry]"
```

## Quick Start

```python
import logging
from turnus_logging import setup_logging, log_context

# Setup once at application start
logger = setup_logging(
    service_name="my-app",
    log_level=logging.INFO,
)

# Use anywhere in your code
logger.info("Application started")

# Add custom context
with log_context(order_id='12345', step='payment'):
    logger.info("Processing order")  # Includes order_id and step
    
    # Nested contexts work too
    with log_context(gateway='stripe'):
        logger.info("Calling payment gateway")  # Includes all parent context
```

## Core Concepts

### 1. Automatic Context Propagation

Request ID and user context are automatically included in all logs:

```python
from turnus_logging import set_request_id, set_user_context, UserContext

# Usually set by middleware
set_request_id('req_abc123')
set_user_context(UserContext(
    user_id='user_789',
    username='john.doe',
    organization='acme-corp'
))

logger.info("Processing request")
# Output: 2026-01-16 10:30:00 - INFO - [req_id=req_abc123] [user=user_789] [org=acme-corp] - Processing request
```

### 2. Custom Log Context

Inject temporary context that applies to all logs within a scope:

```python
with log_context(order_id='order_123', amount=99.99):
    logger.info("Order received")
    
    with log_context(step='validation'):
        logger.info("Validating order")  # Includes order_id, amount, AND step
        
    with log_context(step='payment'):
        logger.info("Processing payment")  # Includes order_id, amount, AND step (new value)
```

**Context automatically cleans up** when exiting the `with` block.

### 3. Context Isolation

Each request/task has isolated context (thanks to `contextvars`):

```python
import asyncio

async def handle_request(request_id, user_id):
    set_request_id(request_id)
    with log_context(user_id=user_id):
        logger.info("Handling request")  # Only sees THIS request's context

# These run concurrently but contexts don't mix
await asyncio.gather(
    handle_request('req_1', 'user_a'),
    handle_request('req_2', 'user_b'),
)
```

## Complete Example

See `example.py` for a full working demonstration:

```bash
python example.py
```

## Configuration Options

```python
setup_logging(
    service_name='my-app',           # Logger name
    log_level=logging.INFO,          # Minimum log level
    console_format=None,             # Custom format string (optional)
    enable_console=True,             # Enable console output
    
    # Sentry integration (optional)
    sentry_dsn='https://...',        # Sentry DSN
    sentry_environment='production', # Environment tag
    sentry_event_level=logging.ERROR,     # Log level for Sentry events
    sentry_breadcrumb_level=logging.INFO, # Log level for breadcrumbs
)
```

## Log Formats

Built-in format options:

```python
from turnus_logging import (
    get_default_format,   # Standard format with request_id and user context
    get_compact_format,   # Minimal format
    get_verbose_format,   # Includes module, function, line number
    get_json_format,      # JSON format for structured logging
)

logger = setup_logging(
    service_name='my-app',
    console_format=get_verbose_format(),
)
```

## Payload Sanitization

Built-in tools to safely log request/response data:

```python
from turnus_logging import (
    sanitize_payload,
    sanitize_request_payload,
    sanitize_response_metadata,
)

# Sanitize any payload (redacts passwords, tokens, files)
safe_data = sanitize_payload(user_input)
logger.info("User data", extra={'data': safe_data})

# Sanitize request
safe_request = sanitize_request_payload(
    method='POST',
    path='/api/users',
    body=request_body
)
logger.info("API request", extra=safe_request)

# Response metadata only (no body)
response_meta = sanitize_response_metadata(
    status_code=200,
    duration_ms=125.5
)
logger.info("API response", extra=response_meta)
```

## API Reference

### Context Management

```python
# Request ID
set_request_id(request_id: str)
get_request_id() -> Optional[str]

# User Context
set_user_context(context: UserContext)
get_user_context() -> Optional[UserContext]

# Custom Log Context
log_context(**kwargs)  # Context manager
get_log_context() -> Dict[str, Any]
set_log_context(context: Dict[str, Any])
update_log_context(context: Dict[str, Any])

# Get all context
get_context_dict() -> Dict[str, Any]
```

### Logging Setup

```python
setup_logging(...) -> logging.Logger
get_logger(name: Optional[str] = None) -> logging.Logger
```

### Formatters

```python
ContextFormatter  # Formatter class
get_default_format() -> str
get_compact_format() -> str
get_verbose_format() -> str
get_json_format() -> str
```

### Sanitization

```python
sanitize_payload(payload: Any, ...) -> Dict[str, Any]
sanitize_request_payload(method, path, ...) -> Dict[str, Any]
sanitize_response_metadata(status_code, duration_ms, ...) -> Dict[str, Any]
get_payload_summary(payload: Any) -> str
```

## Development

```bash
# Clone the repository
git clone https://github.com/turnus-ai/turnus-logging.git
cd turnus-logging

# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Format code
black turnus_logging/
isort turnus_logging/

# Type checking
mypy turnus_logging/
```

## Architecture

The library is organized into focused modules:

- **`context.py`** - Context management using `contextvars` (zero dependencies)
- **`formatters.py`** - Log formatters that read from context
- **`setup.py`** - Logging configuration and Sentry integration
- **`sanitizer.py`** - Payload sanitization utilities
- **`__init__.py`** - Public API exports

## Use Cases

### Web Application with Middleware

```python
from fastapi import FastAPI, Request
from turnus_logging import setup_logging, set_request_id, log_context
import uuid

app = FastAPI()
logger = setup_logging(service_name='api')

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    set_request_id(request_id)
    
    response = await call_next(request)
    return response

@app.post("/orders")
async def create_order(order_data: dict):
    with log_context(order_id=order_data['id']):
        logger.info("Creating order")
        # All logs here include request_id and order_id
        return {"status": "created"}
```

### Background Tasks

```python
with log_context(task_id=task_id, task_type='cleanup'):
    logger.info("Starting background task")
    # Process...
    logger.info("Task completed")
```

### Complex Operations with Nested Context

```python
with log_context(transaction_id=tx_id):
    logger.info("Starting transaction")
    
    with log_context(step='validate'):
        validate()  # Logs include transaction_id + step
    
    with log_context(step='execute'):
        execute()  # Logs include transaction_id + step (new value)
    
    logger.info("Transaction complete")  # Back to just transaction_id
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/turnus-ai/turnus-logging/issues
- Documentation: See `turnus_logging/README.md` for detailed usage

---

Made with ❤️ by Turnus AI
