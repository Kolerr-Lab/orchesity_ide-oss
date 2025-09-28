"""
LLM orchestration router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any
import asyncio
import time
import logging
from ..models import OrchestrationRequest, OrchestrationResponse, LLMResult, LLMProvider
from ..core.container import ServiceContainer
from ..services.llm_orchestrator import LLMOrchestratorService

logger = logging.getLogger(__name__)


def create_router(container: ServiceContainer) -> APIRouter:
    """Create LLM router with dependency injection"""
    router = APIRouter()

    def get_orchestrator() -> LLMOrchestratorService:
        """Dependency injection for orchestrator service"""
        return container.get_service(LLMOrchestratorService)

    def get_settings():
        """Get settings from container"""
        return container.settings

    @router.post("/orchestrate", response_model=OrchestrationResponse)
    async def orchestrate_llms(
        request: OrchestrationRequest,
        background_tasks: BackgroundTasks,
        orchestrator: LLMOrchestratorService = Depends(get_orchestrator),
    ):
        """Orchestrate requests across multiple LLM providers"""
        try:
            # Generate request ID
            request_id = f"req_{int(time.time() * 1000)}"

            logger.info(f"Starting orchestration request: {request_id}")

            # Check if we should use async processing
            use_async = len(request.providers) > 1 or request.stream

            if use_async:
                # Async processing for multiple providers or streaming
                background_tasks.add_task(
                    process_orchestration_async, request_id, request, orchestrator
                )

                return OrchestrationResponse(
                    request_id=request_id, status="processing", results=[], errors=[]
                )
            else:
                # Sync processing for single provider
                results, errors = await orchestrator.orchestrate(request)

                return OrchestrationResponse(
                    request_id=request_id,
                    status="completed",
                    results=results,
                    errors=errors,
                )

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status/{request_id}")
    async def get_orchestration_status(request_id: str):
        """Get the status of an async orchestration request"""
        # TODO: Implement proper async request tracking
        # For now, return a placeholder response
        return {
            "request_id": request_id,
            "status": "completed",  # Placeholder
            "message": "Async orchestration tracking not yet implemented",
        }

    @router.get("/providers")
    async def get_available_providers(
        orchestrator: LLMOrchestratorService = Depends(get_orchestrator),
    ):
        """Get information about available LLM providers"""
        try:
            logger.info("Getting provider stats...")
            # Get provider stats from orchestrator
            provider_stats = await orchestrator.get_provider_stats()
            logger.info(f"Got provider stats: {list(provider_stats.keys())}")

            # Build provider information
            providers_info = []
            settings = get_settings()
            logger.info(f"Settings: enable_caching={settings.enable_caching}")

            for provider in LLMProvider:
                provider_name = provider.value
                is_configured = False

                # Check if provider is configured
                if provider == LLMProvider.OPENAI and settings.openai_api_key:
                    is_configured = True
                elif provider == LLMProvider.ANTHROPIC and settings.anthropic_api_key:
                    is_configured = True
                elif provider == LLMProvider.GEMINI and settings.gemini_api_key:
                    is_configured = True
                elif provider == LLMProvider.GROK and settings.grok_api_key:
                    is_configured = True

                provider_info = {
                    "name": provider_name,
                    "configured": is_configured,
                    "available": is_configured
                    and provider_stats.get(provider_name, {}).get("available", False),
                    "stats": provider_stats.get(provider_name, {}),
                }
                providers_info.append(provider_info)

            result = {
                "providers": providers_info,
                "routing_strategy": settings.routing_strategy,
                "max_concurrent_requests": settings.max_concurrent_requests,
                "enable_caching": settings.enable_caching,
            }
            logger.info(f"Returning result with {len(providers_info)} providers")
            return result

        except Exception as e:
            logger.error(f"Failed to get provider information: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/test/{provider}")
    async def test_provider(
        provider: str, orchestrator: LLMOrchestratorService = Depends(get_orchestrator)
    ):
        """Test connectivity to a specific LLM provider"""
        try:
            # Validate provider
            try:
                provider_enum = LLMProvider(provider)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid provider: {provider}"
                )

            # Create a simple test request
            test_request = OrchestrationRequest(
                prompt="Hello, this is a test message. Please respond with 'Test successful'.",
                providers=[provider_enum],
                model="test-model",
                max_tokens=50,
            )

            # Execute test orchestration
            results, errors = await orchestrator.orchestrate(test_request)

            if results and len(results) > 0:
                return {
                    "provider": provider,
                    "status": "success",
                    "response": (
                        results[0].response[:100] + "..."
                        if len(results[0].response) > 100
                        else results[0].response
                    ),
                    "response_time": getattr(results[0], "response_time", None),
                    "tokens_used": getattr(results[0], "tokens_used", None),
                }
            else:
                return {
                    "provider": provider,
                    "status": "failed",
                    "errors": [str(error) for error in errors],
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Provider test failed for {provider}: {e}")
            raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

    @router.get("/stats")
    async def get_orchestration_stats(
        orchestrator: LLMOrchestratorService = Depends(get_orchestrator),
    ):
        """Get orchestration statistics and DWA metrics"""
        try:
            provider_stats = await orchestrator.get_provider_stats()

            return {
                "provider_stats": provider_stats,
                "system_info": {
                    "routing_strategy": container.settings.routing_strategy,
                    "max_concurrent_requests": container.settings.max_concurrent_requests,
                    "enable_caching": container.settings.enable_caching,
                    "lightweight_mode": container.settings.lightweight_mode,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get orchestration stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


async def process_orchestration_async(
    request_id: str, request: OrchestrationRequest, orchestrator: LLMOrchestratorService
):
    """Process orchestration request asynchronously"""
    logger.info(f"Processing async orchestration: {request_id}")

    try:
        results, errors = await orchestrator.orchestrate(request)

        # TODO: Store results in database/cache for retrieval via /status/{request_id}
        # For now, just log the completion
        logger.info(
            f"Async orchestration completed: {request_id} - {len(results)} results, {len(errors)} errors"
        )

    except Exception as e:
        logger.error(f"Async orchestration failed: {request_id} - {e}")
