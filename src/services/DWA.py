"""
DynamicWeightAlgorithm v2 (OSS Edition)
---------------------------------------
A simplified provider weighting and orchestration engine.

Features (OSS):
- Simple moving average updates for metrics
- Custom weighting strategy hook
- Batch requests
- Basic semantic cache (exact match only)
- Multi-LLM fallback
- Error handling

Note: Advanced features (EMA updates, adaptive drift tracing, auto-healing,
bandit policies, semantic similarity search) are available in enterprise.
"""

import random
import time
from typing import List, Dict, Any, Optional, Callable, Tuple, Generator
from dataclasses import dataclass, field
from enum import Enum

from ..models import LLMProvider
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderMetrics:
    """Provider performance metrics for DWA"""
    name: str
    provider_type: LLMProvider
    cost: float = 0.0
    speed: float = 1.0  # seconds
    accuracy: float = 0.8
    availability: float = 1.0
    feedback: float = 0.0
    
    # History tracking for moving averages
    cost_history: List[float] = field(default_factory=list)
    speed_history: List[float] = field(default_factory=list)
    accuracy_history: List[float] = field(default_factory=list)
    availability_history: List[float] = field(default_factory=list)
    
    # Failure tracking
    consecutive_failures: int = 0
    last_success_time: Optional[float] = None
    last_error: Optional[str] = None


class SelectionPolicy(str, Enum):
    """Provider selection policies"""
    MAX_ACCURACY = "max_accuracy"
    MIN_COST = "min_cost"
    MIN_LATENCY = "min_latency"
    WEIGHTED_COMPOSITE = "weighted_composite"
    ROUND_ROBIN = "round_robin"


# --- Provider Metrics Update (OSS Placeholder) ---
def update_metrics(provider: ProviderMetrics, latency_s=None, success=None, feedback_delta=None):
    """
    Update provider metrics with simple overrides.
    Extend with advanced updaters in enterprise edition.
    """
    if latency_s is not None:
        provider.speed = latency_s
    if success is not None:
        provider.accuracy = 1.0 if success else 0.0
        if success:
            provider.consecutive_failures = 0
            provider.last_success_time = time.time()
        else:
            provider.consecutive_failures += 1
    if feedback_delta is not None:
        provider.feedback = feedback_delta


# --- Simple Provider Selection ---
def choose_provider(
    providers: List[ProviderMetrics], 
    policy: SelectionPolicy = SelectionPolicy.MAX_ACCURACY
) -> Tuple[Optional[str], Dict[str, float], Dict[str, Any]]:
    """
    Select provider based on specified policy.
    Returns: (best_name, scores, policy_info)
    """
    if not providers:
        return None, {}, {}
    
    # Filter out providers with too many consecutive failures
    available_providers = [p for p in providers if p.consecutive_failures < 5]
    if not available_providers:
        available_providers = providers  # Fallback to all providers
    
    if policy == SelectionPolicy.MAX_ACCURACY:
        best = max(available_providers, key=lambda p: p.accuracy)
        scores = {p.name: p.accuracy for p in available_providers}
    elif policy == SelectionPolicy.MIN_COST:
        best = min(available_providers, key=lambda p: p.cost or float('inf'))
        scores = {p.name: p.cost for p in available_providers}
    elif policy == SelectionPolicy.MIN_LATENCY:
        best = min(available_providers, key=lambda p: p.speed)
        scores = {p.name: p.speed for p in available_providers}
    elif policy == SelectionPolicy.WEIGHTED_COMPOSITE:
        # Composite score: accuracy/latency ratio with availability factor
        def composite_score(p):
            if p.speed <= 0:
                return 0
            return (p.accuracy * p.availability) / p.speed
        
        best = max(available_providers, key=composite_score)
        scores = {p.name: composite_score(p) for p in available_providers}
    else:  # ROUND_ROBIN or fallback
        best = random.choice(available_providers)
        scores = {p.name: 1.0 for p in available_providers}
    
    policy_info = {
        "policy": policy.value,
        "available_count": len(available_providers),
        "total_count": len(providers)
    }
    
    return best.name, scores, policy_info


# --- DynamicWeightAlgorithm OSS ---
class DynamicWeightAlgorithm:
    """
    Dynamic Weight Algorithm for LLM Provider Selection
    Integrates with Orchesity IDE OSS orchestration system
    """
    
    def __init__(self, providers=None, selection_policy=SelectionPolicy.MAX_ACCURACY):
        self.provider_metrics: Dict[str, ProviderMetrics] = {}
        self.custom_weighting_strategy: Optional[Callable] = None
        self.selection_policy = selection_policy
        self.round_robin_index = 0
        
        # Initialize with provided providers
        if providers:
            self.initialize_providers(providers)
    
    def initialize_providers(self, providers: List[LLMProvider]):
        """Initialize provider metrics from LLM providers"""
        for provider in providers:
            self.provider_metrics[provider.value] = ProviderMetrics(
                name=provider.value,
                provider_type=provider,
                accuracy=0.8,  # Default starting accuracy
                speed=1.0,     # Default starting speed
                availability=1.0,
                cost=0.01      # Default cost per token
            )
        logger.info(f"Initialized DWA with {len(self.provider_metrics)} providers")

    # --- Metric Sync (simple moving average) ---
    def _sync(self, provider: ProviderMetrics, attr: str, value: float, max_history=10):
        """Sync metric using simple moving average"""
        hist_attr = f"{attr}_history"
        history = getattr(provider, hist_attr)
        history.append(value)
        
        # Keep only recent history
        if len(history) > max_history:
            history.pop(0)
        
        # Update metric with moving average
        avg = sum(history) / len(history)
        setattr(provider, attr, avg)
        
        logger.debug(f"Updated {provider.name} {attr}: {avg:.3f} (from {len(history)} samples)")

    def sync_cost(self, provider_name: str, new_cost: float):
        if provider_name in self.provider_metrics:
            self._sync(self.provider_metrics[provider_name], "cost", new_cost)

    def sync_speed(self, provider_name: str, new_speed: float):
        if provider_name in self.provider_metrics:
            self._sync(self.provider_metrics[provider_name], "speed", new_speed)

    def sync_accuracy(self, provider_name: str, new_acc: float):
        if provider_name in self.provider_metrics:
            self._sync(self.provider_metrics[provider_name], "accuracy", new_acc)

    def sync_availability(self, provider_name: str, new_avail: float):
        if provider_name in self.provider_metrics:
            self._sync(self.provider_metrics[provider_name], "availability", new_avail)

    def record_request_result(self, provider_name: str, success: bool, response_time: float, 
                             error: Optional[str] = None, tokens_used: Optional[int] = None):
        """Record the result of a provider request for metrics tracking"""
        if provider_name not in self.provider_metrics:
            return
            
        provider = self.provider_metrics[provider_name]
        
        # Update speed (response time)
        self.sync_speed(provider_name, response_time)
        
        # Update accuracy based on success
        self.sync_accuracy(provider_name, 1.0 if success else 0.0)
        
        # Update availability
        self.sync_availability(provider_name, 1.0 if success else 0.0)
        
        # Update failure tracking
        if success:
            provider.consecutive_failures = 0
            provider.last_success_time = time.time()
            provider.last_error = None
        else:
            provider.consecutive_failures += 1
            provider.last_error = error
        
        logger.info(f"Recorded result for {provider_name}: success={success}, "
                   f"time={response_time:.3f}s, failures={provider.consecutive_failures}")

    # --- Weighting ---
    def get_weight(self, provider_name: str) -> float:
        """Get weight for a provider"""
        if self.custom_weighting_strategy and provider_name in self.provider_metrics:
            return self.custom_weighting_strategy(self.provider_metrics[provider_name])
        return 1.0  # default equal weight

    def set_custom_weighting_strategy(self, strategy: Callable[[ProviderMetrics], float]):
        """Set a custom weighting strategy function"""
        self.custom_weighting_strategy = strategy
        logger.info("Custom weighting strategy applied")

    def update_weights(self, feedback=None):
        """Placeholder for adaptive logic (enterprise only)"""
        pass

    def get_active_providers(self) -> List[ProviderMetrics]:
        """Get list of active providers"""
        return [p for p in self.provider_metrics.values() if p.availability > 0.1]

    def select_best_provider(self, exclude_providers=None) -> Optional[str]:
        """Select the best provider based on current policy"""
        available_providers = self.get_active_providers()
        
        if exclude_providers:
            available_providers = [
                p for p in available_providers 
                if p.name not in exclude_providers
            ]
        
        if not available_providers:
            return None
            
        best_name, scores, policy_info = choose_provider(
            available_providers, 
            self.selection_policy
        )
        
        logger.info(f"Selected provider: {best_name} using {policy_info.get('policy')} policy")
        return best_name

    # --- OSS Additions ---
    def batch_requests(self, requests: List[Any], batch_size: int = 8) -> Generator[List[Any], None, None]:
        """Yield batches of requests for processing"""
        for i in range(0, len(requests), batch_size):
            yield requests[i : i + batch_size]

    def semantic_cache_lookup(self, cache: Dict[str, Any], input_text: str) -> Optional[Any]:
        """Basic semantic cache with exact match only"""
        return cache.get(input_text)

    def multi_llm_fallback(self, providers: List[str], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try multiple providers in sequence until one succeeds"""
        errors = []
        
        for provider_name in providers:
            if provider_name not in self.provider_metrics:
                continue
                
            try:
                provider_metrics = self.provider_metrics[provider_name]
                
                # Skip providers with too many failures
                if provider_metrics.consecutive_failures >= 5:
                    errors.append((provider_name, "Too many consecutive failures"))
                    continue
                
                # Simulate provider call (in real implementation, call actual provider)
                result = self._simulate_provider_call(provider_name, input_data)
                
                if result and not result.get("error"):
                    # Record success
                    self.record_request_result(provider_name, True, result.get("response_time", 1.0))
                    return result
                else:
                    # Record failure
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    self.record_request_result(provider_name, False, 1.0, error_msg)
                    errors.append((provider_name, error_msg))
                    
            except Exception as e:
                error_msg = str(e)
                self.record_request_result(provider_name, False, 1.0, error_msg)
                errors.append((provider_name, error_msg))
        
        return {
            "error": "All providers failed", 
            "details": errors,
            "attempted_providers": len(providers)
        }

    def _simulate_provider_call(self, provider_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a provider call (replace with actual implementation)"""
        # In real implementation, this would call the actual LLM provider
        return {
            "provider": provider_name,
            "response": f"[{provider_name}] Response to: {input_data.get('prompt', '')[:50]}...",
            "response_time": random.uniform(0.5, 2.0),
            "tokens_used": random.randint(50, 200)
        }

    def handle_errors(self, func: Callable, *args, **kwargs) -> Any:
        """Generic error handler wrapper"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return {"error": str(e)}

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive stats for all providers"""
        stats = {}
        for name, provider in self.provider_metrics.items():
            stats[name] = {
                "accuracy": provider.accuracy,
                "speed": provider.speed,
                "cost": provider.cost,
                "availability": provider.availability,
                "consecutive_failures": provider.consecutive_failures,
                "last_success_time": provider.last_success_time,
                "last_error": provider.last_error,
                "weight": self.get_weight(name)
            }
        return stats

    def reset_provider_metrics(self, provider_name: str):
        """Reset metrics for a specific provider"""
        if provider_name in self.provider_metrics:
            provider = self.provider_metrics[provider_name]
            provider.consecutive_failures = 0
            provider.last_error = None
            provider.accuracy = 0.8
            provider.speed = 1.0
            provider.availability = 1.0
            # Clear history
            provider.cost_history.clear()
            provider.speed_history.clear()
            provider.accuracy_history.clear()
            provider.availability_history.clear()
            logger.info(f"Reset metrics for provider: {provider_name}")


# --- Demo ---
if __name__ == "__main__":
    class DummyProvider:
        def __init__(self, name, acc=0.8):
            self.name = name
            self.accuracy = acc
        def generate(self, x): return f"{self.name} -> {x}"

    # Test with LLMProvider enum
    from ..models import LLMProvider
    
    providers = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GEMINI]
    dwa = DynamicWeightAlgorithm(providers=providers)

    # Test provider selection
    best = dwa.select_best_provider()
    print("Best provider:", best)
    
    # Test stats
    print("Provider stats:", dwa.get_provider_stats())

    # Test multi-LLM fallback
    result = dwa.multi_llm_fallback(
        ["openai", "anthropic"], 
        {"prompt": "Hello OSS"}
    )
    print("Fallback result:", result)