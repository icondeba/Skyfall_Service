from uuid import UUID
from typing import Any

from app.core.exceptions import DomainError
from app.models import MenuItem
from app.repositories.menu_repository import category_repository, menu_repository
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuRead


class MenuService:
    async def list_menu(self, db: Any, tenant_id: UUID) -> MenuRead:
        categories = category_repository.get_active_with_items(db, tenant_id)
        for category in categories:
            category.menu_items.sort(key=lambda item: item.name.lower())
        return MenuRead(categories=categories)

    async def get_item(self, db: Any, tenant_id: UUID, item_id: UUID) -> MenuItem:
        item = menu_repository.get_item_with_details(db, tenant_id, item_id)
        if item is None:
            raise DomainError("Menu item not found", status_code=404, error_code="menu_item_not_found")
        return item

    async def list_categories(self, db: Any, tenant_id: UUID) -> list:
        return category_repository.get_active(db, tenant_id)

    async def create_item(self, db: Any, tenant_id: UUID, payload: MenuItemCreate) -> MenuItem:
        if category_repository.get_by_id(db, tenant_id, payload.category_id) is None:
            raise DomainError("Category not found", status_code=404, error_code="category_not_found")
        item = menu_repository.create(
            db,
            tenant_id,
            payload.model_dump(exclude={"variants", "addons"}),
        )
        menu_repository.replace_variants(item, [variant.model_dump() for variant in payload.variants])
        menu_repository.replace_addons(item, [addon.model_dump() for addon in payload.addons])
        db.commit()
        return await self.get_item(db, tenant_id, item.id)

    async def update_item(self, db: Any, tenant_id: UUID, item_id: UUID, payload: MenuItemUpdate) -> MenuItem:
        item = await self.get_item(db, tenant_id, item_id)
        updates = payload.model_dump(exclude_unset=True, exclude={"variants", "addons"})
        if "category_id" in updates and category_repository.get_by_id(db, tenant_id, updates["category_id"]) is None:
            raise DomainError("Category not found", status_code=404, error_code="category_not_found")
        for field, value in updates.items():
            setattr(item, field, value)
        if "variants" in payload.model_fields_set:
            menu_repository.replace_variants(
                item,
                [variant.model_dump() for variant in (payload.variants or [])],
            )
        if "addons" in payload.model_fields_set:
            menu_repository.replace_addons(
                item,
                [addon.model_dump() for addon in (payload.addons or [])],
            )
        db.commit()
        return await self.get_item(db, tenant_id, item.id)

    async def update_availability(self, db: Any, tenant_id: UUID, item_id: UUID, is_available: bool) -> MenuItem:
        item = await self.get_item(db, tenant_id, item_id)
        item.is_available = is_available
        db.commit()
        return await self.get_item(db, tenant_id, item.id)


menu_service = MenuService()
