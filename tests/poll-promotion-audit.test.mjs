import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { auditPollPromotion, buildPromotionAudit, proposedEstimateRows } from "../scripts/build-poll-promotion-audit.mjs";

const manual = JSON.parse(readFileSync(resolve("metadata/manual-source-evidence-2026.json"), "utf8"));
const research = JSON.parse(readFileSync(resolve("metadata/research-source-evidence-2026.json"), "utf8"));
const demos = manual.records[0];
const resolvePoll = research.records[0];

test("DemosAU preview maps the complete primary vote without writing model inputs", () => {
  const rows = proposedEstimateRows(demos);
  assert.equal(rows.length, 5);
  assert.equal(rows.reduce((sum, row) => sum + row.primary_pct, 0), 100);
  assert.deepEqual(rows.map((row) => row.party_id), ["LIB_NAT", "ALP", "ONP", "GRN", "OTH"]);
  assert.ok(rows.every((row) => row.poll_id === "demosau_2026-08"));
});

test("Resolve preview preserves independent and other shares separately", () => {
  const rows = proposedEstimateRows(resolvePoll);
  assert.equal(rows.length, 6);
  assert.equal(rows.reduce((sum, row) => sum + row.primary_pct, 0), 100);
  assert.deepEqual(rows.map((row) => row.party_id), ["LIB_NAT", "ALP", "ONP", "GRN", "IND", "OTH"]);
});

test("current DemosAU evidence is blocked only by review decisions, not missing publication metadata", () => {
  const audit = auditPollPromotion(demos, { modelEvents: [], acceptedPolls: [] });
  assert.equal(audit.canPromoteNow, false);
  assert.ok(audit.blockers.includes("human-evidence-acceptance-required"));
  assert.ok(!audit.blockers.includes("canonical-poll-publication-date-required"));
  assert.equal(audit.primaryVoteTotal, 100);
  assert.equal(audit.sourceTier, "primary_pollster");
});

test("Resolve remains blocked pending primary reconciliation and canonical publication date", () => {
  const audit = auditPollPromotion(resolvePoll, { modelEvents: [], acceptedPolls: [] });
  assert.equal(audit.canPromoteNow, false);
  assert.ok(audit.blockers.includes("human-evidence-acceptance-required"));
  assert.ok(audit.blockers.includes("primary-source-reconciliation-or-reviewed-exception-required"));
  assert.ok(audit.blockers.includes("canonical-poll-publication-date-required"));
  assert.equal(audit.primaryVoteTotal, 100);
});

test("accepted evidence still requires a separate model-eligibility decision", () => {
  const accepted = [{ evidenceId: demos.id, modelEligible: false, verificationStatus: "human-reviewed-source-evidence" }];
  const audit = auditPollPromotion(demos, { modelEvents: [], acceptedPolls: accepted });
  assert.ok(!audit.blockers.includes("human-evidence-acceptance-required"));
  assert.ok(audit.blockers.includes("explicit-model-eligibility-required"));
  assert.equal(audit.canPromoteNow, false);
});

test("promotion preview catches canonical poll-id collisions", () => {
  const audit = auditPollPromotion(demos, { modelEvents: [{ poll_id: "demosau_2026-08" }], acceptedPolls: [] });
  assert.ok(audit.blockers.includes("canonical-poll-id-already-exists"));
});

test("promotion audit is explicitly preview-only", () => {
  const report = buildPromotionAudit({ records: [demos, resolvePoll], modelEvents: [], acceptedPolls: [], asOf: "2026-08-29" });
  assert.equal(report.mode, "preview-only");
  assert.equal(report.automaticWriteEnabled, false);
  assert.equal(report.summary.stagedPolls, 2);
  assert.equal(report.summary.promotableNow, 0);
  assert.equal(report.summary.blocked, 2);
  assert.match(report.policy, /never writes model inputs/i);
});
