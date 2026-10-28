from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "model/scripts/score_candidate_resolved_irv_historical.py"
SPEC = importlib.util.spec_from_file_location("candidate_resolution_irv_score", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_oth_destination_allocation_rules_are_frozen_and_normalised():
    votes = np.asarray([0.0, 0.0, 0.0, 0.0, 0.02, 0.08], dtype=float)
    equal = MODULE.split_oth_mass([4, 5], votes, "equal")
    proportional = MODULE.split_oth_mass([4, 5], votes, "proportional")

    np.testing.assert_allclose(equal, [0.5, 0.5])
    np.testing.assert_allclose(proportional, [0.2, 0.8])
    assert np.isclose(equal.sum(), 1.0)
    assert np.isclose(proportional.sum(), 1.0)


def test_candidate_resolved_counter_exercises_oth_to_oth_transfer():
    # Four named family nodes plus two actual OTH candidates.  The first OTH
    # candidate is deliberately the lowest tally and must be eliminated while
    # the second OTH candidate is still continuing.
    primary = np.asarray([0.38, 0.31, 0.12, 0.10, 0.02, 0.07], dtype=float)
    node_families = np.asarray([0, 1, 2, 3, 4, 4], dtype=int)
    node_labels = ["ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND::a", "OTH_IND::b"]
    preference = np.asarray(MODULE.PREFERENCE_PRIOR, dtype=float)

    winner, pair, exact_pair, oth_steps = MODULE.count_r1(
        primary,
        node_families,
        node_labels,
        preference,
        q_oth=0.36,
        allocation="equal",
    )

    assert winner in range(len(MODULE.PARTIES))
    assert len(pair) == 2
    assert len(exact_pair) == 2
    assert oth_steps >= 1


def test_machine_adjudication_preserves_research_only_boundary_and_adverse_result():
    path = ROOT / "metadata/candidate-resolution-irv-adjudication-2026-10-29.json"
    adjudication = json.loads(path.read_text(encoding="utf-8"))

    assert adjudication["adjudication"] == "historically-supported-architecture-only"
    assert adjudication["canonicalForecastChanged"] is False
    assert adjudication["productionPromotion"] == "rejected-deferred"
    assert adjudication["decisions"]["promoteR1ToProduction"] is False
    assert adjudication["decisions"]["run2026R1ShadowInThisPr"] is False
    assert adjudication["r1Equal"]["frozenSupportChecks"]["allMetricChecksPassed"] is True
    assert adjudication["r1ProportionalSensitivity"]["frozenSupportChecks"]["allMetricChecksPassed"] is True

    # The final-pair architecture passes, but winner log loss is genuinely
    # worse and must remain visible in the durable adjudication.
    assert (
        adjudication["r1Equal"]["matched2014To2022"]["winnerMeanLogLoss"]
        > adjudication["r0"]["matched2014To2022"]["winnerMeanLogLoss"]
    )
    assert adjudication["r1Equal"]["matched2014To2022"]["phantomOthModalPairErrors"] == 0
    assert adjudication["r0"]["matched2014To2022"]["phantomOthModalPairErrors"] == 12
