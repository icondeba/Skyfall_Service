import logging
import time
from collections.abc import Awaitable, Callable
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_access_token
from app.core.tenant_context import clear_tenant_id, get_current_tenant_id, set_tenant_id

logger = logging.getLogger("skyfall.tenant")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started_at = time.perf_counter()
        authorization = request.headers.get("Authorization", "")

        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            try:
                claims = decode_access_token(token, verify=False)
                tenant_value = claims.get("tenant_id")
                if tenant_value:
                    set_tenant_id(UUID(str(tenant_value)))
            except Exception:
                clear_tenant_id()

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request completed",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "tenant_id": str(get_current_tenant_id()) if get_current_tenant_id() else None,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                }
            },
        )
        clear_tenant_id()
        return response
