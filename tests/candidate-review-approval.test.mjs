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
  assert.ok(approval.familyDecisions.every((item) => item.acceptedStatus === "endorsed"));
  assert.ok(approval.familyDecisions.every((item) => item.officialNomination === false));
  assert.ok(approval.familyDecisions.every((item) => item.forecastUse === "excluded"));
});

test("accepted register preserves all endorsement-only safety boundaries", () => {
  assert.equal(candidates.candidates.length, 188);
  assert.equal(new Set(candidates.candidates.map((item) => item.evidenceId)).size, 188);
  assert.ok(candidates.candidates.every((item) => item.status === "endorsed"));
  assert.ok(candidates.candidates.every((item) => item.officialNomination === false));
  assert.ok(candidates.candidates.every((item) => item.forecastUse === "excluded"));
});

test("per-record review audit is complete and leaves model inputs unchanged", () => {
  const decisions = reviewLog.decisions.filter((item) => item.kind === "candidate");
  assert.equal(decisions.length, 188);
  assert.equal(new Set(decisions.map((item) => item.evidenceId)).size, 188);
  assert.ok(decisions.every((item) => item.decision === "approve"));
  assert.ok(decisions.every((item) => item.modelInputsChanged === false));
});

