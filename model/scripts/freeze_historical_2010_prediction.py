"""Freeze the final 2010 certifying prediction without opening outcomes."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vicforecast.historical_forecast import load_historical_cycle_spec, run_historical_forecast_v2


ROOT = Path(__file__).resolve().parents[2]
CYCLE = "vic_la_2010"
OUT = ROOT / "model/data/validation/historical-replays/vic_la_2010-v2-prediction.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    readiness = json.loads((ROOT / "metadata/historical-replay-input-readiness.json").read_text())
    cycle = next(row for row in readiness["cycles"] if row["cycleId"] == CYCLE)
    required = ("pollEvidence", "ballotContest", "incumbencyLocal", "preferencePrior", "councilInput", "cutoffValidation", "replayConfig", "predictionScoringSeparation")
    if not cycle.get("runnable") or any(cycle[key]["status"] not in {"pass", "pass-with-broad-fallback"} for key in required):
        raise RuntimeError("2010 is not input-ready; prediction remains sealed")
    if OUT.exists():
        raise RuntimeError("refusing to overwrite an existing 2010 prediction")
    spec = load_historical_cycle_spec(ROOT, CYCLE)
    inputs = [
        spec["pollInput"], spec["localInput"], spec["councilInput"],
        spec["ballotAvailability"], "metadata/historical-fixed-fact-reconstruction-policy.json",
        "metadata/historical-replay-2010-ballot-availability-audit.json",
        "metadata/historical-replay-v2-cycle-specs.json",
    ]
    for item in inputs:
        if not (ROOT / item).exists():
            raise RuntimeError(f"missing prediction input: {item}")
    prediction = run_historical_forecast_v2(ROOT, CYCLE, seed=spec["seed"], simulations=spec["simulations"])
    if len(prediction["assemblyDistricts"]) != 88 or len(prediction["council"]["regions"]) != 8:
        raise RuntimeError("2010 prediction shape is not 88 Assembly districts and 8 Council regions")
    if prediction["modelVersion"] != "historical_replay_v2" or prediction["activeFamilies"] != ["ALP", "LIB_NAT", "GRN", "OTH_IND"]:
        raise RuntimeError("2010 prediction family/model contract mismatch")
    if any(sum(float(v) for v in district["winProbabilities"].values()) < 0.999999 for district in prediction["assemblyDistricts"]):
        raise RuntimeError("2010 district probabilities do not reconcile")
    if any(set(d["winProbabilities"]) - set(spec["activeFamilies"]) for d in prediction["assemblyDistricts"]):
        raise RuntimeError("2010 prediction contains an ungoverned family")
    prediction["certificationStatus"] = "held-out-certifying-prediction-frozen"
    prediction["targetOutcomeLoaded"] = False
    prediction["outcomesLoaded"] = False
    prediction["versionManifest"] = {
        "modelVersion": "historical_replay_v2",
        "cycleSpec": spec,
        "inputFingerprints": {item: sha(ROOT / item) for item in inputs},
        "codeSha256": sha(ROOT / "model/src/vicforecast/historical_forecast.py"),
        "outcomesLoaded": False,
        "forbiddenInputs": ["model/data/processed/vec_2006_2010_same_boundary_tpp_swing.csv", "model/data/processed/vec_2010_assembly_candidate_primaries.csv", "2010 winner/preference/swing artefacts"],
    }
    payload_sha = canonical_sha(prediction)
    manifest = {
        "schemaVersion": 1,
        "modelVersion": "historical_replay_v2",
        "cycleId": CYCLE,
        "informationCutoff": spec["informationCutoff"],
        "seed": spec["seed"],
        "simulations": spec["simulations"],
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "inputFingerprints": {item: sha(ROOT / item) for item in inputs},
        "forbiddenDependencies": prediction["versionManifest"]["forbiddenInputs"],
        "targetOutcomeLoaded": False,
        "outcomesLoaded": False,
        "predictionSha256": payload_sha,
        "prediction": prediction,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"predictionPath": str(OUT.relative_to(ROOT)), "predictionSha256": payload_sha, "outcomesLoaded": False}, indent=2))


if __name__ == "__main__":
    main()
