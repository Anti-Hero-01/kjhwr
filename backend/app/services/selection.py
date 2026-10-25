from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def decision_cutoff(
    delivery_timestamp: datetime, cutoff: str, timezone_name: str
) -> datetime:
    local_delivery = delivery_timestamp.astimezone(ZoneInfo(timezone_name))
    hour, minute = (int(part) for part in cutoff.split(":", 1))
    local_cutoff = datetime.combine(
        local_delivery.date() - timedelta(days=1),
        time(hour=hour, minute=minute),
        tzinfo=ZoneInfo(timezone_name),
    )
    return local_cutoff.astimezone(delivery_timestamp.tzinfo)


def select_latest_eligible(
    versions: list[dict], delivery_timestamp: datetime, cutoff: str, timezone_name: str
) -> dict | None:
    cutoff_timestamp = decision_cutoff(delivery_timestamp, cutoff, timezone_name)
    eligible = [
        version
        for version in versions
        if version.get("publish_time") is not None
        and version["publish_time"] <= cutoff_timestamp
    ]
    return max(eligible, key=lambda version: version["publish_time"]) if eligible else None


def apply_decision_cutoff(
    points: list[dict], cutoff: str = "10:00", timezone_name: str = "Europe/London"
) -> list[dict]:
    selected = []
    for point in points:
        versions = point.get("forecast_versions", [])
        forecast = select_latest_eligible(
            versions, point["timestamp"], cutoff, timezone_name
        )
        selected.append(
            {
                "timestamp": point["timestamp"],
                "publish_time": forecast.get("publish_time") if forecast else None,
                "forecast_mw": forecast.get("forecast_mw") if forecast else None,
                "actual_mw": point.get("actual_mw"),
                "method": point.get("method"),
                "missing_forecast": forecast is None,
                "forecast_versions": versions,
                "decision_cutoff": decision_cutoff(
                    point["timestamp"], cutoff, timezone_name
                ),
            }
        )
    return selected
