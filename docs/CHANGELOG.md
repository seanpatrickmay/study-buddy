# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the versioning scheme is [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive repository restructure using a `src/` layout and dedicated `docs/` and `tests/` directories.
- MIT license, contribution guidelines, and `.env.example` for easier onboarding.
- Unit tests covering flashcard generation filters and LaTeX sanitisation logic.

### Changed
- Migrated all modules under the `study_buddy` package with descriptive imports and type hints.
- Rewrote the FastAPI application factory to use dependency injection and structured logging.
- Trimmed dependency list and standardised tooling via `pyproject.toml` and Ruff configuration.

### Removed
- Deprecated compatibility scripts, outdated utility modules, and generated database artefacts.

## [0.1.0] - 2024-12-01

### Added
- Initial study workflow combining document ingestion, flashcard creation, and cheat-sheet generation.
- Minimalist web interface for uploading study materials and downloading outputs.
- CrewAI-based agents for key-term extraction and cheat-sheet synthesis.
