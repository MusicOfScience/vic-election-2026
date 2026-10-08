import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

// Validate this proposed contract, never approve it or adapt a release gate.
export function validateNextValidationProtocol(
  audit = read("metadata/validation-evidence-contamination-audit.json"),
  protocol = read("metadata/model-vnext-validation-protocol.json"),
) {
  assert.equal(audit.schemaVersion, 1);
  assert.equal(protocol.schemaVersion, 1);
  const units = new Map(audit.units.map((u) => [u.id, u]));
  assert.equal(units.size, audit.units.length, "duplicate evidence unit");
  for (const unit of units.values()) {
    assert.ok(Object.hasOwn(audit.classificationDefinitions, unit.classification));
    assert.ok(unit.provenance.length > 40, "classification requires provenance");
    assert.equal(unit.certifiesProd10, false, "cannot reopen PROD 1.0");
    assert.equal(Object.keys(unit.exposureDimensions).length, 13);
    if (unit.id !== "vic_2026_general_election") {
      assert.equal(unit.unconsumedEmpiricalUnit, false, "no audited fresh historical unit");
      assert.notEqual(unit.classification, "UNCONSUMED_CANDIDATE", "cannot relabel exposed/unaudited evidence fresh");
    }
  }
  for (const year of [2010, 2014, 2022]) assert.equal(units.get(`vic_la_${year}`).classification, "CONSUMED_AS_VALIDATION");
  assert.equal(units.get("vic_la_2018").classification, "POST_HOC_DIAGNOSTIC_ONLY");
  assert.equal(units.get("vic_2006_general").classification, "CONSUMED_AS_MODEL_INPUT");
  assert.equal(units.get("simulation_studies").classification, "NON_EMPIRICAL");
  assert.equal(units.get("vic_2026_general_election").classification, "UNCONSUMED_CANDIDATE");
  assert.equal(units.get("vic_2026_general_election").unconsumedEmpiricalUnit, true);
  assert.deepEqual(audit.conclusion.confirmedUnconsumedHistoricalCompleteElectionHoldouts, []);
  assert.deepEqual(audit.conclusion.prospectiveEmpiricalUnits, ["vic_2026_general_election"]);
  assert.equal(audit.conclusion.preElectionCompleteModelProductionFeasible, false);
  assert.equal(audit.conclusion.productionAuthorisation, "closed");
  assert.equal(protocol.status, "proposed-awaiting-owner-review", "activation requires separate reviewed change");
  assert.equal(protocol.approval, null);
  for (const field of ["scoringAuthorised", "targetOutcomesLoaded", "snapshotsAreIndependentElections", "simulationCountsAsEmpirical", "productionCanOpenAutomatically"]) assert.equal(protocol[field], false, field);
  assert.equal(protocol.freezeBeforeScoring, true);
  assert.equal(protocol.simulationRole.empiricalElectionCount, 0);
  assert.equal(protocol.independentElectionCount, 1);
  assert.deepEqual(protocol.validationUnits, ["vic_2026_general_election"]);
  assert.deepEqual(protocol.selectedHistoricalHoldouts, []);
  assert.deepEqual(protocol.sealing.currentlySealedSnapshots, []);
  assert.ok(protocol.sealing.activationRequirements.length >= 3);
  assert.equal(protocol.snapshots.filter((s) => s.role === "primary").length, 1);
  assert.equal(protocol.snapshots.find((s) => s.role === "primary").id, "final_pre_election");
  const expectedCutoffs = [null, "2026-11-03T20:00:00+11:00", "2026-11-09T12:00:00+11:00", "2026-11-17T23:59:59+11:00", "2026-11-27T23:59:59+11:00"];
  assert.deepEqual(protocol.snapshots.map((s) => s.cutoff), expectedCutoffs, "changed cutoffs require prospectively reviewed version");
  assert.deepEqual(protocol.snapshots.map((s) => s.id), ["post_freshwater_registration", "writ_roll_close", "nominations_close", "pre_early_voting", "final_pre_election"]);
  for (const snapshot of protocol.snapshots) assert.equal(snapshot.electionUnit, "vic_2026_general_election");
  assert.equal(protocol.model.forecastId, "vic_2026_experimental_joint_v1");
  assert.equal(protocol.model.seed, 20260826);
  assert.equal(protocol.model.simulations, 5000);
  assert.deepEqual(protocol.model.allowedConfigurationChanges, ["as_of"]);
  assert.equal(protocol.model.structuralChangesRequireNewModelVersion, true);
  assert.match(protocol.model.baseCommit, /^[0-9a-f]{40}$/);
  assert.equal(protocol.model.baseCommit, audit.baseCommit);
  assert.equal(protocol.model.baselineForecastSha256, "a1b9f98566931293edbcaf7edc320e90778feffff401d8fbc69e3abb2328eff2");
  assert.ok(Object.keys(protocol.model.engineSha256).length > 5);
  for (const [path, expected] of Object.entries(protocol.model.engineSha256)) assert.equal(hash(readFileSync(resolve(root, path))), expected, `model behaviour changed: ${path}`);
  const config = readFileSync(resolve(root, protocol.model.configurationPath), "utf8");
  assert.equal(hash(config.replace(/^as_of:.*\n/m, "")), protocol.model.structuralConfigurationSha256, "structural configuration changed");
  assert.equal(Object.keys(audit.frozenHistoricalSha256).length, 20);
  for (const [path, expected] of Object.entries(audit.frozenHistoricalSha256)) assert.equal(hash(readFileSync(resolve(root, path))), expected, `frozen history changed: ${path}`);
  assert.deepEqual(protocol.comparators.map((c) => c.id), ["prior_result", "uniform_swing"]);
  for (const field of ["winnerProbability", "primaryVotes", "assemblySeats", "council", "finalPairs", "aggregation", "missing"]) assert.ok(protocol.metrics[field]);
  for (const field of ["PASS", "FAIL", "performance", "stop", "newProtocol", "bugFixes"]) assert.ok(protocol.decisionRules[field]);
  return { status: "valid-draft", independentElectionCount: 1, scoringAuthorised: false, productionAuthorised: false };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) console.log(JSON.stringify(validateNextValidationProtocol()));
