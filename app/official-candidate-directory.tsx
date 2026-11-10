"use client";

import { useMemo, useState } from "react";
import { ExternalLink, Search, ShieldCheck, UsersRound } from "lucide-react";
import roster from "./vec-official-candidates-2026.review.json";

type Chamber = "Assembly" | "Council";
type CandidateRow = [Chamber, string, number, string, string | null];
const candidates = roster.rows as CandidateRow[];
const sourceUrl = "https://www.vec.vic.gov.au/2026-state-election";

const describeParty = (name: string | null) =>
  name?.trim() || "No registered party recorded";

function groupCandidates(chamber: Chamber, q: string, partyFilter: string) {
  const query = q.toLocaleLowerCase("en-AU").trim();
  const groups = new Map<string, CandidateRow[]>();
  for (const row of candidates) {
    const [house, contest] = row;
    if (house !== chamber) continue;
    const previous = groups.get(contest) ?? [];
    previous.push(row);
    groups.set(contest, previous);
  }
  return [...groups.entries()]
    .filter(([contest, list]) =>
      (!query || contest.toLocaleLowerCase("en-AU").includes(query) ||
       list.some((row) => (row[3] + " " + (row[4] ?? "")).toLocaleLowerCase("en-AU").includes(query))) &&
      (partyFilter === "all" || list.some((row) => (row[4] ?? "") === partyFilter)))
    .map(([contest, list]) => ({ contest, rows: list.sort((a, b) => a[2] - b[2]) }))
    .sort((a, b) => a.contest.localeCompare(b.contest, "en-AU"));
}

export function OfficialCandidateDirectory() {
  const [chamber, setChamber] = useState<Chamber>("Assembly");
  const [query, setQuery] = useState("");
  const [party, setParty] = useState("all");
  const parties = useMemo(() => [...new Set(candidates.filter((r) => r[0] === chamber).map((r) => r[4] ?? ""))]
    .sort((a, b) => a.localeCompare(b)), [chamber]);
  const groups = useMemo(() => groupCandidates(chamber, query, party), [chamber, query, party]);
  const listedCandidates = groups.reduce((total, group) => total + group.rows.length, 0);
  const total = chamber === "Assembly" ? roster.chambers.Assembly : roster.chambers.Council;
  const totalContests = chamber === "Assembly" ? roster.contests.Assembly : roster.contests.Council;
  const unmatchedParty = candidates.filter((row) => row[4] == null).length;
  const termsActive = Boolean(query.trim() || party !== "all");

  return <div className="tab-stack">
    <section className="official-roster-hero">
      <div>
        <p className="eyebrow">Victorian Electoral Commission · 2026 official nominations</p>
        <h2>Every candidate. Every electorate.</h2>
        <p>Explore all 1,037 people nominated for the 28 November state election, taken from the VEC's official candidate report after nominations closed. Candidate details are presented as VEC source records, separate from the experimental forecast.</p>
      </div>
      <a className="official-roster-source" href={sourceUrl} target="_blank" rel="noreferrer">View original VEC source <ExternalLink size={14}/></a>
    </section>
    <div className="official-roster-totals" aria-label="Verified candidate totals">
      <article><strong>{roster.chambers.Assembly}</strong><span>Assembly candidates · 88 districts</span></article>
      <article><strong>{roster.chambers.Council}</strong><span>Council candidates · 8 regions</span></article>
      <article><strong>{roster.chambers.Assembly + roster.chambers.Council}</strong><span>VEC nominations · 96 contests</span></article>
    </div>
    <section className="surface official-roster-search" aria-label="Search official nominees">
      <div className="official-roster-form">
        <fieldset className="official-roster-house">
          <legend>Chamber</legend>
          <label><input type="radio" name="official-chamber" checked={chamber === "Assembly"} onChange={() => { setChamber("Assembly"); setParty("all"); }} /> Legislative Assembly</label>
          <label><input type="radio" name="official-chamber" checked={chamber === "Council"} onChange={() => { setChamber("Council"); setParty("all"); }} /> Legislative Council</label>
        </fieldset>
        <label className="official-roster-query"><span>Search a candidate, electorate or party</span><span className="official-roster-input"><Search size={18}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name, district or party…" /></span></label>
        <label className="official-roster-select"><span>Registered party (VEC wording)</span><select value={party} onChange={(e) => setParty(e.target.value)}>
          <option value="all">All party labels</option>
          {parties.map((value) => <option key={value} value={value}>{describeParty(value)}</option>)}
        </select></label>
      </div>
      <div className="official-roster-results" aria-live="polite">
        {termsActive ? `${groups.length} contests matched · ${listedCandidates} candidates listed in those contests` : `${totalContests} contests · ${total} candidates`}
      </div>
    </section>
    <section aria-label="Official candidate lists" className="official-roster-contests">
      {groups.map((group) => <details className="surface official-roster-contest" key={chamber + group.contest}>
        <summary>
          <span className="official-roster-contest-name"><strong>{group.contest}</strong><small>{chamber === "Assembly" ? "Legislative Assembly district" : "Legislative Council region"}</small></span>
          <span className="official-roster-count">{group.rows.length} candidates</span>
          <span aria-hidden="true" className="official-roster-chevron">+</span>
        </summary>
        <div className="official-roster-candidates">
          {group.rows.map((candidate) => <div className="official-roster-candidate" key={candidate[2] + "|" + candidate[3]}>
            <span className="official-roster-position" title="Position in captured VEC source report">{candidate[2]}</span>
            <div><strong>{candidate[3]}</strong><span className={candidate[4] == null ? "official-roster-unaffiliated" : ""}>{describeParty(candidate[4])}</span></div>
          </div>)}
        </div>
        <p className="official-roster-disclaimer">Numbers show order in the captured VEC workbook, not independently certified ballot-paper positions. Council group letters and ungrouped status require separate verification.</p>
      </details>)}
      {groups.length === 0 && <p className="official-roster-empty">No contests match those filters. Try another candidate name or clear the registered-party filter.</p>}
    </section>
    <section className="surface official-roster-caveats" aria-label="Candidate data accuracy and forecast boundaries">
      <div><ShieldCheck size={20}/><h3>Official source, separate model</h3></div>
      <p>Source: VEC candidate report stamped <strong>9 November 2026, 7:58 pm AEDT</strong>. The raw source was independently fingerprinted; this public directory contains candidate names and registered-party labels only. No contact-person names, phone numbers or email addresses were imported.</p>
      <p><strong>Important:</strong> {unmatchedParty} candidates have no registered-party label in the source. That does not necessarily mean independent or ungrouped. Particularly for the Legislative Council, ballot-group letters, above-the-line groups and ungrouped classification are not asserted here.</p>
      <p>The probabilistic forecast is still based on the <strong>31 October experimental model</strong>, which does not yet use this official ballot as its candidate mask. These nomination records do not change the seat probabilities, which remain uncalibrated for production release.</p>
      <div className="official-roster-checks"><UsersRound size={16} /><span>Source record: 734 Assembly + 303 Council · each of 96 contest totals reconciled · review-only candidate identities</span></div>
    </section>
  </div>;
}
