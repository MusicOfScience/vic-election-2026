import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const forecast = read("../model/data/processed/experimental_forecast_2026.json");
const diagnostics = JSON.parse(read("../app/assembly-vote-diagnostics.generated.json"));
assert.equal(createHash("sha256").update(forecast).digest("hex"), diagnostics.forecastSha256);
assert.equal(JSON.parse(forecast).as_of, diagnostics.asOf);

const historical = read("../app/historical-data.generated.ts");
const baselines = JSON.parse(historical.split("export const historicalDistricts = ")[1].split(" as const;")[0]);
const csv = read("../model/data/processed/experimental_forecast_2026_districts.csv").trim().split(/\r?\n/);
const columns = csv.shift().split(",");
const seats = csv.map((line) => Object.fromEntries(line.split(",").map((value, index) => [columns[index], value])));
const byId = new Map(seats.map((seat) => [seat.district_id, seat]));
assert.equal(seats.length, 88);
assert.equal(byId.size, 88);
assert.equal(new Set(baselines.map((row) => row.districtId)).size, baselines.length);

const votes = baselines.reduce((sum, row) => sum + row.tppFormalVotes2022, 0);
const prior = baselines.reduce((sum, row) => sum + row.alpTpp2022 * row.tppFormalVotes2022, 0) / votes;
const target = diagnostics.statewideLabor2pp.mean;
const swing = target - prior;
const results = baselines.map((row) => {
  const seat = byId.get(row.districtId);
  assert.ok(seat, row.districtId);
  const share = row.alpTpp2022 + swing;
  return {
    district: row.districtName,
    swingLabor2pp: Number(share.toFixed(4)),
    swingLeader: share > 50 ? "ALP" : share < 50 ? "LIB_NAT" : "Tie",
    modelLeader: seat.favoured_party,
    modelFinalPair: seat.likely_final_pair,
  };
});
const tally = (key) => Object.fromEntries(
  [...new Set(results.map((row) => row[key]))].sort().map((party) =>
    [party, results.filter((row) => row[key] === party).length]),
);
const covered = new Set(baselines.map((row) => row.districtId));
console.log(JSON.stringify({
  asOf: diagnostics.asOf,
  baselineLabor2pp: prior,
  statewideLabor2pp: target,
  uniformSwingToLabor: swing,
  excludedDistricts: seats.filter((row) => !covered.has(row.district_id)).map((row) => row.district_name),
  uniformLeaders: tally("swingLeader"),
  modelLeaders: tally("modelLeader"),
  nonClassicFinalPairs: results.filter(({ modelFinalPair }) =>
    !["ALP–LIB_NAT", "LIB_NAT–ALP"].includes(modelFinalPair)).length,
  leaderDisagreements: results.filter((row) => row.modelLeader !== row.swingLeader).length,
  results,
}, null, 2));
