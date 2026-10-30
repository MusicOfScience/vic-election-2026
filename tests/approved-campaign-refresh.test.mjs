import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
test('owner approval admits exactly the approved two observations with fixed experimental scope',()=>{
 const approval=read('metadata/poll-admission-approval-2026-10-31.json');
 assert.equal(approval.approved,true);assert.equal(approval.productionAuthorised,false);assert.equal(approval.preferenceModelChangeAuthorised,false);assert.equal(approval.prospectiveSealAuthorised,false);
 assert.deepEqual(approval.modelEligibilityDecisions.filter(d=>d.decision==='eligible').map(d=>d.pollId).sort(),['demosau_2026-09','roy_morgan_2026-10-29']);
 assert.equal(approval.modelEligibilityDecisions.filter(d=>d.decision==='hold').length,3);
 execFileSync(process.execPath,['scripts/apply-campaign-admission.mjs','--check']);
 execFileSync(process.execPath,['scripts/apply-approved-poll-review.mjs','--check']);
});
test('refresh reproduces approved sensitivity and preserves the historical archive',()=>{
 const audit=read('metadata/forecast-refresh-2026-10-31.json');
 assert.equal(audit.canonicalPolling.eligibleBefore,13);assert.equal(audit.canonicalPolling.eligibleAfter,15);
 assert.equal(audit.integrity.matchesApprovedSensitivity,true);assert.equal(audit.integrity.modelParametersUnchanged,true);
 assert.equal(audit.integrity.validationArchiveFilesUnchanged,105);
 assert.equal(audit.assembly.allDistrictChanges.length,88);
 assert.equal(audit.assembly.materialDistricts.length,50);
 assert.equal(audit.assembly.favouredPartyChanges.length,4);
 assert.equal(audit.assembly.likelyFinalPairChanges.length,3);
 execFileSync('python3',['scripts/build-approved-refresh-audit.py','--check']);
});
test('current readiness is fresh but production gates remain closed',()=>{
 const r=read('metadata/release-readiness.generated.json');
 assert.equal(r.assessedAsOf,'2026-10-31');assert.equal(r.summary.passedRequiredGates,6);
 assert.equal(r.gates.criticalSourceFreshness.passed,true);assert.equal(r.gates.modelInputFreshness.passed,true);
 for(const gate of ['completeForecastBacktest','probabilityCalibration','productionAuthorisation']) assert.equal(r.gates[gate].passed,false);
});
