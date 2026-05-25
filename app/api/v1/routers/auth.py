from fastapi import APIRouter

from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    token = create_access_token(
        subject=payload.subject,
        tenant_id=str(payload.tenant_id),
        role=payload.role,
    )
    return TokenResponse(access_token=token)
