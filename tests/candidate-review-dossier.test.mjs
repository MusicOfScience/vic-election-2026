import assert from "node:assert/strict";
import test from "node:test";

import dossier from "../metadata/candidate-review-dossier-2026.json" with { type: "json" };
import provisional from "../metadata/provisional-candidate-evidence-2026.json" with { type: "json" };

test("candidate dossier accounts for every quarantined record", () => {
  assert.equal(dossier.summary.stagedRecords, provisional.records.length);
  assert.equal(dossier.families.reduce((sum, family) => sum + family.records, 0), provisional.records.length);
  assert.equal(dossier.summary.recordsRecommendedForAcceptance, provisional.records.length);
  assert.equal(dossier.summary.recommendEvidenceAcceptance, 5);
  assert.equal(new Set(dossier.families.map((family) => family.authority)).size, dossier.families.length);
});

test("candidate dossier preserves the exact coverage gaps", () => {
  assert.equal(dossier.summary.assemblyContests, 82);
  assert.equal(dossier.summary.councilRegions, 8);
  assert.equal(dossier.summary.duplicateIdentities, 0);
  assert.equal(dossier.summary.unclassifiedContests, 0);
  assert.deepEqual(dossier.missingAssemblyContests, ["Dandenong", "Kalkallo", "Lowan", "Mornington", "Thomastown", "Warrandyte"]);
});

test("candidate evidence approval remains separate from nomination and model use", () => {
  assert.equal(dossier.status, "approved-as-endorsed-evidence");
  assert.equal(dossier.summary.acceptedRecords, 188);
  assert.equal(dossier.summary.acceptedAssemblyContests, 82);
  assert.equal(dossier.decision.officialNomination, false);
  assert.equal(dossier.decision.forecastUse, "excluded");
  assert.match(dossier.policy, /separate human decision/i);
  assert.ok(dossier.families.every((family) => family.evidenceRecommendation === "accept-as-endorsed-evidence"));
  assert.ok(dossier.families.every((family) => family.requiredChecks.some((check) => /official nomination/i.test(check))));
  assert.ok(dossier.knownScopeGaps.some((gap) => /independents/i.test(gap)));
});

