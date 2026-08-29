import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const ledger = JSON.parse(readFileSync(resolve("metadata/resolve-sample-family-2026.json"), "utf8"));
const research = JSON.parse(readFileSync(resolve("metadata/research-source-evidence-2026.json"), "utf8"));

test("Resolve combined releases and monthly components are explicitly mutually exclusive", () => {
  assert.equal(ledger.policy.combinedAndComponentsMutuallyExclusive, true);
  const marApr = ledger.families.find((family) => family.id === "resolve-vic-2026-mar-apr");
  assert.ok(marApr);
  assert.equal(marApr.components.reduce((sum, component) => sum + component.sampleSize, 0), marApr.combinedSampleSize);
  assert.equal(marApr.combinedSampleSize, 1047);
  assert.match(marApr.dependencyCheck, /cannot all enter the polling likelihood/i);
  assert.equal(marApr.modelEligible, false);
});

test("Resolve January-February transition is not treated as a coherent five-way poll", () => {
  const transition = ledger.families.find((family) => family.id === "resolve-vic-2026-jan-feb-transition");
  assert.equal(transition.modelEligible, false);
  assert.match(transition.comparabilityWarning, /January did not separately report One Nation/i);
});

test("staged March-April combined record declares its sample family and remains secondary", () => {
  const record = research.records.find((item) => item.proposedModelPollId === "resolve_strategic_2026-03-04_combined");
  assert.ok(record);
  assert.equal(record.sampleFamily, "resolve-vic-2026-mar-apr");
  assert.equal(record.sampleSize, 1047);
  assert.deepEqual(record.primaryVote, { coalition: 29, alp: 27, oneNation: 21, greens: 10, independents: 7, otherParties: 6 });
  assert.equal(record.componentSamples.reduce((sum, component) => sum + component.sampleSize, 0), 1047);
  assert.equal(record.sourceTier, "reputable_secondary");
  assert.match(record.verificationStatus, /awaiting-primary/i);
  assert.match(record.dependencyPolicy, /never count combined and components independently/i);
});
