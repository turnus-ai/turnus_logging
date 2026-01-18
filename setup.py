"""
Setup configuration for turnus_logging package.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="turnus-logging",
    version="0.1.0",
    author="Turnus AI",
    author_email="dev@turnus.ai",
    description="A flexible logging system with automatic context propagation and Sentry integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/turnus-ai/turnus-logging",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies - none! Uses only stdlib
    ],
    extras_require={
        "sentry": [
            "sentry-sdk>=2.35.0",  # Required for Sentry Logs product
        ],
        "powertools": [
            "aws-lambda-powertools>=2.0.0",  # AWS Lambda Powertools integration
        ],
        "all": [
            "sentry-sdk>=2.35.0",
            "aws-lambda-powertools>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="logging context sentry async",
    project_urls={
        "Bug Reports": "https://github.com/turnus-ai/turnus-logging/issues",
        "Source": "https://github.com/turnus-ai/turnus-logging",
    },
)
