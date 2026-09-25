import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const json = (p) => JSON.parse(readFileSync(new URL(`../${p}`, import.meta.url), "utf8"));

test("2010 scoring preserves sealed artefacts and records the outcome boundary", () => {
  const prediction = json("model/data/validation/historical-replays/vic_la_2010-v2-prediction.json");
  const bundle = json("model/data/validation/historical-replays/vic_la_2010-v2-comparators-v2.json");
  const manifest = json("model/data/validation/historical-replays/vic_la_2010-v2-score-manifest.json");
  assert.equal(prediction.predictionSha256, "3d23e92d8aa0d8d4c6e522bbc07f529d614653c5d20aa68a952a96704804fd5d");
  assert.equal(bundle.bundleSha256, "a5e464f8d84ba7cdc4a198df43006eb64824f4dc71c1d789ce55bffbcbd76b13");
  assert.equal(prediction.outcomesLoaded, false);
  assert.equal(bundle.outcomesLoaded, false);
  assert.equal(manifest.outcomeBoundaryCrossedAfterPredictionAndComparatorVerification, true);
  assert.equal(manifest.forecastRegenerated, false);
});

test("2010 official final-pair artefact covers 88 districts and preserves unavailable pairs", () => {
  const rows = readFileSync(new URL("../model/data/processed/vec_2010_assembly_final_pairs.csv", import.meta.url), "utf8").trim().split("\n");
  assert.equal(rows.length, 89);
  const header = rows[0];
  assert.match(header, /final_pair_available/);
  assert.match(header, /target_outcome_dependency/);
  assert.equal(rows.filter((r) => /,True,/.test(r)).length, 44);
  assert.equal(rows.filter((r) => /,False,/.test(r)).length, 44);
  assert.doesNotMatch(rows.join("\n"), /ASSEMBLY_2010_TARGET|vec_2006_2010_same_boundary_tpp_swing/);
});

test("2010 score and aggregate status preserve the non-certifying 2018 boundary", () => {
  const score = json("model/data/validation/historical-replays/vic_la_2010-v2-score.json");
  const status = json("model/data/validation/historical-replays/historical-four-cycle-validation-status.json");
  assert.equal(score.outcomesLoaded, true);
  assert.equal(score.assembly.districtCount, 88);
  assert.equal(score.council.regions, 8);
  assert.equal(status.certifyingScoredCycles, 3);
  assert.match(status.nonCertifying2018, /post-hoc-v2-diagnostic/);
  assert.equal(status.completeForecastBacktest, "closed-incomplete-certifying-four-cycle-protocol");
  assert.equal(status.productionAuthorisation, "closed");
});
