import math
from collections.abc import Iterable


def calculate_metrics(points: Iterable[dict]) -> dict:
    points = list(points)
    pairs = []
    for point in points:
        try:
            forecast, actual = point.get("forecast_mw"), point.get("actual_mw")
            if forecast is None or actual is None:
                continue
            forecast, actual = float(forecast), float(actual)
            if math.isfinite(forecast) and math.isfinite(actual):
                pairs.append((forecast, actual))
        except (TypeError, ValueError):
            continue
    expected_count = len(points)
    missing_forecast_count = sum(
        1 for point in points if point.get("forecast_mw") is None
    )
    missing_actual_count = sum(
        1 for point in points if point.get("actual_mw") is None
    )
    if not pairs:
        return {"bias_mw": None, "mae_mw": None, "rmse_mw": None, "nmae_percent": None, "mape_percent": None, "coverage_percent": 0.0, "sample_count": 0, "expected_count": expected_count, "missing_forecast_count": missing_forecast_count, "missing_actual_count": missing_actual_count}
    errors = [f - a for f, a in pairs]
    nonzero = [(f, a) for f, a in pairs if a != 0]
    mae = sum(abs(e) for e in errors) / len(errors)
    mean_actual = sum(abs(a) for _, a in pairs) / len(pairs)
    return {
        "bias_mw": round(sum(errors) / len(errors), 2),
        "mae_mw": round(mae, 2),
        "rmse_mw": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 2),
        "nmae_percent": round(mae / mean_actual * 100, 2) if mean_actual else None,
        "mape_percent": round(sum(abs(f - a) / abs(a) for f, a in nonzero) / len(nonzero) * 100, 2) if nonzero else None,
        "coverage_percent": round(len(pairs) / max(1, len(points)) * 100, 2),
        "sample_count": len(pairs),
        "expected_count": expected_count,
        "missing_forecast_count": missing_forecast_count,
        "missing_actual_count": missing_actual_count,
    }
