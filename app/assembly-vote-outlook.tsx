import { parties, partyMeta, type Party } from "./assembly-parties";
import { modelOutput } from "./model-output.generated";
import { pollSeries } from "./poll-data.generated";
import diagnostics from "./assembly-vote-diagnostics.generated.json";
import "./assembly-vote-outlook.css";

type District = (typeof modelOutput.districts)[number];
type NamedParty = (party: Party) => string | null;
const byDistrict = new Map<string, District>(modelOutput.districts.map((seat) => [seat.district_name, seat]));
const date = (value: string) => new Intl.DateTimeFormat("en-AU", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value));
const pct = (value: number) => `${value.toFixed(1)}%`;
const inputs = new Set(diagnostics.pollIds);
const includedPolls = pollSeries.filter((poll) => inputs.has(poll.id))
  .sort((a, b) => b.fieldworkEnd.localeCompare(a.fieldworkEnd));
const latest = includedPolls[0];
const matchups = diagnostics.seats as Partial<Record<string, {
  pair: Party[]; draws: number; firstShare: { mean: number; low: number; high: number }; firstWins: number;
}>>;

function PrimaryRanking({ values, candidate }: { values: Record<Party, number>; candidate?: NamedParty }) {
  const top = [...parties].sort((a, b) => values[b] - values[a]).slice(0, 3);
  return <ol className="vote-primary-ranking">{top.map((party) => <li key={party} style={{ borderColor: `var(--${partyMeta[party].css})` }}>
    <div><strong>{partyMeta[party].label}</strong>{candidate?.(party) && <small>{candidate(party)}</small>}</div>
    <b>{pct(values[party])}</b>
  </li>)}</ol>;
}

export function VoteOutlookPollInputs() {
  return <details className="surface vote-outlook vote-poll-inputs">
    <summary>{includedPolls.length} polls used in the {date(diagnostics.asOf)} forecast</summary>
    <p>The model combines these admitted statewide first-preference polls, then simulates local voting and preference transfers. Recent evidence awaiting admission appears in the November polling review.</p>
    <ul>{includedPolls.map((poll) => <li key={poll.id}>
      {poll.sourceUrl ? <a href={poll.sourceUrl} target="_blank" rel="noreferrer">{poll.pollster}</a> : poll.pollster}
      <span> · Fieldwork ended {date(poll.fieldworkEnd)} · sample {poll.n.toLocaleString("en-AU")}</span>
    </li>)}</ul>
  </details>;
}

export function StatewideVoteOutlook({ openPolls }: { openPolls: () => void }) {
  const { mean, low, high } = diagnostics.statewideLabor2pp;
  return <section className="surface vote-outlook" aria-labelledby="statewide-vote-title">
    <header><p className="eyebrow">Statewide vote · {date(diagnostics.asOf)} snapshot</p><h3 id="statewide-vote-title">First preferences and two-party preferred</h3></header>
    <div className="vote-outlook-grid">
      <div><h4>Top three on first preferences</h4><PrimaryRanking values={modelOutput.manifest.polling.mean} /></div>
      <div><h4>Labor–Coalition two-party preferred (2PP)</h4>
        <div className="vote-pair-labels"><span>Labor <b>{pct(mean)}</b></span><span>Coalition <b>{pct(100 - mean)}</b></span></div>
        <div className="vote-pair-bar" aria-hidden="true"><i style={{ width: pct(mean) }} /></div>
        <p>Labor’s middle 80% of model runs spans {pct(low)}–{pct(high)}.</p>
        <p>Each simulated count keeps Labor and the Coalition as the last two groups. The statewide estimate weights electorates by enrolment.</p>
      </div>
    </div>
    <div className="vote-outlook-source">
      <span>{inputs.size} admitted statewide polls{latest && ` · Latest fieldwork ended ${date(latest.fieldworkEnd)}`}. The 2PP estimate comes from simulated transfers.</span>
      <button type="button" onClick={openPolls}>See polling inputs →</button>
    </div>
  </section>;
}

export function ElectorateVoteOutlook({ districtName, candidate, openPolls }: { districtName: string; candidate: NamedParty; openPolls: () => void }) {
  const district = byDistrict.get(districtName);
  const matchup = district && matchups[district.district_id];
  if (!district || !matchup) return <p className="vote-electorate-note">Forecast unavailable for this electorate.</p>;
  const [first, second] = matchup.pair;
  const label = (party: Party) => {
    const name = candidate(party);
    return name ? `${name} (${partyMeta[party].label})` : partyMeta[party].label;
  };
  const leader = district.favoured_party as Party;
  const { mean, low, high } = matchup.firstShare;
  return <section className="vote-outlook vote-electorate" aria-label={`${districtName} experimental forecast`}>
    <header><p className="eyebrow">Experimental electorate forecast · {date(diagnostics.asOf)}</p><h3>{label(leader)} wins most often · {pct(district.favoured_probability * 100)} of all runs</h3></header>
    <div className="vote-outlook-grid">
      <div><h4>Top three on first preferences</h4><PrimaryRanking candidate={candidate} values={{ ALP: district.primary_alp, LIB_NAT: district.primary_lib_nat, ONP: district.primary_onp, GRN: district.primary_grn, OTH_IND: district.primary_oth_ind }} /></div>
      <div><h4>Most frequent final pair · {pct(100 * matchup.draws / diagnostics.simulations)} of runs</h4>
        <p>Modelled two-candidate preferred (2CP), for runs with this pair</p>
        <div className="vote-pair-labels"><span>{label(first)} <b>{pct(mean)}</b></span><span>{label(second)} <b>{pct(100 - mean)}</b></span></div>
        <div className="vote-pair-bar" aria-hidden="true" style={{ background: `var(--${partyMeta[second].css})` }}><i style={{ width: pct(mean), background: `var(--${partyMeta[first].css})` }} /></div>
        <p>Middle 80% for {partyMeta[first].label} in this matchup: {pct(low)}–{pct(high)}. {partyMeta[first].label} wins {pct(100 * matchup.firstWins / matchup.draws)} of runs with this pair.</p>
      </div>
    </div>
    <div className="vote-outlook-source"><span>The model counts party groups. Names identify sole official nominees where the mapping is clear. Others and independents are pooled.</span><button type="button" onClick={openPolls}>See polling inputs →</button></div>
  </section>;
}
