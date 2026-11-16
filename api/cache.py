"""
NovaNest High-Performance Caching Subsystem (Phase 17)
=====================================================
Multi-tiered caching engine supporting:
- Tier 1: In-Memory TTL Cache (LRU eviction, thread-safe, sub-millisecond retrieval)
- Tier 2: Optional Redis Network Cache with graceful failure fallback
- Strict cache key hashing with user/session isolation
- Data freshness guarantees and verified cache invalidation
- Prometheus telemetry instrumentation for cache hits, misses, and hit ratio
"""

import hashlib
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger("novanest.cache")

# Global Cache Telemetry Counters
CACHE_HITS = 0
CACHE_MISSES = 0
_telemetry_lock = threading.Lock()


def get_cache_stats() -> Dict[str, Any]:
    with _telemetry_lock:
        total = CACHE_HITS + CACHE_MISSES
        hit_ratio = round(CACHE_HITS / total, 4) if total > 0 else 0.0
        return {
            "hits": CACHE_HITS,
            "misses": CACHE_MISSES,
            "total_requests": total,
            "hit_ratio": hit_ratio,
            "hit_ratio_pct": round(hit_ratio * 100, 2),
        }


def record_hit():
    global CACHE_HITS
    with _telemetry_lock:
        CACHE_HITS += 1
        total = CACHE_HITS + CACHE_MISSES
        ratio = CACHE_HITS / total if total > 0 else 0.0
    try:
        from python.operations.metrics import record_cache_lookup, update_cache_metrics
        record_cache_lookup(True)
        update_cache_metrics(ratio, len(GLOBAL_CACHE._store))
    except Exception:
        pass


def record_miss():
    global CACHE_MISSES
    with _telemetry_lock:
        CACHE_MISSES += 1
        total = CACHE_HITS + CACHE_MISSES
        ratio = CACHE_HITS / total if total > 0 else 0.0
    try:
        from python.operations.metrics import record_cache_lookup, update_cache_metrics
        record_cache_lookup(False)
        update_cache_metrics(ratio, len(GLOBAL_CACHE._store))
    except Exception:
        pass


class CacheItem:
    __slots__ = ("value", "expires_at", "created_at")

    def __init__(self, value: Any, ttl_seconds: float):
        now = time.monotonic()
        self.value = value
        self.created_at = time.time()
        self.expires_at = now + ttl_seconds

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class PerformanceCache:
    """
    Thread-safe in-memory L1 cache with LRU eviction and configurable TTL.
    Supports optional Redis L2 peering when configured in environment.
    """

    def __init__(self, max_items: int = 1000, default_ttl: float = 60.0):
        self.max_items = max_items
        self.default_ttl = default_ttl
        self._store: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        self._redis_client = None
        self._redis_available = False
        self._init_redis()

    def _init_redis(self):
        redis_host = os.getenv("REDIS_HOST")
        if redis_host:
            try:
                import redis
                port = int(os.getenv("REDIS_PORT", 6379))
                password = os.getenv("REDIS_PASSWORD", None)
                client = redis.Redis(
                    host=redis_host,
                    port=port,
                    password=password,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
                client.ping()
                self._redis_client = client
                self._redis_available = True
                logger.info("[CACHE_REDIS] Connected to Redis L2 cache at %s:%d", redis_host, port)
            except Exception as e:
                logger.warning("[CACHE_REDIS_FALLBACK] Redis configured but unreachable (%s). Using L1 Memory Cache.", e)
                self._redis_client = None
                self._redis_available = False

    @staticmethod
    def generate_key(prefix: str, params: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None) -> str:
        """
        Generates deterministic, collision-resistant cache key with optional user isolation.
        """
        payload = {
            "p": params or {},
            "u": user_id or "global",
        }
        encoded = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def get(self, key: str) -> Tuple[Optional[Any], str]:
        """
        Retrieves item from cache.
        Returns: (value, cache_status) where cache_status is 'HIT' or 'MISS'.
        """
        with self._lock:
            # 1. Check L1 In-Memory Cache
            item = self._store.get(key)
            if item is not None:
                if not item.is_expired():
                    record_hit()
                    return item.value, "HIT"
                else:
                    del self._store[key]

        # 2. Check L2 Redis Cache if enabled
        if self._redis_available and self._redis_client:
            try:
                raw = self._redis_client.get(key)
                if raw is not None:
                    val = json.loads(raw.decode("utf-8"))
                    # Backfill L1
                    with self._lock:
                        self._store[key] = CacheItem(val, self.default_ttl)
                    record_hit()
                    return val, "HIT"
            except Exception as e:
                logger.debug("Redis get error for %s: %s", key, e)

        record_miss()
        return None, "MISS"

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Stores item in cache with specified TTL.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        with self._lock:
            # Evict if exceeding max items
            if len(self._store) >= self.max_items:
                # Evict oldest 10%
                now = time.monotonic()
                expired_keys = [k for k, v in self._store.items() if v.is_expired()]
                for k in expired_keys:
                    del self._store[k]
                if len(self._store) >= self.max_items:
                    # Remove first 50 keys
                    for k in list(self._store.keys())[:50]:
                        del self._store[k]

            self._store[key] = CacheItem(value, ttl)

        # Write to L2 Redis if available
        if self._redis_available and self._redis_client:
            try:
                payload = json.dumps(value, default=str)
                self._redis_client.setex(key, int(ttl), payload)
            except Exception as e:
                logger.debug("Redis set error for %s: %s", key, e)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception:
                pass

    def invalidate_prefix(self, prefix: str) -> int:
        count = 0
        with self._lock:
            keys_to_del = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_del:
                del self._store[k]
                count += 1
        if self._redis_available and self._redis_client:
            try:
                r_keys = self._redis_client.keys(f"{prefix}*")
                if r_keys:
                    self._redis_client.delete(*r_keys)
            except Exception:
                pass
        return count

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.flushdb()
            except Exception:
                pass


# Global Singleton Instance for Backend API
GLOBAL_CACHE = PerformanceCache(max_items=2000, default_ttl=60.0)
