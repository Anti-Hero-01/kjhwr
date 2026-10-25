from datetime import timedelta
from app.services.demo import generate_points


def test_demo_is_fixed_january_half_hour_data():
    points = generate_points()
    assert len(points) == 31 * 48
    assert points[0]["timestamp"].isoformat() == "2026-01-01T00:00:00+00:00"
    assert points[1]["timestamp"] - points[0]["timestamp"] == timedelta(minutes=30)
    assert points[-1]["timestamp"].date().isoformat() == "2026-01-31"
