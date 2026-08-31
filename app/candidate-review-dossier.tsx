import { ExternalLink, FileCheck2, ShieldCheck, UsersRound } from "lucide-react";
import dossier from "../metadata/candidate-review-dossier-2026.json";
import approval from "../metadata/candidate-review-approval-2026.json";

function recommendationLabel(authority: string, value: string) {
  const decision = approval.familyDecisions.find((item) => item.authority === authority);
  if (decision?.decision === "approve") return `Accepted as ${decision.acceptedStatus} evidence`;
  return value.startsWith("accept-as-") ? "Recommend evidence acceptance" : "Hold for record review";
}

export function CandidateReviewDossier() {
  return <section className="surface candidate-review-dossier" aria-labelledby="candidate-review-heading">
    <div className="section-heading candidate-review-heading">
      <div><p className="eyebrow">Governed candidate review</p><h3 id="candidate-review-heading">194 candidate records now cover all 88 Assembly districts.</h3><p className="section-subcopy">The accepted register preserves whether evidence is announced or endorsed. It does not make a candidate VEC-nominated or add a candidate effect to the forecast.</p></div>
      <span className="candidate-review-status"><ShieldCheck size={15} />Approval recorded</span>
    </div>
    <div className="candidate-review-summary" aria-label="Candidate review summary">
      <article><strong>{dossier.summary.acceptedRecords}</strong><span>candidate records accepted</span></article>
      <article><strong>{dossier.summary.sourceFamilies}</strong><span>reviewed source families</span></article>
      <article><strong>{dossier.summary.assemblyContests}/88</strong><span>Assembly districts covered</span></article>
      <article><strong>{dossier.summary.councilRegions}/8</strong><span>Council regions covered</span></article>
    </div>
    <div className="candidate-review-list">
      {dossier.families.map((family) => <details className="candidate-review-item" key={family.authority}>
        <summary>
          <span className="candidate-review-icon"><ShieldCheck size={16} /></span>
          <span className="candidate-review-name"><strong>{family.authority}</strong><small>{family.records} records · {family.assemblyContests} Assembly districts · {family.councilRegions} Council regions</small></span>
          <span className="candidate-review-recommendation"><b>{recommendationLabel(family.authority, family.evidenceRecommendation)}</b><small>Provisional evidence only; no forecast use</small></span>
        </summary>
        <div className="candidate-review-detail">
          <p>{family.rationale}</p>
          <div className="candidate-review-checks"><strong><FileCheck2 size={14} />Conditions attached to acceptance</strong><ul>{family.requiredChecks.map((check) => <li key={check}>{check}</li>)}</ul></div>
          {family.sourceUrls.map((url) => <a href={url} target="_blank" rel="noreferrer" key={url}>Open reviewed source <ExternalLink size={12} /></a>)}
        </div>
      </details>)}
    </div>
    <div className="candidate-coverage-gaps" role="note">
      <UsersRound size={18} />
      <div><strong>Assembly coverage is complete.</strong><p>All 88 districts have at least one accepted candidate record. Independents, retirements, defections, replacements and formal VEC nominations remain separate evidence tasks.</p></div>
    </div>
    <p className="candidate-review-policy"><strong>Recorded decision:</strong> all eight reviewed source families are accepted at their evidenced status. The coverage gate passes, while candidate model weights stay at zero until local effects are validated.</p>
  </section>;
}
