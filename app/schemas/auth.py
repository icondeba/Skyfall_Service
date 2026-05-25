from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    subject: str = Field(default="dev-user")
    tenant_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    role: str = "admin"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
