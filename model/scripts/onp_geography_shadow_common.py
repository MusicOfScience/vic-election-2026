"""Shared helpers for governed ONP geography shadow experiments."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import vicforecast.forecast_2026 as forecast_module
from vicforecast.forecast_2026 import ASSEMBLY_2022_TARGET, PARTIES


def _canonical_poll_mean(model_root: Path) -> np.ndarray:
    """Read the frozen canonical latent-state mean used by these geography shadows."""
    manifest = json.loads((model_root / "data/processed/experimental_forecast_2026.json").read_text())
    mean = manifest["polling"]["mean"]
    return np.array([float(mean[party]) / 100.0 for party in PARTIES])


def _by_election_boosts(model_root: Path, config: dict, districts: pd.DataFrame) -> np.ndarray:
    boosts = np.zeros((len(districts), len(PARTIES)))
    path = model_root / "data/seed/recent_state_by_elections.json"
    if not path.exists():
        return boosts
    events = json.loads(path.read_text())["events"]
    index = {name: i for i, name in enumerate(districts.district_name)}
    assembly = config["assembly"]
    for event in events:
        if event["district"] not in index:
            continue
        age = (pd.Timestamp(config["election_date"]) - pd.Timestamp(event["date"])).days
        strength = float(assembly["by_election_max_logit_boost"]) * np.exp(
            -age / float(assembly["by_election_decay_days"])
        )
        family = forecast_module._family(event.get("elected_party_raw"))
        boosts[index[event["district"]], PARTIES.index(family)] += strength
    return boosts


def central_weighted_onp_primary(model_root: Path, config: dict, districts: pd.DataFrame, *, onp_offset: float = 0.0) -> float:
    """Evaluate central, shock-free enrolment-weighted ONP primary.

    This reproduces the Assembly model's deterministic local-pattern transform at
    the frozen canonical statewide latent mean. It is used only to calibrate an
    additive ONP intercept so changing the *shape* of geography does not also
    change the central statewide vote level.
    """
    assembly = config["assembly"]
    state = _canonical_poll_mean(model_root)
    baseline_state = ASSEMBLY_2022_TARGET / 100.0
    base = districts.loc[:, PARTIES].to_numpy(float)
    local_pattern = np.log(np.clip(base, .002, None) / baseline_state)
    local_limits = np.array([float(assembly["local_logit_limits"][party]) for party in PARTIES])
    local_pattern = np.clip(local_pattern, -local_limits, local_limits)
    local_pattern[:, 2] = districts.onp_local_log.to_numpy(float) + float(onp_offset)
    greens_limit = float(assembly["greens_local_logit_limit"])
    local_pattern[:, 3] = np.clip(
        local_pattern[:, 3] * float(assembly["greens_local_pattern_multiplier"]),
        -greens_limit,
        greens_limit,
    )
    boosts = _by_election_boosts(model_root, config, districts)
    logits = np.log(np.clip(state, 1e-6, None)) + local_pattern + boosts
    primaries = np.exp(logits - logits.max(axis=1, keepdims=True))
    primaries /= primaries.sum(axis=1, keepdims=True)
    weights = districts.enrolled_electors.to_numpy(float)
    weights /= weights.sum()
    return float(np.sum(weights * primaries[:, 2]))


def conserve_central_onp_primary(model_root: Path, config: dict, candidate: pd.DataFrame, control: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Solve an ONP intercept so candidate and control have equal central vote.

    The spatial ordering/deviations remain unchanged. The solve changes only one
    common additive ONP logit intercept. This is a treatment-isolation device,
    not a production parameter estimate.
    """
    target = central_weighted_onp_primary(model_root, config, control)
    before = central_weighted_onp_primary(model_root, config, candidate)
    low, high = -2.0, 2.0
    low_value = central_weighted_onp_primary(model_root, config, candidate, onp_offset=low)
    high_value = central_weighted_onp_primary(model_root, config, candidate, onp_offset=high)
    if not (low_value <= target <= high_value):
        raise ValueError(
            f"ONP conservation target {target:.6f} not bracketed by {low_value:.6f}..{high_value:.6f}"
        )
    for _ in range(80):
        mid = (low + high) / 2.0
        value = central_weighted_onp_primary(model_root, config, candidate, onp_offset=mid)
        if value < target:
            low = mid
        else:
            high = mid
    offset = (low + high) / 2.0
    out = candidate.copy()
    out["onp_local_log"] = out["onp_local_log"].to_numpy(float) + offset
    after = central_weighted_onp_primary(model_root, config, out)
    return out, {
        "rule": "common additive ONP logit intercept solved at frozen canonical latent mean; central enrolment-weighted ONP primary matched to current geography control",
        "targetCentralWeightedPrimary": target * 100.0,
        "candidateBeforeCalibration": before * 100.0,
        "candidateAfterCalibration": after * 100.0,
        "additiveLogitOffset": float(offset),
        "absoluteResidualPercentagePoints": abs(after - target) * 100.0,
    }
