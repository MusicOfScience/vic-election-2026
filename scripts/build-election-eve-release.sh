#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
cd "$root"
# Build from the tracked model inputs plus the recorded owner-approved waves.
prior="$(node -p 'JSON.parse(require("node:fs").readFileSync("metadata/election-eve-release-2026-11-27.json","utf8")).priorReleaseCommit')"
git archive "$prior" model metadata scripts | tar -x -C "$stage"
cp "$root/metadata/election-eve-release-2026-11-27.json" "$stage/metadata/"
mkdir -p "$stage/app"
cd "$stage"
export PYTHONPATH="$stage/model/src"
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, "model/scripts")
from run_current_evidence_shadow import _scenario_registry

review = json.loads(Path("metadata/election-eve-poll-review-2026-11-27.json").read_text())
release = json.loads(Path("metadata/election-eve-release-2026-11-27.json").read_text())
records = [row for row in review["polls"] if row["id"] in release["admittedPollIds"]]
assert len(records) == len(release["admittedPollIds"]) == 3
processed = Path("model/data/processed")
event_path = processed / "poll_events_seed.csv"
estimate_path = processed / "poll_estimates_seed.csv"
events, estimates = _scenario_registry(pd.read_csv(event_path), pd.read_csv(estimate_path), records)
events.loc[events.poll_id.isin(release["admittedPollIds"]), "notes"] = "Owner-approved election-eve experimental release."
estimates.loc[estimates.poll_id.isin(release["admittedPollIds"]), "notes"] = "Owner-approved election-eve experimental release."
events.to_csv(event_path, index=False)
estimates.to_csv(estimate_path, index=False)
config_path = Path("model/config/experimental_forecast.yml")
config = yaml.safe_load(config_path.read_text())
config["as_of"] = release["forecastDate"]
config_path.write_text(yaml.safe_dump(config, sort_keys=False))
PY
python3 model/scripts/run_experimental_forecast.py
python3 model/scripts/build_assembly_vote_diagnostics.py
python3 model/scripts/build_polling_replay.py
node scripts/generate-model-output.mjs
node scripts/generate-poll-data.mjs
for artefact in model-output.generated.ts poll-data.generated.ts assembly-vote-diagnostics.generated.json polling-replay.generated.json; do
  if [[ "${1:-}" == "--check" ]]; then
    cmp "app/$artefact" "$root/app/election-eve-release/$artefact"
  else
    mkdir -p "$root/app/election-eve-release"
    cp "app/$artefact" "$root/app/election-eve-release/$artefact"
  fi
done
