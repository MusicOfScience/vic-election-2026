import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { gunzipSync } from "node:zlib";

const audit = JSON.parse(readFileSync(new URL("../metadata/vec-2014-2022-council-evidence-audit.json", import.meta.url), "utf8"));

function countNewlines(buffer) {
  let count = 0;
  for (const byte of buffer) if (byte === 10) count++;
  return count;
}

test("reconciles official Council evidence for all 24 harvested region-cycle contests", () => {
  assert.deepEqual(audit.coverage.cycles, ["vic_lc_2014", "vic_lc_2018", "vic_lc_2022"]);
  assert.equal(audit.coverage.regionCycleContests, 24);
  assert.equal(audit.coverage.regionsPerCycle, 8);
  assert.equal(audit.coverage.candidateRows, 1185);
  assert.equal(audit.coverage.countEvents, 5066);
  assert.equal(audit.coverage.countTotalRows, 268994);
  assert.equal(audit.coverage.electedCandidates, 120);
  assert.equal(audit.coverage.fingerprintedSources, 48);
  assert.ok(Object.values(audit.acceptance).every(Boolean));
  assert.equal(audit.regions.length, 24);
  assert.ok(audit.regions.every((region) => region.elected.length === 5));
});

test("stores each complete published count-total ledger losslessly", () => {
  for (const year of [2014, 2018, 2022]) {
    const expectedRows = audit.regions
      .filter((region) => region.electionId === `vic_lc_${year}`)
      .reduce((sum, region) => sum + region.countTotalRows, 0);
    const contents = gunzipSync(readFileSync(new URL(`../model/data/processed/vec_${year}_council_preference_counts.csv.gz`, import.meta.url)));
    assert.match(contents.subarray(0, 300).toString("utf8"), /^election_id,region_id,region_name,count_number,count_detail,/);
    assert.equal(countNewlines(contents) - 1, expectedRows);
  }
});

test("keeps unresolved Council evidence fail-closed", () => {
  assert.match(audit.limitations.join(" "), /2010 Legislative Council/);
  assert.equal(audit.modelImpact.changesCurrentForecast, false);
  assert.equal(audit.modelImpact.historicalReplayEligible, false);
  assert.equal(audit.modelImpact.probabilityCalibrationReady, false);
  assert.equal(audit.modelImpact.automaticGateOpening, false);
});
