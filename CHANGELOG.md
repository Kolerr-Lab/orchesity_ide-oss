# Changelog

All notable changes to Orchesity IDE OSS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Orchesity IDE OSS
- Multi-LLM orchestration with OpenAI, Anthropic, Gemini, and Grok support
- Intelligent load-based routing (round-robin, load-balanced, priority)
- Web-based IDE interface with real-time orchestration
- FastAPI backend with comprehensive API documentation
- Health monitoring and provider status tracking
- Session management for user workflows
- Docker containerization support
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Code quality tools (Black, isort, flake8, mypy)
- Security scanning with Bandit and Safety
- MIT license for open-source distribution

### Technical Details
- Python 3.9+ compatibility
- Pydantic v2 for data validation
- Async/await support for concurrent LLM calls
- Environment-based configuration
- Structured logging with configurable levels
- RESTful API design with OpenAPI documentation

## [1.0.0] - 2025-01-XX

### Added
- Core LLM orchestration engine
- Web interface for workflow management
- API endpoints for health checks, provider management, and orchestration
- Basic authentication and session handling
- Docker and docker-compose support
- Development tooling and CI/CD setup

### Changed
- Initial public release

### Fixed
- N/A (initial release)

---

## Types of changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities