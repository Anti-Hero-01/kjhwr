from app.services.metrics import calculate_metrics


def test_metrics_ignore_missing_and_zero_actuals():
    result = calculate_metrics([
        {"forecast_mw": 10, "actual_mw": 8},
        {"forecast_mw": 4, "actual_mw": 0},
        {"forecast_mw": 2, "actual_mw": None},
    ])
    assert result["sample_count"] == 2
    assert result["mape_percent"] == 25.0
    assert result["bias_mw"] == 3.0
    assert result["nmae_percent"] == 75.0


def test_empty_metrics():
    assert calculate_metrics([{"forecast_mw": 2, "actual_mw": None}])["mae_mw"] is None


def test_invalid_forecast_pairs_are_skipped():
    result = calculate_metrics([
        {"forecast_mw": "not-a-number", "actual_mw": 10},
        {"forecast_mw": None, "actual_mw": 10},
        {"forecast_mw": float("nan"), "actual_mw": 10},
        {"forecast_mw": 12, "actual_mw": 10},
    ])
    assert result["sample_count"] == 1


def test_signed_bias_is_not_absolute_error():
    result = calculate_metrics([
        {"forecast_mw": 110, "actual_mw": 100},
        {"forecast_mw": 80, "actual_mw": 100},
    ])
    assert result["mae_mw"] == 15
    assert result["bias_mw"] == -5
