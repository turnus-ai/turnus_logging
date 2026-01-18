# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-18

### Added
- Initial release of turnus-logging
- Core logging with contextvars-based context management
- `log_context()` context manager for temporary context injection
- `append_context()` for adding to existing context
- Dynamic log formatting with `ContextFormatter`
- Optional Sentry integration with automatic context enrichment
- Sentry tags for searchable context fields
- FastAPI, Flask, and Django middleware for automatic request context
- Configuration via JSON file or environment variables
- Safe header validation to prevent sensitive data logging
- Payload sanitization utilities
- Zero core dependencies (stdlib only)
- Thread-safe and async-safe context management
- AWS Lambda integration examples
- Comprehensive documentation and examples

### Features
- ✅ Zero dependencies core
- ✅ Automatic context propagation
- ✅ Thread & async safe
- ✅ Non-blocking logging
- ✅ Optional Sentry with flat tags
- ✅ Web framework middleware
- ✅ Configuration system
- ✅ Lambda-ready

[0.1.0]: https://github.com/turnus-ai/turnus-logging/releases/tag/v0.1.0
