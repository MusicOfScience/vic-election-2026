import { useState } from "react";
import { partyMeta, type Party } from "./assembly-parties";
import { modelOutput } from "./election-eve-release/model-output.generated";
import { mainMatchup } from "./assembly-matchups";
import notes from "./electorate-watch-notes.json";
import "./forecast-explorers.css";

type District = (typeof modelOutput.districts)[number];
const briefs: Partial<Record<string, { title: string; points: string[]; source?: string }>> = notes;
const closeSeats = [...modelOutput.districts].filter((seat) => seat.favoured_probability < .55)
  .sort((a, b) => a.favoured_probability - b.favoured_probability);
const byId = new Map<string, District>(modelOutput.districts.map((seat) => [seat.district_id, seat]));
const knownSeats = (ids: string[]) => ids.flatMap((id) => { const seat = byId.get(id); return seat ? [seat] : []; });
const lists = {
  close: closeSeats,
  greens: knownSeats(["prahran", "northcote", "albert-park", "melbourne", "richmond", "brunswick"]),
  independent: knownSeats(["kew", "hawthorn", "benambra"]),
  pair: [...modelOutput.districts].sort((a, b) => mainMatchup(a.district_id).frequency - mainMatchup(b.district_id).frequency).slice(0, 12),
};
const labels: Record<keyof typeof lists, string> = {
  close: "Close winners", greens: "Greens paths", independent: "Independent paths", pair: "Unsettled final two",
};
const format = (fraction: number) => `${(100 * fraction).toFixed(1)}%`;

export function ElectorateWatch({ openDistrict }: { openDistrict: (district: District) => void }) {
  const [lens, setLens] = useState<keyof typeof lists>("close");
  return <section className="surface forecast-explorer" id="electorate-watch" aria-labelledby="electorate-watch-title">
    <h3 id="electorate-watch-title">Where the count could turn</h3>
    <p>Find close winners, crossbench paths and seats where the final two often change. These figures are shares of experimental model runs.</p>
    <div className="forecast-options" aria-label="Seats to watch">
      {(Object.keys(lists) as (keyof typeof lists)[]).map((key) => <button type="button" key={key} aria-pressed={key === lens} onClick={() => setLens(key)}>{labels[key]}</button>)}
    </div>
    <div className="watch-card-grid">
      {lists[lens].map((seat) => <button type="button" className="watch-card" key={seat.district_id} onClick={() => openDistrict(seat)}>
        <strong>{seat.district_name}</strong>
        <span>{briefs[seat.district_id]?.title ?? "See the count path and local evidence"}</span>
        {lens === "independent"
          ? <small>Read the named-candidate evidence</small>
          : <small>Wins most often · {partyMeta[seat.favoured_party as Party].label} {format(seat.favoured_probability)}<br />Most frequent pair · {mainMatchup(seat.district_id).label} {format(mainMatchup(seat.district_id).frequency)}</small>}
      </button>)}
    </div>
    {lens === "independent" && <p className="chart-note">The forecast pools independents and minor parties. These briefs follow named candidates using separate electorate evidence.</p>}
  </section>;
}

export function ElectorateWatchBrief({ district }: { district: District }) {
  const brief = briefs[district.district_id];
  const source = "https://www.vec.vic.gov.au/results/state-election-results/2022-state-election-results/results-by-district";
  return <section className="seat-detail-section" aria-labelledby="seat-watch-title">
    <h3 id="seat-watch-title">What to watch</h3>
    {brief && <p><strong>{brief.title}</strong></p>}
    <ul className="seat-watch-list">{(brief?.points ?? ["Compare first preferences by vote mode and track the second-to-third gap as candidates are excluded.", "Check the official indicative pair when counting starts. Changes to that pair can change how an early margin should be read."]).map((line) => <li key={line}>{line}</li>)}</ul>
    <p className="seat-explainer">Reading guide · 18 November 2026. Historical results and local observations provide context for the count.</p>
    <details><summary>Which preference cards could matter here?</summary>
      <p>Compare the final pairs above with the recommendations on each registered card. Start with candidates who may be excluded while second and third place are close. A transfer at that stage can change which two candidates finish the count.</p>
      <p>Check the district printed on the small-ballot instructions. Combined cards also cover a Council region. Voters choose their own preferences, and several registrations can recommend the same order.</p>
      <a href="https://www.vec.vic.gov.au/voting/2026-state-election/how-to-vote-cards">Find the registered cards for {district.district_name} in the VEC register</a>
    </details>
    <p><a href={source}>VEC district results</a>{brief?.source && <> · <a href={brief.source}>Additional local evidence</a></>}</p>
  </section>;
}
