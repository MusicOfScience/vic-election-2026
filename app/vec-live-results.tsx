import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { ContestOverview, HistoricalComparison, LocationResults } from "./vec-count-analysis";

const id = z.string().regex(/^[a-zA-Z0-9_-]+$/);
const integer = z.number().int().nonnegative();
const date = z.string().datetime({ offset: true }).nullable();
const totals = z.object({ votes: integer, voteTypes: z.record(id, integer).nullable() });
const candidates = z.record(id, totals.extend({ elected: z.boolean().nullable() }));
const coverageSchema = z.object({ returned: integer, expected: integer }).nullable();
const tally = z.object({
  updatedAt: date, coverage: coverageSchema, candidates,
  status: z.enum(["reported", "unavailable"]),
  formal: totals, informal: totals, total: totals,
  groups: z.record(id, totals.extend({ aboveTheLine: integer, belowTheLine: integer })),
});
const pair = z.object({
  updatedAt: date, coverage: coverageSchema, candidates, status: z.enum(["reported", "unavailable", "withheld"]),
});
const change = z.object({ family: id, prior: z.number().min(0).max(100), current: z.number().min(0).max(100) });
const location = z.object({
  id, name: z.string(), classification: z.string().nullable(), formal: integer.nullable(), informal: integer.nullable(),
  firstVotes: z.record(id, integer), pairStatus: z.enum(["reported", "unavailable", "withheld", "incompatible"]).nullable(),
  pairVotes: z.record(id, integer),
});
const contest = z.object({
  id, name: z.string(),
  candidates: z.record(id, z.object({
    name: z.string(), independent: z.boolean().nullable(),
    affiliation: z.object({
      feedName: z.string().nullable(),
      register: z.object({ ballotName: z.string() }).nullable().optional(),
    }).nullable(),
  })),
  groups: z.record(id, z.object({ name: z.string(), ticket: z.string().nullable(), candidates: z.array(id) })),
  count: z.object({
    first: tally.nullable(), pair: pair.nullable(), declared: z.boolean(),
    aggregateOnly: z.boolean(), quota: integer.nullable(), quotaProvisional: z.boolean(),
  }).nullable(),
  history: z.array(z.object({
    publishedAt: z.string(), formal: integer.nullable(), declared: z.boolean().nullable(),
    pairStatus: z.enum(["reported", "unavailable", "withheld"]).nullable(),
    pairVotes: z.record(id, integer),
  })),
  comparison: z.object({ primary: z.array(change), pair: z.array(change) }).nullable().optional(),
  locations: z.array(location).optional(),
  operationalExceptions: z.array(z.object({
    pollingLocationId: id, referenceLabel: z.string(), status: z.enum(["closed", "receiving"]),
    venue: z.string().optional(),
  })),
  analyticalCoverage: z.object({ reportedEligibleDetailRows: integer, eligibleDetailRows: integer }).nullable(),
});
const house = z.object({
  publishedAt: date, ingestedAt: date,
  variant: z.enum(["lite", "litepp", "verbose"]).nullable(),
  warnings: z.array(z.string()),
  quarantined: z.array(z.object({ contestId: id, pollingLocationId: id, reason: z.string() })),
  statewide: z.object({
    reporting: integer, expected: integer, formal: integer.nullable(),
    primaries: z.array(z.object({ name: z.string(), votes: integer })),
  }),
  contests: z.array(contest),
});
export const vecResultsSchema = z.object({
  schemaVersion: z.literal(2), mode: z.enum(["production", "sample", "trial"]),
  source: z.literal("Victorian Electoral Commission results data feed"), eventName: z.string(), eventId: id.optional(),
  status: z.object({ state: z.string(), checkedAt: date, lastSuccessfulIngestionAt: date, failures: z.array(z.string()) }),
  houses: z.object({ L: house, U: house }),
});
export type VecResults = z.infer<typeof vecResultsSchema>;
export type CountContest = z.infer<typeof contest>;
type Contest = CountContest;
type Count = NonNullable<Contest["count"]>;
type VoteRow = { id: string; name: string; votes: number; aboveTheLine?: number; elected?: boolean | null };

const fmt = new Intl.NumberFormat("en-AU");
const melbourneTime = new Intl.DateTimeFormat("en-AU", {
  day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Australia/Melbourne",
  timeZoneName: "short",
});
const labels = {
  Ordinary: "Ordinary",
  EVCEarly: "Early voting centres",
  MobileVotingEarly: "Mobile voting",
  Postal: "Postal",
  Early: "Other early",
  MarkedAsVoted: "Marked as voted",
  Provisional: "Provisional",
  Absent: "Absent",
};
const pairLabel = { unavailable: "Awaiting a 2CP result", withheld: "Indicative 2CP withheld", reported: "Indicative 2CP reported" };
const variantLabel = { lite: "Lite", litepp: "LitePP", verbose: "Verbose" };
const formatDate = (value: string | null) => value ? melbourneTime.format(new Date(value)) : "Awaiting data";
const percentage = (votes: number, total: number | null) =>
  total && votes <= total ? `${(100 * votes / total).toFixed(1)}%` : "—";
const number = (value: number | null) => value === null ? "—" : fmt.format(value);

function Rows({ rows, total, atl = false }: { rows: VoteRow[]; total: number | null; atl?: boolean }) {
  return <div className="count-tally">
    <table><thead><tr><th scope="col">Ballot entry</th><th scope="col">Votes</th>
      {atl && <th scope="col">Above the line</th>}<th scope="col">Share</th></tr></thead>
      <tbody>{[...rows].sort((a, b) => b.votes - a.votes || a.name.localeCompare(b.name)).map(row =>
        <tr key={row.id}><th scope="row">{row.name}{row.elected && <small> · Elected</small>}</th>
          <td>{number(row.votes)}</td>{atl && <td>{number(row.aboveTheLine ?? null)}</td>}
          <td>{percentage(row.votes, total)}</td></tr>)}</tbody></table>
  </div>;
}

function candidateRows(contest: Contest, tally: z.infer<typeof candidates>, declared = false): VoteRow[] {
  return Object.entries(tally).map(([id, row]) => {
    const candidate = contest.candidates[id];
    const party = candidate?.affiliation?.register?.ballotName ?? candidate?.affiliation?.feedName;
    const label = party ?? (candidate?.independent ? "Independent" : null);
    return { id, votes: row.votes, name: [candidate?.name ?? id, label].filter(Boolean).join(" · "),
      elected: declared ? row.elected : null };
  });
}

function Reporting({ coverage, updatedAt }: { coverage: z.infer<typeof coverageSchema>; updatedAt: string | null }) {
  return <dl className="vec-count-facts">
    <div><dt>Last count update</dt><dd>{formatDate(updatedAt)}</dd></div>
    {coverage && <div><dt>VEC reporting locations</dt><dd>{number(coverage.returned)} of {number(coverage.expected)}</dd></div>}
  </dl>;
}

function FirstPreferences({ contest, count, upper }: { contest: Contest; count: Count; upper: boolean }) {
  const first = count.first;
  if (!first || first.status !== "reported") return <p>First preferences are awaiting a reported count.</p>;
  const rows = candidateRows(contest, first.candidates, count.declared);
  for (const [key, group] of Object.entries(first.groups)) {
    const reference = contest.groups[key];
    rows.push({ id: `group-${key}`, name: reference?.name || key, votes: group.votes,
      aboveTheLine: group.aboveTheLine });
  }
  return <>
    <Reporting updatedAt={first.updatedAt} coverage={first.coverage} />
    <dl className="vec-count-facts">
      <div><dt>Formal</dt><dd>{number(first.formal.votes)}</dd></div>
      <div><dt>Informal</dt><dd>{number(first.informal.votes)}</dd></div>
      <div><dt>Total ballots reported</dt><dd>{number(first.total.votes)}</dd></div>
      {count.quota !== null && <div><dt>{count.quotaProvisional ? "Provisional quota" : "Quota"}</dt><dd>{number(count.quota)}</dd></div>}
    </dl>
    <Rows rows={rows} total={first.formal.votes} atl={upper} />
    {upper && <p className="chart-note">Group totals combine above- and below-the-line first preferences. Individual tallies are shown for ungrouped candidates.</p>}
    {count.aggregateOnly && <p role="note">The VEC supplied contest totals only for this update. Location and vote-type detail are unavailable.</p>}
    {first.total.voteTypes && Object.keys(first.total.voteTypes).length > 0 &&
      <details><summary>Ballots by VEC vote type</summary><dl className="vec-count-facts">
        {Object.entries(first.total.voteTypes).map(([key, votes]) => <div key={key}>
          <dt>{labels[key as keyof typeof labels] ?? key}</dt><dd>{number(votes)}</dd></div>)}
      </dl></details>}
  </>;
}

function PairResult({ contest, count }: { contest: Contest; count: Count }) {
  const pair = count.pair;
  if (!pair) return null;
  const rows = candidateRows(contest, pair.candidates);
  return <section aria-label="Indicative two-candidate-preferred count">
    <h3>{pairLabel[pair.status]}</h3>
    {pair.status === "withheld" && <p>The VEC has withheld the indicative 2CP count. First preferences can continue to update.</p>}
    <Reporting updatedAt={pair.updatedAt} coverage={pair.status === "withheld" ? null : pair.coverage} />
    {pair.status === "reported" && <Rows rows={rows} total={rows.reduce((sum, row) => sum + row.votes, 0)} />}
  </section>;
}

function Progression({ contest, upper }: { contest: Contest; upper: boolean }) {
  if (contest.history.length < 2) return null;
  return <details><summary>Recent count progression</summary>
    <p className="chart-note">Each row is a complete VEC snapshot. Rechecks can reduce totals. Indicative pairings can change.</p>
    <div className="count-tally"><table>
      <thead><tr><th scope="col">Published</th><th scope="col">Formal votes</th>
        {!upper && <th scope="col">Indicative 2CP</th>}</tr></thead>
      <tbody>{[...contest.history].reverse().map(point => <tr key={point.publishedAt}>
        <th scope="row">{formatDate(point.publishedAt)}</th><td>{number(point.formal)}</td>
        {!upper && <td>{point.pairStatus === "reported"
          ? Object.entries(point.pairVotes).map(([id, votes]) => <div key={id}>{contest.candidates[id]?.name ?? id} {number(votes)}</div>)
          : point.pairStatus === "withheld" ? "Withheld" : "Awaiting data"}</td>}
      </tr>)}</tbody>
    </table></div>
  </details>;
}

export function VecLiveResults({ ledger, forecastDate, onRefresh }: {
  ledger: VecResults; forecastDate: string; onRefresh: (value: VecResults) => void;
}) {
  const [selection, setSelection] = useState<"L" | "U">("L");
  const [contestId, setContestId] = useState("");
  const [watchFile, setWatchFile] = useState<FileSystemFileHandle | null>(null);
  const [watchNote, setWatchNote] = useState("");
  const detail = useRef<HTMLHeadingElement>(null);
  const lastChecked = useRef(ledger.status.checkedAt ?? "");
  useEffect(() => {
    lastChecked.current = ledger.status.checkedAt ?? "";
  }, [ledger.status.checkedAt]);
  const eventId = ledger.eventId, eventName = ledger.eventName, mode = ledger.mode;
  useEffect(() => {
    if (!watchFile) return;
    let active = true, busy = false;
    const refresh = async () => {
      if (busy) return;
      busy = true;
      try {
        const file = await watchFile.getFile();
        if (file.size > 60_000_000) throw new Error("size");
        const candidate = vecResultsSchema.parse(JSON.parse(await file.text()));
        if (candidate.mode !== mode || candidate.eventName !== eventName || candidate.eventId !== eventId) throw new Error("event");
        const next = candidate.status.checkedAt ?? "";
        if (active && next > lastChecked.current) {
          lastChecked.current = next;
          onRefresh(candidate);
          setWatchNote("Following this file locally. The viewer checks every 15 seconds.");
        }
      } catch {
        if (active) setWatchNote("The selected file could not be refreshed. The previous snapshot is still displayed.");
      } finally {
        busy = false;
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15_000);
    return () => { active = false; window.clearInterval(timer); };
  }, [watchFile, eventId, eventName, mode, onRefresh]);

  async function followFile() {
    const local = window as Window & { showOpenFilePicker?: () => Promise<FileSystemFileHandle[]> };
    if (!local.showOpenFilePicker) {
      setWatchNote("This browser uses manual file selection. Choose the updated private count file again to refresh.");
      return;
    }
    try {
      const [handle] = await local.showOpenFilePicker();
      if (!handle) return;
      const file = await handle.getFile();
      if (file.size > 60_000_000) throw new Error("size");
      const candidate = vecResultsSchema.parse(JSON.parse(await file.text()));
      if (candidate.mode !== mode || candidate.eventName !== eventName || candidate.eventId !== eventId)
        throw new Error("event");
      if ((candidate.status.checkedAt ?? "") < (ledger.status.checkedAt ?? "")) throw new Error("older file");
      setWatchNote("Following this file locally. The viewer checks every 15 seconds.");
      setWatchFile(handle);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError"))
        setWatchNote("Choose the current private count file for this election to start following it.");
    }
  }
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const data = ledger.houses[selection];
  const current = data.contests.find(row => row.id === contestId) ?? data.contests[0];
  const upper = selection === "U";
  const age = data.publishedAt ? (now - Date.parse(data.publishedAt)) / 60_000 : null;
  const freshness = ledger.mode !== "production" ? "Rehearsal archive" : age === null ? "Awaiting snapshot"
    : age > 15 ? "Stale · over 15 minutes old" : "Snapshot under 15 minutes old";

  return <div className="vec-live-results">
    {ledger.mode !== "production"
      ? <p className="count-rehearsal" role="note"><strong>{ledger.mode === "sample" ? "VEC sample only." : "Election-night trial only."}</strong> This rehearsal contains test results.</p>
      : <p role="note"><strong>Private preview.</strong> Official results observed in the downloaded VEC feed.</p>}
    <p className="chart-note">{ledger.source}. Experimental pre-election forecast dated {forecastDate}.</p>
    {mode === "production" && <div>
      <div className="forecast-options">{watchFile
        ? <button type="button" onClick={() => { setWatchFile(null); setWatchNote(""); }}>Stop following this file</button>
        : <button type="button" onClick={() => void followFile()}>Follow a count file on this Mac</button>}</div>
      {watchNote && <p role="status">{watchNote}</p>}
    </div>}
    <div className="forecast-options" aria-label="House">
      <button type="button" aria-pressed={!upper} onClick={() => { setSelection("L"); setContestId(""); }}>Legislative Assembly</button>
      <button type="button" aria-pressed={upper} onClick={() => { setSelection("U"); setContestId(""); }}>Legislative Council</button>
    </div>
    <dl className="vec-count-facts" aria-live="polite">
      <div><dt>Feed freshness</dt><dd>{freshness}</dd></div>
      <div><dt>VEC publication</dt><dd>{formatDate(data.publishedAt)}{data.variant ? ` · ${variantLabel[data.variant]}` : ""}</dd></div>
      <div><dt>Snapshot ingested</dt><dd>{formatDate(data.ingestedAt)}</dd></div>
      <div><dt>Latest successful ingestion across both houses</dt><dd>{formatDate(ledger.status.lastSuccessfulIngestionAt)}</dd></div>
      <div><dt>Latest runner check</dt><dd>{formatDate(ledger.status.checkedAt)}</dd></div>
    </dl>
    {ledger.status.failures.length > 0 && <details><summary>Ingestion needs attention · {ledger.status.failures.length}</summary>
      <ul>{ledger.status.failures.map((failure, index) => <li key={index}>{failure}</li>)}</ul></details>}
    {(data.warnings.length > 0 || data.quarantined.length > 0) && <details><summary>Validation notes</summary>
      <ul>{data.warnings.map((warning, index) => <li key={index}>{warning}</li>)}
        {data.quarantined.map(row => <li key={`${row.contestId}-${row.pollingLocationId}`}>
          Location {row.pollingLocationId} excluded from detail · {row.reason}</li>)}</ul></details>}
    <section aria-label="Statewide reported first preferences">
      <h3>{upper ? "Council reporting statewide" : "Statewide Assembly first preferences"}</h3>
      <p>{data.statewide.reporting} of {data.statewide.expected} {upper ? "regions" : "districts"} with a reported primary count.
        {data.statewide.formal !== null && <> {number(data.statewide.formal)} formal ballots reported.</>}</p>
      {data.statewide.primaries.length > 0 && <details><summary>Show statewide party totals</summary>
        <Rows rows={data.statewide.primaries.map((row, index) => ({ ...row, id: String(index) }))} total={data.statewide.formal} /></details>}
    </section>
    {mode === "production" && data.contests.every(contest => contest.locations === undefined) &&
      <p className="chart-note">Open <code>private-analysis.json</code> for polling-location details and 2022 comparisons.</p>}
    <ContestOverview key={selection} contests={data.contests} upper={upper} onSelect={id => {
      setContestId(id);
      detail.current?.scrollIntoView({ block: "start" });
      detail.current?.focus({ preventScroll: true });
    }} />
    {current && <>
      <label className="vec-contest-picker">{upper ? "Council region" : "Assembly district"}
        <select value={current.id} onChange={event => setContestId(event.target.value)}>
          {data.contests.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}
        </select>
      </label>
      <h3 ref={detail} tabIndex={-1}>{current.name}</h3>
      {current.operationalExceptions.length > 0 && <ul className="vec-operations-note">
        {current.operationalExceptions.map(item => <li key={item.pollingLocationId}>
          <strong>{item.referenceLabel}</strong> {item.status === "closed" ? "closed due to flooding. Expected zero."
            : `receives redirected votes${item.venue ? ` at ${item.venue}` : ""}.`}</li>)}
        {current.analyticalCoverage && <li>Matched-booth eligible detail rows reporting first preferences
          {" "}{number(current.analyticalCoverage.reportedEligibleDetailRows)} of {number(current.analyticalCoverage.eligibleDetailRows)} in this snapshot.</li>}
      </ul>}
      {!current.count ? <p>No count is available for this contest in the selected house snapshot.</p> : <>
        <p><strong>{current.count.declared ? "Official declaration reported" : "Awaiting official declaration"}</strong></p>
        <div className="count-status-grid">
          <section aria-label="First preferences"><h3>First preferences</h3>
            <FirstPreferences contest={current} count={current.count} upper={upper} /></section>
          {!upper && <PairResult contest={current} count={current.count} />}
        </div>
      </>}
      <HistoricalComparison comparison={current.comparison} />
      <Progression contest={current} upper={upper} />
      <LocationResults key={current.id} contest={current} />
    </>}
  </div>;
}
