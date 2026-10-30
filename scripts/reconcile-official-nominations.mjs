import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyContest, loadContestUniverse } from './candidate-contests.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const normal = (s) => String(s).normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase();
export function reconcile(packet, registry, universe) {
  const source = new URL(packet.sourceUrl);
  if (source.protocol !== 'https:' || !['vec.vic.gov.au','www.vec.vic.gov.au'].includes(source.hostname)) throw new Error('Official nomination source must be VEC HTTPS');
  if (!Number.isFinite(Date.parse(packet.capturedAt)) || Date.parse(packet.capturedAt) < Date.parse(registry.officialNominations.open)) throw new Error('Capture predates nomination opening or has no valid timestamp');
  if (!Array.isArray(packet.candidates) || !packet.candidates.length) throw new Error('Candidate list is empty');
  const key = (row) => `${normal(row.contest)}|${normal(row.name)}`;
  const accepted = new Map(registry.candidates.map(row=>[key(row),row]));
  const seen = new Set(); const positions = new Set(); const contests = new Set();
  const rows = packet.candidates.map((row) => {
    const contest = classifyContest(row.contest,universe);
    if (!contest || !row.name?.trim() || !row.party?.trim() || !String(row.ballotOrder ?? '').trim()) throw new Error('Candidate requires known contest, name, party and official ballot order');
    const canonical = {...row,contest:contest.canonicalContest}; const identity=key(canonical);
    const position=`${normal(canonical.contest)}|${String(row.ballotOrder)}`;
    if (seen.has(identity) || positions.has(position)) throw new Error('Duplicate candidate or ballot position');
    seen.add(identity); positions.add(position); contests.add(normal(canonical.contest));
    const prior=accepted.get(identity);
    return {...canonical,chamber:contest.chamber,review:prior ? (normal(prior.party)===normal(row.party) ? 'same-person-party-label-matches' : 'party-label-review-required') : 'new-or-name-reconciliation-required'};
  });
  const missingContests=[...universe.assembly.values(),...universe.council.values()].filter(contest=>!contests.has(normal(contest)));
  if (packet.complete === true && missingContests.length) throw new Error('Claimed complete list omits contests');
  return { schemaVersion:1, mode:'official-list-reconciliation-review-only', sourceUrl:packet.sourceUrl,capturedAt:packet.capturedAt, complete:packet.complete===true && !missingContests.length, missingContests, rows, acceptedNotInSuppliedList:registry.candidates.filter(row=>!seen.has(key(row))).map(({name,contest,party})=>({name,contest,party})), policy:'No registry or model mutation. Missing names are not automatically withdrawals. Party aliases, replacements and identity differences require review. Complete means supplied contest coverage, not independently verified VEC completeness.' };
}
function main(){
  const i=process.argv.indexOf('--official'); const j=process.argv.indexOf('--output');
  if(i<0 || j<0) throw new Error('Usage: --official captured-vec.json --output reconciliation.json');
  const packet=JSON.parse(readFileSync(resolve(process.argv[i+1]),'utf8'));
  const registry=JSON.parse(readFileSync(resolve(root,'metadata/candidates-2026.json'),'utf8'));
  writeFileSync(resolve(process.argv[j+1]),JSON.stringify(reconcile(packet,registry,loadContestUniverse(root)),null,2)+'\n');
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) main();
