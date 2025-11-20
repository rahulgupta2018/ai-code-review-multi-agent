"""
Rate Limiter for Gemini API calls

Implements token bucket algorithm to prevent overwhelming the API.
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 10  # Conservative: 10 RPM for free tier
    burst_size: int = 3  # Allow small bursts of 3 requests
    cooldown_on_error: float = 30.0  # Wait 30s after 429/503


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.tokens = float(self.config.burst_size)
        self.last_update = time.time()
        self.cooldown_until: Optional[float] = None
        self._lock = asyncio.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = self.config.requests_per_minute / 60.0
        
    async def acquire(self, timeout: float = 60.0) -> bool:
        """
        Acquire permission to make an API call.
        
        Args:
            timeout: Maximum time to wait for permission (seconds)
            
        Returns:
            True if permission granted, False if timeout
        """
        start_time = time.time()
        
        while True:
            async with self._lock:
                now = time.time()
                
                # Check if in cooldown period
                if self.cooldown_until and now < self.cooldown_until:
                    wait_time = self.cooldown_until - now
                    if (now - start_time) + wait_time > timeout:
                        return False
                    await asyncio.sleep(min(wait_time, 1.0))
                    continue
                
                # Refill tokens based on time elapsed
                elapsed = now - self.last_update
                self.tokens = min(
                    self.config.burst_size,
                    self.tokens + (elapsed * self.refill_rate)
                )
                self.last_update = now
                
                # Check if we have a token available
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
                
                # Calculate wait time for next token
                wait_time = (1.0 - self.tokens) / self.refill_rate
                
                # Check if we'll timeout
                if (now - start_time) + wait_time > timeout:
                    return False
            
            # Wait outside the lock
            await asyncio.sleep(min(wait_time, 1.0))
    
    def on_error(self, status_code: int):
        """
        Handle API error by entering cooldown if needed.
        
        Args:
            status_code: HTTP status code (429=rate limit, 503=unavailable)
        """
        if status_code in (429, 503):
            self.cooldown_until = time.time() + self.config.cooldown_on_error
            print(f"⏸️  Rate limiter: Entering {self.config.cooldown_on_error}s cooldown after {status_code} error")
    
    def reset_cooldown(self):
        """Clear cooldown period (for testing)"""
        self.cooldown_until = None
    
    @property
    def is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period"""
        return self.cooldown_until is not None and time.time() < self.cooldown_until


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def configure_rate_limiter(config: RateLimitConfig):
    """Configure the global rate limiter"""
    global _rate_limiter
    _rate_limiter = RateLimiter(config)


def reset_rate_limiter():
    """Reset rate limiter (for testing)"""
    global _rate_limiter
    _rate_limiter = None
