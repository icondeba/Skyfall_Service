from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tenant
from app.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self) -> None:
        super().__init__(Tenant)

    def get_by_slug(self, db: Session, slug: str) -> Tenant | None:
        return db.scalar(select(Tenant).where(Tenant.slug == slug))

    def get_by_id_unscoped(self, db: Session, tenant_id: UUID) -> Tenant | None:
        return db.get(Tenant, tenant_id)


tenant_repository = TenantRepository()
