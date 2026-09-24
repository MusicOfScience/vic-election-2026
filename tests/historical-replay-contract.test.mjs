import test from "node:test";
import assert from "node:assert/strict";

import { validateHistoricalReplayContract } from "../scripts/validate-historical-replay-contract.mjs";

test("frozen replay contract remains leakage-safe and fail-closed", () => {
  const report = validateHistoricalReplayContract();
  assert.deepEqual(report.cycles.map((cycle) => cycle.id), ["vic_la_2010", "vic_la_2014", "vic_la_2018", "vic_la_2022"]);
  assert.equal(report.runnableCycles, 3);
  assert.equal(report.productionCompatible, false);
  assert.deepEqual(report.cycles.map((cycle) => cycle.cutoff), ["2010-11-26", "2014-11-28", "2018-11-23", "2022-11-25"]);
  assert.equal(report.cycles.find((cycle) => cycle.id === "vic_la_2018").blockedBy.length, 0);
  assert.ok(report.cycles.find((cycle) => cycle.id === "vic_la_2010").blockedBy.length > 0);
  assert.equal(report.cycles.find((cycle) => cycle.id === "vic_la_2014").runnable, true);
});
