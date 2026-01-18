"""
Context storage and reader for logging.

This module provides context storage using contextvars for thread-safe isolation.
"""

import contextvars
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Thread-safe context storage
_context_var: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    'context', default=None
)


def set_context(context: Optional[Dict[str, Any]]) -> None:
    """Set the execution context."""
    _context_var.set(context)


def get_context() -> Optional[Dict[str, Any]]:
    """
    Get the current execution context.
    
    Returns:
        The complete context dictionary, or None if not set
    """
    return _context_var.get()


def append_context(context: Dict[str, Any]) -> None:
    """
    Append/merge new values into the existing context.
    
    Args:
        context: Dictionary of values to merge into current context
    """
    current = get_context()
    if current is None:
        _context_var.set(context.copy())
    else:
        merged = current.copy()
        merged.update(context)
        _context_var.set(merged)


def clear_context() -> None:
    """Clear the execution context."""
    _context_var.set(None)


@contextmanager
def log_context(**kwargs: Any):
    """
    Context manager that automatically manages logging context lifecycle.
    
    Usage:
        from turnus_logging import log_context
        
        with log_context(request_id='123', user_id='abc'):
            # Context is set here
            logger.info("Processing request")
        # Context is automatically cleared here
    
    Args:
        **kwargs: Any key-value pairs to add to the context
    """
    # Save the current context to restore later
    previous_context = get_context()
    
    # Merge new context with existing context (preserve service, etc.)
    if previous_context:
        new_context = {**previous_context, **kwargs}
    else:
        new_context = kwargs
    
    set_context(new_context)
    try:
        yield
    finally:
        # Restore previous context instead of clearing completely
        set_context(previous_context)

