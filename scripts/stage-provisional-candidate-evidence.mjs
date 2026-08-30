import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { classifyContest, loadContestUniverse } from "./candidate-contests.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const arg = (name, fallback = null) => { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : fallback; };
const input = resolve(root, arg("--input", "source-discovery-quarantine.json"));
const sourceId = arg("--source-id");
const asOf = arg("--as-of");
if (!sourceId || !asOf) throw new Error("usage: --source-id <adapter-id> --as-of <ISO timestamp> [--input <quarantine.json>]");

const ledgerPath = resolve(root, "metadata/provisional-candidate-evidence-2026.json");
const ledger = JSON.parse(readFileSync(ledgerPath, "utf8"));
const quarantine = JSON.parse(readFileSync(input, "utf8"));
const incoming = (quarantine.records ?? []).filter((record) => record.kind === "candidate" && record.sourceId === sourceId);
if (!incoming.length) throw new Error(`no quarantined candidate records found for ${sourceId}`);
if (incoming.some((record) => record.status !== "quarantined-awaiting-review" || record.automaticPromotion !== false)) throw new Error("candidate staging accepts quarantined, non-promotable evidence only");

const identity = (record) => `${record.contest}|${record.name}`.toLowerCase();
const merged = new Map((ledger.records ?? []).map((record) => [identity(record), record]));
for (const record of incoming) merged.set(identity(record), record);
ledger.records = [...merged.values()].sort((a, b) => a.contest.localeCompare(b.contest) || a.party.localeCompare(b.party) || a.name.localeCompare(b.name));
ledger.evidenceAsOf = asOf;

const universe = loadContestUniverse(root);
const assembly = new Set();
const council = new Set();
for (const record of ledger.records) {
  const classification = classifyContest(record.contest, universe);
  if (!classification) throw new Error(`unknown contest: ${record.contest}`);
  (classification.chamber === "assembly" ? assembly : council).add(classification.canonicalContest);
}
ledger.summary = {
  records: ledger.records.length,
  assemblyContests: assembly.size,
  assemblyDistrictsTotal: 88,
  councilRegions: council.size,
  sourceFamilies: new Set(ledger.records.map((record) => record.sourceId)).size,
};
writeFileSync(ledgerPath, `${JSON.stringify(ledger, null, 2)}\n`);
console.log(`Staged ${incoming.length} ${sourceId} records; durable quarantine now holds ${ledger.records.length} records from ${ledger.summary.sourceFamilies} source families.`);
