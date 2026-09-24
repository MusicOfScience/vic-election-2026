import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { buildApprovedHistoricalPollInput } from "./apply-approved-historical-poll-review.mjs";
import { buildHistoricalCouncilInputs } from "./build-historical-council-inputs.mjs";
import { buildHistoricalLocalInputs } from "./build-historical-local-inputs.mjs";

const root = resolve(new URL("..", import.meta.url).pathname);
const read = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));

export function validateHistoricalReplayInputReadiness() {
  const readiness = read("metadata/historical-replay-input-readiness.json");
  const sparse = read("metadata/historical-poll-sufficiency-policy.json");
  const generated = buildApprovedHistoricalPollInput();
  const canonical = read("model/data/validation/historical-replay-poll-observations.json");
  const targeted = read("metadata/historical-poll-targeted-recovery-2018.json");
  const local = buildHistoricalLocalInputs("vic_la_2018");
  const council = buildHistoricalCouncilInputs("vic_la_2018");
  if (readiness.cycles.length !== 4 || readiness.runnableCycles !== 0 || readiness.archiveCompleteIsNotRequiredForRunnable !== true) throw new Error("historical replay readiness: cycle inventory is unsafe");
  if (sparse.minimumEligibleObservations !== 3 || sparse.minimumIndependentSourceFamilies !== 2 || !sparse.decisionBeforeScores || sparse.scoreDependentTuning) throw new Error("historical replay readiness: sparse-poll rule is not preregistered");
  if (generated.observations.length !== 3 || canonical.observations.length !== 3 || canonical.independentSourceFamilies !== 1) throw new Error("historical replay readiness: approved Essential input is incomplete");
  if (canonical.observations.some((row) => !row.replayEligible || row.reuseBasis !== "independently_reconstructed_factual_observation" || row.ownerReviewId !== canonical.ownerReviewId)) throw new Error("historical replay readiness: approved input lost its governance boundary");
  const cycle2018 = readiness.cycles.find((cycle) => cycle.cycleId === "vic_la_2018");
  if (cycle2018?.pollEvidence.status !== "blocked" || !cycle2018.pollEvidence.reason.includes("1 independent source family")) throw new Error("historical replay readiness: 2018 sparse-poll blocker is missing");
  if (targeted.status !== "blocked-source-fields-unavailable" || targeted.replayEligible || targeted.missingRequiredFields.length < 1) throw new Error("historical replay readiness: targeted second-family recovery was overstated");
  if (local.status !== "pass" || council.status !== "pass-with-broad-fallback") throw new Error("historical replay readiness: governed historical fallback inputs are not assembled");
  if (local.inputPath.includes("2014_2018") || local.forbiddenPredictionInput === local.inputPath) throw new Error("historical replay readiness: target outcome file leaked into local input");
  if (readiness.modelImpact.forecast2026 || readiness.modelImpact.productionAuthorisation || canonical.modelImpact.forecast2026 || canonical.modelImpact.productionAuthorisation) throw new Error("historical replay readiness: model impact boundary failed");
  return { cycles: readiness.cycles.length, approvedReplayObservations: canonical.observations.length, runnableCycles: readiness.runnableCycles };
}

if (process.argv[1]?.endsWith("validate-historical-replay-input-readiness.mjs")) console.log(JSON.stringify(validateHistoricalReplayInputReadiness()));
