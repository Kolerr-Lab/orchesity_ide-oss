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

from .config import settings
from .routers import llm, user, health
from .utils.logger import setup_logger

# Setup logging
setup_logger()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Open-source Multi-LLM Orchestration IDE",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
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


# Include routers
app.include_router(llm, prefix="/api/llm", tags=["LLM Orchestration"])
app.include_router(user, prefix="/api/user", tags=["User Management"])
app.include_router(health, prefix="/api/health", tags=["Health Checks"])


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


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print("🚀 Starting Orchesity IDE OSS...")
    print(f"📖 API Documentation: http://localhost:{settings.port}/docs")
    print(f"🌐 Web Interface: http://localhost:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    print("👋 Shutting down Orchesity IDE OSS...")


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
