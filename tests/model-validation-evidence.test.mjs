import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { validateModelValidationEvidence } from "../scripts/validate-model-validation-evidence.mjs";

const contract = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-contract.json", import.meta.url), "utf8"));
const inventory = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-inventory.json", import.meta.url), "utf8"));

test("requires evidence matching the complete probability model", () => {
  const byId = Object.fromEntries(contract.components.map((component) => [component.id, component]));
  assert.equal(contract.minimumWalkForwardCycles, 4);
  assert.equal(contract.automaticGateOpening, false);
  assert.equal(byId["boundary-aligned-tpp-outcomes"].status, "complete");
  assert.equal(byId["pre-election-poll-vintages"].status, "partial");
  assert.equal(byId["district-primary-votes-and-party-crosswalk"].status, "partial");
  assert.equal(byId["ballot-and-contest-slates"].status, "partial");
  assert.equal(byId["preference-flows-and-final-pairs"].status, "partial");
  assert.equal(byId["council-results-and-count-rules"].status, "partial");
  assert.equal(byId["frozen-historical-model-configurations"].status, "partial");
  assert.ok(contract.promotionMetrics.includes("multi-class Brier score"));
  assert.ok(contract.promotionMetrics.includes("log loss"));
});

test("fingerprints every available validation artefact and keeps partial evidence fail-closed", () => {
  assert.deepEqual(validateModelValidationEvidence(), {
    complete: 1,
    partial: 6,
    missing: 0,
    total: 7,
    completeForecastBacktestReady: false,
    probabilityCalibrationReady: false,
  });
  assert.equal(inventory.negativeFeatureEvidence.demographicChallenger.outcome, "rejected");
  assert.equal(inventory.negativeFeatureEvidence.demographicChallenger.centralWeight, 0);
});
