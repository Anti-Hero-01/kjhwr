from __future__ import annotations

from datetime import date, datetime, timezone

from .demo import generate_points
from .elexon import fetch_wind_data
from .selection import apply_decision_cutoff

JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)


def validate_dates(start_date: date, end_date: date) -> None:
    if start_date < JAN_START or end_date > JAN_END or start_date > end_date:
        raise ValueError("Only delivery dates from 2026-01-01 through 2026-01-31 are supported")


async def get_forecast(
    mode: str,
    start_date: date = JAN_START,
    end_date: date = JAN_END,
    base_url: str = "",
    cutoff: str = "10:00",
    timezone_name: str = "Europe/London",
) -> dict:
    validate_dates(start_date, end_date)
    if mode == "demo":
        raw = generate_points((end_date - JAN_START).days + 1)
        raw = [point for point in raw if start_date <= point["timestamp"].date() <= end_date]
        for point in raw:
            point["forecast_versions"] = [
                {
                    "timestamp": point["timestamp"],
                    "publish_time": point["publish_time"],
                    "forecast_mw": point["forecast_mw"],
                }
            ]
        metadata = {
            "source": "synthetic demo data",
            "real_data": False,
            "actual_records_retrieved": len(raw),
            "forecast_records_retrieved": len(raw),
            "units": "MW (synthetic)",
            "matching_resolution": "Half-hourly demo fixture",
        }
    else:
        raw, _, metadata = await fetch_wind_data(
            base_url, start_date, end_date, int(cutoff.split(":", 1)[0])
        )
        metadata["source"] = "Elexon BMRS FUELHH and WINDFOR"
        metadata["real_data"] = True
    points = apply_decision_cutoff(raw, cutoff, timezone_name)
    return {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc),
        "points": points,
        "metadata": metadata,
        "cutoff": cutoff,
        "timezone": timezone_name,
    }
