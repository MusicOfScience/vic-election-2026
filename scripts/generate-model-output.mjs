import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const checkOnly = process.argv.includes("--check");
const rootArg = process.argv.slice(2).find((argument) => argument !== "--check") || "model";
const root = path.resolve(rootArg);
const processed = path.join(root, "data", "processed");

function parseLine(line) {
  const cells = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"' && line[i + 1] === '"' && quoted) { value += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { cells.push(value); value = ""; }
    else value += char;
  }
  cells.push(value);
  return cells;
}

function csv(name) {
  const lines = fs.readFileSync(path.join(processed, name), "utf8").trim().split(/\r?\n/);
  const header = parseLine(lines.shift());
  return lines.map((line) => Object.fromEntries(parseLine(line).map((value, index) => {
    const numeric = value !== "" && Number.isFinite(Number(value));
    return [header[index], numeric ? Number(value) : value];
  })));
}

const manifest = JSON.parse(fs.readFileSync(path.join(processed, "experimental_forecast_2026.json"), "utf8"));
const output = {
  manifest,
  districts: csv("experimental_forecast_2026_districts.csv"),
  chamber: csv("experimental_forecast_2026_chamber.csv"),
  seatDistribution: csv("experimental_forecast_2026_seat_distribution.csv"),
  councilRegions: csv("experimental_forecast_2026_council_regions.csv"),
  council: csv("experimental_forecast_2026_council.csv"),
};
// Reject inconsistent releases before generating the app payload.
const assemblyParties = ["ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND"];
const probability = (value) => Number.isFinite(value) && value >= 0 && value <= 1;
const close = (a, b, tolerance = 0.00001) => Math.abs(a - b) < tolerance;
assert.equal(output.districts.length, 88, "Assembly must contain 88 districts");
assert.equal(new Set(output.districts.map((row) => row.district_id)).size, 88, "Duplicate Assembly district");
assert.deepEqual(output.chamber.map((row) => row.party).sort(), [...assemblyParties].sort(), "Unexpected Assembly party groups");
const expectedSeats = new Map(assemblyParties.map((party) => [party, 0]));
for (const seat of output.districts) {
  const wins = assemblyParties.map((party) => seat[`win_${party.toLowerCase()}`]);
  assert.ok(wins.every(probability) && close(wins.reduce((sum, win) => sum + win, 0), 1), `Invalid win frequencies in ${seat.district_name}`);
  const leader = wins[assemblyParties.indexOf(seat.favoured_party)];
  assert.ok(close(leader, Math.max(...wins)) && close(leader, seat.favoured_probability), `Invalid seat leader in ${seat.district_name}`);
  assemblyParties.forEach((party, index) => expectedSeats.set(party, expectedSeats.get(party) + wins[index]));
}
const hung = output.chamber[0].hung_probability;
let outcomeMass = hung;
for (const row of output.chamber) {
  assert.ok(close(row.mean, expectedSeats.get(row.party), .015), `District and chamber means differ for ${row.party}`);
  assert.ok(probability(row.majority_probability) && probability(row.hung_probability) && close(row.hung_probability, hung), `Invalid chamber outcomes for ${row.party}`);
  outcomeMass += row.majority_probability;
}
assert.ok(close(outcomeMass, 1), "Assembly majority and hung frequencies must sum to one");
assert.equal(output.seatDistribution.length, 89, "Labor seat distribution must cover 0–88 seats");
assert.ok(output.seatDistribution.every((row, index) => row.seats === index && probability(row.probability)), "Invalid Labor seat distribution");
assert.ok(close(output.seatDistribution.reduce((sum, row) => sum + row.probability, 0), 1), "Labor seat distribution must sum to one");
const laborMajority = output.seatDistribution.filter((row) => row.seats >= 45).reduce((sum, row) => sum + row.probability, 0);
assert.ok(close(laborMajority, output.chamber.find((row) => row.party === "ALP").majority_probability), "Labor majority frequency disagrees with its seat distribution");

const diagnostics = JSON.parse(fs.readFileSync(path.resolve("app/assembly-vote-diagnostics.generated.json"), "utf8"));
const manifestHash = createHash("sha256").update(fs.readFileSync(path.join(processed, "experimental_forecast_2026.json"))).digest("hex");
assert.equal(diagnostics.forecastSha256, manifestHash, "Vote diagnostics belong to a different forecast");
assert.equal(diagnostics.asOf, manifest.as_of, "Vote diagnostics date differs from the forecast");
assert.equal(diagnostics.simulations, manifest.simulations, "Vote diagnostic simulation count differs from the forecast");
assert.equal(new Set(diagnostics.pollIds).size, manifest.polling.poll_count, "Vote diagnostic poll lineage differs from the forecast");
assert.equal(Object.keys(diagnostics.seats).length, output.districts.length, "Vote diagnostics must cover every electorate");
for (const district of output.districts) {
  const row = diagnostics.seats[district.district_id];
  assert.ok(row && row.pair.length === 2 && new Set(row.pair).size === 2 && row.pair.every((party) => assemblyParties.includes(party)), `Invalid final pair in ${district.district_name}`);
  assert.ok(Number.isInteger(row.draws) && row.draws > 0 && row.draws <= manifest.simulations, `Invalid pair frequency in ${district.district_name}`);
  assert.ok(Number.isInteger(row.firstWins) && row.firstWins >= 0 && row.firstWins <= row.draws, `Invalid conditional wins in ${district.district_name}`);
}
for (const { mean, low, high } of [diagnostics.statewideLabor2pp, ...Object.values(diagnostics.seats).map((row) => row.firstShare)]) {
  assert.ok([mean, low, high].every((value) => probability(value / 100)) && low <= high, "Invalid vote-share summary");
}

const outputPath = path.resolve("app/model-output.generated.ts");
const generated = `// Generated by scripts/generate-model-output.mjs\nexport const modelOutput = ${JSON.stringify(output, null, 2)} as const;\n`;
if (checkOnly) {
  if (!fs.existsSync(outputPath) || fs.readFileSync(outputPath, "utf8") !== generated) throw new Error("generated model output is stale; run npm run forecast:refresh");
  console.log(`Verified ${output.districts.length} districts and ${output.councilRegions.length} Council regions.`);
} else {
  fs.writeFileSync(outputPath, generated);
  console.log(`Generated ${output.districts.length} districts and ${output.councilRegions.length} Council regions.`);
}
