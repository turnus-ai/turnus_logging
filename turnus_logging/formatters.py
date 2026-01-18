"""
Custom log formatters that include context information.
"""

import logging
from typing import Optional

from .context import get_context


class ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Get context and add all fields to record
        context = get_context()
        
        # Build context string from all fields
        context_parts = []
        if context:
            for key, value in context.items():
                setattr(record, key, value)
                context_parts.append(f'{key}={value}')
        
        # Add formatted context string to record
        record.context_str = f'[{", ".join(context_parts)}]' if context_parts else '[-]'

        # Call parent formatter with enriched record
        return super().format(record)


class CompactContextFormatter(ContextFormatter):
    pass


class VerboseContextFormatter(ContextFormatter):
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        if fmt is None:
            fmt = get_verbose_format()
        super().__init__(fmt, datefmt)


def get_default_format() -> str:
    return (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(context_str)s - '
        '%(message)s'
    )


def get_compact_format() -> str:
    return '%(asctime)s - %(levelname)s - %(context_str)s - %(message)s'


def get_verbose_format() -> str:
    return (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(context_str)s - '
        '%(module)s.%(funcName)s:%(lineno)d - '
        '%(message)s'
    )


def get_json_format() -> str:
    return (
        '{"timestamp":"%(asctime)s", "logger":"%(name)s", "level":"%(levelname)s", '
        '"request_id":"%(request_id)s", "user_id":"%(user_id)s", '
        '"organization_id":"%(organization_id)s", "message":"%(message)s"}'
    )
