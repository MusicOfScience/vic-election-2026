import assert from "node:assert/strict";
import test from "node:test";

import approval from "../metadata/candidate-review-approval-2026.json" with { type: "json" };
import candidates from "../metadata/candidates-2026.json" with { type: "json" };
import dossier from "../metadata/candidate-review-dossier-2026.json" with { type: "json" };
import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };
import reviewLog from "../metadata/discovery-review-decisions.json" with { type: "json" };

test("project-owner approval decides every reviewed source family", () => {
  assert.equal(approval.reviewerRole, "project-owner");
  assert.equal(approval.evidenceAsOf, provisional.evidenceAsOf);
  assert.equal(approval.familyDecisions.length, dossier.summary.sourceFamilies);
  assert.ok(approval.familyDecisions.every((item) => item.decision === "approve"));
  assert.deepEqual(new Set(approval.familyDecisions.map((item) => item.acceptedStatus)), new Set(["announced", "endorsed"]));
  assert.ok(approval.familyDecisions.every((item) => item.officialNomination === false));
  assert.ok(approval.familyDecisions.every((item) => item.forecastUse === "excluded"));
});

test("accepted register preserves all provisional-evidence safety boundaries", () => {
  assert.equal(candidates.candidates.length, 194);
  assert.equal(new Set(candidates.candidates.map((item) => item.evidenceId)).size, 194);
  assert.ok(candidates.candidates.every((item) => ["announced", "endorsed"].includes(item.status)));
  assert.equal(candidates.candidates.filter((item) => item.status === "announced").length, 1);
  assert.ok(candidates.candidates.every((item) => item.officialNomination === false));
  assert.ok(candidates.candidates.every((item) => item.forecastUse === "excluded"));
});

test("per-record review audit is complete and leaves model inputs unchanged", () => {
  const decisions = reviewLog.decisions.filter((item) => item.kind === "candidate");
  assert.equal(decisions.length, 194);
  assert.equal(new Set(decisions.map((item) => item.evidenceId)).size, 194);
  assert.ok(decisions.every((item) => item.decision === "approve"));
  assert.ok(decisions.every((item) => item.modelInputsChanged === false));
});
