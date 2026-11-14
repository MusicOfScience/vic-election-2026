import type { CSSProperties } from "react";
import type { modelOutput } from "./model-output.generated";
import { parties, partyMeta, type Party } from "./assembly-parties";
import "./assembly-overview.css";

type Districts = typeof modelOutput.districts;
type Chamber = Record<Party, (typeof modelOutput.chamber)[number]>;
const majority = 45;
const chamberSize = 88;
const seatPosition = (seats: number) => `${seats / chamberSize * 100}%`;
const frequency = (value: number) => `${(value * 100).toFixed(1)}%`;

export function AssemblyOutlook({ chamber }: { chamber: Chamber }) {
  const ordered = [...parties].sort((a, b) => chamber[b].mean - chamber[a].mean);
  return <section className="assembly-outlook" aria-labelledby="assembly-outlook-title">
    <div className="assembly-outlook-heading">
      <h3 id="assembly-outlook-title">Paths to 45 seats</h3>
      <span>Middle 80% of simulated totals</span>
    </div>
    <div className="assembly-axis" aria-hidden="true">
      <div><span>0</span><span>45 · majority</span><span>88</span></div>
    </div>
    <ul>
      {ordered.map((party) => {
        const { median, lower80, upper80 } = chamber[party];
        return <li key={party} style={{ "--seat-party": `var(--${partyMeta[party].css})` } as CSSProperties}>
          <span>{partyMeta[party].label}</span>
          <span className="assembly-range" aria-hidden="true">
            <i style={{ left: seatPosition(lower80), width: seatPosition(upper80 - lower80) }} />
            <b style={{ left: seatPosition(median) }} />
          </span>
          <span className="assembly-range-value"><b>{median}</b><small>{lower80}–{upper80}</small></span>
        </li>;
      })}
    </ul>
    <p>The dot marks the median. The line shows where most runs land for each group.</p>
  </section>;
}

export function AssemblySeatBoard({ districts, chamber }: { districts: Districts; chamber: Chamber }) {
  const groups = parties.map((party) => ({
    party,
    seats: districts.filter((seat) => seat.favoured_party === party)
      .sort((a, b) => a.favoured_probability - b.favoured_probability || a.district_name.localeCompare(b.district_name, "en-AU")),
  })).sort((a, b) => b.seats.length - a.seats.length);
  const closest = districts.filter((seat) => seat.favoured_probability < .55).length;
  return <section className="surface assembly-board" aria-labelledby="assembly-board-title">
    <header className="assembly-board-header">
      <div>
        <p className="eyebrow">Legislative Assembly</p>
        <h3 id="assembly-board-title">Every seat, at a glance</h3>
        <p>Each tile shows the group that won most often in that electorate and its share of model runs. The tightest races appear first within each group.</p>
      </div>
      <div className="assembly-board-tallies">
        <span><b>{districts.length}</b> electorates</span>
        <span><b>{closest}</b> below 55%</span>
        <span><b>{majority}</b> for a majority</span>
      </div>
    </header>
    <div className="assembly-board-groups" aria-label="Party colour key and electorate groups">
      {groups.map(({ party, seats }) => <section className="assembly-group" key={party}
        aria-labelledby={`assembly-group-${party}`} style={{ "--seat-party": `var(--${partyMeta[party].css})` } as CSSProperties}>
        <header>
          <h4 id={`assembly-group-${party}`}>{partyMeta[party].label}</h4>
          <span><b>{seats.length}</b> seats led <span aria-hidden="true">·</span> <b>{chamber[party].mean.toFixed(1)}</b> average seats across runs</span>
        </header>
        {seats.length > 0 && <ul role="list">
          {seats.map((seat) => <li key={seat.district_id} data-seat={seat.district_id}>
            <span className="assembly-seat-name">{seat.district_name}</span>
            <strong>{frequency(seat.favoured_probability)}</strong>
            <span className="assembly-seat-track" aria-hidden="true"><i style={{ width: frequency(seat.favoured_probability) }} /></span>
          </li>)}
        </ul>}
      </section>)}
    </div>
    <p className="assembly-board-note">Seat leaders come from each electorate counted separately. Chamber totals and majority frequencies come from counting all 88 seats together in each simulation. Others / independents is a pooled group in the model.</p>
  </section>;
}
