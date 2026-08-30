import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { classifyContest, loadContestUniverse } from "./candidate-contests.mjs";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const registry = JSON.parse(readFileSync(resolve(root, "metadata/candidates-2026.json"), "utf8"));
const provisional = JSON.parse(readFileSync(resolve(root, "metadata/provisional-candidate-evidence-2026.json"), "utf8"));
const contestUniverse = loadContestUniverse(root);
const allowed = new Set(["announced", "endorsed", "nominated", "withdrawn", "disendorsed", "elected", "not-elected"]);
const official = new Set(["nominated", "withdrawn", "elected", "not-elected"]);
const keys = new Set();
for (const candidate of registry.candidates) {
  if (!candidate.name || !candidate.contest || !candidate.status || !candidate.sourceUrl) throw new Error("candidate registry: incomplete record");
  if (!allowed.has(candidate.status)) throw new Error(`candidate registry: unsupported status ${candidate.status}`);
  const key = `${candidate.contest}|${candidate.name}`.toLowerCase();
  if (keys.has(key)) throw new Error(`candidate registry: duplicate ${candidate.name} / ${candidate.contest}`);
  keys.add(key);
  if (official.has(candidate.status) && candidate.sourceAuthority !== "VEC") throw new Error(`candidate registry: ${candidate.name} cannot be ${candidate.status} without VEC authority`);
  if (!classifyContest(candidate.contest, contestUniverse)) throw new Error(`candidate registry: unknown contest ${candidate.contest}`);
}
const provisionalIds = new Set();
const assemblyContests = new Set();
const councilRegions = new Set();
for (const candidate of provisional.records) {
  if (!candidate.id || !candidate.name || !candidate.contest || !candidate.party || !candidate.sourceUrl) throw new Error("provisional candidate evidence: incomplete record");
  if (candidate.status !== "quarantined-awaiting-review" || candidate.automaticPromotion !== false) throw new Error(`provisional candidate evidence: ${candidate.name} bypasses quarantine`);
  if (!new Set(["announced", "endorsed"]).has(candidate.candidateStatus)) throw new Error(`provisional candidate evidence: ${candidate.name} carries unsupported provisional status`);
  if (provisionalIds.has(candidate.id)) throw new Error(`provisional candidate evidence: duplicate id ${candidate.id}`);
  provisionalIds.add(candidate.id);
  const classification = classifyContest(candidate.contest, contestUniverse);
  if (!classification) throw new Error(`provisional candidate evidence: unknown contest ${candidate.contest}`);
  if (classification.chamber === "council") councilRegions.add(classification.canonicalContest);
  else assemblyContests.add(classification.canonicalContest);
}
if (provisional.summary.records !== provisional.records.length) throw new Error("provisional candidate evidence: record summary mismatch");
if (provisional.summary.assemblyContests !== assemblyContests.size) throw new Error("provisional candidate evidence: Assembly coverage summary mismatch");
if (provisional.summary.councilRegions !== councilRegions.size) throw new Error("provisional candidate evidence: Council coverage summary mismatch");
console.log(`Candidate evidence valid: ${registry.candidates.length} accepted; ${provisional.records.length} quarantined across ${assemblyContests.size}/88 Assembly districts and ${councilRegions.size}/8 Council regions; official nominations remain VEC-only.`);
