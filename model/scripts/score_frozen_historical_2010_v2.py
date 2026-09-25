"""Score the sealed 2010 v2 holdout after crossing the outcome boundary once.

The sealed prediction, corrected comparator bundle and cycle-specific comparator
contract are verified before any target-election file is read.  This module
contains scoring only; it never imports a forecast or comparator generator.
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
PRED_PATH = ROOT / "data/validation/historical-replays/vic_la_2010-v2-prediction.json"
BUNDLE_PATH = ROOT / "data/validation/historical-replays/vic_la_2010-v2-comparators-v2.json"
OLD_BUNDLE_PATH = ROOT / "data/validation/historical-replays/vic_la_2010-v2-comparators.json"
SPEC_PATH = REPO / "metadata/historical-replay-v2-comparator-spec-2010.json"
PRIMARY_PATH = ROOT / "data/processed/vec_2010_assembly_candidate_primaries.csv"
ASSEMBLY_OUTCOME_PATH = ROOT / "data/processed/vec_2010_assembly_final_pairs.csv"
ASSEMBLY_MANIFEST_PATH = REPO / "metadata/historical-replay-2010-assembly-outcome-audit.json"
COUNCIL_PRIMARY_PATH = ROOT / "data/processed/vec_2010_council_candidate_primaries.csv"
COUNCIL_AUDIT_PATH = REPO / "metadata/vec-2010-council-evidence-audit.json"
CRITERIA_PATH = REPO / "metadata/historical-validation-acceptance-criteria.json"
SCORE_PATH = ROOT / "data/validation/historical-replays/vic_la_2010-v2-score.json"
MANIFEST_PATH = ROOT / "data/validation/historical-replays/vic_la_2010-v2-score-manifest.json"
OUTCOME_AUDIT_PATH = REPO / "metadata/historical-replay-2010-outcome-audit.json"
EXPECTED_PREDICTION = "3d23e92d8aa0d8d4c6e522bbc07f529d614653c5d20aa68a952a96704804fd5d"
EXPECTED_BUNDLE = "a5e464f8d84ba7cdc4a198df43006eb64824f4dc71c1d789ce55bffbcbd76b13"
EXPECTED_OLD_BUNDLE = "0000000000000000000000000000000000000000000000000000000000000000"
EXPECTED_SPEC = "f31ad1c4a221cfd076727e5c41595ca6cb316f81be9eafd2d977bb1f59603726"
FAMILIES = ["ALP", "LIB_NAT", "GRN", "OTH_IND"]
HIST_TO_MODEL = {"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "Other/Independent": "OTH_IND"}


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
    prediction = prediction_manifest.get("prediction")
    bundle = json.loads(BUNDLE_PATH.read_text())
    spec = json.loads(SPEC_PATH.read_text())
    if sha_json(prediction) != EXPECTED_PREDICTION or prediction_manifest.get("predictionSha256") != EXPECTED_PREDICTION:
        raise ValueError("sealed 2010 prediction fingerprint mismatch")
    required_prediction = (prediction_manifest.get("cycleId"), prediction_manifest.get("modelVersion"), prediction_manifest.get("informationCutoff"), prediction.get("certificationStatus"), prediction_manifest.get("targetOutcomeLoaded"))
    if required_prediction != ("vic_la_2010", "historical_replay_v2", "2010-11-26", "held-out-certifying-prediction-frozen", False):
        raise ValueError("sealed 2010 prediction manifest is not the expected pre-outcome contract")
    bundle_for_hash = dict(bundle)
    bundle_for_hash.pop("bundleSha256", None)
    if sha_json(bundle_for_hash) != EXPECTED_BUNDLE:
        raise ValueError("2010 comparator bundle fingerprint mismatch")
    if bundle.get("cycleId") != "vic_la_2010" or bundle.get("informationCutoff") != "2010-11-26" or bundle.get("outcomesLoaded") is not False:
        raise ValueError("corrected comparator bundle is not pre-outcome or cutoff-safe")
    if bundle.get("certifyingPredictionSha256") != EXPECTED_PREDICTION or set(bundle.get("comparators", {})) != {"uniform-swing-baseline", "polling-only", "polling-plus-fundamentals", "seat-level-model", "complete-ensemble"}:
        raise ValueError("corrected comparator bundle does not reference all five sealed comparators")
    if sha_file(SPEC_PATH) != EXPECTED_SPEC or bundle.get("comparatorSpecSha256") != EXPECTED_SPEC or spec.get("outcomesLoaded") is not False:
        raise ValueError("2010 comparator specification fingerprint mismatch")
    comps = bundle["comparators"]
    for left, right in (("uniform-swing-baseline", "polling-only"), ("uniform-swing-baseline", "seat-level-model"), ("polling-only", "polling-plus-fundamentals"), ("polling-plus-fundamentals", "seat-level-model")):
        if json.dumps(comps[left].get("assemblyDistricts", []), sort_keys=True) == json.dumps(comps[right].get("assemblyDistricts", []), sort_keys=True):
            raise ValueError(f"comparator alias detected: {left} == {right}")
    complete = comps["complete-ensemble"]
    reference = complete.get("reference", {})
    if reference.get("predictionPath") != str(PRED_PATH.relative_to(REPO)) or reference.get("predictionSha256") != EXPECTED_PREDICTION or reference.get("valuesCopied") is not False:
        raise ValueError("complete ensemble is not a reference to the immutable prediction")
    return prediction, bundle, {"predictionSha256": EXPECTED_PREDICTION, "comparatorBundleSha256": EXPECTED_BUNDLE, "comparatorSpecSha256": EXPECTED_SPEC}


def map_family(value: str) -> str:
    try:
        return HIST_TO_MODEL[value]
    except KeyError as exc:
        raise ValueError(f"unknown historical family {value!r}") from exc


def primary_actual() -> tuple[dict[str, dict[str, float]], dict[str, float], float]:
    rows = [row for row in read_csv(PRIMARY_PATH) if row["election_id"] == "vic_la_2010"]
    districts: dict[str, dict[str, float]] = {}
    totals = {family: 0.0 for family in FAMILIES}
    formal_total = 0.0
    for row in rows:
        family = map_family(row["party_family"])
        district = row["district_id"]
        districts.setdefault(district, {family_name: 0.0 for family_name in FAMILIES})
        districts[district][family] += float(row["first_preference_votes"])
        totals[family] += float(row["first_preference_votes"])
    for district, values in districts.items():
        formal_values = {float(row["formal_votes"]) for row in rows if row["district_id"] == district}
        if len(formal_values) != 1 or next(iter(formal_values)) <= 0:
            raise ValueError(f"formal vote total is not unique and positive for {district}")
        formal = next(iter(formal_values))
        if abs(sum(values.values()) - formal) > 0.01:
            raise ValueError(f"primary family totals do not reconcile for {district}")
        for family in FAMILIES:
            values[family] = values[family] / formal * 100.0
        formal_total += formal
    if len(districts) != 88:
        raise ValueError(f"expected 88 Assembly primary districts, found {len(districts)}")
    if abs(sum(totals.values()) - formal_total) > 0.01:
        raise ValueError("statewide primary totals do not reconcile")
    statewide = {family: totals[family] / formal_total * 100.0 for family in FAMILIES}
    return districts, statewide, formal_total


def validate_outcomes(primary: dict[str, dict[str, float]]) -> dict[str, dict[str, str]]:
    rows = read_csv(ASSEMBLY_OUTCOME_PATH)
    if len(rows) != 88 or len({row["district_id"] for row in rows}) != 88:
        raise ValueError("2010 Assembly scoring universe must contain exactly 88 unique districts")
    if set(primary) != {row["district_id"] for row in rows}:
        raise ValueError("2010 primary and final-pair district universes differ")
    outcomes: dict[str, dict[str, str]] = {}
    for row in rows:
        if not row.get("source_url") or len(row.get("source_sha256", "")) != 64 or row.get("target_outcome_dependency", "True").casefold() != "false":
            raise ValueError(f"invalid official outcome provenance for {row['district_name']}")
        winner = map_family(row["winner_party_family"])
        if row["final_pair_available"].casefold() == "true":
            if not row["finalist_1_candidate"] or not row["finalist_2_candidate"] or not row["finalist_1_party_family"] or not row["finalist_2_party_family"]:
                raise ValueError(f"incomplete final pair for {row['district_name']}")
            if abs(float(row["finalist_1_percent"]) + float(row["finalist_2_percent"]) - 100.0) > 0.25:
                raise ValueError(f"final pair percentages do not reconcile for {row['district_name']}")
            if row["elected_candidate"] not in {row["finalist_1_candidate"], row["finalist_2_candidate"]}:
                raise ValueError(f"elected candidate is not in final pair for {row['district_name']}")
            if float(row["finalist_1_votes"]) == float(row["finalist_2_votes"]):
                raise ValueError(f"tied final pair for {row['district_name']}")
            winner_candidate = row["finalist_1_candidate"] if float(row["finalist_1_votes"]) > float(row["finalist_2_votes"]) else row["finalist_2_candidate"]
            if winner_candidate != row["elected_candidate"]:
                raise ValueError(f"final pair winner mismatch for {row['district_name']}")
        outcomes[row["district_id"]] = row | {"winner_model_family": winner}
    return outcomes


def probability_metrics(rows: list[tuple[dict, str]]) -> dict[str, float | None]:
    if not rows:
        return {"accuracy": None, "multiclassBrier": None, "multiclassLogLoss": None, "alpEventBrier": None, "alpEventLogLoss": None}
    brier = log_loss = alp_brier = alp_log_loss = 0.0
    correct = 0
    for item, actual in rows:
        probs = {family: float(item.get("winProbabilities", {}).get(family, 0.0)) for family in FAMILIES}
        correct += int(max(probs, key=probs.get) == actual)
        brier += sum((probs[family] - float(family == actual)) ** 2 for family in FAMILIES)
        log_loss -= math.log(max(1e-15, probs[actual]))
        event = float(actual == "ALP")
        alp_prob = probs["ALP"]
        alp_brier += (alp_prob - event) ** 2
        alp_log_loss -= math.log(max(1e-15, alp_prob if event else 1.0 - alp_prob))
    n = len(rows)
    return {"accuracy": correct / n, "multiclassBrier": brier / n, "multiclassLogLoss": log_loss / n, "alpEventBrier": alp_brier / n, "alpEventLogLoss": alp_log_loss / n}


def score_assembly(prediction: dict, outcomes: dict[str, dict[str, str]], actual_primary: dict[str, dict[str, float]], statewide_actual: dict[str, float]) -> dict:
    predicted = {row["districtId"]: row for row in prediction["assemblyDistricts"]}
    if set(predicted) != set(outcomes) or len(predicted) != 88:
        raise ValueError("prediction and outcome Assembly districts differ")
    winner_rows = [(predicted[district], row["winner_model_family"]) for district, row in outcomes.items()]
    errors = {family: [] for family in FAMILIES}
    pairs = []
    for district, outcome in outcomes.items():
        for family in FAMILIES:
            errors[family].append(abs(float(predicted[district]["primaryEstimates"].get(family, 0.0)) - actual_primary[district][family]))
        if outcome["final_pair_available"].casefold() == "true":
            actual_pair = {map_family(outcome["finalist_1_party_family"]), map_family(outcome["finalist_2_party_family"])}
            predicted_pair = set(str(predicted[district].get("likelyFinalPair", "")).split("-"))
            pairs.append(predicted_pair == actual_pair)
    winner = probability_metrics(winner_rows)
    actual_seats = {family: sum(actual == family for _, actual in winner_rows) for family in FAMILIES}
    summary = prediction["assemblySeatSummary"]
    by_family = {family: {"actual": actual_seats[family], "mean": summary[family]["mean"], "median": summary[family]["median"], "meanError": float(summary[family]["mean"]) - actual_seats[family], "medianError": float(summary[family]["median"]) - actual_seats[family], "inside80": float(summary[family]["lower80"]) <= actual_seats[family] <= float(summary[family]["upper80"])} for family in FAMILIES}
    state_errors = {family: float(prediction["statewidePrimaryEstimates"].get(family, 0.0)) - statewide_actual[family] for family in FAMILIES}
    return {"districtCount": 88, "winner": winner, "districtPrimaryMAE": sum(sum(values) for values in errors.values()) / (88 * len(FAMILIES)), "districtPrimaryMAEByFamily": {family: sum(values) / len(values) for family, values in errors.items()}, "districtPrimaryMaximumAbsoluteError": max(max(values) for values in errors.values()), "statewideFamilySharesActual": statewide_actual, "statewideVoteErrors": state_errors, "finalPair": {"availableDistricts": len(pairs), "unavailableDistricts": 88 - len(pairs), "accuracy": sum(pairs) / len(pairs) if pairs else None, "calibration": {"status": "unavailable", "reason": "frozen prediction contains only the most-likely pair, not a complete pair distribution"}}, "assemblySeats": {"actual": actual_seats, "byFamily": by_family, "meanAbsoluteMeanSeatError": sum(abs(item["meanError"]) for item in by_family.values()) / len(FAMILIES), "medianAbsoluteMedianSeatError": sum(abs(item["medianError"]) for item in by_family.values()) / len(FAMILIES), "interval80Coverage": sum(item["inside80"] for item in by_family.values()) / len(FAMILIES)}}


def council_actual() -> dict[str, dict[str, int]]:
    audit = json.loads(COUNCIL_AUDIT_PATH.read_text())
    primary_rows = read_csv(COUNCIL_PRIMARY_PATH)
    party_by_candidate = {(row["region_id"], row["candidate_name"]): row["party_name"] for row in primary_rows if row["election_id"] == "vic_lc_2010"}
    aliases = json.loads((ROOT / "config/historical-party-family-crosswalk.json").read_text())["aliases"]
    alias_map = {name.casefold(): family for family, names in aliases.items() for name in names}
    actual: dict[str, dict[str, int]] = {}
    for region in audit["regions"]:
        if region["electionId"] != "vic_lc_2010":
            continue
        counts = {family: 0 for family in FAMILIES}
        for candidate in region["elected"]:
            raw = party_by_candidate.get((region["regionId"], candidate))
            if raw is None:
                raise ValueError(f"unknown Council party for {region['regionName']}: {candidate}")
            # Council minor-party labels are intentionally collapsed into the
            # frozen OTH_IND family; no new prediction class is introduced.
            if raw.casefold() in alias_map:
                mapped = alias_map[raw.casefold()]
                family = {"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "One Nation": "OTH_IND", "Other/Independent": "OTH_IND"}.get(mapped, "OTH_IND")
            else:
                family = "OTH_IND"
            counts[family] += 1
        if sum(counts.values()) != 5:
            raise ValueError(f"Council region does not contain five elected seats: {region['regionName']}")
        actual[region["regionId"]] = counts
    if len(actual) != 8:
        raise ValueError("2010 Council outcome must contain eight regions")
    return actual


def score_council(prediction: dict, actual: dict[str, dict[str, int]]) -> dict:
    predicted_regions = prediction["council"]["regions"]
    if len(predicted_regions) != 8:
        raise ValueError("frozen Council prediction must contain eight regions")
    by_name = {row["regionName"].casefold().replace(" ", "-"): row for row in predicted_regions}
    errors = {}
    actual_total = {family: 0 for family in FAMILIES}
    predicted_total = {family: 0.0 for family in FAMILIES}
    for region_id, counts in actual.items():
        audit_region = next(r for r in json.loads(COUNCIL_AUDIT_PATH.read_text())["regions"] if r["regionId"] == region_id)
        name = audit_region["regionName"].replace(" Region", "").casefold().replace(" ", "-")
        if name not in by_name:
            raise ValueError(f"missing frozen Council region {name}")
        means = by_name[name]["seatDistributionMean"]
        errors[region_id] = {family: float(means.get(family, 0.0)) - counts[family] for family in FAMILIES}
        for family in FAMILIES:
            actual_total[family] += counts[family]
            predicted_total[family] += float(means.get(family, 0.0))
    return {"regions": 8, "seatsPerRegion": 5, "actualSeats": actual_total, "predictedMeanSeats": predicted_total, "absoluteErrorByFamily": {family: abs(predicted_total[family] - actual_total[family]) for family in FAMILIES}, "regionalMeanAbsoluteSeatError": sum(abs(value) for values in errors.values() for value in values.values()) / (8 * len(FAMILIES)), "regionalErrors": errors, "regionalPrimaryMetric": {"status": "unavailable", "reason": "frozen 2010 prediction contains no Council regional primary estimates"}}


def score_comparators(bundle: dict, outcomes: dict[str, dict[str, str]], actual_primary: dict[str, dict[str, float]], complete: dict) -> dict:
    result = {}
    for name, comparator in bundle["comparators"].items():
        if name == "complete-ensemble":
            result[name] = {"status": "scored-by-frozen-prediction", "metrics": complete}
            continue
        rows = {row["districtId"]: row for row in comparator.get("assemblyDistricts", [])}
        availability = set(comparator.get("metricAvailability", []))
        item = {"status": "scored", "metricAvailability": sorted(availability), "metrics": {}}
        winner_available = any(metric == "winner" or metric.startswith("winner-") or "event-probability" in metric for metric in availability)
        if winner_available and len(rows) == 88 and all("winProbabilities" in row for row in rows.values()):
            item["metrics"]["winner"] = probability_metrics([(rows[district], outcome["winner_model_family"]) for district, outcome in outcomes.items()])
        else:
            item["metrics"]["winner"] = {"status": "not-applicable-by-pre-score-contract"}
        if any("district-primary" in metric for metric in availability) and len(rows) == 88 and all("primaryEstimates" in row for row in rows.values()):
            item["metrics"]["districtPrimaryMAE"] = sum(abs(float(rows[district]["primaryEstimates"].get(family, 0.0)) - actual_primary[district][family]) for district in outcomes for family in FAMILIES) / (88 * len(FAMILIES))
        else:
            item["metrics"]["districtPrimaryMAE"] = {"status": "not-applicable-by-pre-score-contract"}
        if "seat-count" in availability and len(rows) == 88 and all("winProbabilities" in row for row in rows.values()):
            predicted = {family: sum(float(rows[district]["winProbabilities"].get(family, 0.0)) for district in outcomes) for family in FAMILIES}
            actual = {family: sum(outcome["winner_model_family"] == family for outcome in outcomes.values()) for family in FAMILIES}
            item["metrics"]["seatCount"] = {"actual": actual, "predictedIndependentMarginalMean": predicted, "absoluteErrorByFamily": {family: abs(predicted[family] - actual[family]) for family in FAMILIES}, "meanAbsoluteError": sum(abs(predicted[family] - actual[family]) for family in FAMILIES) / len(FAMILIES), "derivedFromFrozenIndependentSeatMarginals": True}
        else:
            item["metrics"]["seatCount"] = {"status": "not-applicable-by-pre-score-contract"}
        for metric in ("finalPair", "Council"):
            item["metrics"][metric] = {"status": "not-applicable-by-pre-score-contract"}
        result[name] = item
    return result


def threshold_assessment(assembly: dict, criteria: dict) -> dict:
    thresholds = criteria["thresholds"]
    state_errors = list(assembly["statewideVoteErrors"].values())
    vote_mae = sum(abs(value) for value in state_errors) / len(state_errors)
    vote_max = max(abs(value) for value in state_errors)
    seat_errors = [abs(item["meanError"]) for item in assembly["assemblySeats"]["byFamily"].values()]
    coverage = assembly["assemblySeats"]["interval80Coverage"]
    return {"statewideVoteError": {"meanAbsolutePercentagePoints": vote_mae, "maximumAbsolutePercentagePoints": vote_max, "threshold": thresholds["statewideVoteError"], "status": "met" if vote_mae <= thresholds["statewideVoteError"]["cycleMeanAbsoluteErrorMaxPercentagePoints"] and vote_max <= thresholds["statewideVoteError"]["cycleMaximumAbsoluteErrorMaxPercentagePoints"] else "missed"}, "seatWinnerAccuracy": {"value": assembly["winner"]["accuracy"], "threshold": thresholds["seatWinner"]["cycleAccuracyMin"], "status": "met" if assembly["winner"]["accuracy"] >= thresholds["seatWinner"]["cycleAccuracyMin"] else "missed"}, "seatCountError": {"maximumAbsoluteMeanError": max(seat_errors), "meanAbsoluteMeanError": sum(seat_errors) / len(seat_errors), "threshold": thresholds["seatCount"], "status": "met" if max(seat_errors) <= thresholds["seatCount"]["cycleAbsoluteErrorMaxSeats"] and sum(seat_errors) / len(seat_errors) <= thresholds["seatCount"]["cycleMeanAbsoluteErrorMaxSeats"] else "missed"}, "multiclassBrier": {"value": assembly["winner"]["multiclassBrier"], "threshold": thresholds["brierScore"]["cycleMaximum"], "status": "met" if assembly["winner"]["multiclassBrier"] <= thresholds["brierScore"]["cycleMaximum"] else "missed"}, "multiclassLogLoss": {"value": assembly["winner"]["multiclassLogLoss"], "threshold": thresholds["logLoss"]["cycleMaximum"], "status": "met" if assembly["winner"]["multiclassLogLoss"] <= thresholds["logLoss"]["cycleMaximum"] else "missed"}, "intervalCoverage80": {"value": coverage, "threshold": thresholds["intervalCoverage80"], "status": "met" if thresholds["intervalCoverage80"]["cycleMinimum"] <= coverage <= thresholds["intervalCoverage80"]["cycleMaximum"] else "missed"}, "finalPairCalibration": assembly["finalPair"]["calibration"], "regionalError": {"status": "unavailable", "reason": "no preregistered regional primary probability output in the frozen 2010 artefact"}, "contestType": {"status": "unavailable", "reason": "no preregistered contest-type partition is frozen for this single cycle"}}


def main() -> None:
    prediction, bundle, sealed = verify_sealed()
    boundary = {"outcomeBoundaryCrossedAfterPredictionAndComparatorVerification": True}
    # This is the first point at which target outcome files are read.
    actual_primary, statewide_actual, _ = primary_actual()
    outcomes = validate_outcomes(actual_primary)
    assembly = score_assembly(prediction, outcomes, actual_primary, statewide_actual)
    council = score_council(prediction, council_actual())
    complete_metrics = {"assembly": assembly, "council": council}
    comparators = score_comparators(bundle, outcomes, actual_primary, complete_metrics)
    criteria = json.loads(CRITERIA_PATH.read_text())
    score = {"schemaVersion": 1, "cycleId": "vic_la_2010", "modelVersion": "historical_replay_v2", "outcomesLoaded": True, "predictionSha256": sealed["predictionSha256"], "comparatorBundleSha256": sealed["comparatorBundleSha256"], "comparatorSpecSha256": sealed["comparatorSpecSha256"], "assembly": assembly, "council": council, "comparators": comparators, "thresholds": {"criteriaPath": str(CRITERIA_PATH.relative_to(REPO)), "criteriaSha256": sha_file(CRITERIA_PATH), "cycleLevelOnly": True, "completeBacktest": "unavailable-until-four-cycles", "probabilityCalibration": "unavailable-until-four-cycles", "cycleLevelAssessment": threshold_assessment(assembly, criteria)}}
    OUTCOME_AUDIT_PATH.write_text(json.dumps({"schemaVersion": 1, "cycleId": "vic_la_2010", "status": "scoring-only-outcomes-loaded-after-sealed-prediction-and-comparator-verification", "outcomesLoaded": True, "assemblyOutcomePath": str(ASSEMBLY_OUTCOME_PATH.relative_to(REPO)), "assemblyOutcomeSha256": sha_file(ASSEMBLY_OUTCOME_PATH), "assemblyDistricts": 88, "finalPairAvailableDistricts": assembly["finalPair"]["availableDistricts"], "finalPairUnavailableDistricts": assembly["finalPair"]["unavailableDistricts"], "sourceManifestPath": str(ASSEMBLY_MANIFEST_PATH.relative_to(REPO)), "sourceManifestSha256": sha_file(ASSEMBLY_MANIFEST_PATH), "candidatePrimaryPath": str(PRIMARY_PATH.relative_to(REPO)), "candidatePrimarySha256": sha_file(PRIMARY_PATH), "councilEvidenceAuditPath": str(COUNCIL_AUDIT_PATH.relative_to(REPO)), "councilPrimaryPath": str(COUNCIL_PRIMARY_PATH.relative_to(REPO)), "targetOutcomeDependency": True, "preElectionInputEligible": False, "productionAuthorisation": False}, indent=2) + "\n")
    score["scoreSha256"] = sha_json(score)
    SCORE_PATH.write_text(json.dumps(score, indent=2) + "\n")
    manifest = {"schemaVersion": 1, "cycleId": "vic_la_2010", "modelVersion": "historical_replay_v2", **sealed, "predictionPath": str(PRED_PATH.relative_to(REPO)), "comparatorBundlePath": str(BUNDLE_PATH.relative_to(REPO)), "comparatorSpecPath": str(SPEC_PATH.relative_to(REPO)), "assemblyOutcomePath": str(ASSEMBLY_OUTCOME_PATH.relative_to(REPO)), "assemblyOutcomeSha256": sha_file(ASSEMBLY_OUTCOME_PATH), "assemblySourceManifestPath": str(ASSEMBLY_MANIFEST_PATH.relative_to(REPO)), "assemblySourceManifestSha256": sha_file(ASSEMBLY_MANIFEST_PATH), "primaryArtefactPath": str(PRIMARY_PATH.relative_to(REPO)), "primaryArtefactSha256": sha_file(PRIMARY_PATH), "councilOutcomePaths": [str(COUNCIL_PRIMARY_PATH.relative_to(REPO)), str(COUNCIL_AUDIT_PATH.relative_to(REPO))], "councilOutcomeSha256": {str(COUNCIL_PRIMARY_PATH.relative_to(REPO)): sha_file(COUNCIL_PRIMARY_PATH), str(COUNCIL_AUDIT_PATH.relative_to(REPO)): sha_file(COUNCIL_AUDIT_PATH)}, "criteriaPath": str(CRITERIA_PATH.relative_to(REPO)), "criteriaSha256": sha_file(CRITERIA_PATH), "scoringCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(), **boundary, "forecastRegenerated": False, "scorePath": str(SCORE_PATH.relative_to(REPO)), "scoreSha256": score["scoreSha256"]}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"scorePath": str(SCORE_PATH.relative_to(REPO)), "scoreSha256": score["scoreSha256"], "manifestPath": str(MANIFEST_PATH.relative_to(REPO)), "outcomesLoaded": True, "finalPairAvailableDistricts": assembly["finalPair"]["availableDistricts"]}, indent=2))


if __name__ == "__main__":
    main()
