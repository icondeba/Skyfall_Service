from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedTenantAccessError
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def _has_tenant_id(self) -> bool:
        return hasattr(self.model, "tenant_id")

    def _tenant_matches(self, obj: ModelType, tenant_id: UUID) -> bool:
        if not hasattr(obj, "tenant_id"):
            return True
        return getattr(obj, "tenant_id") == tenant_id

    def _assert_tenant_access(self, obj: ModelType | None, tenant_id: UUID) -> None:
        if obj is not None and not self._tenant_matches(obj, tenant_id):
            raise UnauthorizedTenantAccessError("Record belongs to another tenant")

    def _tenant_filtered_statement(self, tenant_id: UUID) -> Any:
        statement = select(self.model)
        if self._has_tenant_id():
            statement = statement.where(getattr(self.model, "tenant_id") == tenant_id)
        return statement

    def get_by_id(self, db: Session, tenant_id: UUID, record_id: UUID) -> ModelType | None:
        obj = db.get(self.model, record_id)
        self._assert_tenant_access(obj, tenant_id)
        return obj

    def get_all(
        self,
        db: Session,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        statement = self._tenant_filtered_statement(tenant_id).offset(skip).limit(limit)
        return list(db.scalars(statement))

    def get_filtered(self, db: Session, tenant_id: UUID, **filters: Any) -> list[ModelType]:
        statement = self._tenant_filtered_statement(tenant_id)
        for field, value in filters.items():
            statement = statement.where(getattr(self.model, field) == value)
        return list(db.scalars(statement))

    def create(self, db: Session, tenant_id: UUID, obj_in: dict[str, Any]) -> ModelType:
        data = dict(obj_in)
        if self._has_tenant_id() and "tenant_id" not in data:
            data["tenant_id"] = tenant_id
        obj = self.model(**data)
        db.add(obj)
        db.flush()
        self._assert_tenant_access(obj, tenant_id)
        return obj

    def update(
        self,
        db: Session,
        tenant_id: UUID,
        record_id: UUID,
        obj_in: dict[str, Any],
    ) -> ModelType | None:
        obj = self.get_by_id(db, tenant_id, record_id)
        if obj is None:
            return None
        for field, value in obj_in.items():
            setattr(obj, field, value)
        db.flush()
        self._assert_tenant_access(obj, tenant_id)
        return obj

    def soft_delete(self, db: Session, tenant_id: UUID, record_id: UUID) -> bool:
        obj = self.get_by_id(db, tenant_id, record_id)
        if obj is None:
            return False
        if hasattr(obj, "is_active"):
            setattr(obj, "is_active", False)
        else:
            db.delete(obj)
        db.flush()
        return True

    def count(self, db: Session, tenant_id: UUID, **filters: Any) -> int:
        statement = select(func.count(self.model.id))
        if self._has_tenant_id():
            statement = statement.where(getattr(self.model, "tenant_id") == tenant_id)
        for field, value in filters.items():
            statement = statement.where(getattr(self.model, field) == value)
        return int(db.scalar(statement) or 0)

    def exists(self, db: Session, tenant_id: UUID, **filters: Any) -> bool:
        return self.count(db, tenant_id, **filters) > 0
