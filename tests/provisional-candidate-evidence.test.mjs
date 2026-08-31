import assert from "node:assert/strict";
import test from "node:test";

import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };

test("preserves discovered candidate evidence behind quarantine", () => {
  assert.equal(provisional.records.length, 194);
  assert.equal(provisional.summary.assemblyContests, 88);
  assert.equal(provisional.summary.councilRegions, 8);
  assert.equal(new Set(provisional.records.map((record) => record.id)).size, provisional.records.length);
  assert.ok(provisional.records.every((record) => record.status === "quarantined-awaiting-review"));
  assert.ok(provisional.records.every((record) => record.automaticPromotion === false));
  assert.ok(provisional.records.every((record) => ["announced", "endorsed"].includes(record.candidateStatus)));
  assert.equal(provisional.records.filter((record) => record.candidateStatus === "announced").length, 1);
  assert.equal(provisional.summary.sourceFamilies, 8);
  assert.deepEqual([...new Set(provisional.records.map((record) => record.sourceAuthority))].sort(), ["Australian Greens Victoria", "Family First Party Australia", "Liberal Victoria", "Mornington Peninsula Shire", "One Nation Victoria", "The Nationals Victoria", "Victorian Labor", "Victorian Socialists"]);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Australian Greens Victoria").length, 78);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Family First Party Australia").length, 1);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Victorian Labor").length, 31);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Liberal Victoria").length, 51);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Mornington Peninsula Shire").length, 1);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "One Nation Victoria").length, 23);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "The Nationals Victoria").length, 5);
  assert.equal(provisional.records.filter((record) => record.sourceAuthority === "Victorian Socialists").length, 4);
});
