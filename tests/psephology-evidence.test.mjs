import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { independentFamilyCount, validatePsephologyRegistries } from "../scripts/validate-psephology-evidence.mjs";

const sources = JSON.parse(readFileSync(resolve("metadata/psephology-sources.json"), "utf8"));
const evidence = JSON.parse(readFileSync(resolve("metadata/psephology-evidence-2026.json"), "utf8"));

test("psephology registry validates and includes the agreed analyst core", () => {
  const result = validatePsephologyRegistries(sources, evidence);
  assert.deepEqual(result.errors, []);
  const ids = new Set(sources.sources.map((source) => source.id));
  for (const id of ["antony-green", "ben-raue-tally-room", "kevin-bonham", "casey-briggs-abc", "kos-samaras-redbridge", "mark-the-ballot"]) assert.ok(ids.has(id), id);
});

test("Ben Raue and The Tally Room are one source family, not two votes", () => {
  assert.equal(independentFamilyCount(sources, ["ben-raue-tally-room", "ben-raue-tally-room"]), 1);
});

test("poll-derived analyst output cannot silently become another poll/model input", () => {
  const bad = structuredClone(evidence);
  bad.records[0].modelUsage = "model_input";
  bad.records[0].reviewStatus = "approved-model-input";
  const result = validatePsephologyRegistries(sources, bad);
  assert.match(result.errors.join("\n"), /poll-derived analyst output cannot be a direct model input/i);
});

test("poll-derived evidence must declare its upstream dependency", () => {
  const bad = structuredClone(evidence);
  bad.records[1].upstreamEvidence = [];
  const result = validatePsephologyRegistries(sources, bad);
  assert.match(result.errors.join("\n"), /must declare upstream evidence/i);
});
