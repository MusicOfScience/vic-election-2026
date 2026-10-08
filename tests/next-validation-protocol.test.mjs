import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { validateNextValidationProtocol } from "../scripts/validate-next-validation-protocol.mjs";
const audit = JSON.parse(readFileSync(new URL("../metadata/validation-evidence-contamination-audit.json", import.meta.url)));
const protocol = JSON.parse(readFileSync(new URL("../metadata/model-vnext-validation-protocol.json", import.meta.url)));
function rejects(mutate) {
  const a = structuredClone(audit), p = structuredClone(protocol);
  mutate(a, p);
  assert.throws(() => validateNextValidationProtocol(a, p));
}
test("draft preserves frozen history, engine and structural configuration", () => {
  assert.deepEqual(validateNextValidationProtocol(), { status: "valid-draft", independentElectionCount: 1, scoringAuthorised: false, productionAuthorised: false });
});
test("2018, consumed cycles and 2006 lineage cannot be relabelled fresh", () => {
  for (const id of ["vic_la_2010", "vic_la_2014", "vic_la_2018", "vic_la_2022", "vic_2006_general", "vic_2002_general"]) {
    rejects((a) => { a.units.find((u) => u.id === id).classification = "UNCONSUMED_CANDIDATE"; });
    rejects((a) => { a.units.find((u) => u.id === id).certifiesProd10 = true; });
  }
});
test("snapshots and simulations cannot manufacture election replications", () => {
  rejects((a, p) => { p.independentElectionCount = 5; });
  rejects((a, p) => { p.snapshotsAreIndependentElections = true; });
  rejects((a, p) => { p.snapshots[1].electionUnit = "vic_2026_second_election"; });
  rejects((a, p) => { p.simulationCountsAsEmpirical = true; });
  rejects((a) => { a.units.find((u) => u.id === "simulation_studies").unconsumedEmpiricalUnit = true; });
});
test("scoring, automatic production, retrospective freezes and historical selection fail closed", () => {
  rejects((a, p) => { p.freezeBeforeScoring = false; });
  rejects((a, p) => { p.scoringAuthorised = true; });
  rejects((a, p) => { p.targetOutcomesLoaded = true; });
  rejects((a, p) => { p.productionCanOpenAutomatically = true; });
  rejects((a, p) => { p.selectedHistoricalHoldouts = ["vic_1999_general"]; });
  rejects((a, p) => { p.snapshots[4].cutoff = "2026-11-29T00:00:00+11:00"; });
  rejects((a, p) => { p.model.allowedConfigurationChanges.push("simulations"); });
  rejects((a, p) => { p.model.engineSha256[Object.keys(p.model.engineSha256)[0]] = "0".repeat(64); });
});
