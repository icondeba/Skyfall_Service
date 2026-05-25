from uuid import UUID
from typing import Any

from app.core.exceptions import DomainError
from app.models import Customer
from app.repositories.customer_repository import customer_repository
from app.schemas.customer import CustomerIdentifyRequest, CustomerIdentifyResponse, CustomerListRead


class CustomerService:
    async def identify(self, db: Any, tenant_id: UUID, payload: CustomerIdentifyRequest) -> CustomerIdentifyResponse:
        phone = payload.phone.strip()
        if not phone:
            raise DomainError("Phone number is required", status_code=422, error_code="phone_required")
        customer = customer_repository.get_by_phone(db, tenant_id, phone)
        is_new = customer is None
        if customer is None:
            customer = customer_repository.create(
                db,
                tenant_id,
                {
                    "phone": phone,
                    "name": payload.name,
                    "email": payload.email,
                    "birthday": payload.birthday,
                    "anniversary": payload.anniversary,
                    "special_event_date": payload.special_event_date,
                    "special_event_name": payload.special_event_name,
                },
            )
        else:
            if payload.name is not None:
                customer.name = payload.name
            if payload.email is not None:
                customer.email = payload.email
            if payload.birthday is not None:
                customer.birthday = payload.birthday
            if payload.anniversary is not None:
                customer.anniversary = payload.anniversary
            if payload.special_event_date is not None:
                customer.special_event_date = payload.special_event_date
            if payload.special_event_name is not None:
                customer.special_event_name = payload.special_event_name
        db.commit()
        db.refresh(customer)
        return CustomerIdentifyResponse(customer=customer, is_new=is_new)

    async def get_customer(self, db: Any, tenant_id: UUID, customer_id: UUID) -> Customer:
        customer = customer_repository.get_by_id(db, tenant_id, customer_id)
        if customer is None:
            raise DomainError("Customer not found", status_code=404, error_code="customer_not_found")
        return customer

    async def get_repeat_customers(self, db: Any, tenant_id: UUID) -> CustomerListRead:
        return CustomerListRead(customers=customer_repository.get_repeat(db, tenant_id))


customer_service = CustomerService()
