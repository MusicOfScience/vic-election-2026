import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { auditPollPromotion, proposedEstimateRows } from "../scripts/build-poll-promotion-audit.mjs";

const primary = JSON.parse(readFileSync(resolve("metadata/primary-source-evidence-2026.json"), "utf8"));
const redbridge = primary.records.find((record) => record.proposedModelPollId === "redbridge_accent_2026-08");

test("September RedBridge report is captured as fresh primary evidence and remains quarantined", () => {
  const september = primary.records.find((record) => record.proposedModelPollId === "redbridge_accent_2026-09");
  assert.ok(september);
  assert.equal(september.status, "quarantined-awaiting-review");
  assert.equal(september.automaticPromotion, false);
  assert.equal(september.fieldworkEnd, "2026-09-14");
  assert.equal(september.pollPublicationDate, "2026-09-15");
  assert.equal(september.sampleSize, 2371);
  assert.equal(september.effectiveSampleSize, 2009);
  assert.equal(september.publishedVoteIntentionBase, 2160);
  assert.deepEqual(september.primaryVote, { alp: 24, coalition: 29, oneNation: 25, greens: 15, otherParties: 7 });
  assert.deepEqual(september.twoPartyPreferred, { alp: 44, coalition: 53, basis: "respondent allocated; published vote-intention base N=2,160" });
  assert.equal(september.reportSha256, "ba588f8f3cf71b8ee7366dc43c354b6b4e42c42e34dc6c6ee3af8db103dd5ee9");
  assert.match(september.reviewNotes, /211 respondents/);
});

test("RedBridge August evidence preserves corrected first-party toplines and remains quarantined", () => {
  assert.equal(redbridge.pollster, "RedBridge / Accent Research");
  assert.equal(redbridge.status, "quarantined-awaiting-review");
  assert.equal(redbridge.automaticPromotion, false);
  assert.equal(redbridge.sampleSize, 1014);
  assert.equal(redbridge.effectiveSampleSize, 745);
  assert.deepEqual(redbridge.primaryVote, { coalition: 30, alp: 23, oneNation: 22, greens: 14, otherParties: 11 });
  assert.deepEqual(redbridge.twoPartyPreferred, { coalition: 57, alp: 43, basis: "respondent allocated" });
  assert.equal(redbridge.sourceTier, "primary_pollster");
  assert.equal(redbridge.proposedModelPollId, "redbridge_accent_2026-08");
  assert.equal(redbridge.pollPublicationDate, "2026-08-03");
  assert.match(redbridge.sourceUrl, /^https:\/\/www\.accent-research\.com\//);
  assert.match(redbridge.correctionHistory, /53-47/);
  assert.match(redbridge.correctionHistory, /57-43/);
});

test("RedBridge promotion preview is complete but still requires human acceptance", () => {
  const rows = proposedEstimateRows(redbridge);
  assert.equal(rows.reduce((sum, row) => sum + row.primary_pct, 0), 100);
  assert.deepEqual(rows.map((row) => row.party_id), ["LIB_NAT", "ALP", "ONP", "GRN", "OTH"]);

  const audit = auditPollPromotion(redbridge, { modelEvents: [], acceptedPolls: [] });
  assert.equal(audit.canPromoteNow, false);
  assert.deepEqual(audit.blockers, ["human-evidence-acceptance-required"]);
  assert.equal(audit.proposedChanges.pollEvent.effective_sample_size, 745);
  assert.equal(audit.proposedChanges.pollEvent.publication_date, "2026-08-03");
});


test("Freshwater workbooks are primary parsed evidence but remain quarantined", () => {
  const freshwater = primary.records.filter((record) => record.pollster === "Freshwater Strategy");
  assert.equal(freshwater.length, 3);
  assert.deepEqual(freshwater.map((record) => record.sampleSize), [1030, 1062, 1020]);
  assert.ok(freshwater.every((record) => record.sourceTier === "primary_pollster"));
  assert.ok(freshwater.every((record) => record.verificationStatus === "primary-workbook-parsed-awaiting-human-review"));
  assert.ok(freshwater.every((record) => record.status === "quarantined-awaiting-review" && record.automaticPromotion === false));
  assert.ok(freshwater.every((record) => Math.abs(Object.values(record.primaryVote).reduce((sum, value) => sum + value, 0) - 100) < 0.01));
  const february = freshwater.find((record) => record.proposedModelPollId === "freshwater_2026-02");
  assert.equal(february.primaryVote.otherParties, 9.8911);
  const august = freshwater.find((record) => record.proposedModelPollId === "freshwater_2026-08");
  assert.equal(august.pollPublicationDate, "2026-08-04");
  assert.deepEqual(august.primaryVoteRounded, { alp: 25, coalition: 30, oneNation: 22, greens: 14, otherParties: 9 });
});
