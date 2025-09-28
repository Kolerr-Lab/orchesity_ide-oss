"""
DWA Custom Weighting Strategies Examples
======================================
Examples of custom weighting strategies for the Dynamic Weight Algorithm
"""

from src.services.DWA import ProviderMetrics


def cost_optimized_strategy(provider: ProviderMetrics) -> float:
    """
    Weighting strategy that prioritizes low cost providers
    """
    if provider.cost <= 0:
        return 0.1  # Avoid division by zero

    # Higher weight for lower cost, adjusted by availability
    base_weight = 1.0 / provider.cost
    availability_factor = provider.availability
    accuracy_factor = provider.accuracy

    return base_weight * availability_factor * accuracy_factor


def speed_focused_strategy(provider: ProviderMetrics) -> float:
    """
    Weighting strategy that prioritizes fast response times
    """
    if provider.speed <= 0:
        return 0.1

    # Higher weight for faster providers (lower response time)
    speed_weight = 1.0 / provider.speed
    accuracy_weight = provider.accuracy**2  # Square accuracy for emphasis
    availability_weight = provider.availability

    return speed_weight * accuracy_weight * availability_weight


def balanced_strategy(provider: ProviderMetrics) -> float:
    """
    Balanced weighting strategy considering all factors
    """
    # Normalize factors (assuming reasonable ranges)
    cost_score = (
        max(0.1, 2.0 - provider.cost) if provider.cost > 0 else 1.0
    )  # Lower cost = higher score
    speed_score = (
        max(0.1, 3.0 - provider.speed) if provider.speed > 0 else 1.0
    )  # Lower time = higher score
    accuracy_score = provider.accuracy  # 0-1 range
    availability_score = provider.availability  # 0-1 range

    # Weighted combination
    composite_score = (
        0.2 * cost_score  # 20% cost consideration
        + 0.3 * speed_score  # 30% speed consideration
        + 0.4 * accuracy_score  # 40% accuracy consideration
        + 0.1 * availability_score  # 10% availability consideration
    )

    return composite_score


def reliability_first_strategy(provider: ProviderMetrics) -> float:
    """
    Strategy that heavily penalizes providers with failures
    """
    base_weight = provider.accuracy * provider.availability

    # Heavy penalty for consecutive failures
    failure_penalty = max(0.1, 1.0 - (provider.consecutive_failures * 0.2))

    # Recent success bonus
    import time

    if provider.last_success_time:
        time_since_success = time.time() - provider.last_success_time
        recency_bonus = max(0.5, 2.0 - (time_since_success / 3600))  # Decay over 1 hour
    else:
        recency_bonus = 0.5

    return base_weight * failure_penalty * recency_bonus


def adaptive_learning_strategy(provider: ProviderMetrics) -> float:
    """
    Strategy that adapts based on historical performance variance
    """
    # Calculate variance in performance metrics
    if len(provider.accuracy_history) > 1:
        accuracy_variance = sum(
            [(x - provider.accuracy) ** 2 for x in provider.accuracy_history]
        ) / len(provider.accuracy_history)
        consistency_score = max(
            0.1, 1.0 - accuracy_variance
        )  # Lower variance = higher consistency
    else:
        consistency_score = 0.5

    if len(provider.speed_history) > 1:
        speed_variance = sum(
            [(x - provider.speed) ** 2 for x in provider.speed_history]
        ) / len(provider.speed_history)
        speed_consistency = max(0.1, 1.0 - (speed_variance / provider.speed))
    else:
        speed_consistency = 0.5

    # Combine consistency with performance
    performance_score = provider.accuracy * provider.availability
    consistency_factor = (consistency_score + speed_consistency) / 2

    return performance_score * consistency_factor


# Example usage:
"""
# In your application startup or configuration:

from src.services.llm_orchestrator import orchestrator
from dwa_strategies import cost_optimized_strategy, speed_focused_strategy, balanced_strategy

# Apply a cost-optimized strategy
orchestrator.set_custom_dwa_weighting(cost_optimized_strategy)

# Or apply based on configuration
strategy_map = {
    "cost_optimized": cost_optimized_strategy,
    "speed_focused": speed_focused_strategy, 
    "balanced": balanced_strategy,
    "reliability_first": reliability_first_strategy,
    "adaptive_learning": adaptive_learning_strategy
}

# Get strategy from config or environment
selected_strategy = strategy_map.get("balanced")  # default to balanced
orchestrator.set_custom_dwa_weighting(selected_strategy)
"""
