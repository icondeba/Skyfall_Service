from fastapi import APIRouter

from app.api.v1.routers import (
    analytics,
    auth,
    billing,
    crm,
    customers,
    kot,
    menu,
    orders,
    payments,
    platform,
    staff,
    tables,
    tenants,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(menu.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(staff.router)
api_router.include_router(customers.router)
api_router.include_router(tables.router)
api_router.include_router(kot.router)
api_router.include_router(billing.router)
api_router.include_router(analytics.router)
api_router.include_router(crm.router)
api_router.include_router(tenants.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
