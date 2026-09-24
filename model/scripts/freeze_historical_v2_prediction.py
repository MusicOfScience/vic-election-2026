"""Freeze the first certifying 2022 v2 prediction without loading outcomes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from vicforecast.historical_forecast import load_historical_cycle_spec, run_historical_forecast_v2


ROOT = Path(__file__).resolve().parents[1]
CYCLE = "vic_la_2022"
OUT = ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json"
BUNDLE = ROOT / "data/validation/historical-replays/vic_la_2022-v2-comparators.json"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def comparator_bundle(prediction: dict) -> dict:
    families = prediction["activeFamilies"]
    state = prediction["statewidePrimaryEstimates"]
    districts = prediction["assemblyDistricts"]
    uniform_rows = []
    polling_rows = []
    for row in districts:
        uniform_rows.append({"districtId": row["districtId"], "primaryEstimates": state, "method": "uniform-swing-no-local-pattern"})
        polling_rows.append({"districtId": row["districtId"], "primaryEstimates": state, "method": "polling-only-no-local-pattern"})
    return {
        "schemaVersion": 1,
        "modelVersion": "historical_replay_v2",
        "cycleId": CYCLE,
        "outcomesLoaded": False,
        "definitions": {
            "uniform_swing": "statewide poll state with no district local pattern",
            "polling_only": "statewide poll state and polling uncertainty only",
            "polling_plus_fundamentals": "statewide poll state plus governed AEC/VEC local pattern",
            "seat_level": "district-level governed local composition with independent seat draws",
            "complete_ensemble": "historical_replay_v2 shared polling, local, IRV and chamber simulation"
        },
        "predictions": {
            "uniform_swing": {"activeFamilies": families, "assemblyDistricts": uniform_rows},
            "polling_only": {"activeFamilies": families, "assemblyDistricts": polling_rows},
            "polling_plus_fundamentals": {"activeFamilies": families, "assemblyDistricts": districts, "method": "governed-local-pattern"},
            "seat_level": {"activeFamilies": families, "assemblyDistricts": districts, "method": "district-seat-simulation"},
            "complete_ensemble": {"activeFamilies": families, "assemblyDistricts": districts, "method": "historical_replay_v2-complete"}
        }
    }


def main() -> None:
    spec = load_historical_cycle_spec(ROOT, CYCLE)
    prediction = run_historical_forecast_v2(ROOT, CYCLE, seed=spec["seed"], simulations=spec["simulations"])
    inputs = [spec["pollInput"], spec["localInput"], spec["councilInput"], spec["ballotAvailability"], "metadata/historical-replay-v2-cycle-specs.json", "metadata/historical-party-family-mapping.json"]
    input_hashes = {path: digest_file((ROOT.parent / path) if not (ROOT / path).exists() else (ROOT / path)) for path in inputs}
    code_path = ROOT / "src/vicforecast/historical_forecast.py"
    prediction["versionManifest"] = {"modelVersion": "historical_replay_v2", "cycleSpec": spec, "inputFingerprints": input_hashes, "codeSha256": digest_file(code_path), "outcomesLoaded": False}
    payload = json.dumps(prediction, sort_keys=True, separators=(",", ":")).encode()
    manifest = {"cycleId": CYCLE, "modelVersion": "historical_replay_v2", "certificationStatus": "held-out-certifying-prediction-frozen", "informationCutoff": spec["informationCutoff"], "seed": spec["seed"], "simulations": spec["simulations"], "outcomesLoaded": False, "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True).strip(), "inputFingerprints": input_hashes, "predictionSha256": digest_bytes(payload), "prediction": prediction}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(manifest, indent=2) + "\n")
    bundle = comparator_bundle(prediction); bundle_bytes = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode(); bundle["bundleSha256"] = digest_bytes(bundle_bytes); BUNDLE.write_text(json.dumps(bundle, indent=2) + "\n")
    print(json.dumps({"predictionPath": str(OUT.relative_to(ROOT.parent)), "predictionSha256": manifest["predictionSha256"], "comparatorPath": str(BUNDLE.relative_to(ROOT.parent)), "comparatorSha256": bundle["bundleSha256"], "outcomesLoaded": False}))


if __name__ == "__main__":
    main()
