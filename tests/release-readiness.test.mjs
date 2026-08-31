import assert from "node:assert/strict";
import test from "node:test";

import { ageInDays, buildReadiness } from "../scripts/check-release-readiness.mjs";

test("treats a source as current through its inclusive threshold", () => {
  assert.equal(ageInDays("2026-08-07", "2026-08-28"), 21);
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal(readiness.gates.criticalSourceFreshness.passed, true);
});

test("fails closed once a critical source exceeds its threshold", () => {
  const readiness = buildReadiness({ asOf: "2026-08-29" });
  assert.equal(readiness.gates.criticalSourceFreshness.passed, false);
  assert.equal(readiness.status, "experimental-blocked");
});

test("keeps production authorisation separate from technical integrity", () => {
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal(readiness.gates.sourceIntegrity.passed, true);
  assert.equal(readiness.gates.deterministicOutputs.passed, true);
  assert.equal(readiness.gates.historicalDataReadiness.passed, true);
  assert.equal(readiness.gates.completeForecastBacktest.passed, false);
  assert.equal(readiness.gates.probabilityCalibration.passed, false);
  assert.equal(readiness.gates.candidateEvidence.passed, true);
  assert.equal(readiness.gates.productionAuthorisation.passed, false);
  assert.equal(readiness.policy, "retain-last-valid-forecast");
});

test("does not mislabel a four-cycle data ledger as complete model validation", () => {
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal("historicalValidation" in readiness.gates, false);
  assert.equal(readiness.findings.demographicChallenger.outcome, "rejected");
  assert.equal(readiness.findings.demographicChallenger.centralWeight, 0);
  assert.ok(readiness.summary.blockingGateIds.includes("completeForecastBacktest"));
  assert.ok(readiness.summary.blockingGateIds.includes("probabilityCalibration"));
});

test("recognises reviewed staged polling as explicitly excluded from model inputs", () => {
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal(readiness.evidenceFreshness.newerEvidenceAwaitingReview, false);
  assert.equal(readiness.evidenceFreshness.newerEvidenceExcludedByReview, true);
  assert.equal(readiness.evidenceFreshness.reviewResolution.unresolvedRecords, 0);
  assert.equal(readiness.gates.modelInputFreshness.passed, true);
  assert.ok(!readiness.summary.blockingGateIds.includes("modelInputFreshness"));
});

test("opens the candidate evidence gate only at complete Assembly coverage", () => {
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal(readiness.findings.candidateDiscovery.records, 194);
  assert.equal(readiness.findings.candidateDiscovery.acceptedRecords, 194);
  assert.equal(readiness.findings.candidateDiscovery.status, "accepted-candidate-evidence-complete-coverage");
  assert.equal(readiness.findings.candidateDiscovery.assemblyContests, 88);
  assert.equal(readiness.findings.candidateDiscovery.councilRegions, 8);
  assert.deepEqual(readiness.findings.candidateDiscovery.unclassifiedContests, []);
  assert.equal(readiness.findings.candidateDiscovery.acceptedAssemblyContests, 88);
  assert.equal(readiness.findings.candidateDiscovery.automaticPromotion, false);
  assert.equal(readiness.findings.candidateDiscovery.sourceFamilies, 8);
  assert.equal(readiness.gates.candidateEvidence.passed, true);
});

test("does not substitute a two-party residual ledger for complete-model evidence", () => {
  const readiness = buildReadiness({ asOf: "2026-08-28" });
  assert.equal(readiness.findings.validationEvidence.complete, 1);
  assert.equal(readiness.findings.validationEvidence.partial, 5);
  assert.equal(readiness.findings.validationEvidence.missing, 1);
  assert.equal(readiness.findings.validationEvidence.total, 7);
  assert.equal(readiness.findings.validationEvidence.automaticGateOpening, false);
  assert.equal(readiness.gates.completeForecastBacktest.passed, false);
  assert.equal(readiness.gates.probabilityCalibration.passed, false);
});
