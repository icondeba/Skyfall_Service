from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse


class DomainError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "domain_error"

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(message)


class TenantNotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "tenant_not_found"


class OrderNotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "order_not_found"


class TableOccupiedError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "table_occupied"


class MenuItemUnavailableError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "menu_item_unavailable"


class PaymentAlreadyCompletedError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "payment_already_completed"


class InsufficientPaymentError(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "insufficient_payment"


class UnauthorizedTenantAccessError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "unauthorized_tenant_access"


class PlanLimitExceededError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "plan_limit_exceeded"


async def domain_exception_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details={"path": str(request.url.path)},
        ).model_dump(),
    )
