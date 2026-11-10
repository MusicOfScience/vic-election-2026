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
    assert.ok(Math.abs(Math.max(...probabilities) - Number(district.favoured_probability)) < 0.00001,
      district.district_id + " leading-party probability mismatch");
  }
  for (const family of families) {
    const expected = districts.reduce((sum, d) => sum + Number(d["win_" + family]), 0);
    const reported = chamber.find((row) => row.party.toLowerCase() === family);
    assert.ok(reported, family + " missing chamber record");
    assert.ok(Math.abs(expected - Number(reported.mean)) < 0.015,
      family + " expected seats not consistent with chamber mean");
  }
});
