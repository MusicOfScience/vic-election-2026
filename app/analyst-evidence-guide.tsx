"use client";

import { useRef, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { ExternalLink, Microscope, X } from "lucide-react";
import psephologySources from "../metadata/psephology-sources.json";
import psephologyEvidence from "../metadata/psephology-evidence-2026.json";
import { modelOutput } from "./model-output.generated";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;
const pct = (value: number) => `${value.toFixed(1)}%`;

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
  const evidenceCount = new Map<string, number>();
  for (const record of psephologyEvidence.records) evidenceCount.set(record.analystSourceId, (evidenceCount.get(record.analystSourceId) ?? 0) + 1);

  return <>
    {target && createPortal(
      <button type="button" className="analyst-evidence-trigger" onClick={open} aria-haspopup="dialog"><Microscope size={16} />Analysts</button>,
      target,
    )}
    <dialog ref={dialogRef} className="analyst-evidence-dialog" onClick={(event) => { if (event.target === dialogRef.current) close(); }}>
      <div className="analyst-evidence-panel">
        <header className="analyst-evidence-head">
          <div><p className="eyebrow">Psephology &amp; external evidence</p><h2>Model vs analysts</h2><p>Comparison, not averaging. Published analyst work is kept separate from polling observations so the same underlying evidence is not counted twice.</p></div>
          <button type="button" className="analyst-evidence-close" onClick={close} aria-label="Close analyst evidence"><X size={18} /></button>
        </header>

        <section className="analyst-model-snapshot" aria-label="Current model snapshot">
          <div><span>Labor primary</span><strong>{pct(mean.ALP)}</strong></div>
          <div><span>Coalition primary</span><strong>{pct(mean.LIB_NAT)}</strong></div>
          <div><span>One Nation primary</span><strong>{pct(mean.ONP)}</strong></div>
          <div><span>Greens primary</span><strong>{pct(mean.GRN)}</strong></div>
          <div><span>Hung parliament</span><strong>{pct(hung * 100)}</strong></div>
        </section>

        <section className="analyst-evidence-section">
          <div className="analyst-section-heading"><p className="eyebrow">Reviewed comparisons</p><h3>What external analysis is telling us</h3><span>{psephologyEvidence.records.length} evidence records · zero direct analyst model inputs</span></div>
          <div className="analyst-evidence-grid">
            {psephologyEvidence.records.map((record) => {
              const source = psephologySources.sources.find((item) => item.id === record.analystSourceId);
              return <article key={record.id}>
                <div className="analyst-card-meta"><span>{source?.displayName ?? record.analystSourceId}</span><time>{record.publishedDate}</time></div>
                <h4>{record.title}</h4>
                <p>{summaryById[record.id] ?? record.notes}</p>
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
