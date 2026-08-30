import test from "node:test";
import assert from "node:assert/strict";
import approval from "../metadata/poll-review-approval-2026.json" with { type: "json" };
import accepted from "../metadata/accepted-polls-2026.json" with { type: "json" };
import modelDecisions from "../metadata/poll-model-eligibility-decisions.json" with { type: "json" };
import reviewDecisions from "../metadata/discovery-review-decisions.json" with { type: "json" };

test("project-owner approval records every dossier recommendation", () => {
  assert.equal(approval.reviewerRole, "project-owner");
  assert.equal(approval.evidenceDecisions.length, 7);
  assert.equal(reviewDecisions.decisions.length, 7);
  assert.deepEqual(approval.evidenceDecisions.map((item) => item.decision), ["defer", "approve", "approve", "approve", "approve", "hold", "hold"]);
});

test("evidence acceptance remains separate from model eligibility", () => {
  assert.equal(accepted.polls.length, 4);
  assert.equal(accepted.polls.filter((poll) => poll.modelEligible).length, 3);
  assert.equal(modelDecisions.decisions.filter((item) => item.decision === "eligible").length, 3);
  assert.equal(accepted.polls.find((poll) => poll.pollster.startsWith("RedBridge")).modelEligible, false);
});

test("canonical actions add two Freshwater waves and repair August without duplication", () => {
  const actions = modelDecisions.decisions.filter((item) => item.decision === "eligible");
  assert.deepEqual(actions.map((item) => item.canonicalAction), ["add", "add", "repair-existing"]);
  assert.equal(new Set(actions.map((item) => item.pollId)).size, 3);
  assert.equal(actions.at(-1).pollId, "freshwater_2026-08");
});
