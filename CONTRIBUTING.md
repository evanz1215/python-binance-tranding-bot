# Contributing to Python Binance Trading Bot

Thank you for your interest in contributing to this trading bot project! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/python-binance-trading-bot.git`
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt` or `uv sync`

## Development Workflow

1. Create a new branch for your feature: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `python -m pytest`
4. Run linting: `flake8 src/` and `mypy src/`
5. Commit your changes with a descriptive message
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep line length under 88 characters (Black formatter standard)
- Use meaningful variable and function names

## Commit Message Guidelines

We follow the Conventional Commits specification:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or modifying tests
- `chore:` for maintenance tasks

Example: `feat: add RSI strategy with customizable parameters`

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting a PR
- Include integration tests for API endpoints
- Test with different market conditions

## Security

- Never commit API keys or sensitive credentials
- Use environment variables for configuration
- Follow security best practices for financial applications

## Issue Reporting

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant log messages

## Pull Request Guidelines

- Ensure your PR has a clear title and description
- Reference any related issues
- Include tests for new functionality
- Update documentation if needed
- Ensure CI/CD checks pass

## Code Review Process

1. All PRs require at least one review
2. Address all review comments
3. Ensure CI/CD pipeline passes
4. Maintainer will merge after approval

## Questions?

Feel free to open an issue for questions or join our discussions.

Thank you for contributing! 🚀
