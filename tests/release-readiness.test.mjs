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
  assert.equal(readiness.gates.productionAuthorisation.passed, false);
  assert.equal(readiness.policy, "retain-last-valid-forecast");
});
