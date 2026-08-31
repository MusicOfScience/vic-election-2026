import { CircleAlert, ExternalLink, FileCheck2, ShieldCheck, UsersRound } from "lucide-react";
import dossier from "../metadata/candidate-review-dossier-2026.json";

function recommendationLabel(value: string) {
  return value === "accept-as-endorsed-evidence" ? "Recommend evidence acceptance" : "Hold for record review";
}

export function CandidateReviewDossier() {
  return <section className="surface candidate-review-dossier" aria-labelledby="candidate-review-heading">
    <div className="section-heading candidate-review-heading">
      <div><p className="eyebrow">Governed candidate review</p><h3 id="candidate-review-heading">188 party-endorsed records are ready for a human evidence decision.</h3><p className="section-subcopy">Acceptance would record what each party currently publishes. It would not make a candidate VEC-nominated or add a candidate effect to the forecast.</p></div>
      <span className="candidate-review-status"><CircleAlert size={15} />Awaiting approval</span>
    </div>
    <div className="candidate-review-summary" aria-label="Candidate review summary">
      <article><strong>{dossier.summary.stagedRecords}</strong><span>quarantined records reviewed</span></article>
      <article><strong>{dossier.summary.sourceFamilies}</strong><span>official party source families</span></article>
      <article><strong>{dossier.summary.assemblyContests}/88</strong><span>Assembly districts covered</span></article>
      <article><strong>{dossier.summary.councilRegions}/8</strong><span>Council regions covered</span></article>
    </div>
    <div className="candidate-review-list">
      {dossier.families.map((family) => <details className="candidate-review-item" key={family.authority}>
        <summary>
          <span className="candidate-review-icon"><ShieldCheck size={16} /></span>
          <span className="candidate-review-name"><strong>{family.authority}</strong><small>{family.records} records · {family.assemblyContests} Assembly districts · {family.councilRegions} Council regions</small></span>
          <span className="candidate-review-recommendation"><b>{recommendationLabel(family.evidenceRecommendation)}</b><small>Party endorsement only; no automatic promotion</small></span>
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
    <p className="candidate-review-policy"><strong>Recommended decision:</strong> accept all five official-source families as provisional endorsed evidence, preserve the six-seat gap, and keep candidate model weights at zero until local effects are validated.</p>
  </section>;
}

