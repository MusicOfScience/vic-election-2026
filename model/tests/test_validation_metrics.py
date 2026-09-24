import numpy as np
import pytest

from vicforecast.validation_metrics import (
    brier_score,
    calibration_slope_intercept,
    interval_coverage,
    log_loss,
    reliability_bins,
    seat_count_absolute_error,
)


def test_binary_scores_and_calibration_are_deterministic():
    probability = np.array([0.1, 0.4, 0.8, 0.9])
    outcome = np.array([0, 0, 1, 1])
    assert np.isclose(brier_score(probability, outcome), 0.055)
    assert np.isclose(log_loss(probability, outcome), 0.2361726, atol=1e-6)
    slope, intercept = calibration_slope_intercept(probability, outcome)
    assert np.isfinite(slope)
    assert np.isfinite(intercept)


def test_reliability_and_interval_metrics_keep_empty_bins_out():
    probability = np.array([0.1, 0.2, 0.8, 0.9])
    outcome = np.array([0, 0, 1, 0])
    bins = reliability_bins(probability, outcome, bins=4)
    assert sum(item["count"] for item in bins) == 4
    assert len(bins) == 2
    assert np.isclose(interval_coverage([0, 0.3, 0.7], [0.2, 0.7, 1], [0.1, 0.5, 0.6]), 2 / 3)


def test_scoring_helpers_fail_closed_on_invalid_inputs():
    with pytest.raises(ValueError):
        brier_score([0.2], [1, 0])
    with pytest.raises(ValueError):
        log_loss([1.1], [1])
    with pytest.raises(ValueError):
        interval_coverage([0.5], [0.4], [0.5])
    assert seat_count_absolute_error(39, 44) == 5
