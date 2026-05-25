from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CHAR, Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


class PortableUUID(TypeDecorator[uuid.UUID]):
    """Store UUIDs natively in PostgreSQL and as 32-char hex strings elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: Any) -> str | uuid.UUID | None:
        if value is None:
            return None
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return parsed
        return parsed.hex

    def process_result_value(self, value: uuid.UUID | str | None, dialect: Any) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class TenantMixin:
    """Add this mixin to every model that needs tenant isolation."""

    tenant_id = Column(PortableUUID(), nullable=False, index=True)


class TimestampMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
