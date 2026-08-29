import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { buildCoverageReport } from "../scripts/build-poll-coverage-report.mjs";

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i += 1; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i += 1;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}

const root = resolve(new URL("..", import.meta.url).pathname);
const ledger = JSON.parse(readFileSync(resolve(root, "metadata/poll-coverage-ledger-2026.json"), "utf8"));
const events = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));
const research = JSON.parse(readFileSync(resolve(root, "metadata/research-source-evidence-2026.json"), "utf8"));

test("poll coverage ledger separates published coverage from comparable/model-eligible coverage", () => {
  const report = buildCoverageReport({ ledger, events, manualRecords: manual.records, researchRecords: research.records });

  assert.equal(report.externalBenchmark.publishedAssemblyPolls, 60);
  assert.equal(report.externalBenchmark.pollingOrganisations, 8);
  assert.equal(report.policy.comparabilityBreak, "2026-02-10");
  assert.equal(report.repository.sourceFamiliesDeclared, 8);
  assert.equal(report.repository.registryEvents, 11);
  assert.equal(report.repository.modelEligibleEvents, 9);
  assert.equal(report.repository.stagedPollRecords, 2);
  assert.equal(report.integrity.allDeclaredCanonicalIdsExist, true);
  assert.equal(report.integrity.declaredCanonicalIdsAreUnique, true);
});

test("coverage ledger makes missing comparable polling actionable without imputing old One Nation support", () => {
  const byId = Object.fromEntries(ledger.sourceFamilies.map((family) => [family.id, family]));

  assert.equal(byId["wolf-smith"].coverageClass, "historical-non-comparable");
  assert.match(byId["wolf-smith"].exclusionReason, /One Nation was not separately reported/i);
  assert.equal(byId["resolve-strategic"].canonicalModelEligiblePollIds.length, 0);
  assert.ok(byId["resolve-strategic"].actionableGaps.length > 0);
  assert.equal(byId["yougov-common-threads"].actionableGaps[0].sampleSize, 4003);
  assert.deepEqual(byId["yougov-common-threads"].actionableGaps[0].seatProjection, { LIB_NAT: 39, ALP: 29, ONP: 17, GRN: 3 });
  assert.ok(byId["freshwater"].actionableGaps.length >= 3);
  assert.ok(byId["redbridge-accent"].actionableGaps.some((gap) => gap.fieldworkEnd === "2026-08-01"));
});
