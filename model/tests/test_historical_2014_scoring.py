import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PRED = ROOT / "data/validation/historical-replays/vic_la_2014-v2-prediction.json"
BUNDLE = ROOT / "data/validation/historical-replays/vic_la_2014-v2-comparators-v2.json"
OLD = ROOT / "data/validation/historical-replays/vic_la_2014-v2-comparators.json"
SPEC = REPO / "metadata/historical-replay-v2-comparator-spec-2014.json"
OUTCOMES = ROOT / "data/processed/vec_2014_assembly_final_pairs.csv"
SCORE = ROOT / "data/validation/historical-replays/vic_la_2014-v2-score.json"
MANIFEST = ROOT / "data/validation/historical-replays/vic_la_2014-v2-score-manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sealed_boundary_fingerprints_and_old_bundle_protection():
    prediction = json.loads(PRED.read_text())
    bundle = json.loads(BUNDLE.read_text())
    assert hashlib.sha256(json.dumps(prediction["prediction"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == prediction["predictionSha256"] == "7621cd120c9efdd7f891d0d69fbd711b8d5316af632547df6035e3ea096b38b0"
    assert sha(BUNDLE) == "4d706fa0dc0b49b5cd6bf281550914594663da4d31d4c6613be17dc87daa1ccb"
    assert sha(OLD) == "d0178652ddcd922ae8b61cadac40ff6bab296c27f9bcc4be97cd5e34f43e3efd"
    assert sha(SPEC) == "cc217989f7981389cc0669969ceb78b7d71a83bb553f422457152106e19b621f"
    assert bundle["comparatorSpecSha256"] == sha(SPEC)
    assert bundle["outcomesLoaded"] is False


def test_official_2014_assembly_outcomes_have_88_rows_and_actual_final_pair_semantics():
    rows = list(csv.DictReader(OUTCOMES.open()))
    assert len(rows) == 88
    assert len({row["district_id"] for row in rows}) == 88
    assert sum(row["final_pair_available"] == "True" for row in rows) == 45
    assert sum(row["final_pair_available"] == "False" for row in rows) == 43
    allowed = {"ALP", "Coalition", "Greens", "Other/Independent"}
    assert {row["winner_party_family"] for row in rows} <= allowed
    for row in rows:
        if row["final_pair_available"] == "True":
            assert row["elected_candidate"] in {row["finalist_1_candidate"], row["finalist_2_candidate"]}
            assert abs(float(row["finalist_1_percent"]) + float(row["finalist_2_percent"]) - 100) <= 0.25
        else:
            assert row["final_pair_selection_rule"] == "not-available-on-official-early-majority-page"


def test_score_is_four_family_and_outcome_boundary_is_recorded():
    score = json.loads(SCORE.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert score["outcomesLoaded"] is True
    assert score["assembly"]["districtCount"] == 88
    assert score["assembly"]["finalPair"]["availableDistricts"] == 45
    assert set(score["assembly"]["winner"].keys()) == {"accuracy", "multiclassBrier", "multiclassLogLoss", "alpEventBrier", "alpEventLogLoss"}
    assert sum(score["council"]["actualSeats"].values()) == 40
    assert score["council"]["regionalPrimaryMetric"]["status"] == "unavailable"
    assert manifest["outcomeBoundaryCrossedAfterPredictionAndComparatorVerification"] is True
    assert manifest["forecastRegenerated"] is False
    assert manifest["predictionSha256"] == "7621cd120c9efdd7f891d0d69fbd711b8d5316af632547df6035e3ea096b38b0"
    assert manifest["comparatorBundleSha256"] == "4d706fa0dc0b49b5cd6bf281550914594663da4d31d4c6613be17dc87daa1ccb"


def test_scoring_script_has_no_generation_dependency():
    source = (ROOT / "scripts/score_frozen_historical_2014_v2.py").read_text()
    assert "freeze_historical_2014_comparators" not in source
    assert "run_historical_forecast" not in source
