import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function arg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

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

function stagedResolution(family, gap, staged) {
  if (!gap.fieldworkStart || !gap.fieldworkEnd) return null;
  return staged.find((record) =>
    String(record.sourceId ?? "").startsWith(family.id)
    && record.fieldworkStart === gap.fieldworkStart
    && record.fieldworkEnd === gap.fieldworkEnd,
  ) ?? null;
}

export function buildCoverageReport({ ledger, events, manualRecords = [], primaryRecords = [], researchRecords = [] }) {
  const eventIds = new Set(events.map((event) => event.poll_id));
  const eligible = events.filter((event) => String(event.model_eligible).toLowerCase() === "true");
  const declaredIds = ledger.sourceFamilies.flatMap((family) => family.canonicalModelEligiblePollIds ?? []);
  const unknownDeclaredIds = declaredIds.filter((id) => !eventIds.has(id));
  const duplicateDeclaredIds = declaredIds.filter((id, index) => declaredIds.indexOf(id) !== index);
  const staged = [...manualRecords, ...primaryRecords, ...researchRecords].filter((record) => record.kind === "poll");
  const declaredGaps = ledger.sourceFamilies.flatMap((family) =>
    (family.actionableGaps ?? []).map((gap) => ({ family, gap })),
  );
  const stagedCoverageResolutions = declaredGaps.flatMap(({ family, gap }) => {
    const record = stagedResolution(family, gap, staged);
    return record ? [{ sourceFamilyId: family.id, sourceFamily: family.label, evidenceId: record.id, proposedModelPollId: record.proposedModelPollId ?? null, fieldworkStart: gap.fieldworkStart, fieldworkEnd: gap.fieldworkEnd, status: record.status }] : [];
  });
  const actionable = declaredGaps.flatMap(({ family, gap }) =>
    stagedResolution(family, gap, staged) ? [] : [{ sourceFamilyId: family.id, sourceFamily: family.label, ...gap }],
  );
  const representedFamilies = ledger.sourceFamilies.filter((family) => (family.canonicalModelEligiblePollIds ?? []).length > 0);
  const actionableFamilyIds = new Set(actionable.map((gap) => gap.sourceFamilyId));

  return {
    schemaVersion: 1,
    reviewedAt: ledger.reviewedAt,
    purpose: ledger.purpose,
    policy: ledger.policy,
    externalBenchmark: ledger.externalCoverageBenchmark,
    repository: {
      registryEvents: events.length,
      modelEligibleEvents: eligible.length,
      stagedPollRecords: staged.length,
      sourceFamiliesDeclared: ledger.sourceFamilies.length,
      sourceFamiliesWithCanonicalEligiblePolling: representedFamilies.length,
      currentSourceFamiliesWithActionableGaps: actionableFamilyIds.size,
      actionableGapItems: actionable.length,
      declaredGapsResolvedByStaging: stagedCoverageResolutions.length,
    },
    integrity: {
      allDeclaredCanonicalIdsExist: unknownDeclaredIds.length === 0,
      declaredCanonicalIdsAreUnique: duplicateDeclaredIds.length === 0,
      unknownDeclaredCanonicalIds: unknownDeclaredIds,
      duplicateDeclaredCanonicalIds: [...new Set(duplicateDeclaredIds)],
    },
    sourceFamilies: ledger.sourceFamilies.map((family) => ({
      id: family.id,
      label: family.label,
      coverageClass: family.coverageClass,
      canonicalModelEligiblePollIds: family.canonicalModelEligiblePollIds ?? [],
      stagedEvidence: family.stagedEvidence ?? [],
      actionableGapCount: actionable.filter((gap) => gap.sourceFamilyId === family.id).length,
      exclusionReason: family.exclusionReason ?? null,
      nextAction: family.nextAction ?? null,
    })),
    stagedCoverageResolutions,
    actionableGaps: actionable,
    priorityQueue: ledger.priorityQueue,
  };
}

function main() {
  const root = resolve(new URL("..", import.meta.url).pathname);
  const ledger = JSON.parse(readFileSync(resolve(root, "metadata/poll-coverage-ledger-2026.json"), "utf8"));
  const events = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
  const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));
  const primary = JSON.parse(readFileSync(resolve(root, "metadata/primary-source-evidence-2026.json"), "utf8"));
  const research = JSON.parse(readFileSync(resolve(root, "metadata/research-source-evidence-2026.json"), "utf8"));
  const report = buildCoverageReport({ ledger, events, manualRecords: manual.records, primaryRecords: primary.records, researchRecords: research.records });
  if (!report.integrity.allDeclaredCanonicalIdsExist || !report.integrity.declaredCanonicalIdsAreUnique) {
    throw new Error(`poll coverage ledger integrity failed: ${JSON.stringify(report.integrity)}`);
  }
  const output = resolve(root, arg("--output", "poll-coverage-report.json"));
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Poll coverage: ${report.repository.modelEligibleEvents} model-eligible events; ${report.repository.actionableGapItems} actionable gap items across ${report.repository.currentSourceFamiliesWithActionableGaps} source families; ${report.repository.declaredGapsResolvedByStaging} declared gaps resolved by staged evidence.`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
