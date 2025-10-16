"""
Performance monitoring and observability for ADK Multi-Agent Code Review MVP.

This module provides comprehensive monitoring capabilities including metrics
collection, health checks, and performance tracking for production systems.
"""

import time
import psutil
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, NamedTuple
from dataclasses import dataclass, field
from functools import wraps
import json

from ..config.loader import get_config
from ..api.constants import (
    HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR,
    SUCCESS_STATUS_CODES, SERVER_ERROR_STATUS_CODES
)

# TODO: Move these types to appropriate modules
from typing import TypedDict

class PerformanceMetrics(TypedDict):
    """Performance metrics structure."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    response_time_ms: float
    timestamp: datetime

class HealthStatus(TypedDict):
    """Health status structure."""
    status: str
    details: Dict[str, Any]
    timestamp: datetime

# Circular buffer for storing recent metrics
MAX_METRIC_HISTORY = 1000


@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimingInfo:
    """Timing information for operations."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe metrics collection system."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_METRIC_HISTORY))
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._active_timers: Dict[str, TimingInfo] = {}
        
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._counters[key] += value
            
            # Store in time series
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=self._counters[key],
                labels=labels or {}
            ))
    
    def record_timing(self, name: str, duration_seconds: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric."""
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._timers[key].append(duration_seconds)
            
            # Maintain only recent timings
            if len(self._timers[key]) > MAX_METRIC_HISTORY:
                self._timers[key] = self._timers[key][-MAX_METRIC_HISTORY:]
            
            # Store in time series
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=duration_seconds,
                labels=labels or {}
            ))
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric (current value)."""
        with self._lock:
            key = self._build_metric_key(name, labels)
            self._metrics[key].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels or {}
            ))
    
    def start_timer(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a timer and return timer ID."""
        timer_id = f"{name}_{int(time.time() * 1000)}"
        with self._lock:
            self._active_timers[timer_id] = TimingInfo(
                operation=name,
                start_time=time.time(),
                metadata=metadata or {}
            )
        return timer_id
    
    def stop_timer(self, timer_id: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Stop a timer and record the duration."""
        with self._lock:
            if timer_id not in self._active_timers:
                return None
            
            timer_info = self._active_timers.pop(timer_id)
            timer_info.end_time = time.time()
            timer_info.duration = timer_info.end_time - timer_info.start_time
            
            self.record_timing(timer_info.operation, timer_info.duration, labels)
            return timer_info.duration
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        with self._lock:
            key = self._build_metric_key(name, labels)
            return self._counters.get(key, 0)
    
    def get_timing_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get timing statistics for a metric."""
        with self._lock:
            key = self._build_metric_key(name, labels)
            timings = self._timers.get(key, [])
            
            if not timings:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0, "p99": 0.0}
            
            sorted_timings = sorted(timings)
            count = len(sorted_timings)
            
            return {
                "count": count,
                "avg": sum(sorted_timings) / count,
                "min": sorted_timings[0],
                "max": sorted_timings[-1],
                "p95": sorted_timings[int(count * 0.95)] if count > 0 else 0.0,
                "p99": sorted_timings[int(count * 0.99)] if count > 0 else 0.0
            }
    
    def get_recent_metrics(self, name: str, since: Optional[datetime] = None) -> List[MetricPoint]:
        """Get recent metrics for a given name."""
        if since is None:
            since = datetime.utcnow() - timedelta(minutes=5)
        
        with self._lock:
            metrics = []
            for key, points in self._metrics.items():
                if name in key:
                    for point in points:
                        if point.timestamp >= since:
                            metrics.append(point)
            return sorted(metrics, key=lambda p: p.timestamp)
    
    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Build a unique key for a metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def clear_old_metrics(self, older_than: timedelta) -> None:
        """Clear metrics older than specified time."""
        cutoff = datetime.utcnow() - older_than
        with self._lock:
            for key, points in self._metrics.items():
                # Filter out old points
                recent_points = deque(
                    (point for point in points if point.timestamp >= cutoff),
                    maxlen=MAX_METRIC_HISTORY
                )
                self._metrics[key] = recent_points


class PerformanceMonitor:
    """Main performance monitoring system."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self._start_time = datetime.utcnow()
        self._dependencies: Dict[str, Callable[[], bool]] = {}
        
        # Start background monitoring
        self._monitor_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self._monitor_thread.start()
    
    def add_dependency_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """Add a dependency health check."""
        self._dependencies[name] = check_func
    
    def track_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None
    ) -> None:
        """Track API request metrics."""
        labels = {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        }
        
        # Track request count
        self.metrics.increment_counter("http_requests_total", labels=labels)
        
        # Track request duration
        self.metrics.record_timing("http_request_duration_seconds", duration_seconds, labels=labels)
        
        # Track request/response sizes
        if request_size_bytes is not None:
            self.metrics.record_gauge("http_request_size_bytes", request_size_bytes, labels=labels)
        if response_size_bytes is not None:
            self.metrics.record_gauge("http_response_size_bytes", response_size_bytes, labels=labels)
        
        # Track error rates
        if status_code >= 400:
            error_labels = {"method": method, "path": path}
            self.metrics.increment_counter("http_errors_total", labels=error_labels)
    
    def track_agent_execution(
        self,
        agent_type: str,
        status: str,
        duration_seconds: float,
        memory_mb: Optional[float] = None
    ) -> None:
        """Track agent execution metrics."""
        labels = {"agent_type": agent_type, "status": status}
        
        # Track execution count
        self.metrics.increment_counter("agent_executions_total", labels=labels)
        
        # Track execution duration
        self.metrics.record_timing("agent_execution_duration_seconds", duration_seconds, labels=labels)
        
        # Track memory usage if provided
        if memory_mb is not None:
            self.metrics.record_gauge("agent_memory_usage_mb", memory_mb, labels=labels)
    
    def track_llm_request(
        self,
        model: str,
        status: str,
        duration_seconds: float,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None
    ) -> None:
        """Track LLM request metrics."""
        labels = {"model": model, "status": status}
        
        # Track request count
        self.metrics.increment_counter("llm_requests_total", labels=labels)
        
        # Track request duration
        self.metrics.record_timing("llm_request_duration_seconds", duration_seconds, labels=labels)
        
        # Track token usage
        if input_tokens is not None:
            self.metrics.record_gauge("llm_input_tokens", input_tokens, labels=labels)
        if output_tokens is not None:
            self.metrics.record_gauge("llm_output_tokens", output_tokens, labels=labels)
        
        # Track costs
        if cost_usd is not None:
            self.metrics.record_gauge("llm_cost_usd", cost_usd, labels=labels)
    
    def track_session(self, action: str, session_count: Optional[int] = None) -> None:
        """Track session management metrics."""
        labels = {"action": action}
        
        # Track session actions
        self.metrics.increment_counter("session_actions_total", labels=labels)
        
        # Track active session count
        if session_count is not None:
            self.metrics.record_gauge("active_sessions_count", session_count)
    
    @contextmanager
    def time_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        timer_id = self.metrics.start_timer(operation_name)
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = self.metrics.stop_timer(timer_id, labels)
            if duration is not None:
                # Also track operation count
                self.metrics.increment_counter(f"{operation_name}_count", labels=labels)
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        # Request metrics
        request_stats = self.metrics.get_timing_stats("http_request_duration_seconds")
        error_count = self.metrics.get_counter("http_errors_total")
        request_count = self.metrics.get_counter("http_requests_total")
        
        # System metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Session metrics
        active_sessions = self.metrics.get_counter("active_sessions_count")
        
        return {
            "request_count": request_count,
            "error_count": error_count,
            "average_response_time_ms": request_stats["avg"] * 1000,
            "p95_response_time_ms": request_stats["p95"] * 1000,
            "p99_response_time_ms": request_stats["p99"] * 1000,
            "memory_usage_mb": memory_info.used / (1024 * 1024),
            "cpu_usage_percent": cpu_percent,
            "active_sessions": active_sessions
        }
    
    def get_health_status(self) -> HealthStatus:
        """Get application health status."""
        config = get_config()
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        # Check dependencies
        dependency_status = {}
        overall_healthy = True
        
        for name, check_func in self._dependencies.items():
            try:
                dependency_status[name] = check_func()
                if not dependency_status[name]:
                    overall_healthy = False
            except Exception:
                dependency_status[name] = False
                overall_healthy = False
        
        # Check performance thresholds
        metrics = self.get_performance_metrics()
        performance_healthy = (
            metrics["average_response_time_ms"] < config.monitoring.response_time_threshold_ms and
            metrics["memory_usage_mb"] < (psutil.virtual_memory().total / (1024 * 1024)) * (config.monitoring.memory_usage_threshold_percent / 100)
        )
        
        status = "healthy" if (overall_healthy and performance_healthy) else "unhealthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow(),
            "version": config.app_version,
            "uptime_seconds": uptime,
            "dependencies": dependency_status,
            "metrics": metrics
        }
    
    def _background_monitoring(self) -> None:
        """Background thread for system monitoring."""
        while True:
            try:
                # Record system metrics
                memory_info = psutil.virtual_memory()
                self.metrics.record_gauge("system_memory_usage_mb", memory_info.used / (1024 * 1024))
                self.metrics.record_gauge("system_memory_percent", memory_info.percent)
                
                cpu_percent = psutil.cpu_percent(interval=1.0)
                self.metrics.record_gauge("system_cpu_percent", cpu_percent)
                
                # Clean up old metrics
                self.metrics.clear_old_metrics(timedelta(hours=1))
                
                # Sleep for next collection
                time.sleep(30)
                
            except Exception as e:
                # Log error but continue monitoring
                print(f"Background monitoring error: {e}")
                time.sleep(30)


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def track_performance(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator for tracking function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            with monitor.time_operation(operation_name, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_async_performance(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator for tracking async function performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_monitor()
            with monitor.time_operation(operation_name, labels):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Export public interface
__all__ = [
    "MetricPoint",
    "TimingInfo",
    "MetricsCollector",
    "PerformanceMonitor",
    "get_monitor",
    "track_performance",
    "track_async_performance",
]
