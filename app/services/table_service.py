from uuid import UUID
from typing import Any

from app.core.exceptions import DomainError
from app.models import CafeTable
from app.repositories.order_repository import order_repository
from app.repositories.table_repository import table_repository


class TableService:
    async def create_table(self, db: Any, tenant_id: UUID, table_number: int, capacity: int) -> CafeTable:
        existing = table_repository.get_by_number(db, tenant_id, table_number)
        if existing:
            raise DomainError(f"Table {table_number} already exists", status_code=409, error_code="table_number_conflict")
        table = table_repository.create(db, tenant_id, {"table_number": table_number, "capacity": capacity})
        db.commit()
        db.refresh(table)
        return table

    async def update_table(self, db: Any, tenant_id: UUID, table_id: UUID, fields: dict) -> CafeTable:
        if "table_number" in fields and fields["table_number"] is not None:
            existing = table_repository.get_by_number(db, tenant_id, fields["table_number"])
            if existing and existing.id != table_id:
                raise DomainError(f"Table {fields['table_number']} already exists", status_code=409, error_code="table_number_conflict")
        table = table_repository.update(db, tenant_id, table_id, {k: v for k, v in fields.items() if v is not None})
        if table is None:
            raise DomainError("Table not found", status_code=404, error_code="table_not_found")
        db.commit()
        db.refresh(table)
        return table

    async def delete_table(self, db: Any, tenant_id: UUID, table_id: UUID) -> None:
        deleted = table_repository.soft_delete(db, tenant_id, table_id)
        if not deleted:
            raise DomainError("Table not found", status_code=404, error_code="table_not_found")
        db.commit()


    def _reconcile_table_statuses(self, db: Any, tenant_id: UUID, tables: list[CafeTable]) -> bool:
        changed = False
        for table in tables:
            active_count = order_repository.count_open_for_table(db, tenant_id, table.id)
            next_status = table.status
            if active_count > 0 and table.status == "free":
                next_status = "occupied"
            elif active_count == 0 and table.status in {"occupied", "bill_requested"}:
                next_status = "free"

            if next_status != table.status:
                table.status = next_status
                changed = True

        if changed:
            db.commit()
            for table in tables:
                db.refresh(table)
        return changed

    async def list_tables(self, db: Any, tenant_id: UUID) -> list[CafeTable]:
        tables = table_repository.get_ordered(db, tenant_id)
        self._reconcile_table_statuses(db, tenant_id, tables)
        return tables

    async def update_status(self, db: Any, tenant_id: UUID, table_id: UUID, status: str) -> CafeTable:
        table = table_repository.update_status(db, tenant_id, table_id, status)
        if table is None:
            raise DomainError("Table not found", status_code=404, error_code="table_not_found")
        db.commit()
        db.refresh(table)
        return table


table_service = TableService()
