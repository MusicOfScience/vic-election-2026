import test from 'node:test';
import assert from 'node:assert/strict';
import { reconcile } from '../scripts/reconcile-official-nominations.mjs';
const universe={assembly:new Map([['melbourne','Melbourne']]),council:new Map([['northern metropolitan','Northern Metropolitan']])};
const registry={officialNominations:{open:'2026-11-04T09:00:00+11:00'},candidates:[{name:'Test Person',contest:'Melbourne',party:'Greens'},{name:'Absent Person',contest:'Melbourne',party:'Independent'}]};
const packet=()=>({sourceUrl:'https://www.vec.vic.gov.au/test',capturedAt:'2026-11-10T01:00:00Z',candidates:[{name:'Test Person',contest:'Melbourne',party:'Greens',ballotOrder:'1'}]});
test('official reconciliation refuses non-VEC sources and pre-nomination captures',()=>{
  assert.throws(()=>reconcile({...packet(),sourceUrl:'https://vec.vic.gov.au.example.org/test'},registry,universe),/VEC/);
  assert.throws(()=>reconcile({...packet(),capturedAt:'2026-11-01'},registry,universe),/predates/);
});
test('partial official list does not manufacture withdrawals or complete coverage',()=>{
  const original=JSON.stringify(registry);const report=reconcile(packet(),registry,universe);
  assert.equal(report.complete,false);assert.equal(report.acceptedNotInSuppliedList.length,1);
  assert.deepEqual(report.missingContests,['Northern Metropolitan']);assert.equal(JSON.stringify(registry),original);
  assert.throws(()=>reconcile({...packet(),complete:true},registry,universe),/omits contests/);
});
test('duplicate candidates, ballot positions and unknown contests fail closed',()=>{
  const p=packet();p.candidates.push({...p.candidates[0]});assert.throws(()=>reconcile(p,registry,universe),/Duplicate/);
  assert.throws(()=>reconcile({...packet(),candidates:[{...packet().candidates[0],contest:'Imaginary'}]},registry,universe),/known contest/);
});
