import assert from "node:assert/strict";
import test from "node:test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url));

test("refresh audit reconciles exact single-wave addition and every district delta", () => {
  const report = JSON.parse(read("metadata/forecast-refresh-2026-10-08.json"));
  assert.equal(report.baseCommit, "8ddf08a1963973397e9d3b1869d658009282fd5f");
  assert.equal(report.canonicalPolling.eligibleBefore, 12);
  assert.equal(report.canonicalPolling.eligibleAfter, 13);
  assert.equal(report.canonicalPolling.totalEventsAfter - report.canonicalPolling.totalEventsBefore, 1);
  assert.equal(report.assembly.allDistrictChanges.length, 88);
  assert.equal(report.council.regions.length, 8);
  assert.equal(report.assembly.materialDistrictThreshold, 0.05);
  assert.deepEqual(report.assembly.materialDistricts, report.assembly.allDistrictChanges.filter((row) => row.maximumAbsoluteProbabilityChange >= 0.05).sort((a, b) => b.maximumAbsoluteProbabilityChange - a.maximumAbsoluteProbabilityChange));
  assert.equal(report.forecast.sha256After, createHash("sha256").update(read(report.forecast.path)).digest("hex"));
  assert.equal(report.integrity.historicalFrozenArtifactsUnchanged, true);
  assert.equal(report.integrity.modelParametersUnchanged, true);
  execFileSync(process.execPath, ["scripts/build-forecast-refresh-comparison.mjs", "--check"]);
});

test("owner promotion is idempotent and leaves unrelated candidate reviews intact", () => {
  execFileSync(process.execPath, ["scripts/apply-approved-poll-review.mjs", "--check"]);
  const decisions = JSON.parse(read("metadata/discovery-review-decisions.json")).decisions;
  assert.equal(decisions.filter((item) => item.kind !== "poll").length, 305);
});
