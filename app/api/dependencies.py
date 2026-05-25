from dataclasses import dataclass
from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.tenant_context import get_current_tenant_id
from app.services.tenant_service import tenant_service

bearer_scheme = HTTPBearer(auto_error=False)
DEV_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class CurrentUser:
    id: UUID | None
    tenant_id: UUID
    role: str
    token: str | None = None


def _claims_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        if settings.AUTH_DISABLED:
            return {"sub": None, "tenant_id": str(DEV_TENANT_ID), "role": "admin"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_access_token(credentials.credentials, verify=not settings.AUTH_DISABLED)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_tenant(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UUID:
    context_tenant = get_current_tenant_id()
    if context_tenant is not None:
        return context_tenant
    claims = _claims_from_credentials(credentials)
    tenant_id = claims.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tenant_id missing from token")
    return UUID(str(tenant_id))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    tenant_id: UUID = Depends(get_tenant),
) -> CurrentUser:
    claims = _claims_from_credentials(credentials)
    subject = claims.get("sub")
    return CurrentUser(
        id=UUID(str(subject)) if subject else None,
        tenant_id=tenant_id,
        role=str(claims.get("role", "staff")),
        token=credentials.credentials if credentials else None,
    )


def get_current_staff(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in {"admin", "waiter", "kitchen", "owner"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff privileges required")
    return current_user


def get_current_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in {"admin", "owner"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def check_plan(required_plan: str) -> Callable:
    async def dependency(
        db=Depends(get_db),
        tenant_id: UUID = Depends(get_tenant),
    ) -> None:
        if settings.AUTH_DISABLED:
            return None
        await tenant_service.check_plan(db, tenant_id, required_plan)
        return None

    return dependency
