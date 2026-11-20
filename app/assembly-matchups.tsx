import { parties, partyMeta, type Party } from "./assembly-parties";
import diagnostics from "./assembly-vote-diagnostics.generated.json";
import "./forecast-explorers.css";

type Matchup = { pair: Party[]; draws: number; firstShare: { mean: number; low: number; high: number }; firstWins: number };
const seats = diagnostics.seats as Partial<Record<string, { matchups: Matchup[]; thirdPlaceGap: { medianPp: number; withinTwoPoints: number; lastExcluded: Record<Party, number> } }>>;
export function mainMatchup(districtId: string) {
  const result = seats[districtId]?.matchups[0];
  if (!result) throw new Error(`Missing matchup for ${districtId}`);
  return { label: result.pair.map((party) => partyMeta[party].label).join(" vs "), frequency: result.draws / diagnostics.simulations };
}

const format = (value: number) => `${value.toFixed(1)}%`;
const shareOfRuns = (draws: number) => format(100 * draws / diagnostics.simulations);
const count = new Intl.NumberFormat("en-AU");

export function AssemblyMatchups({ districtId }: { districtId: string }) {
  const seat = seats[districtId];
  if (!seat) return null;
  const lastOut = [...parties].sort((a, b) => seat.thirdPlaceGap.lastExcluded[b] - seat.thirdPlaceGap.lastExcluded[a])[0];
  return <section className="seat-detail-section" aria-labelledby="seat-matchups-title">
    <h3 id="seat-matchups-title">Who can make the final two?</h3>
    <p>With three groups left, second and third are within two points in <strong>{shareOfRuns(seat.thirdPlaceGap.withinTwoPoints)}</strong> of runs. The median gap is <strong>{seat.thirdPlaceGap.medianPp.toFixed(1)} points</strong>. {partyMeta[lastOut].label} is most often last out, in <strong>{shareOfRuns(seat.thirdPlaceGap.lastExcluded[lastOut])}</strong> of runs.</p>
    <h4>Paths to winning this seat</h4>
    <p>Each bar shows how often a pair reaches the final count across all {count.format(diagnostics.simulations)} runs. The colours divide those runs by winner.</p>
    {seat.matchups.map(({ pair: [first, second], draws, firstWins }) => <div key={first + second} className="seat-path">
      <strong>{partyMeta[first].label} / {partyMeta[second].label} · {shareOfRuns(draws)}</strong>
      <div aria-hidden="true" className="seat-path-track">{[[first, firstWins], [second, draws - firstWins]].map(([party, wins]) => <span key={party} style={{width: shareOfRuns(Number(wins)), backgroundColor: `var(--${partyMeta[party as Party].css})`}} />)}</div>
      <small>Wins within this pair · {partyMeta[first].label} {count.format(firstWins)} · {partyMeta[second].label} {count.format(draws - firstWins)}</small>
    </div>)}
    <details open><summary>Final pairs and conditional margins</summary>
      <table className="matchup-table">
        <thead><tr><th scope="col">Pair</th><th scope="col">Share of runs</th><th scope="col">First group’s vote share</th></tr></thead>
        <tbody>{seat.matchups.map(({ pair, draws, firstShare }) => <tr key={pair.join("-")}>
          <th scope="row">{partyMeta[pair[0]].label} / {partyMeta[pair[1]].label}</th>
          <td>{shareOfRuns(draws)}<br />{count.format(draws)} runs</td>
          <td>{format(firstShare.mean)}{draws >= 50 && <><br />{format(firstShare.low)}–{format(firstShare.high)}</>}</td>
        </tr>)}</tbody>
      </table>
      <p className="seat-explainer">Each vote share is for runs with that pair. The middle 80% range is shown for pairs with at least 50 runs. The model counts party groups and pools independents with other minor parties.</p>
    </details>
  </section>;
}
