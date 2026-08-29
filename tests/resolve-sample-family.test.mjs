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
  assert.deepEqual(marApr.combinedPublishedPrimaryVote, { alp: 27, coalition: 29, oneNation: 21, greens: 10, independents: 7, otherParties: 6 });
  assert.match(marApr.dependencyCheck, /cannot all enter the polling likelihood/i);
  assert.equal(marApr.modelEligible, false);
});

test("Resolve January-February transition is not treated as a coherent five-way poll", () => {
  const transition = ledger.families.find((family) => family.id === "resolve-vic-2026-jan-feb-transition");
  assert.equal(transition.modelEligible, false);
  assert.match(transition.comparabilityWarning, /January did not separately report One Nation/i);
});

test("historical Resolve family evidence cannot displace the fixed August shadow scenario", () => {
  const stagedResolve = research.records.filter((record) => record.pollster === "Resolve Strategic");
  assert.equal(stagedResolve.length, 1);
  assert.equal(stagedResolve[0].proposedModelPollId, "resolve_strategic_2026-08");
  const marApr = ledger.families.find((family) => family.id === "resolve-vic-2026-mar-apr");
  assert.equal(marApr.status, "comparable-secondary-evidence-awaiting-primary-reconciliation");
  assert.equal(marApr.modelEligible, false);
});


test("Resolve May-June combined family is captured without inventing monthly observations", () => {
  const mayJun = ledger.families.find((family) => family.id === "resolve-vic-2026-may-jun");
  assert.equal(mayJun.combinedSampleSize, 1000);
  assert.equal(mayJun.fieldworkPrecision, "month-only");
  assert.deepEqual(mayJun.combinedPublishedPrimaryVote, { alp: 26, coalition: 26, oneNation: 24, greens: 12, residual: 12 });
  assert.equal(mayJun.componentEvidence.mayOneNation, 20);
  assert.equal(mayJun.componentEvidence.juneOneNation, 28);
  assert.equal(mayJun.componentEvidence.fullMonthlyCompositionsAvailable, false);
  assert.match(mayJun.dependencyCheck, /one sample family/i);
  assert.equal(mayJun.modelEligible, false);
});
