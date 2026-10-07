import test from "node:test";
import assert from "node:assert/strict";
import approval from "../metadata/poll-review-approval-2026.json" with { type: "json" };
import accepted from "../metadata/accepted-polls-2026.json" with { type: "json" };
import modelDecisions from "../metadata/poll-model-eligibility-decisions.json" with { type: "json" };
import reviewDecisions from "../metadata/discovery-review-decisions.json" with { type: "json" };

test("project-owner approval records every dossier recommendation", () => {
  assert.equal(approval.reviewerRole, "project-owner");
  assert.equal(approval.evidenceDecisions.length, 11);
  const pollDecisions = reviewDecisions.decisions.filter((item) => item.kind === "poll");
  assert.equal(pollDecisions.length, 11);
  assert.deepEqual(approval.evidenceDecisions.map((item) => item.decision), ["defer", "approve", "approve", "approve", "approve", "hold", "hold", "approve", "approve", "hold", "hold"]);
});

test("evidence acceptance remains separate from model eligibility", () => {
  assert.equal(accepted.polls.length, 6);
  assert.equal(accepted.polls.filter((poll) => poll.modelEligible).length, 4);
  assert.equal(modelDecisions.decisions.filter((item) => item.decision === "eligible").length, 4);
  assert.equal(accepted.polls.find((poll) => poll.pollster.startsWith("RedBridge")).modelEligible, false);
});

test("canonical actions add two Freshwater waves and repair August without duplication", () => {
  const actions = modelDecisions.decisions.filter((item) => item.decision === "eligible");
  assert.deepEqual(actions.map((item) => item.canonicalAction), ["add", "add", "repair-existing", "add"]);
  assert.equal(new Set(actions.map((item) => item.pollId)).size, 4);
  assert.equal(actions.at(-1).pollId, "freshwater_2026-09");
});

test("September owner decisions retain RedBridge dependence and admit only one Freshwater wave", () => {
  const fresh = accepted.polls.find((poll) => poll.evidenceId === "freshwater-2026-09-primary-workbook");
  assert.equal(fresh.modelEligible, true);
  assert.equal(fresh.sourceFamily, "freshwater");
  assert.deepEqual(fresh.primaryVote, { alp: 24.0121, coalition: 28.9106, oneNation: 22.1313, greens: 14.3689, otherParties: 10.5771 });
  assert.equal(fresh.sampleSize, 1030);
  assert.equal(fresh.primaryVoteUnweightedBase, 977);
  assert.equal(fresh.twoPartyPreferredUnweightedBase, 956);
  assert.equal(fresh.publicationDate, "2026-10-01");
  assert.equal(fresh.primaryReleaseDate, "2026-10-02");
  for (const id of ["redbridge-accent-vic-2026-09-14-primary", "demosau-vic-2026-09-10-20-secondary", "resolve-strategic-vic-2026-09-06-12-secondary"]) {
    const decision = modelDecisions.decisions.find((item) => item.evidenceId === id);
    assert.equal(decision.canonicalAction, "none");
    assert.notEqual(decision.decision, "eligible");
    assert.ok(decision.blocker.length > 30);
  }
});
