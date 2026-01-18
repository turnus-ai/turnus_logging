# Installation Guide

## Quick Install

### From GitHub (Recommended for now)

```bash
pip install git+https://github.com/turnus-ai/turnus-logging.git
```

### With Sentry Support

```bash
pip install "git+https://github.com/turnus-ai/turnus-logging.git#egg=turnus-logging[sentry]"
```

### From PyPI (Once published)

```bash
pip install turnus-logging

# With Sentry
pip install turnus-logging[sentry]
```

## Requirements

- Python 3.8 or higher
- No core dependencies (stdlib only!)
- Optional: `sentry-sdk>=2.35.0` for Sentry integration

## Verification

After installation, verify it works:

```python
from turnus_logging import setup_logging, get_logger

setup_logging(service_name='test')
logger = get_logger(__name__)
logger.info("turnus-logging is working!")
```

## Integration Examples

### FastAPI

```bash
pip install "git+https://github.com/turnus-ai/turnus-logging.git" fastapi uvicorn
```

```python
from fastapi import FastAPI
from turnus_logging import setup_logging
from turnus_logging.middleware import FastAPILoggingMiddleware

setup_logging(service_name='my-api')
app = FastAPI()
app.add_middleware(FastAPILoggingMiddleware)
```

### AWS Lambda

1. Create `requirements.txt`:
```
turnus-logging @ git+https://github.com/turnus-ai/turnus-logging.git
sentry-sdk>=2.35.0  # Optional
```

2. Package for Lambda:
```bash
pip install -r requirements.txt -t ./package/
cp lambda_function.py ./package/
cd package && zip -r ../lambda.zip . && cd ..
```

3. Deploy to AWS Lambda

### Flask

```bash
pip install "git+https://github.com/turnus-ai/turnus-logging.git" flask
```

```python
from flask import Flask
from turnus_logging import setup_logging
from turnus_logging.middleware import FlaskLoggingMiddleware

app = Flask(__name__)
setup_logging(service_name='my-flask-app')
FlaskLoggingMiddleware(app)
```

### Django

```bash
pip install "git+https://github.com/turnus-ai/turnus-logging.git" django
```

Add to `settings.py`:
```python
MIDDLEWARE = [
    'turnus_logging.middleware.DjangoLoggingMiddleware',
    # ... other middleware
]
```

## Troubleshooting

### Import Error

If you get `ModuleNotFoundError: No module named 'turnus_logging'`:

1. Check installation: `pip list | grep turnus-logging`
2. Verify virtual environment is activated
3. Try reinstalling: `pip uninstall turnus-logging && pip install git+https://github.com/turnus-ai/turnus-logging.git`

### Context Not Working

If context doesn't appear in logs:

1. Make sure `setup_logging()` is called before any logging
2. Check you're using `with log_context()` or middleware
3. Verify logger is from `get_logger(__name__)`, not `logging.getLogger()`

### Sentry Not Working

If Sentry isn't receiving logs:

1. Install Sentry extra: `pip install turnus-logging[sentry]`
2. Set `SENTRY_DSN` environment variable
3. Check Sentry DSN is valid
4. Verify log level is ERROR or higher for events

## Upgrading

```bash
pip install --upgrade git+https://github.com/turnus-ai/turnus-logging.git
```

## Uninstalling

```bash
pip uninstall turnus-logging
```
