"""Score the already-frozen 2022 v2 prediction and comparator bundle.

The first operation in this script verifies both sealed pre-outcome artefacts.
Only after that boundary is crossed are official 2022 outcomes read.  This
script never imports or calls a forecast/comparator generator.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PRED_PATH = ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json"
BUNDLE_PATH = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators-v2.json"
OUTCOMES = ROOT / "data/processed/vec_2022_assembly_final_pairs.csv"
PRIMARY = ROOT / "data/processed/vec_2022_assembly_candidate_primaries.csv"
COUNCIL_PRIMARY = ROOT / "data/processed/vec_2022_council_candidate_primaries.csv"
COUNCIL_AUDIT = REPO / "metadata/vec-2014-2022-council-evidence-audit.json"
AUDIT = REPO / "metadata/historical-replay-v2-comparator-defect-audit.json"
CRITERIA = REPO / "metadata/historical-validation-acceptance-criteria.json"
SCORE = ROOT / "data/validation/historical-replays/vic_la_2022-v2-score.json"
MANIFEST = ROOT / "data/validation/historical-replays/vic_la_2022-v2-score-manifest.json"
OUTCOME_AUDIT = REPO / "metadata/historical-replay-2022-outcome-audit.json"
EXPECTED_PRED = "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
EXPECTED_BUNDLE = "cd04d597a9016f714f0c1e98d42c4ca66a91ce53a9c72283cb04c1abaea4a748"
FAMILIES = ["ALP", "LIB_NAT", "GRN", "ONP", "OTH_IND"]
HIST_TO_MODEL = {"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "One Nation": "ONP", "Other/Independent": "OTH_IND"}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_json(value: object) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_sealed() -> tuple[dict, dict, dict]:
    prediction_manifest = json.loads(PRED_PATH.read_text())
    prediction = prediction_manifest["prediction"]
    prediction_sha = sha_json(prediction)
    bundle = json.loads(BUNDLE_PATH.read_text())
    bundle_sha = sha_json({key: value for key, value in bundle.items() if key != "bundleSha256"})
    audit = json.loads(AUDIT.read_text())
    if prediction_sha != EXPECTED_PRED or prediction_manifest.get("predictionSha256") != EXPECTED_PRED:
        raise ValueError("sealed prediction fingerprint mismatch")
    if (prediction_manifest.get("cycleId"), prediction_manifest.get("modelVersion"), prediction_manifest.get("certificationStatus"), prediction_manifest.get("outcomesLoaded")) != ("vic_la_2022", "historical_replay_v2", "held-out-certifying-prediction-frozen", False):
        raise ValueError("sealed prediction manifest is not the expected pre-outcome contract")
    if bundle_sha != EXPECTED_BUNDLE or bundle.get("bundleSha256") != EXPECTED_BUNDLE or audit.get("replacementBundleSha256") != EXPECTED_BUNDLE:
        raise ValueError("sealed comparator bundle fingerprint mismatch")
    if bundle.get("outcomesLoaded") is not False or bundle.get("informationCutoff") != "2022-11-25":
        raise ValueError("comparator bundle is not pre-outcome or cutoff-safe")
    if bundle.get("certifyingPredictionSha256") != EXPECTED_PRED or len(bundle.get("comparators", {})) != 5:
        raise ValueError("comparator bundle does not reference all five sealed comparators")
    return prediction, bundle, {"predictionSha256": prediction_sha, "comparatorBundleSha256": bundle_sha}


def probability_metrics(rows: list[tuple[dict, str]]) -> dict[str, float]:
    brier = 0.0
    log_loss = 0.0
    accuracy = 0
    alp_brier = 0.0
    alp_log_loss = 0.0
    for item, actual in rows:
        probs = {family: float(item.get("winProbabilities", {}).get(family, 0.0)) for family in FAMILIES}
        accuracy += int(max(probs, key=probs.get) == actual)
        brier += sum((probs[family] - float(family == actual)) ** 2 for family in FAMILIES)
        log_loss -= math.log(max(1e-15, probs.get(actual, 0.0)))
        alp = float(actual == "ALP")
        alp_brier += (probs["ALP"] - alp) ** 2
        alp_log_loss -= math.log(max(1e-15, probs["ALP"] if alp else 1.0 - probs["ALP"]))
    n = len(rows)
    return {"accuracy": accuracy / n if n else None, "multiclassBrier": brier / n if n else None, "multiclassLogLoss": log_loss / n if n else None, "alpEventBrier": alp_brier / n if n else None, "alpEventLogLoss": alp_log_loss / n if n else None}


def primary_actual() -> dict[str, dict[str, float]]:
    values: dict[str, dict[str, float]] = {}
    for row in read_csv(PRIMARY):
        if row["contest"] != "general-election":
            continue
        district = row["district_id"]
        family = HIST_TO_MODEL.get(row["party_family"])
        if family is None:
            raise ValueError(f"unknown Assembly family {row['party_family']!r}")
        values.setdefault(district, {family_name: 0.0 for family_name in FAMILIES})[family] += float(row["first_preference_votes"])
        values[district]["_formal"] = float(row["formal_votes"])
    for district, row in values.items():
        formal = row.pop("_formal")
        if formal <= 0:
            raise ValueError(f"non-positive formal vote total for {district}")
        for family in FAMILIES:
            row[family] = row[family] / formal * 100.0
    if len(values) != 87:
        raise ValueError(f"expected 87 Assembly primary districts, found {len(values)}")
    return values


def score_assembly(prediction: dict) -> dict:
    outcomes = {row["district_id"]: row for row in read_csv(OUTCOMES)}
    if len(outcomes) != 87 or "narracan" in outcomes:
        raise ValueError("Assembly outcome universe must contain exactly 87 districts and exclude Narracan")
    actual_primary = primary_actual()
    predicted = {row["districtId"]: row for row in prediction["assemblyDistricts"]}
    if set(predicted) != set(outcomes):
        raise ValueError("prediction and Assembly outcome district universes differ")
    winner_rows = []
    primary_errors = {family: [] for family in FAMILIES}
    final_pair_rows = []
    for district, outcome in outcomes.items():
        actual_winner = HIST_TO_MODEL.get(outcome["winner_party_family"])
        if actual_winner is None:
            raise ValueError(f"unknown winner family {outcome['winner_party_family']!r}")
        winner_rows.append((predicted[district], actual_winner))
        for family in FAMILIES:
            primary_errors[family].append(abs(float(predicted[district]["primaryEstimates"].get(family, 0.0)) - actual_primary[district][family]))
        if outcome["final_pair_available"].casefold() == "true":
            actual_pair = "-".join(HIST_TO_MODEL[part] for part in outcome["final_pair_family_label"].split("-"))
            final_pair_rows.append((predicted[district].get("likelyFinalPair"), actual_pair))
    metrics = probability_metrics(winner_rows)
    actual_seats = {family: sum(1 for _, actual in winner_rows if actual == family) for family in FAMILIES}
    predicted_seats = prediction["assemblySeatSummary"]
    seat_error = {family: {"meanError": float(predicted_seats[family]["mean"]) - actual_seats[family], "medianError": float(predicted_seats[family]["median"]) - actual_seats[family], "actual": actual_seats[family], "mean": predicted_seats[family]["mean"], "median": predicted_seats[family]["median"], "inside80": float(predicted_seats[family]["lower80"]) <= actual_seats[family] <= float(predicted_seats[family]["upper80"])} for family in FAMILIES}
    primary_mae_by_family = {family: sum(errors) / len(errors) for family, errors in primary_errors.items()}
    primary_mae = sum(sum(errors) for errors in primary_errors.values()) / (len(winner_rows) * len(FAMILIES))
    # Statewide quantities are aggregated from candidate votes, not averaged
    # district percentages.
    vote_totals = {family: 0.0 for family in FAMILIES}; formal_total = 0.0
    for row in read_csv(PRIMARY):
        if row["contest"] != "general-election": continue
        family = HIST_TO_MODEL[row["party_family"]]; vote_totals[family] += float(row["first_preference_votes"]); formal_total = formal_total + float(row["formal_votes"]) if row["candidate_order"] == "1" else formal_total
    actual_state = {family: vote_totals[family] / formal_total * 100.0 for family in FAMILIES}
    pred_state = prediction["statewidePrimaryEstimates"]
    state_errors = {family: (float(pred_state.get(family, 0.0)) - actual_state[family]) for family in ["ALP", "LIB_NAT", "GRN"]}
    state_errors["predicted_poll_residual_vs_actual_nonmajor_residual"] = float(pred_state.get("OTH_IND", 0.0)) - (actual_state["ONP"] + actual_state["OTH_IND"])
    return {"districtCount": 87, "winner": metrics, "finalPair": {"availableDistricts": len(final_pair_rows), "unavailableDistricts": 87 - len(final_pair_rows), "unavailableReason": "official VEC page provides only 2CP/early-majority information; no final-pair outcome was used", "accuracy": sum(a == b for a, b in final_pair_rows) / len(final_pair_rows) if final_pair_rows else None}, "districtPrimaryMAE": primary_mae, "districtPrimaryMAEByFamily": primary_mae_by_family, "districtPrimaryMaximumAbsoluteError": max(max(errors) for errors in primary_errors.values()), "statewideFamilySharesActual": actual_state, "statewideVoteErrors": state_errors, "assemblySeats": {"actual": actual_seats, "byFamily": seat_error, "meanAbsoluteMeanSeatError": sum(abs(v["meanError"]) for v in seat_error.values()) / len(FAMILIES), "interval80Coverage": sum(v["inside80"] for v in seat_error.values()) / len(FAMILIES)}}


def score_council(prediction: dict) -> dict:
    audit = json.loads(COUNCIL_AUDIT.read_text())
    actual_by_region: dict[str, dict[str, int]] = {}
    primaries = {(row["region_id"], row["candidate_name"]): row["party_name"] for row in read_csv(COUNCIL_PRIMARY)}
    aliases = json.loads((ROOT / "config/historical-party-family-crosswalk.json")["aliases"] if False else (ROOT / "config/historical-party-family-crosswalk.json").read_text())["aliases"]
    alias_to_family = {alias.casefold(): family for family, names in aliases.items() for alias in names}
    for region in audit["regions"]:
        if region["electionId"] != "vic_lc_2022": continue
        counts = {family: 0 for family in FAMILIES}
        for candidate in region["elected"]:
            raw = primaries.get((region["regionId"], candidate))
            if raw is None or raw.casefold() not in alias_to_family:
                raise ValueError(f"unknown Council elected party for {region['regionName']}: {candidate}")
            counts[HIST_TO_MODEL[alias_to_family[raw.casefold()]]] += 1
        if sum(counts.values()) != 5: raise ValueError("Council region does not have five elected seats")
        actual_by_region[region["regionId"]] = counts
    pred_regions = {row["regionName"]: row for row in prediction["council"]["regions"]}
    region_errors = {}
    for region_id, actual in actual_by_region.items():
        name = next(region["regionName"].replace(" Region", "") for region in audit["regions"] if region["regionId"] == region_id)
        pred = next((row for row in prediction["council"]["regions"] if row["regionName"] == name), None)
        if pred is None: raise ValueError(f"missing Council prediction for {name}")
        means = pred["seatDistributionMean"]
        region_errors[region_id] = {family: float(means.get(family, 0.0)) - actual[family] for family in FAMILIES}
    actual_total = {family: sum(row[family] for row in actual_by_region.values()) for family in FAMILIES}
    predicted_total = {family: sum(float(row["seatDistributionMean"].get(family, 0.0)) for row in prediction["council"]["regions"]) for family in FAMILIES}
    return {"regions": 8, "seatsPerRegion": 5, "actualSeats": actual_total, "predictedMeanSeats": predicted_total, "absoluteErrorByFamily": {family: abs(predicted_total[family] - actual_total[family]) for family in FAMILIES}, "regionalMeanAbsoluteSeatError": sum(abs(value) for errors in region_errors.values() for value in errors.values()) / (8 * len(FAMILIES)), "regionalErrors": region_errors, "regionalPrimaryMetric": {"status": "unavailable", "reason": "frozen certifying prediction contains no Council regional primary estimates"}}


def score_comparators(prediction: dict, bundle: dict, outcomes_score: dict) -> dict:
    actual = {row["district_id"]: row for row in read_csv(OUTCOMES)}
    primary = primary_actual()
    result = {}
    for name, comparator in bundle["comparators"].items():
        if name == "complete-ensemble":
            result[name] = {"status": "scored-by-frozen-prediction", "metrics": outcomes_score["assembly"]}
            continue
        rows = {row["districtId"]: row for row in comparator["assemblyDistricts"]}
        winner_rows = []
        errors = []
        final_pairs = []
        for district, outcome in actual.items():
            item = rows[district]; winner = HIST_TO_MODEL[outcome["winner_party_family"]]; winner_rows.append((item, winner))
            errors.extend(abs(float(item["primaryEstimates"].get(family, 0.0)) - primary[district][family]) for family in FAMILIES)
            if outcome["final_pair_available"].casefold() == "true":
                actual_pair = "-".join(HIST_TO_MODEL[x] for x in outcome["final_pair_family_label"].split("-")); final_pairs.append((item.get("likelyFinalPair"), actual_pair))
        metrics = probability_metrics(winner_rows)
        metrics["districtPrimaryMAE"] = sum(errors) / len(errors)
        metrics["finalPairAccuracy"] = sum(a == b for a, b in final_pairs) / len(final_pairs) if final_pairs else None
        if "assemblySeatSummary" in comparator:
            actual_seats = outcomes_score["assembly"]["assemblySeats"]["actual"]
            means = comparator["assemblySeatSummary"]
            metrics["seatCountErrorByFamily"] = {family: means[family]["mean"] - actual_seats[family] for family in FAMILIES}
        result[name] = {"status": "scored", "metrics": metrics, "unsupported": comparator.get("council", {}).get("reason")}
    return result


def main() -> None:
    prediction, bundle, sealed = verify_sealed()
    boundary = {"outcomeBoundaryCrossedAfterPredictionAndComparatorVerification": True}
    # Outcome files are first read only after verify_sealed() succeeds.
    assembly = score_assembly(prediction)
    council = score_council(prediction)
    score = {"schemaVersion": 1, "cycleId": "vic_la_2022", "modelVersion": "historical_replay_v2", "outcomesLoaded": True, "predictionSha256": sealed["predictionSha256"], "comparatorBundleSha256": sealed["comparatorBundleSha256"], "assembly": assembly, "council": council, "comparators": {}}
    score["comparators"] = score_comparators(prediction, bundle, score)
    vote_mae = sum(abs(value) for key, value in assembly["statewideVoteErrors"].items() if key in {"ALP", "LIB_NAT", "GRN"}) / 3
    vote_max = max(abs(value) for key, value in assembly["statewideVoteErrors"].items() if key in {"ALP", "LIB_NAT", "GRN"})
    seat_errors = [abs(value["meanError"]) for value in assembly["assemblySeats"]["byFamily"].values()]
    score["thresholds"] = {"criteriaPath": str(CRITERIA.relative_to(REPO)), "criteriaSha256": sha_file(CRITERIA), "cycleLevelOnly": True, "completeBacktest": "unavailable-until-four-cycles", "probabilityCalibration": "unavailable-until-four-cycles", "cycleLevelAssessment": {"statewideVoteError": {"meanAbsolutePercentagePoints": vote_mae, "maximumAbsolutePercentagePoints": vote_max, "threshold": {"meanMax": 4.0, "maximumMax": 7.0}, "status": "met" if vote_mae <= 4.0 and vote_max <= 7.0 else "missed"}, "seatWinnerAccuracy": {"value": assembly["winner"]["accuracy"], "threshold": 0.70, "status": "met" if assembly["winner"]["accuracy"] >= 0.70 else "missed"}, "seatCountError": {"maximumAbsoluteMeanError": max(seat_errors), "meanAbsoluteMeanError": sum(seat_errors) / len(seat_errors), "threshold": {"maximum": 8.0, "meanMaximum": 5.0}, "status": "met" if max(seat_errors) <= 8.0 and sum(seat_errors) / len(seat_errors) <= 5.0 else "missed"}, "brierScore": {"value": assembly["winner"]["multiclassBrier"], "threshold": 0.25, "status": "met" if assembly["winner"]["multiclassBrier"] <= 0.25 else "missed"}, "logLoss": {"value": assembly["winner"]["multiclassLogLoss"], "threshold": 1.20, "status": "met" if assembly["winner"]["multiclassLogLoss"] <= 1.20 else "missed"}, "intervalCoverage80": {"value": assembly["assemblySeats"]["interval80Coverage"], "threshold": {"minimum": 0.70, "maximum": 0.90}, "status": "met" if 0.70 <= assembly["assemblySeats"]["interval80Coverage"] <= 0.90 else "missed"}, "finalPairCalibration": {"status": "unavailable", "reason": "frozen prediction contains only most-likely pair fields, and 10 official final pairs are unavailable"}, "regionalError": {"status": "unavailable", "reason": "frozen prediction contains Council seat means but no regional primary estimates"}, "contestType": {"status": "unavailable", "reason": "no preregistered contest-type partition is frozen for this single cycle"}}}
    outcome_audit = {"schemaVersion": 1, "cycleId": "vic_la_2022", "status": "scoring-only-outcomes-loaded-after-sealed-prediction", "assemblyOutcomePath": str(OUTCOMES.relative_to(REPO)), "assemblyOutcomeSha256": sha_file(OUTCOMES), "assemblyDistricts": 87, "narracanIncluded": False, "finalPairAvailableDistricts": assembly["finalPair"]["availableDistricts"], "finalPairUnavailableDistricts": assembly["finalPair"]["unavailableDistricts"], "sourceManifestPath": "metadata/vec-2022-assembly-final-pair-source-manifest.csv", "sourceManifestSha256": sha_file(REPO / "metadata/vec-2022-assembly-final-pair-source-manifest.csv"), "candidatePrimaryPath": str(PRIMARY.relative_to(REPO)), "councilEvidenceAuditPath": str(COUNCIL_AUDIT.relative_to(REPO)), "preElectionInputEligible": False, "productionAuthorisation": False}
    OUTCOME_AUDIT.write_text(json.dumps(outcome_audit, indent=2) + "\n")
    score_bytes = json.dumps(score, sort_keys=True, separators=(",", ":")).encode(); score["scoreSha256"] = sha_bytes(score_bytes)
    SCORE.write_text(json.dumps(score, indent=2) + "\n")
    manifest = {"schemaVersion": 1, "cycleId": "vic_la_2022", "modelVersion": "historical_replay_v2", **sealed, "predictionPath": str(PRED_PATH.relative_to(REPO)), "comparatorBundlePath": str(BUNDLE_PATH.relative_to(REPO)), "assemblyOutcomePath": str(OUTCOMES.relative_to(REPO)), "assemblyOutcomeSha256": sha_file(OUTCOMES), "assemblySourceManifestPath": "metadata/vec-2022-assembly-final-pair-source-manifest.csv", "assemblySourceManifestSha256": sha_file(REPO / "metadata/vec-2022-assembly-final-pair-source-manifest.csv"), "councilOutcomePaths": ["model/data/processed/vec_2022_council_candidate_primaries.csv", "metadata/vec-2014-2022-council-evidence-audit.json"], "councilOutcomeSha256": {"model/data/processed/vec_2022_council_candidate_primaries.csv": sha_file(ROOT / "data/processed/vec_2022_council_candidate_primaries.csv"), "metadata/vec-2014-2022-council-evidence-audit.json": sha_file(COUNCIL_AUDIT)}, "criteriaPath": str(CRITERIA.relative_to(REPO)), "criteriaSha256": sha_file(CRITERIA), "scoringCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(), "outcomeBoundaryCrossedAfterPredictionAndComparatorVerification": True, "forecastRegenerated": False, "scorePath": str(SCORE.relative_to(REPO)), "scoreSha256": score["scoreSha256"]}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"scorePath": str(SCORE.relative_to(REPO)), "scoreSha256": score["scoreSha256"], "manifestPath": str(MANIFEST.relative_to(REPO)), "outcomesLoaded": True, "finalPairAvailableDistricts": assembly["finalPair"]["availableDistricts"]}))


if __name__ == "__main__":
    main()
