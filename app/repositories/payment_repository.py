from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Payment
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)

    def get_by_razorpay_order_id(
        self,
        db: Session,
        tenant_id: UUID,
        razorpay_order_id: str,
    ) -> Payment | None:
        statement = select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        if hasattr(Payment, "tenant_id"):
            statement = statement.where(Payment.tenant_id == tenant_id)
        return db.scalar(statement)

    def get_latest_for_order(self, db: Session, tenant_id: UUID, order_id: UUID) -> Payment | None:
        statement = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        )
        if hasattr(Payment, "tenant_id"):
            statement = statement.where(Payment.tenant_id == tenant_id)
        return db.scalar(statement)

    def successful_breakdown(self, db: Session, tenant_id: UUID) -> list[tuple]:
        statement = (
            select(
                Payment.mode,
                func.coalesce(func.sum(Payment.amount), 0.0),
                func.count(Payment.id),
            )
            .where(Payment.status == "success")
            .group_by(Payment.mode)
            .order_by(func.sum(Payment.amount).desc())
        )
        if hasattr(Payment, "tenant_id"):
            statement = statement.where(Payment.tenant_id == tenant_id)
        return list(db.execute(statement).all())


payment_repository = PaymentRepository()
