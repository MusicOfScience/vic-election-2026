import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { buildAnalystComparison } from "../scripts/build-analyst-comparison.mjs";

const model = JSON.parse(readFileSync(resolve("model/data/processed/experimental_forecast_2026.json"), "utf8"));
const sources = JSON.parse(readFileSync(resolve("metadata/psephology-sources.json"), "utf8"));
const evidence = JSON.parse(readFileSync(resolve("metadata/psephology-evidence-2026.json"), "utf8"));
const [header, ...rows] = readFileSync(resolve("model/data/processed/experimental_forecast_2026_chamber.csv"), "utf8").trim().split(/\r?\n/).map((line) => line.split(","));
const chamber = rows.map((row) => Object.fromEntries(header.map((key, index) => [key, row[index]])));

test("analyst comparison is diagnostic and adds no direct model inputs", () => {
  const report = buildAnalystComparison(model, chamber, sources, evidence);
  assert.equal(report.policy, "comparison-not-averaging");
  assert.equal(report.summary.directModelInputsAdded, 0);
  assert.equal(report.summary.evidenceRecords, evidence.records.length);
  assert.ok(report.records.some((record) => record.analyst === "Antony Green" && record.comparisonMode === "structural-check"));
});

test("Kevin Bonham poll aggregate is compared rather than counted as another poll", () => {
  const report = buildAnalystComparison(model, chamber, sources, evidence);
  const bonham = report.records.find((record) => record.evidenceId === "kevin-bonham-2026-07-17-victoria");
  assert.equal(bonham.comparisonMode, "poll-aggregate-comparator");
  assert.equal(bonham.independenceAssessment, "dependent");
  assert.equal(typeof bonham.modelMinusAnalystPp.coalition, "number");
});

test("Ben Raue seat projection is labelled as a non-like-for-like scenario", () => {
  const report = buildAnalystComparison(model, chamber, sources, evidence);
  const raue = report.records.find((record) => record.evidenceId === "ben-raue-2026-07-27-vote-to-seat");
  assert.equal(raue.comparisonMode, "scenario-seat-comparator");
  assert.match(raue.caution, /not a like-for-like/i);
});
