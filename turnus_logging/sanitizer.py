"""
Payload sanitization utilities for safe logging.
"""

import json
from typing import Any, Dict, Set

# Fields to redact (case-insensitive matching)
SENSITIVE_FIELD_PATTERNS = {
    'password',
    'passwd',
    'pwd',
    'secret',
    'token',
    'api_key',
    'apikey',
    'access_key',
    'private_key',
    'auth',
    'authorization',
    'session',
    'cookie',
    'csrf',
    'xsrf',
}

# Field names that indicate file uploads
FILE_FIELD_PATTERNS = {
    'file',
    'upload',
    'attachment',
    'document',
    'image',
    'video',
    'audio',
}

# Maximum sizes
MAX_STRING_LENGTH = 1000  # Truncate long strings
MAX_LIST_ITEMS = 50  # Limit list size
MAX_DICT_ITEMS = 100  # Limit dict size
MAX_TOTAL_SIZE = 10_000  # Max chars in final JSON


def is_sensitive_field(field_name: str) -> bool:
    """Check if field name matches sensitive patterns."""
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in SENSITIVE_FIELD_PATTERNS)


def is_file_field(field_name: str) -> bool:
    """Check if field name indicates file upload."""
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in FILE_FIELD_PATTERNS)


def sanitize_value(value: Any, field_name: str = '') -> Any:
    """
    Sanitize a single value.

    Args:
        value: Value to sanitize
        field_name: Name of the field (for context-aware sanitization)

    Returns:
        Sanitized value
    """
    # Redact sensitive fields
    if field_name and is_sensitive_field(field_name):
        return '[REDACTED]'

    # Remove file data
    if field_name and is_file_field(field_name):
        if isinstance(value, (bytes, bytearray)):
            return f'[FILE: {len(value)} bytes]'
        elif isinstance(value, str) and len(value) > 1000:
            # Likely base64 encoded file
            return f'[FILE: ~{len(value)} chars]'
        return '[FILE]'

    # Handle different types
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        # Truncate long strings
        if len(value) > MAX_STRING_LENGTH:
            return value[:MAX_STRING_LENGTH] + f'... [truncated, total: {len(value)} chars]'
        return value

    if isinstance(value, bytes):
        return f'[BINARY: {len(value)} bytes]'

    if isinstance(value, (list, tuple)):
        # Limit list size
        sanitized = [sanitize_value(item, field_name) for item in value[:MAX_LIST_ITEMS]]
        if len(value) > MAX_LIST_ITEMS:
            sanitized.append(f'... [truncated, total: {len(value)} items]')
        return sanitized

    if isinstance(value, dict):
        return sanitize_dict(value)

    # For other types, convert to string representation
    str_repr = str(value)
    if len(str_repr) > MAX_STRING_LENGTH:
        return f'[{type(value).__name__}: {str_repr[:100]}... truncated]'
    return str_repr


def sanitize_dict(data: Dict[str, Any], max_items: int = MAX_DICT_ITEMS) -> Dict[str, Any]:
    """
    Sanitize a dictionary recursively.

    Args:
        data: Dictionary to sanitize
        max_items: Maximum number of items to keep

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    count = 0

    for key, value in data.items():
        if count >= max_items:
            sanitized['__truncated__'] = f'... [truncated, total: {len(data)} keys]'
            break

        sanitized[key] = sanitize_value(value, field_name=key)
        count += 1

    return sanitized


def sanitize_payload(
    payload: Any,
    max_size: int = MAX_TOTAL_SIZE,
    additional_redact_fields: Set[str] | None = None,
) -> Dict[str, Any] | str:
    """
    Sanitize a payload for safe logging.

    Args:
        payload: Payload to sanitize (dict, list, or other)
        max_size: Maximum size of final JSON string
        additional_redact_fields: Additional field names to redact

    Returns:
        Sanitized payload (dict or string representation)
    """
    if payload is None:
        return {'payload': None}

    # Add any custom fields to redact
    if additional_redact_fields:
        global SENSITIVE_FIELD_PATTERNS
        original_patterns = SENSITIVE_FIELD_PATTERNS.copy()
        SENSITIVE_FIELD_PATTERNS.update(f.lower() for f in additional_redact_fields)

    try:
        # Make a deep copy to avoid modifying original
        if isinstance(payload, dict):
            sanitized = sanitize_dict(payload)
        elif isinstance(payload, (list, tuple)):
            sanitized = sanitize_value(payload, '')
        else:
            sanitized = sanitize_value(payload, '')

        # Check final size
        try:
            json_str = json.dumps(sanitized)
            if len(json_str) > max_size:
                return {
                    'payload': '[TRUNCATED: payload too large]',
                    'size': len(json_str),
                    'max_size': max_size,
                }
        except (TypeError, ValueError):
            # If can't serialize, return string representation
            return {'payload': str(sanitized)[:max_size]}

        return sanitized

    finally:
        # Restore original patterns if we modified them
        if additional_redact_fields:
            SENSITIVE_FIELD_PATTERNS = original_patterns


def sanitize_request_payload(
    method: str,
    path: str,
    headers: Dict[str, str] | None = None,
    query_params: Dict[str, Any] | None = None,
    body: Any = None,
) -> Dict[str, Any]:
    """
    Sanitize request data for logging.

    Args:
        method: HTTP method
        path: Request path
        headers: Request headers
        query_params: Query parameters
        body: Request body

    Returns:
        Sanitized request data
    """
    sanitized: Dict[str, Any] = {
        'method': method,
        'path': path,
    }

    # Sanitize headers (redact Authorization, Cookie, etc.)
    if headers:
        sanitized_headers = {}
        for key, value in headers.items():
            if is_sensitive_field(key):
                sanitized_headers[key] = '[REDACTED]'
            else:
                sanitized_headers[key] = value[:100] if len(value) > 100 else value
        sanitized['headers'] = sanitized_headers

    # Sanitize query params
    if query_params:
        sanitized['query_params'] = sanitize_dict(query_params)

    # Sanitize body
    if body is not None:
        sanitized['body'] = sanitize_payload(body)

    return sanitized


def sanitize_response_metadata(
    status_code: int,
    duration_ms: float,
    headers: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """
    Extract response metadata (NO payload).

    Args:
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        headers: Response headers

    Returns:
        Response metadata only
    """
    metadata: Dict[str, Any] = {
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2),
    }

    # Include useful headers (content-type, content-length)
    if headers:
        useful_headers = {}
        for key in ['content-type', 'content-length', 'content-encoding']:
            if key in headers:
                useful_headers[key] = headers[key]
        if useful_headers:
            metadata['headers'] = useful_headers

    return metadata


def get_payload_summary(payload: Any) -> str:
    """
    Get a brief summary of payload (for quick logging).

    Args:
        payload: Any payload

    Returns:
        Brief string summary
    """
    if payload is None:
        return 'null'

    if isinstance(payload, dict):
        keys = list(payload.keys())[:5]
        more = f' (+{len(payload) - 5} more)' if len(payload) > 5 else ''
        return f'dict with keys: {keys}{more}'

    if isinstance(payload, (list, tuple)):
        return f'{type(payload).__name__} with {len(payload)} items'

    if isinstance(payload, str):
        return f'string ({len(payload)} chars)'

    if isinstance(payload, bytes):
        return f'bytes ({len(payload)} bytes)'

    return f'{type(payload).__name__}'
