import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const readJson = (path) => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url), "utf8"));

test("2010 selection is evidence-completeness based and remains pre-score", () => {
  const selection = readJson("metadata/historical-replay-next-cycle-selection.json");
  assert.equal(selection.selectedCycle, "vic_la_2010");
  assert.match(selection.reason, /pre-score evidence completeness/i);
  assert.equal(selection.candidates.vic_la_2010.automatedPassObservations, 3);
  assert.equal(selection.candidates.vic_la_2010.independentFamilies, 2);
});

test("2006 Assembly prior is complete, varied and does not use the 2006-2010 transition", () => {
  const rows = readFileSync(new URL("../model/data/processed/vec_2006_assembly_family_primaries.csv", import.meta.url), "utf8").trim().split("\n");
  const audit = readJson("metadata/historical-replay-2010-input-audit.json");
  assert.equal(rows.length, 353);
  assert.equal(audit.sameBoundary.status, "verified");
  assert.equal(audit.priorAssembly.districts, 88);
  assert.equal(audit.priorAssembly.targetOutcomeDependency, false);
  assert.ok(audit.forbiddenPredictionInputs.some((path) => path.includes("vec_2006_2010_same_boundary_tpp_swing")));
  assert.doesNotMatch(rows.join("\n"), /vec_2006_2010_same_boundary_tpp_swing|alp_tpp_share_2010|alp_tpp_swing_2006_2010/i);
});

test("2010 local and Council priors are prior-only and structurally complete", () => {
  const local = readFileSync(new URL("../model/data/validation/historical-replay-2010-local-inputs.csv", import.meta.url), "utf8").trim().split("\n");
  const mask = readFileSync(new URL("../model/data/validation/historical-replay-2010-ballot-mask.csv", import.meta.url), "utf8").trim().split("\n");
  const council = readFileSync(new URL("../model/data/validation/historical-replay-2010-council-prior.csv", import.meta.url), "utf8").trim().split("\n");
  assert.equal(local.length, 89);
  assert.equal(mask.length, 89);
  assert.equal(council.length, 33);
  assert.doesNotMatch(local.join("\n"), /vec_2006_2010|2010_result|swing/i);
  assert.doesNotMatch(council.join("\n"), /2010_result|winner|count_sequence/i);
  assert.ok(new Set(local.slice(1).map((row) => row.split(",").slice(7, 11).join(","))).size > 1);
  assert.doesNotMatch(mask.join("\n"), /unknown-pending-verification/);
  assert.match(mask[0], /ballot_active_families/);
  assert.equal(mask.length, 89);
});

test("2010 poll cases are explicitly owner-approved and source-family diverse", () => {
  const input = readJson("model/data/validation/historical-replay-2010-poll-observations.json");
  const review = readJson("metadata/historical-poll-reuse-review-2010.json");
  assert.equal(input.automatedPassObservationCount, 3);
  assert.equal(input.approvedObservationCount, 3);
  assert.equal(input.independentSourceFamilies, 2);
  assert.equal(new Set(input.observations.map((row) => row.sourceFamily)).size, 2);
  assert.equal(input.observations.every((row) => row.replayEligible === true), true);
  assert.equal(review.status, "approved-for-historical-replay");
});

test("2010 readiness is runnable and sealed without outcomes", () => {
  const readiness = readJson("metadata/historical-replay-input-readiness.json");
  const state = readiness.cycles.find((cycle) => cycle.cycleId === "vic_la_2010");
  const audit = readJson("metadata/historical-replay-2010-input-audit.json");
  assert.equal(state.runnable, true);
  assert.equal(state.pollEvidence.status, "pass");
  assert.equal(state.ballotContest.status, "pass");
  assert.equal(state.incumbencyLocal.status, "pass");
  assert.equal(state.councilInput.status, "pass-with-broad-fallback");
  assert.equal(audit.predictionFrozen, true);
  assert.equal(audit.outcomesLoaded, false);
  assert.equal(audit.predictionPath, "model/data/validation/historical-replays/vic_la_2010-v2-prediction.json");
});

test("2010 ballot audit records the fixed-fact reconstruction route and preserves failed archive attempts", () => {
  const audit = readJson("metadata/historical-replay-2010-ballot-availability-audit.json");
  assert.equal(audit.status, "pass-fixed-fact-reconstruction");
  assert.equal(audit.summarySource.assemblyDistricts, 88);
  assert.equal(audit.summarySource.assemblyCandidates, 502);
  assert.equal(audit.districtSource.archiveCaptureBeforeCutoffAfterNominations, false);
  assert.equal(audit.fixedFactReconstruction.reconstruction.targetOutcomeDependency, false);
  assert.equal(audit.districtCount, 88);
  assert.equal(audit.finalMask.othIndActiveDistricts, 86);
  assert.equal(audit.finalMask.othIndInactiveDistricts, 2);
  assert.equal(audit.targetOutcomeDependency, false);
  const pandora = audit.archiveRoutesChecked.find((route) => route.nlaIdentifier === "nla.arc-123701");
  assert.ok(pandora);
  assert.equal(pandora.postNominationBeforeCutoff, false);
  assert.equal(pandora.captureTimestampProven, false);
  assert.equal(pandora.coverage, 0);
});

test("2010 fixed-fact candidate reconstruction is minimal and reconciles to the nomination summary", () => {
  const rows = readFileSync(new URL("../model/data/validation/historical-replay-2010-fixed-fact-candidate-slate.csv", import.meta.url), "utf8").trim().split("\n");
  const policy = readJson("metadata/historical-fixed-fact-reconstruction-policy.json");
  assert.equal(rows.length, 503);
  assert.match(rows[0], /district_id/);
  assert.doesNotMatch(rows.join("\n"), /first_preference|winner|elected|swing|preference_count/i);
  assert.ok(policy.conditions.includes("target outcome values are not consulted or imported"));
  assert.equal(policy["2010Application"].reconstructionSource.resultFieldsRead, false);
});

test("2010 certifying prediction and comparator bundle are frozen before outcomes", () => {
  const prediction = readJson("model/data/validation/historical-replays/vic_la_2010-v2-prediction.json");
  const bundle = readJson("model/data/validation/historical-replays/vic_la_2010-v2-comparators-v2.json");
  assert.equal(prediction.outcomesLoaded, false);
  assert.equal(prediction.targetOutcomeLoaded, false);
  assert.equal(prediction.prediction.certificationStatus, "held-out-certifying-prediction-frozen");
  assert.equal(prediction.predictionSha256, "3d23e92d8aa0d8d4c6e522bbc07f529d614653c5d20aa68a952a96704804fd5d");
  assert.equal(bundle.outcomesLoaded, false);
  assert.equal(bundle.bundleSha256, "a5e464f8d84ba7cdc4a198df43006eb64824f4dc71c1d789ce55bffbcbd76b13");
  assert.deepEqual(Object.keys(bundle.comparators).sort(), ["complete-ensemble", "polling-only", "polling-plus-fundamentals", "seat-level-model", "uniform-swing-baseline"]);
  assert.equal(bundle.comparators["complete-ensemble"].reference.valuesCopied, false);
  const arrays = ["uniform-swing-baseline", "polling-only", "polling-plus-fundamentals", "seat-level-model"].map((name) => JSON.stringify(bundle.comparators[name].assemblyDistricts));
  assert.equal(new Set(arrays).size, 4);
});
