"use client";

import { useRef, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { ExternalLink, Microscope, X } from "lucide-react";
import psephologySources from "../metadata/psephology-sources.json";
import psephologyEvidence from "../metadata/psephology-evidence-2026.json";
import reviewedAdditions from "../metadata/analyst-live-reviewed-additions.json";
import externalModels from "../metadata/analyst-external-models.json";
import analystLive from "./analyst-live.generated.json";
import stagedPollShadow from "../metadata/staged-poll-seat-shadow-2026.json";
import { modelOutput } from "./model-output.generated";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;
const pct = (value: number) => `${value.toFixed(1)}%`;
const pp = (value: number) => `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)} pp`;
const seats = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(1)}`;
const partyLabel: Record<string, string> = { ALP: "Labor", LIB_NAT: "Coalition", ONP: "One Nation", GRN: "Greens", OTH_IND: "Other / Independent" };

type ExternalSeatModel = {
  id: string;
  publisher: string;
  modelName: string;
  modelKind: string;
  publishedDate: string;
  fieldworkLabel: string;
  sampleSize: number | null;
  sourceUrl: string;
  sourceTier: string;
  verificationStatus: string;
  caution: string;
  projection: {
    coalition: number;
    labor: number;
    oneNation: number;
    greens: number;
    otherIndependent: number;
    totalSeats: number;
  };
};

type LiveRecord = {
  sourceId: string;
  sourceName: string;
  publishedDate: string | null;
  title: string;
  sourceUrl: string;
  status: string;
};

const summaryById: Record<string, string> = {
  "ben-raue-2026-07-27-vote-to-seat": "A specified 26 Coalition / 26 Labor / 27 One Nation / 13 Greens MRP scenario produced 31 Coalition, 30 Labor, 27 One Nation and 0 Greens seats under Raue's preference assumptions. This is a scenario comparison, not a second forecast observation.",
  "kevin-bonham-2026-07-17-victoria": "Bonham's July aggregate put Coalition 27.3%, Labor 26.0%, One Nation 23.7% and Greens 12.8%, with Coalition 52% two-party preferred. The aggregate is compared with our polling model rather than counted as another poll.",
  "casey-briggs-2026-05-13-nepean": "Briggs's Nepean by-election analysis is used as an interpretive cross-check on a local electoral test; official VEC results remain the numerical authority.",
  "kos-samaras-2026-08-07-victoria-context": "Samaras's published interpretation provides demographic and political context. Because it is connected to RedBridge polling, it is explicitly marked dependent rather than independent confirmation.",
  "antony-green-2026-07-25-victorian-pendulum": "Green highlights the limits of a traditional two-party pendulum in a three-party contest: 16 Coalition gains and a 7.6% uniform swing would be required for a majority if the Coalition lost no seats, while preferences and One Nation geography can disrupt that arithmetic.",
};

export function AnalystEvidenceGuide() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const isClient = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  const target = isClient ? document.querySelector(".dashboard-tabs-list") : null;
  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();
  const hung = modelOutput.chamber.find((row) => row.party === "ALP")?.hung_probability ?? 0;
  const mean = modelOutput.manifest.polling.mean;
  const modelMedian = (party: string) => modelOutput.chamber.find((row) => row.party === party)?.median ?? 0;

  const reviewedRecords = [...psephologyEvidence.records, ...reviewedAdditions.records]
    .sort((a, b) => b.publishedDate.localeCompare(a.publishedDate));
  const evidenceCount = new Map<string, number>();
  for (const record of reviewedRecords) evidenceCount.set(record.analystSourceId, (evidenceCount.get(record.analystSourceId) ?? 0) + 1);
  const seatModels = [...(externalModels.models as ExternalSeatModel[])]
    .sort((a, b) => b.publishedDate.localeCompare(a.publishedDate));
  const liveRecords = analystLive.records as LiveRecord[];

  return <>
    {target && createPortal(
      <button type="button" className="analyst-evidence-trigger" onClick={open} aria-haspopup="dialog"><Microscope size={16} />Analysts</button>,
      target,
    )}
    <dialog ref={dialogRef} className="analyst-evidence-dialog" onClick={(event) => { if (event.target === dialogRef.current) close(); }}>
      <div className="analyst-evidence-panel">
        <header className="analyst-evidence-head">
          <div><p className="eyebrow">Psephology &amp; external evidence</p><h2>Model vs analysts</h2><p>Comparison, not averaging. Published analyst work and external models are kept separate from polling observations so the same underlying evidence is not counted twice.</p></div>
          <button type="button" className="analyst-evidence-close" onClick={close} aria-label="Close analyst evidence"><X size={18} /></button>
        </header>

        <section className="analyst-model-snapshot" aria-label="Current model snapshot">
          <div><span>Labor primary</span><strong>{pct(mean.ALP)}</strong></div>
          <div><span>Coalition primary</span><strong>{pct(mean.LIB_NAT)}</strong></div>
          <div><span>One Nation primary</span><strong>{pct(mean.ONP)}</strong></div>
          <div><span>Greens primary</span><strong>{pct(mean.GRN)}</strong></div>
          <div><span>Hung parliament</span><strong>{pct(hung * 100)}</strong></div>
        </section>

        <section className="analyst-evidence-section shadow-evidence-section" aria-label="Staged polling shadow sensitivity">
          <div className="analyst-section-heading"><p className="eyebrow">Governed sensitivity test</p><h3>What if the two newest staged polls were admitted?</h3><span>Shadow only · {stagedPollShadow.simulationsPerScenario.toLocaleString()} paired simulations</span></div>
          <p className="shadow-intro">This deliberately reruns the full election with the quarantined August DemosAU and Resolve polls added in memory. It measures sensitivity; it does not accept either poll, change the published forecast or open the production gate.</p>
          <div className="shadow-summary-grid">
            <article><span>Hung parliament</span><strong>{pct(stagedPollShadow.assembly.canonicalHungProbability * 100)} → {pct(stagedPollShadow.assembly.shadowHungProbability * 100)}</strong><small>{pp(stagedPollShadow.assembly.deltaHungProbability)}</small></article>
            <article><span>Coalition mean seats</span><strong>{stagedPollShadow.assembly.parties.LIB_NAT.canonicalMeanSeats.toFixed(1)} → {stagedPollShadow.assembly.parties.LIB_NAT.shadowMeanSeats.toFixed(1)}</strong><small>{seats(stagedPollShadow.assembly.parties.LIB_NAT.deltaMeanSeats)} seats</small></article>
            <article><span>Labor mean seats</span><strong>{stagedPollShadow.assembly.parties.ALP.canonicalMeanSeats.toFixed(1)} → {stagedPollShadow.assembly.parties.ALP.shadowMeanSeats.toFixed(1)}</strong><small>{seats(stagedPollShadow.assembly.parties.ALP.deltaMeanSeats)} seats</small></article>
            <article><span>Meaningful seat movement</span><strong>{stagedPollShadow.assembly.districts.seatsWithFivePointOrLargerProbabilityShift} electorates</strong><small>win chance shifted by at least 5 points</small></article>
          </div>
          <div className="shadow-flips">
            <div className="analyst-section-heading compact"><p className="eyebrow">Most fragile calls</p><h4>{stagedPollShadow.assembly.districts.modalWinnerChanges.length} electorate favourites change</h4></div>
            {stagedPollShadow.assembly.districts.modalWinnerChanges.map((seat) => <article key={seat.districtId}>
              <div><strong>{seat.districtName}</strong><span>{partyLabel[seat.canonicalFavourite]} → {partyLabel[seat.shadowFavourite]}</span></div>
              <p>{partyLabel[seat.canonicalFavourite]} {pct(seat.canonicalFavouriteProbability * 100)} in the canonical run; {partyLabel[seat.shadowFavourite]} {pct(seat.shadowFavouriteProbability * 100)} in the shadow run.</p>
            </article>)}
          </div>
          <p className="analyst-policy-note"><strong>Why this is not the forecast:</strong> DemosAU is primary-source evidence awaiting explicit human acceptance; Resolve remains corroborated secondary evidence awaiting primary reconciliation or a reviewed exception. The report is fingerprinted to its exact model and evidence inputs so it fails closed if either changes.</p>
        </section>

        <section className="analyst-evidence-section" aria-label="External seat model comparisons">
          <div className="analyst-section-heading"><p className="eyebrow">External seat models &amp; scenarios</p><h3>Same chamber, different machinery</h3><span>{seatModels.length} dated comparisons · never averaged into the forecast</span></div>
          <div className="analyst-evidence-grid">
            {seatModels.map((record) => <article key={record.id}>
              <div className="analyst-card-meta"><span>{record.publisher} · {record.modelKind.replaceAll("-", " ")}</span><time>{record.publishedDate}</time></div>
              <h4>{record.projection.coalition} Coalition · {record.projection.labor} Labor · {record.projection.oneNation} One Nation · {record.projection.greens} Greens · {record.projection.otherIndependent} Other / independent</h4>
              <p><strong>{record.modelName}.</strong> {record.fieldworkLabel}{record.sampleSize ? ` · n=${record.sampleSize.toLocaleString()}` : ""}. {record.caution}</p>
              <div className="analyst-card-foot"><span>{record.sourceTier.replaceAll("-", " ")} · {record.verificationStatus.replaceAll("-", " ")}</span><a href={record.sourceUrl} target="_blank" rel="noreferrer">Source <ExternalLink size={11} /></a></div>
            </article>)}
            <article>
              <div className="analyst-card-meta"><span>Our current experimental model</span><span>Same 88-seat chamber</span></div>
              <h4>{modelMedian("LIB_NAT")} Coalition · {modelMedian("ALP")} Labor · {modelMedian("ONP")} One Nation · {modelMedian("GRN")} Greens · {modelMedian("OTH_IND")} Other / independent</h4>
              <p>These are current model median seats, not a re-fit to any external model. Showing every category explicitly makes both disagreement and omitted crossbench assumptions visible.</p>
              <div className="analyst-card-foot"><span>Internal probabilistic model · 5,000 simulations</span></div>
            </article>
          </div>
        </section>

        <section className="analyst-evidence-section" aria-label="Live analyst evidence monitor">
          <div className="analyst-section-heading"><p className="eyebrow">Live monitor</p><h3>New since the reviewed evidence snapshot</h3><span>{liveRecords.length} discovery leads · refreshed {analystLive.generatedAt.slice(0, 10)}</span></div>
          <p className="shadow-intro">This layer is deliberately less authoritative than the reviewed comparisons below. It discovers new analyst/source material and keeps it visible while review catches up; discovery never changes the forecast or promotes evidence automatically.</p>
          <div className="analyst-evidence-grid">
            {liveRecords.length ? liveRecords.map((record) => <article key={record.sourceUrl}>
              <div className="analyst-card-meta"><span>{record.sourceName}</span><time>{record.publishedDate ?? "date pending"}</time></div>
              <h4>{record.title}</h4>
              <p>Discovered by the live source monitor. Numerical claims and model implications remain pending governed review.</p>
              <div className="analyst-card-foot"><span>{record.status.replaceAll("-", " ")}</span><a href={record.sourceUrl} target="_blank" rel="noreferrer">Open <ExternalLink size={11} /></a></div>
            </article>) : <article><div className="analyst-card-meta"><span>Monitor current</span></div><h4>No unreviewed analyst leads in the current snapshot</h4><p>The reviewed evidence below remains the latest governed comparison layer.</p></article>}
          </div>
          <p className="analyst-policy-note">Refresh status: {analystLive.refreshStatus.mode.replaceAll("-", " ")} · {analystLive.refreshStatus.sourcesSucceeded}/{analystLive.refreshStatus.sourcesAttempted} monitored source pages refreshed successfully.</p>
        </section>

        <section className="analyst-evidence-section">
          <div className="analyst-section-heading"><p className="eyebrow">Reviewed comparisons</p><h3>What external analysis is telling us</h3><span>{reviewedRecords.length} evidence records · reviewed through {reviewedAdditions.reviewedAt} · zero direct analyst model inputs</span></div>
          <div className="analyst-evidence-grid">
            {reviewedRecords.map((record) => {
              const source = psephologySources.sources.find((item) => item.id === record.analystSourceId);
              const summary = "summary" in record ? record.summary : summaryById[record.id] ?? record.notes;
              return <article key={record.id}>
                <div className="analyst-card-meta"><span>{source?.displayName ?? record.analystSourceId}</span><time>{record.publishedDate}</time></div>
                <h4>{record.title}</h4>
                <p>{summary}</p>
                <div className="analyst-card-foot"><span>{record.modelUsage.replaceAll("_", " ")} · {record.independenceAssessment.replaceAll("_", " ")}</span><a href={record.sourceUrl} target="_blank" rel="noreferrer">Source <ExternalLink size={11} /></a></div>
              </article>;
            })}
          </div>
        </section>

        <section className="analyst-source-section">
          <div className="analyst-section-heading"><p className="eyebrow">Source families</p><h3>Who is being tracked</h3><span>One analyst/platform family = one source, not multiple votes</span></div>
          <div className="analyst-source-grid">
            {psephologySources.sources.map((source) => <div key={source.id}><strong>{source.displayName}</strong><span>{evidenceCount.get(source.id) ? `${evidenceCount.get(source.id)} reviewed evidence record${evidenceCount.get(source.id) === 1 ? "" : "s"}` : "Registered · suitable Victorian evidence still to be captured"}</span></div>)}
          </div>
          <p className="analyst-policy-note">Analyst outputs can challenge preference assumptions, local priors and uncertainty. They do not become forecast weights until a separately specified transformation is backtested and approved. Poll-derived analyst work always retains its dependency on the underlying polls.</p>
        </section>
      </div>
    </dialog>
  </>;
}
