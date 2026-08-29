import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { buildCoverageReport } from "../scripts/build-poll-coverage-report.mjs";

function parseCsv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) { const ch = text[i]; if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i += 1; } else if (ch === '"') quoted = !quoted; else if (ch === "," && !quoted) { row.push(cell); cell = ""; } else if ((ch === "\n" || ch === "\r") && !quoted) { if (ch === "\r" && text[i + 1] === "\n") i += 1; row.push(cell); cell = ""; if (row.some((value) => value !== "")) rows.push(row); row = []; } else cell += ch; }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows; return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}

const root = resolve(new URL("..", import.meta.url).pathname);
const ledger = JSON.parse(readFileSync(resolve(root, "metadata/poll-coverage-ledger-2026.json"), "utf8"));
const events = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));
const primary = JSON.parse(readFileSync(resolve(root, "metadata/primary-source-evidence-2026.json"), "utf8"));
const research = JSON.parse(readFileSync(resolve(root, "metadata/research-source-evidence-2026.json"), "utf8"));

test("poll coverage ledger separates published coverage from comparable/model-eligible coverage", () => {
  const report = buildCoverageReport({ ledger, events, manualRecords: manual.records, primaryRecords: primary.records, researchRecords: research.records });
  assert.equal(report.externalBenchmark.publishedAssemblyPolls, 60);
  assert.equal(report.externalBenchmark.pollingOrganisations, 8);
  assert.equal(report.repository.sourceFamiliesDeclared, 8);
  assert.equal(report.repository.registryEvents, 11);
  assert.equal(report.repository.modelEligibleEvents, 9);
  assert.equal(report.repository.stagedPollRecords, manual.records.length + primary.records.length + research.records.length);
  assert.equal(report.repository.declaredGapsResolvedByStaging, 5);
  assert.equal(report.repository.actionableGapItems, 0);
  assert.equal(report.repository.currentSourceFamiliesWithActionableGaps, 0);
  assert.equal(report.integrity.allDeclaredCanonicalIdsExist, true);
});

test("staged evidence resolves dated coverage gaps without pretending it is model eligible", () => {
  const report = buildCoverageReport({ ledger, events, manualRecords: manual.records, primaryRecords: primary.records, researchRecords: research.records });
  const resolved = report.stagedCoverageResolutions.map((item) => item.proposedModelPollId).sort();
  assert.deepEqual(resolved, ["freshwater_2026-02", "freshwater_2026-03", "freshwater_2026-08", "redbridge_accent_2026-08", "yougov_common_threads_mrp_2026-07"]);
  assert.deepEqual(report.actionableGaps, []);
});

test("coverage ledger keeps old non-comparable polling out of the current five-way model", () => {
  const byId = Object.fromEntries(ledger.sourceFamilies.map((family) => [family.id, family]));
  assert.equal(byId["wolf-smith"].coverageClass, "historical-non-comparable");
  assert.match(byId["wolf-smith"].exclusionReason, /One Nation was not separately reported/i);
  assert.equal(byId["resolve-strategic"].canonicalModelEligiblePollIds.length, 0);
  assert.equal(byId["resolve-strategic"].actionableGaps.length, 0);
  assert.ok(byId["resolve-strategic"].familyEvidence.some((item) => item.id === "resolve-vic-2026-may-jun"));
});

test("Freshwater staged records now derive from parsed first-party workbooks", () => {
  const freshwater = primary.records.filter((record) => record.pollster === "Freshwater Strategy");
  assert.equal(freshwater.length, 3);
  assert.deepEqual(freshwater.map((record) => record.sampleSize), [1030, 1062, 1020]);
  assert.ok(freshwater.every((record) => record.sourceTier === "primary_pollster"));
  assert.ok(freshwater.every((record) => /primary-workbook-parsed/.test(record.verificationStatus)));
  assert.equal(research.records.filter((record) => record.pollster === "Freshwater Strategy").length, 0);
  const august = freshwater.find((record) => record.fieldworkEnd === "2026-08-03");
  assert.deepEqual(august.registryReconciliation.missingReportedParties, ["GRN", "OTH"]);
});

test("YouGov Common Threads keeps statewide polling and seat-model output in one dependency family", () => {
  const record = research.records.find((item) => item.pollster === "YouGov");
  assert.ok(record);
  assert.equal(record.sampleSize, 4003);
  assert.equal(record.effectiveSampleSize, 2901);
  assert.equal(record.primaryMethodologyFieldworkEnd, "2026-07-09");
  assert.equal(record.methodologyReconciliation.secondaryReportedFieldworkEnd, "2026-07-10");
  assert.equal(record.sourceTier, "reputable_secondary");
  assert.equal(record.methodologySourceTier, "primary_pollster");
  assert.match(record.verificationStatus, /primary-methodology-captured/);
  assert.match(record.questionnaireOrder, /before the later issue and Treaty questions/i);
  assert.deepEqual(record.seatModelProjection, { coalition: 39, alp: 29, oneNation: 17, greens: 3, totalSeats: 88, role: "external-seat-model-comparison-only" });
  assert.match(record.dependencyPolicy, /never be counted as independent polling observations/i);
});
