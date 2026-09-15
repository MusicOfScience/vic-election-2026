import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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
  const [rawHeaders, ...data] = rows;
  if (!rawHeaders) return [];
  const headers = rawHeaders.map((header, index) => index === 0 ? header.replace(/^\uFEFF/, "") : header);
  return data.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function sourceFamilyId(firm, brand) {
  return [firm, brand].filter(Boolean).join("-").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export function buildHistoricalPollReconstructionQueue({ sourceBuffer, audit, reviewedAt }) {
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== audit.source.sha256) {
    throw new Error(`historical poll source fingerprint mismatch: expected ${audit.source.sha256}, received ${sourceHash}`);
  }

  const sourceRows = parseCsv(sourceBuffer.toString("utf8"));
  const assignedRows = [];
  for (const cycle of audit.coverage.cycles) {
    const rows = sourceRows.filter((row) => row.MidDate >= cycle.windowStart && row.MidDate <= cycle.informationCutoff);
    if (rows.length !== cycle.candidateRows) {
      throw new Error(`${cycle.id} candidate count mismatch: expected ${cycle.candidateRows}, received ${rows.length}`);
    }
    for (const row of rows) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(row.MidDate) || !row.Firm) {
        throw new Error(`${cycle.id} contains a lead without a valid MidDate and Firm`);
      }
      assignedRows.push({ ...row, cycleId: cycle.id });
    }
  }
  if (assignedRows.length !== audit.coverage.candidateRows) {
    throw new Error(`candidate count mismatch: expected ${audit.coverage.candidateRows}, received ${assignedRows.length}`);
  }

  const grouped = new Map();
  for (const row of assignedRows) {
    const key = `${row.Firm}\u0000${row.Brand}`;
    const current = grouped.get(key) ?? {
      id: sourceFamilyId(row.Firm, row.Brand),
      firmLabel: row.Firm,
      brandLabel: row.Brand || null,
      candidateRows: 0,
      earliestMidDate: row.MidDate,
      latestMidDate: row.MidDate,
      cycles: {},
    };
    current.candidateRows += 1;
    current.earliestMidDate = row.MidDate < current.earliestMidDate ? row.MidDate : current.earliestMidDate;
    current.latestMidDate = row.MidDate > current.latestMidDate ? row.MidDate : current.latestMidDate;
    current.cycles[row.cycleId] = (current.cycles[row.cycleId] ?? 0) + 1;
    grouped.set(key, current);
  }

  const queue = [...grouped.values()]
    .sort((left, right) => right.candidateRows - left.candidateRows || left.id.localeCompare(right.id))
    .map((family, index) => ({
      priority: index + 1,
      ...family,
      shareOfCandidateRows: Number((family.candidateRows / assignedRows.length).toFixed(4)),
      reconstructedRows: 0,
      residualRows: family.candidateRows,
    }));

  return {
    schemaVersion: 1,
    reviewedAt,
    status: "reconstruction-queue-defined-first-party-evidence-missing",
    scope: audit.scope,
    purpose: "Aggregate the frozen lead list into a bounded first-party reconstruction queue without copying observation rows into the repository.",
    candidateSource: {
      repository: audit.source.repository,
      commit: audit.source.commit,
      path: audit.source.path,
      sha256: audit.source.sha256,
      declaredLicence: audit.source.declaredLicence,
      rawDataImported: false,
      observationRowsWritten: false,
    },
    coverage: {
      candidateRows: assignedRows.length,
      sourceFamilies: queue.length,
      reconstructedRows: 0,
      replayEligibleRows: 0,
      residualRows: assignedRows.length,
      requiredFieldCoverage: Object.fromEntries(audit.missingRequiredFields.map((field) => [field, 0])),
      cycles: audit.coverage.cycles.map((cycle) => ({
        id: cycle.id,
        informationCutoff: cycle.informationCutoff,
        candidateRows: cycle.candidateRows,
        reconstructedRows: 0,
        residualRows: cycle.candidateRows,
      })),
    },
    reconstructionQueue: queue,
    acceptanceRules: {
      originalPollsterOrPublisherSourceRequired: true,
      publicationDateAtOrBeforeCycleCutoffRequired: true,
      fieldworkMidpointAsPublicationDateAccepted: false,
      sampleSizeRequired: true,
      explicitMethodRequired: true,
      observationSourceUrlRequired: true,
      explicitReuseAuthorityRequired: true,
      unresolvedRowsRemainQuarantined: true,
    },
    externalContact: {
      status: "deferred",
      trigger: "Only after the aggregate queue has been worked against original sources and material provenance or licensing gaps remain.",
    },
    modelImpact: {
      changesCurrentForecast: false,
      historicalReplayEligible: false,
      automaticPromotion: false,
      automaticGateOpening: false,
      productionAuthorisation: false,
    },
  };
}

function arg(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}

function main() {
  const sourcePath = arg("--source");
  if (!sourcePath) throw new Error("usage: node scripts/build-historical-poll-reconstruction-queue.mjs --source <frozen poll-data-vic.csv> [--output <path>]");
  const audit = JSON.parse(readFileSync(resolve(root, "metadata/historical-poll-vintage-audit.json"), "utf8"));
  const report = buildHistoricalPollReconstructionQueue({
    sourceBuffer: readFileSync(resolve(sourcePath)),
    audit,
    reviewedAt: arg("--reviewed-at") ?? audit.reviewedAt,
  });
  const outputPath = resolve(root, arg("--output") ?? "metadata/historical-poll-reconstruction-queue.json");
  writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Historical poll reconstruction queue: ${report.coverage.residualRows} residual leads across ${report.coverage.sourceFamilies} source families; zero rows imported or replay-eligible.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
