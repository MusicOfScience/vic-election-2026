import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

function readJson(path) {
  return JSON.parse(readFileSync(resolve(root, path), "utf8"));
}

function assert(condition, message) {
  if (!condition) throw new Error(`historical replay contract: ${message}`);
}

export function validateHistoricalReplayContract() {
  const config = readJson("model/config/historical-validation-cycles.json");
  const readiness = readJson("metadata/historical-replay-input-readiness.json");
  const expected = ["vic_la_2010", "vic_la_2014", "vic_la_2018", "vic_la_2022"];
  assert(config.status === "partial-unrunnable", "contract must remain explicitly partial until all inputs are present");
  assert(config.productionCompatible === false, "historical replay contract cannot authorise production");
  assert(Array.isArray(config.requiredOutputs) && config.requiredOutputs.includes("district-winners-and-probabilities"), "complete seat outputs are required");
  assert(config.leakageRules?.enforcePublicationDateCutoff === true, "publication cutoff enforcement is required");
  assert(config.leakageRules?.electionOutcomes === "scoring-only", "outcomes must remain scoring-only");
  assert(config.leakageRules?.postCutoffPolls === "forbidden", "post-cutoff polls must be forbidden");
  assert(config.leakageRules?.postCutoffCandidateEvidence === "forbidden", "post-cutoff candidate evidence must be forbidden");
  assert(config.leakageRules?.postCutoffBallotEvidence === "forbidden", "post-cutoff ballot evidence must be forbidden");
  assert(config.leakageRules?.postCutoffCensusEvidence === "forbidden", "post-cutoff census evidence must be forbidden");

  const cycles = config.cycles ?? [];
  assert(cycles.length === expected.length, "all four frozen cycles must be declared");
  assert(JSON.stringify(cycles.map((cycle) => cycle.id)) === JSON.stringify(expected), "cycle order must remain canonical");
  for (const cycle of cycles) {
    assert(Number.isSafeInteger(cycle.seed), `${cycle.id} must have a deterministic integer seed`);
    assert(/^\d{4}-\d{2}-\d{2}$/.test(cycle.electionDate), `${cycle.id} election date is invalid`);
    assert(/^\d{4}-\d{2}-\d{2}$/.test(cycle.informationCutoff), `${cycle.id} information cutoff is invalid`);
    assert(cycle.informationCutoff < cycle.electionDate, `${cycle.id} cutoff must precede election day`);
    assert(cycle.inputPolicy?.outcomesAvailableToModel === false, `${cycle.id} cannot expose outcomes to the model`);
    assert(cycle.inputPolicy?.outcomesAvailableForScoring === true, `${cycle.id} must retain scoring outcomes separately`);
    if (cycle.id === "vic_la_2018") {
      assert(cycle.runnable === true, "2018 must be runnable only after governed readiness passes");
      assert(Array.isArray(cycle.blockedBy) && cycle.blockedBy.length === 0, "2018 stale static blockers must be cleared");
    } else if (cycle.id === "vic_la_2022") {
      const state = readiness.cycles?.find((item) => item.cycleId === cycle.id);
      assert(state?.runnable === true, "2022 runnable state must derive from governed readiness");
      assert(cycle.runnable === true, "2022 must be runnable only after governed readiness passes");
      assert(Array.isArray(cycle.blockedBy) && cycle.blockedBy.length === 0, "2022 stale static blockers must be cleared");
      assert(cycle.certifyingPredictionFrozen === true && cycle.predictionArtefact, "2022 certifying prediction must be explicitly frozen");
    } else {
      assert(cycle.runnable === false, `${cycle.id} cannot be marked runnable before residual inputs are complete`);
      assert(Array.isArray(cycle.blockedBy) && cycle.blockedBy.length > 0, `${cycle.id} must disclose concrete blockers`);
    }
  }
  return {
    status: config.status,
    cycles: cycles.map((cycle) => ({ id: cycle.id, seed: cycle.seed, cutoff: cycle.informationCutoff, runnable: cycle.runnable, blockedBy: cycle.blockedBy })),
    runnableCycles: cycles.filter((cycle) => cycle.runnable).length,
    productionCompatible: config.productionCompatible,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) {
  console.log(JSON.stringify(validateHistoricalReplayContract(), null, 2));
}
