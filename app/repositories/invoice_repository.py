from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Invoice
from app.repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self) -> None:
        super().__init__(Invoice)

    def count_created_between(
        self,
        db: Session,
        tenant_id: UUID,
        start: datetime,
        end: datetime,
    ) -> int:
        statement = select(func.count(Invoice.id)).where(
            Invoice.created_at >= start,
            Invoice.created_at < end,
        )
        if hasattr(Invoice, "tenant_id"):
            statement = statement.where(Invoice.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0)


invoice_repository = InvoiceRepository()
