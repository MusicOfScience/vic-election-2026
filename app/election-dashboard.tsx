"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownUp,
  BookOpen,
  ChevronRight,
  Gauge,
  Landmark,
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
  latestPrimary,
  MODEL_VINTAGE,
  POLL_ANCHOR_DATE,
  pollTrend,
  sources,
  upperHouseRegions,
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
        <div className="forecast-copy"><div className="forecast-kicker"><Badge>Experimental benchmark</Badge><span>Conditional on ALP {alpTpp.toFixed(1)}% 2PP</span></div><p className="eyebrow">Legislative Assembly · nowcast</p><h2 id="forecast-title">{leadingOutcome}</h2><p className="forecast-deck">The map remains astonishingly close: a one-point statewide Coalition lead still leaves the lower house balanced on a handful of suburban seats.</p><div className="seat-totals" aria-label="Expected seats"><div className="labor"><span>Labor</span><strong>{Math.round(forecast.expectedLabor)}</strong><small>expected seats</small></div><div className="coalition"><span>Coalition</span><strong>{Math.round(forecast.expectedCoalition)}</strong><small>expected seats</small></div><div className="greens"><span>Greens</span><strong>3</strong><small>held constant</small></div></div></div>
        <div className="parliament-card"><SeatArc forecast={forecast} /><div className="arc-caption"><span>88 seats</span><strong>45 for a majority</strong><span>Each dot is a district</span></div></div>
      </section>
      <section className="outcome-strip" aria-label="Government outcome probabilities">{outcomes.map(([label, probability]) => <OutcomeProbability key={label} label={label} probability={probability} active={label === leadingOutcome} />)}</section>
      <section className="scenario-studio"><div className="studio-copy"><p className="eyebrow">Scenario studio</p><h3>Move the vote. Watch Victoria move.</h3><p>Set Labor’s statewide two-party vote. The seat model applies that swing to the 2022 district surface and recalculates all 83 major-party contests.</p></div><div className="slider-console"><div className="slider-value"><span>Coalition {(100 - alpTpp).toFixed(1)}</span><strong>{alpTpp.toFixed(1)}% ALP 2PP</strong><span>Labor {alpTpp.toFixed(1)}</span></div><Slider min={44} max={56} step={0.1} value={[alpTpp]} onValueChange={(value) => setAlpTpp(value[0] ?? DEFAULT_ALP_TPP)} aria-label="Labor statewide two-party-preferred vote" /><div className="slider-scale"><span>44%</span><span>49% poll</span><span>50%</span><span>56%</span></div>{scenarioChanged && <button className="reset-scenario" onClick={() => setAlpTpp(DEFAULT_ALP_TPP)}>Return to the 49% poll anchor</button>}</div></section>
      <section className="forecast-grid">
        <article className="surface distribution-card"><div className="section-heading"><div><p className="eyebrow">Uncertainty, not decoration</p><h3>Where Labor’s seat count could land</h3></div><Badge variant="outline">Historical error envelope</Badge></div><div className="distribution-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={forecast.seatDistribution} margin={{ top: 8, right: 2, left: -27, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="seats" tickLine={false} axisLine={false} tick={{ fill: "#65707c", fontSize: 10 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#65707c", fontSize: 10 }} tickFormatter={(value) => `${value}%`} /><ReferenceLine x={45} stroke="#e8773f" strokeDasharray="4 3" label={{ value: "majority", fill: "#8e4a2c", fontSize: 9, position: "insideTopRight" }} /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, "Chance"]} labelFormatter={(value) => `${value} Labor seats`} contentStyle={{ border: "1px solid #c8cbc8", borderRadius: 3, boxShadow: "0 12px 30px rgba(9,25,40,.12)" }} /><Bar dataKey="probability" radius={[2, 2, 0, 0]}>{forecast.seatDistribution.map((row) => <Cell key={row.seats} fill={row.seats >= 45 ? "#d84a42" : row.seats >= 41 ? "#b5906f" : "#2e63ad"} />)}</Bar></BarChart></ResponsiveContainer></div><p className="chart-note">Conditional distribution: the statewide poll anchor is held fixed; district errors use the 3.69-point historical baseline RMSE.</p></article>
        <article className="surface signal-card"><p className="eyebrow">Why this is close</p><h3>The vote and the chamber tell different stories.</h3><div className="signal-number"><strong>{(100 - alpTpp).toFixed(1)}–{alpTpp.toFixed(1)}</strong><span>Coalition–Labor statewide 2PP</span></div><div className="signal-rule" /><p>Labor’s large 2022 majority was built on a 55% statewide vote. A six-point swing removes its cushion but does not translate evenly into seats.</p><a href={sources.lowerHousePoll} target="_blank" rel="noreferrer">Read the poll source <ChevronRight size={14} /></a></article>
      </section>
      <section className="model-warning"><AlertTriangle size={20} aria-hidden="true" /><div><strong>This is a deliberately limited forecast.</strong><p>It is a transparent uniform-swing benchmark, not the failed demographic candidate and not an authorised production model. It does not yet model candidate quality, three-way eliminations or local One Nation effects.</p></div></section>
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
      <section className="explorer-intro"><div><p className="eyebrow">Every district, one landscape</p><h2>The seat frontier</h2><p>Forecast edge, uncertainty, region and enrolment for all 88 Assembly districts. Hover or tap a tile; filter the table below.</p></div><Badge variant="outline" className="reference-badge">Scenario · ALP {alpTpp.toFixed(1)}% 2PP</Badge></section>
      <section className="surface seat-landscape" aria-label="District forecast matrix"><div className="landscape-key"><span><i className="labor" />Labor</span><span><i className="coalition" />Coalition</span><span><i className="greens" />Greens</span><span className="faded">Paler = less certain</span></div><div className="seat-matrix">{[...forecast.projected].sort((a, b) => a.winProbability - b.winProbability).map((district) => <button key={district.id} className={`seat-tile ${district.projectedParty.toLowerCase()}`} style={{ opacity: 0.46 + district.winProbability * 0.54 }} title={`${district.name} · ${district.projectedParty} ${Math.round(district.winProbability * 100)}% · ${district.basis}`}><span>{district.name}</span><strong>{Math.round(district.winProbability * 100)}</strong></button>)}</div></section>
      <div className="filter-bar"><label className="search-field"><span className="sr-only">Search districts</span><Search size={17} /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a district…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" /></label><Select value={region} onValueChange={(value) => setRegion(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by region"><SelectValue placeholder="All regions" /></SelectTrigger><SelectContent><SelectItem value="all">All regions</SelectItem>{regions.map((item) => <SelectItem value={item} key={item}>{item}</SelectItem>)}</SelectContent></Select><Select value={party} onValueChange={(value) => setParty(value ?? "all")}><SelectTrigger className="filter-select" aria-label="Filter by projected party"><SelectValue placeholder="All parties" /></SelectTrigger><SelectContent><SelectItem value="all">All projected parties</SelectItem><SelectItem value="Labor">Labor</SelectItem><SelectItem value="Coalition">Coalition</SelectItem><SelectItem value="Greens">Greens</SelectItem></SelectContent></Select><Select value={sort} onValueChange={(value) => setSort(value ?? "marginal")}><SelectTrigger className="filter-select" aria-label="Sort districts"><ArrowDownUp size={15} /><SelectValue /></SelectTrigger><SelectContent><SelectItem value="marginal">Most uncertain</SelectItem><SelectItem value="name">District name</SelectItem><SelectItem value="enrolment">Largest enrolment</SelectItem></SelectContent></Select></div>
      <div className="result-count" aria-live="polite">{filtered.length} {filtered.length === 1 ? "district" : "districts"}</div>
      <section className="surface district-table-wrap"><div className="desktop-table"><Table><TableHeader><TableRow><TableHead>District</TableHead><TableHead>Region</TableHead><TableHead>Forecast</TableHead><TableHead>Win chance</TableHead><TableHead>ALP 2PP</TableHead></TableRow></TableHeader><TableBody>{filtered.map((district) => <TableRow key={district.id}><TableCell className="district-name">{district.name}</TableCell><TableCell className="region-name">{district.region}</TableCell><TableCell><span className={`party-chip ${district.projectedParty.toLowerCase()}`}>{district.projectedParty}</span></TableCell><TableCell><strong>{Math.round(district.winProbability * 100)}%</strong></TableCell><TableCell>{district.forecastTpp === null ? <span className="muted">Separate contest</span> : `${district.forecastTpp.toFixed(1)}%`}</TableCell></TableRow>)}</TableBody></Table></div><div className="mobile-districts">{filtered.map((district) => <article className="district-card" key={district.id}><div><h3>{district.name}</h3><p>{district.region}</p></div><dl><div><dt>Forecast</dt><dd><span className={`party-chip ${district.projectedParty.toLowerCase()}`}>{district.projectedParty}</span></dd></div><div><dt>Win chance</dt><dd>{Math.round(district.winProbability * 100)}%</dd></div><div><dt>ALP 2PP</dt><dd>{district.forecastTpp === null ? "Separate contest" : `${district.forecastTpp.toFixed(1)}%`}</dd></div><div><dt>Enrolment</dt><dd>{district.enrolment === null ? "—" : number.format(district.enrolment)}</dd></div></dl></article>)}</div></section>
      <p className="data-note">Probabilities are conditional on the selected statewide scenario. Prahran, Narracan and the three Greens-held seats use separate holdover benchmarks and are not included in the two-party swing engine.</p>
    </div>
  );
}

function UpperHouse() {
  const totals = [["Coalition", 11, "coalition"], ["One Nation", 10, "onp"], ["Labor", 9, "labor"], ["Greens", 2, "greens"], ["Other", 1, "other"], ["Unresolved", 7, "undecided"]] as const;
  return (
    <div className="tab-stack"><section className="council-hero"><div><p className="eyebrow">Legislative Council · poll-based projection</p><h2>The fractured forty</h2><p>Reform has abolished group voting tickets. Roy Morgan’s region poll points to a chamber where Coalition and One Nation together secure at least 21 of 40 seats, with seven final seats unresolved.</p></div><a href={sources.upperHousePoll} target="_blank" rel="noreferrer">Roy Morgan region analysis <ChevronRight size={15} /></a></section><section className="surface council-total"><div className="forty-grid" aria-label="Projected 40-seat Legislative Council">{totals.flatMap(([party, count, key]) => Array.from({ length: count }, (_, index) => <span key={`${party}-${index}`} className={key} title={party} />))}</div><div className="council-legend">{totals.map(([party, count, key]) => <div key={party}><i className={key} /><strong>{count}</strong><span>{party}</span></div>)}</div></section><section className="region-grid">{upperHouseRegions.map((region) => { const seatRows = [["ALP", region.alp, "labor"], ["L–NP", region.coalition, "coalition"], ["ONP", region.onp, "onp"], ["GRN", region.greens, "greens"], ["Other", region.other, "other"], ["Open", region.undecided, "undecided"]] as const; return <article className="surface region-card" key={region.region}><div className="region-card-head"><h3>{region.region}</h3><span>5 seats</span></div><div className="region-seat-row">{seatRows.flatMap(([label, count, key]) => Array.from({ length: count }, (_, index) => <i className={key} title={label} key={`${label}-${index}`} />))}</div><div className="region-votes"><span><b>{region.alpVote}%</b> ALP</span><span><b>{region.coalitionVote}%</b> L–NP</span><span><b>{region.onpVote}%</b> ONP</span><span><b>{region.greensVote}%</b> GRN</span></div></article>; })}</section><p className="data-note">These are Roy Morgan’s minimum/projected regional seat allocations from interviews conducted 5–7 August 2026, not outputs of the lower-house swing benchmark. “Open” denotes the seven seats the poll source leaves undecided.</p></div>
  );
}

function Evidence() {
  return (
    <div className="tab-stack"><section className="explorer-intro"><div><p className="eyebrow">Signals, tests and limits</p><h2>Show the workings</h2><p>The forecast headline is only the final layer. Here are the polling signal, the failed demographic test and the exact rule used to turn vote into seats.</p></div><Badge variant="outline">Reproducible · inspectable</Badge></section><section className="evidence-grid"><article className="surface poll-card"><div className="section-heading"><div><p className="eyebrow">Roy Morgan forced choice</p><h3>Labor–Coalition 2PP trend</h3></div><strong className="latest-signal">49–51</strong></div><div className="poll-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={pollTrend} margin={{ top: 15, right: 8, left: -20, bottom: 0 }}><CartesianGrid vertical={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#65707c" }} /><YAxis domain={[45, 55]} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#65707c" }} tickFormatter={(value) => `${value}%`} /><ReferenceLine y={50} stroke="#8b9198" strokeDasharray="3 3" /><Tooltip formatter={(value, name) => [`${value}%`, name === "alp" ? "Labor" : "Coalition"]} /><Line type="monotone" dataKey="alp" stroke="#d84a42" strokeWidth={3} dot={{ r: 4, fill: "#d84a42" }} /><Line type="monotone" dataKey="coalition" stroke="#2e63ad" strokeWidth={3} dot={{ r: 4, fill: "#2e63ad" }} /></LineChart></ResponsiveContainer></div><p className="chart-note">February, April and August 2026 Roy Morgan pairwise forced-choice results. The latest fieldwork followed the change to Premier Ben Carroll.</p></article><article className="surface primary-card"><p className="eyebrow">Latest first preferences</p><h3>A three-pole election</h3><div className="primary-list">{latestPrimary.map((row) => <div key={row.party}><span>{row.party}</span><i><b className={row.key} style={{ width: `${row.value * 2.9}%` }} /></i><strong>{row.value}%</strong></div>)}</div><p>The benchmark compresses this unusually fragmented field into a two-party contest. That is its most important limitation.</p></article></section><section className="surface chart-surface"><div className="chart-heading"><div><h3>Did demographics improve prediction?</h3><p>Mean absolute error · percentage points · lower is better</p></div><div className="chart-summary"><strong>Failed</strong><span>promotion gate</span></div></div><div className="chart-frame"><ResponsiveContainer width="100%" height="100%"><BarChart data={validationChart} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d8d6cf" /><XAxis dataKey="cycle" tickLine={false} axisLine={false} tick={{ fill: "#42454b", fontSize: 12 }} /><YAxis domain={[0, 4]} tickLine={false} axisLine={false} tick={{ fill: "#6d7076", fontSize: 11 }} tickFormatter={(value) => `${value} pp`} /><Tooltip formatter={(value, name) => [`${Number(value).toFixed(2)} pp`, name === "baseline" ? "Uniform-swing baseline" : "Demographic candidate"]} /><Bar dataKey="baseline" fill="#173d64" radius={[2, 2, 0, 0]} /><Bar dataKey="candidate" fill="#dc6a32" radius={[2, 2, 0, 0]} /></BarChart></ResponsiveContainer></div><p className="chart-note">Across four whole-election holdouts, the candidate’s pooled MAE was 2.81 points versus 2.78 for the simple baseline; winner errors rose from 21 to 24.</p></section><section className="method-cards"><article><span>01</span><h3>Anchor</h3><p>Start at the latest verified Labor–Coalition 2PP poll: 49–51.</p></article><article><span>02</span><h3>Swing</h3><p>Subtract six points from each district’s official 2022 ALP 2PP.</p></article><article><span>03</span><h3>Uncertainty</h3><p>Translate the margin through the baseline’s 3.69-point historical RMSE.</p></article><article><span>04</span><h3>Chamber</h3><p>Combine district probabilities exactly with a Poisson-binomial distribution.</p></article></section><section className="integrity-strip"><ShieldCheck size={22} /><div><strong>Evidence foundation intact</strong><span>415/415 tests · 118/118 source records verified · four historical outcome cycles</span></div><Badge>Checkpoint 14 Aug</Badge></section></div>
  );
}

export function ElectionDashboard() {
  const [alpTpp, setAlpTpp] = useState(DEFAULT_ALP_TPP);
  return <main className="site-shell"><header className="topbar"><div className="topbar-inner"><a href="#content" className="brand" aria-label="Victorian Election Forecast home"><span className="brand-mark" aria-hidden="true">V</span><span><strong>Victorian Election</strong><small>Forecasting laboratory · 2026</small></span></a><div className="status-cluster"><span className="status-dot" /><span>Experimental forecast live</span></div></div></header><div className="content-shell" id="content"><section className="page-heading"><div><p className="eyebrow">The election, rendered honestly</p><h1>Victoria’s most consequential 88 dots.</h1><p className="page-deck">A provisional 2026 forecast that lets uncertainty stay visible—from statewide vote to every district and the radically reshaped upper house.</p></div><div className="snapshot-stamp"><span>Model vintage</span><strong>{MODEL_VINTAGE.toUpperCase()}</strong><span>Latest poll anchor</span><strong>{POLL_ANCHOR_DATE.toUpperCase()}</strong></div></section><Tabs defaultValue="forecast" className="dashboard-tabs"><div className="tabs-rail"><TabsList variant="line" className="dashboard-tabs-list" aria-label="Dashboard sections"><TabsTrigger value="forecast"><Gauge />Forecast</TabsTrigger><TabsTrigger value="districts"><MapPinned />88 districts</TabsTrigger><TabsTrigger value="council"><Landmark />Upper house</TabsTrigger><TabsTrigger value="evidence"><BookOpen />Evidence</TabsTrigger></TabsList></div><TabsContent value="forecast"><ForecastOverview alpTpp={alpTpp} setAlpTpp={setAlpTpp} /></TabsContent><TabsContent value="districts"><DistrictExplorer alpTpp={alpTpp} /></TabsContent><TabsContent value="council"><UpperHouse /></TabsContent><TabsContent value="evidence"><Evidence /></TabsContent></Tabs></div><footer><div><strong>Victorian Election Forecasting Laboratory</strong><span>Independent · provisional · reproducible</span></div><p>Experimental forecast, not voting advice. Published probabilities are conditional benchmarks and will change as evidence changes.</p></footer></main>;
}
