import assert from "node:assert/strict";
import test from "node:test";
import { buildHistoricalCouncilInputs } from "../scripts/build-historical-council-inputs.mjs";
import { buildHistoricalLocalInputs } from "../scripts/build-historical-local-inputs.mjs";

test("2018 local-input builder fails closed on the absent boundary artefact", () => {
  const result = buildHistoricalLocalInputs("vic_la_2018");
  assert.equal(result.status, "blocked");
  assert.match(result.reason, /outcomes cannot substitute/i);
  assert.equal(result.sourceOutcomeUse, "forbidden");
});

test("2018 Council builder rejects the modern regional poll as post-cutoff", () => {
  const result = buildHistoricalCouncilInputs("vic_la_2018");
  assert.equal(result.status, "blocked");
  assert.equal(result.rejectedModernArtefact, "model/data/processed/upper_house_region_poll_2026-08.csv");
  assert.match(result.reason, /2026 input after the frozen cutoff/i);
  assert.equal(result.outcomeCountSequences, "scoring-only");
});
