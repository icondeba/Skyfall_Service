from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.repositories.customer_repository import customer_repository
from app.repositories.order_repository import order_repository
from app.repositories.payment_repository import payment_repository
from app.schemas.analytics import (
    AnalyticsPeriod,
    AnalyticsSummaryRead,
    PaymentBreakdownItem,
    PaymentBreakdownRead,
    PeakHourRead,
    PeakHoursRead,
    SalesChartPoint,
    SalesChartRead,
    TopItemRead,
    TopItemsRead,
)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def period_window(period: AnalyticsPeriod) -> tuple[datetime, datetime]:
    now = utc_now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


class AnalyticsService:
    async def summary(self, db: Any, tenant_id: UUID, period: AnalyticsPeriod) -> AnalyticsSummaryRead:
        start, end = period_window(period)
        orders_count, gross_sales = order_repository.summary_between(db, tenant_id, start, end)
        active_orders = order_repository.count_active(db, tenant_id)
        new_customers = customer_repository.count_created_between(db, tenant_id, start, end)
        average_order_value = gross_sales / orders_count if orders_count else 0.0
        return AnalyticsSummaryRead(
            period=period,
            from_date=start,
            to_date=end,
            gross_sales=round(gross_sales, 2),
            orders_count=orders_count,
            average_order_value=round(average_order_value, 2),
            active_orders=active_orders,
            new_customers=new_customers,
        )

    async def sales_chart(self, db: Any, tenant_id: UUID, period: str) -> SalesChartRead:
        days = 7 if period == "week" else 30
        end = utc_now()
        start = (end - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        orders = order_repository.get_between(db, tenant_id, start, end)
        buckets = {
            (start + timedelta(days=offset)).date(): {"sales": 0.0, "orders_count": 0}
            for offset in range(days)
        }
        for order in orders:
            key = order.created_at.date()
            if key in buckets:
                buckets[key]["sales"] += order.total_amount
                buckets[key]["orders_count"] += 1
        return SalesChartRead(
            period=period,
            points=[
                SalesChartPoint(
                    label=day.strftime("%d %b"),
                    sales=round(values["sales"], 2),
                    orders_count=int(values["orders_count"]),
                )
                for day, values in buckets.items()
            ],
        )

    async def top_items(self, db: Any, tenant_id: UUID, limit: int) -> TopItemsRead:
        rows = order_repository.top_items(db, tenant_id, limit)
        return TopItemsRead(
            items=[
                TopItemRead(
                    menu_item_id=str(row[0]),
                    name=row[1],
                    quantity_sold=int(row[2] or 0),
                    gross_sales=round(float(row[3] or 0.0), 2),
                )
                for row in rows
            ]
        )

    async def payment_breakdown(self, db: Any, tenant_id: UUID) -> PaymentBreakdownRead:
        rows = payment_repository.successful_breakdown(db, tenant_id)
        return PaymentBreakdownRead(
            items=[
                PaymentBreakdownItem(
                    mode=row[0],
                    amount=round(float(row[1] or 0.0), 2),
                    count=int(row[2] or 0),
                )
                for row in rows
            ]
        )

    async def peak_hours(self, db: Any, tenant_id: UUID) -> PeakHoursRead:
        start = utc_now() - timedelta(days=30)
        orders = order_repository.get_between(db, tenant_id, start, utc_now())
        buckets = {hour: 0 for hour in range(24)}
        for order in orders:
            buckets[order.created_at.hour] += 1
        return PeakHoursRead(
            hours=[
                PeakHourRead(hour=hour, orders_count=count)
                for hour, count in sorted(buckets.items(), key=lambda item: item[1], reverse=True)
                if count > 0
            ]
        )


analytics_service = AnalyticsService()
