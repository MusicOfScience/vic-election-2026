"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownUp,
  ChevronRight,
  Database,
  Gauge,
  Landmark,
  Layers3,
  MapPinned,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { districts, validationFolds } from "./data.generated";
import {
  DEFAULT_ALP_TPP,
  greenSeatMargins,
  HISTORICAL_BASELINE_RMSE,
  modelLayers,
  MODEL_VINTAGE,
  pollingBenchmark,
  pollSeries,
  sources,
  upperHouseRegions,
  validationSummary,
} from "./forecast-data";

type ForecastParty = "Labor" | "Coalition" | "Greens";
type District = (typeof districts)[number];

const regions = [...new Set(districts.map((district) => district.region))].sort();
const number = new Intl.NumberFormat("en-AU");
const partyColour: Record<ForecastParty, string> = {
  Labor: "#d84a42",
  Coalition: "#2e63ad",
  Greens: "#159867",
};

const validationChart = validationFolds.map((fold) => ({
  cycle: fold.cycle,
  baseline: Number(fold.baselineMae.toFixed(2)),
  candidate: Number(fold.candidateMae.toFixed(2)),
}));

const benchmarkPartyRows = (halfLife: 21 | 45 | 90) => {
  const estimate = pollingBenchmark.estimates[halfLife];
  return [
    { party: "Coalition", value: estimate.coalition, key: "coalition" },
    { party: "Labor", value: estimate.alp, key: "alp" },
    { party: "One Nation", value: estimate.onp, key: "onp" },
    { party: "Greens", value: estimate.greens, key: "greens" },
    { party: "Other + independent", value: estimate.other, key: "other" },
  ];
};

function PollAverageBars({ halfLife = 45 }: { halfLife?: 21 | 45 | 90 }) {
  return <div className="aggregate-bars">{benchmarkPartyRows(halfLife).map((row) => <div key={row.party}><span>{row.party}</span><i><b className={row.key} style={{ width: `${row.value * 3}%` }} /></i><strong>{row.value.toFixed(1)}%</strong></div>)}</div>;
}

function Synthesis() {
  return <div className="tab-stack">
    <section className="synthesis-hero">
      <div className="synthesis-copy"><div className="forecast-kicker"><Badge>Evidence synthesis</Badge><span>Sealed checkpoint · 14 August 2026</span></div><p className="eyebrow">What the project actually contains</p><h2>Polls are one signal.<br />The model is the argument.</h2><p>A living research system joining polling, official results, redistributions, demographics, housing, preference evidence and historical tests. The first complex candidate failed—so the evidence is visible and the production gate remains closed.</p></div>
      <div className="synthesis-ledger" aria-label="Project evidence counts"><div><strong>9</strong><span>eligible polls</span></div><div><strong>4</strong><span>held-out elections</span></div><div><strong>340</strong><span>district transitions</span></div><div><strong>2,464</strong><span>demographic cells</span></div><div><strong>39/39</strong><span>preference files parsed</span></div><div><strong>88 + 8</strong><span>districts + regions</span></div></div>
    </section>
    <section className="synthesis-grid">
      <article className="surface aggregate-card"><div className="section-heading"><div><p className="eyebrow">Poll of polls · primary vote</p><h3>Nine polls, not one headline</h3></div><Badge variant="outline">45-day half-life</Badge></div><PollAverageBars /><p className="chart-note">Sample-size and recency weighted across nine complete, eligible multi-party polls. This transparent benchmark has no house-effect correction and is not yet the planned Bayesian latent-state model.</p></article>
      <article className="surface gate-card"><p className="eyebrow">Historical verdict</p><h3>The complex model did not earn promotion.</h3><div className="gate-metric"><strong>{validationSummary.baselineMae.toFixed(2)}</strong><span>baseline MAE</span><i>vs</i><strong>{validationSummary.candidateMae.toFixed(2)}</strong><span>demographic MAE</span></div><p>Winner errors worsened from {validationSummary.baselineWinnerErrors} to {validationSummary.candidateWinnerErrors}. That negative result is part of the product—not something to hide behind a simpler-looking forecast.</p><Badge>Production gate closed</Badge></article>
    </section>
    <section className="model-stack"><div className="model-stack-head"><div><p className="eyebrow">Six-layer evidence engine</p><h3>From source bytes to forecast release</h3></div><p>Each layer has its own provenance, eligibility rules and promotion gate. “Available” does not mean “authorised for prediction.”</p></div><div className="model-layer-grid">{modelLayers.map((item, index) => <article key={item.layer}><span>{String(index + 1).padStart(2, "0")}</span><div><h4>{item.layer}</h4><strong>{item.status}</strong><p>{item.detail}</p></div></article>)}</div></section>
    <section className="model-warning"><ShieldCheck size={20} aria-hidden="true" /><div><strong>Correct scientific status</strong><p>The site may show transparent polling aggregates, historical results and conditional scenarios. It must not present 2026 seat probabilities as an authorised production forecast until a candidate clears the preregistered gates.</p></div></section>
  </div>;
}

function PollingLab() {
  const [halfLife, setHalfLife] = useState<21 | 45 | 90>(45);
  return <div className="tab-stack">
    <section className="explorer-intro"><div><p className="eyebrow">Polling laboratory</p><h2>Every poll, every assumption.</h2><p>Explore the complete eligible 2026 polling series and test how recency changes the aggregate. Questionnaire breaks, leadership regimes, overlapping samples and incomplete tables remain explicit.</p></div><Select value={String(halfLife)} onValueChange={(value) => setHalfLife(Number(value) as 21 | 45 | 90)}><SelectTrigger className="filter-select" aria-label="Polling half-life"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="21">21-day half-life</SelectItem><SelectItem value="45">45-day half-life</SelectItem><SelectItem value="90">90-day half-life</SelectItem></SelectContent></Select></section>
    <section className="polling-layout">
      <article className="surface poll-card"><div className="section-heading"><div><p className="eyebrow">Eligible poll series</p><h3>Victoria’s fragmented primary vote</h3></div><Badge variant="outline">n = 1,034–5,516</Badge></div><div className="poll-series-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={pollSeries} margin={{ top: 14, right: 12, left: -18, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 9, fill: "#65707c" }} /><YAxis domain={[10, 34]} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#65707c" }} tickFormatter={(value) => `${value}%`} /><Tooltip labelFormatter={(_, payload) => payload?.[0]?.payload ? `${payload[0].payload.pollster} · n=${number.format(payload[0].payload.n)}` : ""} formatter={(value, name) => [`${Number(value).toFixed(1)}%`, String(name)]} /><Line type="monotone" dataKey="coalition" name="Coalition" stroke="#2e63ad" strokeWidth={2.4} dot={{ r: 3 }} /><Line type="monotone" dataKey="alp" name="Labor" stroke="#d84a42" strokeWidth={2.4} dot={{ r: 3 }} /><Line type="monotone" dataKey="onp" name="One Nation" stroke="#e4a22a" strokeWidth={2.4} dot={{ r: 3 }} /><Line type="monotone" dataKey="greens" name="Greens" stroke="#159867" strokeWidth={2.4} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div><p className="chart-note">Lines connect separate polls for visual orientation; they are not a fitted trend. The aggregate at right applies explicit weighting.</p></article>
      <article className="surface aggregate-card compact"><div className="section-heading"><div><p className="eyebrow">Weighted benchmark</p><h3>{halfLife}-day half-life</h3></div><strong className="poll-count">{pollingBenchmark.pollCount} polls</strong></div><PollAverageBars halfLife={halfLife} /><p className="chart-note">As at {pollingBenchmark.asOf}. Effective sample size is capped at 2,500; incomplete and ineligible polls are retained in the registry but excluded here.</p></article>
    </section>
    <section className="surface poll-register"><div className="section-heading"><div><p className="eyebrow">Canonical poll registry</p><h3>The observations behind the average</h3></div><Badge variant="outline">Complete eligible set</Badge></div><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>Fieldwork end</TableHead><TableHead>Pollster</TableHead><TableHead>Sample</TableHead><TableHead>ALP</TableHead><TableHead>Coalition</TableHead><TableHead>ONP</TableHead><TableHead>Greens</TableHead></TableRow></TableHeader><TableBody>{pollSeries.map((poll) => <TableRow key={`${poll.pollster}-${poll.date}`}><TableCell>{poll.date}</TableCell><TableCell className="district-name">{poll.pollster}</TableCell><TableCell>{number.format(poll.n)}</TableCell><TableCell>{poll.alp}%</TableCell><TableCell>{poll.coalition}%</TableCell><TableCell>{poll.onp}%</TableCell><TableCell>{poll.greens}%</TableCell></TableRow>)}</TableBody></Table></div></section>
  </div>;
}

function erf(value: number) {
  const sign = value < 0 ? -1 : 1;
  const x = Math.abs(value);
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x));
  return sign * y;
}

function normalCdf(value: number) {
  return 0.5 * (1 + erf(value / Math.sqrt(2)));
}

function poissonBinomial(probabilities: number[]) {
  const distribution = Array(probabilities.length + 1).fill(0);
  distribution[0] = 1;
  probabilities.forEach((probability, index) => {
    for (let seats = index + 1; seats >= 0; seats -= 1) {
      distribution[seats] =
        (distribution[seats] ?? 0) * (1 - probability) +
        (seats > 0 ? distribution[seats - 1] * probability : 0);
    }
  });
  return distribution;
}

function projectDistrict(district: District, alpTpp: number) {
  if (district.name in greenSeatMargins) {
    const greenShare = greenSeatMargins[district.name];
    return { ...district, forecastTpp: null, projectedParty: "Greens" as ForecastParty, winProbability: normalCdf((greenShare - 50) / HISTORICAL_BASELINE_RMSE), alpProbability: null, basis: `2022 GRN 2CP ${greenShare.toFixed(1)}%`, specialContest: true };
  }
  if (district.name === "Prahran") {
    return { ...district, forecastTpp: null, projectedParty: "Coalition" as ForecastParty, winProbability: normalCdf((51.35 - 50) / HISTORICAL_BASELINE_RMSE), alpProbability: null, basis: "2025 Liberal–Green by-election", specialContest: true };
  }
  if (district.name === "Narracan" || district.alpTpp2022 === null) {
    return { ...district, forecastTpp: null, projectedParty: "Coalition" as ForecastParty, winProbability: 0.97, alpProbability: null, basis: "2023 supplementary result", specialContest: true };
  }
  const forecastTpp = district.alpTpp2022 + (alpTpp - 55);
  const alpProbability = normalCdf((forecastTpp - 50) / HISTORICAL_BASELINE_RMSE);
  const projectedParty: ForecastParty = alpProbability >= 0.5 ? "Labor" : "Coalition";
  return { ...district, forecastTpp, projectedParty, winProbability: projectedParty === "Labor" ? alpProbability : 1 - alpProbability, alpProbability, basis: "Uniform swing benchmark", specialContest: false };
}

function getForecast(alpTpp: number) {
  const projected = districts.map((district) => projectDistrict(district, alpTpp));
  const probabilities = projected.filter((district) => !district.specialContest).map((district) => district.alpProbability ?? 0);
  const distribution = poissonBinomial(probabilities);
  const expectedLabor = probabilities.reduce((sum, probability) => sum + probability, 0);
  const laborMajority = distribution.slice(45).reduce((sum, probability) => sum + probability, 0);
  const coalitionMajority = distribution.slice(0, 41).reduce((sum, probability) => sum + probability, 0);
  const hung = distribution.slice(41, 45).reduce((sum, probability) => sum + probability, 0);
  const seatDistribution = distribution.map((probability, seats) => ({ seats, probability: probability * 100 })).filter((row) => row.seats >= 25 && row.seats <= 58 && row.probability > 0.04);
  return { projected, expectedLabor, expectedCoalition: 85 - expectedLabor, laborMajority, coalitionMajority, hung, seatDistribution };
}

function OutcomeProbability({ label, probability, active }: { label: string; probability: number; active: boolean }) {
  return <div className={`outcome-probability ${active ? "active" : ""}`}><span>{label}</span><strong>{Math.round(probability * 100)}%</strong><i aria-hidden="true"><b style={{ width: `${probability * 100}%` }} /></i></div>;
}

function SeatArc({ forecast }: { forecast: ReturnType<typeof getForecast> }) {
  const seats = [...forecast.projected].sort((a, b) => {
    const partyOrder = { Coalition: 0, Greens: 1, Labor: 2 };
    return partyOrder[a.projectedParty] - partyOrder[b.projectedParty] || a.winProbability - b.winProbability;
  });
  const rows = [18, 16, 14, 12, 10, 8, 6, 4];
  const points: { x: number; y: number; seat: (typeof seats)[number] }[] = [];
  let cursor = 0;
  rows.forEach((count, rowIndex) => {
    const radius = 76 + rowIndex * 23;
    for (let index = 0; index < count; index += 1) {
      const angle = Math.PI + (Math.PI * index) / Math.max(1, count - 1);
      points.push({ x: 260 + Math.cos(angle) * radius, y: 250 + Math.sin(angle) * radius, seat: seats[cursor] });
      cursor += 1;
    }
  });
  return <svg className="seat-arc" viewBox="0 0 520 280" role="img" aria-label="Projected 88-seat Legislative Assembly"><line x1="260" y1="248" x2="260" y2="265" className="majority-line" />{points.map(({ x, y, seat }) => <circle key={seat.id} cx={x} cy={y} r="7.3" fill={partyColour[seat.projectedParty]} opacity={0.5 + seat.winProbability * 0.5}><title>{seat.name}: {seat.projectedParty} {Math.round(seat.winProbability * 100)}%</title></circle>)}</svg>;
}

function ForecastOverview({ alpTpp, setAlpTpp }: { alpTpp: number; setAlpTpp: (value: number) => void }) {
  const forecast = useMemo(() => getForecast(alpTpp), [alpTpp]);
  const outcomes = [["Labor majority", forecast.laborMajority], ["Hung parliament", forecast.hung], ["Coalition majority", forecast.coalitionMajority]] as const;
  const leadingOutcome = [...outcomes].sort((a, b) => b[1] - a[1])[0][0];
  const scenarioChanged = Math.abs(alpTpp - DEFAULT_ALP_TPP) > 0.01;
  return (
    <div className="tab-stack forecast-stack">
      <section className="forecast-hero" aria-labelledby="forecast-title">
        <div className="forecast-copy"><div className="forecast-kicker"><Badge>Conditional scenario</Badge><span>User-set ALP {alpTpp.toFixed(1)}% 2PP assumption</span></div><p className="eyebrow">Legislative Assembly · baseline laboratory</p><h2 id="forecast-title">{leadingOutcome}</h2><p className="forecast-deck">This is the model’s transparent uniform-swing comparator: useful for exploring the chamber, but deliberately separate from the poll-of-polls and not an authorised 2026 forecast.</p><div className="seat-totals" aria-label="Illustrative expected seats"><div className="labor"><span>Labor</span><strong>{Math.round(forecast.expectedLabor)}</strong><small>illustrative expected seats</small></div><div className="coalition"><span>Coalition</span><strong>{Math.round(forecast.expectedCoalition)}</strong><small>illustrative expected seats</small></div><div className="greens"><span>Greens</span><strong>3</strong><small>held constant</small></div></div></div>
        <div className="parliament-card"><SeatArc forecast={forecast} /><div className="arc-caption"><span>88 seats</span><strong>45 for a majority</strong><span>Each dot is a district</span></div></div>
      </section>
      <section className="outcome-strip" aria-label="Illustrative conditional government outcome references">{outcomes.map(([label, probability]) => <OutcomeProbability key={label} label={label} probability={probability} active={label === leadingOutcome} />)}</section>
      <section className="scenario-studio"><div className="studio-copy"><p className="eyebrow">Scenario studio</p><h3>Move an assumption. Watch Victoria move.</h3><p>Set a hypothetical Labor statewide two-party vote. The baseline applies that swing to the 2022 district surface. The poll-of-polls estimates primary votes and does not authorise this 2PP conversion.</p></div><div className="slider-console"><div className="slider-value"><span>Coalition {(100 - alpTpp).toFixed(1)}</span><strong>{alpTpp.toFixed(1)}% ALP 2PP</strong><span>Labor {alpTpp.toFixed(1)}</span></div><Slider min={44} max={56} step={0.1} value={[alpTpp]} onValueChange={(value) => setAlpTpp(value[0] ?? DEFAULT_ALP_TPP)} aria-label="Assumed Labor statewide two-party-preferred vote" /><div className="slider-scale"><span>44%</span><span>49% starting scenario</span><span>50%</span><span>56%</span></div>{scenarioChanged && <button className="reset-scenario" onClick={() => setAlpTpp(DEFAULT_ALP_TPP)}>Return to the 49% starting scenario</button>}</div></section>
      <section className="forecast-grid">
        <article className="surface distribution-card"><div className="section-heading"><div><p className="eyebrow">Diagnostic only</p><h3>Illustrative seat-count envelope</h3></div><Badge variant="outline">Unauthorised error reference</Badge></div><div className="distribution-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={forecast.seatDistribution} margin={{ top: 8, right: 2, left: -27, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="seats" tickLine={false} axisLine={false} tick={{ fill: "#65707c", fontSize: 10 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#65707c", fontSize: 10 }} tickFormatter={(value) => `${value}%`} /><ReferenceLine x={45} stroke="#e8773f" strokeDasharray="4 3" label={{ value: "majority", fill: "#8e4a2c", fontSize: 9, position: "insideTopRight" }} /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, "Illustrative weight"]} labelFormatter={(value) => `${value} Labor seats`} contentStyle={{ border: "1px solid #c8cbc8", borderRadius: 3, boxShadow: "0 12px 30px rgba(9,25,40,.12)" }} /><Bar dataKey="probability" radius={[2, 2, 0, 0]}>{forecast.seatDistribution.map((row) => <Cell key={row.seats} fill={row.seats >= 45 ? "#d84a42" : row.seats >= 41 ? "#b5906f" : "#2e63ad"} />)}</Bar></BarChart></ResponsiveContainer></div><p className="chart-note">This display reuses the 3.69-point historical baseline RMSE for exploration. The sealed checkpoint explicitly says the forecast-error distribution is not authorised.</p></article>
        <article className="surface signal-card"><p className="eyebrow">Why this is close</p><h3>The vote and the chamber tell different stories.</h3><div className="signal-number"><strong>{(100 - alpTpp).toFixed(1)}–{alpTpp.toFixed(1)}</strong><span>Coalition–Labor statewide 2PP</span></div><div className="signal-rule" /><p>Labor’s large 2022 majority was built on a 55% statewide vote. A six-point swing removes its cushion but does not translate evenly into seats.</p><a href={sources.lowerHousePoll} target="_blank" rel="noreferrer">Read the poll source <ChevronRight size={14} /></a></article>
      </section>
      <section className="model-warning"><AlertTriangle size={20} aria-hidden="true" /><div><strong>This tab is a comparator, not the project forecast.</strong><p>It does not yet model candidate quality, three-way eliminations, local One Nation effects or an approved preference conversion. Use Polling for the aggregate evidence and Validation for the model gates.</p></div></section>
    </div>
  );
}

function DistrictExplorer({ alpTpp }: { alpTpp: number }) {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("all");
  const [party, setParty] = useState("all");
  const [sort, setSort] = useState("marginal");
  const forecast = useMemo(() => getForecast(alpTpp), [alpTpp]);
  const filtered = useMemo(() => {
    const normalisedQuery = query.trim().toLowerCase();
    const selected = forecast.projected.filter((district) => (region === "all" || district.region === region) && (party === "all" || district.projectedParty === party) && (!normalisedQuery || district.name.toLowerCase().includes(normalisedQuery)));
    return [...selected].sort((a, b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "enrolment" ? (b.enrolment ?? 0) - (a.enrolment ?? 0) : a.winProbability - b.winProbability);
  }, [forecast.projected, party, query, region, sort]);
  return (
    <div className="tab-stack">
      <section className="explorer-intro"><div><p className="eyebrow">Every district, one landscape</p><h2>The scenario frontier</h2><p>Conditional edge, historical-reference uncertainty, region and enrolment for all 88 Assembly districts. This view responds to the 2PP assumption selected in Scenario.</p></div><Badge variant="outline" className="reference-badge">Conditional · ALP {alpTpp.toFixed(1)}% 2PP</Badge></section>
      <section className="surface seat-landscape" aria-label="District scenario matrix"><div className="landscape-key"><span><i className="labor" />Labor</span><span><i className="coalition" />Coalition</span><span><i className="greens" />Greens</span><span className="faded">Paler = weaker scenario edge</span></div><div className="seat-matrix">{[...forecast.projected].sort((a, b) => a.winProbability - b.winProbability).map((district) => <button key={district.id} className={`seat-tile ${district.projectedParty.toLowerCase()}`} style={{ opacity: 0.46 + district.winProbability * 0.54 }} title={`${district.name} · ${district.projectedParty} · ${district.basis}`}><span>{district.name}</span><strong>{Math.round(district.winProbability * 100)}</strong></button>)}</div></section>
      <div className="filter-bar"><label className="search-field"><span className="sr-only">Search districts</span><Search size={17} /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a district…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" /></label><Select value={region} onValueChange={(value) => setRegion(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by region"><SelectValue placeholder="All regions" /></SelectTrigger><SelectContent><SelectItem value="all">All regions</SelectItem>{regions.map((item) => <SelectItem value={item} key={item}>{item}</SelectItem>)}</SelectContent></Select><Select value={party} onValueChange={(value) => setParty(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by projected party"><SelectValue placeholder="All parties" /></SelectTrigger><SelectContent><SelectItem value="all">All projected parties</SelectItem><SelectItem value="Labor">Labor</SelectItem><SelectItem value="Coalition">Coalition</SelectItem><SelectItem value="Greens">Greens</SelectItem></SelectContent></Select><Select value={sort} onValueChange={(value) => setSort(value ?? "marginal")}><SelectTrigger className="filter-select" aria-label="Sort districts"><ArrowDownUp size={15} /><SelectValue /></SelectTrigger><SelectContent><SelectItem value="marginal">Most uncertain</SelectItem><SelectItem value="name">District name</SelectItem><SelectItem value="enrolment">Largest enrolment</SelectItem></SelectContent></Select></div>
      <div className="result-count" aria-live="polite">{filtered.length} {filtered.length === 1 ? "district" : "districts"}</div>
      <section className="surface district-table-wrap"><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>District</TableHead><TableHead>Region</TableHead><TableHead>Scenario leader</TableHead><TableHead>Reference edge</TableHead><TableHead>Scenario ALP 2PP</TableHead></TableRow></TableHeader><TableBody>{filtered.map((district) => <TableRow key={district.id}><TableCell className="district-name">{district.name}</TableCell><TableCell className="region-name">{district.region}</TableCell><TableCell><span className={`party-chip ${district.projectedParty.toLowerCase()}`}>{district.projectedParty}</span></TableCell><TableCell><strong>{Math.round(district.winProbability * 100)}%</strong></TableCell><TableCell>{district.forecastTpp === null ? <span className="muted">Separate contest</span> : `${district.forecastTpp.toFixed(1)}%`}</TableCell></TableRow>)}</TableBody></Table></div><div className="mobile-districts">{filtered.map((district) => <article className="district-card" key={district.id}><div><h3>{district.name}</h3><p>{district.region}</p></div><dl><div><dt>Scenario leader</dt><dd><span className={`party-chip ${district.projectedParty.toLowerCase()}`}>{district.projectedParty}</span></dd></div><div><dt>Reference edge</dt><dd>{Math.round(district.winProbability * 100)}%</dd></div><div><dt>Scenario ALP 2PP</dt><dd>{district.forecastTpp === null ? "Separate contest" : `${district.forecastTpp.toFixed(1)}%`}</dd></div><div><dt>Enrolment</dt><dd>{district.enrolment === null ? "—" : number.format(district.enrolment)}</dd></div></dl></article>)}</div></section>
      <p className="data-note">The percentage edge uses an unauthorised historical error reference and is diagnostic only. Prahran, Narracan and the three Greens-held seats use separate holdover benchmarks.</p>
    </div>
  );
}

function UpperHouse() {
  const totals = [["Coalition", 11, "coalition"], ["One Nation", 10, "onp"], ["Labor", 9, "labor"], ["Greens", 2, "greens"], ["Other", 1, "other"], ["Unresolved", 7, "undecided"]] as const;
  return (
    <div className="tab-stack"><section className="council-hero"><div><p className="eyebrow">Legislative Council · external benchmark</p><h2>The fractured forty</h2><p>The project has a five-member STV/PR engine and eight-region validation targets, but no authorised 2026 Council forecast. This panel therefore preserves Roy Morgan as one dated external benchmark—never as the whole model.</p></div><a href={sources.upperHousePoll} target="_blank" rel="noreferrer">Open external benchmark <ChevronRight size={15} /></a></section><section className="surface council-total"><div className="forty-grid" aria-label="Roy Morgan external benchmark for the 40-seat Legislative Council">{totals.flatMap(([party, count, key]) => Array.from({ length: count }, (_, index) => <span key={`${party}-${index}`} className={key} title={party} />))}</div><div className="council-legend">{totals.map(([party, count, key]) => <div key={party}><i className={key} /><strong>{count}</strong><span>{party}</span></div>)}</div></section><section className="region-grid">{upperHouseRegions.map((region) => { const seatRows = [["ALP", region.alp, "labor"], ["L–NP", region.coalition, "coalition"], ["ONP", region.onp, "onp"], ["GRN", region.greens, "greens"], ["Other", region.other, "other"], ["Open", region.undecided, "undecided"]] as const; return <article className="surface region-card" key={region.region}><div className="region-card-head"><h3>{region.region}</h3><span>5 seats</span></div><div className="region-seat-row">{seatRows.flatMap(([label, count, key]) => Array.from({ length: count }, (_, index) => <i className={key} title={label} key={`${label}-${index}`} />))}</div><div className="region-votes"><span><b>{region.alpVote}%</b> ALP</span><span><b>{region.coalitionVote}%</b> L–NP</span><span><b>{region.onpVote}%</b> ONP</span><span><b>{region.greensVote}%</b> GRN</span></div></article>; })}</section><p className="data-note">Roy Morgan interviews, 5–7 August 2026. “Open” denotes seven seats left unresolved by that source. The panel is isolated from the project model to prevent circular forecasting.</p></div>
  );
}

function Evidence() {
  return (
    <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">Historical validation</p><h2>Make every candidate earn its place.</h2><p>Four whole-election holdouts test whether structure improves on uniform swing. The first preregistered demographic candidate failed; that result blocks downstream probabilities rather than being quietly tuned away.</p></div><Badge variant="outline">340 held-out transitions</Badge></section><section className="surface chart-surface"><div className="chart-heading"><div><h3>Did demographics improve prediction?</h3><p>Mean absolute error · percentage points · lower is better</p></div><div className="chart-summary"><strong>Failed</strong><span>promotion gate</span></div></div><div className="chart-frame"><ResponsiveContainer width="100%" height="100%"><BarChart data={validationChart} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d8d6cf" /><XAxis dataKey="cycle" tickLine={false} axisLine={false} tick={{ fill: "#42454b", fontSize: 12 }} /><YAxis domain={[0, 4]} tickLine={false} axisLine={false} tick={{ fill: "#6d7076", fontSize: 11 }} tickFormatter={(value) => `${value} pp`} /><Tooltip formatter={(value, name) => [`${Number(value).toFixed(2)} pp`, name === "baseline" ? "Uniform-swing baseline" : "Demographic candidate"]} /><Bar dataKey="baseline" fill="#173d64" radius={[2, 2, 0, 0]} /><Bar dataKey="candidate" fill="#dc6a32" radius={[2, 2, 0, 0]} /></BarChart></ResponsiveContainer></div><p className="chart-note">Pooled MAE: {validationSummary.baselineMae.toFixed(2)} baseline vs {validationSummary.candidateMae.toFixed(2)} candidate. RMSE: {validationSummary.baselineRmse.toFixed(2)} vs {validationSummary.candidateRmse.toFixed(2)}. Winner errors: {validationSummary.baselineWinnerErrors} vs {validationSummary.candidateWinnerErrors}.</p></section><section className="method-cards"><article><span>01</span><h3>Four cycles</h3><p>2002→2006, 2010→2014, 2014→2018 and redistribution-adjusted 2018→2022.</p></article><article><span>02</span><h3>Seven features</h3><p>Mortgage, rent, outright ownership, housing structure and two age bands—frozen before testing.</p></article><article><span>03</span><h3>Outcome-blind build</h3><p>Official Census surfaces are aligned to historical boundaries without using the election result.</p></article><article><span>04</span><h3>Fail closed</h3><p>No production forecast or error distribution is authorised when the candidate misses its gates.</p></article></section><section className="integrity-strip"><ShieldCheck size={22} /><div><strong>Sealed evidence state reproduced</strong><span>409/409 baseline tests before final held-out run · 4/4 surfaces · 4/4 outcomes · 31/31 provenance records</span></div><Badge>14 Aug · 14:55 AEST</Badge></section></div>
  );
}

export function ElectionDashboard() {
  const [alpTpp, setAlpTpp] = useState(DEFAULT_ALP_TPP);
  return <main className="site-shell"><header className="topbar"><div className="topbar-inner"><a href="#content" className="brand" aria-label="Victorian Election Forecast home"><span className="brand-mark" aria-hidden="true">V</span><span><strong>Victorian Election</strong><small>Forecasting laboratory · 2026</small></span></a><div className="status-cluster"><span className="status-dot amber" /><span>Research model · gate closed</span></div></div></header><div className="content-shell" id="content"><section className="page-heading"><div><p className="eyebrow">The election, rendered honestly</p><h1>A living model, not a single number.</h1><p className="page-deck">Poll aggregation, official results, boundary history, demographics, preferences and model validation—kept separate enough to audit, joined carefully enough to learn.</p></div><div className="snapshot-stamp"><span>Site vintage</span><strong>{MODEL_VINTAGE.toUpperCase()}</strong><span>Polling benchmark</span><strong>{pollingBenchmark.pollCount} ELIGIBLE POLLS</strong></div></section><Tabs defaultValue="synthesis" className="dashboard-tabs"><div className="tabs-rail"><TabsList variant="line" className="dashboard-tabs-list" aria-label="Dashboard sections"><TabsTrigger value="synthesis"><Layers3 />Synthesis</TabsTrigger><TabsTrigger value="polling"><Activity />Polling</TabsTrigger><TabsTrigger value="scenario"><Gauge />Scenario</TabsTrigger><TabsTrigger value="districts"><MapPinned />88 districts</TabsTrigger><TabsTrigger value="council"><Landmark />Upper house</TabsTrigger><TabsTrigger value="evidence"><Database />Validation</TabsTrigger></TabsList></div><TabsContent value="synthesis"><Synthesis /></TabsContent><TabsContent value="polling"><PollingLab /></TabsContent><TabsContent value="scenario"><ForecastOverview alpTpp={alpTpp} setAlpTpp={setAlpTpp} /></TabsContent><TabsContent value="districts"><DistrictExplorer alpTpp={alpTpp} /></TabsContent><TabsContent value="council"><UpperHouse /></TabsContent><TabsContent value="evidence"><Evidence /></TabsContent></Tabs></div><footer><div><strong>Victorian Election Forecasting Laboratory</strong><span>Independent · provisional · reproducible</span></div><p>Research dashboard, not voting advice. Poll aggregates are transparent benchmarks; production forecast and error-distribution gates remain closed.</p></footer></main>;
}
