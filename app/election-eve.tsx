import review from "../metadata/election-eve-poll-review-2026-11-27.json";
import sensitivity from "../metadata/election-eve-poll-sensitivity-2026-11-27.json";
import "./melbourne-map.css";

export const officialResults = "https://www.vec.vic.gov.au/results/state-election-results";

const latePolls = [...review.polls].sort((a, b) => b.publicationDate.localeCompare(a.publicationDate));
const scenarios = [
  ["reaged", "Existing polls, dated to 27 November"],
  ["three", "Add DemosAU, RedBridge and Morgan"],
  ["replace", "Replace the three earlier waves"],
  ["plusNewspoll", "Add the three plus Newspoll"],
  ["plusResolve", "Add the three plus Resolve"],
  ["allFive", "Add all five"],
] as const;
const fieldwork = (start: string, end: string) => `${Number(start.slice(-2))}–${Number(end.slice(-2))} Nov`;
const frequency = (value: number) => `${(value * 100).toFixed(1)}%`;

export function ElectionNight({ openMap, openCount }: { openMap: () => void; openCount: () => void }) {
  return <section className="surface election-night" aria-labelledby="election-night-title">
    <h2 id="election-night-title">Election night · Saturday 28 November</h2>
    <p>The Victorian Electoral Commission publishes progressive results from 6 pm Melbourne time. Early tallies are provisional and reporting coverage varies by electorate.</p>
    <div className="election-night-links">
      <a href={officialResults}>Official VEC results</a>
      <button type="button" onClick={openCount}>Count status</button>
      <button type="button" onClick={openMap}>Greater Melbourne map</button>
    </div>
  </section>;
}

export function LatePolling({ includedThrough, forecastDate }: { includedThrough: string; forecastDate: string }) {
  return <section className="surface election-night" aria-labelledby="late-polls-title">
    <h2 id="late-polls-title">Late campaign polling</h2>
    <p>The {forecastDate} forecast uses polls with fieldwork through {includedThrough}. The table and sensitivity test below use later published statewide first preferences.</p>
    <div className="late-poll-table" role="region" aria-label="Late statewide poll results" tabIndex={0}>
      <table className="matchup-table">
        <thead><tr><th scope="col">Poll</th><th scope="col">Coalition</th><th scope="col">Labor</th><th scope="col">One Nation</th><th scope="col">Greens</th></tr></thead>
        <tbody>{latePolls.map((poll) => <tr key={poll.id}>
          <th scope="row"><a href={poll.sourceUrl}>{poll.pollster}</a><small>{fieldwork(poll.fieldworkStart, poll.fieldworkEnd)} · n={poll.sampleSize.toLocaleString("en-AU")}</small></th>
          <td>{poll.primaryVote.coalition}%</td><td>{poll.primaryVote.alp}%</td>
          <td>{poll.primaryVote.oneNation}%</td><td>{poll.primaryVote.greens}%</td>
        </tr>)}</tbody>
      </table>
    </div>
    <h3>27 November sensitivity · What changes with the late polls?</h3>
    <p>Each row uses the same Assembly model and {sensitivity.simulations.toLocaleString("en-AU")} simulations. All rows use the 27 November model date, so the comparison isolates the polling choices.</p>
    <div className="late-poll-table" role="region" aria-label="Election-eve Assembly sensitivity" tabIndex={0}>
      <table className="matchup-table">
        <thead><tr><th scope="col">Polling scenario</th><th scope="col">One Nation primary</th><th scope="col">Coalition mean seats</th><th scope="col">Coalition majority</th><th scope="col">Hung Assembly</th></tr></thead>
        <tbody>{scenarios.map(([id, label]) => {
          const row = sensitivity.scenarios[id];
          return <tr key={id}>
            <th scope="row">{label}<small>{row.pollCount} polls</small></th>
            <td>{row.pollingMean.ONP.toFixed(1)}%</td><td>{row.meanSeats.LIB_NAT.toFixed(1)}</td>
            <td>{frequency(row.coalitionMajority)}</td><td>{frequency(row.hungAssembly)}</td>
          </tr>;
        })}</tbody>
      </table>
    </div>
    <p>The majority and hung Assembly columns show the share of runs. Seat totals remain sensitive to how the model distributes statewide support across electorates and allocates preferences.</p>
    <details><summary>Sources and admission notes</summary>
      <ul>{latePolls.map((poll) => <li key={poll.id}><strong>{poll.pollster}.</strong> {poll.reviewNote} {poll.effectiveSampleSize && <>Effective sample {poll.effectiveSampleSize.toLocaleString("en-AU")}. </>}{"methodologyUrl" in poll && <a href={poll.methodologyUrl}>Methodology statement</a>}</li>)}</ul>
      <p><a href="https://www.heraldsun.com.au/news/victoria/state-election/updated-live-hourly-seatbyseat-projections-for-all-88-seats/news-story/2c39bf0624842cf3906f66a7b6de7f55">YouGov’s seat projections</a> come from a separate model and are useful for comparison. This sensitivity uses statewide survey primaries.</p>
      <p><a href="https://github.com/MusicOfScience/vic-election-2026/blob/main/model/scripts/run_election_eve_poll_sensitivity.py">Reproduce this sensitivity</a></p>
    </details>
  </section>;
}
