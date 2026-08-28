import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const registry = JSON.parse(readFileSync(resolve(root, "metadata/candidates-2026.json"), "utf8"));
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
}
console.log(`Candidate registry valid: ${registry.candidates.length} tracked candidates; official nominations remain VEC-only.`);
