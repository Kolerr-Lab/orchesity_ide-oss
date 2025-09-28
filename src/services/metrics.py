"""
Metrics service for Orchesity IDE OSS
Provides performance monitoring and analytics for LLM operations
"""

from typing import Dict, Any, List, Optional
import time
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
import asyncio

from ..core.config import Settings


logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point"""

    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series data for a metric"""

    name: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    aggregations: Dict[str, float] = field(default_factory=dict)

    def add_point(self, value: float, tags: Optional[Dict[str, str]] = None):
        """Add a data point to the series"""
        point = MetricPoint(timestamp=time.time(), value=value, tags=tags or {})
        self.points.append(point)
        self._update_aggregations()

    def _update_aggregations(self):
        """Update rolling aggregations"""
        if not self.points:
            return

        values = [p.value for p in self.points]
        self.aggregations.update(
            {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1],
            }
        )


class MetricsService:
    """Service for collecting and analyzing performance metrics"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._metrics: Dict[str, MetricSeries] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._is_initialized = False

        # Performance tracking
        self._start_time = time.time()
        self._operation_counts = defaultdict(int)
        self._error_counts = defaultdict(int)

    async def initialize(self) -> None:
        """Initialize metrics service"""
        if self._is_initialized:
            return

        # Initialize core metrics
        self._init_core_metrics()

        self._is_initialized = True
        logger.info("Metrics service initialized")

    async def shutdown(self) -> None:
        """Shutdown metrics service"""
        self._is_initialized = False
        logger.info("Metrics service shutdown")

    def _init_core_metrics(self):
        """Initialize core system metrics"""
        # Request metrics
        self.create_metric("requests_total", "counter")
        self.create_metric("requests_duration", "histogram")
        self.create_metric("requests_errors", "counter")

        # Provider metrics
        self.create_metric("provider_requests", "counter")
        self.create_metric("provider_errors", "counter")
        self.create_metric("provider_latency", "histogram")

        # Cache metrics
        self.create_metric("cache_hits", "counter")
        self.create_metric("cache_misses", "counter")
        self.create_metric("cache_sets", "counter")

        # System metrics
        self.create_metric("memory_usage", "gauge")
        self.create_metric("cpu_usage", "gauge")

    def create_metric(self, name: str, metric_type: str):
        """Create a new metric"""
        if metric_type == "histogram":
            self._histograms[name] = []
        elif metric_type == "counter":
            self._counters[name] = 0
        elif metric_type == "gauge":
            self._gauges[name] = 0.0
        elif metric_type == "timeseries":
            self._metrics[name] = MetricSeries(name)

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        if name in self._counters:
            self._counters[name] += value
        else:
            self._counters[name] = value

        # Also track in time series if it exists
        if name in self._metrics:
            self._metrics[name].add_point(float(value), tags)

    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        self._gauges[name] = value

        # Also track in time series if it exists
        if name in self._metrics:
            self._metrics[name].add_point(value)

    def record_histogram(self, name: str, value: float):
        """Record a histogram value"""
        if name in self._histograms:
            self._histograms[name].append(value)
            # Keep only last 1000 values
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]

        # Also track in time series if it exists
        if name in self._metrics:
            self._metrics[name].add_point(value)

    def record_request(
        self,
        provider: str,
        model: str,
        duration: float,
        success: bool = True,
        tokens_used: Optional[int] = None,
    ):
        """Record an LLM request"""
        self.increment_counter("requests_total")

        if not success:
            self.increment_counter("requests_errors")

        self.record_histogram("requests_duration", duration)

        # Provider-specific metrics
        tags = {"provider": provider, "model": model}
        self.increment_counter("provider_requests", tags=tags)

        if not success:
            self.increment_counter("provider_errors", tags=tags)

        self.record_histogram("provider_latency", duration)

        if tokens_used:
            self.record_histogram("tokens_used", tokens_used)

    def record_cache_operation(self, operation: str, hit: bool = False):
        """Record a cache operation"""
        if operation == "get":
            if hit:
                self.increment_counter("cache_hits")
            else:
                self.increment_counter("cache_misses")
        elif operation == "set":
            self.increment_counter("cache_sets")

    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a metric"""
        if name in self._metrics:
            series = self._metrics[name]
            return {
                "name": name,
                "count": len(series.points),
                "aggregations": series.aggregations.copy(),
                "latest_timestamp": (
                    series.points[-1].timestamp if series.points else None
                ),
            }
        elif name in self._counters:
            return {"name": name, "type": "counter", "value": self._counters[name]}
        elif name in self._gauges:
            return {"name": name, "type": "gauge", "value": self._gauges[name]}
        elif name in self._histograms:
            values = self._histograms[name]
            if not values:
                return {"name": name, "type": "histogram", "count": 0}

            return {
                "name": name,
                "type": "histogram",
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": sorted(values)[len(values) // 2],
                "p95": sorted(values)[int(len(values) * 0.95)],
                "p99": sorted(values)[int(len(values) * 0.99)],
            }

        return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics data"""
        result = {
            "uptime": time.time() - self._start_time,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {},
            "timeseries": {},
        }

        # Summarize histograms
        for name, values in self._histograms.items():
            if values:
                result["histograms"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }

        # Summarize time series
        for name, series in self._metrics.items():
            result["timeseries"][name] = {
                "count": len(series.points),
                "aggregations": series.aggregations.copy(),
            }

        return result

    def reset_metric(self, name: str):
        """Reset a metric to its initial state"""
        if name in self._counters:
            self._counters[name] = 0
        elif name in self._gauges:
            self._gauges[name] = 0.0
        elif name in self._histograms:
            self._histograms[name].clear()
        elif name in self._metrics:
            self._metrics[name].points.clear()
            self._metrics[name].aggregations.clear()

    async def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            import psutil

            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage", memory.percent)

            # CPU usage (over 1 second interval)
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("cpu_usage", cpu_percent)

        except ImportError:
            # psutil not available, skip system metrics
            pass
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if metrics service is initialized"""
        return self._is_initialized
