#!/usr/bin/env python3
"""Run the repaired adapter as a clearly non-certifying 2018 diagnostic."""
import hashlib, json
from pathlib import Path
from vicforecast.historical_forecast import run_historical_2018_forecast_v2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json"

def main() -> None:
    result = run_historical_2018_forecast_v2(ROOT / "model", seed=20181123, simulations=1200)
    result["diagnosticReason"] = "2018 outcomes were already observed by v1; this output is post-hoc implementation verification, not held-out evidence"
    payload = json.dumps(result, sort_keys=True, indent=2).encode() + b"\n"
    OUT.write_bytes(payload)
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "sha256": hashlib.sha256(payload).hexdigest(), "modelVersion": result["modelVersion"]}))

if __name__ == "__main__":
    main()
