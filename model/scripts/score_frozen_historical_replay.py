#!/usr/bin/env python3
"""Score the committed 2018 prediction without invoking forecast generation."""
from __future__ import annotations
import csv, hashlib, json, subprocess
from pathlib import Path
import numpy as np
from vicforecast.validation_metrics import brier_score, log_loss, calibration_slope_intercept, reliability_bins

ROOT = Path(__file__).resolve().parents[2]
PREDICTION = ROOT / "model/data/validation/historical-replays/vic_la_2018-prediction.json"
OUTCOMES = ROOT / "model/data/processed/vec_2018_assembly_final_pairs.csv"
CRITERIA = ROOT / "metadata/historical-validation-acceptance-criteria.json"
EXPECTED = "424552f6ad8fe362044543bb966d2642e34267c32a89b44c47ff390037a4c115"

def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canon(value: str) -> str: return {"Coalition":"LIB_NAT", "Greens":"GRN", "Other/Independent":"OTH_IND"}.get(value, value)

def main() -> None:
    prediction_bytes = PREDICTION.read_bytes()
    manifest = json.loads(prediction_bytes)
    prediction = manifest["prediction"]
    canonical = json.dumps(prediction, sort_keys=True, separators=(",", ":")).encode()
    prediction_sha = hashlib.sha256(canonical).hexdigest()
    if prediction_sha != EXPECTED or prediction_sha != manifest["predictionSha256"]: raise ValueError("frozen 2018 prediction hash mismatch")
    rows = list(csv.DictReader(OUTCOMES.open()))
    if len(rows) != 88 or len({row["district_id"] for row in rows}) != 88: raise ValueError("2018 scoring artefact must contain 88 unique districts")
    by_id = {row["district_id"]: row for row in rows}
    districts = prediction["assemblyDistricts"]
    if {row["districtId"] for row in districts} != set(by_id): raise ValueError("prediction and scoring districts differ")
    actual_alp = np.array([int(by_id[row["districtId"]]["alp_won"]) for row in districts])
    pred_alp = np.array([row["winProbabilities"]["ALP"] for row in districts])
    winner_accuracy = float(np.mean([row["favouredParty"] == canon(by_id[row["districtId"]]["winner_party_family"]) for row in districts]))
    pair_accuracy = float(np.mean([set(row["likelyFinalPair"].split("-")) == {canon(x) for x in by_id[row["districtId"]]["final_pair_family_label"].split("-")} for row in districts]))
    primary_errors = []
    baseline_alp = {}
    with (ROOT / "model/data/processed/vec_2018_assembly_family_primaries.csv").open() as handle:
        primary = list(csv.DictReader(handle))
    for district in districts:
        values = {p: 0.0 for p in prediction["activeFamilies"]}; total = 0
        for row in primary:
            if row["district_id"] == district["districtId"]:
                key = {"Coalition":"LIB_NAT", "Greens":"GRN", "Other/Independent":"OTH_IND"}.get(row["party_family"], row["party_family"])
                if key not in values: continue
                values[key] = values.get(key, 0.0) + float(row["first_preference_votes"]); total += int(row["first_preference_votes"])
        for party in values: values[party] = values[party] / total * 100
        primary_errors.extend(abs(district["primaryEstimates"][party] - values[party]) for party in values)
    actual_seats = {party: sum(canon(row["winner_party_family"]) == party for row in rows) for party in prediction["activeFamilies"]}
    predicted_seats = prediction["assemblySeatMean"]
    seat_valid = all(0 <= float(predicted_seats.get(p, 0)) <= 88 for p in actual_seats)
    # Comparators are constructed from the same frozen pre-cutoff universe and
    # scored only after the prediction/outcome boundary has been crossed.
    prior = {}
    with (ROOT / "model/data/processed/vec_2014_assembly_family_primaries.csv").open() as handle:
        for row in csv.DictReader(handle):
            key = row["district_id"]; prior.setdefault(key, {p: 0.0 for p in prediction["activeFamilies"]})
            key_party = canon(row["party_family"])
            if key_party in prior[key]: prior[key][key_party] += float(row["first_preference_votes"])
    uniform = []; polling_only = []; polling_fundamentals = []; seat_level = []; complete = []
    statewide = prediction["statewidePrimaryEstimates"]; poll_binary = statewide["ALP"] / (statewide["ALP"] + statewide["LIB_NAT"])
    for row in districts:
        base = prior[row["districtId"]]; base_binary = base["ALP"] / max(base["ALP"] + base["LIB_NAT"], 1)
        uniform.append(base_binary); polling_only.append(poll_binary); polling_fundamentals.append((base_binary + poll_binary) / 2)
        favoured_probability = max(row["winProbabilities"].values())
        seat_level.append(favoured_probability if row["favouredParty"] == "ALP" else 1 - favoured_probability)
        complete.append(row["winProbabilities"]["ALP"])
    comparators = {}
    for name, values in {"uniformSwing": uniform, "pollingOnly": polling_only, "pollingPlusFundamentals": polling_fundamentals, "seatLevel": seat_level, "completeEnsemble": complete}.items():
        comparators[name] = {"brierALPEvent": brier_score(values, actual_alp), "logLossALPEvent": log_loss(values, actual_alp)}
    score = {"cycleId":"vic_la_2018", "predictionSha256":prediction_sha, "outcomeSha256":digest(OUTCOMES),
      "winner": {"accuracy":winner_accuracy, "brierALPEvent":brier_score(pred_alp, actual_alp), "logLossALPEvent":log_loss(pred_alp, actual_alp), "calibrationSlopeALPEvent":calibration_slope_intercept(pred_alp, actual_alp)[0], "calibrationInterceptALPEvent":calibration_slope_intercept(pred_alp, actual_alp)[1], "reliabilityALPEvent":reliability_bins(pred_alp, actual_alp)},
      "finalPair":{"accuracy":pair_accuracy}, "districtPrimary":{"meanAbsoluteError":float(np.mean(primary_errors))},
      "assembly":{"actualSeatTotals":actual_seats, "predictedSeatMeans":predicted_seats, "seatScoring":"valid" if seat_valid else "invalid-frozen-output-seat-scale", "seatCountAbsoluteErrors":({p:abs(float(predicted_seats.get(p,0))-actual_seats[p]) for p in actual_seats} if seat_valid else None)},
      "council":{"primaryScoring":"deferred-to-region-outcome-comparator", "seatScoring":"deferred", "reason":"frozen prediction contains governed broad-prior regional outputs; Council final-seat outcome adapter is a separate follow-up"},
      "comparators": comparators,
      "interpretation":{"singleCycleMetrics":True, "fourCycleCalibration":False, "completeBacktestGate":"closed", "probabilityCalibrationGate":"closed", "productionAuthorisation":"closed"}}
    score_bytes = json.dumps(score, sort_keys=True, indent=2).encode() + b"\n"
    score_path = ROOT / "model/data/validation/historical-replays/vic_la_2018-score.json"; score_path.write_bytes(score_bytes)
    score_manifest = {"cycleId":"vic_la_2018", "predictionSha256":prediction_sha, "outcomeSha256":digest(OUTCOMES), "criteriaSha256":digest(CRITERIA), "scoringCommit":subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip(), "scoreSha256":hashlib.sha256(score_bytes).hexdigest(), "scorePath":str(score_path.relative_to(ROOT))}
    (ROOT / "model/data/validation/historical-replays/vic_la_2018-score-manifest.json").write_text(json.dumps(score_manifest, indent=2)+"\n")
    print(json.dumps({"scorePath":score_manifest["scorePath"], "scoreSha256":score_manifest["scoreSha256"], "winnerAccuracy":winner_accuracy, "finalPairAccuracy":pair_accuracy}, indent=2))

if __name__ == "__main__": main()
