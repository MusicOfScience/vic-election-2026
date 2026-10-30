import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { loadCampaignPolls } from '../scripts/load-campaign-polls.mjs';
import { auditPollPromotion } from '../scripts/build-poll-promotion-audit.mjs';
const root=new URL('..',import.meta.url).pathname;
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
test('source reconciliation retains effective N without conferring model approval',()=>{
 const polls=loadCampaignPolls(root);const demos=polls.find(p=>p.pollster==='DemosAU');
 assert.equal(demos.effectiveSampleSize,572);assert.equal(demos.sampleSize,1020);
 assert.equal(demos.modelEligibilityDecision,'pending');
 assert.equal(auditPollPromotion(demos,{modelEvents:[],acceptedPolls:[]}).canPromoteNow,false);
 const newspoll=polls.find(p=>p.pollster.startsWith('Newspoll'));
 assert.equal(newspoll.pollPublicationDate,'2026-10-25');
 assert.ok(auditPollPromotion(newspoll,{modelEvents:[],acceptedPolls:[]}).blockers.includes('primary-source-reconciliation-or-reviewed-exception-required'));
});
test('concrete proposed rows are isolated and canonical baselines unchanged',()=>{
 const manifest=read('metadata/poll-admission-proposal-2026-10-31/manifest.json');
 assert.equal(manifest.approved,false);assert.equal(manifest.canonicalInputsChanged,false);
 assert.deepEqual(manifest.requestedActions.modelAdmission,['demosau_2026-09','roy_morgan_2026-10-29']);
 for(const [path,sha] of Object.entries({...manifest.files,...manifest.canonicalBaseline})) assert.equal(createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex'),sha,path);
});
test('original frozen campaign results remain intact after later review',()=>{
 const record=read('metadata/campaign-run-record-2026-10-31.json');
 for(const [path,sha] of Object.entries(record.resultSha256)) assert.equal(createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex'),sha);
});
