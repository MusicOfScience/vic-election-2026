import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { validateModelValidationEvidence } from "../scripts/validate-model-validation-evidence.mjs";
import { validateHistoricalPollReusePolicy } from "../scripts/validate-historical-poll-reuse-policy.mjs";
import { validateHistoricalPartyFamilyAvailability } from "../scripts/validate-historical-party-family-availability.mjs";
import { validateHistoricalReplayInputReadiness } from "../scripts/validate-historical-replay-input-readiness.mjs";

const contract = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-contract.json", import.meta.url), "utf8"));
const inventory = JSON.parse(readFileSync(new URL("../metadata/model-validation-evidence-inventory.json", import.meta.url), "utf8"));
const crosswalk = JSON.parse(readFileSync(new URL("../model/config/historical-party-family-crosswalk.json", import.meta.url), "utf8"));
const councilRules = JSON.parse(readFileSync(new URL("../model/config/historical-council-count-rules.json", import.meta.url), "utf8"));
const historicalCycles = JSON.parse(readFileSync(new URL("../model/config/historical-validation-cycles.json", import.meta.url), "utf8"));
const outcomeAvailability = JSON.parse(readFileSync(new URL("../metadata/historical-assembly-outcome-availability.json", import.meta.url), "utf8"));
const pollQueue = JSON.parse(readFileSync(new URL("../metadata/historical-poll-reconstruction-queue.json", import.meta.url), "utf8"));
const pollEvidence = JSON.parse(readFileSync(new URL("../metadata/historical-poll-reconstruction-evidence.json", import.meta.url), "utf8"));

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

test("separates historical poll provenance, methodology and reuse basis", () => {
  assert.deepEqual(validateHistoricalPollReusePolicy(), {
    policyClasses: 7,
    adjudicatedCases: 1,
    replayEligibleCases: 1,
  });
});

test("derives cycle-aware Assembly party availability from candidate evidence", () => {
  assert.deepEqual(validateHistoricalPartyFamilyAvailability(), {
    cycles: 4,
    verifiedFromCandidateEvidence: true,
    historicalOnpInactiveThrough2018: true,
  });
});

test("records owner-approved replay input without making a cycle runnable", () => {
  assert.deepEqual(validateHistoricalReplayInputReadiness(), {
    cycles: 4,
    approvedReplayObservations: 3,
    runnableCycles: 0,
  });
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
  assert.equal(pollQueue.coverage.candidateRows, 200);
  assert.equal(pollQueue.coverage.sourceFamilies, 18);
  assert.equal(pollQueue.coverage.sourceMatchedRows, 64);
  assert.equal(pollQueue.coverage.replayEligibleRows, 0);
  assert.equal(pollQueue.candidateSource.observationVoteRowsWritten, false);
  assert.equal(pollQueue.modelImpact.productionAuthorisation, false);
  const essentialEvidence = pollEvidence.sourceFamilies.find((family) => family.id === "essential");
  const newspollEvidence = pollEvidence.sourceFamilies.find((family) => family.id === "newspoll");
  const smsMorganEvidence = pollEvidence.sourceFamilies.find((family) => family.id === "sms-morgan");
  assert.equal(essentialEvidence.matchedObservations.length, 33);
  assert.equal(essentialEvidence.unresolvedObservations.length, 8);
  assert.equal(essentialEvidence.coverage.explicitMethodRows, 12);
  assert.equal(essentialEvidence.coverage.replayEligibleRows, 0);
  assert.equal(newspollEvidence.matchedObservations.length, 7);
  assert.equal(newspollEvidence.unresolvedObservations.length, 32);
  assert.equal(newspollEvidence.coverage.explicitMethodRows, 6);
  assert.equal(newspollEvidence.coverage.replayEligibleRows, 0);
  assert.equal(smsMorganEvidence.matchedObservations.length, 24);
  assert.equal(smsMorganEvidence.unresolvedObservations.length, 9);
  assert.equal(smsMorganEvidence.coverage.explicitMethodRows, 23);
  assert.equal(smsMorganEvidence.coverage.replayEligibleRows, 0);
});

test("distinguishes archived poll documents from a historical link to a current graphic", () => {
  const family = pollEvidence.sourceFamilies.find((entry) => entry.id === "newspoll");
  const mirrorRow = family.matchedObservations.find((row) => row.leadMidDate === "2011-12-01");
  const mirror = family.sources.find((source) => source.id === mirrorRow.sourceId);
  assert.equal(mirror.sourceType, "archived-contemporaneous-mirror-of-first-party-pollster-pdf");
  assert.equal(mirrorRow.evidenceAvailableByDate, mirror.archivedAt);
  assert.notEqual(mirrorRow.evidenceAvailableByDate, mirror.publishedAt);
  assert.equal(mirrorRow.explicitMethodSourceId, mirror.id);

  const graphicRow = family.matchedObservations.find((row) => row.leadMidDate === "2015-06-01");
  const graphic = family.sources.find((source) => source.id === graphicRow.sourceId);
  assert.equal(graphicRow.evidenceAvailableByDate, graphic.availabilityEvidence.archivedAt);
  assert.equal(graphicRow.sampleSize, 1154);
  assert.match(graphic.availabilityEvidence.limitation, /does not preserve the graphic binary/);
  assert.equal(graphicRow.explicitMethodSourceId, null);
  assert.equal(graphicRow.replayEligible, false);
});
