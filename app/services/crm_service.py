import csv
from datetime import UTC, datetime, timedelta
from io import StringIO
from typing import Any, Literal
from uuid import UUID

from app.core.exceptions import DomainError
from app.repositories.customer_repository import customer_repository
from app.repositories.order_repository import order_repository
from app.schemas.crm import CRMCustomerDetailRead, CRMCustomerListRead, CRMCustomerRead
from app.schemas.customer import CustomerRead

CustomerTag = Literal["vip", "regular", "new", "inactive"]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def customer_tag(customer: Any) -> str:
    inactive_before = utc_now() - timedelta(days=60)
    if customer.last_visit is not None and customer.last_visit < inactive_before:
        return "inactive"
    if customer.visit_count <= 1:
        return "new"
    if customer.visit_count >= 5 or customer.total_spent >= 5000:
        return "vip"
    return "regular"


class CRMService:
    def _filtered_customers(
        self,
        db: Any,
        tenant_id: UUID,
        tag: CustomerTag | None,
        search: str | None,
    ) -> list:
        customers = customer_repository.search(db, tenant_id, search)
        if tag is None:
            return customers
        return [customer for customer in customers if customer_tag(customer) == tag]

    async def list_customers(
        self,
        db: Any,
        tenant_id: UUID,
        page: int,
        limit: int,
        tag: CustomerTag | None,
        search: str | None,
    ) -> CRMCustomerListRead:
        customers = self._filtered_customers(db, tenant_id, tag, search)
        start = (page - 1) * limit
        end = start + limit
        return CRMCustomerListRead(
            page=page,
            limit=limit,
            total=len(customers),
            customers=[
                CRMCustomerRead(
                    **CustomerRead.model_validate(customer).model_dump(),
                    tag=customer_tag(customer),
                )
                for customer in customers[start:end]
            ],
        )

    async def get_customer_detail(self, db: Any, tenant_id: UUID, customer_id: UUID) -> CRMCustomerDetailRead:
        customer = customer_repository.get_by_id(db, tenant_id, customer_id)
        if customer is None:
            raise DomainError("Customer not found", status_code=404, error_code="customer_not_found")
        return CRMCustomerDetailRead(
            customer=customer,
            tag=customer_tag(customer),
            orders=order_repository.get_by_customer(db, tenant_id, customer_id),
        )

    async def export_customers(
        self,
        db: Any,
        tenant_id: UUID,
        tag: CustomerTag | None,
        search: str | None,
    ) -> str:
        customers = self._filtered_customers(db, tenant_id, tag, search)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "phone",
                "name",
                "email",
                "tag",
                "visit_count",
                "total_spent",
                "last_visit",
                "created_at",
            ]
        )
        for customer in customers:
            writer.writerow(
                [
                    str(customer.id),
                    customer.phone,
                    customer.name or "",
                    customer.email or "",
                    customer_tag(customer),
                    customer.visit_count,
                    f"{customer.total_spent:.2f}",
                    customer.last_visit.isoformat() if customer.last_visit else "",
                    customer.created_at.isoformat(),
                ]
            )
        return output.getvalue()


crm_service = CRMService()
