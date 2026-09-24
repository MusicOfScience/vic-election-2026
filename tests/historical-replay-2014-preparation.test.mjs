import test from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildHistoricalLocalInputs } from "../scripts/build-historical-local-inputs.mjs";
import { buildApprovedHistoricalPollInput2014 } from "../scripts/apply-approved-historical-poll-review.mjs";

const readJson = (path) => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url), "utf8"));

test("2014 is selected by pre-score completeness and remains prediction-fail-closed", () => {
  const selection = readJson("metadata/historical-replay-next-cycle-selection.json");
  const audit = readJson("metadata/historical-replay-2014-input-audit.json");
  assert.equal(selection.selectedCycle, "vic_la_2014");
  assert.match(selection.reason, /pre-score evidence completeness/i);
  assert.equal(audit.predictionGenerated, false);
  assert.equal(audit.targetOutcomeLoaded, false);
  assert.equal(audit.polling.approvedReplayObservations, 4);
  assert.equal(audit.polling.independentFamiliesApproved, 2);
});

test("2014 Roy Morgan cases record the explicit owner approval and promote only through the governed builder", () => {
  const ids = [
    "metadata/historical-poll-reuse-case-2014-roymorgan-2014-10-01.json",
    "metadata/historical-poll-reuse-case-2014-roymorgan-2014-10-27.json",
    "metadata/historical-poll-reuse-case-2014-roymorgan-2014-11-10.json",
  ];
  for (const path of ids) {
    const item = readJson(path);
    assert.equal(item.cycleId, "vic_la_2014");
    assert.equal(item.gates.provenance.passed, true);
    assert.equal(item.gates.methodologicalAdequacy.passed, true);
    assert.equal(item.ownerReviewStatus, "approved-for-historical-replay");
    assert.equal(item.replayEligible, true);
    assert.equal(item.notFromQuarantinedDataset, true);
  }
});

test("the 2010-to-2014 outcome transition remains forbidden prediction input", () => {
  const audit = readJson("metadata/historical-replay-2014-input-audit.json");
  assert.equal(audit.localAssembly.targetOutcomeTransitionRole, "scoring-only-forbidden-in-prediction");
  assert.ok(audit.localAssembly.predictionSafeTppBaseline);
  const sandbox = join(tmpdir(), "vic-election-2014-local-input-test");
  mkdirSync(join(sandbox, "model/data/processed"), { recursive: true });
  writeFileSync(join(sandbox, "model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv"), "district_id,alp_tpp_share_2014,alp_tpp_swing_2010_2014\nexample,50,4\n");
  assert.throws(() => buildHistoricalLocalInputs("vic_la_2014", sandbox), /forbidden target-outcome-derived local input/i);
});

test("2014 poll promotion reaches the fixed two-family sufficiency rule after Essential approval", () => {
  const promoted = buildApprovedHistoricalPollInput2014();
  const assessment = readJson("metadata/historical-poll-2014-second-family-assessment.json");
  const essential = readJson("metadata/historical-poll-reuse-case-2014-essential-2014-05.json");
  assert.equal(promoted.observations.length, 4);
  assert.equal(promoted.independentSourceFamilies, 2);
  assert.equal(promoted.sufficiency.status, "pass");
  assert.equal(assessment.status, "second-family-approved-and-promoted");
  assert.equal(essential.replayEligible, true);
  assert.equal(essential.ownerReviewStatus, "approved-for-historical-replay");
  assert.deepEqual(essential.modelPrimaryShares, { LIB_NAT: 38, ALP: 40, GRN: 10, OTH_IND: 12 });
});

test("2010 and 2014 readiness reasons remain cycle-scoped", () => {
  const readiness = readJson("metadata/historical-replay-input-readiness.json");
  const c2010 = readiness.cycles.find((cycle) => cycle.cycleId === "vic_la_2010");
  const c2014 = readiness.cycles.find((cycle) => cycle.cycleId === "vic_la_2014");
  assert.doesNotMatch(c2010.pollEvidence.reason, /Roy Morgan|2014 geography|2010-to-2014/);
  assert.match(c2014.pollEvidence.reason, /Roy Morgan|Essential/);
  assert.match(c2014.councilInput.reason, /2014 Council/);
});

test("prediction-safe 2014 baseline and Council prior are complete without target outcomes", () => {
  const baseline = readJson("metadata/historical-replay-2014-baseline-audit.json");
  const assembly = readFileSync(new URL("../model/data/validation/historical-replay-2014-assembly-notional-baseline.csv", import.meta.url), "utf8").trim().split("\n");
  const council = readFileSync(new URL("../model/data/validation/historical-replay-2014-council-prior.csv", import.meta.url), "utf8").trim().split("\n");
  assert.equal(baseline.assembly.status, "pass-for-notional-margin-anchor");
  assert.equal(assembly.length, 89);
  assert.equal(council.length, 9);
  assert.doesNotMatch(assembly[0], /2014_result|swing/i);
  assert.doesNotMatch(assembly.slice(1).join("\n"), /vec_2010_2014|alp_tpp_share_2014|swing/i);
  assert.equal(baseline.council.regions, 8);
});

test("2014 crosswalk rebuild remains fail-closed when the original raw inputs are absent", () => {
  const audit = readJson("metadata/historical-replay-2014-crosswalk-source-audit.json");
  assert.equal(audit.status, "blocked-original-raw-inputs-absent");
  assert.equal(audit.expectedInputs.length, 4);
  assert.equal(audit.expectedInputs.every((input) => input.status === "missing-locally" && input.path === null && input.sha256 === null), true);
  assert.equal(audit.duplicateIdentityCheck.status, "not-applicable-no-copies-found");
  assert.equal(audit.rebuildContract.targetElectionOutcomesUsed, false);
  assert.deepEqual(audit.rebuildContract.forbiddenInputs, ["model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv"]);
  const baseline = readJson("metadata/historical-replay-2014-baseline-audit.json");
  assert.equal(baseline.assemblyFamilyTranslation.status, "blocked");
  assert.equal(baseline.assemblyFamilyTranslation.sourceAudit, "metadata/historical-replay-2014-crosswalk-source-audit.json");
});

test("2014 ballot availability uses the cutoff-safe family mask and remains outcome-isolated", () => {
  const audit = readJson("metadata/historical-replay-2014-ballot-availability-audit.json");
  assert.equal(audit.cycleId, "vic_la_2014");
  assert.equal(audit.status, "pass-cutoff-safe-family-mask");
  assert.equal(audit.targetOutcomeUse, "forbidden");
  assert.equal(audit.oneNation.status, "verified-unavailable");
  assert.equal(audit.candidateAvailabilitySources.some((source) => source.cutoffSafe === true), true);
  const mask = readFileSync(new URL("../model/data/validation/historical-replay-2014-ballot-mask.csv", import.meta.url), "utf8").trim().split("\n");
  assert.equal(mask.length, 89);
  const hawthorn = mask.find((row) => row.includes('","Hawthorn","'));
  assert.ok(hawthorn);
  assert.doesNotMatch(hawthorn, /OTH_IND/);
  assert.match(mask.find((row) => row.includes("Albert Park")), /OTH_IND/);
});

test("sealed 2018 and 2022 evidence is not rewritten while preparing 2014", () => {
  const v1 = readJson("model/data/validation/historical-replays/vic_la_2018-prediction.json");
  const v2 = readJson("model/data/validation/historical-replays/vic_la_2022-v2-prediction.json");
  const score = readJson("model/data/validation/historical-replays/vic_la_2022-v2-score.json");
  assert.equal(v1.predictionSha256, "424552f6ad8fe362044543bb966d2642e34267c32a89b44c47ff390037a4c115");
  assert.equal(v2.predictionSha256, "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0");
  assert.equal(score.predictionSha256, v2.predictionSha256);
});
