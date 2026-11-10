import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import review from "../metadata/november-poll-evidence-review-2026-11-11.json" with {type:"json"};
import { buildSeatIntegrityAudit, familyFromRegisteredParty, preferencePriorFromSource, meanPathCount } from "../scripts/audit-2026-model-mechanics.mjs";

const root = resolve(import.meta.dirname,"..");

test("November poll-review sources are held and cannot silently enter the model", () => {
  assert.equal(review.ownerApprovalRecorded, false);
  assert.equal(review.invariants.canonicalPollRegistryChanged, false);
  assert.equal(review.invariants.canonicalForecastChanged, false);
  assert.equal(review.invariants.proposedInputRowsAdded, 0);
  assert.ok(review.evidence.length >= 4);
  assert.ok(review.evidence.every((x) => x.modelEligibility === "hold" && /^https:/.test(x.sourceUrl)));
  const resolveWave = review.evidence.find((x) => x.id.startsWith("resolve-"));
  assert.deepEqual(resolveWave.alternativeEndDates, ["2026-11-05","2026-11-07"]);
  assert.equal(resolveWave.reportedDates.end, null);
  const demo = review.evidence.find((x) => x.id.startsWith("demosau-"));
  assert.equal(demo.otherPartyResidual.status, "computed-from-four-published-categories-not-verified-primary-report");
  assert.equal(demo.effectiveSampleSize, null);
});

test("candidate family mapping never equates blank registered party with an independent person", () => {
  assert.equal(familyFromRegisteredParty("One Nation Victoria"), "ONP");
  assert.equal(familyFromRegisteredParty("National Party of Australia - Victoria"), "LIB_NAT");
  assert.equal(familyFromRegisteredParty("Liberal Party of Australia - Victorian Division"), "LIB_NAT");
  assert.equal(familyFromRegisteredParty(null), "OTH_IND");
  assert.equal(familyFromRegisteredParty("Victorian Socialists"), "OTH_IND");
});

test("model preference matrix conditional arithmetic is recovered from actual Python engine source", () => {
  const engine = readFileSync(resolve(root,"model/src/vicforecast/forecast_2026.py"),"utf8");
  const prior = preferencePriorFromSource(engine);
  assert.equal(prior.length,5);
  assert.ok(Math.abs(prior[1][2]/(prior[1][2]+prior[1][0])-0.6623376623376623)<1e-10);
  assert.ok(Math.abs(prior[0][1]/(prior[0][1]+prior[0][4])-0.75)<1e-10);
  const votes=[25,30,25,15,5];
  const result=meanPathCount(votes,prior);
  assert.ok(["ALP","LIB_NAT","ONP","GRN","OTH_IND"].includes(result.winner));
  assert.ok(result.finalWinnerSharePercent>=50 && result.finalWinnerSharePercent<=100);
  assert.equal(result.eliminations.length,3);
});

test("complete November integrity report discloses core 31 October model path risks", () => {
  const result = buildSeatIntegrityAudit(root);
  assert.equal(result.status,"frozen-reference-output-diagnostic-not-calibration-or-forecast-refresh");
  assert.equal(result.canonicalDataChanged,false);
  assert.equal(result.statisticalProductionGatesChanged,false);
  assert.equal(result.eligibleNewPolls,0);
  assert.equal(result.counts.assemblyDistricts,88);
  assert.equal(result.candidateAvailability.allFiveFamilyRepresentativesPerSeat,true);
  assert.equal(result.counts.missingNominatedPartyFamilies,0);
  assert.deepEqual(result.counts.coalitionNomineeDuplicationSeats,[{seat:"Ripon",count:2}]);
  assert.equal(result.allSeats.length,88);
  if (result.referenceAsOf==="2026-10-31"){
    assert.equal(result.counts.onpWinFrequencyAtLeast80Percent,6);
    assert.equal(result.counts.largeResidualPrimaryNegligibleResidualWins,3);
    const hawthorn=result.allSeats.find(x=>x.seat==="Hawthorn");
    assert.ok(hawthorn.primaryVote.OTH_IND>27 && hawthorn.winFrequency.OTH_IND<.01);
    assert.equal(hawthorn.candidateFamilyCounts.OTH_IND,3);
    assert.equal(result.pakenhamIndependentDiagnostic.effectiveSample,289);
    assert.ok(Math.abs(result.pakenhamIndependentDiagnostic.gapInPercentagePoints-12.411995771479337)<.001);
    const pakenham=result.allSeats.find(x=>x.seat==="Pakenham");
    assert.equal(pakenham.modelledWinner,"LIB_NAT");
    assert.equal(pakenham.winFrequency.LIB_NAT,.8292);
  }
});

test("audit does not mistake simulated party family's seat as a named candidate prediction", () => {
  const report=buildSeatIntegrityAudit(root);
  const otherSeats=report.allSeats.filter(s=>s.primaryVote.OTH_IND>=20);
  assert.ok(otherSeats.length>=3);
  assert.ok(otherSeats.every(s=>s.candidateFamilyCounts.OTH_IND>1));
  assert.ok(report.derivedConditionalPreferenceRatios.caveat.includes("not population estimates"));
  const ids=Object.entries(report.source);
  assert.ok(ids.every(([_,source])=>/^[a-f0-9]{64}$/.test(source.sha256)));
});
