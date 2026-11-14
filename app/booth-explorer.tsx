"use client";

import { useState } from "react";
import { ExternalLink, Search, Vote } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { boothData } from "./booth-data.generated";
import { parties, partyMeta, type Party } from "./assembly-parties";
import type { modelOutput } from "./model-output.generated";

type District = (typeof modelOutput.districts)[number];
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

const number = new Intl.NumberFormat("en-AU");
const boothById = new Map(boothData.districts.map((district) => [district.districtId, district as unknown as BoothDistrict]));

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

export default function BoothExplorer({ district }: { district: District }) {
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
    <div className="booth-controls"><label className="search-field"><Search size={15} /><Input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Find a voting centre" placeholder="Find a voting centre…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" /></label><Select value={metric} onValueChange={(value) => setMetric((value ?? district.favoured_party) as Party | "FINAL_TWO")}><SelectTrigger className="filter-select" aria-label="Choose booth comparison"><SelectValue /></SelectTrigger><SelectContent>{parties.map((party) => <SelectItem key={party} value={party}>{partyMeta[party].label} first preference</SelectItem>)}{finalTwo.length === 2 && <SelectItem value="FINAL_TWO">{candidateShortName(finalTwo[0].name)} vs {candidateShortName(finalTwo[1].name)} final two</SelectItem>}</SelectContent></Select></div>
    <div className="booth-chart-heading"><strong>{metricLabel}</strong><span>{filtered.length > 14 ? "Seven highest and seven lowest" : `${filtered.length} matching booths`}</span></div>
    {chartRows.length ? <div className="booth-chart"><ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={1}><BarChart data={chartRows} layout="vertical" margin={{ top: 4, right: 18, left: 18, bottom: 0 }}><CartesianGrid horizontal={false} stroke="#d7d8d4" strokeDasharray="2 4" /><XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 8 }} tickFormatter={(value) => `${value}%`} /><YAxis type="category" dataKey="name" width={112} tickLine={false} axisLine={false} tick={{ fontSize: 8 }} /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, metricLabel]} labelFormatter={(label, payload) => `${label} · ${number.format(payload?.[0]?.payload?.total ?? 0)} total votes`} /><Bar dataKey="value" fill={metricColour} radius={[0, 2, 2, 0]} /></BarChart></ResponsiveContainer></div> : <p className="empty-booths">No voting centre matches that search.</p>}
    <div className="booth-table desktop-table"><Table><TableHeader><TableRow><TableHead>Voting centre</TableHead><TableHead>Formal</TableHead>{parties.map((party) => <TableHead key={party}>{partyMeta[party].short} 1st pref.</TableHead>)}{finalTwo.length === 2 && <TableHead>{candidateShortName(finalTwo[0].name)} 2CP</TableHead>}</TableRow></TableHeader><TableBody>{filtered.map((booth) => <TableRow key={booth.name}><TableCell className="district-name">{booth.name}</TableCell><TableCell>{number.format(booth.formal)}</TableCell>{parties.map((party) => <TableCell key={party}>{booth.primaryPct[party].toFixed(1)}%</TableCell>)}{finalTwo.length === 2 && <TableCell><strong>{booth.twoCandidate ? `${booth.twoCandidate.pct[0].toFixed(1)}%` : "—"}</strong></TableCell>}</TableRow>)}</TableBody></Table></div>
    <div className="mobile-booths">{filtered.map((booth) => <article key={booth.name}><div><strong>{booth.name}</strong><span>{number.format(booth.formal)} formal votes</span></div><dl>{parties.map((party) => <div key={party}><dt>{partyMeta[party].short}</dt><dd>{booth.primaryPct[party].toFixed(1)}%</dd></div>)}{finalTwo.length === 2 && <div><dt>{candidateShortName(finalTwo[0].name)} 2CP</dt><dd>{booth.twoCandidate ? `${booth.twoCandidate.pct[0].toFixed(1)}%` : "—"}</dd></div>}</dl></article>)}</div>
    <div className="booth-source-links"><a href={record.source} target="_blank" rel="noreferrer">Verify first preferences at VEC <ExternalLink size={12} /></a><a href={record.twoCandidateSource} target="_blank" rel="noreferrer">Verify final two at VEC <ExternalLink size={12} /></a></div>
  </section>;
}

