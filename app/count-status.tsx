import { useState } from "react";
import { z } from "zod";
import "./count-status.css";

const statuses = {
  unavailable: "Indicative pair awaiting results",
  published: "Indicative pair published",
  withheld: "Indicative pair withheld",
};
const transitions = {
  "pair-published": "Indicative pair first published",
  "pair-withheld": "Indicative pair withheld",
  "pair-changed": "Indicative pair changed",
  "pair-restored": "Indicative pair restored",
};
const vecFeed = "https://www.vec.vic.gov.au/about-us/media/2026-results-data-feed";
const date = new Intl.DateTimeFormat("en-AU", { dateStyle: "medium", timeStyle: "short", timeZone: "Australia/Melbourne" });
const number = new Intl.NumberFormat("en-AU");
const formatDate = (value: string) => date.format(new Date(value));
const integer = z.number().int().nonnegative();
const timestamp = z.string().datetime({ offset: true });
const votes = z.record(z.string(), integer);
const tally = z.object({
  votes, updatedAt: timestamp.nullable(),
  coverage: z.object({ returned: integer, expected: integer }).nullable(),
});
const observation = z.object({
  createdAt: timestamp, declared: z.boolean(), series: integer.nullable(),
  transition: z.enum(["pair-published", "pair-withheld", "pair-changed", "pair-restored"]).nullable(),
  first: tally.extend({ formal: integer, voteModes: votes }),
  pair: tally.extend({ status: z.enum(["unavailable", "published", "withheld"]) }),
});
const ledgerSchema = z.object({
  schemaVersion: z.literal(1), mode: z.enum(["sample", "trial", "live"]),
  frames: z.array(z.object({ createdAt: timestamp })).min(1),
  districts: z.record(z.string(), z.object({
    name: z.string(), candidates: z.record(z.string(), z.string()),
    history: z.array(observation).min(1),
  })).refine((districts) => Object.keys(districts).length > 0),
});
type Ledger = z.infer<typeof ledgerSchema>;
type Tally = z.infer<typeof tally>;
type Observation = z.infer<typeof observation>;

const rehearsalSteps: { at: string; status: keyof typeof statuses; votes: Record<string, number>; series: number | null; transition: Observation["transition"]; declared?: boolean }[] = [
  { at: "07:03", status: "unavailable", votes: {}, series: null, transition: null },
  { at: "07:20", status: "published", votes: { a: 420, b: 380 }, series: 1, transition: "pair-published" },
  { at: "07:40", status: "withheld", votes: {}, series: null, transition: "pair-withheld" },
  { at: "08:03", status: "published", votes: { a: 630, c: 670 }, series: 2, transition: "pair-changed" },
  { at: "08:20", status: "published", votes: { a: 930, c: 970 }, series: 2, transition: null, declared: true },
];
const rehearsalHistory: Observation[] = rehearsalSteps.map(({ at, status, votes, series, transition, declared }, index) => {
  const createdAt = `2026-11-28T${at}:00Z`;
  const firstVotes = { a: 315 + 145 * index, b: 285 + 110 * index, c: 296 + 150 * index };
  return {
    createdAt, series, transition, declared: declared ?? false,
    first: { votes: firstVotes, formal: Object.values(firstVotes).reduce((a, b) => a + b, 0),
      coverage: { returned: index + 2, expected: 10 }, updatedAt: createdAt, voteModes: {} },
    pair: { status, votes, coverage: status === "unavailable" ? null : { returned: index + 1, expected: 10 }, updatedAt: status === "unavailable" ? null : createdAt },
  };
});

const demo: Ledger = { schemaVersion: 1, mode: "sample", frames: rehearsalHistory, districts: {
  rehearsal: { name: "Example district", candidates: { a: "Candidate A", b: "Candidate B", c: "Candidate C" }, history: rehearsalHistory },
} };

function CountTable({ tally, candidates, onlyPublished = true }: { tally: Tally; candidates: Record<string, string>; onlyPublished?: boolean }) {
  const rows = Object.entries(tally.votes).sort((a, b) => b[1] - a[1]);
  const total = rows.reduce((sum, [, votes]) => sum + votes, 0);
  return <div className="count-tally">
    {tally.coverage && <p>{tally.coverage.returned} of {tally.coverage.expected} reporting locations</p>}
    {tally.updatedAt && <p>Updated {formatDate(tally.updatedAt)} Melbourne time</p>}
    {onlyPublished && rows.length > 0 && <table><thead><tr><th scope="col">Candidate</th><th scope="col">Votes</th><th scope="col">Share</th></tr></thead><tbody>
      {rows.map(([id, votes]) => <tr key={id}><th scope="row">{candidates[id]}</th><td>{number.format(votes)}</td><td>{total ? `${(100 * votes / total).toFixed(1)}%` : "—"}</td></tr>)}
    </tbody></table>}
  </div>;
}

export default function CountStatus() {
  const [showDemo, setShowDemo] = useState(false);
  const [privateLedger, setPrivateLedger] = useState<Ledger | null>(null);
  const [fileError, setFileError] = useState("");
  const [loading, setLoading] = useState(false);
  const [districtId, setDistrictId] = useState("");
  const [frame, setFrame] = useState<number | null>(null);
  const ledger = showDemo ? demo : privateLedger;
  const districts = Object.entries(ledger?.districts ?? {}).sort((a, b) => a[1].name.localeCompare(b[1].name, "en-AU"));
  const district = ledger?.districts[districtId] ?? districts[0]?.[1];
  const index = frame ?? (ledger ? ledger.frames.length - 1 : 0);
  const moment = ledger?.frames[index]?.createdAt;
  const history = moment ? district?.history.filter((entry) => entry.createdAt <= moment) ?? [] : [];
  const current = history.at(-1);
  return <div className="tab-stack">
    <section className="surface forecast-explorer count-status" aria-labelledby="count-status-title">
      <p className="eyebrow">Victorian Legislative Assembly</p>
      <h2 id="count-status-title">Election count status</h2>
      <p>Follow first preferences, indicative pair changes and declarations reported by the Victorian Electoral Commission (VEC).</p>
      <div className="forecast-options"><button type="button" aria-pressed={showDemo} onClick={() => {
        setShowDemo(!showDemo); setDistrictId(""); setFrame(showDemo ? null : 0);
      }}>{showDemo ? "Exit rehearsal" : "Try the rehearsal"}</button><a href={vecFeed}>VEC feed and documentation</a><a href="https://www.vec.vic.gov.au/results/state-election-results">Official state election results</a></div>
      {showDemo && <p className="count-rehearsal" role="note"><strong>Rehearsal only.</strong> The district and candidate labels are fictional. All vote totals in this view are illustrative.</p>}
      {!ledger && <p><strong>Public results are published by the VEC.</strong> You can also try the rehearsal or review an authorised count file privately in this browser.</p>}
      <details><summary>Review a count file privately</summary>
        <p>Choose a JSON ledger made by the project’s count converter. The file stays in this browser tab.</p>
        <label>Count ledger file <input type="file" accept=".json,application/json" disabled={loading} onChange={async (event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (!file) return;
          setFileError("");
          setLoading(true);
          try {
            if (file.size > 60_000_000) throw new Error("The count file exceeds the 60 MB local preview limit.");
            const parsed = ledgerSchema.safeParse(JSON.parse(await file.text()));
            if (!parsed.success) throw new Error("This file does not match the count ledger format.");
            setPrivateLedger(parsed.data); setDistrictId(""); setFrame(null); setShowDemo(false);
          } catch (error) {
            setFileError(error instanceof SyntaxError ? "The selected file is not valid JSON." :
              error instanceof Error ? error.message : "The count file could not be read.");
          } finally {
            setLoading(false);
          }
        }} /></label>
        {fileError && <p role="alert">{fileError}</p>}
        {privateLedger && <div className="forecast-options"><button type="button" disabled={loading} onClick={() => {
          setPrivateLedger(null); setDistrictId(""); setFrame(null);
        }}>Clear private count file</button></div>}
      </details>
      {!showDemo && privateLedger && <p role="note"><strong>Private preview.</strong> Source file mode: {privateLedger.mode}. These figures are visible only in this browser tab.</p>}
      {ledger && district && current && moment && <>
        <div className="forecast-options">
          <label>Electorate<select value={districtId && ledger.districts[districtId] ? districtId : districts[0][0]} onChange={(event) => setDistrictId(event.target.value)}>
            {districts.map(([id, row]) => <option key={id} value={id}>{row.name}</option>)}
          </select></label>
          <button type="button" onClick={() => setFrame(null)}>Latest snapshot</button>
        </div>
        <label className="replay-timeline">Count timeline
          <input type="range" min={0} max={ledger.frames.length - 1} value={index} aria-valuetext={formatDate(moment)} onChange={(event) => setFrame(Number(event.target.value))} />
        </label>
        <p aria-live="polite"><strong>{district.name}</strong> · {formatDate(moment)} Melbourne time</p>
        <div className="count-status-grid">
          <section aria-label="First preferences"><h3>First preferences</h3>
            <p>{number.format(current.first.formal)} formal votes recorded in this view.</p>
            <CountTable tally={current.first} candidates={district.candidates} />
            {Object.keys(current.first.voteModes).length > 0 && <details><summary>Formal votes by VEC vote type</summary>
              <dl>{Object.entries(current.first.voteModes).map(([mode, votes]) => <div key={mode}><dt>{mode}</dt><dd>{number.format(votes)}</dd></div>)}</dl>
              <p className="chart-note">Categories follow the feed. Reporting coverage may differ by vote type.</p>
            </details>}
          </section>
          <section aria-label="Indicative two-candidate preferred count"><h3>{statuses[current.pair.status]}</h3>
            {current.pair.status === "withheld" && <p>The feed has withheld the indicative two-candidate-preferred count. First preferences can continue to update. The feed flag gives no reason for withholding.</p>}
            {current.pair.status === "published" && <p>Pair series {current.series}. When the pair changes, its earlier margins belong to a separate series.</p>}
            <CountTable tally={current.pair} candidates={district.candidates} onlyPublished={current.pair.status === "published"} />
          </section>
        </div>
        <p><strong>{current.declared ? "Declaration reported by the feed" : "Declaration pending"}</strong>. Counting can continue after a declaration. The feed provides neither the formal preference distribution nor the declaration date.</p>
        <details><summary>Count milestones for {district.name}</summary>
          <ul>{history.flatMap((row, i) => {
            const entries: string[] = [];
            if (row.transition) entries.push(transitions[row.transition]);
            if (row.declared !== (history[i - 1]?.declared ?? false)) entries.push(row.declared ? "Declaration flag recorded" : "Declaration flag removed");
            return entries.map((entry) => <li key={`${row.createdAt}-${entry}`}>{formatDate(row.createdAt)} · {entry}</li>);
          })}</ul>
          <p className="chart-note">Milestone dates are the first captured snapshots showing each change.</p>
        </details>
      </>}
    </section>
  </div>;
}
