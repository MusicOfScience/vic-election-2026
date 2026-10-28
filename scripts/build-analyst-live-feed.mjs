import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function readJson(path) {
  return JSON.parse(readFileSync(resolve(path), "utf8"));
}

export function cleanHtml(value = "") {
  return value
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#8211;|&ndash;/gi, "–")
    .replace(/&#8212;|&mdash;/gi, "—")
    .replace(/&#8217;|&rsquo;/gi, "’")
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&quot;/gi, '"')
    .replace(/\s+/g, " ")
    .trim();
}

function normaliseUrl(href, baseUrl) {
  try {
    const url = new URL(href, baseUrl);
    url.hash = "";
    return url.href;
  } catch {
    return null;
  }
}

function isoDate(value) {
  if (!value) return null;
  const exact = String(value).match(/\b(20\d{2}-\d{2}-\d{2})\b/);
  if (exact) return exact[1];
  const parsed = Date.parse(String(value));
  return Number.isFinite(parsed) ? new Date(parsed).toISOString().slice(0, 10) : null;
}

function dateFromUrl(url) {
  const match = url.match(/\/(20\d{2})\/(\d{1,2})\/(\d{1,2})(?:\/|$)/);
  return match ? `${match[1]}-${match[2].padStart(2, "0")}-${match[3].padStart(2, "0")}` : null;
}

function firstArticleLink(block, baseUrl) {
  const heading = block.match(/<h[1-6]\b[^>]*>[\s\S]*?<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/h[1-6]>/i);
  if (heading) return { url: normaliseUrl(heading[1], baseUrl), title: cleanHtml(heading[2]) };
  const anchor = block.match(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/i);
  return anchor ? { url: normaliseUrl(anchor[1], baseUrl), title: cleanHtml(anchor[2]) } : null;
}

function articleDate(block, url) {
  const datetime = block.match(/<time\b[^>]*datetime=["']([^"']+)["'][^>]*>/i);
  if (datetime) return isoDate(datetime[1]);
  const timeText = block.match(/<time\b[^>]*>([\s\S]*?)<\/time>/i);
  if (timeText) return isoDate(cleanHtml(timeText[1]));
  const visible = cleanHtml(block).match(/\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}\b/i);
  return isoDate(visible?.[0]) ?? dateFromUrl(url);
}

export function discoverArticles(html, source) {
  const pattern = new RegExp(source.titlePattern, "i");
  const found = [];
  const seen = new Set();
  const blocks = [...html.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/gi)].map((m) => m[0]);

  for (const block of blocks) {
    const link = firstArticleLink(block, source.url);
    if (!link?.url || !link.title || !pattern.test(link.title) || seen.has(link.url)) continue;
    seen.add(link.url);
    found.push({
      sourceId: source.id,
      sourceName: source.displayName,
      publishedDate: articleDate(block, link.url),
      title: link.title,
      sourceUrl: link.url,
      status: "discovered-pending-review",
    });
  }

  if (!found.length) {
    for (const match of html.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
      const url = normaliseUrl(match[1], source.url);
      const title = cleanHtml(match[2]);
      if (!url || !title || !pattern.test(title) || seen.has(url)) continue;
      const publishedDate = dateFromUrl(url);
      if (!publishedDate) continue;
      seen.add(url);
      found.push({ sourceId: source.id, sourceName: source.displayName, publishedDate, title, sourceUrl: url, status: "discovered-pending-review" });
    }
  }

  return found;
}

async function fetchText(url) {
  const response = await fetch(url, {
    headers: { "user-agent": "vic-election-2026-analyst-monitor/1.0 (+https://github.com/MusicOfScience/vic-election-2026)" },
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.text();
}

function ageDays(date, now) {
  if (!date) return Number.POSITIVE_INFINITY;
  const ms = now.getTime() - new Date(`${date}T00:00:00Z`).getTime();
  return ms / 86400000;
}

export async function buildLiveFeed({ sources, reviewedRecords, existing, now = new Date(), fetcher = fetchText }) {
  const reviewedUrls = new Set(reviewedRecords.map((record) => record.sourceUrl).filter(Boolean));
  const recordsByUrl = new Map();
  const failures = [];
  let succeeded = 0;

  for (const source of sources) {
    try {
      const html = await fetcher(source.url);
      succeeded += 1;
      for (const record of discoverArticles(html, source)) {
        if (reviewedUrls.has(record.sourceUrl)) continue;
        if (record.publishedDate && ageDays(record.publishedDate, now) <= 45) recordsByUrl.set(record.sourceUrl, record);
      }
    } catch (error) {
      failures.push({ sourceId: source.id, message: error instanceof Error ? error.message : String(error) });
    }
  }

  for (const record of existing.records ?? []) {
    if (reviewedUrls.has(record.sourceUrl) || recordsByUrl.has(record.sourceUrl)) continue;
    if (record.publishedDate && ageDays(record.publishedDate, now) <= 45) recordsByUrl.set(record.sourceUrl, record);
  }

  const records = [...recordsByUrl.values()]
    .sort((a, b) => (b.publishedDate ?? "").localeCompare(a.publishedDate ?? "") || a.sourceName.localeCompare(b.sourceName))
    .slice(0, 24);

  return {
    schemaVersion: 1,
    generatedAt: now.toISOString(),
    policy: "discovery-only-no-automatic-promotion",
    refreshStatus: {
      mode: failures.length ? "partial-live-refresh" : "live-refresh",
      sourcesAttempted: sources.length,
      sourcesSucceeded: succeeded,
      sourcesFailed: failures.length,
      failures,
    },
    records,
  };
}

async function main() {
  const sources = readJson(arg("--sources", "metadata/analyst-live-sources.json"));
  const reviewed = readJson(arg("--reviewed", "metadata/psephology-evidence-2026.json"));
  const additions = readJson(arg("--additions", "metadata/analyst-live-reviewed-additions.json"));
  const output = arg("--output", "app/analyst-live.generated.json");
  const existing = readJson(output);
  const feed = await buildLiveFeed({
    sources: sources.sources,
    reviewedRecords: [...reviewed.records, ...additions.records],
    existing,
  });
  writeFileSync(resolve(output), `${JSON.stringify(feed, null, 2)}\n`);
  console.log(`Analyst live feed: ${feed.records.length} pending records; ${feed.refreshStatus.sourcesSucceeded}/${feed.refreshStatus.sourcesAttempted} sources refreshed.`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
