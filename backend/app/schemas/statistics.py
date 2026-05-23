from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class StatisticsPeriod(StrEnum):
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    LAST_365D = "365d"


PERIOD_DAYS = {
    StatisticsPeriod.LAST_7D: 7,
    StatisticsPeriod.LAST_30D: 30,
    StatisticsPeriod.LAST_90D: 90,
    StatisticsPeriod.LAST_365D: 365,
}


class TopServiceRow(BaseModel):
    service_id: int
    service_title: str
    completed_count: int
    revenue: Decimal


class TopStaffRow(BaseModel):
    staff_id: int
    staff_name: str
    completed_count: int


class DailyVolumeRow(BaseModel):
    date: date
    bookings_count: int


class StatisticsResponse(BaseModel):
    period: StatisticsPeriod
    revenue: Decimal
    total_bookings: int
    completed_count: int
    no_show_count: int
    cancellation_count: int
    cancellation_rate: float
    top_services: list[TopServiceRow]
    top_staff: list[TopStaffRow]
    daily_volume: list[DailyVolumeRow]
