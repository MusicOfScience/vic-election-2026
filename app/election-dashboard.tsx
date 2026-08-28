"use client";

import { useMemo, useState } from "react";
import { Activity, ArrowRight, CircleHelp, Database, ExternalLink, History, Landmark, Layers3, MapPinned, Search, ShieldCheck, Vote } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { districts as districtBaselines, validationFolds } from "./data.generated";
import { boothData } from "./booth-data.generated";
import { modelLayers, pollSeries, validationSummary } from "./forecast-data";
import { historicalDistricts } from "./historical-data.generated";
import { modelOutput } from "./model-output.generated";

type District = (typeof modelOutput.districts)[number];
type Party = "ALP" | "LIB_NAT" | "ONP" | "GRN" | "OTH_IND";
type Booth = {
  name: string;
  formal: number;
  informal: number;
  total: number;
  primaryVotes: Record<Party, number>;
  primaryPct: Record<Party, number>;
  twoCandidate: { votes: readonly number[]; pct: readonly number[] } | null;
};
type BoothDistrict = {
  districtId: string;
  districtName: string;
  status: string;
  source?: string;
  twoCandidateSource?: string;
  finalTwo?: readonly { name: string; party: string }[];
  booths: readonly Booth[];
};
const parties: Party[] = ["ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND"];
const partyMeta: Record<Party, { label: string; short: string; css: string; colour: string }> = {
  ALP: { label: "Labor", short: "ALP", css: "labor", colour: "#d84a42" },
  LIB_NAT: { label: "Coalition", short: "L–NP", css: "coalition", colour: "#2e63ad" },
  ONP: { label: "One Nation", short: "ONP", css: "onp", colour: "#6e4da0" },
  GRN: { label: "Greens", short: "GRN", css: "greens", colour: "#159867" },
  OTH_IND: { label: "Other / independent", short: "OTH", css: "other", colour: "#d19b2a" },
};
const number = new Intl.NumberFormat("en-AU");
const pct = (value: number, digits = 0) => `${(value * 100).toFixed(digits)}%`;
const chamber = Object.fromEntries(modelOutput.chamber.map((row) => [row.party, row])) as Record<Party, (typeof modelOutput.chamber)[number]>;
const regions = [...new Set(modelOutput.districts.map((district) => district.region_name))].sort();
const baselineById = new Map(districtBaselines.map((district) => [district.id, district]));
const historyById = new Map(historicalDistricts.map((district) => [district.districtId, district]));
const boothById = new Map(boothData.districts.map((district) => [district.districtId, district as unknown as BoothDistrict]));

function confidenceLabel(probability: number) {
  if (probability < .55) return "Toss-up";
  if (probability < .65) return "Leaning";
  if (probability < .80) return "Likely";
  return "Strongly favoured";
}

function finalPairLabel(value: string) {
  return value.split("–").map((party) => partyMeta[party as Party]?.label ?? party.replaceAll("_", " ")).join(" vs ");
}

function districtProbability(district: District, party: Party) {
  if (party === "ALP") return district.win_alp;
  if (party === "LIB_NAT") return district.win_lib_nat;
  if (party === "ONP") return district.win_onp;
  if (party === "GRN") return district.win_grn;
  return district.win_oth_ind;
}
function districtPrimary(district: District, party: Party) {
  if (party === "ALP") return district.primary_alp;
  if (party === "LIB_NAT") return district.primary_lib_nat;
  if (party === "ONP") return district.primary_onp;
  if (party === "GRN") return district.primary_grn;
  return district.primary_oth_ind;
}

function OutcomeProbability({ label, probability, active }: { label: string; probability: number; active?: boolean }) {
  return <div className={`outcome-probability ${active ? "active" : ""}`}><span>{label}</span><strong>{pct(probability)}</strong><i><b style={{ width: pct(probability) }} /></i></div>;
}

function ForecastQuickRead() {
  return <section className="quick-read" aria-label="Forecast in plain English">
    <div className="quick-read-heading"><CircleHelp size={18} /><div><p className="eyebrow">In plain English</p><h3>What this forecast is saying</h3></div></div>
    <div className="quick-read-grid">
      <article><strong>Most likely outcome</strong><p>No party reaches 45 seats on its own in about {pct(chamber.ALP.hung_probability)} of simulations.</p></article>
      <article><strong>The middle result</strong><p>Labor finishes near {Math.round(chamber.ALP.median)} seats and the Coalition near {Math.round(chamber.LIB_NAT.median)}—but the plausible range is wide.</p></article>
      <article><strong>How to read a seat</strong><p>A 60% win chance means the party won 6 in 10 modelled elections. It does not mean a 60% vote share.</p></article>
    </div>
  </section>;
}

function BattlegroundBoard() {
  const closest = [...modelOutput.districts].sort((a, b) => a.favoured_probability - b.favoured_probability).slice(0, 12);
  const bands = [
    { label: "Toss-ups", detail: "Party ahead below 55%", count: modelOutput.districts.filter((seat) => seat.favoured_probability < .55).length },
    { label: "Leaning", detail: "55% to below 65%", count: modelOutput.districts.filter((seat) => seat.favoured_probability >= .55 && seat.favoured_probability < .65).length },
    { label: "Likely", detail: "65% to below 80%", count: modelOutput.districts.filter((seat) => seat.favoured_probability >= .65 && seat.favoured_probability < .80).length },
    { label: "Strongly favoured", detail: "80% or higher", count: modelOutput.districts.filter((seat) => seat.favoured_probability >= .80).length },
  ];
  return <section className="surface battleground-board">
    <div className="section-heading"><div><p className="eyebrow">Where the election is closest</p><h3>The twelve most uncertain electorates</h3><p className="section-subcopy">Ordered by the leading party’s win chance. A close seat is one where simulations frequently produce different winners—not simply one with a small 2022 margin.</p></div><Badge variant="outline">Model uncertainty</Badge></div>
    <div className="certainty-bands">{bands.map((band) => <article key={band.label}><strong>{band.count}</strong><span>{band.label}</span><small>{band.detail}</small></article>)}</div>
    <div className="battleground-grid">{closest.map((district, index) => { const party = district.favoured_party as Party; return <article key={district.district_id}><span>{String(index + 1).padStart(2, "0")}</span><div><h4>{district.district_name}</h4><p>{finalPairLabel(district.likely_final_pair)}</p></div><div className={`battle-party ${partyMeta[party].css}`}><strong>{pct(district.favoured_probability)}</strong><small>{partyMeta[party].label}</small></div></article>; })}</div>
    <p className="chart-note">Open “88 electorates” for the complete probability breakdown, historical swing and official voting-centre evidence behind any seat.</p>
  </section>;
}

function SeatArc() {
  const seats = [...modelOutput.districts].sort((a, b) => parties.indexOf(a.favoured_party as Party) - parties.indexOf(b.favoured_party as Party) || a.favoured_probability - b.favoured_probability);
  const rows = [18, 16, 14, 12, 10, 8, 6, 4];
  const points: { x: number; y: number; seat: District }[] = [];
  let cursor = 0;
  rows.forEach((count, rowIndex) => {
    const radius = 76 + rowIndex * 23;
    for (let index = 0; index < count; index += 1) {
      const angle = Math.PI + (Math.PI * index) / Math.max(1, count - 1);
      points.push({ x: 260 + Math.cos(angle) * radius, y: 250 + Math.sin(angle) * radius, seat: seats[cursor] });
      cursor += 1;
    }
  });
  return <svg className="seat-arc" viewBox="0 0 520 280" role="img" aria-label="Simulated 88-seat Legislative Assembly"><line x1="260" y1="248" x2="260" y2="265" className="majority-line" />{points.map(({ x, y, seat }) => { const party = seat.favoured_party as Party; return <circle key={seat.district_id} cx={x} cy={y} r="7.3" fill={partyMeta[party].colour} opacity={.42 + seat.favoured_probability * .58}><title>{seat.district_name}: {partyMeta[party].label} {pct(seat.favoured_probability)}</title></circle>; })}</svg>;
}

function Forecast() {
  const hung = chamber.ALP.hung_probability;
  const outcomes = [["Labor majority", chamber.ALP.majority_probability], ["Hung parliament", hung], ["Coalition majority", chamber.LIB_NAT.majority_probability]] as const;
  const distribution = modelOutput.seatDistribution.filter((row) => row.seats >= 18 && row.seats <= 60 && row.probability > .0002).map((row) => ({ ...row, probabilityPct: row.probability * 100 }));
  return <div className="tab-stack forecast-stack">
    <section className="forecast-hero"><div className="forecast-copy"><div className="forecast-kicker"><Badge>Experimental forecast</Badge><span>{number.format(modelOutput.manifest.simulations)} whole-election simulations · 26 August 2026</span></div><p className="eyebrow">Lower House · all 88 electorates</p><h2>Hung parliament leads.</h2><p className="forecast-deck">The model reruns the whole Victorian election 5,000 times. Polls, official results, local patterns, by-elections and uncertain preference flows change together in each run.</p><div className="seat-totals" aria-label="Middle forecast seat totals and likely ranges"><div className="labor"><span>Labor</span><strong>{Math.round(chamber.ALP.median)}</strong><small>Likely range: {Math.round(chamber.ALP.lower80)}–{Math.round(chamber.ALP.upper80)}</small></div><div className="coalition"><span>Coalition</span><strong>{Math.round(chamber.LIB_NAT.median)}</strong><small>Likely range: {Math.round(chamber.LIB_NAT.lower80)}–{Math.round(chamber.LIB_NAT.upper80)}</small></div><div className="onp"><span>One Nation</span><strong>{Math.round(chamber.ONP.median)}</strong><small>Likely range: {Math.round(chamber.ONP.lower80)}–{Math.round(chamber.ONP.upper80)}</small></div></div></div><div className="parliament-card"><SeatArc /><div className="arc-caption"><span>88 electorates</span><strong>45 for a majority</strong><span>Colour = party most often winning each seat</span></div></div></section>
    <ForecastQuickRead />
    <section className="outcome-strip">{outcomes.map(([label, probability]) => <OutcomeProbability key={label} label={label} probability={probability} active={label === "Hung parliament"} />)}</section>
    <BattlegroundBoard />
    <section className="forecast-grid"><article className="surface distribution-card"><div className="section-heading"><div><p className="eyebrow">How often each total occurs</p><h3>Labor’s possible Lower House results</h3></div><Badge variant="outline">Middle result {Math.round(chamber.ALP.median)}</Badge></div><div className="distribution-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={distribution} margin={{ top: 12, right: 4, left: -20, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="seats" tickLine={false} axisLine={false} tick={{ fontSize: 9 }} /><YAxis tickLine={false} axisLine={false} tick={{ fontSize: 9 }} tickFormatter={(v) => `${v}%`} /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, "Share of simulations"]} /><ReferenceLine x={45} stroke="#ea7540" strokeWidth={2} label={{ value: "MAJORITY", fill: "#9a522f", fontSize: 8 }} /><Bar dataKey="probabilityPct" radius={[2, 2, 0, 0]}>{distribution.map((row) => <Cell key={row.seats} fill={row.seats >= 45 ? "#d84a42" : "#173d64"} />)}</Bar></BarChart></ResponsiveContainer></div><p className="chart-note">Each bar shows the share of 5,000 whole-election simulations producing that Labor seat total. The 88 electorates move together rather than being added as if they were independent.</p></article><article className="surface signal-card"><p className="eyebrow">Central finding</p><h3>Three large blocs, few easy paths.</h3><div className="signal-number"><strong>{pct(hung)}</strong><span>chance that no party wins 45 seats</span></div><div className="signal-rule" /><p>One Nation’s polling rise is modelled as a distinct multi-party force. The count does not assume every electorate ends Labor versus Coalition.</p></article></section>
    <section className="model-warning"><ShieldCheck size={20} /><div><strong>Experimental, reproducible, and deliberately uncertain</strong><p>The historical baseline is verified, but this 2026 layer has not cleared a production forecast gate. It is a documented research estimate, not voting advice. The failed demographic challenger has zero central weight.</p></div></section>
  </div>;
}

function PollBars() {
  const poll = modelOutput.manifest.polling;
  return <div className="aggregate-bars">{parties.map((party) => <div key={party}><span>{partyMeta[party].label}</span><i><b className={partyMeta[party].css} style={{ width: `${poll.mean[party] * 3}%` }} /></i><strong>{poll.mean[party].toFixed(1)}%</strong></div>)}</div>;
}

function Polling() {
  const houseEffects = Object.entries(modelOutput.manifest.polling.house_effects);
  return <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">Poll of polls</p><h2>Roy Morgan is one input—not the answer.</h2><p>Nine eligible polls are combined. Newer polls count more, very large samples are prevented from dominating, and the model allows for each pollster’s recurring lean.</p></div><Badge variant="outline">9 eligible polls</Badge></section><section className="polling-layout"><article className="surface poll-card"><div className="section-heading"><div><p className="eyebrow">Published poll results</p><h3>A fragmented first-preference vote</h3></div><Badge variant="outline">Points are separate polls</Badge></div><div className="poll-series-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={pollSeries} margin={{ top: 14, right: 12, left: -18, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 9 }} /><YAxis domain={[10, 34]} tickLine={false} axisLine={false} tick={{ fontSize: 9 }} tickFormatter={(v) => `${v}%`} /><Tooltip labelFormatter={(_, payload) => payload?.[0]?.payload ? `${payload[0].payload.pollster} · n=${number.format(payload[0].payload.n)}` : ""} /><Line type="monotone" dataKey="alp" name="Labor" stroke="#d84a42" strokeWidth={2.2} /><Line type="monotone" dataKey="coalition" name="Coalition" stroke="#2e63ad" strokeWidth={2.2} /><Line type="monotone" dataKey="onp" name="One Nation" stroke="#6e4da0" strokeWidth={2.2} /><Line type="monotone" dataKey="greens" name="Greens" stroke="#159867" strokeWidth={2.2} /></LineChart></ResponsiveContainer></div><p className="chart-note">The connecting lines help the eye follow each party; they are not a claimed trend between polls. The combined estimate keeps all party shares adding to 100%.</p></article><article className="surface aggregate-card compact"><div className="section-heading"><div><p className="eyebrow">Combined estimate · 26 Aug</p><h3>Where support sits now</h3></div><strong className="poll-count">Likely ranges</strong></div><PollBars />{parties.map((party) => <p className="chart-note" key={party}><strong>{partyMeta[party].short}</strong> likely range {modelOutput.manifest.polling.lower80[party].toFixed(1)}–{modelOutput.manifest.polling.upper80[party].toFixed(1)}%</p>)}</article></section><section className="surface poll-register"><div className="section-heading"><div><p className="eyebrow">Estimated pollster lean</p><h3>Pollsters may lean; no pollster is “the truth”.</h3><p className="section-subcopy">A positive number means that pollster has tended to report the party a little higher than the combined polling picture; a negative number means lower.</p></div><Badge variant="outline">percentage-point adjustment</Badge></div><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>Pollster</TableHead>{parties.map((party) => <TableHead key={party}>{partyMeta[party].short}</TableHead>)}</TableRow></TableHeader><TableBody>{houseEffects.map(([pollster, values]) => <TableRow key={pollster}><TableCell className="district-name">{pollster}</TableCell>{parties.map((party) => <TableCell key={party}>{values[party] >= 0 ? "+" : ""}{values[party].toFixed(1)}</TableCell>)}</TableRow>)}</TableBody></Table></div></section></div>;
}

function partyFromRaw(value: string): Party {
  const raw = value.toLowerCase();
  if (raw.includes("labor")) return "ALP";
  if (raw.includes("liberal") || raw.includes("nationals")) return "LIB_NAT";
  if (raw.includes("one nation")) return "ONP";
  if (raw.includes("greens")) return "GRN";
  return "OTH_IND";
}

function candidateShortName(value: string) {
  return value.split(",")[0].trim().replaceAll("nan", "Independent");
}

function BoothExplorer({ district }: { district: District }) {
  const record = boothById.get(district.district_id);
  const [query, setQuery] = useState("");
  const [metric, setMetric] = useState<Party | "FINAL_TWO">(district.favoured_party as Party);
  if (!record || !record.booths.length) {
    return <section className="booth-launcher"><Vote size={20} /><div><p className="eyebrow">Voting-centre explorer</p><h3>Supplementary-election booth data still to come</h3><p>Narracan voted separately in January 2023 after the 2022 election was postponed. Its voting-centre table needs the supplementary-election source and is not being mixed into the ordinary 2022 acquisition.</p></div></section>;
  }

  const finalTwo = record.finalTwo ?? [];
  const firstFinalParty = finalTwo[0] ? partyFromRaw(finalTwo[0].party) : "OTH_IND";
  const valueFor = (booth: Booth) => metric === "FINAL_TWO" ? (booth.twoCandidate?.pct[0] ?? 0) : booth.primaryPct[metric];
  const filtered = record.booths.filter((booth) => booth.name.toLowerCase().includes(query.toLowerCase())).sort((a, b) => valueFor(b) - valueFor(a));
  const chartRows = (filtered.length > 14 ? [...filtered.slice(0, 7), ...filtered.slice(-7)] : filtered).sort((a, b) => valueFor(b) - valueFor(a)).map((booth) => ({ name: booth.name, value: valueFor(booth), total: booth.total }));
  const metricLabel = metric === "FINAL_TWO" && finalTwo[0] ? `${candidateShortName(finalTwo[0].name)} final-two share` : `${partyMeta[metric as Party].label} first-preference share`;
  const metricColour = metric === "FINAL_TWO" ? partyMeta[firstFinalParty].colour : partyMeta[metric].colour;

  return <section className="seat-detail-section embedded-booths">
    <div className="seat-detail-heading"><div><p className="eyebrow"><Vote size={13} /> Official VEC 2022 results</p><h3>{record.booths.length} ordinary voting centres</h3></div><span>Physical booths only · vote modes excluded</span></div>
    <p className="seat-explainer">Explore genuine state-election booth results. Early, postal, absent and provisional votes are district-wide vote modes, so they are deliberately excluded from this geographic comparison.</p>
    <div className="booth-controls"><label className="search-field"><Search size={15} /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a voting centre…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" /></label><Select value={metric} onValueChange={(value) => setMetric((value ?? district.favoured_party) as Party | "FINAL_TWO")}><SelectTrigger className="filter-select" aria-label="Choose booth comparison"><SelectValue /></SelectTrigger><SelectContent>{parties.map((party) => <SelectItem key={party} value={party}>{partyMeta[party].label} first preference</SelectItem>)}{finalTwo.length === 2 && <SelectItem value="FINAL_TWO">{candidateShortName(finalTwo[0].name)} vs {candidateShortName(finalTwo[1].name)} final two</SelectItem>}</SelectContent></Select></div>
    <div className="booth-chart-heading"><strong>{metricLabel}</strong><span>{filtered.length > 14 ? "Seven highest and seven lowest" : `${filtered.length} matching booths`}</span></div>
    {chartRows.length ? <div className="booth-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartRows} layout="vertical" margin={{ top: 4, right: 18, left: 18, bottom: 0 }}><CartesianGrid horizontal={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 8 }} tickFormatter={(value) => `${value}%`} /><YAxis type="category" dataKey="name" width={112} tickLine={false} axisLine={false} tick={{ fontSize: 8 }} /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, metricLabel]} labelFormatter={(label, payload) => `${label} · ${number.format(payload?.[0]?.payload?.total ?? 0)} total votes`} /><Bar dataKey="value" fill={metricColour} radius={[0, 2, 2, 0]} /></BarChart></ResponsiveContainer></div> : <p className="empty-booths">No voting centre matches that search.</p>}
    <div className="booth-table desktop-table"><Table><TableHeader><TableRow><TableHead>Voting centre</TableHead><TableHead>Formal</TableHead>{parties.map((party) => <TableHead key={party}>{partyMeta[party].short} 1st pref.</TableHead>)}{finalTwo.length === 2 && <TableHead>{candidateShortName(finalTwo[0].name)} 2CP</TableHead>}</TableRow></TableHeader><TableBody>{filtered.map((booth) => <TableRow key={booth.name}><TableCell className="district-name">{booth.name}</TableCell><TableCell>{number.format(booth.formal)}</TableCell>{parties.map((party) => <TableCell key={party}>{booth.primaryPct[party].toFixed(1)}%</TableCell>)}{finalTwo.length === 2 && <TableCell><strong>{booth.twoCandidate ? `${booth.twoCandidate.pct[0].toFixed(1)}%` : "—"}</strong></TableCell>}</TableRow>)}</TableBody></Table></div>
    <div className="mobile-booths">{filtered.map((booth) => <article key={booth.name}><div><strong>{booth.name}</strong><span>{number.format(booth.formal)} formal votes</span></div><dl>{parties.map((party) => <div key={party}><dt>{partyMeta[party].short}</dt><dd>{booth.primaryPct[party].toFixed(1)}%</dd></div>)}{finalTwo.length === 2 && <div><dt>{candidateShortName(finalTwo[0].name)} 2CP</dt><dd>{booth.twoCandidate ? `${booth.twoCandidate.pct[0].toFixed(1)}%` : "—"}</dd></div>}</dl></article>)}</div>
    <div className="booth-source-links"><a href={record.source} target="_blank" rel="noreferrer">Verify first preferences at VEC <ExternalLink size={12} /></a><a href={record.twoCandidateSource} target="_blank" rel="noreferrer">Verify final two at VEC <ExternalLink size={12} /></a></div>
  </section>;
}

function SeatDetail({ district, onOpenChange }: { district: District | null; onOpenChange: (open: boolean) => void }) {
  if (!district) return null;
  const favoured = district.favoured_party as Party;
  const baseline = baselineById.get(district.district_id);
  const history = historyById.get(district.district_id);
  const winRows = parties.map((party) => ({ party, probability: districtProbability(district, party) })).sort((a, b) => b.probability - a.probability);
  const primaryRows = parties.map((party) => ({ party, primary: districtPrimary(district, party) })).sort((a, b) => b.primary - a.primary);
  const swingChart = history?.cycles.map((cycle) => ({ cycle: cycle.cycle, swing: Number(cycle.alpSwing.toFixed(1)), comparison: cycle.comparison })) ?? [];
  return <Sheet open onOpenChange={onOpenChange}>
    <SheetContent className="seat-sheet">
      <SheetHeader className="seat-sheet-header">
        <p className="eyebrow">Electorate profile · {district.region_name}</p>
        <SheetTitle>{district.district_name}</SheetTitle>
        <SheetDescription>Forecast, 2022 baseline and comparable historical movement in one view.</SheetDescription>
      </SheetHeader>
      <div className="seat-sheet-body">
        <section className={`seat-verdict ${partyMeta[favoured].css}`}>
          <div><span>{confidenceLabel(district.favoured_probability)}</span><strong>{partyMeta[favoured].label}</strong><p>favoured to win</p></div>
          <b>{pct(district.favoured_probability)}</b>
        </section>

        <section className="seat-detail-section">
          <div className="seat-detail-heading"><div><p className="eyebrow">Who can win?</p><h3>Chance of winning the seat</h3></div><span>Across 5,000 whole-election simulations</span></div>
          <div className="seat-probability-list">{winRows.map(({ party, probability }) => <div key={party}><span>{partyMeta[party].label}</span><i><b className={partyMeta[party].css} style={{ width: pct(probability) }} /></i><strong>{pct(probability)}</strong></div>)}</div>
          <p className="seat-explainer">These are chances, not vote shares. The model can find a Greens, One Nation or independent final-two contest rather than forcing every seat into Labor versus Coalition.</p>
        </section>

        <section className="seat-detail-section">
          <div className="seat-detail-heading"><div><p className="eyebrow">First preferences</p><h3>Average modelled primary vote</h3></div><span>Before preferences are distributed</span></div>
          <div className="primary-breakdown">{primaryRows.map(({ party, primary }) => <div key={party}><span>{partyMeta[party].short}</span><i><b className={partyMeta[party].css} style={{ width: `${primary * 2.6}%` }} /></i><strong>{primary.toFixed(1)}%</strong></div>)}</div>
          <dl className="seat-facts"><div><dt>Most likely final two</dt><dd>{finalPairLabel(district.likely_final_pair)}</dd></div><div><dt>Chance of that pairing</dt><dd>{pct(district.final_pair_probability)}</dd></div><div><dt>Current enrolment</dt><dd>{baseline ? number.format(baseline.enrolment) : "Not available"}</dd></div><div><dt>Compared with district average</dt><dd>{baseline ? `${baseline.enrolmentVariance >= 0 ? "+" : ""}${baseline.enrolmentVariance.toFixed(1)}%` : "Not available"}</dd></div></dl>
        </section>

        <section className="seat-detail-section historical-section">
          <div className="seat-detail-heading"><div><p className="eyebrow"><History size={13} /> Historical movement</p><h3>Labor two-party swing by election</h3></div><span>Positive = towards Labor</span></div>
          {swingChart.length ? <><div className="seat-swing-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={swingChart} margin={{ top: 8, right: 4, left: -20, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="cycle" tickLine={false} axisLine={false} tick={{ fontSize: 9 }} /><YAxis tickLine={false} axisLine={false} tick={{ fontSize: 9 }} tickFormatter={(value) => `${value > 0 ? "+" : ""}${value}`} /><Tooltip formatter={(value) => [`${Number(value) > 0 ? "+" : ""}${Number(value).toFixed(1)} pp`, "Labor swing"]} /><ReferenceLine y={0} stroke="#6c7377" /><Bar dataKey="swing" radius={[2, 2, 0, 0]}>{swingChart.map((row) => <Cell key={row.cycle} fill={row.swing >= 0 ? "#d84a42" : "#2e63ad"} />)}</Bar></BarChart></ResponsiveContainer></div><p className="seat-explainer">Boundary comparisons differ by cycle: 2010–14 is redistribution-adjusted and 2018–22 uses the VEC estimate on 2022 boundaries. Earlier same-name seats are shown only where the checkpoint marks the boundary comparison as valid.</p></> : <p className="seat-explainer">A complete comparable history is not available for this district.</p>}
          {history && <div className="baseline-callout"><span>2022 Labor two-party share</span><strong>{history.alpTpp2022.toFixed(1)}%</strong><small>{history.tppMethod2022} · {number.format(history.tppFormalVotes2022)} formal two-party votes</small></div>}
        </section>

        <BoothExplorer district={district} />
      </div>
    </SheetContent>
  </Sheet>;
}

function DistrictExplorer() {
  const [query, setQuery] = useState(""); const [region, setRegion] = useState("all"); const [party, setParty] = useState("all"); const [selected, setSelected] = useState<District | null>(null);
  const filtered = useMemo(() => modelOutput.districts.filter((district) => district.district_name.toLowerCase().includes(query.toLowerCase()) && (region === "all" || district.region_name === region) && (party === "all" || district.favoured_party === party)).sort((a, b) => a.favoured_probability - b.favoured_probability), [query, region, party]);
  return <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">All 88 electorates</p><h2>Search a seat. Open its story.</h2><p>Choose any electorate for win chances, average first preferences, the most likely final two, 2022 baseline, enrolment and up to five comparable swing cycles.</p></div><Badge variant="outline">Select a seat for detail</Badge></section><section className="surface seat-landscape"><div className="landscape-key">{parties.map((p) => <span key={p}><i className={partyMeta[p].css} />{partyMeta[p].label}</span>)}<span className="faded">Paler = less certain · tap for details</span></div><div className="seat-matrix">{[...modelOutput.districts].sort((a, b) => a.favoured_probability - b.favoured_probability).map((district) => { const p = district.favoured_party as Party; return <button key={district.district_id} className={`seat-tile ${partyMeta[p].css}`} style={{ opacity: .42 + district.favoured_probability * .58 }} title={`${district.district_name} · ${partyMeta[p].label} ${pct(district.favoured_probability)}`} onClick={() => setSelected(district)}><span>{district.district_name}</span><strong>{pct(district.favoured_probability)}</strong></button>; })}</div></section><div className="filter-bar"><label className="search-field"><Search size={17} /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search an electorate…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" /></label><Select value={region} onValueChange={(value) => setRegion(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by upper-house region"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All regions</SelectItem>{regions.map((item) => <SelectItem key={item} value={item}>{item}</SelectItem>)}</SelectContent></Select><Select value={party} onValueChange={(value) => setParty(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by favoured party"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All favoured parties</SelectItem>{parties.map((item) => <SelectItem key={item} value={item}>{partyMeta[item].label}</SelectItem>)}</SelectContent></Select></div><div className="result-count">{filtered.length} electorates · closest contests first</div><section className="surface district-table-wrap"><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>Electorate</TableHead><TableHead>Upper-house region</TableHead><TableHead>Party ahead</TableHead><TableHead>Chance of winning</TableHead><TableHead>Most likely final two</TableHead><TableHead>Avg first preference</TableHead></TableRow></TableHeader><TableBody>{filtered.map((district) => { const p = district.favoured_party as Party; return <TableRow key={district.district_id}><TableCell className="district-name"><button className="seat-open" onClick={() => setSelected(district)}>{district.district_name}<ArrowRight size={13} /></button></TableCell><TableCell className="region-name">{district.region_name}</TableCell><TableCell><span className={`party-chip ${partyMeta[p].css}`}>{partyMeta[p].label}</span></TableCell><TableCell><strong>{pct(district.favoured_probability)}</strong> <span className="confidence-word">{confidenceLabel(district.favoured_probability)}</span></TableCell><TableCell>{finalPairLabel(district.likely_final_pair)}</TableCell><TableCell>{districtPrimary(district, p).toFixed(1)}%</TableCell></TableRow>; })}</TableBody></Table></div><div className="mobile-districts">{filtered.map((district) => { const p = district.favoured_party as Party; return <button className="district-card" key={district.district_id} onClick={() => setSelected(district)}><div><h3>{district.district_name}</h3><p>{district.region_name}</p></div><dl><div><dt>Party ahead</dt><dd><span className={`party-chip ${partyMeta[p].css}`}>{partyMeta[p].label}</span></dd></div><div><dt>Chance of winning</dt><dd>{pct(districtProbability(district, p))}</dd></div><div><dt>Most likely final two</dt><dd>{finalPairLabel(district.likely_final_pair)}</dd></div><div><dt>Avg first preference</dt><dd>{districtPrimary(district, p).toFixed(1)}%</dd></div></dl><span className="open-profile">Open profile <ArrowRight size={13} /></span></button>; })}</div></section><SeatDetail district={selected} onOpenChange={(open) => { if (!open) setSelected(null); }} /></div>;
}

function Council() {
  const seatsFor = (region: (typeof modelOutput.councilRegions)[number], party: Party) => party === "ALP" ? region.seats_alp : party === "LIB_NAT" ? region.seats_lib_nat : party === "ONP" ? region.seats_onp : party === "GRN" ? region.seats_grn : region.seats_oth_ind;
  const meanFor = (region: (typeof modelOutput.councilRegions)[number], party: Party) => party === "ALP" ? region.mean_alp : party === "LIB_NAT" ? region.mean_lib_nat : party === "ONP" ? region.mean_onp : party === "GRN" ? region.mean_grn : region.mean_oth_ind;
  const totals = parties.map((party) => ({ party, seats: modelOutput.councilRegions.reduce((sum, region) => sum + seatsFor(region, party), 0) }));
  return <div className="tab-stack"><section className="council-hero"><div><p className="eyebrow">Upper House · modelled separately</p><h2>Forty seats, eight regional counts.</h2><p>Each region elects five members. The 2026 election removes group voting tickets, so the model lets voters’ preferences vary and sometimes exhaust. It forecasts party totals—not which individual candidates will win.</p></div><Badge variant="outline">8 regions × 5 seats</Badge></section><section className="surface council-total"><div className="forty-grid">{totals.flatMap(({ party, seats }) => Array.from({ length: seats }, (_, index) => <span key={`${party}-${index}`} className={partyMeta[party].css} title={partyMeta[party].label} />))}</div><div className="council-legend">{totals.map(({ party, seats }) => <div key={party}><i className={partyMeta[party].css} /><strong>{seats}</strong><span>{partyMeta[party].label}</span></div>)}</div></section><section className="region-grid">{modelOutput.councilRegions.map((region) => <article className="surface region-card" key={region.region_id}><div className="region-card-head"><h3>{region.region_name}</h3><span>most common result · {pct(region.modal_probability)}</span></div><div className="region-seat-row">{parties.flatMap((party) => Array.from({ length: seatsFor(region, party) }, (_, index) => <i className={partyMeta[party].css} key={`${party}-${index}`} title={partyMeta[party].label} />))}</div><div className="region-votes">{parties.slice(0, 4).map((party) => <span key={party}><b>{meanFor(region, party).toFixed(1)}</b>average {partyMeta[party].short} seats</span>)}</div></article>)}</section><p className="data-note">Each regional row is the single five-seat combination that occurred most often in simulations. The decimal figures underneath are averages across all simulations, so they are not meant to add up as one actual result.</p></div>;
}

const historyCycleNotes: Record<string, string> = {
  "2002–06": "Same boundaries within the cycle",
  "2006–10": "Same boundaries within the cycle",
  "2010–14": "2010 result translated onto the 2014 boundaries",
  "2014–18": "Same boundaries within the cycle",
  "2018–22": "VEC estimate of 2018 support on the 2022 boundaries",
};

function HistoricalExplorer() {
  const [cycle, setCycle] = useState("2018–22");
  const rows = historicalDistricts.flatMap((district) => {
    const result = district.cycles.find((item) => item.cycle === cycle);
    return result ? [{ districtName: district.districtName, ...result }] : [];
  }).sort((a, b) => b.alpSwing - a.alpSwing);
  const sortedSwings = rows.map((row) => row.alpSwing).sort((a, b) => a - b);
  const medianSwing = sortedSwings.length ? sortedSwings[Math.floor(sortedSwings.length / 2)] : 0;
  const flipsToLabor = rows.filter((row) => row.alpStart < 50 && row.alpEnd >= 50).length;
  const flipsFromLabor = rows.filter((row) => row.alpStart >= 50 && row.alpEnd < 50).length;
  const binStarts = [-20, -15, -10, -5, 0, 5, 10, 15];
  const distribution = binStarts.map((start, index) => ({
    range: index === 0 ? "≤−15" : index === binStarts.length - 1 ? "+15+" : `${start > 0 ? "+" : ""}${start} to ${start + 5 > 0 ? "+" : ""}${start + 5}`,
    count: rows.filter((row) => index === 0 ? row.alpSwing < -15 : index === binStarts.length - 1 ? row.alpSwing >= 15 : row.alpSwing >= start && row.alpSwing < start + 5).length,
    direction: start >= 0 ? "labor" : "coalition",
  }));
  const extremes = [...rows.slice(0, 6), ...rows.slice(-6)].sort((a, b) => b.alpSwing - a.alpSwing);

  return <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">Five election-to-election comparisons</p><h2>Swing is local, not uniform.</h2><p>See how strongly electorates moved towards or away from Labor in each historical cycle. Boundary adjustments are labelled, and these results describe the past—they are not treated as a 2026 forecast.</p></div><Select value={cycle} onValueChange={(value) => setCycle(value ?? "2018–22")}><SelectTrigger className="filter-select" aria-label="Choose historical election cycle"><SelectValue /></SelectTrigger><SelectContent>{Object.keys(historyCycleNotes).map((item) => <SelectItem key={item} value={item}>{item} election cycle</SelectItem>)}</SelectContent></Select></section>
    <section className="history-summary"><article><span>Comparable electorates</span><strong>{rows.length}</strong><small>{historyCycleNotes[cycle]}</small></article><article><span>Middle electorate swing</span><strong>{medianSwing >= 0 ? "+" : ""}{medianSwing.toFixed(1)}</strong><small>percentage points towards Labor</small></article><article><span>Crossed to Labor</span><strong>{flipsToLabor}</strong><small>two-party share moved through 50%</small></article><article><span>Crossed away</span><strong>{flipsFromLabor}</strong><small>two-party share moved below 50%</small></article></section>
    <section className="history-grid"><article className="surface history-distribution"><div className="section-heading"><div><p className="eyebrow">Distribution across electorates</p><h3>How widespread was the movement?</h3></div><Badge variant="outline">Labor two-party swing</Badge></div><div className="history-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={distribution} margin={{ top: 12, right: 6, left: -18, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="range" tickLine={false} axisLine={false} tick={{ fontSize: 8 }} /><YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 8 }} /><Tooltip formatter={(value) => [number.format(Number(value)), "Electorates"]} /><Bar dataKey="count" radius={[2, 2, 0, 0]}>{distribution.map((row) => <Cell key={row.range} fill={row.direction === "labor" ? partyMeta.ALP.colour : partyMeta.LIB_NAT.colour} />)}</Bar></BarChart></ResponsiveContainer></div><p className="chart-note">Blue bars are movements away from Labor; red bars are movements towards Labor. Counts use comparable named electorates available for that cycle.</p></article><article className="surface history-extremes"><div className="section-heading"><div><p className="eyebrow">The tails</p><h3>Largest local movements</h3></div></div><div className="extreme-list">{extremes.map((row) => <div key={row.districtName}><span>{row.districtName}</span><i><b className={row.alpSwing >= 0 ? "labor" : "coalition"} style={{ width: `${Math.min(100, Math.abs(row.alpSwing) * 5)}%` }} /></i><strong>{row.alpSwing >= 0 ? "+" : ""}{row.alpSwing.toFixed(1)}</strong></div>)}</div></article></section>
    <section className="surface historical-table"><div className="section-heading"><div><p className="eyebrow">Every comparable electorate</p><h3>{cycle} movement</h3></div><span className="history-note">Two-party preferred · Labor share</span></div><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>Electorate</TableHead><TableHead>At start</TableHead><TableHead>At end</TableHead><TableHead>Labor swing</TableHead><TableHead>Comparison basis</TableHead></TableRow></TableHeader><TableBody>{rows.map((row) => <TableRow key={row.districtName}><TableCell className="district-name">{row.districtName}</TableCell><TableCell>{row.alpStart.toFixed(1)}%</TableCell><TableCell>{row.alpEnd.toFixed(1)}%</TableCell><TableCell><strong className={row.alpSwing >= 0 ? "swing-to-labor" : "swing-to-coalition"}>{row.alpSwing >= 0 ? "+" : ""}{row.alpSwing.toFixed(1)} pp</strong></TableCell><TableCell className="region-name">{row.comparison}</TableCell></TableRow>)}</TableBody></Table></div><div className="mobile-history">{rows.map((row) => <article key={row.districtName}><strong>{row.districtName}</strong><span>{row.alpStart.toFixed(1)}% → {row.alpEnd.toFixed(1)}%</span><b className={row.alpSwing >= 0 ? "swing-to-labor" : "swing-to-coalition"}>{row.alpSwing >= 0 ? "+" : ""}{row.alpSwing.toFixed(1)} pp</b></article>)}</div></section>
    <section className="model-warning"><ShieldCheck size={20} /><div><strong>Read boundaries before comparing</strong><p>2010–14 uses a redistribution-adjusted starting point and 2018–22 uses the VEC’s estimated 2018 result on the new 2022 boundaries. The app does not pretend those estimates are raw booth counts.</p></div></section>
  </div>;
}

function Model() {
  const chart = validationFolds.map((fold) => ({ cycle: fold.cycle, baseline: Number(fold.baselineMae.toFixed(2)), candidate: Number(fold.candidateMae.toFixed(2)) }));
  return <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">How the model is tested</p><h2>Beauty should never outrun evidence.</h2><p>The model only uses an added layer if it improves predictions on elections that were held back from training. The demographic version failed that test, so it has no influence on the central 2026 forecast.</p></div><Badge variant="outline">Demographic layer weight: 0%</Badge></section><section className="model-stack"><div className="model-stack-head"><div><p className="eyebrow">Forecast pipeline</p><h3>From source data to simulated parliaments</h3></div><p>Official VEC results provide the state-election anchor. Federal AEC patterns can add local context, but they are kept secondary and clearly labelled.</p></div><div className="model-layer-grid">{modelLayers.map((item, index) => <article key={item.layer}><span>{String(index + 1).padStart(2, "0")}</span><div><h4>{item.layer}</h4><strong>{item.status}</strong><p>{item.detail}</p></div></article>)}</div></section><section className="surface chart-surface"><div className="chart-heading"><div><h3>Did adding demographics improve past predictions?</h3><p>Average electorate error in percentage points · lower is better</p></div><div className="chart-summary"><strong>No</strong><span>the simpler baseline stays</span></div></div><div className="chart-frame"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d8d6cf" /><XAxis dataKey="cycle" tickLine={false} axisLine={false} /><YAxis domain={[0, 4]} tickLine={false} axisLine={false} tickFormatter={(v) => `${v} pp`} /><Tooltip formatter={(value, name) => [`${Number(value).toFixed(2)} points`, name === "baseline" ? "Simpler baseline" : "With demographics"]} /><Bar dataKey="baseline" fill="#173d64" /><Bar dataKey="candidate" fill="#dc6a32" /></BarChart></ResponsiveContainer></div><p className="chart-note">Across the held-back elections, the simpler baseline missed by {validationSummary.baselineMae.toFixed(2)} points on average versus {validationSummary.candidateMae.toFixed(2)} with the demographic layer. Wrong seat winners also rose from {validationSummary.baselineWinnerErrors} to {validationSummary.candidateWinnerErrors}.</p></section><section className="method-cards"><article><span>01</span><h3>Combine polls</h3><p>Give newer and better-sized polls more weight; account for recurring pollster lean.</p></article><article><span>02</span><h3>Build local starting points</h3><p>Anchor every electorate in official VEC results, then cautiously add local evidence.</p></article><article><span>03</span><h3>Distribute preferences</h3><p>Eliminate candidates until two remain; let transfers vary between simulations.</p></article><article><span>04</span><h3>Rerun the whole election</h3><p>Move statewide, regional, electorate and preference uncertainty together 5,000 times.</p></article></section><section className="integrity-strip"><ShieldCheck size={22} /><div><strong>Reproducible experimental forecast</strong><span>Seed {modelOutput.manifest.seed} · {number.format(modelOutput.manifest.simulations)} whole-election runs · 88 electorates · 8 regions · output fingerprints recorded</span></div><Badge>Experimental</Badge></section></div>;
}

function ReadingGuide() {
  return <details className="reading-guide">
    <summary><CircleHelp size={16} />How to read the forecast <span>Six terms explained</span></summary>
    <div className="guide-grid">
      <article><strong>Win chance</strong><p>How often a party won in the model’s 5,000 simulated elections—not its predicted vote share.</p></article>
      <article><strong>Likely range</strong><p>The middle 80% of simulated results. About one in five model runs falls outside it.</p></article>
      <article><strong>Middle result</strong><p>The median: half the simulations finish above it and half below it.</p></article>
      <article><strong>First preference</strong><p>The number 1 vote before preferences from eliminated candidates are distributed.</p></article>
      <article><strong>Final two</strong><p>The two candidates left after the preferential count eliminates the others.</p></article>
      <article><strong>Swing</strong><p>The change in a party’s two-party vote from one election to the next, measured in percentage points.</p></article>
    </div>
  </details>;
}

export function ElectionDashboard() {
  return <main className="site-shell"><header className="topbar"><div className="topbar-inner"><a href="#content" className="brand"><span className="brand-mark">V</span><span><strong>Victorian Election</strong><small>Forecasting laboratory · 2026</small></span></a><div className="status-cluster"><span className="status-dot" /><span>Experimental research forecast · updated 26 August</span></div></div></header><div className="content-shell" id="content"><section className="page-heading"><div><p className="eyebrow">The election, rendered honestly</p><h1>A forecast you can interrogate.</h1><p className="page-deck">See the headline, then open the evidence: polls, all 88 electorates, Upper House regions, historical swings and the tests the model passed—or failed.</p></div><div className="snapshot-stamp"><span>Forecast updated</span><strong>26 AUGUST 2026</strong><span>Model runs</span><strong>{number.format(modelOutput.manifest.simulations)} WHOLE ELECTIONS</strong></div></section><ReadingGuide /><Tabs defaultValue="forecast" className="dashboard-tabs"><div className="tabs-rail"><TabsList variant="line" className="dashboard-tabs-list"><TabsTrigger value="forecast"><Layers3 />Forecast</TabsTrigger><TabsTrigger value="polling"><Activity />Polls</TabsTrigger><TabsTrigger value="districts"><MapPinned />88 electorates</TabsTrigger><TabsTrigger value="council"><Landmark />Upper House</TabsTrigger><TabsTrigger value="history"><History />Swing history</TabsTrigger><TabsTrigger value="model"><Database />How it works</TabsTrigger></TabsList></div><TabsContent value="forecast"><Forecast /></TabsContent><TabsContent value="polling"><Polling /></TabsContent><TabsContent value="districts"><DistrictExplorer /></TabsContent><TabsContent value="council"><Council /></TabsContent><TabsContent value="history"><HistoricalExplorer /></TabsContent><TabsContent value="model"><Model /></TabsContent></Tabs></div><footer><div><strong>Victorian Election Forecasting Laboratory</strong><span>Independent · provisional · reproducible</span></div><p>Experimental research forecast, not voting advice. Inputs and assumptions are versioned; uncertainty is part of the result.</p></footer></main>;
}
