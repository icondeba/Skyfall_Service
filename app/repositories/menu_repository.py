from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Category, ItemAddon, ItemVariant, MenuItem
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self) -> None:
        super().__init__(Category)

    def get_active_with_items(self, db: Session, tenant_id: UUID) -> list[Category]:
        statement = (
            select(Category)
            .where(Category.is_active.is_(True))
            .options(
                selectinload(Category.menu_items).selectinload(MenuItem.category),
                selectinload(Category.menu_items).selectinload(MenuItem.variants),
                selectinload(Category.menu_items).selectinload(MenuItem.addons),
            )
            .order_by(Category.display_order, Category.name)
        )
        if hasattr(Category, "tenant_id"):
            statement = statement.where(Category.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_active(self, db: Session, tenant_id: UUID) -> list[Category]:
        statement = (
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.display_order, Category.name)
        )
        if hasattr(Category, "tenant_id"):
            statement = statement.where(Category.tenant_id == tenant_id)
        return list(db.scalars(statement))


class MenuRepository(BaseRepository[MenuItem]):
    def __init__(self) -> None:
        super().__init__(MenuItem)

    def get_item_with_details(self, db: Session, tenant_id: UUID, item_id: UUID) -> MenuItem | None:
        statement = (
            select(MenuItem)
            .where(MenuItem.id == item_id)
            .options(
                selectinload(MenuItem.category),
                selectinload(MenuItem.variants),
                selectinload(MenuItem.addons),
            )
        )
        if hasattr(MenuItem, "tenant_id"):
            statement = statement.where(MenuItem.tenant_id == tenant_id)
        return db.scalar(statement)

    def replace_variants(self, item: MenuItem, variants: list[dict]) -> None:
        item.variants.clear()
        item.variants.extend(ItemVariant(**variant) for variant in variants)

    def replace_addons(self, item: MenuItem, addons: list[dict]) -> None:
        item.addons.clear()
        item.addons.extend(ItemAddon(**addon) for addon in addons)


category_repository = CategoryRepository()
menu_repository = MenuRepository()
