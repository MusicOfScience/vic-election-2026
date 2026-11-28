import { useState } from "react";
import type { CountContest } from "./vec-live-results";

const fmt = new Intl.NumberFormat("en-AU");
const familyNames: Record<string, string> = { ALP: "Labor", LIB_NAT: "Coalition", GRN: "Greens", ONP: "One Nation" };
const locationTypes: Record<string, string> = {
  VotingCentre: "Election-day voting centre",
  EarlyVotingCentre: "Early voting centre",
  MobileVotingCentre: "Mobile voting centre",
};
const pairStatuses: Record<string, string> = {
  reported: "Reported", unavailable: "Awaiting 2CP", withheld: "Withheld", incompatible: "Incompatible pairing",
};
const num = (value: number | null) => value === null ? "—" : fmt.format(value);
const pct = (value: number) => `${value.toFixed(1)}%`;
const voteName = (contest: CountContest, key: string) =>
  contest.candidates[key]?.name ?? contest.groups[key.replace(/^group-/, "")]?.name ?? key;

export function ContestOverview({ contests, upper, onSelect }: {
  contests: CountContest[]; upper: boolean; onSelect: (id: string) => void;
}) {
  const [sort, setSort] = useState("reported");
  const rows = contests.map(contest => {
    const first = contest.count?.first;
    const pair = contest.count?.pair;
    const entries = pair?.status === "reported" ? Object.entries(pair.candidates).sort((a, b) => b[1].votes - a[1].votes) : [];
    const pairTotal = entries.reduce((n, entry) => n + entry[1].votes, 0);
    const lead = pairTotal && entries.length === 2 ? 100 * (entries[0][1].votes - entries[1][1].votes) / pairTotal : null;
    return { contest, pairTotal, pair, entries, lead, formal: first?.status === "reported" ? first.formal.votes : null };
  });
  if (sort === "reported") rows.sort((a, b) => (b.formal ?? -1) - (a.formal ?? -1));
  if (sort === "close") rows.sort((a, b) => (a.lead ?? Infinity) - (b.lead ?? Infinity));

  return <details open className="vec-overview">
    <summary>{upper ? "All Council regions" : "All Assembly districts"} · results monitor</summary>
    <label className="vec-contest-picker">Sort results<select value={sort} onChange={event => setSort(event.target.value)}>
      <option value="reported">Most formal votes reported</option>
      {!upper && <option value="close">Closest reported indicative 2CP</option>}
      <option value="name">Name</option>
    </select></label>
    <div className="count-tally vec-overview-table" tabIndex={0} aria-label="Scrollable election results">
      <table><thead><tr><th scope="col">{upper ? "Region" : "District"}</th><th scope="col">Formal votes</th>
        {!upper && <th scope="col">Indicative 2CP</th>}</tr></thead>
        <tbody>{rows.map(({ contest, formal, pairTotal, pair, entries, lead }) => <tr key={contest.id}>
          <th scope="row"><button type="button" onClick={() => onSelect(contest.id)}>{contest.name}</button>
            {contest.count?.declared && <small> · Declared</small>}</th>
          <td>{num(formal)}</td>
          {!upper && <td>{lead !== null ? <>{voteName(contest, entries[0][0])} {pct(100 * entries[0][1].votes / pairTotal)}
            {" · "}{voteName(contest, entries[1][0])} {pct(100 * entries[1][1].votes / pairTotal)}</>
            : pair?.status === "withheld" ? "Withheld" : "Awaiting 2CP"}</td>}
        </tr>)}</tbody></table>
    </div>
  </details>;
}

export function HistoricalComparison({ comparison }: { comparison: CountContest["comparison"] }) {
  if (!comparison) return null;
  return <section aria-label="Change since the 2022 election">
    <h3>Change since 2022</h3>
    <p className="chart-note">Compares the votes reported so far with the final 2022 result for this district. Early reporting can skew the comparison.</p>
    <div className="count-tally"><table>
      <thead><tr><th scope="col">Party or grouping</th><th scope="col">2022 final</th><th scope="col">Reported so far</th><th scope="col">Change (pp)</th></tr></thead>
      {([["First preferences", comparison.primary], ["Indicative 2CP · same party pairing", comparison.pair]] as const)
        .filter(([, rows]) => rows.length).map(([label, rows]) => <tbody key={label}>
          <tr><th scope="rowgroup" colSpan={4}>{label}</th></tr>
          {rows.map(row => <tr key={row.family}><th scope="row">{familyNames[row.family] ?? row.family}</th>
            <td>{pct(row.prior)}</td><td>{pct(row.current)}</td>
            <td>{row.current - row.prior >= 0 ? "+" : "−"}{Math.abs(row.current - row.prior).toFixed(1)}</td></tr>)}
        </tbody>)}
    </table></div>
  </section>;
}

export function LocationResults({ contest }: { contest: CountContest }) {
  const [chosen, setChosen] = useState("");
  const locations = contest.locations ?? [];
  if (!locations.length) return null;
  const current = locations.find(item => item.id === chosen) ?? locations[0];
  const votes = (items: Record<string, number>) => Object.entries(items).sort((a, b) => b[1] - a[1]).map(([key, value]) =>
    <div key={key}><dt>{voteName(contest, key)}</dt><dd>{num(value)}</dd></div>);
  return <details>
    <summary>Polling-location results · {locations.length} locations with feed detail</summary>
    <label className="vec-contest-picker">Polling location<select value={current.id} onChange={event => setChosen(event.target.value)}>
      {locations.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></label>
    {current.classification && <p className="chart-note">{locationTypes[current.classification] ?? current.classification}</p>}
    <div className="count-status-grid">
      <section><h3>First preferences by ballot entry</h3>
        {current.formal === null ? <p>Awaiting local first preferences.</p> : <dl>
          {votes(current.firstVotes)}
          <div><dt>Formal</dt><dd>{num(current.formal)}</dd></div>
          <div><dt>Informal</dt><dd>{num(current.informal)}</dd></div>
        </dl>}
      </section>
      {current.pairStatus && <section><h3>Indicative 2CP</h3>
        {current.pairStatus === "reported" ? <dl>{votes(current.pairVotes)}</dl>
          : <p>{pairStatuses[current.pairStatus] ?? current.pairStatus}</p>}
      </section>}
    </div>
  </details>;
}
