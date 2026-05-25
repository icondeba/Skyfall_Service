from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Staff
from app.repositories.base_repository import BaseRepository


class StaffRepository(BaseRepository[Staff]):
    def __init__(self) -> None:
        super().__init__(Staff)

    def get_ordered(self, db: Session, tenant_id: UUID) -> list[Staff]:
        statement = select(Staff).order_by(Staff.created_at.desc(), Staff.name.asc())
        if hasattr(Staff, "tenant_id"):
            statement = statement.where(Staff.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_by_email(self, db: Session, tenant_id: UUID, email: str) -> Staff | None:
        statement = select(Staff).where(Staff.email == email.lower().strip())
        if hasattr(Staff, "tenant_id"):
            statement = statement.where(Staff.tenant_id == tenant_id)
        return db.scalar(statement)


staff_repository = StaffRepository()
