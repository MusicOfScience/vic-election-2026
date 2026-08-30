import assert from "node:assert/strict";
import test from "node:test";

import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };

test("preserves discovered candidate evidence behind quarantine", () => {
  assert.equal(provisional.records.length, 104);
  assert.equal(provisional.summary.assemblyContests, 73);
  assert.equal(provisional.summary.councilRegions, 8);
  assert.equal(new Set(provisional.records.map((record) => record.id)).size, provisional.records.length);
  assert.ok(provisional.records.every((record) => record.status === "quarantined-awaiting-review"));
  assert.ok(provisional.records.every((record) => record.automaticPromotion === false));
  assert.ok(provisional.records.every((record) => record.candidateStatus === "endorsed"));
  assert.equal(provisional.summary.sourceFamilies, 3);
  assert.deepEqual([...new Set(provisional.records.map((record) => record.sourceAuthority))].sort(), ["Australian Greens Victoria", "One Nation Victoria", "The Nationals Victoria"]);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "One Nation Victoria").length, 23);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "The Nationals Victoria").length, 5);
});
