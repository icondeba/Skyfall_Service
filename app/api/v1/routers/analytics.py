from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, check_plan, get_current_staff, get_db, get_tenant
from app.schemas.analytics import (
    AnalyticsPeriod,
    AnalyticsSummaryRead,
    PaymentBreakdownRead,
    PeakHoursRead,
    SalesChartRead,
    TopItemsRead,
)
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryRead)
async def get_analytics_summary(
    period: AnalyticsPeriod = Query("today"),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> AnalyticsSummaryRead:
    return await analytics_service.summary(db, tenant_id, period)


@router.get("/sales-chart", response_model=SalesChartRead)
async def get_sales_chart(
    period: str = Query("week", pattern="^(week|month)$"),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> SalesChartRead:
    return await analytics_service.sales_chart(db, tenant_id, period)


@router.get("/top-items", response_model=TopItemsRead)
async def get_top_items(
    limit: int = Query(10, ge=1, le=100),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> TopItemsRead:
    return await analytics_service.top_items(db, tenant_id, limit)


@router.get("/payment-breakdown", response_model=PaymentBreakdownRead)
async def get_payment_breakdown(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> PaymentBreakdownRead:
    return await analytics_service.payment_breakdown(db, tenant_id)


@router.get("/peak-hours", response_model=PeakHoursRead)
async def get_peak_hours(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> PeakHoursRead:
    return await analytics_service.peak_hours(db, tenant_id)
