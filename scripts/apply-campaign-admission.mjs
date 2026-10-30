import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=path=>JSON.parse(readFileSync(resolve(root,path),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const approval=read('metadata/poll-admission-approval-2026-10-31.json');
const manifest=read(approval.proposalManifestPath);
if(approval.approved!==true || approval.reviewerRole!=='project-owner' || approval.productionAuthorised || approval.preferenceModelChangeAuthorised || approval.prospectiveSealAuthorised) throw new Error('Approved experimental input-only scope required');
if(hash(readFileSync(resolve(root,approval.proposalManifestPath)))!==approval.proposalManifestSha256) throw new Error('Proposal manifest changed after approval');
for(const [path,sha] of Object.entries(manifest.files)) if(hash(readFileSync(resolve(root,path)))!==sha) throw new Error('Approved proposal rows changed');
const expected=manifest.requestedActions.modelAdmission.slice().sort();
const eligible=approval.modelEligibilityDecisions.filter(d=>d.decision==='eligible');
if(JSON.stringify(eligible.map(d=>d.pollId).sort())!==JSON.stringify(expected)) throw new Error('Admission set differs from approved bundle');
function parse(text){const rows=[];let row=[],cell='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'&&quoted&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=!quoted;else if(c===','&&!quoted){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);cell='';if(row.some(Boolean))rows.push(row);row=[];}else cell+=c;}if(cell||row.length){row.push(cell);rows.push(row);}const[headers,...data]=rows;return{headers,rows:data.map(values=>Object.fromEntries(headers.map((h,i)=>[h,values[i]??'']))) };}
const cell=v=>/[",\n\r]/.test(String(v??''))?'"'+String(v).replaceAll('"','""')+'"':String(v??'');
const csv=table=>table.headers.join(',')+'\n'+table.rows.map(row=>table.headers.map(h=>cell(row[h])).join(',')).join('\n')+'\n';
const eventPath='model/data/processed/poll_events_seed.csv',estimatePath='model/data/processed/poll_estimates_seed.csv';
const events=parse(readFileSync(resolve(root,eventPath),'utf8')),estimates=parse(readFileSync(resolve(root,estimatePath),'utf8'));
const proposedEvents=parse(readFileSync(resolve(root,'metadata/poll-admission-proposal-2026-10-31/poll-events.csv'),'utf8'));
const proposedEstimates=parse(readFileSync(resolve(root,'metadata/poll-admission-proposal-2026-10-31/poll-estimates.csv'),'utf8'));
const existing=events.rows.filter(r=>expected.includes(r.poll_id));
if(existing.length!==0 && existing.length!==2) throw new Error('Partial admission requires investigation');
if(!existing.length) for(const path of [eventPath,estimatePath]) if(hash(readFileSync(resolve(root,path)))!==manifest.canonicalBaseline[path]) throw new Error('Canonical registry changed since approved proposal');
for(const row of proposedEvents.rows){row.notes=row.notes.replace('PROPOSAL ONLY: not approved; no canonical input changed. ','Owner-approved 31 October 2026. ');const prior=events.rows.find(r=>r.poll_id===row.poll_id);if(prior){if(JSON.stringify(prior)!==JSON.stringify(row))throw new Error('Existing admitted row differs: '+row.poll_id);}else events.rows.push(row);}
for(const row of proposedEstimates.rows){row.notes='Owner-approved 31 October 2026; complete published composition retained.';const prior=estimates.rows.find(r=>r.poll_id===row.poll_id&&r.party_id===row.party_id);if(prior){if(JSON.stringify(prior)!==JSON.stringify(row))throw new Error('Admitted estimate differs');}else estimates.rows.push(row);}
events.rows.sort((a,b)=>a.fieldwork_end.localeCompare(b.fieldwork_end)||a.poll_id.localeCompare(b.poll_id));const order=new Map(events.rows.map((r,i)=>[r.poll_id,i]));estimates.rows.sort((a,b)=>order.get(a.poll_id)-order.get(b.poll_id));
const writes=new Map([[eventPath,csv(events)],[estimatePath,csv(estimates)]]);
const records=read('metadata/poll-admission-review-2026-10-31.json').assemblyPolls;
const accepted=read('metadata/accepted-polls-2026.json');
for(const decision of eligible){const record=records.find(r=>r.id===decision.evidenceId);const entry={...record,evidenceId:record.id,publicationDate:record.pollPublicationDate,modelEligible:true,status:'accepted-model-eligible',modelEligibilityDecision:'eligible',blocker:null,verificationStatus:'human-reviewed-source-evidence',reviewerRole:'project-owner',reviewedAt:approval.approvedAt,approvalPath:'metadata/poll-admission-approval-2026-10-31.json'};const i=accepted.polls.findIndex(r=>r.evidenceId===record.id);if(i<0)accepted.polls.push(entry);else if(JSON.stringify(accepted.polls[i])!==JSON.stringify(entry))throw new Error('Accepted evidence differs from approved record');}
const reviews=read('metadata/discovery-review-decisions.json');
for(const d of approval.evidenceDecisions){const record=records.find(r=>r.id===d.evidenceId);const row={evidenceId:d.evidenceId,recordHash:hash(JSON.stringify(record)),kind:'poll',decision:d.decision,reviewer:'project-owner',reviewedAt:approval.approvedAt,note:'Approved two-wave bundle; other campaign waves held. See metadata/poll-admission-approval-2026-10-31.json',modelInputsChanged:d.decision==='approve'};const prior=reviews.decisions.find(r=>r.evidenceId===d.evidenceId);if(!prior)reviews.decisions.push(row);else if(JSON.stringify(prior)!==JSON.stringify(row))throw new Error('Review record conflict');}
reviews.decisions.sort((a,b)=>Number(a.kind!=='poll')-Number(b.kind!=='poll'));
const decisions=read('metadata/poll-model-eligibility-decisions.json');
for(const row of approval.modelEligibilityDecisions){const prior=decisions.decisions.find(r=>r.evidenceId===row.evidenceId);if(!prior)decisions.decisions.push(row);else if(JSON.stringify(prior)!==JSON.stringify(row))throw new Error('Eligibility decision conflict');}
for(const[path,value]of [['metadata/accepted-polls-2026.json',accepted],['metadata/discovery-review-decisions.json',reviews],['metadata/poll-model-eligibility-decisions.json',decisions]]) writes.set(path,JSON.stringify(value,null,2)+'\n');
const coverage=read('metadata/poll-coverage-ledger-2026.json');
for(const [familyId,pollster] of [['demosau','DemosAU'],['roy-morgan','Roy Morgan']]){
 const family=coverage.sourceFamilies.find(row=>row.id===familyId);
 family.canonicalModelEligiblePollIds=events.rows.filter(row=>row.pollster===pollster&&row.model_eligible==='True').map(row=>row.poll_id);
 family.latestAdmissionDecision='metadata/poll-admission-approval-2026-10-31.json';
 family.nextAction='Continue monitoring; owner-approved September DemosAU and latest Morgan are canonical. Other staged waves remain separately governed.';
}
writes.set('metadata/poll-coverage-ledger-2026.json',JSON.stringify(coverage,null,2)+'\n');
for(const[path,text]of writes){if(process.argv.includes('--check')){if(readFileSync(resolve(root,path),'utf8')!==text)throw new Error('Campaign admission drift: '+path);}else writeFileSync(resolve(root,path),text);}
console.log('Verified owner-approved two-wave admission; all other campaign waves held.');
