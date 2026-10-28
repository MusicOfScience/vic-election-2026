import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADJUDICATION = ROOT / "metadata/candidate-resolution-preference-uncertainty-adjudication-2026-10-29.json"
FREEZE = ROOT / "metadata/candidate-resolution-preference-concentration-freeze-2026-10-29.json"


def test_preference_uncertainty_result_preserves_governance_boundary():
    result = json.loads(ADJUDICATION.read_text(encoding="utf-8"))

    assert result["researchSupportGate"]["result"] == "pass"
    assert result["productionCandidateGate"]["result"] == "fail"
    assert result["adjudication"]["historicallySupportedUncertaintyCorrection"] is True
    assert result["adjudication"]["globalConcentration4ProductionReady"] is False
    assert result["adjudication"]["separateGoverned2026ShadowAuthorised"] is False
    assert result["adjudication"]["productionPromotionAuthorised"] is False
    assert result["adjudication"]["canonicalProdModified"] is False


def test_concentration_four_was_frozen_before_heldout_score():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))

    assert freeze["status"] == "frozen-before-heldout-2018-2022-score"
    assert freeze["guardrails"]["heldout2022OutcomeScoredBeforeFreeze"] is False
    for allocation in ("equal", "proportional"):
        assert freeze["selections"][allocation]["2018"]["concentration"] == 4.0
        assert freeze["selections"][allocation]["2022"]["concentration"] == 4.0


def test_lower_grid_boundary_is_not_reinterpreted_as_production_optimum():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    result = json.loads(ADJUDICATION.read_text(encoding="utf-8"))

    selected = [
        freeze["selections"][allocation][year]["concentration"]
        for allocation in ("equal", "proportional")
        for year in ("2018", "2022")
    ]
    assert selected == [4.0, 4.0, 4.0, 4.0]
    assert min(freeze["grid"]) == 4
    assert "lower grid boundary" in freeze["boundaryObservation"]
    assert result["adjudication"]["extendGridBelow4PostHoc"] is False
    assert result["adjudication"]["globalConcentration4ProductionReady"] is False
