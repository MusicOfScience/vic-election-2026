import test from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildHistoricalLocalInputs } from "../scripts/build-historical-local-inputs.mjs";

const readJson = (path) => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url), "utf8"));

test("2014 is selected by pre-score completeness and remains fail-closed", () => {
  const selection = readJson("metadata/historical-replay-next-cycle-selection.json");
  const audit = readJson("metadata/historical-replay-2014-input-audit.json");
  assert.equal(selection.selectedCycle, "vic_la_2014");
  assert.match(selection.reason, /pre-score evidence completeness/i);
  assert.equal(audit.predictionGenerated, false);
  assert.equal(audit.targetOutcomeLoaded, false);
  assert.equal(audit.polling.approvedReplayObservations, 0);
});

test("2014 Roy Morgan cases are governed but cannot auto-promote", () => {
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
    assert.equal(item.ownerReviewStatus, "awaiting-project-owner-approval");
    assert.equal(item.replayEligible, false);
    assert.equal(item.notFromQuarantinedDataset, true);
  }
});

test("the 2010-to-2014 outcome transition remains forbidden prediction input", () => {
  const audit = readJson("metadata/historical-replay-2014-input-audit.json");
  assert.equal(audit.localAssembly.targetOutcomeTransitionRole, "scoring-only-forbidden-in-prediction");
  assert.equal(audit.localAssembly.predictionSafeTppBaseline, null);
  const sandbox = join(tmpdir(), "vic-election-2014-local-input-test");
  mkdirSync(join(sandbox, "model/data/processed"), { recursive: true });
  writeFileSync(join(sandbox, "model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv"), "district_id,alp_tpp_share_2014,alp_tpp_swing_2010_2014\nexample,50,4\n");
  assert.throws(() => buildHistoricalLocalInputs("vic_la_2014", sandbox), /forbidden target-outcome-derived local input/i);
});

test("sealed 2018 and 2022 evidence is not rewritten while preparing 2014", () => {
  const v1 = readJson("model/data/validation/historical-replays/vic_la_2018-prediction.json");
  const v2 = readJson("model/data/validation/historical-replays/vic_la_2022-v2-prediction.json");
  const score = readJson("model/data/validation/historical-replays/vic_la_2022-v2-score.json");
  assert.equal(v1.predictionSha256, "424552f6ad8fe362044543bb966d2642e34267c32a89b44c47ff390037a4c115");
  assert.equal(v2.predictionSha256, "f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0");
  assert.equal(score.predictionSha256, v2.predictionSha256);
});
