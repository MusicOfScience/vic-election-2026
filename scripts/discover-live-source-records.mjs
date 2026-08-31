import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { canonicaliseHtml } from "./monitor-live-sources.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const adaptersPath = resolve(root, "metadata/live-source-adapters.json");
const candidatesPath = resolve(root, "metadata/candidates-2026.json");
const liveStatePath = resolve(root, "metadata/live-source-state.json");
const pollsPath = resolve(root, "model/data/processed/poll_events_seed.csv");

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function clean(value) {
  return canonicaliseHtml(value ?? "").replace(/\s+/g, " ").trim();
}

export function extractLinks(html, baseUrl) {
  const links = [];
  const re = /<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  for (const match of html.matchAll(re)) {
    try {
      links.push({ url: new URL(match[1], baseUrl).href, text: clean(match[2]) });
    } catch {}
  }
  return links;
}

export function findVecCandidateListUrls(html, baseUrl) {
  const wanted = /(nominated candidates|candidate list|candidates for the 2026 state election|state election candidates)/i;
  return [...new Set(extractLinks(html, baseUrl).filter((link) => wanted.test(link.text)).map((link) => link.url))];
}

export function parseHtmlTables(html) {
  const tables = [];
  for (const tableMatch of html.matchAll(/<table\b[^>]*>([\s\S]*?)<\/table>/gi)) {
    const rows = [];
    for (const rowMatch of tableMatch[1].matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)) {
      const cells = [...rowMatch[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map((cell) => clean(cell[1]));
      if (cells.length) rows.push(cells);
    }
    if (rows.length) tables.push(rows);
  }
  return tables;
}

function headerIndex(headers, pattern) {
  return headers.findIndex((value) => pattern.test(value));
}

export function extractVecCandidatesFromHtml(html, sourceUrl) {
  const records = [];
  for (const rows of parseHtmlTables(html)) {
    const headers = rows[0].map((value) => value.toLowerCase());
    const nameIdx = headerIndex(headers, /candidate|name/);
    const contestIdx = headerIndex(headers, /district|region|electorate|contest/);
    const partyIdx = headerIndex(headers, /party|affiliation/);
    if (nameIdx < 0 || contestIdx < 0) continue;
    for (const row of rows.slice(1)) {
      const name = row[nameIdx]?.trim();
      const contest = row[contestIdx]?.trim();
      if (!name || !contest || /^candidate$|^name$/i.test(name)) continue;
      records.push({ kind: "candidate", name, contest, party: partyIdx >= 0 ? row[partyIdx]?.trim() || null : null, candidateStatus: "nominated", sourceAuthority: "VEC", sourceUrl });
    }
  }
  return records;
}

export function extractGreensCandidates(html, pageUrl) {
  const records = [];
  for (const link of extractLinks(html, pageUrl)) {
    const match = link.text.match(/^(.+?)\s+(?:Lead\s+)?Candidate for\s+(.+?)(?:\s+and\s+(?:Councillor|Mayor)\b.*)?$/i);
    if (!match) continue;
    records.push({ kind: "candidate", name: match[1].trim(), contest: match[2].trim(), party: "Australian Greens Victoria", candidateStatus: "endorsed", sourceAuthority: "Australian Greens Victoria", sourceUrl: link.url });
  }
  return records;
}

export function extractOneNationCandidates(html, pageUrl) {
  const records = [];
  for (const heading of html.matchAll(/<h3\b[^>]*>[\s\S]*?<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/h3>/gi)) {
    const text = clean(heading[2]);
    const match = text.match(/^(.+?)\s+for\s+(.+)$/i);
    if (!match) continue;
    let sourceUrl = pageUrl;
    try { sourceUrl = new URL(heading[1], pageUrl).href; } catch {}
    records.push({ kind: "candidate", name: match[1].trim(), contest: match[2].trim(), party: "Pauline Hanson's One Nation", candidateStatus: "endorsed", sourceAuthority: "One Nation Victoria", sourceUrl });
  }
  return records;
}

export function extractNationalsCandidates(html, pageUrl) {
  const records = [];
  for (const section of html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1>\s*<h3\b[^>]*>([\s\S]*?)<\/h3>/gi)) {
    const name = clean(section[1]);
    const role = clean(section[2]);
    const match = role.match(/^Candidate for\s+(.+)$/i);
    if (!name || !match) continue;
    records.push({ kind: "candidate", name, contest: match[1].trim(), party: "The Nationals", candidateStatus: "endorsed", sourceAuthority: "The Nationals Victoria", sourceUrl: pageUrl });
  }
  return records;
}

export function extractLaborCandidates(html, pageUrl) {
  const records = [];
  const sections = html.split(/(?=<div\b[^>]*role=["']listitem["'][^>]*class=["']member_list-item(?:\s|["']))/i);
  for (const section of sections) {
    const type = section.match(/fs-list-field=["']member-type["'][^>]*>([\s\S]*?)<\//i);
    if (!type || clean(type[1]) !== "Candidates") continue;
    const name = section.match(/<h4\b[^>]*fs-list-field=["']full-name["'][^>]*>([\s\S]*?)<\/h4>/i);
    const contest = section.match(/<div\b[^>]*class=["'][^"']*w-embed[^"']*["'][^>]*>\s*Candidate for\s+([^<]+)<\/div>/i);
    if (!name || !contest) continue;
    const profile = section.match(/<a\b[^>]*href=["']([^"']+)["']/i);
    let sourceUrl = pageUrl;
    try { if (profile) sourceUrl = new URL(profile[1], pageUrl).href; } catch {}
    records.push({ kind: "candidate", name: clean(name[1]), contest: clean(contest[1]).replace(/\.$/, ""), party: "Australian Labor Party - Victorian Branch", candidateStatus: "endorsed", sourceAuthority: "Victorian Labor", sourceUrl });
  }
  return records;
}

export function extractLiberalCandidates(jsonText) {
  const payload = JSON.parse(jsonText);
  if (!Array.isArray(payload.Datas)) throw new Error("Liberal Victoria candidate API returned no Datas array");
  const records = payload.Datas.filter((item) => item.IsCandidate === true && item.FirstName && item.LastName && item.Electorate).map((item) => ({
    kind: "candidate",
    name: clean(`${item.FirstName} ${item.LastName}`),
    contest: clean(item.Electorate),
    party: "Liberal Party of Australia (Victorian Division)",
    candidateStatus: "endorsed",
    sourceAuthority: "Liberal Victoria",
    sourceUrl: `https://vic.liberal.org.au/team/${item.Slug}`,
  }));
  if (!records.length) throw new Error("Liberal Victoria candidate API returned no candidates");
  return records;
}

function contestWanted(contest, targetContests = []) {
  return targetContests.length === 0 || targetContests.some((target) => target.toLowerCase() === contest.toLowerCase());
}

export function extractVictorianSocialistsCandidates(html, pageUrl, targetContests = []) {
  const records = [];
  for (const link of extractLinks(html, pageUrl)) {
    const match = link.text.match(/^(.+?)\s+for\s+(.+)$/i);
    if (!match || !contestWanted(match[2].trim(), targetContests)) continue;
    records.push({
      kind: "candidate",
      name: match[1].trim(),
      contest: match[2].trim(),
      party: "Victorian Socialists",
      candidateStatus: "endorsed",
      sourceAuthority: "Victorian Socialists",
      sourceUrl: link.url,
    });
  }
  return records;
}

export function extractFamilyFirstCandidates(html, pageUrl, targetContests = []) {
  const records = [];
  const links = extractLinks(html, pageUrl);
  for (const rows of parseHtmlTables(html)) {
    for (const cell of rows.flat()) {
      const match = cell.match(/^(.+?)\s*[-–]\s*(.+)$/);
      if (!match || !contestWanted(match[1].trim(), targetContests)) continue;
      const name = match[2].trim();
      const profile = links.find((link) => link.text.toLowerCase() === name.toLowerCase());
      records.push({
        kind: "candidate",
        name,
        contest: match[1].trim(),
        party: "Family First Party Australia",
        candidateStatus: "endorsed",
        sourceAuthority: "Family First Party Australia",
        sourceUrl: profile?.url ?? pageUrl,
      });
    }
  }
  return records;
}

export function extractMorningtonPeninsulaCandidates(html, pageUrl, targetContests = []) {
  const records = [];
  const sections = html.split(/(?=<h3\b[^>]*>)/i);
  for (const section of sections) {
    const headingTag = section.match(/^<h3\b[^>]*>([\s\S]*?)<\/h3>/i);
    const heading = headingTag && clean(headingTag[1]).match(/^Electorate:\s*(.+)$/i);
    if (!heading) continue;
    const contest = heading[1].trim();
    if (!contestWanted(contest, targetContests)) continue;
    for (const rows of parseHtmlTables(section)) {
      const headers = rows[0].map((value) => value.toLowerCase());
      const nameIdx = headerIndex(headers, /candidate|name/);
      const partyIdx = headerIndex(headers, /party|affiliation/);
      if (nameIdx < 0) continue;
      for (const row of rows.slice(1)) {
        const name = row[nameIdx]?.trim();
        if (!name) continue;
        const publishedParty = partyIdx >= 0 ? row[partyIdx]?.trim() || null : null;
        const party = publishedParty === "Liberal" ? "Liberal Party of Australia (Victorian Division)" : publishedParty;
        records.push({ kind: "candidate", name, contest, party, candidateStatus: "announced", sourceAuthority: "Mornington Peninsula Shire", sourceUrl: pageUrl });
      }
    }
  }
  return records;
}

export function findNextTeamPageUrl(html, pageUrl) {
  const link = extractLinks(html, pageUrl).find((item) => /^(next|next page)$/i.test(item.text) || /w-pagination-next/.test(item.url));
  if (link) return link.url;
  for (const tag of html.matchAll(/<a\b[^>]*>/gi)) {
    if (!/class=["'][^"']*w-pagination-next/i.test(tag[0]) && !/aria-label=["']Next Page["']/i.test(tag[0])) continue;
    const href = tag[0].match(/href=["']([^"']+)["']/i);
    try { if (href) return new URL(href[1], pageUrl).href; } catch {}
  }
  return null;
}

const MONTHS = { january: "01", february: "02", march: "03", april: "04", may: "05", june: "06", july: "07", august: "08", september: "09", october: "10", november: "11", december: "12" };

export function parseFieldworkRange(text) {
  const match = text.match(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*[-–]\s*(\d{1,2}),\s*(20\d{2})\b/i);
  if (!match) return null;
  const month = MONTHS[match[1].toLowerCase()];
  const year = match[4];
  return { start: `${year}-${month}-${String(match[2]).padStart(2, "0")}`, end: `${year}-${month}-${String(match[3]).padStart(2, "0")}` };
}

function pct(text, label) {
  const match = text.match(new RegExp(`${label}\\s*(?:Coalition\\s*)?(\\d+(?:\\.\\d+)?)%`, "i"));
  return match ? Number(match[1]) : null;
}

export function extractRoyMorganStatePoll(text, sourceUrl) {
  const fieldwork = parseFieldworkRange(text);
  const sampleMatch = text.match(/cross-section of\s+([\d,]+)\s+electors/i);
  const sampleSize = sampleMatch ? Number(sampleMatch[1].replaceAll(",", "")) : null;
  const primaryVote = { coalition: pct(text, "L-NP"), alp: pct(text, "ALP"), oneNation: pct(text, "One Nation"), greens: pct(text, "Greens"), otherParties: pct(text, "Other Parties"), independents: pct(text, "Independents") };
  const tppMatch = text.match(/two-party preferred[\s\S]{0,500}?L-NP\s+(\d+(?:\.\d+)?)%[\s\S]{0,180}?ALP\s+(\d+(?:\.\d+)?)%/i);
  if (!fieldwork || !sampleSize || primaryVote.alp === null || primaryVote.coalition === null) return null;
  return { kind: "poll", pollster: "Roy Morgan", fieldworkStart: fieldwork.start, fieldworkEnd: fieldwork.end, sampleSize, method: /special SMS Roy Morgan Poll/i.test(text) ? "special SMS survey" : "Roy Morgan survey", geography: "Victoria", primaryVote, twoPartyPreferred: tppMatch ? { coalition: Number(tppMatch[1]), alp: Number(tppMatch[2]) } : null, sourceUrl };
}

export function extractRoyMorganUpperHouse(text, sourceUrl) {
  const fieldwork = parseFieldworkRange(text);
  const sampleMatch = text.match(/cross-section of\s+([\d,]+)\s+electors/i);
  const coalition = text.match(/L-NP Coalition is set to win\s+(\d+)\s+seats/i);
  const oneNation = text.match(/One Nation\s*\((\d+)\s+seats\)/i);
  const alpWord = text.match(/ALP\s*\((\d+|nine|ten|eleven|twelve)\s+seats\)/i);
  const words = { nine: 9, ten: 10, eleven: 11, twelve: 12 };
  if (!fieldwork || !sampleMatch || !coalition || !oneNation || !alpWord) return null;
  return { kind: "poll-upper-house", pollster: "Roy Morgan", fieldworkStart: fieldwork.start, fieldworkEnd: fieldwork.end, sampleSize: Number(sampleMatch[1].replaceAll(",", "")), geography: "Victoria Legislative Council", seatProjection: { coalition: Number(coalition[1]), oneNation: Number(oneNation[1]), alp: Number(alpWord[1]) || words[alpWord[1].toLowerCase()] }, sourceUrl };
}

export function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some(Boolean)) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}

function identity(record) {
  if (record.kind === "candidate") return `candidate|${record.contest}|${record.name}`.toLowerCase();
  return `${record.kind}|${record.pollster}|${record.fieldworkStart}|${record.fieldworkEnd}|${record.sampleSize}`.toLowerCase();
}

function isKnown(record, candidates, polls) {
  if (record.kind === "candidate") return candidates.some((item) => identity(item) === identity(record));
  if (record.kind === "poll") return polls.some((item) => item.pollster === record.pollster && item.fieldwork_start === record.fieldworkStart && item.fieldwork_end === record.fieldworkEnd && Number(item.sample_size) === record.sampleSize);
  return false;
}

async function fetchPage(url) {
  const response = await fetch(url, { headers: { "user-agent": "vic-election-forecast-discovery/1.0 (+https://github.com/MusicOfScience/vic-election-2026)" }, redirect: "follow", signal: AbortSignal.timeout(20_000) });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return { html: await response.text(), finalUrl: response.url };
}

function wrapRecord(record, sourceId, status) {
  const dataHash = sha256(JSON.stringify(record));
  return { id: sha256(`${sourceId}|${identity(record)}|${dataHash}`), sourceId, status, automaticPromotion: false, dataHash, ...record };
}

async function discoverRoyMorganLinks(page, adapter, found) {
  const links = extractLinks(page.html, page.finalUrl).filter((link) => /victorian state voting intention/i.test(link.text) && /\/findings\//i.test(link.url));
  for (const link of [...new Map(links.map((item) => [item.url, item])).values()].slice(0, 8)) {
    const article = await fetchPage(link.url);
    const text = canonicaliseHtml(article.html);
    const record = /upper house/i.test(text) ? extractRoyMorganUpperHouse(text, article.finalUrl) : extractRoyMorganStatePoll(text, article.finalUrl);
    if (record) found.push(record);
  }
}

async function discoverLaborCandidates(firstPage, found) {
  const initialCount = found.length;
  let page = firstPage;
  const visited = new Set();
  for (let i = 0; i < 12 && !visited.has(page.finalUrl); i++) {
    visited.add(page.finalUrl);
    found.push(...extractLaborCandidates(page.html, page.finalUrl));
    const nextUrl = findNextTeamPageUrl(page.html, page.finalUrl);
    if (!nextUrl || visited.has(nextUrl)) break;
    page = await fetchPage(nextUrl);
  }
  if (found.length === initialCount) throw new Error("Victorian Labor roster returned no explicitly labelled candidates");
}

async function discoverFromAdapter(adapter, acceptedFingerprint, candidates, polls) {
  const page = await fetchPage(adapter.url);
  const canonical = canonicaliseHtml(page.html);
  const currentFingerprint = sha256(canonical);
  const baselineHealthy = acceptedFingerprint && acceptedFingerprint === currentFingerprint;
  const found = [];

  if (adapter.discovery.extractor === "roy-morgan-state-poll") {
    const record = extractRoyMorganStatePoll(canonical, page.finalUrl);
    if (record) found.push(record);
  } else if (adapter.discovery.extractor === "roy-morgan-upper-house") {
    const record = extractRoyMorganUpperHouse(canonical, page.finalUrl);
    if (record) found.push(record);
  } else if (adapter.discovery.extractor === "roy-morgan-homepage") {
    await discoverRoyMorganLinks(page, adapter, found);
  } else if (adapter.discovery.extractor === "vec-candidate-table") {
    const urls = [page.finalUrl, ...findVecCandidateListUrls(page.html, page.finalUrl)];
    for (const url of [...new Set(urls)]) {
      const candidatePage = url === page.finalUrl ? page : await fetchPage(url);
      found.push(...extractVecCandidatesFromHtml(candidatePage.html, candidatePage.finalUrl));
    }
  } else if (adapter.discovery.extractor === "greens-victoria-candidates") {
    found.push(...extractGreensCandidates(page.html, page.finalUrl));
  } else if (adapter.discovery.extractor === "one-nation-victoria-candidates") {
    found.push(...extractOneNationCandidates(page.html, page.finalUrl));
  } else if (adapter.discovery.extractor === "nationals-victoria-candidates") {
    found.push(...extractNationalsCandidates(page.html, page.finalUrl));
  } else if (adapter.discovery.extractor === "labor-victoria-candidates") {
    await discoverLaborCandidates(page, found);
  } else if (adapter.discovery.extractor === "liberal-victoria-candidates") {
    found.push(...extractLiberalCandidates(page.html));
  } else if (adapter.discovery.extractor === "victorian-socialists-candidates") {
    found.push(...extractVictorianSocialistsCandidates(page.html, page.finalUrl, adapter.discovery.targetContests));
  } else if (adapter.discovery.extractor === "family-first-victoria-candidates") {
    found.push(...extractFamilyFirstCandidates(page.html, page.finalUrl, adapter.discovery.targetContests));
  } else if (adapter.discovery.extractor === "mornington-peninsula-candidates") {
    found.push(...extractMorningtonPeninsulaCandidates(page.html, page.finalUrl, adapter.discovery.targetContests));
  }

  return found.map((record) => {
    const known = isKnown(record, candidates, polls);
    const acceptedSource = (adapter.discovery.acceptedSourceUrls ?? []).includes(record.sourceUrl);
    const status = known ? "already-tracked" : (baselineHealthy || acceptedSource) ? "baseline-observed" : "quarantined-awaiting-review";
    return wrapRecord(record, adapter.id, status);
  });
}

async function main() {
  const config = JSON.parse(readFileSync(adaptersPath, "utf8"));
  const registry = JSON.parse(readFileSync(candidatesPath, "utf8"));
  const liveState = JSON.parse(readFileSync(liveStatePath, "utf8"));
  const polls = parseCsv(readFileSync(pollsPath, "utf8"));
  const accepted = new Map((liveState.sources ?? []).map((source) => [source.id, source.acceptedFingerprint]));
  const records = [], observations = [];

  for (const adapter of config.adapters.filter((item) => item.discovery?.enabled)) {
    try {
      const extracted = await discoverFromAdapter(adapter, accepted.get(adapter.id), registry.candidates ?? [], polls);
      records.push(...extracted);
      observations.push({ sourceId: adapter.id, status: "ok", extracted: extracted.length });
    } catch (error) {
      observations.push({ sourceId: adapter.id, status: "extract-failed", error: error instanceof Error ? error.message : String(error) });
    }
  }

  const unique = [...new Map(records.map((record) => [identity(record), record])).values()];
  const quarantine = unique.filter((record) => record.status === "quarantined-awaiting-review");
  const report = {
    schemaVersion: 1,
    checkedAt: new Date().toISOString(),
    policy: "source-specific-extract-dedupe-quarantine-review",
    automaticPromotion: false,
    summary: {
      sourcesScanned: observations.length,
      recordsExtracted: unique.length,
      candidates: unique.filter((record) => record.kind === "candidate").length,
      polls: unique.filter((record) => record.kind.startsWith("poll")).length,
      quarantined: quarantine.length,
      alreadyTracked: unique.filter((record) => record.status === "already-tracked").length,
      extractionFailures: observations.filter((item) => item.status === "extract-failed").length,
    },
    observations,
    records: unique,
  };
  const reportPath = resolve(root, arg("--report", "source-discovery-report.json"));
  const quarantinePath = resolve(root, arg("--quarantine", "source-discovery-quarantine.json"));
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(quarantinePath, `${JSON.stringify({ schemaVersion: 1, checkedAt: report.checkedAt, automaticPromotion: false, records: quarantine }, null, 2)}\n`);
  console.log(`Source discovery: ${unique.length} structured records, ${quarantine.length} quarantined, ${report.summary.extractionFailures} extraction failures.`);
  if (process.argv.includes("--fail-on-extraction-error") && report.summary.extractionFailures) process.exitCode = 3;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
