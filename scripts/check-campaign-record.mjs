import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const record = JSON.parse(readFileSync(new URL('../metadata/campaign-run-record-2026-10-31.json',import.meta.url),'utf8'));
for (const [path, expected] of Object.entries({...record.inputSha256,...record.resultSha256})) {
  const actual=createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex');
  if(actual!==expected) throw new Error(`Campaign run drift: ${path}. Archive this run; do not rewrite its hashes to conceal changed inputs.`);
}
if(record.canonicalDiff.length || record.candidateResearchPromotion || record.prospectiveSealCreated) throw new Error('Campaign record scope mismatch');
console.log('Campaign run input and output hashes match.');
