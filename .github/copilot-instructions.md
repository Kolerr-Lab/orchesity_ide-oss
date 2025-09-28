# Orchesity IDE OSS - AI Developer Guide

## Project Overview

Orchesity IDE OSS is a **Multi-LLM Orchestration IDE** built with FastAPI. The system features intelligent provider selection via Dynamic Weight Algorithm (DWA), Redis caching, PostgreSQL persistence, and advanced performance optimization.

**Core Architecture**: FastAPI backend → DWA Engine → Redis Cache → PostgreSQL DB → Multiple Provider SDKs → Web UI

**New in v2**: Dynamic Weight Algorithm, Redis caching, PostgreSQL integration, custom weighting strategies, and comprehensive analytics.

## Essential File Structure

```
src/
├── main.py              # FastAPI app with database/cache initialization
├── config.py            # Pydantic settings with Redis/PostgreSQL config
├── models.py            # Pydantic models for requests/responses
├── database/            # Database layer
│   ├── models.py       # SQLAlchemy models (requests, sessions, workflows)
│   ├── schemas.py      # Pydantic schemas for database operations
│   └── database.py     # Async database connection and operations
├── routers/             # API endpoints grouped by domain
│   ├── llm.py          # Orchestration + DWA endpoints (/dwa/stats, /dwa/reset)
│   ├── health.py       # System health with DWA status
│   ├── user.py         # Session management
│   └── database.py     # Database and cache management endpoints
├── services/
│   ├── llm_orchestrator.py  # Core orchestrator with DWA integration
│   ├── DWA.py          # Dynamic Weight Algorithm engine
│   ├── cache.py        # Redis caching service
│   ├── database.py     # Database CRUD operations
│   └── dwa_strategies.py  # Custom weighting strategy examples
└── utils/
    └── logger.py       # Centralized logging setup
```

## Key Patterns & Conventions

### 1. Configuration Management
- **All settings** via `src/config.py` using `pydantic-settings`
- Environment variables auto-loaded from `.env` file
- **API keys**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`
- **Database**: `DATABASE_URL`, `DATABASE_ECHO`, connection pooling settings
- **Redis**: `REDIS_URL`, `REDIS_DB`, `CACHE_EXPIRE_SECONDS`, connection pool config
- **DWA**: Routing strategy configurable: `load_balanced`, `round_robin`, `random`, `priority`

### 2. Request/Response Pattern
- **Always use Pydantic models** from `src/models.py` for API contracts
- `OrchestrationRequest` → `OrchestrationResponse` for LLM operations
- Request IDs generated as `f"req_{int(time.time() * 1000)}"`
- Async processing triggered when `len(providers) > 1` or `stream=True`

### 3. LLM Orchestration with DWA
- **Dynamic selection** via `DynamicWeightAlgorithm` with real-time performance metrics
- **Provider metrics** tracked: accuracy, speed, cost, availability, failure rates
- **Caching integration** automatic cache-first lookup with Redis
- **Database persistence** all requests/responses stored in PostgreSQL
- **Custom strategies** pluggable weighting algorithms (cost, speed, accuracy, balanced)
- **Concurrent execution** using `asyncio.gather()` with intelligent failover

### 4. Router Organization
- Each domain gets its own router (llm, health, user)
- Background tasks for async operations: `background_tasks.add_task()`
- Provider testing endpoint: `/api/llm/test/{provider}` for connectivity checks

## Development Workflows

### Running the Application
```bash
# Development server with auto-reload
uvicorn src.main:app --reload

# Or using Python module
python -m src.main

# Using Makefile
make run
```

### Environment Setup
- **Required**: Create `.env` file with LLM provider API keys
- **Development**: Use `setup_development.py` for automated environment setup
- **Testing**: `pytest tests/` or `make test`

### Code Quality
- **Formatting**: Black with 88-char line length (configured in `pyproject.toml`)
- **Type checking**: MyPy with strict settings
- **Testing**: Pytest with FastAPI TestClient

## Key Integration Points

### Provider SDK Integration
- **OpenAI**: Standard `openai` library pattern
- **Anthropic**: Uses `anthropic` SDK
- **Gemini**: Google's `google-generativeai` package
- Each provider checked for configuration in `/api/llm/providers`

### Async vs Sync Processing
- **Sync**: Single provider requests return immediately
- **Async**: Multiple providers or streaming → background processing
- Status checking via `/api/llm/status/{request_id}` (placeholder implementation)

### Health Monitoring
- **System resources**: CPU/memory via `psutil`
- **Provider status**: Configuration-based availability checks
- **Service discovery**: Returns all configured providers with status

## Common Development Tasks

### Adding New LLM Provider
1. Add enum value to `LLMProvider` in `models.py`
2. Add API key setting to `config.py`
3. Implement provider logic in `llm_orchestrator.py`
4. Update health checks in `health.py`

### Adding New API Endpoint
1. Create/extend router in `src/routers/`
2. Define Pydantic models in `models.py`
3. Include router in `main.py` with prefix and tags
4. Add tests in `tests/`

### Debugging Tips
- **API docs**: Available at `http://localhost:8000/docs`
- **Health status**: Check `/api/health` for system state
- **Provider testing**: Use `/api/llm/test/{provider}` for connectivity
- **Logging**: Centralized via `utils/logger.py` with configurable levels

## Build & Deploy

- **PyPI package**: Uses `pyproject.toml` with setuptools backend
- **Dependencies**: Core deps in `requirements.txt`, dev deps as optional extras
- **Docker**: Dockerfile included for containerized deployment
- **Build command**: `python -m build` (creates wheel and source distribution)