import test from "node:test";
import assert from "node:assert/strict";
import manual from "../metadata/manual-source-evidence-2026.json" with { type: "json" };
import primary from "../metadata/primary-source-evidence-2026.json" with { type: "json" };
import research from "../metadata/research-source-evidence-2026.json" with { type: "json" };
import dossier from "../metadata/poll-review-dossier-2026.json" with { type: "json" };

const staged = [...manual.records, ...primary.records, ...research.records].filter((record) => record.kind === "poll" && record.status === "quarantined-awaiting-review");

test("review dossier covers every staged poll exactly once", () => {
  const stagedIds = staged.map((record) => record.id).sort();
  const reviewedIds = dossier.reviews.map((review) => review.evidenceId).sort();
  assert.deepEqual(reviewedIds, stagedIds);
  assert.equal(new Set(reviewedIds).size, reviewedIds.length);
  assert.equal(dossier.summary.stagedPolls, staged.length);
});

test("review dossier keeps evidence acceptance separate from model admission", () => {
  const evidenceRecommendations = new Set(["accept", "verify_then_accept", "hold"]);
  const modelRecommendations = new Set(["admit_after_acceptance", "repair_existing_then_admit", "conditional_review", "hold", "comparison_only"]);
  for (const review of dossier.reviews) {
    assert.ok(evidenceRecommendations.has(review.evidenceRecommendation));
    assert.ok(modelRecommendations.has(review.modelRecommendation));
    assert.ok(review.rationale.length > 40);
    assert.ok(review.requiredChecks.length > 0);
  }
  assert.equal(dossier.status, "recommendations-awaiting-human-decision");
  assert.match(dossier.policy, /separate decision/i);
});

test("dossier recommendation totals are internally consistent", () => {
  assert.equal(dossier.summary.recommendEvidenceAcceptance, dossier.reviews.filter((review) => review.evidenceRecommendation === "accept").length);
  assert.equal(dossier.summary.verifyThenAccept, dossier.reviews.filter((review) => review.evidenceRecommendation === "verify_then_accept").length);
  assert.equal(dossier.summary.holdEvidence, dossier.reviews.filter((review) => review.evidenceRecommendation === "hold").length);
  assert.equal(dossier.summary.readyForModelDecisionAfterAcceptance, dossier.reviews.filter((review) => review.modelRecommendation === "admit_after_acceptance").length);
});
