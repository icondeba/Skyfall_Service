from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, SessionLocal, engine
from app.models import CafeTable, Category, MenuItem, Staff


CATEGORIES = [
    {"name": "Hot Beverages", "icon": "☕", "display_order": 1},
    {"name": "Cold Beverages", "icon": "🥤", "display_order": 2},
    {"name": "Breakfast", "icon": "🍳", "display_order": 3},
    {"name": "Small Plates", "icon": "🍟", "display_order": 4},
    {"name": "Mains", "icon": "🍝", "display_order": 5},
    {"name": "Desserts", "icon": "🍰", "display_order": 6},
]

MENU_ITEMS = [
    {
        "category": "Hot Beverages",
        "name": "Skyfall Cappuccino",
        "description": "Espresso with steamed milk and a soft foam cap.",
        "base_price": 149.0,
        "is_veg": True,
        "prep_time_minutes": 6,
    },
    {
        "category": "Hot Beverages",
        "name": "Masala Chai",
        "description": "House chai simmered with ginger and warming spices.",
        "base_price": 99.0,
        "is_veg": True,
        "prep_time_minutes": 7,
    },
    {
        "category": "Hot Beverages",
        "name": "Classic Hot Chocolate",
        "description": "Rich cocoa blended with steamed milk.",
        "base_price": 139.0,
        "is_veg": True,
        "prep_time_minutes": 6,
    },
    {
        "category": "Cold Beverages",
        "name": "Iced Americano",
        "description": "Chilled espresso over ice with filtered water.",
        "base_price": 129.0,
        "is_veg": True,
        "prep_time_minutes": 5,
    },
    {
        "category": "Cold Beverages",
        "name": "Mango Mint Cooler",
        "description": "Mango, mint, lime, and soda.",
        "base_price": 159.0,
        "is_veg": True,
        "prep_time_minutes": 8,
    },
    {
        "category": "Cold Beverages",
        "name": "Berry Iced Tea",
        "description": "Black tea shaken with berry syrup and lemon.",
        "base_price": 149.0,
        "is_veg": True,
        "prep_time_minutes": 7,
    },
    {
        "category": "Breakfast",
        "name": "Paneer Bhurji Toast",
        "description": "Spiced paneer scramble on buttered toast.",
        "base_price": 219.0,
        "is_veg": True,
        "prep_time_minutes": 14,
    },
    {
        "category": "Breakfast",
        "name": "Cheese Omelette",
        "description": "Three-egg omelette with cheese and herbs.",
        "base_price": 199.0,
        "is_veg": False,
        "prep_time_minutes": 12,
    },
    {
        "category": "Small Plates",
        "name": "Peri Peri Fries",
        "description": "Crisp fries tossed with peri peri seasoning.",
        "base_price": 169.0,
        "is_veg": True,
        "prep_time_minutes": 10,
    },
    {
        "category": "Small Plates",
        "name": "Chicken Popcorn",
        "description": "Bite-sized fried chicken with house dip.",
        "base_price": 239.0,
        "is_veg": False,
        "prep_time_minutes": 14,
    },
    {
        "category": "Small Plates",
        "name": "Loaded Nachos",
        "description": "Nachos layered with beans, salsa, cheese, and jalapenos.",
        "base_price": 249.0,
        "is_veg": True,
        "prep_time_minutes": 12,
    },
    {
        "category": "Mains",
        "name": "Creamy Alfredo Pasta",
        "description": "Penne in parmesan cream sauce with vegetables.",
        "base_price": 329.0,
        "is_veg": True,
        "prep_time_minutes": 18,
    },
    {
        "category": "Mains",
        "name": "Grilled Chicken Sandwich",
        "description": "Grilled chicken, lettuce, tomato, and aioli in toasted bread.",
        "base_price": 289.0,
        "is_veg": False,
        "prep_time_minutes": 16,
    },
    {
        "category": "Desserts",
        "name": "Chocolate Brownie",
        "description": "Warm brownie served with chocolate sauce.",
        "base_price": 179.0,
        "is_veg": True,
        "prep_time_minutes": 8,
    },
    {
        "category": "Desserts",
        "name": "Biscoff Cheesecake",
        "description": "No-bake cheesecake with a Biscoff crumb base.",
        "base_price": 229.0,
        "is_veg": True,
        "prep_time_minutes": 5,
    },
]

STAFF = [
    {"name": "Aarav Mehta", "email": "aarav@skyfall.local", "role": "admin"},
    {"name": "Nisha Rao", "email": "nisha@skyfall.local", "role": "waiter"},
    {"name": "Kabir Khan", "email": "kabir@skyfall.local", "role": "kitchen"},
]

TABLES = [
    {"table_number": 1, "capacity": 2},
    {"table_number": 2, "capacity": 4},
    {"table_number": 3, "capacity": 4},
    {"table_number": 4, "capacity": 6},
    {"table_number": 5, "capacity": 8},
    {"table_number": 6, "capacity": 4},
]


def first_or_none(session: Session, statement):
    return session.scalars(statement).first()


def seed_categories(session: Session) -> dict[str, Category]:
    categories: dict[str, Category] = {}

    for data in CATEGORIES:
        category = first_or_none(session, select(Category).where(Category.name == data["name"]))
        if category is None:
            category = Category(**data)
            session.add(category)
        else:
            category.icon = data["icon"]
            category.display_order = data["display_order"]
            category.is_active = True
        categories[category.name] = category

    session.flush()
    return categories


def seed_menu_items(session: Session, categories: dict[str, Category]) -> None:
    for data in MENU_ITEMS:
        item = first_or_none(session, select(MenuItem).where(MenuItem.name == data["name"]))
        item_data = {
            "category": categories[data["category"]],
            "name": data["name"],
            "description": data["description"],
            "base_price": data["base_price"],
            "is_veg": data["is_veg"],
            "prep_time_minutes": data["prep_time_minutes"],
            "is_available": True,
        }

        if item is None:
            session.add(MenuItem(**item_data))
        else:
            for key, value in item_data.items():
                setattr(item, key, value)


def seed_staff(session: Session) -> None:
    for data in STAFF:
        staff = first_or_none(session, select(Staff).where(Staff.email == data["email"]))
        if staff is None:
            session.add(Staff(**data))
        else:
            staff.name = data["name"]
            staff.role = data["role"]
            staff.is_active = True


def seed_tables(session: Session) -> None:
    for data in TABLES:
        table = first_or_none(
            session,
            select(CafeTable).where(CafeTable.table_number == data["table_number"]),
        )
        if table is None:
            session.add(CafeTable(**data))
        else:
            table.capacity = data["capacity"]


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        categories = seed_categories(session)
        seed_menu_items(session, categories)
        seed_staff(session)
        seed_tables(session)
        session.commit()

    print("Seeded 6 categories, 15 menu items, 3 staff, and 6 tables.")


if __name__ == "__main__":
    main()
