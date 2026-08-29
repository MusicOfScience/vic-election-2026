import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { auditPollPromotion, proposedEstimateRows } from "../scripts/build-poll-promotion-audit.mjs";

const primary = JSON.parse(readFileSync(resolve("metadata/primary-source-evidence-2026.json"), "utf8"));
const redbridge = primary.records[0];

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
