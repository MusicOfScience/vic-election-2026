import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { canonicaliseHtml } from "./monitor-live-sources.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MONTHS = { january: "01", february: "02", march: "03", april: "04", may: "05", june: "06", july: "07", august: "08", september: "09", october: "10", november: "11", december: "12" };

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}
function sha256(value) { return createHash("sha256").update(value).digest("hex"); }
function clean(value) { return canonicaliseHtml(value ?? "").replace(/\s+/g, " ").trim(); }

function extractLinks(html, baseUrl) {
  const links = [];
  for (const match of html.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    try { links.push({ url: new URL(match[1], baseUrl).href, text: clean(match[2]) }); } catch {}
  }
  return links;
}

export function normaliseDemosText(value) {
  return String(value ?? "")
    .replace(/&#(?:8211|x2013);|&ndash;|\u2013/gi, "-")
    .replace(/&#(?:8212|x2014);|&mdash;|\u2014/gi, "-")
    .replace(/&#(?:8216|8217|x2018|x2019);|&(?:lsquo|rsquo);|[\u2018\u2019]/gi, "'")
    .replace(/&#(?:8220|8221|x201c|x201d);|&(?:ldquo|rdquo);|[\u201c\u201d]/gi, '"')
    .replace(/&#(?:160|xa0);|&nbsp;|\u00a0/gi, " ")
    .replace(/&#37;|&percnt;/gi, "%")
    .replace(/&amp;/gi, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function dayFirstRange(text, fallbackYear = "2026") {
  const match = text.match(/conducted\s+(?:from|between)\s+(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:[ ,]+(20\d{2}))?/i);
  if (!match) return null;
  const year = match[4] ?? fallbackYear;
  const month = MONTHS[match[3].toLowerCase()];
  return { start: `${year}-${month}-${String(match[1]).padStart(2, "0")}`, end: `${year}-${month}-${String(match[2]).padStart(2, "0")}` };
}

function matchNumber(text, pattern) {
  const match = text.match(pattern);
  return match ? Number(match[1].replaceAll(",", "")) : null;
}

function extractFields(value) {
  const text = normaliseDemosText(value);
  const fieldwork = dayFirstRange(text);
  const sampleSize = matchNumber(text, /poll\s+of\s+([\d,]+)\s+(?:Victorians|voters)/i);
  const coalition =
    matchNumber(text, /(?:Liberal\/National\s+)?Coalition[^.]{0,220}?primary\s+vote(?:\s+of)?[^\d]{0,30}(\d+(?:\.\d+)?)\s*%/i) ??
    matchNumber(text, /(?:Liberal\/National\s+)?Coalition[^.]{0,140}?(\d+(?:\.\d+)?)\s*%/i);
  const alp =
    matchNumber(text, /Labor[^.]{0,140}?(?:to|on|at)\s*(\d+(?:\.\d+)?)\s*%/i) ??
    matchNumber(text, /Labor\s+(?:is\s+)?(\d+(?:\.\d+)?)\s*%/i);
  const oneNation =
    matchNumber(text, /One\s+Nation[^.]{0,100}?(?:is|on|at|second\s+on)\s*(\d+(?:\.\d+)?)\s*%/i) ??
    matchNumber(text, /One\s+Nation\s+(\d+(?:\.\d+)?)\s*%/i);
  const greens = matchNumber(text, /(?:The\s+)?Greens[^.]{0,80}?(\d+(?:\.\d+)?)\s*%/i);
  const otherParties = matchNumber(text, /Others?\s*(\d+(?:\.\d+)?)\s*%/i);
  const tpp = text.match(/Coalition\s+leads?\s+Labor\s+(\d+(?:\.\d+)?)\s*%?\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*%?/i);
  return { text, fieldwork, sampleSize, coalition, alp, oneNation, greens, otherParties, tpp };
}

export function diagnoseDemosPoll(value) {
  const fields = extractFields(value);
  return {
    fieldwork: Boolean(fields.fieldwork),
    sampleSize: fields.sampleSize !== null,
    coalition: fields.coalition !== null,
    alp: fields.alp !== null,
    oneNation: fields.oneNation !== null,
    greens: fields.greens !== null,
    otherParties: fields.otherParties !== null,
    twoPartyPreferred: Boolean(fields.tpp),
  };
}

export function extractDemosAuVictoriaPoll(value, sourceUrl) {
  const { fieldwork, sampleSize, coalition, alp, oneNation, greens, otherParties, tpp } = extractFields(value);
  if (!fieldwork || sampleSize === null || coalition === null || alp === null || oneNation === null || greens === null) return null;
  return {
    kind: "poll",
    pollster: "DemosAU",
    commissioner: "PremierNational",
    fieldworkStart: fieldwork.start,
    fieldworkEnd: fieldwork.end,
    sampleSize,
    method: "DemosAU / PremierNational state poll",
    geography: "Victoria",
    primaryVote: { coalition, alp, oneNation, greens, otherParties },
    twoPartyPreferred: tpp ? { coalition: Number(tpp[1]), alp: Number(tpp[2]) } : null,
    sourceUrl,
  };
}

async function fetchPage(url) {
  const response = await fetch(url, {
    headers: { "user-agent": "vic-election-forecast-discovery/1.0 (+https://github.com/MusicOfScience/vic-election-2026)" },
    redirect: "follow",
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return { html: await response.text(), finalUrl: response.url };
}

function parsePollSeed(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const values = [];
    let cell = "", quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"' && quoted && line[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') quoted = !quoted;
      else if (ch === "," && !quoted) { values.push(cell); cell = ""; }
      else cell += ch;
    }
    values.push(cell);
    return Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""]));
  });
}

function identity(record) { return `poll|${record.pollster}|${record.fieldworkStart}|${record.fieldworkEnd}|${record.sampleSize}`.toLowerCase(); }
function known(record, polls) {
  return polls.some((item) => item.pollster === record.pollster && item.fieldwork_start === record.fieldworkStart && item.fieldwork_end === record.fieldworkEnd && Number(item.sample_size) === record.sampleSize);
}
function wrap(record, sourceId, status) {
  const dataHash = sha256(JSON.stringify(record));
  return { id: sha256(`${sourceId}|${identity(record)}|${dataHash}`), sourceId, status, automaticPromotion: false, dataHash, ...record };
}

function recompute(report) {
  const records = report.records ?? [];
  const observations = report.observations ?? [];
  report.summary = {
    sourcesScanned: observations.length,
    recordsExtracted: records.length,
    candidates: records.filter((r) => r.kind === "candidate").length,
    polls: records.filter((r) => r.kind?.startsWith("poll")).length,
    quarantined: records.filter((r) => r.status === "quarantined-awaiting-review").length,
    alreadyTracked: records.filter((r) => r.status === "already-tracked").length,
    extractionFailures: observations.filter((o) => o.status === "extract-failed").length,
  };
}

async function main() {
  const reportPath = resolve(root, arg("--report", "source-discovery-report.json"));
  const quarantinePath = resolve(root, arg("--quarantine", "source-discovery-quarantine.json"));
  const config = JSON.parse(readFileSync(resolve(root, "metadata/live-source-adapters.json"), "utf8"));
  const adapter = config.adapters.find((item) => item.id === "demosau-victoria-state-polls");
  if (!adapter) throw new Error("DemosAU adapter missing");

  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const quarantine = JSON.parse(readFileSync(quarantinePath, "utf8"));
  const polls = parsePollSeed(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
  const urls = new Set(adapter.discovery.seedUrls ?? []);
  let indexError = null;
  try {
    const index = await fetchPage(adapter.url);
    for (const link of extractLinks(index.html, index.finalUrl)) {
      if (/\/news\//i.test(link.url) && /victoria|victorian/i.test(link.text) && /poll|coalition|labor|election/i.test(link.text)) urls.add(link.url);
    }
  } catch (error) { indexError = error instanceof Error ? error.message : String(error); }

  const extracted = [];
  const errors = [];
  for (const url of [...urls].slice(0, 10)) {
    try {
      const page = await fetchPage(url);
      const canonical = canonicaliseHtml(page.html);
      const record = extractDemosAuVictoriaPoll(canonical, page.finalUrl);
      if (record) extracted.push(record);
      else errors.push(`${page.finalUrl}: parse-miss ${JSON.stringify(diagnoseDemosPoll(canonical))}`);
    } catch (error) { errors.push(`${url}: ${error instanceof Error ? error.message : String(error)}`); }
  }

  const existingIds = new Set((report.records ?? []).map(identity));
  let added = 0;
  for (const record of extracted) {
    if (existingIds.has(identity(record))) continue;
    const status = known(record, polls) ? "already-tracked" : "quarantined-awaiting-review";
    const wrapped = wrap(record, adapter.id, status);
    report.records.push(wrapped);
    existingIds.add(identity(record));
    if (status === "quarantined-awaiting-review") quarantine.records.push(wrapped);
    added++;
  }

  report.observations.push({
    sourceId: adapter.id,
    status: extracted.length ? "ok" : "extract-failed",
    extracted: extracted.length,
    added,
    ...(indexError ? { indexWarning: indexError } : {}),
    ...(errors.length ? { errors } : {}),
  });
  recompute(report);
  quarantine.checkedAt = report.checkedAt;
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(quarantinePath, `${JSON.stringify(quarantine, null, 2)}\n`);
  console.log(`DemosAU discovery: ${extracted.length} parsed, ${added} added; automatic promotion disabled.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
