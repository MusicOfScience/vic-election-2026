import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OLD = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators.json"
NEW = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators-v2.json"
PRED = ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json"
SPEC = REPO / "metadata/historical-replay-v2-comparator-spec.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_defective_pre_score_bundle_is_preserved():
    old = json.loads(OLD.read_text())
    assert old["bundleSha256"] == "1492dc93eb8db7b95055d0473bc0c7e9c0d1029225d01a3eb23c110407a63dd4"
    assert old["outcomesLoaded"] is False


def test_new_bundle_references_immutable_prediction_and_spec():
    bundle = json.loads(NEW.read_text())
    prediction = json.loads(PRED.read_text())
    spec = json.loads(SPEC.read_text())
    assert bundle["schemaVersion"] == 2
    assert bundle["outcomesLoaded"] is False
    assert bundle["certifyingPredictionSha256"] == "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
    assert digest(json.dumps(prediction["prediction"], sort_keys=True, separators=(",", ":")).encode()) == bundle["certifyingPredictionSha256"]
    assert bundle["comparatorSpecSha256"] == digest(SPEC.read_bytes())
    assert set(bundle["comparators"]) == {"uniform-swing-baseline", "polling-only", "polling-plus-fundamentals", "seat-level-model", "complete-ensemble"}
    assert spec["outcomesLoaded"] is False


def test_simple_comparators_have_distinct_scopes_and_local_variation():
    comparators = json.loads(NEW.read_text())["comparators"]
    uniform = comparators["uniform-swing-baseline"]
    polling = comparators["polling-only"]
    fundamentals = comparators["polling-plus-fundamentals"]
    seat = comparators["seat-level-model"]
    u_rows = uniform["assemblyDistricts"]
    p_rows = polling["assemblyDistricts"]
    f_rows = fundamentals["assemblyDistricts"]
    s_rows = seat["assemblyDistricts"]
    assert len(u_rows) == len(p_rows) == len(f_rows) == len(s_rows) == 87
    assert len({tuple(row["primaryEstimates"].items()) for row in u_rows}) > 1
    assert len({tuple(row["primaryEstimates"].items()) for row in f_rows}) > 1
    assert {tuple(row["primaryEstimates"].items()) for row in p_rows} != {tuple(row["primaryEstimates"].items()) for row in f_rows}
    assert {tuple(row["primaryEstimates"].items()) for row in s_rows} != {tuple(row["primaryEstimates"].items()) for row in f_rows}
    assert seat["chamberAggregation"] == "independent-seat-marginals"
    assert "model/data/processed/vec_2018_estimated_2022_boundary_2cp.csv" in uniform["allowedInputs"]
    assert "AEC district surface" not in uniform["allowedInputs"]
    assert "AEC district surface" in polling["forbiddenInputs"]


def test_complete_is_reference_only_and_no_outcomes_are_loaded():
    complete = json.loads(NEW.read_text())["comparators"]["complete-ensemble"]
    assert complete["reference"]["frozenPrediction"] is True
    assert complete["reference"]["valuesCopied"] is False
    assert complete["reference"]["predictionSha256"] == "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
    bundle = json.loads(NEW.read_text())
    assert bundle["outcomesLoaded"] is False
    assert not (ROOT / "data/validation/historical-replays/vic_la_2022-score.json").exists()
