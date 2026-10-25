from datetime import datetime, timezone

from app.services.selection import apply_decision_cutoff, decision_cutoff


def test_later_publication_cannot_leak_into_selection():
    delivery = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    points = [{
        "timestamp": delivery,
        "actual_mw": 100,
        "forecast_versions": [
            {"publish_time": datetime(2026, 1, 14, 9, tzinfo=timezone.utc), "forecast_mw": 80},
            {"publish_time": datetime(2026, 1, 14, 10, tzinfo=timezone.utc), "forecast_mw": 90},
            {"publish_time": datetime(2026, 1, 14, 10, 1, tzinfo=timezone.utc), "forecast_mw": 999},
        ],
    }]
    selected = apply_decision_cutoff(points, "10:00", "Europe/London")
    assert selected[0]["forecast_mw"] == 90
    assert selected[0]["publish_time"].hour == 10


def test_cutoff_is_previous_day_in_london_and_equality_is_included():
    delivery = datetime(2026, 1, 15, 0, tzinfo=timezone.utc)
    assert decision_cutoff(delivery, "10:00", "Europe/London") == datetime(
        2026, 1, 14, 10, tzinfo=timezone.utc
    )
