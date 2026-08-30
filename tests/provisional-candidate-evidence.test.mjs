import assert from "node:assert/strict";
import test from "node:test";

import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };

test("preserves discovered candidate evidence behind quarantine", () => {
  assert.equal(provisional.records.length, 76);
  assert.equal(provisional.summary.assemblyContests, 72);
  assert.equal(provisional.summary.councilRegions, 4);
  assert.equal(new Set(provisional.records.map((record) => record.id)).size, provisional.records.length);
  assert.ok(provisional.records.every((record) => record.status === "quarantined-awaiting-review"));
  assert.ok(provisional.records.every((record) => record.automaticPromotion === false));
  assert.ok(provisional.records.every((record) => record.candidateStatus === "endorsed"));
  assert.ok(provisional.records.every((record) => record.sourceAuthority === "Australian Greens Victoria"));
});
