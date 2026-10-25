from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    timestamp: datetime
    publish_time: datetime | None = None
    forecast_mw: float | None = None
    actual_mw: float | None = None
    method: str
    missing_forecast: bool = False


class ForecastResponse(BaseModel):
    mode: Literal["demo", "elexon"]
    generated_at: datetime
    points: list[ForecastPoint]
    metadata: dict
    cutoff: str
    timezone: str


class Metrics(BaseModel):
    bias_mw: float | None
    mae_mw: float | None
    rmse_mw: float | None
    nmae_percent: float | None
    mape_percent: float | None
    coverage_percent: float
    sample_count: int
    expected_count: int
    missing_forecast_count: int
    missing_actual_count: int


class HistoryRow(BaseModel):
    timestamp: datetime
    publish_time: datetime | None = None
    forecast_mw: float | None = None
    actual_mw: float | None = None
    eligible: bool
