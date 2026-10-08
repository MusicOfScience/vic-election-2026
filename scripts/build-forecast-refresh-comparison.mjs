import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import assert from "node:assert/strict";

const root = resolve(new URL("..", import.meta.url).pathname);
const base = "8ddf08a1963973397e9d3b1869d658009282fd5f"; // Merged PR #123; fixed pre-admission forecast.
const old = (path) => execFileSync("git", ["show", `${base}:${path}`], { cwd: root, encoding: "utf8" });
const current = (path) => readFileSync(resolve(root, path), "utf8");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
function csv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = ""; if (row.some(Boolean)) rows.push(row); row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}
const path = "model/data/processed/experimental_forecast_2026.json";
const before = JSON.parse(old(path)), after = JSON.parse(current(path));
const parties = after.party_order;
const delta = (a, b) => ({ before: Number(a), after: Number(b), change: Number(b) - Number(a) });
const beforeEvents = csv(old("model/data/processed/poll_events_seed.csv"));
const afterEvents = csv(current("model/data/processed/poll_events_seed.csv"));
const beforeEstimates = csv(old("model/data/processed/poll_estimates_seed.csv"));
const afterEstimates = csv(current("model/data/processed/poll_estimates_seed.csv"));
assert.deepEqual(afterEvents.filter((row) => row.poll_id !== "freshwater_2026-09"), beforeEvents);
assert.deepEqual(afterEstimates.filter((row) => row.poll_id !== "freshwater_2026-09"), beforeEstimates);
assert.equal(afterEvents.length, beforeEvents.length + 1);
assert.equal(afterEstimates.length, beforeEstimates.length + 5);
assert.equal(old("model/config/experimental_forecast.yml").replace(/^as_of:.*$/m, ""), current("model/config/experimental_forecast.yml").replace(/^as_of:.*$/m, ""));
const historicalPaths = execFileSync("git", ["ls-tree", "-r", "--name-only", base, "model/data/validation/historical-replays"], { cwd: root, encoding: "utf8" }).trim().split("\n");
for (const p of historicalPaths) assert.equal(sha(execFileSync("git", ["show", `${base}:${p}`], { cwd: root })), sha(readFileSync(resolve(root, p))), `${p} changed`);

function chamber(kind) {
  const p = `model/data/processed/experimental_forecast_2026_${kind}.csv`;
  const a = new Map(csv(old(p)).map((row) => [row.party, row]));
  return Object.fromEntries(csv(current(p)).map((row) => [row.party,
    Object.fromEntries(["mean", "median", "lower80", "upper80", "majority_probability"].map((key) => [key, delta(a.get(row.party)[key], row[key])]))]));
}
const districtsPath = "model/data/processed/experimental_forecast_2026_districts.csv";
const oldDistricts = new Map(csv(old(districtsPath)).map((row) => [row.district_id, row]));
const districtChanges = csv(current(districtsPath)).map((row) => {
  const prior = oldDistricts.get(row.district_id);
  const wins = Object.fromEntries(parties.map((party) => [party, delta(prior[`win_${party.toLowerCase()}`], row[`win_${party.toLowerCase()}`])]));
  return { districtId: row.district_id, districtName: row.district_name, winProbabilities: wins,
    maximumAbsoluteProbabilityChange: Math.max(...Object.values(wins).map((item) => Math.abs(item.change))),
    favouredParty: { before: prior.favoured_party, after: row.favoured_party },
    likelyFinalPair: { before: prior.likely_final_pair, after: row.likely_final_pair } };
});
const materialThreshold = 0.05;
const material = districtChanges.filter((row) => row.maximumAbsoluteProbabilityChange >= materialThreshold).sort((a, b) => b.maximumAbsoluteProbabilityChange - a.maximumAbsoluteProbabilityChange);
const regionsPath = "model/data/processed/experimental_forecast_2026_council_regions.csv";
const oldRegions = new Map(csv(old(regionsPath)).map((row) => [row.region_id, row]));
const beforeReadiness = JSON.parse(old("metadata/release-readiness.generated.json"));
const afterReadiness = JSON.parse(current("metadata/release-readiness.generated.json"));
const report = {
  schemaVersion: 1, assessedAsOf: after.as_of, baseCommit: execFileSync("git", ["rev-parse", base], { cwd: root, encoding: "utf8" }).trim(),
  changeReason: "Owner-admitted September Freshwater observation and routine assessment-date advance; all model coefficients, seed and simulations unchanged. Deltas are total refresh effects, not causal estimates of one poll.",
  forecast: { path, sha256Before: sha(old(path)), sha256After: sha(current(path)), asOfBefore: before.as_of, asOfAfter: after.as_of, seed: after.seed, simulations: after.simulations },
  canonicalPolling: { totalEventsBefore: beforeEvents.length, totalEventsAfter: afterEvents.length, eligibleBefore: before.polling.poll_count, eligibleAfter: after.polling.poll_count, newestPollId: "freshwater_2026-09", effectiveDate: "2026-09-28", publicationDate: "2026-10-01", dataReleaseDate: "2026-10-02", sourceFamily: "freshwater" },
  statewidePrimary: Object.fromEntries(parties.map((party) => [party, Object.fromEntries(["mean", "lower80", "upper80"].map((key) => [key, delta(before.polling[key][party], after.polling[key][party])]))])),
  assembly: { families: chamber("chamber"), hungProbability: delta(before.assembly.hung_probability, after.assembly.hung_probability),
    materialDistrictThreshold: materialThreshold, materialDistrictRule: "Any canonical-family win probability changes by at least 0.05 (five percentage points); all qualifying districts listed, regardless of direction.",
    materialDistricts: material, allDistrictChanges: districtChanges, likelyFinalPairChanges: districtChanges.filter((row) => row.likelyFinalPair.before !== row.likelyFinalPair.after) },
  council: { families: chamber("council"), majorPartyNoControlProbability: delta(before.council.major_party_no_control_probability, after.council.major_party_no_control_probability),
    regions: csv(current(regionsPath)).map((row) => ({ regionId: row.region_id, regionName: row.region_name, families: Object.fromEntries(parties.map((party) => [party, Object.fromEntries(["primary", "mean", "at_least_one"].map((key) => [key, delta(oldRegions.get(row.region_id)[`${key}_${party.toLowerCase()}`], row[`${key}_${party.toLowerCase()}`])]))])) })) },
  releaseGates: Object.fromEntries(Object.entries(afterReadiness.gates).map(([id, gate]) => [id, { before: beforeReadiness.gates[id].passed, after: gate.passed }])),
  integrity: { historicalFrozenArtifactsUnchanged: true, historicalArtifactsChecked: historicalPaths.length, existingPollRowsUnchanged: true, modelParametersUnchanged: true, productionAuthorisation: false },
};
const output = "metadata/forecast-refresh-2026-10-08.json";
const payload = `${JSON.stringify(report, null, 2)}\n`;
if (process.argv.includes("--check")) assert.equal(current(output), payload);
else writeFileSync(resolve(root, output), payload);
console.log(`Refresh comparison: ${material.length} material districts; ${report.assembly.likelyFinalPairChanges.length} final-pair changes; ${historicalPaths.length} historical artefacts unchanged; forecast ${report.forecast.sha256After}.`);
