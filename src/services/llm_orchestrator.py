"""
LLM Orchestrator Service for Orchesity IDE OSS
Handles intelligent routing across multiple LLM providers
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random

from ..models import OrchestrationRequest, LLMResult, LLMProvider
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RoutingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    RANDOM = "random"
    PRIORITY = "priority"


@dataclass
class ProviderLoad:
    provider: LLMProvider
    current_load: int = 0
    max_load: int = 10
    response_time: float = 0.0
    error_rate: float = 0.0


class LLMOrchestrator:
    """Core orchestrator for multi-LLM operations"""

    def __init__(self):
        self.providers_load: Dict[LLMProvider, ProviderLoad] = {}
        self._initialize_provider_loads()
        self.routing_strategy = RoutingStrategy(settings.routing_strategy)

    def _initialize_provider_loads(self):
        """Initialize load tracking for each provider"""
        for provider in LLMProvider:
            self.providers_load[provider] = ProviderLoad(
                provider=provider,
                max_load=settings.max_concurrent_requests // len(LLMProvider),
            )

    async def orchestrate(
        self, request: OrchestrationRequest
    ) -> tuple[List[LLMResult], List[Dict[str, Any]]]:
        """Main orchestration method"""
        logger.info(f"Orchestrating request with {len(request.providers)} providers")

        results = []
        errors = []

        # Determine which providers to use
        providers_to_use = self._select_providers(request.providers)

        # Execute requests concurrently
        tasks = []
        for provider in providers_to_use:
            task = asyncio.create_task(
                self._execute_provider_request(provider, request)
            )
            tasks.append(task)

        # Wait for all tasks to complete
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(task_results):
            provider = providers_to_use[i]
            if isinstance(result, Exception):
                error_info = {
                    "provider": provider.value,
                    "error": str(result),
                    "timestamp": time.time(),
                }
                errors.append(error_info)
                self._update_provider_load(provider, success=False)
            else:
                results.append(result)
                self._update_provider_load(
                    provider, success=True, response_time=result.get("response_time", 0)
                )

        return results, errors

    def _select_providers(
        self, requested_providers: List[LLMProvider]
    ) -> List[LLMProvider]:
        """Select providers based on routing strategy"""
        available_providers = [
            p for p in requested_providers if self._is_provider_available(p)
        ]

        if not available_providers:
            # Fallback to any available provider
            available_providers = [
                p for p in LLMProvider if self._is_provider_available(p)
            ]

        if not available_providers:
            raise ValueError("No LLM providers are configured or available")

        if self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_select(available_providers)
        elif self.routing_strategy == RoutingStrategy.LOAD_BALANCED:
            return self._load_balanced_select(available_providers)
        elif self.routing_strategy == RoutingStrategy.RANDOM:
            return [random.choice(available_providers)]
        elif self.routing_strategy == RoutingStrategy.PRIORITY:
            return self._priority_select(available_providers)
        else:
            return available_providers[:1]  # Default to first available

    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is configured and not overloaded"""
        load = self.providers_load[provider]

        # Check if API key is configured
        if not self._has_api_key(provider):
            return False

        # Check load capacity
        return load.current_load < load.max_load

    def _has_api_key(self, provider: LLMProvider) -> bool:
        """Check if provider has API key configured"""
        if provider == LLMProvider.OPENAI:
            return bool(settings.openai_api_key)
        elif provider == LLMProvider.ANTHROPIC:
            return bool(settings.anthropic_api_key)
        elif provider == LLMProvider.GEMINI:
            return bool(settings.gemini_api_key)
        elif provider == LLMProvider.GROK:
            return bool(settings.grok_api_key)
        return False

    def _round_robin_select(self, providers: List[LLMProvider]) -> List[LLMProvider]:
        """Round-robin provider selection"""
        # Simple implementation - in production, track last used
        return providers[:1]

    def _load_balanced_select(self, providers: List[LLMProvider]) -> List[LLMProvider]:
        """Load-balanced provider selection"""
        # Select provider with lowest current load
        sorted_providers = sorted(
            providers, key=lambda p: self.providers_load[p].current_load
        )
        return sorted_providers[:1]

    def _priority_select(self, providers: List[LLMProvider]) -> List[LLMProvider]:
        """Priority-based provider selection"""
        # Define priority order (can be configurable)
        priority_order = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.GEMINI,
            LLMProvider.GROK,
        ]

        for priority_provider in priority_order:
            if priority_provider in providers:
                return [priority_provider]

        return providers[:1]

    async def _execute_provider_request(
        self, provider: LLMProvider, request: OrchestrationRequest
    ) -> LLMResult:
        """Execute request against a specific provider"""
        start_time = time.time()

        try:
            # Increment load
            self.providers_load[provider].current_load += 1

            # Simulate API call (replace with actual provider SDK calls)
            response = await self._call_provider_api(provider, request)

            response_time = time.time() - start_time

            return LLMResult(
                provider=provider,
                response=response,
                response_time=response_time,
                tokens_used=len(response.split()) * 1.3,  # Rough estimate
                model=self._get_provider_model(provider),
            )

        finally:
            # Decrement load
            self.providers_load[provider].current_load -= 1

    async def _call_provider_api(
        self, provider: LLMProvider, request: OrchestrationRequest
    ) -> str:
        """Call the actual provider API"""
        # This is a placeholder - in real implementation, use actual SDKs
        await asyncio.sleep(0.1)  # Simulate network delay

        if provider == LLMProvider.OPENAI:
            return f"[OpenAI GPT-4] Response to: {request.prompt[:50]}..."
        elif provider == LLMProvider.ANTHROPIC:
            return f"[Anthropic Claude] Response to: {request.prompt[:50]}..."
        elif provider == LLMProvider.GEMINI:
            return f"[Google Gemini] Response to: {request.prompt[:50]}..."
        elif provider == LLMProvider.GROK:
            return f"[xAI Grok] Response to: {request.prompt[:50]}..."
        else:
            return f"[Unknown Provider] Response to: {request.prompt[:50]}..."

    def _get_provider_model(self, provider: LLMProvider) -> str:
        """Get the model name for a provider"""
        model_map = {
            LLMProvider.OPENAI: "gpt-4",
            LLMProvider.ANTHROPIC: "claude-3-sonnet",
            LLMProvider.GEMINI: "gemini-pro",
            LLMProvider.GROK: "grok-1",
        }
        return model_map.get(provider, "unknown")

    def _update_provider_load(
        self, provider: LLMProvider, success: bool, response_time: float = 0
    ):
        """Update provider load statistics"""
        load = self.providers_load[provider]

        if success:
            # Update response time (simple moving average)
            load.response_time = (load.response_time + response_time) / 2
            # Decrease error rate
            load.error_rate = max(0, load.error_rate - 0.01)
        else:
            # Increase error rate
            load.error_rate = min(1.0, load.error_rate + 0.1)

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers"""
        stats = {}
        for provider, load in self.providers_load.items():
            stats[provider.value] = {
                "current_load": load.current_load,
                "max_load": load.max_load,
                "response_time": round(load.response_time, 3),
                "error_rate": round(load.error_rate, 3),
                "available": self._is_provider_available(provider),
            }
        return stats
