import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const readJson = (path) => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url), "utf8"));

test("historical closure keeps 2018 non-certifying and preserves the three-cycle aggregate", () => {
  const status = readJson("model/data/validation/historical-replays/historical-four-cycle-validation-status.json");
  const aggregate = readJson("model/data/validation/historical-replays/historical-certifying-v2-aggregate.json");
  assert.equal(status.certifyingScoredCycles, 3);
  assert.match(status.nonCertifying2018, /post-hoc-v2-diagnostic/);
  assert.equal(status.completeForecastBacktest, "closed-incomplete-certifying-four-cycle-protocol");
  assert.equal(status.probabilityCalibration, "closed-incomplete-cycle-clustered-protocol");
  assert.ok(Math.abs(aggregate.descriptivePooledMetrics.multiclassBrier - 0.2193372181) < 1e-9);
  assert.ok(Math.abs(aggregate.descriptivePooledMetrics.multiclassLogLoss - 1.0486418097) < 1e-9);
});

test("closure audit classifies current evidence blockers without promoting September polling", () => {
  const audit = readJson("metadata/prod-1.0-closure-audit.json");
  assert.equal(audit.gates.sourceIntegrity.status, "PASS");
  assert.equal(audit.gates.criticalSourceFreshness.class, "resolvable-current-evidence-blocker");
  assert.equal(audit.gates.modelInputFreshness.class, "resolvable-current-evidence-blocker");
  assert.equal(audit.gates.completeForecastBacktest.class, "structurally-blocked-under-prod-1.0-validation-protocol");
  assert.equal(audit.gates.probabilityCalibration.class, "structurally-blocked-under-prod-1.0-validation-protocol");
  assert.equal(audit.septemberRedbridgeAccent.sampleFamilyIndependence, "independence-not-proven");
  assert.equal(audit.septemberRedbridgeAccent.modelInputPromotion, false);
  assert.equal(audit.gates.productionAuthorisation.class, "downstream-blocked");
});

test("canonical 2010 Council metric and 2026 forecast identity remain unchanged", () => {
  const score = readJson("model/data/validation/historical-replays/vic_la_2010-v2-score.json");
  const audit = readJson("metadata/prod-1.0-closure-audit.json");
  assert.equal(score.council.regionalMeanAbsoluteSeatError, 0.27911458333333333);
  assert.equal(audit.gates.deterministicOutputs.forecastSha256, "70ed0b9b6abc45ed66dd4ac44ed727d8841d2b19358a473d0eb1c2574a9a1aab");
});
