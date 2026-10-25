from datetime import datetime, timezone

from app.services.elexon import aggregate_actuals_to_hour


def test_raw_fuelhh_records_are_aggregated_to_hourly_mw():
    rows = [
        {
            "dataset": "FUELHH",
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 100,
        },
        {
            "dataset": "FUELHH",
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:30:00Z",
            "generation": 140,
        },
        {
            "dataset": "FUELHH",
            "fuelType": "GAS",
            "startTime": "2026-01-15T00:30:00Z",
            "generation": 999,
        },
    ]
    result = aggregate_actuals_to_hour(rows)
    assert result[datetime(2026, 1, 15, tzinfo=timezone.utc)] == 120
