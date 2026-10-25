from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

FUELHH = "FUELHH"
WINDFOR = "WINDFOR"


class ElexonDataError(RuntimeError):
    """An upstream Elexon response could not be used safely."""


def aggregate_actuals_to_hour(rows: list[dict[str, Any]]) -> dict[datetime, float]:
    """Aggregate FUELHH MW observations to the hourly WINDFOR resolution."""
    half_hours: dict[datetime, list[float]] = {}
    for row in rows:
        if row.get("fuelType") != "WIND" or row.get("generation") is None:
            continue
        timestamp = _parse_timestamp(row.get("startTime"))
        try:
            value = float(row["generation"])
        except (TypeError, ValueError) as exc:
            raise ElexonDataError(f"Invalid FUELHH generation: {row!r}") from exc
        half_hours.setdefault(
            timestamp.replace(minute=0, second=0, microsecond=0), []
        ).append(value)
    return {
        timestamp: sum(values) / len(values)
        for timestamp, values in half_hours.items()
    }


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ElexonDataError(f"Missing timestamp in Elexon record: {value!r}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ElexonDataError(f"Invalid Elexon timestamp: {value!r}") from exc
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(
        timezone.utc
    )


async def _get_dataset(
    client: httpx.AsyncClient,
    base_url: str,
    dataset: str,
    params: dict[str, str],
) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/datasets/{dataset}/stream"
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ElexonDataError(
            f"Elexon {dataset} request failed for {params}: {exc}"
        ) from exc
    if not isinstance(payload, list):
        raise ElexonDataError(f"Elexon {dataset} returned a non-array payload")
    return [row for row in payload if isinstance(row, dict)]


async def fetch_wind_data(
    base_url: str,
    start_date: date,
    end_date: date,
    cutoff_hour: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Fetch January wind actuals and all forecast publications needed for cutoff selection.

    FUELHH accepts settlementDateFrom/settlementDateTo and returns half-hourly
    records. WINDFOR accepts publishDateTimeFrom/publishDateTimeTo and returns
    publication versions (hourly in the observed January 2026 response).
    """
    publish_from = datetime.combine(
        start_date - timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc
    )
    publish_to = datetime.combine(
        end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )
    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
        actual_rows = await _get_dataset(
            client,
            base_url,
            FUELHH,
            {
                "settlementDateFrom": start_date.isoformat(),
                "settlementDateTo": end_date.isoformat(),
            },
        )
        forecast_rows = await _get_dataset(
            client,
            base_url,
            WINDFOR,
            {
                "publishDateTimeFrom": publish_from.isoformat().replace("+00:00", "Z"),
                "publishDateTimeTo": publish_to.isoformat().replace("+00:00", "Z"),
            },
        )

    actual_wind_rows = [
        row for row in actual_rows
        if row.get("fuelType") == "WIND" and row.get("generation") is not None
    ]

    forecasts: list[dict[str, Any]] = []
    for row in forecast_rows:
        if row.get("generation") is None:
            continue
        try:
            forecasts.append(
                {
                    "timestamp": _parse_timestamp(row.get("startTime")),
                    "publish_time": _parse_timestamp(row.get("publishTime")),
                    "forecast_mw": float(row["generation"]),
                    "dataset": row.get("dataset", WINDFOR),
                }
            )
        except (TypeError, ValueError) as exc:
            raise ElexonDataError(f"Invalid WINDFOR generation: {row!r}") from exc

    actuals = aggregate_actuals_to_hour(actual_wind_rows)
    points: list[dict[str, Any]] = []
    for timestamp, actual in sorted(actuals.items()):
        if not (start_date <= timestamp.date() <= end_date):
            continue
        eligible = [
            forecast
            for forecast in forecasts
            if forecast["timestamp"] == timestamp
        ]
        points.append(
            {
                "timestamp": timestamp,
                "actual_mw": actual,
                "forecast_versions": sorted(
                    eligible, key=lambda item: item["publish_time"]
                ),
                "method": "Elexon WINDFOR at cutoff",
            }
        )

    metadata = {
        "actual_records_retrieved": len(actual_rows),
        "forecast_records_retrieved": len(forecast_rows),
        "actual_wind_records": len(actual_wind_rows),
        "actual_hourly_intervals": len(actuals),
        "forecast_publication_versions": len(forecasts),
        "units": "MW (Elexon generation fields)",
        "forecast_resolution": "Hourly target intervals",
        "actual_resolution": "FUELHH half-hourly aggregated to hourly arithmetic mean (two observations)",
        "matching_resolution": "Hourly UTC startTime",
        "cutoff_hour": cutoff_hour,
        "historical_publication_window": {
            "from": publish_from.isoformat(),
            "to": publish_to.isoformat(),
        },
    }
    return points, forecasts, metadata
