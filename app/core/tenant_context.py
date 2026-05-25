import contextvars
from uuid import UUID

tenant_id_var: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "tenant_id",
    default=None,
)


def get_current_tenant_id() -> UUID | None:
    return tenant_id_var.get()


def set_tenant_id(tenant_id: UUID) -> None:
    tenant_id_var.set(tenant_id)


def clear_tenant_id() -> None:
    tenant_id_var.set(None)
