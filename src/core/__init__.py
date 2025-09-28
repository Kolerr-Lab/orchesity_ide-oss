"""
Core package for Orchesity IDE OSS
Contains dependency injection, configuration, and base services
"""

from .container import ServiceContainer, get_container, init_container, lifespan_context

__all__ = ["ServiceContainer", "get_container", "init_container", "lifespan_context"]
