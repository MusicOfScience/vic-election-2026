import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const outputPath = resolve(root, "model/data/validation/historical-replay-poll-observations.json");

export function buildApprovedHistoricalPollInput() {
  const caseFile = read("metadata/historical-poll-reuse-case-2018-essential.json");
  const review = read("metadata/historical-poll-reuse-review.json");
  if (review.caseId !== caseFile.caseId || review.decision !== "approved-for-historical-replay") throw new Error("historical poll review is not approved for replay");
  if (!review.checks.provenanceGate || !review.checks.methodologicalAdequacyGate || !review.checks.ownerReuseBasisApproval || !review.checks.notFromQuarantinedDataset) throw new Error("historical poll review has a failed gate");
  if (caseFile.reuseBasis !== review.reuseBasis || !caseFile.modelInputAdmissible || !caseFile.methodologicalAdequacyGate.passed) throw new Error("approved case does not match the reviewed admissible record");
  const observations = Object.entries(caseFile.reportedPrimaryShares).map(([period, shares]) => ({
    observationId: `${caseFile.caseId}-${period}`,
    cycleId: caseFile.cycleId,
    period,
    sourceId: caseFile.sourceId,
    sourceUrl: caseFile.sourceUrl,
    sourceSha256: caseFile.sourceSha256,
    evidenceAvailableByDate: caseFile.evidenceAvailableByDate,
    sampleSize: caseFile.fieldwork.sampleSizes[period],
    population: caseFile.fieldwork.population,
    mode: caseFile.fieldwork.mode,
    primaryShares: shares,
    groupedResidual: "OTH_IND",
    ballotActiveFamilies: caseFile.cycleBallotUniverse.activeFamilies,
    reuseBasis: caseFile.reuseBasis,
    ownerReviewId: review.reviewId,
    replayEligible: true,
  }));
  return {
    schemaVersion: 1,
    generatedBy: "scripts/apply-approved-historical-poll-review.mjs",
    generatedAt: review.approvedAt,
    sourceCaseId: caseFile.caseId,
    ownerReviewId: review.reviewId,
    independentSourceFamilies: 1,
    observations,
    quarantineBoundary: "No values are read from d-j-hirst/aus-polling-analyser; this file contains only the approved structured factual reconstruction.",
    modelImpact: { forecast2026: false, productionAuthorisation: false },
  };
}

if (process.argv[1]?.endsWith("apply-approved-historical-poll-review.mjs")) {
  const report = buildApprovedHistoricalPollInput();
  if (process.argv.includes("--apply")) {
    writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  }
  console.log(`Approved historical poll input: ${report.observations.length} observations; ${report.independentSourceFamilies} independent source family; replay input only.`);
}
