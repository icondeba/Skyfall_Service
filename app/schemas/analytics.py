from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AnalyticsPeriod = Literal["today", "week", "month"]


class AnalyticsSummaryRead(BaseModel):
    period: AnalyticsPeriod
    from_date: datetime
    to_date: datetime
    gross_sales: float
    orders_count: int
    average_order_value: float
    active_orders: int
    new_customers: int


class SalesChartPoint(BaseModel):
    label: str
    sales: float
    orders_count: int


class SalesChartRead(BaseModel):
    period: Literal["week", "month"]
    points: list[SalesChartPoint]


class TopItemRead(BaseModel):
    menu_item_id: str
    name: str
    quantity_sold: int
    gross_sales: float


class TopItemsRead(BaseModel):
    items: list[TopItemRead]


class PaymentBreakdownItem(BaseModel):
    mode: str
    amount: float
    count: int


class PaymentBreakdownRead(BaseModel):
    items: list[PaymentBreakdownItem]


class PeakHourRead(BaseModel):
    hour: int
    orders_count: int


class PeakHoursRead(BaseModel):
    hours: list[PeakHourRead]
