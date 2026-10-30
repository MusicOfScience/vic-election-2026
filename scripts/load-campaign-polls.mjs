import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// The frozen sensitivity packet is immutable. Later source reconciliation lives
// in a separate review packet and must never imply approval or eligibility.
export function loadCampaignPolls(root) {
  const read = (path) => JSON.parse(readFileSync(resolve(root,path),'utf8'));
  const frozen = read('metadata/current-evidence-shadow-2026-10-31.json');
  const review = read('metadata/poll-admission-review-2026-10-31.json');
  const originals = new Map(frozen.assemblyPolls.map(poll=>[poll.id,poll]));
  if(review.assemblyPolls.length!==originals.size || new Set(review.assemblyPolls.map(poll=>poll.id)).size!==originals.size) throw new Error("Campaign review must preserve every wave exactly once");
  return review.assemblyPolls.map((poll)=>{
    const prior=originals.get(poll.id);
    if(!prior) throw new Error('Unrecognised campaign wave in admission review');
    if(JSON.stringify(prior.primaryVote)!==JSON.stringify(poll.primaryVote)) throw new Error('Admission review cannot silently alter reported primaries');
    if(poll.modelEligibilityDecision!==prior.modelEligibilityDecision) throw new Error('Source reconciliation cannot change eligibility decisions');
    return poll;
  });
}
