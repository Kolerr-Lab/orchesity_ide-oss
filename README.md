# Orchesity IDE OSS

[![CI](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/actions/workflows/ci.yml/badge.svg)](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/orchesity-ide-oss.svg)](https://pypi.org/project/orchesity-ide-oss/)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source Integrated Development Environment for Multi-LLM Orchestration, built with FastAPI and modern web technologies.

## Features

- **Multi-LLM Orchestration**: Seamlessly integrate and orchestrate multiple Large Language Models (OpenAI, Anthropic, Gemini, Grok)
- **Intelligent Routing**: Automatic load-based routing between sync and async processing
- **Web-Based IDE**: Visual workflow builder for designing LLM orchestration pipelines
- **Real-Time Monitoring**: Live health checks and performance metrics
- **Developer-Friendly**: Simple setup and comprehensive documentation
- **Extensible Architecture**: Plugin system for adding new LLM providers

## 🏗️ Architecture

```
Frontend (Web UI) ←→ FastAPI Backend ←→ LLM Providers
     ↓                        ↓
Visual Builder          Orchestration Engine
Real-time Editor        Intelligent Routing
Team Collaboration      Multi-LLM Management
```

## Prerequisites

- Python 3.8+
- Node.js 16+ (for web UI development)
- API keys for LLM providers (OpenAI, Anthropic, etc.)

## Quick Start

### Option 1: Install from PyPI (Recommended)
```bash
pip install orchesity-ide-oss
```

### Option 2: Install from Source
1. **Clone the repository**
   ```bash
   git clone https://github.com/Kolerr-Lab/Orchesity_IDE_OSS.git
   cd orchesity-ide-oss
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

4. **Run the application**
   ```bash
   uvicorn src.main:app --reload
   ```

5. **Open your browser**
   ```
   http://localhost:8000
   ```

## 📖 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `GROK_API_KEY` | xAI Grok API key | - |
| `LOG_LEVEL` | Logging level | INFO |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | 5 |

### LLM Provider Configuration

The IDE supports multiple LLM providers with automatic failover and load balancing:

```python
# Example configuration
llm_config = {
    "providers": {
        "openai": {"model": "gpt-4", "priority": 1},
        "anthropic": {"model": "claude-3", "priority": 2},
        "gemini": {"model": "gemini-pro", "priority": 3}
    },
    "routing": "intelligent"  # or "round-robin", "priority"
}
```

## Building and Publishing

### Build for PyPI
```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Test locally (optional)
pip install dist/orchesity_ide_oss-1.0.0.tar.gz
```

### Publish to PyPI
```bash
# Upload to PyPI
twine upload dist/*
```

### Test on TestPyPI First
```bash
# Upload to test PyPI
twine upload --repository testpypi dist/*

# Install from test PyPI
pip install -i https://test.pypi.org/simple/ orchesity-ide-oss
```

## 📁 Project Structure

```
orchesity-ide-oss/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── src/                         # Source code
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration settings
│   ├── models.py                # Pydantic models
│   ├── routers/                 # API endpoints
│   │   ├── llm.py               # LLM orchestration routes
│   │   ├── user.py              # User management routes
│   │   └── health.py            # Health check routes
│   ├── services/                # Business logic
│   │   ├── llm_orchestrator.py  # Core orchestration logic
│   │   └── user_service.py      # User/session handling
│   └── utils/                   # Utilities
│       ├── logger.py            # Logging utilities
│       └── helpers.py           # Helper functions
├── tests/                       # Test suite
│   ├── test_llm.py              # LLM tests
│   └── test_health.py           # Health check tests
└── web/                         # Web interface
    └── static/
        └── index.html           # Basic HTML interface
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Submit a pull request

### Adding New LLM Providers

1. Create a new provider class in `src/services/`
2. Implement the `LLMProvider` interface
3. Add configuration in `src/config.py`
4. Update tests and documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the powerful orchestration concepts from the original Orchesity platform
- Inspired by the need for accessible multi-LLM development tools
- Thanks to the open-source community for amazing libraries and frameworks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/discussions)
- **Documentation**: [Wiki](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/wiki)

---

**Happy orchestrating! 🎭🤖**