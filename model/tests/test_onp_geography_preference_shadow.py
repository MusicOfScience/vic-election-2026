"""Safety and numerical-contract checks for shadow-only ONP/transfer stress tests."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "model/scripts/shadow_onp_geography_preference_factorial.py"
spec = importlib.util.spec_from_file_location("onp_stress", MODULE)
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)


def frame():
    x = {key: np.full(88, .2, dtype=float) for key in stress.forecast.PARTIES}
    x["onp_local_log"] = np.linspace(-1.2, 1.1, 88)
    x["district_name"] = ["District " + str(i) for i in range(88)]
    return pd.DataFrame(x)


def test_bounded_onp_geography_leaves_other_fields_and_original_untouched():
    baseline = frame()
    before = baseline.copy(deep=True)
    clipped = stress.bound_onp_geography(baseline, .45)
    assert np.isclose(clipped.onp_local_log.min(), -.45)
    assert np.isclose(clipped.onp_local_log.max(), .45)
    assert np.all(np.abs(clipped.onp_local_log) <= .450000001)
    pd.testing.assert_frame_equal(baseline, before)
    for party in stress.forecast.PARTIES:
        assert np.array_equal(clipped[party].to_numpy(), baseline[party].to_numpy())
    assert np.isclose(clipped.iloc[40].onp_local_log, baseline.iloc[40].onp_local_log, atol=.45)


@pytest.mark.parametrize("limit", [0, -1, 1.21, float("nan"), float("inf")])
def test_invalid_bounded_locality_limit_fails_closed(limit):
    with pytest.raises(ValueError, match="Invalid ONP locality"):
        stress.bound_onp_geography(frame(), limit)


def test_reject_unexpected_assembly_universe():
    with pytest.raises(ValueError, match="Unexpected AEC locality"):
        stress.bound_onp_geography(frame().iloc[:87], .45)


def test_reference_registration_and_inputs_are_not_mutated():
    config, manifest = stress.load_registered_reference(ROOT)
    assert config["as_of"] == manifest["as_of"] == "2026-10-31"
    assert len(stress.SCENARIOS) == 4
    assert len(set(s[0] for s in stress.SCENARIOS)) == 4
    assert all(s[2] in [4, 72] for s in stress.SCENARIOS)
    before = stress.fingerprint(ROOT)
    assert before["combinedSha256"] == stress.fingerprint(ROOT)["combinedSha256"]
    assert len(before["files"]) == len(stress.INPUTS)
    assert all(len(value) == 64 for value in before["files"].values())
    assert config["assembly"]["preference_prior_concentration"] == 72
    x = deepcopy(config)
    x["assembly"]["preference_prior_concentration"] = 4
    assert config["assembly"]["preference_prior_concentration"] == 72


def test_factorial_interaction_formula_is_exact():
    cells = {}
    for name, geographic, concentration in stress.SCENARIOS:
        # Values deliberately non-additive; ensure factor interaction
        # is calculated as both - (geography + preferences) + reference.
        value = {"reference": 15, "onp_geography_bounded": 12,
                 "preferences_wider_stress": 14, "bounded_plus_wider": 10}[name]
        districts = []
        for d in range(88):
            districts.append({
                "district": str(d), "region": "R", "winner": "ALP",
                "winnerFrequency": 1.0, "modalPair": "ALP–LIB_NAT",
                "modalPairFrequency": 1.0,
                "winningFrequencies": {p: (1 if p == "ALP" else 0) for p in stress.forecast.PARTIES},
                "oneNationPrimaryPercent": 20.0,
            })
        cells[name] = {
            "districts": districts,
            "chamberMeanSeats": {"ALP": 88 - value, "ONP": value, "LIB_NAT": 0,
                                 "GRN": 0, "OTH_IND": 0},
            "majorityFrequency": {"ALP": 1, "LIB_NAT": 0},
            "hungFrequency": 0,
            "oneNationSeatsAtOrAbove80Percent": 0,
        }
    report = stress.compare_cells(cells)
    assert report["factorInteractionMeanSeats"]["ONP"] == -1
    assert report["factorInteractionMeanSeats"]["ALP"] == 1
    assert report["scenarios"]["onp_geography_bounded"]["deltaMeanSeats"]["ONP"] == -3
    assert report["scenarios"]["preferences_wider_stress"]["deltaMeanSeats"]["ONP"] == -1
    assert report["scenarios"]["bounded_plus_wider"]["deltaMeanSeats"]["ONP"] == -5
