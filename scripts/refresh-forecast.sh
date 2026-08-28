#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="${project_root}/model/src${PYTHONPATH:+:${PYTHONPATH}}"

run_forecast=1
run_model_export=1
run_polls=1
run_provenance=1
if [[ "${1:-}" == "--changed-since" ]]; then
  base_ref="${2:?usage: refresh-forecast.sh --changed-since BASE_REF}"
  run_forecast=0; run_model_export=0; run_polls=0; run_provenance=0
  while IFS= read -r changed_path; do
    case "${changed_path}" in
      model/src/*|model/config/*|model/data/*|model/scripts/*)
        run_forecast=1; run_model_export=1; run_provenance=1
        [[ "${changed_path}" == *poll* || "${changed_path}" == *upper_house* ]] && run_polls=1
        ;;
      scripts/generate-model-output.mjs) run_model_export=1; run_provenance=1 ;;
      scripts/generate-poll-data.mjs|app/poll-data.generated.ts) run_polls=1; run_provenance=1 ;;
      metadata/sources.json|scripts/generate-source-provenance.mjs|app/data.generated.ts|app/booth-data.generated.ts|app/historical-data.generated.ts) run_provenance=1 ;;
    esac
  done < <(git -C "${project_root}" diff --name-only "${base_ref}"...HEAD)
fi

if [[ "${run_forecast}" == "1" ]]; then python3 "${project_root}/model/scripts/run_experimental_forecast.py" --root "${project_root}/model"; fi
if [[ "${run_model_export}" == "1" ]]; then node "${project_root}/scripts/generate-model-output.mjs" "${project_root}/model"; fi
if [[ "${run_polls}" == "1" ]]; then node "${project_root}/scripts/generate-poll-data.mjs"; fi
if [[ "${run_provenance}" == "1" ]]; then node "${project_root}/scripts/generate-source-provenance.mjs"; fi
node "${project_root}/scripts/check-release-readiness.mjs"
echo "Deterministic forecast artefacts regenerated. Review the Git diff before release."
