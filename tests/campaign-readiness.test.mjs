import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildCampaignStatus } from '../scripts/build-campaign-status.mjs';
const read = (path) => JSON.parse(readFileSync(new URL('../'+path, import.meta.url),'utf8'));
test('current status expires old polling without rewriting the retained release assessment', () => {
  const current = buildCampaignStatus('2026-10-31');
  assert.equal(current.forecastStale, true);
  assert.equal(current.pollAgeDays, 33);
  assert.equal(current.readiness.summary.passedRequiredGates,4);
  assert.equal(current.readiness.gates.modelInputFreshness.passed,false);
  assert.equal(current.latestReviewedPublication,'2026-10-30');
  assert.equal(current.campaignPollsAwaitingAdmission,5);
  assert.equal(read('metadata/release-readiness.generated.json').assessedAsOf,'2026-10-08');
  assert.equal(buildCampaignStatus('2026-11-03').pollAgeDays,36);
});
test('Morgan primary composition is coherent while erroneous alternative pair is excluded', () => {
  const evidence=read('metadata/current-evidence-shadow-2026-10-31.json');
  const morgan=evidence.assemblyPolls.find(p=>p.pollster==='Roy Morgan');
  assert.equal(Object.values(morgan.primaryVote).reduce((a,b)=>a+b,0),100);
  assert.equal(morgan.alternativePairwise[1].status,'source-arithmetic-conflict-excluded');
  assert.equal(morgan.alternativePairwise[1].values.reduce((a,b)=>a+b,0),103);
  assert.equal(morgan.earlierWave.sampleSize,null);
  assert.equal(evidence.councilEvidence.modelInjection,false);
});
test('shadow outputs preserve chamber totals and are not canonical promotions',()=>{
  const report=read('metadata/current-evidence-results-2026-10-31.json');
  assert.equal(report.canonicalModelInputsChanged,false);
  assert.equal(report.scenarioEvidencePromoted,false);
  assert.equal(report.simulationsPerScenario,5000);
  for(const scenario of Object.values(report.scenarios)){
    const parties=Object.values(scenario.summary.assembly.parties);
    assert.ok(Math.abs(parties.reduce((n,p)=>n+p.meanSeats,0)-88)<1e-8);
    assert.ok(Math.abs(parties.reduce((n,p)=>n+p.majorityProbability,0)+scenario.summary.assembly.hungProbability-1)<1e-8);
  }
});
