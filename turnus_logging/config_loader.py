"""
Optional configuration file support for turnus_logging.

This allows users to configure logging behavior without touching code.
"""

import json
import os
from typing import Dict, Any, Optional


def load_logging_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load logging configuration from file or environment variables.
    
    Looks for config in this order:
    1. Explicit config_path parameter
    2. LOGGING_CONFIG_FILE environment variable
    3. ./logging_config.json (current directory)
    4. ~/.turnus_logging.json (home directory)
    
    Config file format (JSON):
    {
        "service_name": "my-api",
        "log_level": "INFO",
        "sentry": {
            "dsn": "https://...",  // Can also use ${SENTRY_DSN} to reference env var
            "environment": "production",
            "event_level": "ERROR",
            "breadcrumb_level": "INFO"
        },
        "middleware": {
            "type": "fastapi",  // or "flask", "django"
            "request_id_header": "X-Request-ID",
            "generate_request_id": true,
            "include_method": true,
            "include_path": true,
            "include_client_ip": false,
            "capture_headers": [
                "X-API-Version",
                "X-Tenant-ID",
                "X-User-Agent"
            ],
            "exclude_paths": ["/health", "/metrics"]  // Don't log these paths
        }
    }
    
    Environment variable format:
    LOGGING_SERVICE_NAME=my-api
    LOGGING_LEVEL=INFO
    LOGGING_CAPTURE_HEADERS=X-API-Version,X-Tenant-ID
    SENTRY_DSN=https://...
    SENTRY_ENVIRONMENT=production
    
    Returns:
        Configuration dict
    """
    config = {}
    
    # Try to load from file
    if config_path is None:
        # Check env var
        config_path = os.getenv('LOGGING_CONFIG_FILE')
        
        # Check default locations
        if config_path is None:
            for path in ['./logging_config.json', os.path.expanduser('~/.turnus_logging.json')]:
                if os.path.exists(path):
                    config_path = path
                    break
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Expand environment variable references like ${SENTRY_DSN}
            config = _expand_env_vars(config)
    
    # Override/supplement with environment variables
    config = _merge_env_vars(config)
    
    return config


def _expand_env_vars(config: Any) -> Any:
    """Recursively expand ${VAR_NAME} references in config."""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
        var_name = config[2:-1]
        return os.getenv(var_name, config)
    return config


def _merge_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge environment variables into config."""
    # Service name
    if os.getenv('LOGGING_SERVICE_NAME'):
        config['service_name'] = os.getenv('LOGGING_SERVICE_NAME')
    
    # Log level
    if os.getenv('LOGGING_LEVEL'):
        config['log_level'] = os.getenv('LOGGING_LEVEL')
    
    # Sentry config
    if 'sentry' not in config:
        config['sentry'] = {}
    
    if os.getenv('SENTRY_DSN'):
        config['sentry']['dsn'] = os.getenv('SENTRY_DSN')
    
    if os.getenv('SENTRY_ENVIRONMENT'):
        config['sentry']['environment'] = os.getenv('SENTRY_ENVIRONMENT')
    
    # Middleware config
    if 'middleware' not in config:
        config['middleware'] = {}
    
    # Capture headers from comma-separated env var
    capture_headers = os.getenv('LOGGING_CAPTURE_HEADERS')
    if capture_headers:
        config['middleware']['capture_headers'] = [h.strip() for h in capture_headers.split(',')]
    
    return config


# Industry-standard headers that are safe to capture
SAFE_HEADERS = [
    'X-Request-ID',
    'X-Correlation-ID',
    'X-API-Version',
    'X-Client-Version',
    'X-Tenant-ID',
    'X-Organization-ID',
    'User-Agent',
    'X-Forwarded-For',
    'X-Real-IP',
    'Content-Type',
    'Accept',
    'Accept-Language',
]

# Headers that should NEVER be captured (security-sensitive)
BLOCKED_HEADERS = [
    'Authorization',
    'Cookie',
    'Set-Cookie',
    'X-API-Key',
    'X-Auth-Token',
    'Proxy-Authorization',
    'WWW-Authenticate',
]


def is_safe_header(header_name: str) -> bool:
    """Check if a header is safe to capture."""
    header_lower = header_name.lower()
    
    # Block sensitive headers
    for blocked in BLOCKED_HEADERS:
        if blocked.lower() in header_lower:
            return False
    
    # Block anything with 'secret', 'password', 'key', 'token'
    sensitive_words = ['secret', 'password', 'key', 'token', 'auth']
    if any(word in header_lower for word in sensitive_words):
        return False
    
    return True
