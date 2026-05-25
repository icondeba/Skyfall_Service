import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable, max_requests: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self.requests[client]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "rate_limit_exceeded",
                    "message": "Too many requests",
                    "details": None,
                },
            )
        bucket.append(now)
        return await call_next(request)
