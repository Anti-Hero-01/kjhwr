from datetime import datetime, timedelta, timezone
import math
import random


def generate_points(days: int = 31, seed: int = 7) -> list[dict]:
    """Generate deterministic Jan 2026 delivery data at 48 half-hour intervals/day."""
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    days = min(max(days, 1), 31)
    points = []
    for i in range(days * 48):
        ts = start + timedelta(minutes=30 * i)
        half_hour = ts.hour * 2 + ts.minute // 30
        daily = 95 + 42 * math.sin((half_hour - 8) / 48 * 2 * math.pi)
        weather = 16 * math.sin(i / 11) + rng.uniform(-9, 9)
        actual = max(0.0, daily + weather)
        forecast = max(0.0, daily + 16 * math.sin((i + 2) / 11) + rng.uniform(-7, 7))
        cutoff = ts.replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=1)
        points.append({
            "timestamp": ts,
            "publish_time": cutoff,
            "forecast_mw": round(forecast, 2),
            "actual_mw": round(actual, 2),
            "method": "Demo ensemble",
        })
    return points
