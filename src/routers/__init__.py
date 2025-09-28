# Routers package

from .llm import router as llm_router
from .user import router as user_router
from .health import router as health_router

# Re-export for convenience
llm = llm_router
user = user_router
health = health_router
