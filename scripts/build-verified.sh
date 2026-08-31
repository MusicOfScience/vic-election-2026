#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${SITES_ENV_READY:-}" != "1" ]]; then
  exec "${script_dir}/sites-env.sh" -- "$0" "$@"
fi

command -v timeout || {
  echo "build-verified.sh requires GNU timeout." >&2
  exit 69
}

vinext="${SITES_PROJECT_ROOT}/node_modules/.bin/vinext"
if [[ ! -x "${vinext}" ]]; then
  echo "vinext is unavailable. Run npm run install:ci and wait for it to finish before building." >&2
  exit 69
fi

echo "Running bounded vinext build..."
node "${SITES_PROJECT_ROOT}/scripts/generate-model-output.mjs" "${SITES_PROJECT_ROOT}/model" --check
node "${SITES_PROJECT_ROOT}/scripts/generate-poll-data.mjs" --check
node "${SITES_PROJECT_ROOT}/scripts/generate-source-provenance.mjs" --check
node "${SITES_PROJECT_ROOT}/scripts/check-release-readiness.mjs" --check
node "${SITES_PROJECT_ROOT}/scripts/build-candidate-review-dossier.mjs" --check
node "${SITES_PROJECT_ROOT}/scripts/apply-approved-candidate-review.mjs" --check
node "${SITES_PROJECT_ROOT}/scripts/check-staged-poll-shadow.mjs"
timeout \
  --signal=TERM \
  --kill-after="${SITES_BUILD_KILL_AFTER:-10s}" \
  "${SITES_BUILD_TIMEOUT:-3m}" \
  "${vinext}" build
