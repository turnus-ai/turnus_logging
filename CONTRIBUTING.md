# Contributing to turnus-logging

Thank you for your interest in contributing to turnus-logging!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/turnus-ai/turnus-logging.git
cd turnus-logging
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,sentry]"
```

## Running Tests

```bash
pytest tests/
```

## Code Style

We use:
- **black** for formatting
- **flake8** for linting
- **mypy** for type checking

Run before committing:
```bash
black turnus_logging/
flake8 turnus_logging/
mypy turnus_logging/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Reporting Issues

Use GitHub Issues to report bugs or request features. Include:
- Python version
- turnus-logging version
- Minimal reproducible example
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
