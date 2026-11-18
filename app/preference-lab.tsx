import { useState } from "react";
import { partyMeta, type Party } from "./assembly-parties";
import "./forecast-explorers.css";

type TransferParty = Extract<Party, "LIB_NAT" | "ALP" | "GRN">;
const parties: TransferParty[] = ["LIB_NAT", "ALP", "GRN"];
const colour = (party: TransferParty) => `var(--${partyMeta[party].css})`;
const label = (party: TransferParty) => partyMeta[party].label;
const percent = (value: number) => `${value.toFixed(1)}%`;
const aec = "https://results.aec.gov.au/31496/Website/HouseDivisionPage-31496-203.htm";

export default function PreferenceLab() {
  const [split, setSplit] = useState(48);
  const before = { LIB_NAT: 37, ALP: 37 - split / 10, GRN: 26 + split / 10 };
  const tied = split === 55;
  const eliminated = split < 55 ? "GRN" : "ALP";
  const survivor = eliminated === "GRN" ? "ALP" : "GRN";
  const toCoalition = before[eliminated] * (eliminated === "ALP" ? .30 : .50);
  const coalition = before.LIB_NAT + toCoalition;
  const survivorShare = 100 - coalition;
  const winner = coalition > survivorShare ? "LIB_NAT" : survivor;
  const scale = 1.5;
  const left = { LIB_NAT: 42, ALP: 42 + before.LIB_NAT * scale + 8, GRN: 42 + (before.LIB_NAT + before.ALP) * scale + 16 };
  const right = 42 + coalition * scale + 8;
  const flows: [TransferParty, number, number, number][] = [
    ["LIB_NAT", left.LIB_NAT, 42, before.LIB_NAT], [survivor, left[survivor], right, before[survivor]],
    [eliminated, left[eliminated], 42 + before.LIB_NAT * scale, toCoalition],
    [eliminated, left[eliminated] + toCoalition * scale, right + before[survivor] * scale, before[eliminated] - toCoalition],
  ];
  return <section className="surface forecast-explorer" id="preference-lab" aria-labelledby="preference-lab-title">
    <h3 id="preference-lab-title">How the last exclusion changes a seat</h3>
    <details><summary>Observed count · Calwell, federal 2025</summary>
      <p>Carly Moore started third on 11.95% and reached the final two. After the penultimate exclusion, Moore had 26,665 votes, ahead of Liberal Usman Ghani on 20,030. Labor’s Basem Abdo then won the final count with 55.08%.</p>
      <p>Moore received 68.32% of the Liberals’ last exclusion parcel. Among ballots marked Liberal first, 70.34% ranked Moore above Abdo. Those are different groups of ballots. The exclusion parcel includes votes that arrived from candidates already eliminated.</p>
      <p><a href={aec}>Australian Electoral Commission count and preference tables</a></p>
    </details>
    <h4>Try an illustrative count</h4>
    <label className="preference-slider">Share of a hypothetical 10-point parcel going to the Greens
      <input type="range" min={10} max={90} value={split} aria-valuetext={`${split}% to Greens`} onChange={(e) => setSplit(Number(e.target.value))} />
    </label>
    <p>{split}% to Greens · {100 - split}% to Labor</p>
    <svg viewBox="0 0 530 218" role="img" aria-label="Illustrative transfer ribbons sized by share of formal votes">
      <text x="83" y="25">Three remaining</text><text x="357" y="25">Final pair</text>
      {!tied && flows.map(([party, a, b, value], i) => {
        const w = value * scale;
        return <path key={i} fill={colour(party)} opacity=".61" d={`M111 ${a} C200 ${a} 252 ${b} 354 ${b} L354 ${b + w} C252 ${b + w} 200 ${a + w} 111 ${a + w}Z`} />;
      })}
      {parties.map((p) => <g key={p}><rect x="104" width="7" y={left[p]} height={before[p] * scale} fill={colour(p)} /><text x="100" y={left[p] + before[p] * scale / 2} textAnchor="end">{label(p)} {percent(before[p])}</text></g>)}
      {!tied && <><rect x="354" width="7" y="42" height={coalition * scale} fill={colour("LIB_NAT")} /><text x="368" y={42 + coalition * scale / 2}>Coalition {percent(coalition)}</text><rect x="354" width="7" y={right} height={survivorShare * scale} fill={colour(survivor)} /><text x="368" y={right + survivorShare * scale / 2}>{label(survivor)} {percent(survivorShare)}</text></>}
    </svg>
    <p aria-live="polite"><strong>{tied ? "Labor and Greens tie at the final exclusion. The tie-breaking rule determines the pair." : `${label(eliminated)} ${eliminated === "GRN" ? "are" : "is"} excluded. Coalition faces ${label(survivor)}. ${winner === "GRN" ? "The Greens win" : `${label(winner)} wins`} with ${percent(Math.max(coalition, survivorShare))}.`}</strong></p>
    <p className="chart-note">This example assumes 30% of an eliminated Labor parcel or 50% of an eliminated Greens parcel goes to the Coalition. The other votes go to the surviving candidate.</p>
  </section>;
}
