"""
LLM orchestration router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import asyncio
import time
from ..models import OrchestrationRequest, OrchestrationResponse, LLMResult, LLMProvider
from ..services.llm_orchestrator import LLMOrchestrator
from ..config import settings
from ..utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize orchestrator
orchestrator = LLMOrchestrator()


@router.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_llms(
    request: OrchestrationRequest, background_tasks: BackgroundTasks
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
            background_tasks.add_task(process_orchestration_async, request_id, request)

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
    """Get the status of an orchestration request"""
    # In a real implementation, this would check a database or cache
    # For now, return a placeholder
    return {
        "request_id": request_id,
        "status": "unknown",
        "message": "Status tracking not yet implemented",
    }


@router.get("/providers")
async def list_providers():
    """List available LLM providers and their status"""
    providers_status = {}

    for provider in LLMProvider:
        is_configured = False
        model = "unknown"

        if provider == LLMProvider.OPENAI and settings.openai_api_key:
            is_configured = True
            model = "gpt-4"
        elif provider == LLMProvider.ANTHROPIC and settings.anthropic_api_key:
            is_configured = True
            model = "claude-3"
        elif provider == LLMProvider.GEMINI and settings.gemini_api_key:
            is_configured = True
            model = "gemini-pro"
        elif provider == LLMProvider.GROK and settings.grok_api_key:
            is_configured = True
            model = "grok-1"

        providers_status[provider.value] = {
            "configured": is_configured,
            "model": model,
            "status": "available" if is_configured else "not_configured",
        }

    return {
        "providers": providers_status,
        "routing_strategy": settings.routing_strategy,
        "max_concurrent_requests": settings.max_concurrent_requests,
    }


@router.post("/test/{provider}")
async def test_provider(provider: LLMProvider):
    """Test a specific LLM provider"""
    try:
        test_prompt = "Hello! Please respond with just 'Hello from [Provider Name]'"

        # Create a simple test request
        test_request = OrchestrationRequest(
            prompt=test_prompt, providers=[provider], max_tokens=50
        )

        results, errors = await orchestrator.orchestrate(test_request)

        if errors:
            return {
                "provider": provider.value,
                "status": "error",
                "error": errors[0].get("error", "Unknown error"),
            }

        if results:
            return {
                "provider": provider.value,
                "status": "success",
                "response": results[0].get("response", ""),
                "response_time": results[0].get("response_time", 0),
            }

        return {"provider": provider.value, "status": "no_response"}

    except Exception as e:
        logger.error(f"Provider test failed for {provider}: {e}")
        return {"provider": provider.value, "status": "error", "error": str(e)}


@router.get("/dwa/stats")
async def get_dwa_statistics():
    """Get Dynamic Weight Algorithm statistics and provider metrics"""
    try:
        return orchestrator.get_dwa_statistics()
    except Exception as e:
        logger.error(f"Failed to get DWA statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dwa/reset")
async def reset_dwa_metrics(provider: str = None):
    """Reset DWA metrics for a specific provider or all providers"""
    try:
        orchestrator.reset_dwa_metrics(provider)
        return {
            "message": f"Reset DWA metrics for {'all providers' if not provider else provider}",
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Failed to reset DWA metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dwa/best-provider")
async def get_best_provider():
    """Get the current best provider according to DWA"""
    try:
        best_provider = orchestrator.dwa.select_best_provider()
        if best_provider:
            provider_stats = orchestrator.dwa.provider_metrics[best_provider]
            return {
                "best_provider": best_provider,
                "accuracy": provider_stats.accuracy,
                "speed": provider_stats.speed,
                "availability": provider_stats.availability,
                "consecutive_failures": provider_stats.consecutive_failures
            }
        else:
            return {"best_provider": None, "message": "No providers available"}
    except Exception as e:
        logger.error(f"Failed to get best provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_orchestration_async(request_id: str, request: OrchestrationRequest):
    """Process orchestration asynchronously"""
    try:
        logger.info(f"Processing async orchestration: {request_id}")

        results, errors = await orchestrator.orchestrate(request)

        # In a real implementation, store results in database/cache
        # For now, just log completion
        logger.info(
            f"Completed async orchestration: {request_id}, "
            f"results: {len(results)}, errors: {len(errors)}"
        )

    except Exception as e:
        logger.error(f"Async orchestration failed: {request_id}, error: {e}")
