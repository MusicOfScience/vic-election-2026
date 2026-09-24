"""Leakage-neutral scoring primitives for held-out forecast validation.

These functions accept predictions and scoring-only outcomes. They do not fit
forecast inputs, mutate model state, or decide whether a release gate passes.
Callers must construct predictions using only information available at the
cycle cutoff and keep outcomes in a separate scoring dataset.
"""
from __future__ import annotations

import numpy as np


def _arrays(probability, outcome) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(probability, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if p.shape != y.shape or p.size == 0:
        raise ValueError("probability and outcome must have the same non-empty shape")
    if not np.isfinite(p).all() or not np.isfinite(y).all():
        raise ValueError("probability and outcome must be finite")
    if ((p < 0) | (p > 1)).any() or ((y < 0) | (y > 1)).any():
        raise ValueError("probability and outcome must lie in [0, 1]")
    return p, y


def brier_score(probability, outcome) -> float:
    """Mean squared probability error for binary events."""
    p, y = _arrays(probability, outcome)
    return float(np.mean((p - y) ** 2))


def log_loss(probability, outcome, epsilon: float = 1e-12) -> float:
    """Binary logarithmic loss with explicit finite clipping."""
    p, y = _arrays(probability, outcome)
    if epsilon <= 0 or epsilon >= 0.5:
        raise ValueError("epsilon must be between 0 and 0.5")
    clipped = np.clip(p, epsilon, 1 - epsilon)
    return float(-np.mean(y * np.log(clipped) + (1 - y) * np.log1p(-clipped)))


def reliability_bins(probability, outcome, bins: int = 10) -> list[dict[str, float | int]]:
    """Return non-empty equal-width reliability bins without smoothing."""
    p, y = _arrays(probability, outcome)
    if bins < 2:
        raise ValueError("bins must be at least 2")
    edges = np.linspace(0, 1, bins + 1)
    result = []
    for index in range(bins):
        mask = (p >= edges[index]) & ((p < edges[index + 1]) if index < bins - 1 else (p <= edges[index + 1]))
        if mask.any():
            result.append({
                "bin": index,
                "lower": float(edges[index]),
                "upper": float(edges[index + 1]),
                "count": int(mask.sum()),
                "meanPredicted": float(p[mask].mean()),
                "observedRate": float(y[mask].mean()),
            })
    return result


def calibration_slope_intercept(probability, outcome, epsilon: float = 1e-12) -> tuple[float, float]:
    """Fit the descriptive logit calibration line to held-out predictions.

    This is a scoring diagnostic, not a calibrator to apply to the same data.
    The caller must fit any production calibrator inside the training folds.
    """
    p, y = _arrays(probability, outcome)
    clipped = np.clip(p, epsilon, 1 - epsilon)
    design = np.column_stack([np.ones(p.size), np.log(clipped / (1 - clipped))])
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    intercept, slope = coefficients
    return float(slope), float(intercept)


def interval_coverage(lower, upper, outcome) -> float:
    """Fraction of scoring outcomes contained by a predictive interval."""
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if lo.shape != hi.shape or lo.shape != y.shape or lo.size == 0:
        raise ValueError("interval bounds and outcome must have the same non-empty shape")
    if not np.isfinite(lo).all() or not np.isfinite(hi).all() or not np.isfinite(y).all() or (lo > hi).any():
        raise ValueError("interval bounds and outcome must be finite and ordered")
    return float(np.mean((y >= lo) & (y <= hi)))


def seat_count_absolute_error(predicted, observed) -> float:
    """Absolute error in a chamber seat count."""
    predicted_value = float(predicted)
    observed_value = float(observed)
    if not np.isfinite(predicted_value) or not np.isfinite(observed_value):
        raise ValueError("seat counts must be finite")
    return abs(predicted_value - observed_value)

