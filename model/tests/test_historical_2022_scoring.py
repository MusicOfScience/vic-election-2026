import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PRED = ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json"
BUNDLE = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators-v2.json"
OUTCOMES = ROOT / "data/processed/vec_2022_assembly_final_pairs.csv"
SCORE = ROOT / "data/validation/historical-replays/vic_la_2022-v2-score.json"
MANIFEST = ROOT / "data/validation/historical-replays/vic_la_2022-v2-score-manifest.json"


def sha_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_sealed_prediction_and_comparator_fingerprints_are_exact():
    prediction = json.loads(PRED.read_text())
    bundle = json.loads(BUNDLE.read_text())
    assert prediction["predictionSha256"] == "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
    assert sha_json(prediction["prediction"]) == prediction["predictionSha256"]
    assert bundle["bundleSha256"] == "cd04d597a9016f714f0c1e98d42c4ca66a91ce53a9c72283cb04c1abaea4a748"
    assert sha_json({key: value for key, value in bundle.items() if key != "bundleSha256"}) == bundle["bundleSha256"]
    assert bundle["outcomesLoaded"] is False


def test_assembly_outcome_universe_and_final_pair_availability_are_explicit():
    import csv

    rows = list(csv.DictReader(OUTCOMES.open()))
    assert len(rows) == 87
    assert "narracan" not in {row["district_id"] for row in rows}
    assert sum(row["final_pair_available"] == "True" for row in rows) == 77
    assert sum(row["final_pair_available"] == "False" for row in rows) == 10
    assert all(row["winner_party_family"] for row in rows)


def test_score_manifest_proves_outcome_boundary_and_immutability():
    score = json.loads(SCORE.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["outcomeBoundaryCrossedAfterPredictionAndComparatorVerification"] is True
    assert manifest["forecastRegenerated"] is False
    assert manifest["predictionSha256"] == "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
    assert manifest["comparatorBundleSha256"] == "cd04d597a9016f714f0c1e98d42c4ca66a91ce53a9c72283cb04c1abaea4a748"
    assert manifest["assemblyOutcomeSha256"] == hashlib.sha256(OUTCOMES.read_bytes()).hexdigest()
    assert score["outcomesLoaded"] is True
    assert score["thresholds"]["completeBacktest"] == "unavailable-until-four-cycles"


def test_defective_comparator_bundle_is_not_the_scored_bundle():
    score = json.loads(SCORE.read_text())
    assert score["comparatorBundleSha256"] != "1492dc93eb8db7b95055d0473bc0c7e9c0d1029225d01a3eb23c110407a63dd4"
    assert score["comparatorBundleSha256"] == "cd04d597a9016f714f0c1e98d42c4ca66a91ce53a9c72283cb04c1abaea4a748"
