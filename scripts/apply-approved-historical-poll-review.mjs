import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const outputPath = resolve(root, "model/data/validation/historical-replay-poll-observations.json");
const output2014Path = resolve(root, "model/data/validation/historical-replay-2014-poll-observations.json");

export function buildApprovedHistoricalPollInput2014() {
  const review = read("metadata/historical-poll-reuse-review-2014.json");
  if (review.decision !== "approved-for-historical-replay" || !review.checks.ownerReuseBasisApproval) throw new Error("2014 historical poll review is not approved for replay");
  const cases = review.caseIds.map((caseId) => read(`metadata/${caseId.replace(/^historical-poll-/, "historical-poll-reuse-case-")}.json`));
  for (const caseFile of cases) {
    if (caseFile.cycleId !== "vic_la_2014" || !caseFile.replayEligible || !caseFile.modelInputAdmissible || caseFile.ownerReviewStatus !== "approved-for-historical-replay" || !caseFile.notFromQuarantinedDataset) throw new Error(`2014 case ${caseFile.caseId} is not governed for replay`);
    if (!caseFile.gates.provenance.passed || !caseFile.gates.methodologicalAdequacy.passed || !caseFile.gates.reuseBasis.passed) throw new Error(`2014 case ${caseFile.caseId} has a failed automated gate`);
  }
  const observations = cases.map((caseFile) => ({
    observationId: caseFile.caseId,
    cycleId: caseFile.cycleId,
    period: caseFile.observationPeriod ?? caseFile.fieldwork.end,
    sourceId: caseFile.sourceId,
    sourceUrl: caseFile.sourceUrl,
    sourceSha256: caseFile.sourceSha256,
    evidenceAvailableByDate: caseFile.evidenceAvailableByDate,
    sampleSize: caseFile.fieldwork.sampleSize,
    population: caseFile.fieldwork.population,
    mode: caseFile.fieldwork.mode,
    primaryShares: caseFile.reportedPrimaryCategories,
    reportedTpp: caseFile.reportedTpp,
    groupedResidual: caseFile.groupedResidual.family,
    ballotActiveFamilies: caseFile.ballotActiveFamilies,
    reuseBasis: caseFile.reuseBasis,
    ownerReviewId: review.reviewId,
    replayEligible: true,
  }));
  return {
    schemaVersion: 1,
    generatedBy: "scripts/apply-approved-historical-poll-review.mjs",
    generatedAt: review.approvedAt,
    cycleId: "vic_la_2014",
    ownerReviewId: review.reviewId,
    independentSourceFamilies: 1,
    observations,
    sufficiency: {minimumEligibleObservations: 3, minimumIndependentSourceFamilies: 2, status: "blocked-pending-second-family"},
    quarantineBoundary: "No values are read from d-j-hirst/aus-polling-analyser; this file contains only approved structured factual reconstruction.",
    modelImpact: {forecast2026: false, productionAuthorisation: false},
  };
}

export function buildApprovedHistoricalPollInput() {
  const caseFile = read("metadata/historical-poll-reuse-case-2018-essential.json");
  const review = read("metadata/historical-poll-reuse-review.json");
  if (review.caseId !== caseFile.caseId || review.decision !== "approved-for-historical-replay") throw new Error("historical poll review is not approved for replay");
  if (!review.checks.provenanceGate || !review.checks.methodologicalAdequacyGate || !review.checks.ownerReuseBasisApproval || !review.checks.notFromQuarantinedDataset) throw new Error("historical poll review has a failed gate");
  if (caseFile.reuseBasis !== review.reuseBasis || !caseFile.modelInputAdmissible || !caseFile.methodologicalAdequacyGate.passed) throw new Error("approved case does not match the reviewed admissible record");
  const essentialObservations = Object.entries(caseFile.reportedPrimaryShares).map(([period, shares]) => ({
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
  const ucomms = read("metadata/historical-poll-reuse-case-2018-ucomms.json");
  const ucommsReview = read("metadata/historical-poll-reuse-review-2018-ucomms.json");
  if (ucommsReview.caseId !== ucomms.caseId || ucommsReview.decision !== "approved-for-historical-replay") throw new Error("uComms review is not approved for replay");
  if (!ucomms.gates.provenance.passed || !ucomms.gates.methodologicalAdequacy.passed || !ucomms.gates.reuseBasis.passed || !ucomms.replayEligible || !ucomms.notFromQuarantinedDataset) throw new Error("uComms case has a failed gate");
  const ucommsObservation = {
    observationId: `${ucomms.caseId}-2018-11-13`, cycleId: ucomms.cycleId, period: "2018-11-13",
    sourceId: ucomms.sourceId, sourceUrl: ucomms.sourceUrl, sourceSha256: ucomms.sourceSha256,
    evidenceAvailableByDate: ucomms.evidenceAvailableByDate, sampleSize: ucomms.fieldwork.sampleSize,
    population: ucomms.fieldwork.population, mode: ucomms.fieldwork.mode,
    primaryShares: { ALP: 37.6, LIB_NAT: 35.2, GRN: 10.2, OTH_IND: 10.3 },
    reportedCategories: ucomms.reportedPrimaryCategories, groupedResidual: "OTH_IND",
    ballotActiveFamilies: ucomms.cycleBallotUniverse.activeFamilies, reuseBasis: ucomms.reuseBasis,
    ownerReviewId: ucommsReview.reviewId, replayEligible: true,
  };
  const review2022 = read("metadata/historical-poll-reuse-review-2022.json");
  const approved2022Ids = new Set(review2022.ownerDecision?.approvedCaseIds ?? []);
  const royMorganCases = [
    read("metadata/historical-poll-reuse-case-2022-roymorgan-2022-11-10.json"),
    read("metadata/historical-poll-reuse-case-2022-roymorgan-2022-11-23.json"),
  ];
  if (review2022.decision !== "partially-approved" || approved2022Ids.size !== 3) throw new Error("2022 historical poll review is not explicitly approved for all three governed observations");
  const royMorganObservations = royMorganCases.map((caseFile) => {
    if (!approved2022Ids.has(caseFile.caseId) || caseFile.ownerReviewStatus !== "approved-for-historical-replay" || !caseFile.modelInputAdmissible || !caseFile.replayEligible) throw new Error(`2022 case ${caseFile.caseId} is not governed for replay`);
    if (!caseFile.gates.provenance.passed || !caseFile.gates.methodologicalAdequacy.passed || !caseFile.gates.reuseBasis.passed || !caseFile.notFromQuarantinedDataset) throw new Error(`2022 case ${caseFile.caseId} has a failed automated gate`);
    return {
      observationId: `${caseFile.caseId}-${caseFile.fieldwork.end}`,
      cycleId: caseFile.cycleId,
      period: caseFile.fieldwork.end,
      sourceId: caseFile.sourceId,
      sourceUrl: caseFile.sourceUrl,
      sourceSha256: caseFile.sourceSha256,
      evidenceAvailableByDate: caseFile.evidenceAvailableByDate,
      sampleSize: caseFile.fieldwork.sampleSize,
      population: caseFile.fieldwork.population,
      mode: caseFile.fieldwork.mode,
      primaryShares: caseFile.reportedPrimaryCategories,
      reportedTpp: caseFile.reportedTpp,
      groupedResidual: "OTH_IND",
      ballotActiveFamilies: caseFile.ballotActiveFamilies,
      reuseBasis: caseFile.reuseBasis,
      ownerReviewId: review2022.reviewId,
      replayEligible: true,
    };
  });
  const resolveCase = read("metadata/historical-poll-reuse-case-2022-resolve-2022-11-16-20.json");
  if (!approved2022Ids.has(resolveCase.caseId) || resolveCase.ownerReviewStatus !== "approved-for-historical-replay" || !resolveCase.modelInputAdmissible || !resolveCase.replayEligible) throw new Error("2022 Resolve case is not governed for replay");
  if (!resolveCase.gates.provenance.passed || !resolveCase.gates.methodologicalAdequacy.passed || !resolveCase.gates.reuseBasis.passed || !resolveCase.notFromQuarantinedDataset) throw new Error("2022 Resolve case has a failed automated gate");
  const resolveObservation = {
    observationId: `${resolveCase.caseId}-${resolveCase.fieldwork.end}`,
    cycleId: resolveCase.cycleId, period: resolveCase.fieldwork.end,
    sourceId: resolveCase.sourceId, sourceUrl: resolveCase.sourceUrl, sourceSha256: resolveCase.sourceSha256,
    evidenceAvailableByDate: resolveCase.evidenceAvailableByDate, sampleSize: resolveCase.fieldwork.sampleSize,
    population: resolveCase.fieldwork.population, mode: resolveCase.fieldwork.mode,
    primaryShares: { ALP: resolveCase.reportedPrimaryCategories.ALP, LIB_NAT: resolveCase.reportedPrimaryCategories.LIB_NAT, GRN: resolveCase.reportedPrimaryCategories.GRN, OTH_IND: resolveCase.groupedResidual.OTH_IND },
    reportedCategories: resolveCase.reportedPrimaryCategories, reportedTpp: resolveCase.reportedTpp,
    groupedResidual: "OTH_IND", ballotActiveFamilies: resolveCase.ballotActiveFamilies,
    reuseBasis: resolveCase.reuseBasis, ownerReviewId: review2022.reviewId, replayEligible: true,
  };
  const observations = [...essentialObservations, ucommsObservation, ...royMorganObservations, resolveObservation];
  return {
    schemaVersion: 1,
    generatedBy: "scripts/apply-approved-historical-poll-review.mjs",
    generatedAt: review.approvedAt,
    sourceCaseId: caseFile.caseId,
    ownerReviewId: review.reviewId,
    independentSourceFamilies: 3,
    observations,
    quarantineBoundary: "No values are read from d-j-hirst/aus-polling-analyser; this file contains only the approved structured factual reconstruction.",
    modelImpact: { forecast2026: false, productionAuthorisation: false },
  };
}

if (process.argv[1]?.endsWith("apply-approved-historical-poll-review.mjs")) {
  if (process.argv.includes("--cycle=2014")) {
    const report2014 = buildApprovedHistoricalPollInput2014();
    if (process.argv.includes("--apply")) writeFileSync(output2014Path, `${JSON.stringify(report2014, null, 2)}\n`);
    console.log(`Approved 2014 historical poll input: ${report2014.observations.length} observations; ${report2014.independentSourceFamilies} independent source family; replay input only.`);
    process.exit(0);
  }
  const report = buildApprovedHistoricalPollInput();
  if (process.argv.includes("--apply")) {
    writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  }
  console.log(`Approved historical poll input: ${report.observations.length} observations; ${report.independentSourceFamilies} independent source family; replay input only.`);
}
