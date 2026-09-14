import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { validateModelValidationEvidence } from "../scripts/validate-model-validation-evidence.mjs";

const contract = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-contract.json", import.meta.url), "utf8"));
const inventory = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-inventory.json", import.meta.url), "utf8"));
const crosswalk = JSON.parse(readFileSync(new URL("../model/config/historical-party-family-crosswalk.json", import.meta.url), "utf8"));
const councilRules = JSON.parse(readFileSync(new URL("../model/config/historical-council-count-rules.json", import.meta.url), "utf8"));
const historicalCycles = JSON.parse(readFileSync(new URL("../model/config/historical-validation-cycles.json", import.meta.url), "utf8"));
const outcomeAvailability = JSON.parse(readFileSync(new URL("../metadata/historical-assembly-outcome-availability.json", import.meta.url), "utf8"));

test("requires evidence matching the complete probability model", () => {
  const byId = Object.fromEntries(contract.components.map((component) => [component.id, component]));
  assert.equal(contract.minimumWalkForwardCycles, 4);
  assert.equal(contract.automaticGateOpening, false);
  assert.equal(byId["boundary-aligned-tpp-outcomes"].status, "complete");
  assert.equal(byId["pre-election-poll-vintages"].status, "partial");
  assert.equal(byId["district-primary-votes-and-party-crosswalk"].status, "complete");
  assert.equal(byId["ballot-and-contest-slates"].status, "partial");
  assert.equal(byId["preference-flows-and-final-pairs"].status, "partial");
  assert.equal(byId["council-results-and-count-rules"].status, "complete");
  assert.equal(byId["frozen-historical-model-configurations"].status, "partial");
  assert.ok(contract.promotionMetrics.includes("multi-class Brier score"));
  assert.ok(contract.promotionMetrics.includes("log loss"));
  assert.deepEqual(crosswalk.targetFamilies, ["ALP", "Coalition", "Greens", "One Nation", "Other/Independent"]);
  assert.equal(crosswalk.unknownPartyPolicy.automaticOtherMapping, false);
  assert.equal(crosswalk.modelEligibility.historicalPrimaryInputsComplete, true);
  assert.equal(councilRules.status, "complete-cycle-pinned-authorised-legislation");
  assert.equal(councilRules.cycles.length, 4);
  assert.equal(councilRules.modelEligibility.automaticGateOpening, false);
});

test("separates the delayed Narracan contest from the November 2022 replay", () => {
  const cycle2022 = outcomeAvailability.cycles.find((cycle) => cycle.id === "vic_la_2022");
  const narracan = cycle2022.separatePostCycleContests[0];
  assert.equal(cycle2022.generalElectionDistricts, 87);
  assert.deepEqual(cycle2022.districtsWithoutGeneralElectionOutcome, ["Narracan"]);
  assert.equal(narracan.eventDate, "2023-01-28");
  assert.equal(narracan.resultEvidencePublicationDate, null);
  assert.equal(narracan.preCutoffInputEligible, false);
  assert.equal(narracan.includedInGeneralElectionScoring, false);
  assert.equal(outcomeAvailability.modelImpact.changesCurrentForecast, false);
  assert.equal(outcomeAvailability.modelImpact.automaticGateOpening, false);
  assert.deepEqual(historicalCycles.cycles.find((cycle) => cycle.id === "vic_la_2022").blockedBy, [
    "pre-election-poll-vintages",
    "ballot-and-contest-slates",
    "preference-flows-and-final-pairs",
  ]);
});

test("fingerprints every available validation artefact and keeps partial evidence fail-closed", () => {
  assert.deepEqual(validateModelValidationEvidence(), {
    complete: 3,
    partial: 4,
    missing: 0,
    total: 7,
    completeForecastBacktestReady: false,
    probabilityCalibrationReady: false,
  });
  assert.equal(inventory.negativeFeatureEvidence.demographicChallenger.outcome, "rejected");
  assert.equal(inventory.negativeFeatureEvidence.demographicChallenger.centralWeight, 0);
});
