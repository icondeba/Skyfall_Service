# Skyfall 4-Layer Migration Guide

## Orders

Before:

```python
@router.post("/orders")
async def create_order(payload, db):
    table = db.query(CafeTable).filter_by(id=payload.table_id).first()
    order = Order(**payload.model_dump())
    db.add(order)
    db.commit()
    return order
```

After:

```python
@router.post("/orders")
async def create_order(payload, db=Depends(get_db), tenant_id=Depends(get_tenant)):
    order = await order_service.create_order(db, tenant_id, payload)
    return OrderResponse.model_validate(order)
```

Router validates HTTP input only. `OrderService` validates table state, totals, table occupancy, status transitions, and KOT side effects. `OrderRepository`, `TableRepository`, and `MenuRepository` perform ORM reads/writes.

## Payments

Before:

```python
@router.post("/payments/razorpay/create-order")
async def create_payment(payload, db):
    order = db.query(Order).filter_by(id=payload.order_id).first()
    gateway_order = razorpay.Client(...).order.create(...)
    payment = Payment(order_id=order.id, status="pending")
    db.add(payment)
    db.commit()
    return gateway_order
```

After:

```python
@router.post("/payments/razorpay/create-order")
async def create_payment(payload, db=Depends(get_db), tenant_id=Depends(get_tenant)):
    return await payment_service.create_razorpay_order(db, tenant_id, payload)
```

Router stays thin. `PaymentService` owns payment state rules. `services/integrations/razorpay.py` owns Razorpay transport. `PaymentRepository` owns payment queries.

## Menu

Before:

```python
@router.get("/menu")
async def list_menu(db):
    return db.query(Category).options(...).all()
```

After:

```python
@router.get("/menu")
async def list_menu(db=Depends(get_db), tenant_id=Depends(get_tenant)):
    return await menu_service.list_menu(db, tenant_id)
```

Router delegates. `MenuService` applies the existing sort/shape behavior. `MenuRepository` performs category/item eager loading.

## Delete Checklist

Already removed from the old structure:

- `app/routers/*.py`
- `app/services/ordering.py`
- `app/services/realtime.py`

Keep as compatibility shims:

- `app/config.py` re-exports `app.core.config`
- `app/dependencies.py` re-exports `app.api.dependencies`
- `app/db/database.py` re-exports `app.core.database`

Copy future changes into these layers:

- Router code: only HTTP decorators, dependencies, service calls, response validation.
- Service code: business rules, orchestration, transaction commits, external integration calls through `services/integrations`.
- Repository code: SQLAlchemy ORM queries and persistence only.
- Model/schema code: SQLAlchemy columns/relationships and Pydantic v2 request/response models only.
