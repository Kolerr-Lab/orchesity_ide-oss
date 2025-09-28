"""
LLM Orchestrator Service for Orchesity IDE OSS
Handles intelligent routing across multiple LLM providers with dependency injection
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
import logging

from ..models import OrchestrationRequest, LLMResult, LLMProvider
from ..core.config import Settings
from .cache import CacheService
from .metrics import MetricsService
from .DWA import DynamicWeightAlgorithm, SelectionPolicy


logger = logging.getLogger(__name__)


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


class LLMOrchestratorService:
    """Core orchestrator for multi-LLM operations with DWA integration"""

    def __init__(
        self,
        settings: Settings,
        cache: Optional[CacheService] = None,
        metrics: Optional[MetricsService] = None,
    ):
        self.settings = settings
        self.cache = cache
        self.metrics = metrics
        self.providers_load: Dict[LLMProvider, ProviderLoad] = {}
        self._is_initialized = False

        # Initialize components that will be set up in initialize()
        self.dwa: Optional[DynamicWeightAlgorithm] = None
        self.routing_strategy = RoutingStrategy(settings.routing_strategy)

    async def initialize(self) -> None:
        """Initialize the orchestrator service"""
        if self._is_initialized:
            return

        self._initialize_provider_loads()

        # Initialize Dynamic Weight Algorithm
        self.dwa = DynamicWeightAlgorithm(
            providers=list(LLMProvider),
            selection_policy=self._map_routing_strategy_to_dwa_policy(),
        )

        self._is_initialized = True
        logger.info("LLM Orchestrator Service initialized with DWA integration")

    async def shutdown(self) -> None:
        """Shutdown the orchestrator service"""
        self._is_initialized = False
        logger.info("LLM Orchestrator Service shutdown")

    def _initialize_provider_loads(self):
        """Initialize load tracking for each provider"""
        for provider in LLMProvider:
            self.providers_load[provider] = ProviderLoad(
                provider=provider,
                max_load=self.settings.max_concurrent_requests // len(LLMProvider),
            )

    def _map_routing_strategy_to_dwa_policy(self) -> SelectionPolicy:
        """Map orchestrator routing strategy to DWA selection policy"""
        strategy_mapping = {
            RoutingStrategy.LOAD_BALANCED: SelectionPolicy.WEIGHTED_COMPOSITE,
            RoutingStrategy.ROUND_ROBIN: SelectionPolicy.ROUND_ROBIN,
            RoutingStrategy.RANDOM: SelectionPolicy.ROUND_ROBIN,  # Use round robin for random
            RoutingStrategy.PRIORITY: SelectionPolicy.MAX_ACCURACY,
        }
        return strategy_mapping.get(self.routing_strategy, SelectionPolicy.MAX_ACCURACY)

    async def orchestrate(
        self, request: OrchestrationRequest
    ) -> tuple[List[LLMResult], List[Dict[str, Any]]]:
        """Main orchestration method"""
        logger.info(f"Orchestrating request with {len(request.providers)} providers")

        start_time = time.time()
        results = []
        errors = []

        try:
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

            # Process results and feed back to DWA
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

                    # Update DWA with failure
                    if self.dwa:
                        self.dwa.record_request_result(
                            provider.value,
                            success=False,
                            response_time=1.0,  # Default penalty time
                            error=str(result),
                        )

                    # Record metrics
                    if self.metrics:
                        self.metrics.record_request(
                            provider.value, "unknown", 1.0, success=False
                        )
                else:
                    results.append(result)
                    response_time = getattr(result, "response_time", 1.0)
                    tokens_used = getattr(result, "tokens_used", None)

                    self._update_provider_load(
                        provider, success=True, response_time=response_time
                    )

                    # Update DWA with success
                    if self.dwa:
                        self.dwa.record_request_result(
                            provider.value,
                            success=True,
                            response_time=response_time,
                            tokens_used=int(tokens_used) if tokens_used else None,
                        )

                    # Record metrics
                    if self.metrics:
                        self.metrics.record_request(
                            provider.value,
                            getattr(result, "model", "unknown"),
                            response_time,
                            success=True,
                            tokens_used=tokens_used,
                        )

            # Record overall request metrics
            total_duration = time.time() - start_time
            if self.metrics:
                self.metrics.record_histogram("orchestration_duration", total_duration)

            return results, errors

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            if self.metrics:
                self.metrics.increment_counter("orchestration_errors")
            raise

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

        # Use DWA for intelligent provider selection
        selected_providers = []

        if len(requested_providers) == 1:
            # Single provider requested
            selected_providers = requested_providers
        else:
            # Multiple providers - use DWA selection
            if self.dwa:
                for _ in range(len(requested_providers)):
                    selected_provider = self.dwa.select_provider()
                    if selected_provider:
                        provider_enum = LLMProvider(selected_provider)
                        if provider_enum not in selected_providers:
                            selected_providers.append(provider_enum)
                    if len(selected_providers) >= len(requested_providers):
                        break

            # Fallback to round-robin if DWA fails
            if not selected_providers:
                selected_providers = available_providers[: len(requested_providers)]

        return selected_providers

    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available and configured"""
        # Check if provider has API key configured
        provider_key = f"{provider.value}_api_key"
        api_key = getattr(self.settings, provider_key, None)
        return bool(api_key)

    async def _execute_provider_request(
        self, provider: LLMProvider, request: OrchestrationRequest
    ) -> LLMResult:
        """Execute a request against a specific provider"""
        cache_key = None

        # Check cache first if enabled
        if self.cache and self.settings.enable_caching:
            cache_key = self._generate_cache_key(provider, request)
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for {provider.value}")
                if self.metrics:
                    self.metrics.record_cache_operation("get", hit=True)
                return LLMResult(**cached_result)

        if self.metrics:
            self.metrics.record_cache_operation("get", hit=False)

        # Execute the actual provider request
        start_time = time.time()

        try:
            result = await self._call_provider_api(provider, request)
            response_time = time.time() - start_time

            # Add response time to result
            result.response_time = response_time

            # Cache the result if caching is enabled
            if self.cache and cache_key and self.settings.enable_caching:
                cache_data = {
                    "provider": provider.value,
                    "model": result.model,
                    "response": result.response,
                    "tokens_used": result.tokens_used,
                    "response_time": response_time,
                    "cached_at": time.time(),
                }
                await self.cache.set(cache_key, cache_data)
                if self.metrics:
                    self.metrics.record_cache_operation("set")

            return result

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Provider {provider.value} request failed: {e}")
            raise

    async def _call_provider_api(
        self, provider: LLMProvider, request: OrchestrationRequest
    ) -> LLMResult:
        """Call the actual provider API"""
        # This is a placeholder - in the real implementation, this would
        # call the specific provider SDK (OpenAI, Anthropic, etc.)
        # For now, we'll simulate a response

        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Simulate response based on provider
        if provider == LLMProvider.OPENAI:
            response = f"OpenAI GPT response to: {request.prompt[:50]}..."
            model = "gpt-3.5-turbo"
        elif provider == LLMProvider.ANTHROPIC:
            response = f"Anthropic Claude response to: {request.prompt[:50]}..."
            model = "claude-3-haiku-20240307"
        elif provider == LLMProvider.GEMINI:
            response = f"Google Gemini response to: {request.prompt[:50]}..."
            model = "gemini-pro"
        elif provider == LLMProvider.GROK:
            response = f"Grok response to: {request.prompt[:50]}..."
            model = "grok-beta"
        else:
            response = f"Unknown provider response to: {request.prompt[:50]}..."
            model = "unknown"

        return LLMResult(
            provider=provider,
            model=model,
            response=response,
            tokens_used=random.randint(100, 500),
            finish_reason="stop",
        )

    def _generate_cache_key(
        self, provider: LLMProvider, request: OrchestrationRequest
    ) -> str:
        """Generate a cache key for the request"""
        import hashlib

        key_data = f"{provider.value}:{request.prompt}:{request.model or 'default'}"
        return f"llm:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"

    def _update_provider_load(
        self,
        provider: LLMProvider,
        success: bool,
        response_time: Optional[float] = None,
    ):
        """Update provider load tracking"""
        load_info = self.providers_load[provider]

        if success:
            load_info.response_time = response_time or 1.0
            load_info.error_rate = max(
                0, load_info.error_rate - 0.01
            )  # Decrease error rate
        else:
            load_info.error_rate = min(
                1.0, load_info.error_rate + 0.05
            )  # Increase error rate

    async def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        stats = {}

        for provider, load_info in self.providers_load.items():
            stats[provider.value] = {
                "current_load": load_info.current_load,
                "max_load": load_info.max_load,
                "response_time": load_info.response_time,
                "error_rate": load_info.error_rate,
                "available": self._is_provider_available(provider),
            }

        # Add DWA stats if available
        if self.dwa:
            stats["dwa"] = self.dwa.get_stats()

        return stats

    @property
    def is_initialized(self) -> bool:
        """Check if orchestrator service is initialized"""
        return self._is_initialized
