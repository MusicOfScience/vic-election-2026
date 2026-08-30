import { CircleAlert, ExternalLink, FileCheck2, ShieldCheck } from "lucide-react";
import manualEvidence from "../metadata/manual-source-evidence-2026.json";
import primaryEvidence from "../metadata/primary-source-evidence-2026.json";
import researchEvidence from "../metadata/research-source-evidence-2026.json";
import dossier from "../metadata/poll-review-dossier-2026.json";
import approval from "../metadata/poll-review-approval-2026.json";

type StagedPoll = {
  id: string;
  kind: string;
  pollster: string;
  commissioner: string;
  fieldworkStart: string;
  fieldworkEnd: string;
  sampleSize: number;
  primaryVote: Record<string, number>;
  sourceUrl: string;
  sourceTier?: string;
  captureMode?: string;
};

const records = [
  ...manualEvidence.records,
  ...primaryEvidence.records,
  ...researchEvidence.records,
] as unknown as StagedPoll[];
const byId = new Map(records.map((record) => [record.id, record]));
const evidenceDecisionById = new Map(approval.evidenceDecisions.map((decision) => [decision.evidenceId, decision.decision]));
const modelDecisionById = new Map(approval.modelEligibilityDecisions.map((decision) => [decision.evidenceId, decision]));

const evidenceLabels: Record<string, string> = {
  approve: "Evidence accepted",
  defer: "Verification deferred",
  hold: "Evidence held",
};

const modelLabels: Record<string, string> = {
  eligible: "Admitted to canonical polling model",
  pending: "Model admission pending further checks",
};

const partyKeys = [
  ["coalition", "Coalition"],
  ["alp", "Labor"],
  ["oneNation", "One Nation"],
  ["greens", "Greens"],
  ["independents", "Independent"],
  ["otherParties", "Other"],
] as const;

function dateRange(start: string, end: string) {
  const fmt = new Intl.DateTimeFormat("en-AU", { day: "numeric", month: "short", timeZone: "UTC" });
  return `${fmt.format(new Date(start))}–${fmt.format(new Date(end))}`;
}

export function PollReviewDossier() {
  return <section className="surface poll-review-dossier" aria-labelledby="poll-review-heading">
    <div className="section-heading poll-review-heading">
      <div><p className="eyebrow">Governed polling review</p><h3 id="poll-review-heading">Seven staged polls now have an explicit evidence decision.</h3><p className="section-subcopy">Evidence acceptance remains separate from model eligibility. Only three human-reviewed Freshwater records were admitted to the canonical polling model.</p></div>
      <span className="poll-review-status approved"><ShieldCheck size={15} />Decision recorded · 30 Aug</span>
    </div>
    <div className="poll-review-summary" aria-label="Poll review decision summary">
      <article><strong>4</strong><span>evidence records accepted</span></article>
      <article><strong>1</strong><span>verification deferred</span></article>
      <article><strong>2</strong><span>evidence records held</span></article>
      <article><strong>3</strong><span>polls admitted to model</span></article>
    </div>
    <div className="poll-review-list">
      {dossier.reviews.map((review) => {
        const record = byId.get(review.evidenceId);
        const evidenceDecision = evidenceDecisionById.get(review.evidenceId) ?? "hold";
        const modelDecision = modelDecisionById.get(review.evidenceId);
        if (!record) return null;
        return <details className={`poll-review-item ${evidenceDecision}`} key={review.evidenceId}>
          <summary>
            <span className="poll-review-icon">{evidenceDecision === "approve" ? <ShieldCheck size={16} /> : <CircleAlert size={16} />}</span>
            <span className="poll-review-name"><strong>{record.pollster}</strong><small>{dateRange(record.fieldworkStart, record.fieldworkEnd)} · n={record.sampleSize.toLocaleString("en-AU")}</small></span>
            <span className="poll-review-recommendation"><b>{evidenceLabels[evidenceDecision]}</b><small>{modelDecision ? modelLabels[modelDecision.decision] : "Not admitted to the model"}</small></span>
          </summary>
          <div className="poll-review-detail">
            <p>{review.rationale}</p>
            <div className="poll-review-votes">{partyKeys.flatMap(([key, label]) => record.primaryVote[key] == null ? [] : [<span key={key}><b>{Number(record.primaryVote[key]).toFixed(1)}%</b>{label}</span>])}</div>
            <div className="poll-review-checks"><strong><FileCheck2 size={14} />Checks attached to any decision</strong><ul>{review.requiredChecks.map((check) => <li key={check}>{check}</li>)}</ul></div>
            <a href={record.sourceUrl} target="_blank" rel="noreferrer">Open cited evidence <ExternalLink size={12} /></a>
          </div>
        </details>;
      })}
    </div>
    <p className="poll-review-policy"><strong>Approval has been recorded, not inferred.</strong> Freshwater February and March were added; August was repaired in place. RedBridge evidence is accepted but remains outside the model pending sample-family checks. DemosAU is deferred; Resolve and YouGov/Common Threads remain held.</p>
  </section>;
}
