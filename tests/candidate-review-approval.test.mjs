import assert from "node:assert/strict";
import test from "node:test";

import approval from "../metadata/candidate-review-approval-2026.json" with { type: "json" };
import candidates from "../metadata/candidates-2026.json" with { type: "json" };
import dossier from "../metadata/candidate-review-dossier-2026.json" with { type: "json" };
import adjudication from "../metadata/current-evidence-adjudication-2026-10-08.json" with { type: "json" };
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
  assert.equal(candidates.candidates.length, 305);
  assert.equal(new Set(candidates.candidates.map((item) => item.evidenceId)).size, 305);
  assert.ok(candidates.candidates.every((item) => ["announced", "endorsed"].includes(item.status)));
  assert.equal(candidates.candidates.filter((item) => item.status === "announced").length, 5);
  assert.ok(candidates.candidates.every((item) => item.officialNomination === false));
  assert.ok(candidates.candidates.every((item) => item.forecastUse === "excluded"));
});

test("per-record review audit is complete and leaves model inputs unchanged", () => {
  const decisions = reviewLog.decisions.filter((item) => item.kind === "candidate");
  assert.equal(decisions.length, 305);
  assert.equal(new Set(decisions.map((item) => item.evidenceId)).size, 305);
  assert.ok(decisions.every((item) => item.decision === "approve"));
  assert.ok(decisions.every((item) => item.modelInputsChanged === false));
});

test("owner record adjudication preserves held and reconciled packet records", () => {
  const counts = Object.fromEntries(["accept", "hold", "reject", "reconcile"].map((decision) => [decision, approval.recordDecisions.filter((item) => item.decision === decision).length]));
  assert.equal(approval.recordDecisions.length, 114);
  assert.deepEqual(counts, { accept: 111, hold: 1, reject: 0, reconcile: 2 });
  assert.equal(counts.accept + counts.hold + counts.reject + counts.reconcile, adjudication.ownerAdjudication.candidateReview.recordsReviewed);
  assert.equal(adjudication.ownerAdjudication.candidateReview.canonicalNewAccepted, adjudication.ownerAdjudication.candidateReview.newAcceptedAsEndorsed + adjudication.ownerAdjudication.candidateReview.newAcceptedAsAnnounced);
  assert.equal(adjudication.ownerAdjudication.candidateReview.duplicateReconciled, adjudication.ownerAdjudication.candidateReview.reconciledExistingByStatus.endorsed + adjudication.ownerAdjudication.candidateReview.reconciledExistingByStatus.announced);
  assert.equal(adjudication.ownerAdjudication.candidateReview.previousCanonicalAccepted + adjudication.ownerAdjudication.candidateReview.canonicalNewAccepted, adjudication.ownerAdjudication.candidateReview.resultingCanonicalAccepted);
  assert.equal(adjudication.ownerAdjudication.candidateReview.resultingCanonicalAccepted, candidates.candidates.length);
  assert.ok(approval.recordDecisions.every((item) => item.forecastUse === "excluded" && item.officialNomination === false && item.modelInputsChanged === false));
});
