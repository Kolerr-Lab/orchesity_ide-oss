# Contributing to Orchesity IDE OSS

Thank you for your interest in contributing to Orchesity IDE OSS! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/Orchesity_IDE_OSS.git
   cd Orchesity_IDE_OSS
   ```
3. **Set up development environment**:
   ```bash
   make dev-install
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🧪 Development Workflow

### Code Quality Standards

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **bandit**: Security linting

### Running Quality Checks

```bash
# Run all quality checks
make ci

# Or run individually
make lint        # Check formatting and linting
make format      # Auto-format code
make type-check  # Type checking
make test        # Run tests
make security    # Security checks
```

### Testing

- Write tests for new features in `tests/`
- Maintain test coverage above 80%
- Run tests before submitting PR: `make test-cov`

## 📝 Pull Request Process

1. **Update documentation** for any new features
2. **Add tests** for new functionality
3. **Ensure CI passes** - all checks must pass
4. **Update CHANGELOG.md** if needed
5. **Submit PR** with clear description

### PR Template

Please use this template for pull requests:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
```

## 🏗️ Architecture Guidelines

### Adding New LLM Providers

1. **Create provider class** in `src/services/`:
   ```python
   from ..models import LLMProvider

   class NewProvider:
       async def generate(self, prompt: str, **kwargs) -> str:
           # Implementation here
           pass
   ```

2. **Update models** in `src/models.py`:
   ```python
   class LLMProvider(str, Enum):
       # Add new provider
       NEW_PROVIDER = "new_provider"
   ```

3. **Update orchestrator** in `src/services/llm_orchestrator.py`

4. **Add configuration** in `src/config.py`

5. **Add tests** in `tests/`

### API Design

- Use RESTful conventions
- Include comprehensive OpenAPI documentation
- Handle errors gracefully with appropriate HTTP status codes
- Validate inputs using Pydantic models

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions/classes
- Update API documentation in code comments

## 🔒 Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Run security checks: `make security`
- Report security issues privately to maintainers

## 🎯 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute

## 📞 Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Discord/Slack**: For real-time chat (if available)

## 🙏 Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors list
- Future release notes

Thank you for contributing to Orchesity IDE OSS! 🎭🤖