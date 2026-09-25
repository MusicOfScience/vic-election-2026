import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OLD = ROOT / "data/validation/historical-replays/vic_la_2014-v2-comparators.json"
NEW = ROOT / "data/validation/historical-replays/vic_la_2014-v2-comparators-v2.json"
PRED = ROOT / "data/validation/historical-replays/vic_la_2014-v2-prediction.json"
SPEC = REPO / "metadata/historical-replay-v2-comparator-spec-2014.json"
AUDIT = REPO / "metadata/historical-replay-2014-v2-comparator-defect-audit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_defective_2014_bundle_is_preserved_and_audited_pre_score():
    assert sha(OLD) == "d0178652ddcd922ae8b61cadac40ff6bab296c27f9bcc4be97cd5e34f43e3efd"
    audit = json.loads(AUDIT.read_text())
    assert audit["oldBundleSha256"] == sha(OLD)
    assert audit["outcomesLoaded"] is False
    assert audit["predictionUntouched"] is True
    assert "uniform-swing-baseline and seat-level-model" in audit["defect"]


def test_corrected_bundle_is_pre_outcome_and_references_sealed_prediction():
    bundle = json.loads(NEW.read_text())
    prediction = json.loads(PRED.read_text())
    spec = json.loads(SPEC.read_text())
    assert bundle["outcomesLoaded"] is False
    assert bundle["certifyingPredictionSha256"] == prediction["predictionSha256"]
    assert bundle["certifyingPredictionSha256"] == "7621cd120c9efdd7f891d0d69fbd711b8d5316af632547df6035e3ea096b38b0"
    assert bundle["comparatorSpecSha256"] == sha(SPEC)
    assert spec["outcomesLoaded"] is False
    assert set(bundle["comparators"]) == {
        "uniform-swing-baseline",
        "polling-only",
        "polling-plus-fundamentals",
        "seat-level-model",
        "complete-ensemble",
    }


def test_2014_comparators_are_structurally_distinct():
    comparators = json.loads(NEW.read_text())["comparators"]
    uniform = comparators["uniform-swing-baseline"]["districts"]
    polling = comparators["polling-only"]["districts"]
    fundamentals = comparators["polling-plus-fundamentals"]["districts"]
    seat = comparators["seat-level-model"]["districts"]
    assert len(uniform) == len(polling) == len(fundamentals) == len(seat) == 88
    assert uniform != seat
    assert polling != fundamentals
    assert len({row["districtId"] for row in uniform}) == 88
    assert len({json.dumps(row["winProbabilities"], sort_keys=True) for row in uniform}) > 1
    assert len({json.dumps(row["primaryEstimates"], sort_keys=True) for row in fundamentals}) > 1
    assert comparators["seat-level-model"]["chamberAggregation"] == "independent-seat-marginals"


def test_2014_comparator_contract_forbids_target_outcomes_and_uses_cycle_families():
    bundle = json.loads(NEW.read_text())
    spec = json.loads(SPEC.read_text())
    assert spec["activeFamilies"] == ["ALP", "LIB_NAT", "GRN", "OTH_IND"]
    assert any("2014 Victorian Assembly outcomes" in item for item in bundle["forbiddenDependencies"])
    assert any("2014 Victorian Council outcomes" in item for item in bundle["forbiddenDependencies"])
    assert "vec_2010_2014_redistribution_adjusted_tpp_swing.csv" in " ".join(bundle["forbiddenDependencies"])
    complete = bundle["comparators"]["complete-ensemble"]
    assert complete["predictionPath"].endswith("vic_la_2014-v2-prediction.json")
    assert "districts" not in complete
