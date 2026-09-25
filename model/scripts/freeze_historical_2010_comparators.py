"""Freeze the distinct pre-outcome 2010 comparator bundle."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CYCLE = "vic_la_2010"
FAMILIES = ["ALP", "LIB_NAT", "GRN", "OTH_IND"]
SPEC = ROOT / "metadata/historical-replay-v2-comparator-spec-2010.json"
PRED = ROOT / "model/data/validation/historical-replays/vic_la_2010-v2-prediction.json"
MASK = ROOT / "model/data/validation/historical-replay-2010-ballot-mask.csv"
LOCAL = ROOT / "model/data/validation/historical-replay-2010-local-inputs.csv"
BASELINE = ROOT / "model/data/validation/historical-replay-2010-assembly-notional-baseline.csv"
POLLS = ROOT / "model/data/validation/historical-replay-2010-poll-observations.json"
OUT = ROOT / "model/data/validation/historical-replays/vic_la_2010-v2-comparators-v2.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def normalise(values: dict[str, float], active: set[str]) -> dict[str, float]:
    values = {family: max(0.0, float(values.get(family, 0.0))) if family in active else 0.0 for family in FAMILIES}
    total = sum(values.values())
    if total <= 0:
        raise ValueError("ballot mask removed every family")
    return {family: values[family] / total * 100.0 for family in FAMILIES}


def probabilities(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    return {family: values[family] / total for family in FAMILIES}


def pair(values: dict[str, float]) -> str:
    ranked = sorted(((value, family) for family, value in values.items() if value > 0), reverse=True)
    return "-".join(sorted([ranked[0][1], ranked[1][1]])) if len(ranked) > 1 else ranked[0][1]


def poll_state() -> dict[str, float]:
    rows = [row for row in json.loads(POLLS.read_text())["observations"] if row.get("cycleId") == CYCLE and row.get("replayEligible")]
    if len(rows) < 3 or len({row["sourceFamily"] for row in rows}) < 2:
        raise ValueError("2010 poll rule is not satisfied")
    weighted = []
    weights = []
    for row in rows:
        vector = {family: float(row["primaryShares"][family]) for family in FAMILIES}
        weighted.append(vector)
        age = max(0, ("2010-11-26" > row["evidenceAvailableByDate"]) and (0))
        # Evidence dates precede the cutoff; normalise the same fixed 45-day decay.
        from datetime import date
        age = max(0, (date.fromisoformat("2010-11-26") - date.fromisoformat(row["evidenceAvailableByDate"])).days)
        weights.append(float(row.get("sampleSize", 500)) * 0.5 ** (age / 45.0))
    return {family: sum(vector[family] * weight for vector, weight in zip(weighted, weights)) / sum(weights) for family in FAMILIES}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    if not PRED.exists() or not MASK.exists() or not LOCAL.exists() or not BASELINE.exists():
        raise RuntimeError("2010 comparator inputs are incomplete")
    prediction = json.loads(PRED.read_text())
    prediction_hash = prediction.get("predictionSha256")
    sealed = prediction.get("prediction", {})
    if not prediction_hash or canonical_sha(sealed) != prediction_hash or prediction.get("cycleId") != CYCLE or prediction.get("modelVersion") != "historical_replay_v2" or sealed.get("certificationStatus") != "held-out-certifying-prediction-frozen" or prediction.get("targetOutcomeLoaded") is not False or prediction.get("outcomesLoaded") is not False or sealed.get("targetOutcomeLoaded") is not False or sealed.get("outcomesLoaded") is not False:
        raise RuntimeError("2010 prediction is not sealed pre-outcome")
    spec = json.loads(SPEC.read_text())
    if spec["cycleId"] != CYCLE or spec["outcomesLoaded"] is not False:
        raise RuntimeError("2010 comparator spec is not pre-outcome")
    poll = poll_state()
    mask = {row["district_id"]: row for row in read_rows(MASK)}
    local = {row["district_id"]: row for row in read_rows(LOCAL)}
    baseline = {row["district_id"]: row for row in read_rows(BASELINE)}
    if len(mask) != 88 or set(mask) != set(local) or set(mask) != set(baseline):
        raise ValueError("2010 comparator sources must reconcile to 88 districts")
    major = poll["ALP"] + poll["LIB_NAT"]
    tpp = poll["ALP"] / major
    uniform, polling, fundamentals, seat = [], [], [], []
    for district_id in sorted(mask):
        ballot = set(mask[district_id]["ballot_active_families"].split(";"))
        row = baseline[district_id]
        margin = float(row["notional_margin_pp"]) / 100.0
        holder = row["notional_holder_family"]
        baseline_alp = 0.5 + (margin if holder == "ALP" else -margin if holder == "LIB_NAT" else 0.0)
        uniform_values = normalise({"ALP": major * baseline_alp + (major * (tpp - 0.5)), "LIB_NAT": major * (1 - baseline_alp) - (major * (tpp - 0.5)), "GRN": poll["GRN"], "OTH_IND": poll["OTH_IND"]}, ballot)
        uniform.append({"districtId": district_id, "districtName": row["district_name"], "winProbabilities": probabilities(uniform_values), "method": "uniform-swing-baseline", "metricAvailability": ["winner", "binary-ALP-event"]})
        polling_values = normalise(poll, ballot)
        polling.append({"districtId": district_id, "districtName": row["district_name"], "primaryEstimates": polling_values, "winProbabilities": probabilities(polling_values), "method": "polling-only", "metricAvailability": ["statewide-primary", "district-primary", "winner"]})
        local_values = normalise({family: float(local[district_id][f"prior_{family.lower()}_share"]) * 100 for family in FAMILIES}, ballot)
        fundamentals_values = normalise({family: 0.65 * polling_values[family] + 0.35 * local_values[family] for family in FAMILIES}, ballot)
        fundamentals.append({"districtId": district_id, "districtName": row["district_name"], "primaryEstimates": fundamentals_values, "winProbabilities": probabilities(fundamentals_values), "method": "polling-plus-fundamentals", "metricAvailability": ["district-primary", "winner"]})
        # A fixed hash-derived perturbation is independent of target outcomes.
        perturb = (int(hashlib.sha256(district_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF - 0.5) * 1.6
        seat_values = dict(fundamentals_values)
        if "ALP" in ballot and "LIB_NAT" in ballot:
            seat_values["ALP"] = max(0.0, seat_values["ALP"] + perturb)
            seat_values["LIB_NAT"] = max(0.0, seat_values["LIB_NAT"] - perturb)
        seat_values = normalise(seat_values, ballot)
        seat.append({"districtId": district_id, "districtName": row["district_name"], "primaryEstimates": seat_values, "winProbabilities": probabilities(seat_values), "likelyFinalPair": pair(seat_values), "method": "seat-level-model", "uncertaintyRule": "fixed-pre-score-independent-seat-perturbation", "metricAvailability": ["district-primary", "winner", "seat-count"]})
    arrays = [json.dumps(rows, sort_keys=True) for rows in (uniform, polling, fundamentals, seat)]
    if arrays[0] == arrays[1] or arrays[0] == arrays[2] or arrays[0] == arrays[3] or arrays[1] == arrays[2] or arrays[2] == arrays[3]:
        raise RuntimeError("2010 comparator implementations are aliased")
    complete = {"reference": {"predictionPath": str(PRED.relative_to(ROOT)), "predictionSha256": prediction_hash, "frozenPrediction": True, "valuesCopied": False}, "metricAvailability": spec["comparators"]["complete-ensemble"]["metricAvailability"]}
    bundle = {"schemaVersion": 2, "modelVersion": "historical_replay_v2", "cycleId": CYCLE, "informationCutoff": "2010-11-26", "outcomesLoaded": False, "comparatorSpecPath": str(SPEC.relative_to(ROOT)), "comparatorSpecSha256": sha(SPEC), "certifyingPredictionPath": str(PRED.relative_to(ROOT)), "certifyingPredictionSha256": prediction_hash, "forbiddenDependencies": spec["forbiddenInputs"], "comparators": {"uniform-swing-baseline": {"assemblyDistricts": uniform, "metricAvailability": spec["comparators"]["uniform-swing-baseline"]["metricAvailability"]}, "polling-only": {"assemblyDistricts": polling, "metricAvailability": spec["comparators"]["polling-only"]["metricAvailability"]}, "polling-plus-fundamentals": {"assemblyDistricts": fundamentals, "metricAvailability": spec["comparators"]["polling-plus-fundamentals"]["metricAvailability"]}, "seat-level-model": {"assemblyDistricts": seat, "chamberAggregation": "independent-seat-marginals", "metricAvailability": spec["comparators"]["seat-level-model"]["metricAvailability"]}, "complete-ensemble": complete}}
    bundle["bundleSha256"] = canonical_sha(bundle)
    OUT.write_text(json.dumps(bundle, indent=2) + "\n")
    print(json.dumps({"comparatorPath": str(OUT.relative_to(ROOT)), "comparatorSha256": bundle["bundleSha256"], "outcomesLoaded": False}, indent=2))


if __name__ == "__main__":
    main()
