import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { buildEvidenceFreshness } from "./build-evidence-freshness-report.mjs";
import { classifyContest, loadContestUniverse } from "./candidate-contests.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const generatedJson = resolve(root, "metadata/release-readiness.generated.json");
const generatedTs = resolve(root, "app/release-readiness.generated.ts");

export function ageInDays(effectiveDate, asOf) {
  return Math.floor((Date.parse(`${asOf}T00:00:00Z`) - Date.parse(`${effectiveDate}T00:00:00Z`)) / 86_400_000);
}

function hash(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}

function readJson(path) {
  return JSON.parse(readFileSync(resolve(root, path), "utf8"));
}

export function buildReadiness({ asOf }) {
  const registry = readJson("metadata/sources.json");
  const provenance = readJson("metadata/source-provenance.generated.json");
  const forecast = readJson("model/data/processed/experimental_forecast_2026.json");
  const validation = readJson("metadata/model-validation-status.json");
  const validationEvidence = readJson("metadata/model-validation-evidence-contract.json");
  const candidates = readJson("metadata/candidates-2026.json");
  const provisionalCandidates = readJson("metadata/provisional-candidate-evidence-2026.json");
  const accepted = readJson("metadata/accepted-polls-2026.json");
  const manual = readJson("metadata/manual-source-evidence-2026.json");
  const primary = readJson("metadata/primary-source-evidence-2026.json");
  const research = readJson("metadata/research-source-evidence-2026.json");
  const provenanceById = new Map(provenance.sources.map((source) => [source.id, source]));
  const sources = registry.sources.map((source) => {
    const ageDays = ageInDays(source.dataEffectiveDate, asOf);
    const stale = source.stalenessThresholdDays !== null && ageDays > source.stalenessThresholdDays;
    const traced = provenanceById.get(source.id);
    const artifactsCurrent = Boolean(traced) && traced.artifacts.every((artifact) => {
      const path = resolve(root, artifact.path);
      return existsSync(path) && hash(path) === artifact.sha256;
    });
    return { id: source.id, critical: source.criticalToForecast, dataEffectiveDate: source.dataEffectiveDate, ageDays, stalenessThresholdDays: source.stalenessThresholdDays, stale, artifactsCurrent };
  });
  const modelOutputsCurrent = Object.values(forecast.outputs).every((output) => {
    const path = resolve(root, "model", output.path);
    return existsSync(path) && hash(path) === output.sha256;
  });
  const configCurrent = hash(resolve(root, "model/config/experimental_forecast.yml")) === forecast.assumptions.config_sha256;
  const criticalSourcesFresh = sources.filter((source) => source.critical).every((source) => !source.stale);
  const sourceIntegrity = sources.every((source) => source.artifactsCurrent);
  const generatedOutputsCurrent = sourceIntegrity && modelOutputsCurrent && configCurrent;
  const expectedCycles = ["2010", "2014", "2018", "2022"];
  const historicalDataReady = validation.historicalDataReadiness?.passed === true
    && expectedCycles.every((cycle) => validation.historicalDataReadiness.cycles?.includes(cycle));
  const modelPolls = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
  const stagedPolls = [
    ...(manual.records ?? []),
    ...(primary.records ?? []).map((record) => ({ ...record, publicationDate: record.pollPublicationDate ?? record.publicationDate })),
    ...(research.records ?? []),
  ];
  const evidenceFreshness = buildEvidenceFreshness({ modelPolls, acceptedPolls: accepted.polls ?? [], stagedPolls, asOf });
  const modelInputCurrent = !evidenceFreshness.newerEvidenceAwaitingReview;
  const contestUniverse = loadContestUniverse(root);
  const assemblyContests = new Set(
    (candidates.candidates ?? [])
      .map((candidate) => classifyContest(candidate.contest, contestUniverse))
      .filter((contest) => contest?.chamber === "assembly")
      .map((contest) => contest.canonicalContest),
  );
  const candidateEvidenceReady = assemblyContests.size === 88;
  const stagedContests = (provisionalCandidates.records ?? [])
    .filter((candidate) => candidate.status === "quarantined-awaiting-review")
    .map((candidate) => ({ sourceContest: candidate.contest, classification: classifyContest(candidate.contest, contestUniverse) }));
  const stagedAssemblyContests = new Set(stagedContests.filter((item) => item.classification?.chamber === "assembly").map((item) => item.classification.canonicalContest));
  const stagedCouncilRegions = new Set(stagedContests.filter((item) => item.classification?.chamber === "council").map((item) => item.classification.canonicalContest));
  const unclassifiedCandidateContests = [...new Set(stagedContests.filter((item) => !item.classification).map((item) => item.sourceContest))];
  const completeForecastBacktest = validation.completeForecastBacktest?.passed === true;
  const probabilityCalibration = validation.probabilityCalibration?.passed === true;
  const validationEvidenceCounts = validationEvidence.components.reduce((counts, component) => {
    counts[component.status] = (counts[component.status] ?? 0) + 1;
    return counts;
  }, {});
  const productionAuthorised = forecast.production_compatible === true;
  const gates = {
    sourceIntegrity: { passed: sourceIntegrity, label: "Source fingerprints match" },
    criticalSourceFreshness: { passed: criticalSourcesFresh, label: "Critical sources are within age policy" },
    modelInputFreshness: { passed: modelInputCurrent, label: "Newer reviewed evidence is resolved into or excluded from model inputs" },
    deterministicOutputs: { passed: generatedOutputsCurrent, label: "Model outputs and configuration match" },
    historicalDataReadiness: { passed: historicalDataReady, label: validation.historicalDataReadiness.label },
    completeForecastBacktest: { passed: completeForecastBacktest, label: validation.completeForecastBacktest.label },
    probabilityCalibration: { passed: probabilityCalibration, label: validation.probabilityCalibration.label },
    candidateEvidence: { passed: candidateEvidenceReady, label: `2026 candidate evidence covers ${assemblyContests.size}/88 Assembly districts` },
    productionAuthorisation: { passed: productionAuthorised, label: "Complete probability model explicitly authorised" },
  };
  const blockingGateIds = Object.entries(gates).filter(([, gate]) => !gate.passed).map(([id]) => id);
  return {
    schemaVersion: 2,
    assessedAsOf: asOf,
    status: blockingGateIds.length === 0 ? "production-ready" : "experimental-blocked",
    policy: "retain-last-valid-forecast",
    automation: { scheduledMonitoring: true, automaticProductionPublish: false },
    summary: {
      passedRequiredGates: Object.values(gates).filter((gate) => gate.passed).length,
      requiredGateCount: Object.keys(gates).length,
      blockingGateIds,
    },
    gates,
    findings: {
      demographicChallenger: validation.demographicChallenger,
      candidateDiscovery: {
        status: assemblyContests.size > 0 ? "accepted-endorsed-evidence-incomplete-coverage" : "quarantined-awaiting-review",
        records: provisionalCandidates.records?.length ?? 0,
        acceptedRecords: candidates.candidates?.length ?? 0,
        sourceFamilies: provisionalCandidates.summary?.sourceFamilies ?? 0,
        assemblyContests: stagedAssemblyContests.size,
        assemblyDistrictsTotal: 88,
        councilRegions: stagedCouncilRegions.size,
        councilRegionsTotal: 8,
        acceptedAssemblyContests: assemblyContests.size,
        unclassifiedContests: unclassifiedCandidateContests,
        automaticPromotion: false,
        label: `${assemblyContests.size}/88 Assembly districts have accepted endorsed candidate evidence`,
      },
      validationEvidence: {
        scope: validationEvidence.scope,
        complete: validationEvidenceCounts.complete ?? 0,
        partial: validationEvidenceCounts.partial ?? 0,
        missing: validationEvidenceCounts.missing ?? 0,
        total: validationEvidence.components.length,
        automaticGateOpening: validationEvidence.automaticGateOpening,
        label: `${validationEvidenceCounts.complete ?? 0}/${validationEvidence.components.length} complete-model historical evidence components are complete`,
      },
    },
    evidenceFreshness,
    sources,
  };
}

function main() {
  const checkOnly = process.argv.includes("--check");
  const requireFresh = process.argv.includes("--require-fresh");
  const asOfIndex = process.argv.indexOf("--as-of");
  const reportIndex = process.argv.indexOf("--report");
  const registry = JSON.parse(readFileSync(resolve(root, "metadata/sources.json"), "utf8"));
  const asOf = asOfIndex >= 0 ? process.argv[asOfIndex + 1] : registry.registryReviewedAt.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf)) throw new Error("release readiness: --as-of must be YYYY-MM-DD");
  const readiness = buildReadiness({ asOf });
  const json = `${JSON.stringify(readiness, null, 2)}\n`;
  const ts = `// Generated by scripts/check-release-readiness.mjs. Do not edit by hand.\nexport const releaseReadiness = ${JSON.stringify(readiness, null, 2)} as const;\n`;
  if (reportIndex >= 0) writeFileSync(resolve(root, process.argv[reportIndex + 1]), json);
  else if (checkOnly) {
    if (!existsSync(generatedJson) || readFileSync(generatedJson, "utf8") !== json) throw new Error("release readiness: generated JSON is stale");
    if (!existsSync(generatedTs) || readFileSync(generatedTs, "utf8") !== ts) throw new Error("release readiness: generated TypeScript is stale");
  } else {
    writeFileSync(generatedJson, json);
    writeFileSync(generatedTs, ts);
  }
  console.log(`Release readiness: ${readiness.status}; ${Object.values(readiness.gates).filter((gate) => gate.passed).length}/${Object.keys(readiness.gates).length} gates pass.`);
  if (requireFresh && !readiness.gates.criticalSourceFreshness.passed) process.exitCode = 2;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
