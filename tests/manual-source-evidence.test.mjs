import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { stageManualEvidence } from "../scripts/stage-manual-source-evidence.mjs";

const manual = JSON.parse(readFileSync(resolve("metadata/manual-source-evidence-2026.json"), "utf8"));

test("manual DemosAU evidence remains quarantined and provenance-complete", () => {
  const record = manual.records[0];
  assert.equal(record.pollster, "DemosAU");
  assert.equal(record.status, "quarantined-awaiting-review");
  assert.equal(record.automaticPromotion, false);
  assert.equal(record.fieldworkEnd, "2026-08-11");
  assert.equal(record.sampleSize, 1007);
  assert.deepEqual(record.primaryVote, { coalition: 32, alp: 23, oneNation: 22, greens: 13, otherParties: 10 });
  assert.deepEqual(record.twoPartyPreferred, { coalition: 55, alp: 45 });
  assert.match(record.sourceUrl, /^https:\/\/demosau\.com\//);
  assert.match(record.captureReason, /403/i);
});

test("manual evidence staging adds review records but never promotes them", () => {
  const report = { checkedAt: "2026-08-29T00:00:00Z", records: [], observations: [] };
  const quarantine = { checkedAt: null, records: [] };
  const additions = stageManualEvidence(report, quarantine, manual);
  assert.equal(additions.length, 1);
  assert.equal(report.summary.quarantined, 1);
  assert.equal(report.summary.polls, 1);
  assert.equal(quarantine.records[0].automaticPromotion, false);
  assert.equal(report.observations[0].status, "manual-evidence-staged");
  assert.equal(stageManualEvidence(report, quarantine, manual).length, 0, "staging must be idempotent");
});

test("manual staging refuses records that bypass quarantine", () => {
  const bad = structuredClone(manual);
  bad.records[0].status = "approved";
  assert.throws(() => stageManualEvidence({ records: [], observations: [] }, { records: [] }, bad), /must remain quarantined/i);
});
