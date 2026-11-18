import { useEffect, useState } from "react";
import { parties, partyMeta, type Party } from "./assembly-parties";
import { pollSeries } from "./poll-data.generated";
import replayData from "./polling-replay.generated.json";
import "./forecast-explorers.css";

type Values = Record<Party, number>;
type Frame = { date: string; pollIds: string[]; variants: Record<string, { mean: Values; low: Values; high: Values }> };
const frames: Frame[] = replayData.frames;
const byId = new Map<string, (typeof pollSeries)[number]>(pollSeries.map((poll) => [poll.id, poll]));
const dates = new Intl.DateTimeFormat("en-AU", { dateStyle: "medium", timeZone: "UTC" });
const last = frames.length - 1;
const left = 41, right = 585;
const start = Date.parse(frames[0].date);
const end = Date.parse(frames[last].date);
const x = (date: string) => left + (Date.parse(date) - start) / (end - start || 1) * (right - left);
const y = (value: number) => 201 - value * 5;
const pct = (n: number) => `${n.toFixed(1)}%`;
const colour = (p: Party) => `var(--${partyMeta[p].css})`;

export default function PollingReplay() {
  const [index, setIndex] = useState(last);
  const [halfLife, setHalfLife] = useState(String(replayData.defaultHalfLife));
  const [mode, setMode] = useState<"line" | "ribbons">("line");
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing || index === last) return;
    const timer = window.setTimeout(() => {
      setIndex(index + 1);
      if (index + 1 === last) setPlaying(false);
    }, 850);
    return () => window.clearTimeout(timer);
  }, [index, playing]);

  const active = frames[index];
  const previous = frames[index - 1];
  const shown = frames.slice(0, index + 1);
  const bars = shown.map((frame) => {
    let top = 13;
    const values = frame.variants[halfLife].mean;
    return Object.fromEntries([...parties].sort((a, b) => values[b] - values[a]).map((p) => {
      const bottom = top + 1.55 * values[p];
      const bounds = [top, bottom];
      top = bottom + 6;
      return [p, bounds];
    }));
  });
  const stats = active.variants[halfLife];
  const previousIds = new Set(previous?.pollIds);
  const newIds = active.pollIds.filter((id) => !previousIds.has(id));
  const admitted = active.pollIds.flatMap((id) => { const p = byId.get(id); return p ? [p] : []; })
    .sort((a, b) => b.publicationDate.localeCompare(a.publicationDate));
  const ticks = [0, 1, 2, 3].map((i) => new Date(start + (end - start) * i / 3).toISOString());
  return <section className="surface forecast-explorer" id="polling-replay" aria-labelledby="polling-replay-title">
    <h3 id="polling-replay-title">Replay the polling average</h3>
    <p>Each stop refits the forecast’s first-preference average with admitted polls published by that date. Earlier stops reconstruct the series using the latest release’s admission list.</p>
    <div className="forecast-options replay-controls">
      <label>Weight of earlier polls
        <select value={halfLife} onChange={(event) => setHalfLife(event.target.value)}>
          {replayData.windows.map((days) => <option key={days} value={days}>Halves every {days} days</option>)}
        </select>
      </label>
      <label>Chart view
        <select value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}><option value="line">Trend lines</option><option value="ribbons">Rank ribbons</option></select>
      </label>
      <button type="button" onClick={() => {
        if (playing) setPlaying(false);
        else { if (index === last) setIndex(0); setPlaying(true); }
      }}>{playing ? "Pause replay" : "Play replay"}</button>
    </div>
    <label className="replay-timeline">Publication timeline
      <input type="range" min={0} max={last} value={index} aria-valuetext={dates.format(new Date(active.date))} onChange={(event) => { setPlaying(false); setIndex(Number(event.target.value)); }} />
    </label>
    <p aria-live={playing ? "off" : "polite"}><strong>{dates.format(new Date(active.date))}</strong> · {active.pollIds.length} admitted polls · {previous ? `${newIds.length} added at this stop` : "First replay stop"}</p>
    <svg viewBox="0 0 620 231" role="img" aria-label={mode === "line" ? "First-preference polling trends by party" : "Polling rank ribbons, with width representing first-preference share"}>
      {mode === "line" && [0, 10, 20, 30, 40].map((n) => <g key={n}><line x1={left} x2={right} y1={y(n)} y2={y(n)} opacity=".23" stroke="currentColor" /><text x={36} y={y(n) + 4} textAnchor="end">{n}%</text></g>)}
      {ticks.map((tick, i) => <text key={i} x={x(tick)} y={224} textAnchor="middle">{new Intl.DateTimeFormat("en-AU", { month: "short", timeZone: "UTC" }).format(new Date(tick))}</text>)}
      <line x1={x(active.date)} x2={x(active.date)} y1={3} y2={202} stroke="currentColor" opacity=".5" strokeDasharray="4 4" />
      {parties.map((p) => mode === "line" ? <g key={p}>
        <polyline fill="none" stroke={colour(p)} strokeWidth={2.8} points={shown.map((f) => `${x(f.date)},${y(f.variants[halfLife].mean[p])}`).join(" ")} />
        <circle cx={x(active.date)} cy={y(stats.mean[p])} r={4} fill={colour(p)} />
      </g> : <g key={p}>
        {shown.slice(1).map((f, j) => {
          const a = x(shown[j].date), b = x(f.date), m = (a + b) / 2;
          const [at, ab] = bars[j][p], [bt, bb] = bars[j + 1][p];
          return <path key={f.date} fill={colour(p)} opacity=".73" d={`M${a} ${at} C${m} ${at} ${m} ${bt} ${b} ${bt} L${b} ${bb} C${m} ${bb} ${m} ${ab} ${a} ${ab}Z`} />;
        })}
        <rect x={x(active.date) - 2} y={bars[index][p][0]} height={bars[index][p][1] - bars[index][p][0]} width={5} fill={colour(p)} />
      </g>)}
    </svg>
    <ul className="poll-replay-values">{parties.map((p) => {
      const change = previous ? stats.mean[p] - previous.variants[halfLife].mean[p] : null;
      return <li key={p} style={{ borderColor: colour(p) }}><strong>{partyMeta[p].label}</strong><b>{pct(stats.mean[p])}</b><span>{pct(stats.low[p])}–{pct(stats.high[p])} middle 80%</span>{change !== null && <span>{change.toFixed(1) === "-0.0" ? "0.0" : `${change >= .05 ? "+" : ""}${change.toFixed(1)}`} pp since previous stop</span>}</li>;
    })}</ul>
    <details><summary>Polls available at this stop</summary><ul>{admitted.map((poll) => <li key={poll.id}>
      {poll.sourceUrl ? <a href={poll.sourceUrl}>{poll.pollster}</a> : poll.pollster} · Published {dates.format(new Date(poll.publicationDate))} · Fieldwork ended {dates.format(new Date(poll.fieldworkEnd))}{newIds.includes(poll.id) && " · Added at this stop"}
    </li>)}</ul></details>
    <p className="chart-note">{mode === "ribbons" ? "Ribbon width shows vote share. Crossings indicate a rank change between stops. " : ""}A movement can reflect several new polls or a change in their weights. The interval describes the polling model at that stop.</p>
  </section>;
}
