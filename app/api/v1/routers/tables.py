from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.table import TableCreate, TableListRead, TableRead, TableStatusUpdate, TableUpdate
from app.services.table_service import table_service

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=TableListRead)
async def list_tables(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> TableListRead:
    tables = await table_service.list_tables(db, tenant_id)
    return TableListRead(tables=tables)


@router.post("", response_model=TableRead, status_code=201)
async def create_table(
    payload: TableCreate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> TableRead:
    table = await table_service.create_table(db, tenant_id, payload.table_number, payload.capacity)
    return TableRead.model_validate(table)


@router.patch("/{table_id}", response_model=TableRead)
async def update_table(
    table_id: UUID,
    payload: TableUpdate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> TableRead:
    table = await table_service.update_table(db, tenant_id, table_id, payload.model_dump())
    return TableRead.model_validate(table)


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    table_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> Response:
    await table_service.delete_table(db, tenant_id, table_id)
    return Response(status_code=204)


@router.patch("/{table_id}/status", response_model=TableRead)
async def update_table_status(
    table_id: UUID,
    payload: TableStatusUpdate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> TableRead:
    table = await table_service.update_status(db, tenant_id, table_id, payload.status)
    return TableRead.model_validate(table)
