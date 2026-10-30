import { frozenResearchInput, researchAnchors } from "./frozen-research-input.mjs";
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const record = JSON.parse(readFileSync(new URL('../metadata/campaign-run-record-2026-10-31.json',import.meta.url),'utf8'));
for (const [path, expected] of Object.entries({...record.inputSha256,...record.resultSha256})) {
  const bytes=Object.hasOwn(record.inputSha256,path) ? frozenResearchInput(researchAnchors.campaignInputRef,path) : readFileSync(new URL('../'+path,import.meta.url));
  const actual=createHash('sha256').update(bytes).digest('hex');
  if(actual!==expected) throw new Error(`Campaign run drift: ${path}. Original frozen tree/result no longer matches its recorded hash.`);
}
if(record.canonicalDiff.length || record.candidateResearchPromotion || record.prospectiveSealCreated) throw new Error('Campaign record scope mismatch');
console.log('Frozen campaign input tree and preserved output hashes match.');
