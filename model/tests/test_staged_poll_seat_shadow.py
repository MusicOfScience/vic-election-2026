from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model/scripts"))

from run_staged_poll_seat_shadow import SHADOW_INPUT_PATHS, _scenario_registry, build_impact_report  # noqa: E402
from vicforecast.forecast_2026 import PARTIES  # noqa: E402


def test_shadow_fingerprint_includes_the_pinned_numerical_stack():
    constraints = (ROOT / "model/constraints.txt").read_text()
    assert "numpy==2.3.5" in constraints
    assert "pandas==2.2.3" in constraints
    assert "pyyaml==6.0.3" in constraints
    assert "model/constraints.txt" in SHADOW_INPUT_PATHS


def _chamber(hung: float = 0.7) -> pd.DataFrame:
    return pd.DataFrame([
        {"party": party, "mean": 10.0 + i, "median": 10.0 + i, "lower80": 8.0, "upper80": 14.0,
         "majority_probability": 0.1 if i == 0 else 0.0, "hung_probability": hung,
         "major_party_no_control_probability": 0.9}
        for i, party in enumerate(PARTIES)
    ])


def _districts(delta: float = 0.0) -> pd.DataFrame:
    row = {"district_id": "example", "district_name": "Example", "favoured_party": "ALP"}
    for party in PARTIES:
        row[f"win_{party.lower()}"] = 0.1
    row["win_alp"] = 0.6 - delta
    row["win_lib_nat"] = 0.25 + delta
    row["favoured_probability"] = max(row[f"win_{party.lower()}"] for party in PARTIES)
    return pd.DataFrame([row])


def _regions(delta: float = 0.0) -> pd.DataFrame:
    row = {"region_id": "example", "region_name": "Example"}
    for party in PARTIES:
        row[f"seats_{party.lower()}"] = 1
        row[f"at_least_one_{party.lower()}"] = 0.5
    row["at_least_one_lib_nat"] += delta
    return pd.DataFrame([row])


def _forecast(*, poll_count: int, poll_shift: float = 0.0, district_shift: float = 0.0):
    poll_mean = {party: 20.0 for party in PARTIES}
    poll_mean["LIB_NAT"] += poll_shift
    poll_mean["ALP"] -= poll_shift
    chamber = _chamber()
    council = _chamber()
    return SimpleNamespace(
        poll_state=SimpleNamespace(mean=poll_mean, poll_count=poll_count),
        chamber=chamber,
        districts=_districts(district_shift),
        council=council,
        council_regions=_regions(district_shift),
    )


def test_scenario_registry_is_in_memory_and_adds_only_the_two_staged_polls():
    event_path = ROOT / "model/data/processed/poll_events_seed.csv"
    estimate_path = ROOT / "model/data/processed/poll_estimates_seed.csv"
    canonical_events = pd.read_csv(event_path)
    canonical_estimates = pd.read_csv(estimate_path)

    scenario_events, scenario_estimates = _scenario_registry(ROOT)
    staged_ids = {"demosau_2026-08", "resolve_strategic_2026-08"}

    assert len(scenario_events) == len(canonical_events) + 2
    assert set(scenario_events.poll_id) - set(canonical_events.poll_id) == staged_ids
    assert scenario_events.loc[scenario_events.poll_id.isin(staged_ids), "model_eligible"].all()
    assert len(scenario_estimates) > len(canonical_estimates)
    assert pd.read_csv(event_path).equals(canonical_events)
    assert pd.read_csv(estimate_path).equals(canonical_estimates)


def test_impact_report_is_counterfactual_and_exposes_probability_shifts():
    canonical = _forecast(poll_count=12)
    shadow = _forecast(poll_count=14, poll_shift=0.5, district_shift=0.08)
    report = build_impact_report(canonical, shadow, simulations=100, seed=42, as_of="2026-08-26")

    assert report["canonicalModelInputsChanged"] is False
    assert report["canonicalForecastArtifactsWritten"] is False
    assert report["scenarioEvidencePromoted"] is False
    assert report["commonRandomNumbers"] is True
    assert report["polling"]["canonicalPollCount"] == 12
    assert report["polling"]["shadowPollCount"] == 14
    assert report["polling"]["deltaMean"]["LIB_NAT"] == 0.5
    assert report["assembly"]["districts"]["seatsWithFivePointOrLargerProbabilityShift"] == 1
    assert report["council"]["regions"]["largestProbabilityShifts"][0]["regionName"] == "Example"
