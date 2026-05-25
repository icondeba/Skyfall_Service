from uuid import UUID

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Customer
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self) -> None:
        super().__init__(Customer)

    def get_by_phone(self, db: Session, tenant_id: UUID, phone: str) -> Customer | None:
        statement = select(Customer).where(Customer.phone == phone)
        if hasattr(Customer, "tenant_id"):
            statement = statement.where(Customer.tenant_id == tenant_id)
        return db.scalar(statement)

    def get_repeat(self, db: Session, tenant_id: UUID) -> list[Customer]:
        statement = (
            select(Customer)
            .where(Customer.visit_count > 1)
            .order_by(Customer.visit_count.desc(), Customer.total_spent.desc())
        )
        if hasattr(Customer, "tenant_id"):
            statement = statement.where(Customer.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def search(self, db: Session, tenant_id: UUID, search: str | None = None) -> list[Customer]:
        statement = select(Customer).order_by(Customer.created_at.desc())
        if hasattr(Customer, "tenant_id"):
            statement = statement.where(Customer.tenant_id == tenant_id)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Customer.phone.ilike(pattern),
                    Customer.name.ilike(pattern),
                    Customer.email.ilike(pattern),
                )
            )
        return list(db.scalars(statement))

    def count_created_between(self, db: Session, tenant_id: UUID, start: datetime, end: datetime) -> int:
        statement = select(func.count(Customer.id)).where(
            Customer.created_at >= start,
            Customer.created_at <= end,
        )
        if hasattr(Customer, "tenant_id"):
            statement = statement.where(Customer.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0)


customer_repository = CustomerRepository()
