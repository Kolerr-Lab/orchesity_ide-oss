# Orchesity IDE OSS

[![CI](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/actions/workflows/ci.yml/badge.svg)](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/orchesity-ide-oss.svg)](https://pypi.org/project/orchesity-ide-oss/)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source Integrated Development Environment for Multi-LLM Orchestration, built with FastAPI and modern web technologies. **Save 25-40% on API costs** while improving performance and reliability through intelligent provider selection.

## Features

- **Multi-LLM Orchestration**: Seamlessly integrate and orchestrate multiple Large Language Models (OpenAI, Anthropic, Gemini, Grok)
- **Dynamic Weight Algorithm (DWA)**: Intelligent provider selection based on performance metrics, cost optimization, and reliability
- **Redis Caching**: High-performance caching for LLM responses, session data, and workflow results
- **PostgreSQL Database**: Persistent storage for orchestration history, user sessions, workflows, and analytics
- **Intelligent Routing**: Advanced load-based routing with failure detection and automatic fallback
- **Real-Time Monitoring**: Live health checks, performance metrics, and provider analytics
- **Web-Based IDE**: Visual workflow builder for designing LLM orchestration pipelines
- **Custom Weighting Strategies**: Configurable algorithms for cost, speed, accuracy, or balanced optimization
- **Developer-Friendly**: Simple setup with Docker Compose and comprehensive documentation
- **Extensible Architecture**: Plugin system for adding new LLM providers and custom strategies

## 🏗️ Architecture

```mermaid
graph TB
    A[Web UI] --> B[FastAPI Backend]
    B --> C[DWA Engine]
    B --> D[Redis Cache]
    B --> E[PostgreSQL DB]
    C --> F[LLM Providers]
    F --> G[OpenAI]
    F --> H[Anthropic]
    F --> I[Gemini]
    F --> J[Grok]
    
    subgraph "Core Features"
        C
        D
        E
    end
    
    subgraph "Intelligence Layer"
        K[Provider Selection]
        L[Performance Tracking]
        M[Cost Optimization]
        N[Failure Detection]
    end
    
    C --> K
    K --> L
    L --> M
    M --> N
```

**Key Components:**

- **DWA (Dynamic Weight Algorithm)**: Intelligent provider selection and performance optimization
- **Redis Cache**: High-speed caching for responses and session data
- **PostgreSQL**: Persistent storage for analytics and workflow management
- **FastAPI Backend**: Async orchestration engine with real-time monitoring

## Prerequisites

- **Python 3.9+** (Required for async SQLAlchemy and modern typing)
- **Docker & Docker Compose** (Recommended for full stack deployment)
- **PostgreSQL 15+** (or use Docker Compose setup)
- **Redis 7+** (or use Docker Compose setup)
- **API keys** for LLM providers (OpenAI, Anthropic, Gemini, Grok)

## Quick Start

### Option 1: Docker Compose (Recommended)

Full stack with PostgreSQL, Redis, and DWA enabled:

```bash
# Clone the repository
git clone https://github.com/Kolerr-Lab/Orchesity_IDE_OSS.git
cd orchesity-ide-oss

# Create environment file
cp .env.example .env
# Add your LLM API keys to .env

# Start full stack
docker-compose up -d

# View logs
docker-compose logs -f orchesity-ide-oss
```

### Option 2: Docker Build

Build and run with Docker:

```bash
# Build image
docker build -t orchesity-ide-oss:latest .

# Run with basic setup (no persistence)
docker run -p 8000:8000 --env-file .env orchesity-ide-oss:latest
```

### Option 3: Local Development

For development with external Redis/PostgreSQL:

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database URLs

# Run application
uvicorn src.main:app --reload
```

### Option 4: PyPI Installation

```bash
pip install orchesity-ide-oss
```

**Access Points:**

- **Web Interface**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

## 📖 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **LLM Providers** | | |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `GROK_API_KEY` | xAI Grok API key | - |
| **Database & Cache** | | |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://orchesity:orchesity@localhost:5432/orchesity_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `REDIS_DB` | Redis database number | 0 |
| `CACHE_EXPIRE_SECONDS` | Default cache expiration | 3600 |
| **Orchestration** | | |
| `ROUTING_STRATEGY` | Provider selection strategy | `load_balanced` |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | 5 |
| `REQUEST_TIMEOUT` | Request timeout in seconds | 30 |
| **Application** | | |
| `LOG_LEVEL` | Logging level | INFO |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |

### Dynamic Weight Algorithm (DWA)

Orchesity IDE OSS features an intelligent **Dynamic Weight Algorithm** that automatically optimizes provider selection based on real-time performance metrics:

**Selection Strategies:**

- `max_accuracy` - Prioritize providers with highest success rates
- `min_cost` - Optimize for lowest cost per token
- `min_latency` - Select fastest responding providers  
- `weighted_composite` - Balanced optimization across all metrics
- `round_robin` - Simple rotation between providers

**Custom Weighting:**

```python
# Example: Cost-optimized strategy
def cost_strategy(provider):
    return (provider.accuracy * provider.availability) / provider.cost

# Apply custom strategy
orchestrator.set_custom_dwa_weighting(cost_strategy)
```

**Automatic Learning:**

- Tracks response times, accuracy, and failure rates
- Learns from every request to improve future selections
- Automatically excludes failing providers
- Provides detailed analytics and metrics

### Redis Caching

**Intelligent Caching System:**

- **LLM Response Caching**: Automatic caching based on prompt+provider+model hash
- **Session Storage**: User session data with configurable expiration
- **Workflow Results**: Temporary storage for complex orchestration results
- **Performance Metrics**: Cache hit rates and optimization statistics

### PostgreSQL Database

**Persistent Storage Features:**

- **Request History**: Complete audit trail of all orchestration requests
- **Performance Analytics**: Provider metrics, response times, and costs
- **User Sessions**: Persistent user data and preferences
- **Workflow Management**: Save and execute complex multi-step workflows
- **Error Tracking**: Detailed error logs and failure analysis

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

```text
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

## � Documentation

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

- **[LLM Orchestration Benefits](./docs/LLM_ORCHESTRATION_BENEFITS.md)** - Detailed analysis of cost savings, performance improvements, and ROI from multi-LLM orchestration
- **[API Documentation](./docs/API_DOCUMENTATION.md)** - Complete API reference and usage examples
- **[Database Setup](./docs/DATABASE_SETUP.md)** - PostgreSQL configuration and schema details
- **[Docker Deployment](./docs/DOCKER.md)** - Containerized deployment guide
- **[Migration Guide](./docs/MIGRATION_GUIDE.md)** - Upgrading from previous versions

## �📞 Support

- **Issues**: [GitHub Issues](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kolerr-Lab/Orchesity_IDE_OSS/discussions)
- **Documentation**: See the [`docs/`](./docs/) directory for comprehensive guides

---

**Happy orchestrating! 🎭🤖**
