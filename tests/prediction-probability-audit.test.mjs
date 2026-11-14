import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
function loadRows(path) {
  const rows = readFileSync(resolve(root, path), "utf8").trim().split(/\r?\n/);
  const fields = rows.shift().split(",");
  return rows.map((row) => Object.fromEntries(row.split(",").map((value, i) => [fields[i], value])));
}

test("district party-winning mass reconciles with chamber mean without independence assumptions", () => {
  const districts = loadRows("model/data/processed/experimental_forecast_2026_districts.csv");
  const chamber = loadRows("model/data/processed/experimental_forecast_2026_chamber.csv");
  const families = ["alp", "lib_nat", "onp", "grn", "oth_ind"];
  assert.equal(districts.length, 88);
  assert.equal(chamber.length, 5);
  assert.equal(new Set(districts.map((d) => d.district_id)).size, 88);
  assert.equal(new Set(districts.map((d) => d.region_name)).size, 8);
  for (const district of districts) {
    const probabilities = families.map((family) => Number(district["win_" + family]));
    assert.ok(probabilities.every((p) => Number.isFinite(p) && p >= 0 && p <= 1), district.district_id);
    assert.ok(Math.abs(probabilities.reduce((sum, p) => sum + p, 0) - 1) < 0.00001, district.district_id);
    const leader = district.favoured_party.toLowerCase();
    assert.ok(families.includes(leader), district.district_id + " unknown leading group");
    assert.equal(Number(district["win_" + leader]), Number(district.favoured_probability),
      district.district_id + " leading-party label does not match its win frequency");
    assert.ok(Math.abs(Math.max(...probabilities) - Number(district.favoured_probability)) < 0.00001,
      district.district_id + " leading-party probability mismatch");
  }
  const hung = Number(chamber[0].hung_probability);
  const majorities = chamber.map((row) => Number(row.majority_probability));
  assert.ok([hung, ...majorities].every((p) => Number.isFinite(p) && p >= 0 && p <= 1));
  assert.ok(chamber.every((row) => Number(row.hung_probability) === hung));
  assert.ok(Math.abs(majorities.reduce((sum, p) => sum + p, hung) - 1) < 0.00001);
  for (const family of families) {
    const expected = districts.reduce((sum, d) => sum + Number(d["win_" + family]), 0);
    const reported = chamber.find((row) => row.party.toLowerCase() === family);
    assert.ok(reported, family + " missing chamber record");
    assert.ok(Math.abs(expected - Number(reported.mean)) < 0.015,
      family + " expected seats not consistent with chamber mean");
  }
});

test("vote outlook uses the exact published forecast and poll registry", async () => {
  const { pollSeries } = await import("../app/poll-data.generated.ts");
  const { modelOutput } = await import("../app/model-output.generated.ts");
  const diagnostics = JSON.parse(readFileSync(resolve(root, "app/assembly-vote-diagnostics.generated.json"), "utf8"));
  const pollIds = new Set(pollSeries.map((poll) => poll.id));
  assert.equal(diagnostics.pollIds.length, modelOutput.manifest.polling.poll_count);
  assert.ok(diagnostics.pollIds.every((id) => pollIds.has(id)));
  assert.equal(diagnostics.asOf, modelOutput.manifest.as_of);
  assert.equal(Object.keys(diagnostics.seats).length, 88);
  for (const district of modelOutput.districts) {
    const { pair, draws, firstWins } = diagnostics.seats[district.district_id];
    assert.ok(draws >= district.final_pair_probability * diagnostics.simulations - 1e-9);
    assert.ok(firstWins <= draws);
    assert.equal(new Set(pair).size, 2);
  }
});
