from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from .config import settings
from .schemas import ForecastResponse
from .services.elexon import ElexonDataError
from .services.forecast import JAN_END, JAN_START, get_forecast
from .services.metrics import calculate_metrics

router = APIRouter(prefix="/api")


def _dates(
    date_value: date | None, start_date: date | None, end_date: date | None
) -> tuple[date, date]:
    if date_value:
        return date_value, date_value
    return start_date or JAN_START, end_date or JAN_END


async def _data(
    date_value: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = None,
    mode: str | None = None,
) -> dict:
    start, end = _dates(date_value, start_date, end_date)
    selected = mode or ("demo" if settings.demo_mode else "elexon")
    try:
        return await get_forecast(
            selected,
            start,
            end,
            settings.elexon_base_url,
            cutoff or settings.decision_cutoff,
            timezone_name or settings.timezone,
        )
    except (ValueError, ElexonDataError) as exc:
        raise HTTPException(status_code=502 if isinstance(exc, ElexonDataError) else 400, detail=str(exc)) from exc


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": "demo" if settings.demo_mode else "elexon",
        "delivery_range": {"start": JAN_START, "end": JAN_END},
    }


@router.get("/dates")
async def dates():
    return {"dates": [(JAN_START.fromordinal(JAN_START.toordinal() + i)).isoformat() for i in range(31)]}


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    date_value: date | None = Query(None, alias="date"),
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = Query(None, alias="timezone"),
    mode: str | None = None,
):
    return await _data(date_value, start_date, end_date, cutoff, timezone_name, mode)


@router.get("/analysis")
async def analysis(
    date_value: date | None = Query(None, alias="date"),
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = Query(None, alias="timezone"),
):
    data = await _data(date_value, start_date, end_date, cutoff, timezone_name)
    return {**data, "metrics": calculate_metrics(data["points"])}


@router.get("/accuracy")
async def accuracy(
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = Query(None, alias="timezone"),
):
    data = await _data(None, start_date, end_date, cutoff, timezone_name)
    return {"metrics": calculate_metrics(data["points"]), "cutoff": data["cutoff"], "timezone": data["timezone"], "metadata": data["metadata"]}


@router.get("/metrics")
async def metrics(start_date: date | None = None, end_date: date | None = None):
    data = await _data(None, start_date, end_date)
    return calculate_metrics(data["points"])


@router.get("/forecast-history")
async def forecast_history(
    date_value: date = Query(JAN_START, alias="date"),
    interval: str | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = Query(None, alias="timezone"),
):
    data = await _data(date_value, cutoff=cutoff, timezone_name=timezone_name)
    points = data["points"]
    if interval:
        points = [point for point in points if point["timestamp"].strftime("%H:%M") == interval]
    versions = []
    for point in points:
        for version in point.get("forecast_versions", []):
            versions.append({
                **version,
                "selected": (
                    point.get("publish_time") is not None
                    and version.get("publish_time") == point["publish_time"]
                ),
                "eligible_at_cutoff": (
                    version.get("publish_time") is not None
                    and version["publish_time"] <= point["decision_cutoff"]
                ),
                "decision_cutoff": point["decision_cutoff"],
            })
    return {
        "delivery_date": date_value,
        "cutoff": data["cutoff"],
        "timezone": data["timezone"],
        "points": points,
        "metadata": data["metadata"],
        "publication_versions": versions,
    }


@router.get("/export.csv")
async def export_csv(
    date_value: date | None = Query(None, alias="date"),
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff: str | None = None,
    timezone_name: str | None = Query(None, alias="timezone"),
):
    data = await _data(date_value, start_date, end_date, cutoff, timezone_name)
    output = io.StringIO()
    fields = ["timestamp", "forecast_mw", "actual_mw", "method", "publish_time", "missing_forecast"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: point.get(field) for field in fields} for point in data["points"])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=wind-intelligence.csv"})
