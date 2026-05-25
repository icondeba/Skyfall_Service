from typing import Any
from uuid import UUID

from app.core.exceptions import DomainError
from app.models import Staff
from app.repositories.staff_repository import staff_repository
from app.schemas.staff import StaffCreate, StaffUpdate


class StaffService:
    async def list_staff(self, db: Any, tenant_id: UUID) -> list[Staff]:
        return staff_repository.get_ordered(db, tenant_id)

    async def create_staff(self, db: Any, tenant_id: UUID, payload: StaffCreate) -> Staff:
        existing = staff_repository.get_by_email(db, tenant_id, payload.email)
        if existing is not None:
            raise DomainError("A staff member with this email already exists", status_code=409, error_code="staff_exists")
        staff = staff_repository.create(
            db,
            tenant_id,
            {
                "name": payload.name.strip(),
                "email": payload.email.lower().strip(),
                "role": payload.role,
                "is_active": True,
            },
        )
        db.commit()
        db.refresh(staff)
        return staff

    async def update_staff(self, db: Any, tenant_id: UUID, staff_id: UUID, payload: StaffUpdate) -> Staff:
        staff = staff_repository.get_by_id(db, tenant_id, staff_id)
        if staff is None:
            raise DomainError("Staff member not found", status_code=404, error_code="staff_not_found")

        if payload.email is not None:
            email = payload.email.lower().strip()
            existing = staff_repository.get_by_email(db, tenant_id, email)
            if existing is not None and existing.id != staff.id:
                raise DomainError("A staff member with this email already exists", status_code=409, error_code="staff_exists")
            staff.email = email
        if payload.name is not None:
            staff.name = payload.name.strip()
        if payload.role is not None:
            staff.role = payload.role
        if payload.is_active is not None:
            staff.is_active = payload.is_active

        db.commit()
        db.refresh(staff)
        return staff

    async def set_active(self, db: Any, tenant_id: UUID, staff_id: UUID, is_active: bool) -> Staff:
        return await self.update_staff(db, tenant_id, staff_id, StaffUpdate(is_active=is_active))


staff_service = StaffService()
