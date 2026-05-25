from typing import Any


class RedisCache:
    def get(self, key: str) -> Any | None:
        # TODO: wire Upstash Redis.
        return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        return None

    def delete(self, key: str) -> None:
        return None


redis_cache = RedisCache()
