import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_official_2018_final_pair_artefact_covers_all_districts_and_non_major_pairs():
    rows = list(csv.DictReader((ROOT / "data/processed/vec_2018_assembly_final_pairs.csv").open()))
    assert len(rows) == 88
    assert len({row["district_id"] for row in rows}) == 88
    assert all(row["elected_candidate"] in {row["finalist_1_candidate"], row["finalist_2_candidate"]} for row in rows)
    assert all(
        int(row["finalist_1_votes"]) > int(row["finalist_2_votes"])
        if row["elected_candidate"] == row["finalist_1_candidate"]
        else int(row["finalist_2_votes"]) > int(row["finalist_1_votes"])
        for row in rows
    )
    assert all(abs(float(row["finalist_1_percent"]) + float(row["finalist_2_percent"]) - 100) <= 0.25 for row in rows)
    assert any("Greens" in row["final_pair_family_label"] for row in rows)
    assert any(row["winner_party_family"] not in {"ALP", "Coalition"} for row in rows)


def test_frozen_prediction_hash_is_unchanged_and_score_is_separate():
    manifest = json.loads((ROOT / "data/validation/historical-replays/vic_la_2018-prediction.json").read_text())
    assert manifest["predictionSha256"] == "424552f6ad8fe362044543bb966d2642e34267c32a89b44c47ff390037a4c115"
    score = ROOT / "data/validation/historical-replays/vic_la_2018-score.json"
    assert score.exists()
    assert json.loads(score.read_text())["predictionSha256"] == manifest["predictionSha256"]
