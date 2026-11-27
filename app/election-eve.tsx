import "./melbourne-map.css";

export const officialResults = "https://www.vec.vic.gov.au/results/state-election-results";

const latePolls = [
  { name: "DemosAU / PremierNational", period: "21–25 Nov", coalition: 34, labor: 19, oneNation: 16, greens: 16, url: "https://demosau.com/wp-content/uploads/DemosAU/vic-poll-end-nov-2026.html" },
  { name: "Newspoll / Pyxis", period: "Reported 27 Nov", coalition: 33, labor: 20, oneNation: 18, greens: 17, url: "https://www.pollbludger.net/2026/11/27/victorian-polls-newspoll-and-demosau/" },
  { name: "RedBridge / Accent", period: "13–20 Nov", coalition: 33, labor: 22, oneNation: 23, greens: 15, url: "https://www.accent-research.com/projects/afr-redbridge-group-and-accent-research-victorian-state-poll-13-20-november" },
  { name: "Roy Morgan", period: "18–19 Nov", coalition: 31, labor: 22.5, oneNation: 20, greens: 13, url: "https://www.roymorgan.com/findings/10393-victorian-state-voting-intention-november-2026" },
];

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
    <p>The {forecastDate} forecast uses polls with fieldwork through {includedThrough}. These later statewide first preferences are shown as published evidence.</p>
    <div className="late-poll-table" role="region" aria-label="Late statewide poll results" tabIndex={0}>
      <table className="matchup-table">
        <thead><tr><th scope="col">Poll</th><th scope="col">Coalition</th><th scope="col">Labor</th><th scope="col">One Nation</th><th scope="col">Greens</th></tr></thead>
        <tbody>{latePolls.map(({ name, period, coalition, labor, oneNation, greens, url }) => <tr key={name}>
          <th scope="row"><a href={url}>{name}</a><small>{period}</small></th>
          <td>{coalition}%</td><td>{labor}%</td><td>{oneNation}%</td><td>{greens}%</td>
        </tr>)}</tbody>
      </table>
    </div>
    <p><a href="https://electiontracker.au/elections/vic/2026/polls">Full external polling ledger, including Resolve and YouGov</a></p>
  </section>;
}
