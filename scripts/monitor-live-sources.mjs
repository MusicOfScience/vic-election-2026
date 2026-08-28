import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const adaptersPath = resolve(root, "metadata/live-source-adapters.json");

function arg(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function canonicaliseHtml(html) {
  return html
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/\s+/g, " ")
    .trim();
}

export function validateMarkers(text, markers = []) {
  const missing = markers.filter((marker) => !text.toLowerCase().includes(marker.toLowerCase()));
  return { passed: missing.length === 0, missing };
}

export function classifyObservation({ valid, acceptedFingerprint, observedFingerprint }) {
  if (!valid) return "invalid-quarantined";
  if (!acceptedFingerprint) return "observed-unbaselined";
  if (acceptedFingerprint === observedFingerprint) return "healthy";
  return "changed-quarantined";
}

async function inspect(adapter, prior) {
  const started = new Date().toISOString();
  try {
    const response = await fetch(adapter.url, {
      headers: { "user-agent": "vic-election-forecast-source-monitor/1.0 (+https://github.com/MusicOfScience/vic-election-2026)" },
      redirect: "follow",
      signal: AbortSignal.timeout(adapter.timeoutMs ?? 20_000),
    });
    const body = await response.text();
    const canonical = canonicaliseHtml(body);
    const markers = validateMarkers(canonical, adapter.expectedMarkers);
    const sizePassed = canonical.length >= (adapter.minimumCanonicalBytes ?? 500);
    const valid = response.ok && markers.passed && sizePassed;
    const observedFingerprint = sha256(canonical);
    return {
      id: adapter.id,
      url: adapter.url,
      checkedAt: started,
      httpStatus: response.status,
      contentType: response.headers.get("content-type"),
      canonicalBytes: Buffer.byteLength(canonical),
      observedFingerprint,
      acceptedFingerprint: prior?.acceptedFingerprint ?? null,
      status: classifyObservation({ valid, acceptedFingerprint: prior?.acceptedFingerprint, observedFingerprint }),
      validation: { httpOk: response.ok, markersPassed: markers.passed, missingMarkers: markers.missing, sizePassed },
      critical: adapter.critical,
      promotionPolicy: adapter.promotionPolicy,
    };
  } catch (error) {
    return {
      id: adapter.id,
      url: adapter.url,
      checkedAt: started,
      status: "fetch-failed",
      critical: adapter.critical,
      acceptedFingerprint: prior?.acceptedFingerprint ?? null,
      validation: { httpOk: false, markersPassed: false, missingMarkers: adapter.expectedMarkers, sizePassed: false },
      error: error instanceof Error ? error.message : String(error),
      promotionPolicy: adapter.promotionPolicy,
    };
  }
}

async function main() {
  const config = JSON.parse(readFileSync(adaptersPath, "utf8"));
  const statePath = resolve(root, arg("--state") ?? "metadata/live-source-state.json");
  const reportPath = resolve(root, arg("--report") ?? "live-source-report.json");
  const prior = existsSync(statePath) ? JSON.parse(readFileSync(statePath, "utf8")) : { sources: [] };
  const priorById = new Map((prior.sources ?? []).map((source) => [source.id, source]));
  const observations = [];
  const monitoredAdapters = config.adapters.filter((adapter) => adapter.monitor !== false);
  for (const adapter of monitoredAdapters) observations.push(await inspect(adapter, priorById.get(adapter.id)));
  const unhealthy = observations.filter((item) => ["fetch-failed", "invalid-quarantined"].includes(item.status));
  const quarantined = observations.filter((item) => item.status.endsWith("quarantined"));
  const report = {
    schemaVersion: 1,
    checkedAt: new Date().toISOString(),
    policy: "observe-validate-quarantine-review-promote",
    automaticPromotion: false,
    summary: {
      adapters: observations.length,
      healthy: observations.filter((item) => item.status === "healthy").length,
      unbaselined: observations.filter((item) => item.status === "observed-unbaselined").length,
      quarantined: quarantined.length,
      unhealthy: unhealthy.length,
    },
    observations,
  };
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Live source monitor: ${report.summary.healthy} healthy, ${report.summary.unbaselined} unbaselined, ${report.summary.quarantined} quarantined, ${report.summary.unhealthy} unhealthy.`);
  if (process.argv.includes("--fail-on-unhealthy") && unhealthy.some((item) => item.critical)) process.exitCode = 2;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
