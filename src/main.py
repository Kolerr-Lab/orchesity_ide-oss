"""
Orchesity IDE OSS - Multi-LLM Orchestration IDE
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
from pathlib import Path
from contextlib import asynccontextmanager

from .core.config import settings
from .core.container import init_container, ServiceContainer, lifespan_context
from .routers import llm, user, health, database
from .utils.logger import setup_logger

# Setup logging
setup_logger()


# Initialize FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    async with lifespan_context(settings) as container:
        # Store container for router access
        app.state.container = container
        yield


app = FastAPI(
    title=settings.app_name,
    description="Open-source Multi-LLM Orchestration IDE",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Initialize container for synchronous access (for testing)
container = init_container(settings)

# For testing, initialize services synchronously if possible
# This allows tests to run without async context
try:
    # Try to initialize lightweight services synchronously
    from src.services.health import HealthService
    from src.services.metrics import MetricsService
    from src.services.llm_orchestrator import LLMOrchestratorService

    container.health = HealthService(settings)
    container.metrics = MetricsService(settings)
    container.orchestrator = LLMOrchestratorService(settings, container.cache, container.metrics)
    container._services['healthservice'] = container.health
    container._services['metricsservice'] = container.metrics
    container._services['llmorchestratorservice'] = container.orchestrator
except Exception as e:
    # If initialization fails, services will be None - tests should handle this
    pass

# Include routers immediately (not in lifespan)
app.include_router(
    llm.create_router(container), prefix="/api/llm", tags=["LLM Orchestration"]
)
app.include_router(
    user.create_router(container), prefix="/api/user", tags=["User Management"]
)
app.include_router(
    health.create_router(container),
    prefix="/api/health",
    tags=["Health Checks"],
)
app.include_router(
    database.create_router(container),
    prefix="/api/db",
    tags=["Database & Cache"],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
web_path = Path(__file__).parent.parent / "web"
static_path = web_path / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    html_path = web_path / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback HTML if index.html doesn't exist
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchesity IDE OSS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; color: #333; }
            .api-link { display: inline-block; margin: 20px 0; padding: 10px 20px; background: #007acc; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎭🤖 Orchesity IDE OSS</h1>
                <p>Multi-LLM Orchestration IDE</p>
            </div>
            <div style="text-align: center;">
                <a href="/docs" class="api-link">📖 API Documentation</a>
                <br><br>
                <p><strong>Status:</strong> <span id="status">Loading...</span></p>
            </div>
        </div>
        <script>
            // Simple health check
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML =
                        data.status === 'healthy' ? '✅ System Healthy' : '❌ System Issues';
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '❌ Connection Error';
                });
        </script>
    </body>
    </html>
    """

    # Fallback HTML if index.html doesn't exist
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchesity IDE OSS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; color: #333; }
            .api-link { display: inline-block; margin: 20px 0; padding: 10px 20px; background: #007acc; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎭🤖 Orchesity IDE OSS</h1>
                <p>Multi-LLM Orchestration IDE</p>
            </div>
            <div style="text-align: center;">
                <a href="/docs" class="api-link">📖 API Documentation</a>
                <br><br>
                <p><strong>Status:</strong> <span id="status">Loading...</span></p>
            </div>
        </div>
        <script>
            // Simple health check
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML =
                        data.status === 'healthy' ? '✅ System Healthy' : '❌ System Issues';
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '❌ Connection Error';
                });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
