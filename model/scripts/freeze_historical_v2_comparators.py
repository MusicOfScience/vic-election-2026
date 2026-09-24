"""Freeze the preregistered 2022 v2 comparator predictions.

This is deliberately separate from ``freeze_historical_v2_prediction.py``.  The
certifying ensemble is already frozen; this script only builds the four
comparators from the same pre-cutoff information boundary and records the
ensemble by immutable reference.  It never opens an outcome artefact and fails
closed if the frozen prediction has changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
CYCLE = "vic_la_2022"
CUTOFF = "2022-11-25"
EXPECTED_PREDICTION_SHA = "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0"
PREDICTION_PATH = ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json"
LOCAL_PATH = ROOT / "data/validation/historical-replay-2022-local-inputs.csv"
VEC_PATH = ROOT / "data/processed/vec_2018_estimated_2022_boundary_2cp.csv"
SPEC_PATH = REPO / "metadata/historical-replay-v2-comparator-spec.json"
OUT_PATH = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators-v2.json"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_json(value: object) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load_prediction() -> tuple[dict, str]:
    manifest = json.loads(PREDICTION_PATH.read_text())
    prediction = manifest["prediction"]
    digest = sha_json(prediction)
    if digest != EXPECTED_PREDICTION_SHA or manifest.get("predictionSha256") != EXPECTED_PREDICTION_SHA:
        raise ValueError("frozen 2022 prediction hash mismatch; comparator freeze aborted")
    if manifest.get("outcomesLoaded") is not False or prediction.get("outcomesLoaded") is True:
        raise ValueError("outcome material is present in the certifying prediction")
    return prediction, digest


def read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def ballot_families(row: dict[str, str]) -> set[str]:
    return set(filter(None, row["ballot_active_families"].split(";")))


def normalise(values: dict[str, float], active: set[str]) -> dict[str, float]:
    usable = {key: max(0.0, float(value)) if key in active else 0.0 for key, value in values.items()}
    total = sum(usable.values())
    if total <= 0:
        raise ValueError("ballot mask removed every comparator family")
    return {key: value / total * 100.0 for key, value in usable.items()}


def top_pair(values: dict[str, float]) -> str:
    ranked = sorted(((v, k) for k, v in values.items() if v > 0), reverse=True)
    if len(ranked) < 2:
        return ranked[0][1] if ranked else ""
    return "-".join(sorted((ranked[0][1], ranked[1][1])))


def win_probabilities(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in values.values())
    if total <= 0:
        raise ValueError("cannot derive probabilities from empty comparator vector")
    return {key: max(0.0, value) / total for key, value in values.items()}


def row(district_id: str, district_name: str, values: dict[str, float], method: str, scope: str) -> dict:
    probabilities = win_probabilities(values)
    favoured = max(probabilities, key=probabilities.get)
    return {
        "districtId": district_id,
        "districtName": district_name,
        "primaryEstimates": {key: round(value, 10) for key, value in values.items()},
        "winProbabilities": {key: round(value, 10) for key, value in probabilities.items()},
        "likelyFinalPair": top_pair(values),
        "finalPairProbability": 1.0,
        "favouredParty": favoured,
        "method": method,
        "scope": scope,
    }


def seat_row(district_id: str, district_name: str, values: dict[str, float], perturb: float) -> dict:
    """Independent-seat approximation with the frozen broad preference fallback.

    This is intentionally simpler than the complete correlated IRV ensemble,
    but it still models a one-step transfer of non-major mass and a fixed
    district shock before deriving the independent seat marginal.
    """
    adjusted = dict(values)
    major = values.get("ALP", 0.0) + values.get("LIB_NAT", 0.0)
    non_major = max(0.0, 100.0 - major)
    if major > 0:
        adjusted["ALP"] += 0.15 * non_major * values.get("ALP", 0.0) / major
        adjusted["LIB_NAT"] += 0.15 * non_major * values.get("LIB_NAT", 0.0) / major
    adjusted["ALP"] = max(0.0, adjusted.get("ALP", 0.0) + perturb)
    adjusted["LIB_NAT"] = max(0.0, adjusted.get("LIB_NAT", 0.0) - perturb)
    probabilities = win_probabilities(adjusted)
    return {
        "districtId": district_id,
        "districtName": district_name,
        "primaryEstimates": {key: round(value, 10) for key, value in values.items()},
        "winProbabilities": {key: round(value, 10) for key, value in probabilities.items()},
        "likelyFinalPair": top_pair(adjusted),
        "finalPairProbability": 1.0,
        "favouredParty": max(probabilities, key=probabilities.get),
        "method": "seat-level-model",
        "scope": "independent district IRV marginals",
        "preferencePrior": "broad-fallback-v2",
        "irvApproximation": "single deterministic transfer step before independent seat marginal",
    }


def build_comparators(prediction: dict, local_rows: list[dict[str, str]], vec_rows: list[dict[str, str]]) -> dict[str, dict]:
    state = {key: float(value) for key, value in prediction["statewidePrimaryEstimates"].items()}
    # The polling observation is four-bucket.  ONP is intentionally absent from
    # the observed state and is only allocated by a local ballot-layer model.
    families = ["ALP", "LIB_NAT", "GRN", "ONP", "OTH_IND"]
    vec_by_id = {r["district_id"]: r for r in vec_rows}
    local_by_id = {r["district_id"]: r for r in local_rows}
    if set(vec_by_id) != set(local_by_id) or len(local_rows) != 87:
        raise ValueError("2022 comparator inputs must contain the same 87 districts")

    # Uniform swing preserves the VEC two-party margin and applies the common
    # statewide poll level.  No AEC district surface is read in this branch.
    major_total = state["ALP"] + state["LIB_NAT"]
    uniform_rows = []
    polling_rows = []
    fundamentals_rows = []
    seat_rows = []
    for district_id in sorted(local_by_id):
        local = local_by_id[district_id]
        active = ballot_families(local)
        vec = vec_by_id[district_id]
        tpp_alp = float(vec["estimated_2018_alp_tpp_share"]) / 100.0
        uniform_values = normalise({
            "ALP": major_total * tpp_alp,
            "LIB_NAT": major_total * (1.0 - tpp_alp),
            "GRN": state.get("GRN", 0.0),
            "ONP": 0.0,
            "OTH_IND": state.get("OTH_IND", 0.0),
        }, active)
        uniform_rows.append(row(district_id, local["district_name"], uniform_values, "uniform-swing-baseline", "ALP-vs-Coalition baseline plus common statewide poll level"))

        polling_values = normalise({
            "ALP": state.get("ALP", 0.0),
            "LIB_NAT": state.get("LIB_NAT", 0.0),
            "GRN": state.get("GRN", 0.0),
            "ONP": 0.0,
            "OTH_IND": state.get("OTH_IND", 0.0),
        }, active)
        polling_rows.append(row(district_id, local["district_name"], polling_values, "polling-only", "statewide poll state with ballot masks only"))

        # AEC values are relative contextual geography.  Blend their local
        # composition with the statewide poll; no target-election anchor is used.
        aec = {"ALP": float(local["aec_local_alp"]), "LIB_NAT": float(local["aec_local_lib_nat"]), "GRN": float(local["aec_local_grn"]), "ONP": float(local["aec_local_onp"]), "OTH_IND": float(local["aec_local_oth_ind"])}
        blended = {key: 0.62 * state.get(key, 0.0) + 0.38 * aec[key] * 100.0 for key in families}
        fundamentals_values = normalise(blended, active)
        fundamentals_rows.append(row(district_id, local["district_name"], fundamentals_values, "polling-plus-fundamentals", "statewide polling plus VEC/AEC pre-cutoff local pattern"))

        # Seat-level is an independent-district implementation: it uses the
        # same permitted inputs but applies a fixed, seed-derived district
        # perturbation and aggregates independent seat marginals.
        perturb = (int(sha_bytes(district_id.encode())[:8], 16) / 0xFFFFFFFF) - 0.5
        seat_values = dict(fundamentals_values)
        if "ALP" in active and "LIB_NAT" in active:
            shift = perturb * 1.6
            seat_values["ALP"] = max(0.0, seat_values["ALP"] + shift)
            seat_values["LIB_NAT"] = max(0.0, seat_values["LIB_NAT"] - shift)
            seat_values = normalise(seat_values, active)
        seat_rows.append(seat_row(district_id, local["district_name"], seat_values, perturb))

    def chamber(rows: list[dict]) -> dict[str, dict[str, float]]:
        means = {family: sum(item["winProbabilities"].get(family, 0.0) for item in rows) for family in families}
        return {family: {"mean": round(value, 10), "scope": "independent-seat-marginals"} for family, value in means.items()}

    forbidden = ["all 2022 outcome artefacts", "ASSEMBLY_2022_TARGET", "COUNCIL_2022_TARGET", "vec_2022_indicative_candidate_evidence.csv"]
    return {
        "uniform-swing-baseline": {"allowedInputs": ["model/data/processed/vec_2018_estimated_2022_boundary_2cp.csv", "model/data/validation/historical-replay-poll-observations.json", "district ballot masks"], "forbiddenInputs": forbidden, "activeFamilies": families, "assemblyDistricts": uniform_rows, "metricsAvailable": ["district-primary", "binary-ALP-event"], "council": {"status": "not-modelled", "reason": "uniform-swing comparator has no regional analogue"}},
        "polling-only": {"allowedInputs": ["model/data/validation/historical-replay-poll-observations.json", "district ballot masks"], "forbiddenInputs": forbidden + ["vec_2018_estimated_2022_boundary_2cp.csv", "AEC district surface"], "activeFamilies": families, "assemblyDistricts": polling_rows, "metricsAvailable": ["statewide-primary", "district-primary", "binary-ALP-event"], "council": {"status": "not-modelled", "reason": "polling-only comparator has no local regional input"}},
        "polling-plus-fundamentals": {"allowedInputs": ["model/data/processed/vec_2018_estimated_2022_boundary_2cp.csv", "model/data/validation/historical-replay-2022-local-inputs.csv", "model/data/validation/historical-replay-poll-observations.json"], "forbiddenInputs": forbidden, "activeFamilies": families, "assemblyDistricts": fundamentals_rows, "metricsAvailable": ["district-primary", "binary-ALP-event"], "council": {"status": "not-modelled", "reason": "comparator excludes full Council ensemble"}},
        "seat-level-model": {"allowedInputs": ["model/data/processed/vec_2018_estimated_2022_boundary_2cp.csv", "model/data/validation/historical-replay-2022-local-inputs.csv", "model/data/validation/historical-replay-poll-observations.json", "fixed pre-score uncertainty"], "forbiddenInputs": forbidden, "activeFamilies": families, "assemblyDistricts": seat_rows, "assemblySeatSummary": chamber(seat_rows), "chamberAggregation": "independent-seat-marginals", "metricsAvailable": ["district-primary", "winner", "seat-count"], "council": {"status": "not-modelled", "reason": "seat-level comparator is Assembly-only"}},
    }


def main() -> None:
    prediction, prediction_sha = load_prediction()
    local_rows = read_csv(LOCAL_PATH)
    vec_rows = read_csv(VEC_PATH)
    spec = json.loads(SPEC_PATH.read_text())
    if spec["cycleId"] != CYCLE or spec["informationCutoff"] != CUTOFF or spec["outcomesLoaded"] is not False:
        raise ValueError("comparator spec is not the frozen pre-outcome 2022 contract")
    comparators = build_comparators(prediction, local_rows, vec_rows)
    comparators["complete-ensemble"] = {
        "reference": {
            "predictionPath": "model/data/validation/historical-replays/vic_la_2022-v2-prediction.json",
            "predictionSha256": prediction_sha,
            "frozenPrediction": True,
            "valuesCopied": False,
        },
        "metricsAvailable": ["statewide-primary", "district-primary", "winner", "final-pair", "assembly-seats", "council"],
        "council": {"status": "available", "source": "frozen-certifying-prediction"},
    }
    bundle = {
        "schemaVersion": 2,
        "modelVersion": "historical_replay_v2",
        "cycleId": CYCLE,
        "informationCutoff": CUTOFF,
        "outcomesLoaded": False,
        "comparatorSpecPath": "metadata/historical-replay-v2-comparator-spec.json",
        "comparatorSpecSha256": sha_file(SPEC_PATH),
        "certifyingPredictionPath": "model/data/validation/historical-replays/vic_la_2022-v2-prediction.json",
        "certifyingPredictionSha256": prediction_sha,
        "forbiddenInputs": ["all 2022 outcome artefacts", "ASSEMBLY_2022_TARGET", "COUNCIL_2022_TARGET", "vec_2022_indicative_candidate_evidence.csv", "2018-to-2022 observed outcome transitions"],
        "comparators": comparators,
    }
    bundle["bundleSha256"] = sha_json(bundle)
    OUT_PATH.write_text(json.dumps(bundle, indent=2) + "\n")
    print(json.dumps({"path": str(OUT_PATH.relative_to(REPO)), "bundleSha256": bundle["bundleSha256"], "predictionSha256": prediction_sha, "outcomesLoaded": False}))


if __name__ == "__main__":
    main()
