import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { canonicaliseHtml } from "./monitor-live-sources.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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

function normaliseContest(value) {
  return clean(value)
    .replace(/\s+(?:Image|Make a Donation|Donate|Volunteer|Community Survey|Read More).*$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function teamLinks(value, baseUrl) {
  const links = [];
  for (const match of String(value ?? "").matchAll(/<a\b[^>]*href=["']([^"']*\/team\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    const text = clean(match[2]);
    if (!text) continue;
    try {
      links.push({ index: match.index ?? 0, url: new URL(match[1], baseUrl).href, text });
    } catch {}
  }
  return links;
}

export function extractLiberalCandidates(html, pageUrl) {
  const links = teamLinks(html, pageUrl);
  const records = [];
  const roleRe = /\b(?:Candidate|Liberal)\s+for\s+([^<\r\n]{2,100})/gi;

  for (const role of String(html ?? "").matchAll(roleRe)) {
    const roleIndex = role.index ?? 0;
    const preceding = links.filter((link) => link.index < roleIndex && roleIndex - link.index < 1800);
    const person = preceding.at(-1);
    if (!person) continue;

    const contest = normaliseContest(role[1]);
    const name = person.text.replace(/\s+(?:Candidate|Liberal|Member)\s+for\s+.*$/i, "").trim();
    if (!name || !contest || /^(state|federal|all|candidates?)$/i.test(name)) continue;

    records.push({
      kind: "candidate",
      name,
      contest,
      party: "Liberal Party",
      candidateStatus: "endorsed",
      sourceAuthority: "Liberal Victoria",
      sourceUrl: person.url,
    });
  }

  return [...new Map(records.map((record) => [`${record.name}|${record.contest}`.toLowerCase(), record])).values()];
}

function identity(record) {
  return `candidate|${record.contest}|${record.name}`.toLowerCase();
}

function acceptedCandidate(record, candidates) {
  return candidates.some((item) => identity(item) === identity(record));
}

function wrap(record, sourceId, status) {
  const dataHash = sha256(JSON.stringify(record));
  return {
    id: sha256(`${sourceId}|${identity(record)}|${dataHash}`),
    sourceId,
    status,
    automaticPromotion: false,
    dataHash,
    ...record,
  };
}

function recompute(report) {
  const records = report.records ?? [];
  const observations = report.observations ?? [];
  report.summary = {
    sourcesScanned: observations.length,
    recordsExtracted: records.length,
    candidates: records.filter((record) => record.kind === "candidate").length,
    polls: records.filter((record) => record.kind?.startsWith("poll")).length,
    quarantined: records.filter((record) => record.status === "quarantined-awaiting-review").length,
    alreadyTracked: records.filter((record) => record.status === "already-tracked").length,
    extractionFailures: observations.filter((item) => item.status === "extract-failed").length,
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

async function main() {
  const reportPath = resolve(root, arg("--report", "source-discovery-report.json"));
  const quarantinePath = resolve(root, arg("--quarantine", "source-discovery-quarantine.json"));
  const config = JSON.parse(readFileSync(resolve(root, "metadata/live-source-adapters.json"), "utf8"));
  const adapter = config.adapters.find((item) => item.id === "liberal-victoria-candidates");
  if (!adapter) throw new Error("Liberal Victoria adapter missing");

  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const quarantine = JSON.parse(readFileSync(quarantinePath, "utf8"));
  const accepted = JSON.parse(readFileSync(resolve(root, "metadata/candidates-2026.json"), "utf8"));
  const urls = adapter.discovery?.urls ?? [adapter.url];
  const extracted = [];
  const errors = [];

  for (const url of urls) {
    try {
      const page = await fetchPage(url);
      extracted.push(...extractLiberalCandidates(page.html, page.finalUrl));
    } catch (error) {
      errors.push(`${url}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  const uniqueExtracted = [...new Map(extracted.map((record) => [identity(record), record])).values()];
  const existing = new Set((report.records ?? []).filter((record) => record.kind === "candidate").map(identity));
  let added = 0;
  for (const record of uniqueExtracted) {
    if (existing.has(identity(record))) continue;
    const status = acceptedCandidate(record, accepted.candidates ?? []) ? "already-tracked" : "quarantined-awaiting-review";
    const wrapped = wrap(record, adapter.id, status);
    report.records.push(wrapped);
    if (status === "quarantined-awaiting-review") quarantine.records.push(wrapped);
    existing.add(identity(record));
    added++;
  }

  report.observations.push({
    sourceId: adapter.id,
    status: uniqueExtracted.length ? "ok" : "extract-failed",
    extracted: uniqueExtracted.length,
    added,
    pagesScanned: urls.length,
    ...(errors.length ? { errors } : {}),
  });
  recompute(report);
  quarantine.checkedAt = report.checkedAt;
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(quarantinePath, `${JSON.stringify(quarantine, null, 2)}\n`);
  console.log(`Liberal Victoria discovery: ${uniqueExtracted.length} parsed, ${added} added; automatic promotion disabled.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
