from fastapi import APIRouter

from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/plans")
async def list_plans() -> dict[str, list[dict[str, str]]]:
    return {
        "plans": [
            {"name": "starter", "label": "Starter"},
            {"name": "pro", "label": "Pro"},
            {"name": "enterprise", "label": "Enterprise"},
        ]
    }


@router.get("/status", response_model=SuccessResponse)
async def platform_status() -> SuccessResponse:
    return SuccessResponse(message="Platform services are reachable")
