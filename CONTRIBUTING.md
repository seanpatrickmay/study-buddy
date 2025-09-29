# Contributing to Study Buddy

Thanks for your interest in improving Study Buddy! This document captures the conventions used throughout the project so contributions remain consistent and maintainable.

## Getting Started

1. Fork the repository and create a feature branch from `main`.
2. Install dependencies with `pip install -r requirements.txt` (use a virtual environment).
3. Copy `.env.example` if available, or export the required environment variables listed in the README.

## Development Workflow

- **Formatting** – Run `ruff format src tests` to apply the project formatting rules.
- **Linting** – Run `ruff check src tests` and address all reported issues.
- **Testing** – Add or update tests under `tests/` and run `pytest` before opening a pull request.
- **Type Hints** – All public functions and methods should include type annotations.
- **Docstrings** – Public modules, classes, and functions must include descriptive docstrings following Google or Sphinx style.

## Pull Request Checklist

- [ ] The change set is focused and scoped to a single problem.
- [ ] New or modified behaviour is covered by tests.
- [ ] Documentation and examples are updated if applicable.
- [ ] Linting (`ruff check`) and tests (`pytest`) pass locally.

## Reporting Issues

When filing an issue, please include:

- A concise summary of the problem.
- Steps to reproduce and expected vs. actual behaviour.
- Relevant logs, stack traces, or screenshots.
- Environment details (OS, Python version, Study Buddy commit).

Thank you for helping make Study Buddy a better learning companion!
