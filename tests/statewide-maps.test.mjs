import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { gzipSync } from "node:zlib";

test("statewide map paths match the 2026 district and region universe", async () => {
  const archive = await readFile(new URL("../app/election-state-maps.generated.json", import.meta.url));
  const maps = JSON.parse(archive);
  const csv = await readFile(new URL("../model/data/processed/district_region_membership_2026.csv", import.meta.url), "utf8");
  const rows = csv.trim().split("\n").slice(1).map(line => line.split(","));
  const electorates = [new Set(rows.map(row => row[0])), new Set(rows.map(row => row[1]))];
  assert.match(maps.sourceSha256, /^[a-f\d]{64}$/);
  assert.ok(gzipSync(archive).byteLength < 100_000);
  for (const [index, item] of [maps.assembly, maps.council].entries()) {
    assert.match(item.viewBox, /^0 0 900 [\d.]+$/);
    assert.equal(item.areas.length, index === 0 ? 88 : 8);
    assert.deepEqual(new Set(item.areas.map(area => area.name)), electorates[index]);
    assert.equal(new Set(item.areas.map(area => area.boundaryCode)).size, item.areas.length);
    assert.equal(new Set(item.areas.map(area => area.id)).size, item.areas.length);
    assert.ok(item.areas.every(area => /^M[\d., MZ]+Z$/.test(area.path)));
  }
});
