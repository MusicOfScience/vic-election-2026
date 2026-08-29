import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function readJson(path) { return JSON.parse(readFileSync(resolve(path), "utf8")); }
function writeJson(path, value) { writeFileSync(resolve(path), `${JSON.stringify(value, null, 2)}\n`); }

export function stageManualEvidence(report, quarantine, manual) {
  const existing = new Set((report.records ?? []).map((record) => record.id));
  const additions = [];
  for (const record of manual.records ?? []) {
    if (!record.id || !record.sourceId || !record.sourceUrl || !record.kind) throw new Error("manual evidence: incomplete record");
    if (record.status !== "quarantined-awaiting-review" || record.automaticPromotion !== false) throw new Error(`manual evidence: ${record.id} must remain quarantined with automaticPromotion=false`);
    if (existing.has(record.id)) continue;
    report.records.push(record);
    quarantine.records.push(record);
    existing.add(record.id);
    additions.push(record);
  }
  if (additions.length) {
    report.observations.push({
      sourceId: "manual-blocked-source-evidence",
      status: "manual-evidence-staged",
      extracted: additions.length,
      added: additions.length,
      recordIds: additions.map((record) => record.id),
    });
  }
  const records = report.records ?? [];
  const observations = report.observations ?? [];
  report.summary = {
    sourcesScanned: observations.filter((observation) => observation.sourceId !== "manual-blocked-source-evidence").length,
    recordsExtracted: records.length,
    candidates: records.filter((record) => record.kind === "candidate").length,
    polls: records.filter((record) => record.kind?.startsWith("poll")).length,
    quarantined: records.filter((record) => record.status === "quarantined-awaiting-review").length,
    alreadyTracked: records.filter((record) => record.status === "already-tracked").length,
    extractionFailures: observations.filter((observation) => observation.status === "extract-failed").length,
  };
  quarantine.checkedAt = report.checkedAt;
  return additions;
}

function main() {
  const reportPath = arg("--report", "source-discovery-report.json");
  const quarantinePath = arg("--quarantine", "source-discovery-quarantine.json");
  const manualPath = arg("--manual", "metadata/manual-source-evidence-2026.json");
  const report = readJson(reportPath);
  const quarantine = readJson(quarantinePath);
  const manual = readJson(manualPath);
  const additions = stageManualEvidence(report, quarantine, manual);
  writeJson(reportPath, report);
  writeJson(quarantinePath, quarantine);
  console.log(`Manual evidence staging: ${additions.length} quarantined record(s) added; automatic promotion disabled.`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
