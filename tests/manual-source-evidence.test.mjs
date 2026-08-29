import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { stageManualEvidence } from "../scripts/stage-manual-source-evidence.mjs";

const manual = JSON.parse(readFileSync(resolve("metadata/manual-source-evidence-2026.json"), "utf8"));
const research = JSON.parse(readFileSync(resolve("metadata/research-source-evidence-2026.json"), "utf8"));

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

test("corroborated Resolve evidence remains secondary and awaiting primary capture", () => {
  const record = research.records[0];
  assert.equal(record.pollster, "Resolve Strategic");
  assert.equal(record.fieldworkStart, "2026-08-09");
  assert.equal(record.fieldworkEnd, "2026-08-15");
  assert.equal(record.sampleSize, 1000);
  assert.deepEqual(record.primaryVote, { coalition: 27, alp: 25, oneNation: 23, greens: 12, independents: 7, otherParties: 6 });
  assert.equal(record.twoPartyPreferred.basis, "respondent preferences");
  assert.equal(record.sourceTier, "reputable_secondary");
  assert.equal(record.verificationStatus, "corroborated-secondary-awaiting-primary");
  assert.equal(record.status, "quarantined-awaiting-review");
  assert.equal(record.automaticPromotion, false);
});

test("evidence staging adds review records but never promotes them", () => {
  const report = { checkedAt: "2026-08-29T00:00:00Z", records: [], observations: [] };
  const quarantine = { checkedAt: null, records: [] };
  assert.equal(stageManualEvidence(report, quarantine, manual).length, 1);
  assert.equal(stageManualEvidence(report, quarantine, research).length, 1);
  assert.equal(report.summary.quarantined, 2);
  assert.equal(report.summary.polls, 2);
  assert.ok(quarantine.records.every((record) => record.automaticPromotion === false));
  assert.deepEqual(report.observations.map((item) => item.sourceId), ["manual-blocked-source-evidence", "corroborated-secondary-evidence"]);
  assert.equal(stageManualEvidence(report, quarantine, manual).length, 0, "staging must be idempotent");
  assert.equal(stageManualEvidence(report, quarantine, research).length, 0, "secondary staging must be idempotent");
});

test("staging refuses records that bypass quarantine", () => {
  const bad = structuredClone(manual);
  bad.records[0].status = "approved";
  assert.throws(() => stageManualEvidence({ records: [], observations: [] }, { records: [] }, bad), /must remain quarantined/i);
});

test("secondary staging refuses evidence that hides its tier", () => {
  const bad = structuredClone(research);
  delete bad.records[0].sourceTier;
  assert.throws(() => stageManualEvidence({ records: [], observations: [] }, { records: [] }, bad), /must disclose reputable_secondary tier/i);
});
