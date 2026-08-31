import assert from "node:assert/strict";
import test from "node:test";

import dossier from "../metadata/candidate-review-dossier-2026.json" with { type: "json" };
import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };

test("candidate dossier accounts for every quarantined record", () => {
  assert.equal(dossier.summary.stagedRecords, provisional.records.length);
  assert.equal(dossier.families.reduce((sum, family) => sum + family.records, 0), provisional.records.length);
  assert.equal(dossier.summary.recordsRecommendedForAcceptance, provisional.records.length);
  assert.equal(dossier.summary.recommendEvidenceAcceptance, 8);
  assert.equal(new Set(dossier.families.map((family) => family.authority)).size, dossier.families.length);
});

test("candidate dossier closes the Assembly coverage gaps", () => {
  assert.equal(dossier.summary.assemblyContests, 88);
  assert.equal(dossier.summary.councilRegions, 8);
  assert.equal(dossier.summary.duplicateIdentities, 0);
  assert.equal(dossier.summary.unclassifiedContests, 0);
  assert.deepEqual(dossier.missingAssemblyContests, []);
});

test("candidate evidence approval remains separate from nomination and model use", () => {
  assert.equal(dossier.status, "approved-as-candidate-evidence");
  assert.equal(dossier.summary.acceptedRecords, 194);
  assert.equal(dossier.summary.acceptedAssemblyContests, 88);
  assert.equal(dossier.decision.officialNomination, false);
  assert.equal(dossier.decision.forecastUse, "excluded");
  assert.match(dossier.policy, /separate human decision/i);
  assert.ok(dossier.families.every((family) => family.evidenceRecommendation.startsWith("accept-as-")));
  assert.equal(dossier.families.find((family) => family.authority === "Mornington Peninsula Shire").recommendedStatus, "announced");
  assert.ok(dossier.families.every((family) => family.requiredChecks.some((check) => /official nomination/i.test(check))));
  assert.ok(dossier.knownScopeGaps.some((gap) => /independents/i.test(gap)));
});
