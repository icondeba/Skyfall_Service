import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CafeTable
from app.repositories.base_repository import BaseRepository


class TableRepository(BaseRepository[CafeTable]):
    def __init__(self) -> None:
        super().__init__(CafeTable)

    def get_ordered(self, db: Session, tenant_id: UUID) -> list[CafeTable]:
        statement = select(CafeTable).order_by(CafeTable.table_number.asc())
        if hasattr(CafeTable, "tenant_id"):
            statement = statement.where(CafeTable.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def update_status(self, db: Session, tenant_id: UUID, table_id: UUID, status: str) -> CafeTable | None:
        table = self.get_by_id(db, tenant_id, table_id)
        if table is None:
            return None
        table.status = status
        db.flush()
        return table

    def get_by_number(self, db: Session, tenant_id: UUID, table_number: int) -> CafeTable | None:
        statement = select(CafeTable).where(CafeTable.table_number == table_number)
        if hasattr(CafeTable, "tenant_id"):
            statement = statement.where(CafeTable.tenant_id == tenant_id)
        return db.scalar(statement)

    def resolve_table_reference(
        self,
        db: Session,
        tenant_id: UUID,
        table_reference: UUID | int | str,
    ) -> CafeTable | None:
        if isinstance(table_reference, UUID):
            return self.get_by_id(db, tenant_id, table_reference)
        if isinstance(table_reference, int):
            return self.get_by_number(db, tenant_id, table_reference)

        value = str(table_reference).strip()
        if not value:
            return None
        try:
            return self.get_by_id(db, tenant_id, uuid.UUID(value))
        except ValueError:
            if value.isdigit():
                return self.get_by_number(db, tenant_id, int(value))
            return None


table_repository = TableRepository()
