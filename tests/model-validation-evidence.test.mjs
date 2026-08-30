import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const contract = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-contract.json", import.meta.url), "utf8"));

test("requires evidence matching the complete probability model", () => {
  const byId = Object.fromEntries(contract.components.map((component) => [component.id, component]));
  assert.equal(contract.minimumWalkForwardCycles, 4);
  assert.equal(contract.automaticGateOpening, false);
  assert.equal(byId["boundary-aligned-tpp-outcomes"].status, "complete");
  assert.equal(byId["pre-election-poll-vintages"].status, "missing");
  assert.equal(byId["district-primary-votes-and-party-crosswalk"].status, "missing");
  assert.equal(byId["preference-flows-and-final-pairs"].status, "partial");
  assert.equal(byId["council-results-and-count-rules"].status, "missing");
  assert.ok(contract.promotionMetrics.includes("multi-class Brier score"));
  assert.ok(contract.promotionMetrics.includes("log loss"));
});
