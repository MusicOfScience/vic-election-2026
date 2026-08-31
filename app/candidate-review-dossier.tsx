import { ExternalLink, FileCheck2, ShieldCheck, UsersRound } from "lucide-react";
import dossier from "../metadata/candidate-review-dossier-2026.json";
import approval from "../metadata/candidate-review-approval-2026.json";

function recommendationLabel(authority: string, value: string) {
  const decision = approval.familyDecisions.find((item) => item.authority === authority);
  if (decision?.decision === "approve") return "Accepted as endorsed evidence";
  return value === "accept-as-endorsed-evidence" ? "Recommend evidence acceptance" : "Hold for record review";
}

export function CandidateReviewDossier() {
  return <section className="surface candidate-review-dossier" aria-labelledby="candidate-review-heading">
    <div className="section-heading candidate-review-heading">
      <div><p className="eyebrow">Governed candidate review</p><h3 id="candidate-review-heading">188 party-endorsed records have passed the evidence review.</h3><p className="section-subcopy">The accepted register records what each party currently publishes. It does not make a candidate VEC-nominated or add a candidate effect to the forecast.</p></div>
      <span className="candidate-review-status"><ShieldCheck size={15} />Approval recorded</span>
    </div>
    <div className="candidate-review-summary" aria-label="Candidate review summary">
      <article><strong>{dossier.summary.acceptedRecords}</strong><span>endorsed records accepted</span></article>
      <article><strong>{dossier.summary.sourceFamilies}</strong><span>official party source families</span></article>
      <article><strong>{dossier.summary.assemblyContests}/88</strong><span>Assembly districts covered</span></article>
      <article><strong>{dossier.summary.councilRegions}/8</strong><span>Council regions covered</span></article>
    </div>
    <div className="candidate-review-list">
      {dossier.families.map((family) => <details className="candidate-review-item" key={family.authority}>
        <summary>
          <span className="candidate-review-icon"><ShieldCheck size={16} /></span>
          <span className="candidate-review-name"><strong>{family.authority}</strong><small>{family.records} records · {family.assemblyContests} Assembly districts · {family.councilRegions} Council regions</small></span>
          <span className="candidate-review-recommendation"><b>{recommendationLabel(family.authority, family.evidenceRecommendation)}</b><small>Party endorsement only; no forecast use</small></span>
        </summary>
        <div className="candidate-review-detail">
          <p>{family.rationale}</p>
          <div className="candidate-review-checks"><strong><FileCheck2 size={14} />Conditions attached to acceptance</strong><ul>{family.requiredChecks.map((check) => <li key={check}>{check}</li>)}</ul></div>
          {family.sourceUrls.map((url) => <a href={url} target="_blank" rel="noreferrer" key={url}>Open official party source <ExternalLink size={12} /></a>)}
        </div>
      </details>)}
    </div>
    <div className="candidate-coverage-gaps" role="note">
      <UsersRound size={18} />
      <div><strong>Coverage is broad, not complete.</strong><p>The uncovered Assembly districts are {dossier.missingAssemblyContests.join(", ")}. Independents, retirements, defections, replacements and formal VEC nominations remain separate evidence tasks.</p></div>
    </div>
    <p className="candidate-review-policy"><strong>Recorded decision:</strong> all five official-source families are accepted as endorsed evidence. The six-seat gap remains, and candidate model weights stay at zero until local effects are validated.</p>
  </section>;
}

