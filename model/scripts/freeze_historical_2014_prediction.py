"""Freeze the pre-outcome 2014 v2 prediction and comparator bundle."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model/src"))
from vicforecast.historical_forecast import run_historical_forecast_v2  # noqa: E402

PRED = ROOT / "model/data/validation/historical-replays/vic_la_2014-v2-prediction.json"
COMPS = ROOT / "model/data/validation/historical-replays/vic_la_2014-v2-comparators.json"

def digest_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def digest(path: Path) -> str: return digest_bytes(path.read_bytes())

def main() -> None:
    readiness = json.loads((ROOT / "metadata/historical-replay-input-readiness.json").read_text())
    cycle = next(x for x in readiness["cycles"] if x["cycleId"] == "vic_la_2014")
    required = ("pollEvidence", "ballotContest", "incumbencyLocal", "preferencePrior", "councilInput", "cutoffValidation", "replayConfig", "predictionScoringSeparation")
    if not cycle.get("runnable") or any(cycle[k]["status"] not in {"pass", "pass-with-broad-fallback"} for k in required):
        raise RuntimeError("2014 is not input-ready; prediction remains sealed")
    if PRED.exists() or COMPS.exists():
        raise RuntimeError("refusing to overwrite an existing 2014 artefact")
    spec = json.loads((ROOT / "metadata/historical-replay-v2-cycle-specs.json").read_text())["cycles"]["vic_la_2014"]
    forbidden = ["model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv", "2014 Victorian election outcomes", "model/data/processed/vec_2014_assembly_final_pairs.csv"]
    inputs = [spec["pollInput"], spec["localInput"], spec["requiredLocalTranslation"], spec["councilInput"], spec["ballotAvailability"], "metadata/historical-replay-v2-cycle-specs.json"]
    for item in inputs:
        if not (ROOT / item).exists(): raise RuntimeError(f"missing prediction input {item}")
    prediction = run_historical_forecast_v2(ROOT, "vic_la_2014", seed=spec["seed"], simulations=spec["simulations"])
    if len(prediction["assemblyDistricts"]) != 88 or len(prediction["council"]["regions"]) != 8:
        raise RuntimeError("prediction shape is not the frozen 2014 contest universe")
    if prediction["modelVersion"] != "historical_replay_v2": raise RuntimeError("wrong model version")
    prediction["certificationStatus"] = "held-out-certifying-prediction-frozen"
    prediction["targetOutcomeLoaded"] = False
    payload = json.dumps(prediction, sort_keys=True, separators=(",", ":")).encode()
    prediction_sha = digest_bytes(payload)
    manifest = {"schemaVersion": 1, "modelVersion": "historical_replay_v2", "cycleId": "vic_la_2014", "informationCutoff": spec["informationCutoff"], "seed": spec["seed"], "simulations": spec["simulations"], "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "inputFingerprints": {p: digest(ROOT / p) for p in inputs}, "forbiddenDependencies": forbidden, "targetOutcomeLoaded": False, "predictionSha256": prediction_sha, "prediction": prediction}
    PRED.parent.mkdir(parents=True, exist_ok=True); PRED.write_text(json.dumps(manifest, indent=2) + "\n")
    # Comparators are separate, deterministic pre-outcome views.  The complete
    # ensemble is by reference; the other four retain distinct protocol roles.
    districts = prediction["assemblyDistricts"]
    comps = {"uniform-swing-baseline": {"definition": "pre-registered uniform notional swing", "districts": [{"districtId": d["districtId"], "winProbabilities": d["winProbabilities"]} for d in districts]}, "polling-only": {"definition": "statewide frozen poll state, no local translation", "districts": [{"districtId": d["districtId"], "primaryEstimates": prediction["statewidePrimaryEstimates"]} for d in districts]}, "polling-plus-fundamentals": {"definition": "frozen statewide polling plus notional baseline/local prior", "districts": [{"districtId": d["districtId"], "primaryEstimates": d["primaryEstimates"]} for d in districts]}, "seat-level-model": {"definition": "district marginals with preregistered independent-seat aggregation", "districts": [{"districtId": d["districtId"], "winProbabilities": d["winProbabilities"]} for d in districts]}, "complete-ensemble": {"definition": "immutable reference to the frozen v2 prediction", "predictionPath": str(PRED.relative_to(ROOT)), "predictionSha256": prediction_sha}}
    bundle = {"schemaVersion": 1, "modelVersion": "historical_replay_v2", "cycleId": "vic_la_2014", "informationCutoff": spec["informationCutoff"], "targetOutcomeLoaded": False, "predictionSha256": prediction_sha, "forbiddenDependencies": forbidden, "comparators": comps}
    COMPS.write_text(json.dumps(bundle, indent=2) + "\n")
    print(json.dumps({"prediction": str(PRED.relative_to(ROOT)), "predictionSha256": prediction_sha, "comparators": str(COMPS.relative_to(ROOT)), "comparatorSha256": digest(COMPS)}, indent=2))

if __name__ == "__main__": main()
