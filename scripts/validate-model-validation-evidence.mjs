import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function readJson(path) {
  return JSON.parse(readFileSync(resolve(root, path), "utf8"));
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(resolve(root, path))).digest("hex");
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

function assert(condition, message) {
  if (!condition) throw new Error(`model validation evidence: ${message}`);
}

export function validateModelValidationEvidence() {
  const contract = readJson("metadata/model-validation-evidence-contract.json");
  const inventory = readJson("metadata/model-validation-evidence-inventory.json");
  const contractById = new Map(contract.components.map((component) => [component.id, component]));
  const inventoryById = new Map(inventory.components.map((component) => [component.id, component]));
  const statusCounts = inventory.components.reduce((counts, component) => {
    counts[component.status] = (counts[component.status] ?? 0) + 1;
    return counts;
  }, {});

  assert(inventory.components.length === contract.components.length, "inventory must cover every contract component");
  assert(inventory.summary.complete === (statusCounts.complete ?? 0), "complete summary count is stale");
  assert(inventory.summary.partial === (statusCounts.partial ?? 0), "partial summary count is stale");
  assert(inventory.summary.missing === (statusCounts.missing ?? 0), "missing summary count is stale");
  assert(inventory.summary.total === inventory.components.length, "total summary count is stale");

  const acquisition = readJson("metadata/historical-source-acquisition-plan.json");
  const publicAudit = readJson("metadata/historical-public-source-audit.json");
  assert(acquisition.schemaVersion === 2, "historical source acquisition schema is stale");
  assert(acquisition.status === "assembly-primary-harvest-complete-residual-reconstruction-continues", "historical source acquisition status is stale");
  assert(acquisition.userActionRequired === false, "historical source acquisition must not assign premature external contact to the project owner");
  assert(acquisition.publicSourceAudit.path === "metadata/historical-public-source-audit.json", "public source audit path is incorrect");
  assert(acquisition.requests.length === 2, "expected exactly two deferred historical source requests");
  assert(new Set(acquisition.requests.map((request) => request.id)).size === acquisition.requests.length, "historical source request ids must be unique");
  assert(publicAudit.status === "assembly-primary-public-harvest-complete", "public source audit status is unexpected");
  assert(publicAudit.userActionRequired === false, "public source audit must require no owner action");
  assert(publicAudit.quarantinePolicy.candidateDataImported === false, "public source discovery cannot import candidate data");
  assert(publicAudit.quarantinePolicy.residualGapsMustBeMachineReported === true, "external contact requires a machine-readable residual-gap report");

  const vecRequest = acquisition.requests.find((request) => request.id === "vec-legislative-assembly-primaries-2010-2022");
  const pollRequest = acquisition.requests.find((request) => request.id === "historical-poll-vintage-enrichment-and-reuse");
  assert(vecRequest?.status === "not-required-public-harvest-complete", "VEC contact must be retired after the complete public harvest");
  assert(vecRequest.userActionRequired === false, "VEC acquisition cannot require premature owner action");
  assert(vecRequest.preContactWork.includes("audit-supplied-project-checkpoints"), "VEC acquisition must re-audit supplied checkpoints");
  assert(vecRequest.preContactWork.includes("harvest-public-vec-district-pages-and-spreadsheets"), "VEC acquisition must harvest public first-party results");
  assert(vecRequest.contactTrigger === null, "complete Assembly primary evidence must not retain a VEC contact trigger");
  assert(vecRequest.cycles.length === 4, "VEC acquisition must cover four Assembly cycles");
  assert(vecRequest.cycles.every((cycle) => cycle.requiredDistricts === 88), "VEC acquisition must cover every Assembly district");
  assert(vecRequest.cycles.every((cycle) => cycle.auditedDistricts === 88), "VEC acquisition must record complete four-cycle district coverage");
  assert(vecRequest.publishedAvailability.listed2022GeneralElectionDistricts === 87, "VEC public 2022 index must distinguish the general election districts");
  assert(vecRequest.publishedAvailability.narracanSupplementaryDistricts === 1, "VEC public 2022 index must record the Narracan supplementary election");
  assert(vecRequest.publishedAvailability.candidateFirstPreferenceTablesAvailable === true, "VEC public first-preference tables must be acknowledged");
  assert(vecRequest.publishedAvailability.perDistrictPrimaryExcelLinksAvailable === true, "VEC public district spreadsheets must be acknowledged");
  assert(vecRequest.publishedAvailability.indicativePreferenceDistributionDistricts === 39, "VEC indicative preference count is unexpected");
  assert(vecRequest.acceptanceRules.districtFormalVoteReconciliationRequired === true, "VEC result imports must reconcile to formal votes");
  assert(vecRequest.acceptanceRules.pdfOnlyAccepted === false, "PDF-only historical results are not reproducible inputs");

  const vecAudit = publicAudit.sources.find((source) => source.id === "vec-historical-assembly-results");
  assert(vecAudit?.findings.fourCycleTppOutcomes.boundaryAlignedRows === 340, "public audit must preserve the complete TPP benchmark");
  assert(vecAudit.findings.processedCandidatePrimaryEvidence.semantics.includes("not a count of files supplied"), "processed coverage must not be misrepresented as supplied-file coverage");
  assert(vecAudit.findings.processedCandidatePrimaryEvidence.status === "complete", "public audit must record complete Assembly primary evidence");
  assert(vecAudit.findings.processedCandidatePrimaryEvidence.districtCycleContests === 352, "public audit Assembly contest count is stale");
  assert(vecAudit.findings.processedCandidatePrimaryEvidence.candidateRows === 2296, "public audit Assembly candidate count is stale");
  assert(vecAudit.externalContact.status === "not-required", "VEC contact must be retired in the public audit");

  assert(pollRequest?.status === "deferred-pending-first-party-reconstruction", "polling repository contact must remain deferred");
  assert(pollRequest.userActionRequired === false, "polling provenance work cannot require premature owner action");
  assert(pollRequest.maintainerIdentity.account === "d-j-hirst", "polling repository owner account is incorrect");
  assert(pollRequest.maintainerIdentity.verifiedPublicName === null, "polling repository owner name must not be invented");
  assert(pollRequest.preContactWork.includes("search-original-pollster-and-publisher-sources"), "polling acquisition must prefer original sources");
  assert(pollRequest.completedPreContactWork.includes("produce-machine-readable-residual-provenance-gap-report"), "polling acquisition must record the completed residual-gap report");
  assert(pollRequest.residualGapReport.path === "metadata/historical-poll-reconstruction-queue.json", "polling residual-gap report path is incorrect");
  assert(pollRequest.residualGapReport.evidencePath === "metadata/historical-poll-reconstruction-evidence.json", "polling reconstruction evidence path is incorrect");
  assert(pollRequest.residualGapReport.candidateRows === 200 && pollRequest.residualGapReport.sourceMatchedRows === 57
    && pollRequest.residualGapReport.replayEligibleRows === 0, "polling residual-gap summary is stale");
  assert(pollRequest.frozenCandidateSource.candidateRows === 200, "polling acquisition must preserve the audited lead-list count");
  assert(pollRequest.frozenCandidateSource.currentlyReplayEligibleRows === 0, "unresolved polling rows cannot enter replay");
  assert(pollRequest.requiredFields.includes("publicationDate"), "polling acquisition must seek publication dates");
  assert(pollRequest.requiredFields.includes("sampleSize"), "polling acquisition must seek sample sizes");
  assert(pollRequest.requiredFields.includes("explicitMethod"), "polling acquisition must seek explicit methods");
  assert(pollRequest.requiredFields.includes("observationSourceUrl"), "polling acquisition must seek observation provenance");
  assert(pollRequest.requiredFields.includes("declaredReuseLicence"), "polling acquisition must seek reuse authority");
  assert(pollRequest.acceptanceRules.fieldworkMidpointAsPublicationDateAccepted === false, "fieldwork midpoint cannot substitute for publication date");

  const pollPublicAudit = publicAudit.sources.find((source) => source.id === "historical-poll-provenance");
  assert(pollPublicAudit?.candidateSource.publicNameVerified === false, "polling repository owner identity must remain conservative");
  assert(pollPublicAudit.candidateSource.declaredLicence === null, "public audit must not invent polling reuse authority");
  assert(pollPublicAudit.role === "lead-list-only", "unlicensed polling data must remain a lead list");
  assert(pollPublicAudit.residualGapReport.sourceMatchedRows === 57, "public audit polling reconstruction count is stale");
  assert(pollPublicAudit.externalContact.status === "deferred", "polling repository contact must remain deferred");

  assert(acquisition.modelImpact.changesCurrentForecast === false, "source acquisition cannot change the current forecast");
  assert(acquisition.modelImpact.automaticPromotion === false, "source responses cannot promote automatically");
  assert(acquisition.modelImpact.automaticGateOpening === false, "source acquisition cannot open gates");
  assert(publicAudit.modelImpact.changesCurrentForecast === false, "public source audit cannot change the current forecast");
  assert(publicAudit.modelImpact.productionAuthorisation === false, "public source audit cannot authorise production");

  const outcomeAvailability = readJson("metadata/historical-assembly-outcome-availability.json");
  assert(outcomeAvailability.status === "complete-outcome-date-separation", "Assembly outcome-date separation is incomplete");
  assert(outcomeAvailability.cycles.length === contract.minimumWalkForwardCycles, "Assembly outcome-date audit must cover four cycles");
  assert(new Set(outcomeAvailability.cycles.map((cycle) => cycle.id)).size === contract.minimumWalkForwardCycles, "Assembly outcome-date cycle ids must be unique");
  assert(outcomeAvailability.checks.eventDatesSeparatedFromEvidencePublicationDates === true, "event dates and evidence publication dates must remain distinct");
  assert(outcomeAvailability.checks.unknownPublicationDatesCannotProvePreCutoffAvailability === true, "unknown publication dates cannot prove pre-cutoff availability");
  assert(outcomeAvailability.modelImpact.changesCurrentForecast === false, "outcome-date audit cannot change the current forecast");
  assert(outcomeAvailability.modelImpact.historicalReplayEligible === false, "outcome-date audit cannot independently authorise replay");
  assert(outcomeAvailability.modelImpact.probabilityCalibrationReady === false, "outcome-date audit cannot independently authorise calibration");
  assert(outcomeAvailability.modelImpact.automaticGateOpening === false, "outcome-date audit cannot open a gate");
  assert(outcomeAvailability.modelImpact.productionAuthorisation === false, "outcome-date audit cannot authorise production");

  const outcome2022 = outcomeAvailability.cycles.find((cycle) => cycle.id === "vic_la_2022");
  assert(outcome2022?.generalElectionDate === "2022-11-26", "2022 general-election date is incorrect");
  assert(outcome2022.informationCutoff === "2022-11-25", "2022 information cutoff is incorrect");
  assert(outcome2022.generalElectionDistricts === 87, "2022 general-election scoring must contain 87 districts");
  assert(JSON.stringify(outcome2022.districtsWithoutGeneralElectionOutcome) === JSON.stringify(["Narracan"]), "Narracan must be the only district without a November 2022 outcome");
  assert(outcome2022.separatePostCycleContests.length === 1, "expected one post-cycle 2022 contest");
  const narracan = outcome2022.separatePostCycleContests[0];
  assert(narracan.id === "vic_la_2023_narracan_supplementary", "Narracan supplementary contest id is incorrect");
  assert(narracan.district === "Narracan" && narracan.contest === "supplementary-election", "Narracan supplementary contest classification is incorrect");
  assert(narracan.eventDate === "2023-01-28", "Narracan supplementary event date is incorrect");
  assert(Date.parse(`${narracan.eventDate}T00:00:00Z`) > Date.parse(`${outcome2022.generalElectionDate}T00:00:00Z`), "Narracan must postdate the 2022 general election");
  assert(narracan.resultEvidencePublicationDate === null, "Narracan evidence publication date must not be invented");
  assert(narracan.publicationDateStatus === "exact-publication-date-not-established", "Narracan publication-date limitation must be explicit");
  assert(narracan.preCutoffInputEligible === false, "Narracan supplementary evidence cannot enter the November 2022 information set");
  assert(narracan.includedInGeneralElectionScoring === false, "Narracan supplementary outcome cannot score the November 2022 cycle");
  assert(narracan.scoringUse === "separate-post-cycle-outcome-only", "Narracan scoring use is incorrect");

  const assembly2022Candidates = parseCsv(readFileSync(resolve(root, "model/data/processed/vec_2022_assembly_candidate_primaries.csv"), "utf8"));
  const assembly2022General = assembly2022Candidates.filter((row) => row.contest === "general-election");
  const narracanSupplementary = assembly2022Candidates.filter((row) => row.contest === "supplementary-election");
  assert(new Set(assembly2022General.map((row) => row.district_id)).size === 87, "2022 general-election outcome rows must cover 87 districts");
  assert(assembly2022General.reduce((sum, row) => sum + Number(row.first_preference_votes), 0) === 3617000, "2022 general-election formal votes do not reconcile");
  assert(new Set(narracanSupplementary.map((row) => row.district_id)).size === 1, "supplementary rows must cover exactly one district");
  assert(narracanSupplementary.length === 11 && narracanSupplementary.every((row) => row.district_name === "Narracan"), "Narracan supplementary candidate rows are incomplete");
  assert(narracanSupplementary.reduce((sum, row) => sum + Number(row.first_preference_votes), 0) === 37205, "Narracan supplementary formal votes do not reconcile");

  for (const [id, component] of inventoryById) {
    assert(contractById.has(id), `unknown inventory component ${id}`);
    assert(contractById.get(id).status === component.status, `${id} status differs from the contract`);
    if (component.status === "missing") assert(component.evidence.length === 0, `${id} cannot claim evidence while missing`);
    if (component.status === "complete") assert(component.coverage.cycles?.length >= contract.minimumWalkForwardCycles, `${id} lacks four-cycle coverage`);
    for (const evidence of component.evidence) {
      assert(existsSync(resolve(root, evidence.path)), `missing artefact ${evidence.path}`);
      assert(sha256(evidence.path) === evidence.sha256, `fingerprint mismatch for ${evidence.path}`);
    }
  }

  for (const evidence of inventory.negativeFeatureEvidence.demographicChallenger.evidence) {
    assert(existsSync(resolve(root, evidence.path)), `missing negative-test artefact ${evidence.path}`);
    assert(sha256(evidence.path) === evidence.sha256, `fingerprint mismatch for ${evidence.path}`);
  }

  const readiness = readJson("model/data/processed/historical_four_cycle_readiness_report.json");
  const validationInputs = readJson("model/data/processed/historical_four_cycle_validation_inputs_report.json");
  const nullReport = readJson("model/data/processed/historical_four_cycle_uniform_swing_null_report.json");
  assert(readiness.four_cycle_backtest_input_ready === true, "four-cycle TPP substrate is not ready");
  assert(readiness.production_forecast_authorised === false, "historical substrate must not authorise production");
  assert(validationInputs.outcome_rows === 340, "expected 340 boundary-aligned TPP transitions");
  assert(validationInputs.expected_cycles.length === 4, "expected four historical outcome cycles");
  assert(validationInputs.explicit_outcome_exclusions.some((entry) => entry.cycle_id === "vic_la_2022"
    && entry.district_name === "Narracan"
    && entry.exclusion_reason === "missing_2022_ordinary_tpp"), "Narracan must remain excluded from the November 2022 TPP score");
  assert(nullReport.forecast_error_distribution_authorised === false, "null residuals must remain unauthorised");

  const pollAudit = readJson("metadata/historical-poll-vintage-audit.json");
  const expectedPollRows = new Map([
    ["vic_la_2010", 37],
    ["vic_la_2014", 68],
    ["vic_la_2018", 59],
    ["vic_la_2022", 36],
  ]);
  assert(pollAudit.status === "partial-quarantined-not-imported", "historical polling candidate must remain explicitly quarantined");
  assert(pollAudit.source.repository === "d-j-hirst/aus-polling-analyser", "unexpected historical polling source repository");
  assert(pollAudit.source.commit === "a244da459807a22284d569b0b7e95ce79dfc53ff", "historical polling source commit is not frozen");
  assert(pollAudit.source.path === "analysis/Data/poll-data-vic.csv", "unexpected historical polling source path");
  assert(pollAudit.source.blobSha === "ecacd306524de046ad23db9434dedae7dbb94acd", "historical polling source blob is not frozen");
  assert(pollAudit.source.sha256 === "9d09af56c639151035b4b8b74bd216d92a916c3d374d2d15fbab70cb128fa720", "historical polling source fingerprint is not frozen");
  assert(pollAudit.source.declaredLicence === null, "historical polling audit must not invent reuse authority");
  assert(pollAudit.source.rawDataImported === false, "unlicensed historical polling data cannot be imported");
  assert(pollAudit.coverage.cycles.length === expectedPollRows.size, "historical polling audit must cover four cycles");
  assert(new Set(pollAudit.coverage.cycles.map((cycle) => cycle.id)).size === expectedPollRows.size, "historical polling cycle ids must be unique");
  assert(pollAudit.coverage.cycles.reduce((sum, cycle) => sum + cycle.candidateRows, 0) === pollAudit.coverage.candidateRows, "historical polling cycle counts do not reconcile");
  assert(pollAudit.coverage.candidateRows === 200, "expected 200 quarantined historical poll candidates");
  assert(pollAudit.coverage.publicationDatedRows === 0, "fieldwork midpoint must not be relabelled as publication date");
  assert(pollAudit.coverage.sampleSizeRows === 0, "historical polling audit must disclose missing sample sizes");
  assert(pollAudit.coverage.explicitMethodRows === 0, "historical polling audit must disclose missing methods");
  assert(pollAudit.coverage.importedRows === 0, "quarantined polling candidates cannot enter model inputs");
  for (const cycle of pollAudit.coverage.cycles) {
    assert(expectedPollRows.get(cycle.id) === cycle.candidateRows, `unexpected candidate poll count for ${cycle.id}`);
    assert(Date.parse(`${cycle.latestMidDate}T00:00:00Z`) <= Date.parse(`${cycle.informationCutoff}T00:00:00Z`), `candidate polls exceed the frozen cutoff for ${cycle.id}`);
  }
  assert(pollAudit.decision.forecastEligible === false, "historical polling candidate cannot affect the 2026 forecast");
  assert(pollAudit.decision.historicalReplayEligible === false, "historical polling candidate cannot enter a replay");
  assert(pollAudit.decision.automaticPromotion === false, "historical polling candidate cannot promote automatically");

  const pollEvidence = readJson("metadata/historical-poll-reconstruction-evidence.json");
  const essentialEvidence = pollEvidence.sourceFamilies.find((family) => family.id === "essential");
  const smsMorganEvidence = pollEvidence.sourceFamilies.find((family) => family.id === "sms-morgan");
  assert(pollEvidence.schemaVersion === 1 && pollEvidence.sourceFamilies.length === 2, "historical polling evidence schema or family count is unexpected");
  assert(pollEvidence.availabilityDateSemantics.includes("may be later")
    && pollEvidence.availabilityDateSemantics.includes("must not be represented as that original release date"), "historical polling evidence must distinguish corroborated availability from original publication");
  const sourceIds = pollEvidence.sourceFamilies.flatMap((family) => family.sources.map((source) => source.id));
  assert(new Set(sourceIds).size === sourceIds.length, "historical polling source ids must be globally unique");
  for (const family of pollEvidence.sourceFamilies) {
    assert(family.status === "partial-first-party-reconstruction", `${family.label} polling evidence status is stale`);
    assert(family.coverage.sourceDocuments === family.sources.length, `${family.label} source document count does not reconcile`);
    assert(family.sources.every((source) => source.url.startsWith("https://") && source.declaredReuseLicence === null), `${family.label} sources must retain HTTPS provenance and unresolved reuse authority`);
    assert(family.sources.every((source) => /^[a-f0-9]{64}$/.test(source.sha256 ?? source.contentSha256 ?? source.retrievedSha256)), `${family.label} sources must retain a SHA-256 fingerprint`);
    for (const source of family.sources.filter((entry) => entry.sourceType === "archived-first-party-pollster-web-page")) {
      const capture = source.url.match(/\/web\/(\d{4})(\d{2})(\d{2})\d{6}/);
      assert(capture, `${family.label} archived source ${source.id} lacks a timestamped capture URL`);
      assert(source.archivedAt === `${capture[1]}-${capture[2]}-${capture[3]}`, `${family.label} archived source ${source.id} capture date is inconsistent`);
      assert(source.archivedAt >= source.publishedAt.slice(0, 10), `${family.label} archived source ${source.id} predates its stated publication`);
    }
    const sourceById = new Map(family.sources.map((source) => [source.id, source]));
    const rows = [...family.matchedObservations, ...family.unresolvedObservations];
    assert(rows.length === family.candidateRows, `${family.label} observation inventory does not reconcile`);
    assert(new Set(rows.map((row) => `${row.cycleId}\u0000${row.leadMidDate}`)).size === family.candidateRows, `${family.label} observation inventory contains duplicates`);
    for (const observation of family.matchedObservations) {
      const source = sourceById.get(observation.sourceId);
      const cycle = pollAudit.coverage.cycles.find((entry) => entry.id === observation.cycleId);
      assert(source, `${family.label} observation ${observation.leadMidDate} has an unknown source`);
      assert(Number.isSafeInteger(observation.sampleSize) && observation.sampleSize > 0, `${family.label} observation ${observation.leadMidDate} lacks a valid sample`);
      const sourceAvailableDate = source.archivedAt ?? source.publishedDateAustraliaMelbourne ?? source.publishedAt.slice(0, 10);
      assert(observation.evidenceAvailableByDate === sourceAvailableDate, `${family.label} observation ${observation.leadMidDate} availability date differs from its cited source`);
      assert(cycle && observation.evidenceAvailableByDate <= cycle.informationCutoff, `${family.label} observation ${observation.leadMidDate} was not evidenced by its frozen cutoff`);
      assert(observation.explicitMethodSourceId === null || sourceById.get(observation.explicitMethodSourceId)?.explicitMethod, `${family.label} observation ${observation.leadMidDate} has invalid method evidence`);
      assert(observation.replayEligible === false, `${family.label} observation ${observation.leadMidDate} cannot be replay-eligible without reuse authority`);
      assert(!("primaryVote" in observation) && !("twoPartyPreferred" in observation), `${family.label} reconstruction evidence must not copy vote values from the quarantined lead list`);
    }
    assert(family.coverage.sourceMatchedRows === family.matchedObservations.length
      && family.coverage.unresolvedRows === family.unresolvedObservations.length, `${family.label} source coverage does not reconcile`);
    assert(family.coverage.publicationDatedRows === family.matchedObservations.length
      && family.coverage.sampleSizeRows === family.matchedObservations.length
      && family.coverage.observationSourceUrlRows === family.matchedObservations.length, `${family.label} provenance field coverage does not reconcile`);
    assert(family.coverage.explicitMethodRows === family.matchedObservations.filter((row) => row.explicitMethodSourceId !== null).length, `${family.label} method coverage does not reconcile`);
    assert(family.coverage.declaredReuseLicenceRows === 0 && family.coverage.fullyReconstructedRows === 0
      && family.coverage.replayEligibleRows === 0, `${family.label} evidence must remain fail-closed`);
    assert(Object.values(family.decision).filter((value) => typeof value === "boolean").every((value) => value === false), `${family.label} decision must remain fail-closed`);
  }
  assert(essentialEvidence?.candidateRows === 41 && essentialEvidence.sources.length === 10, "Essential candidate or source count is stale");
  assert(essentialEvidence.matchedObservations.length === 33 && essentialEvidence.unresolvedObservations.length === 8, "Essential matched and unresolved counts are stale");
  const essentialCoverage = essentialEvidence.coverage;
  assert(essentialCoverage.explicitMethodRows === 12, "Essential method coverage is stale");
  assert(smsMorganEvidence?.candidateRows === 33 && smsMorganEvidence.sources.length === 24, "SMS Morgan candidate or source count is stale");
  assert(smsMorganEvidence.matchedObservations.length === 24 && smsMorganEvidence.unresolvedObservations.length === 9, "SMS Morgan matched and unresolved counts are stale");
  assert(smsMorganEvidence.coverage.explicitMethodRows === 23, "SMS Morgan method coverage is stale");
  const archivedMorganSources = smsMorganEvidence.sources.filter((source) => source.sourceType === "archived-first-party-pollster-web-page");
  assert(archivedMorganSources.length === 14 && archivedMorganSources.every((source) => source.archivedAt), "archived SMS Morgan sources must retain capture dates");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2014-09-28" && row.sourcePeriodLabel.includes("does not identify")), "SMS Morgan September 2014 commissioning discrepancy must remain explicit");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2015-02-14" && row.sourcePeriodLabel.includes("conflicts")), "SMS Morgan February 2015 source discrepancy must remain explicit");
  assert(smsMorganEvidence.unresolvedObservations.some((row) => row.leadMidDate === "2020-09-09" && row.reason.includes("approval figures only")), "SMS Morgan approval-only lead must remain unresolved");
  assert(smsMorganEvidence.unresolvedObservations.some((row) => row.leadMidDate === "2018-11-23" && row.reason.includes("2018-11-24 in Melbourne") && row.reason.includes("after")), "SMS Morgan election-eve source must remain excluded after the local cutoff");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2020-09-30" && row.sourcePeriodLabel.includes("article prose says")), "SMS Morgan September 2020 date discrepancy must remain explicit");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2020-10-13" && row.sourcePeriodLabel.includes("article prose says")), "SMS Morgan October 2020 date discrepancy must remain explicit");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2021-11-11" && row.sourcePeriodLabel.includes("table labels")), "SMS Morgan November 2021 date discrepancy must remain explicit");
  assert(smsMorganEvidence.matchedObservations.some((row) => row.leadMidDate === "2022-07-01" && row.sourcePeriodLabel.includes("misprints 2021")), "SMS Morgan source date discrepancy must remain explicit");
  assert(Object.values(pollEvidence.modelImpact).every((value) => value === false), "historical polling evidence cannot change forecasts or gates");

  const pollQueue = readJson("metadata/historical-poll-reconstruction-queue.json");
  assert(pollQueue.status === "partial-first-party-reconstruction", "historical polling reconstruction status is stale");
  assert(pollQueue.candidateSource.sha256 === pollAudit.source.sha256, "polling queue and audit fingerprints differ");
  assert(pollQueue.candidateSource.declaredLicence === null, "polling queue must not invent reuse authority");
  assert(pollQueue.candidateSource.rawDataImported === false, "polling queue cannot import the unlicensed candidate data");
  assert(pollQueue.candidateSource.observationVoteRowsWritten === false, "polling queue cannot write vote rows from the quarantined lead list");
  assert(pollQueue.candidateSource.reconstructionMetadataWritten === true, "polling queue must record first-party reconstruction progress");
  assert(pollQueue.coverage.candidateRows === 200, "polling queue candidate count is stale");
  assert(pollQueue.coverage.sourceFamilies === 18, "polling queue source-family count is stale");
  assert(pollQueue.coverage.sourceMatchedRows === 57, "historical polling source-matched count is stale");
  assert(pollQueue.coverage.reconstructedRows === 0 && pollQueue.coverage.replayEligibleRows === 0, "unverified polling leads cannot be reconstructed or replay-eligible");
  assert(pollQueue.coverage.residualRows === 200, "polling queue residual count is stale");
  assert(JSON.stringify(pollQueue.coverage.requiredFieldCoverage) === JSON.stringify({
    publicationDate: 57,
    sampleSize: 57,
    explicitMethod: 35,
    observationSourceUrl: 57,
    declaredReuseLicence: 0,
  }), "polling queue required-field coverage is stale");
  assert(pollQueue.reconstructionQueue.length === pollQueue.coverage.sourceFamilies, "polling queue family count does not reconcile");
  assert(new Set(pollQueue.reconstructionQueue.map((family) => family.id)).size === pollQueue.coverage.sourceFamilies, "polling queue family ids must be unique");
  assert(pollQueue.reconstructionQueue.every((family, index) => family.priority === index + 1), "polling queue priorities must be contiguous");
  assert(pollQueue.reconstructionQueue.reduce((sum, family) => sum + family.candidateRows, 0) === pollQueue.coverage.candidateRows, "polling queue rows do not reconcile");
  assert(pollQueue.reconstructionQueue.reduce((sum, family) => sum + family.residualRows, 0) === pollQueue.coverage.residualRows, "polling queue residual rows do not reconcile");
  assert(pollQueue.reconstructionQueue.slice(0, 5).reduce((sum, family) => sum + family.candidateRows, 0) === 142, "polling queue high-priority coverage is stale");
  const essentialQueue = pollQueue.reconstructionQueue.find((family) => family.id === "essential");
  assert(essentialQueue?.sourceMatchedRows === 33 && essentialQueue.reconstructedRows === 0
    && essentialQueue.replayEligibleRows === 0 && essentialQueue.residualRows === 41, "Essential queue progress is stale or unsafe");
  const smsMorganQueue = pollQueue.reconstructionQueue.find((family) => family.id === "sms-morgan");
  assert(smsMorganQueue?.sourceMatchedRows === 24 && smsMorganQueue.reconstructedRows === 0
    && smsMorganQueue.replayEligibleRows === 0 && smsMorganQueue.residualRows === 33, "SMS Morgan queue progress is stale or unsafe");
  assert(pollQueue.coverage.cycles.every((cycle) => expectedPollRows.get(cycle.id) === cycle.candidateRows && cycle.residualRows === cycle.candidateRows), "polling queue cycle coverage is stale");
  assert(pollQueue.acceptanceRules.fieldworkMidpointAsPublicationDateAccepted === false, "polling queue cannot treat MidDate as publication date");
  assert(pollQueue.acceptanceRules.explicitReuseAuthorityRequired === true, "polling queue must require explicit reuse authority");
  assert(pollQueue.externalContact.status === "deferred", "polling repository contact must remain deferred while first-party reconstruction is pending");
  assert(Object.values(pollQueue.modelImpact).every((value) => value === false), "polling reconstruction queue cannot change forecasts or gates");

  const candidates = parseCsv(readFileSync(resolve(root, "model/data/processed/vec_2022_indicative_candidate_evidence.csv"), "utf8"));
  assert(candidates.length === 323, "expected 323 audited 2022 candidate-primary rows");
  assert(new Set(candidates.map((row) => row.district_id)).size === 39, "expected 39 districts with audited 2022 primary evidence");

  const crosswalk = readJson("model/config/historical-party-family-crosswalk.json");
  const expectedFamilies = ["ALP", "Coalition", "Greens", "One Nation", "Other/Independent"];
  assert(crosswalk.status === "frozen-fail-closed", "historical party crosswalk must be frozen and fail closed");
  assert(JSON.stringify(crosswalk.targetFamilies) === JSON.stringify(expectedFamilies), "historical party families differ from the complete model");
  assert(crosswalk.normalisation.trim === true, "party labels must be trimmed before exact matching");
  assert(crosswalk.normalisation.collapseWhitespace === true, "party-label whitespace must be normalised");
  assert(crosswalk.normalisation.caseFold === true, "party labels must be case folded");
  assert(crosswalk.normalisation.substringMatching === false, "substring party matching is unsafe");
  const normaliseAlias = (alias) => alias.trim().replace(/\s+/g, " ").toLocaleLowerCase("en-AU");
  const aliasOwners = new Map();
  for (const family of expectedFamilies) {
    assert(Array.isArray(crosswalk.aliases[family]) && crosswalk.aliases[family].length > 0, `missing aliases for ${family}`);
    for (const alias of crosswalk.aliases[family]) {
      assert(alias !== "*", "wildcard party aliases are forbidden");
      const normalised = normaliseAlias(alias);
      assert(!aliasOwners.has(normalised), `party alias ${alias} is assigned to more than one family`);
      aliasOwners.set(normalised, family);
    }
  }
  assert(crosswalk.independentCandidateRule.requiresExplicitIndependentStatus === true, "blank-party candidates require explicit independent status");
  assert(crosswalk.unknownPartyPolicy.action === "reject-row-and-require-adjudication", "unknown parties must fail closed");
  assert(crosswalk.unknownPartyPolicy.automaticOtherMapping === false, "unknown parties cannot map automatically to Other/Independent");
  assert(crosswalk.unknownPartyPolicy.requiresEvidenceLog === true, "party adjudications require an evidence log");
  assert(crosswalk.absentFamilyPolicy.action === "missing-until-no-contest-is-verified", "absent party families cannot be assumed");
  assert(crosswalk.absentFamilyPolicy.automaticZero === false, "missing party families cannot become automatic zeroes");
  assert(crosswalk.reconciliation.requireEveryFormalVoteMappedExactlyOnce === true, "every formal vote must map exactly once");
  assert(crosswalk.reconciliation.requireDistrictFamilySumEqualsFormalVotes === true, "district family totals must reconcile to formal votes");
  assert(crosswalk.reconciliation.allowNegativeVotes === false, "negative historical primary votes are invalid");
  assert(crosswalk.modelEligibility.crosswalkFrozen === true, "party crosswalk must be frozen before import");
  assert(crosswalk.modelEligibility.historicalPrimaryInputsComplete === true, "complete historical primaries must be marked complete");
  assert(crosswalk.modelEligibility.automaticGateOpening === false, "party crosswalk cannot open a gate automatically");

  const transfers = parseCsv(gunzipSync(readFileSync(resolve(root, "model/data/processed/vec_2022_preference_transfer_evidence.csv.gz"))).toString("utf8"));
  assert(transfers.length === 1204, "expected 1204 audited preference transfer rows");
  assert(new Set(transfers.map((row) => row.district_id)).size === 39, "expected 39 districts with preference distributions");
  const preferenceReport = readJson("model/data/processed/vec_2022_preference_evidence_build_report.json");
  const conditionalReport = readJson("model/data/processed/vec_2022_conditional_preference_validation_report.json");
  assert(preferenceReport.max_workbook_internal_reconstruction_abs_delta === 0, "preference workbook reconstruction is not exact");
  assert(conditionalReport.forecast_ready_source_parties.length === 0, "unapproved preference parameters detected");

  const council = readJson("model/data/seed/vec_2022_council_validation_targets.json");
  assert(council.regions.length === 8, "expected eight 2022 Council regions");
  assert(council.regions.reduce((sum, region) => sum + region.formal_votes, 0) === council.statewide_formal_votes, "Council formal votes do not reconcile");
  for (const region of council.regions) {
    assert(region.quota === Math.floor(region.formal_votes / (council.vacancies_per_region + 1)) + 1, `invalid quota for ${region.region_name}`);
    assert(region.elected_order.length === council.vacancies_per_region, `invalid elected set for ${region.region_name}`);
  }

  const councilEvidence = readJson("metadata/vec-2014-2022-council-evidence-audit.json");
  assert(councilEvidence.status === "partial-three-cycle-official-council-evidence", "Council evidence status is unexpected");
  assert(councilEvidence.coverage.cycles.length === 3, "Council evidence must cover the 2014, 2018 and 2022 cycles");
  assert(councilEvidence.coverage.regionCycleContests === 24, "expected 24 Council region-cycle contests");
  assert(councilEvidence.coverage.regionsPerCycle === 8, "expected eight Council regions per harvested cycle");
  assert(councilEvidence.coverage.candidateRows === 1185, "Council candidate-primary count is stale");
  assert(councilEvidence.coverage.countEvents === 5066, "Council count-event total is stale");
  assert(councilEvidence.coverage.countTotalRows === 268994, "Council count-total row count is stale");
  assert(councilEvidence.coverage.electedCandidates === 120, "Council elected-member total is stale");
  assert(councilEvidence.coverage.fingerprintedSources === 48, "Council source-manifest count is stale");
  assert(Object.values(councilEvidence.acceptance).every(Boolean), "Council evidence acceptance checks must all pass");
  assert(councilEvidence.regions.length === 24, "Council audit must contain one record per region-cycle contest");
  for (const year of [2014, 2018, 2022]) {
    const electionId = `vic_lc_${year}`;
    const regions = councilEvidence.regions.filter((region) => region.electionId === electionId);
    assert(regions.length === 8, `expected eight Council regions for ${year}`);
    const primaries = parseCsv(readFileSync(resolve(root, `model/data/processed/vec_${year}_council_candidate_primaries.csv`), "utf8"));
    assert(primaries.length === regions.reduce((sum, region) => sum + region.candidateRows, 0), `Council primary count differs for ${year}`);
    assert(new Set(primaries.map((row) => row.region_id)).size === 8, `Council primary regions differ for ${year}`);
    for (const region of regions) {
      const rows = primaries.filter((row) => row.region_id === region.regionId);
      assert(rows.reduce((sum, row) => sum + Number(row.first_preference_votes), 0) === region.formalVotes, `Council primaries do not reconcile for ${year} ${region.regionName}`);
      assert(region.quota === Math.floor(region.formalVotes / 6) + 1, `Council quota does not reconcile for ${year} ${region.regionName}`);
      assert(region.elected.length === 5, `Council elected set differs for ${year} ${region.regionName}`);
    }
    const countBuffer = gunzipSync(readFileSync(resolve(root, `model/data/processed/vec_${year}_council_preference_counts.csv.gz`)));
    let newlines = 0;
    for (const byte of countBuffer) if (byte === 10) newlines++;
    assert(newlines - 1 === regions.reduce((sum, region) => sum + region.countTotalRows, 0), `Council count-total rows differ for ${year}`);
  }

  const council2010 = readJson("metadata/vec-2010-council-evidence-audit.json");
  assert(council2010.status === "complete-official-2010-council-outcome-evidence", "2010 Council evidence status is unexpected");
  assert(council2010.coverage.regionCycleContests === 8, "expected eight 2010 Council regions");
  assert(council2010.coverage.candidateRows === 209, "2010 Council candidate-primary count is stale");
  assert(council2010.coverage.countEvents === 909, "2010 Council count-event total is stale");
  assert(council2010.coverage.countTotalRows === 27093, "2010 Council count-total row count is stale");
  assert(council2010.coverage.electedCandidates === 40, "2010 Council elected-member total is stale");
  assert(council2010.coverage.fingerprintedSources === 16, "2010 Council source-manifest count is stale");
  assert(Object.values(council2010.acceptance).every(Boolean), "2010 Council evidence acceptance checks must all pass");
  assert(council2010.regions.length === 8, "2010 Council audit must contain eight region records");
  const council2010Primaries = parseCsv(readFileSync(resolve(root, "model/data/processed/vec_2010_council_candidate_primaries.csv"), "utf8"));
  assert(council2010Primaries.length === 209, "2010 Council primary rows differ");
  assert(new Set(council2010Primaries.map((row) => row.region_id)).size === 8, "2010 Council primary regions differ");
  for (const region of council2010.regions) {
    const rows = council2010Primaries.filter((row) => row.region_id === region.regionId);
    assert(rows.reduce((sum, row) => sum + Number(row.first_preference_votes), 0) === region.formalVotes, `2010 Council primaries do not reconcile for ${region.regionName}`);
    assert(region.quota === Math.floor(region.formalVotes / 6) + 1, `2010 Council quota does not reconcile for ${region.regionName}`);
    assert(region.elected.length === 5, `2010 Council elected set differs for ${region.regionName}`);
  }
  const council2010CountBuffer = gunzipSync(readFileSync(resolve(root, "model/data/processed/vec_2010_council_preference_counts.csv.gz")));
  let council2010Newlines = 0;
  for (const byte of council2010CountBuffer) if (byte === 10) council2010Newlines++;
  assert(council2010Newlines - 1 === 27093, "2010 Council count-total rows differ");

  const councilRules = readJson("model/config/historical-council-count-rules.json");
  const councilRuleAudit = readJson("metadata/historical-council-count-rules-audit.json");
  const councilRuleSources = parseCsv(readFileSync(resolve(root, "metadata/historical-council-count-rule-source-manifest.csv"), "utf8"));
  assert(councilRules.status === "complete-cycle-pinned-authorised-legislation", "historical Council rule status is unexpected");
  assert(councilRules.vacanciesPerRegion === 5, "historical Council vacancy count must remain five per region");
  assert(councilRules.cycles.length === 4, "historical Council rules must cover four cycles");
  assert(councilRuleSources.length === 4, "historical Council rule manifest must contain four authorised Act versions");
  assert(councilRuleAudit.status === "complete-four-cycle-council-count-rule-evidence", "historical Council rule audit status is unexpected");
  assert(Object.values(councilRuleAudit.acceptance).every(Boolean), "historical Council rule acceptance checks must all pass");
  assert(councilRuleAudit.modelImpact.changesCurrentForecast === false, "historical Council rules cannot change the current forecast");
  assert(councilRuleAudit.modelImpact.historicalReplayEligible === false, "historical Council rules cannot independently authorise replay");
  assert(councilRuleAudit.modelImpact.probabilityCalibrationReady === false, "historical Council rules cannot independently authorise calibration");
  assert(councilRuleAudit.modelImpact.automaticGateOpening === false, "historical Council rules cannot open a gate");
  const expectedCouncilRuleCycles = new Map([
    ["vic_lc_2010", ["2010-11-27", "030"]],
    ["vic_lc_2014", ["2014-11-29", "040"]],
    ["vic_lc_2018", ["2018-11-24", "050"]],
    ["vic_lc_2022", ["2022-11-26", "064"]],
  ]);
  for (const cycle of councilRules.cycles) {
    const expected = expectedCouncilRuleCycles.get(cycle.id);
    assert(expected, `unexpected historical Council rule cycle ${cycle.id}`);
    assert(cycle.electionDate === expected[0], `incorrect Council election date for ${cycle.id}`);
    assert(cycle.actVersion === expected[1], `incorrect Electoral Act version for ${cycle.id}`);
    assert(Date.parse(`${cycle.effectiveFrom}T00:00:00Z`) <= Date.parse(`${cycle.electionDate}T00:00:00Z`), `Act version starts after election day for ${cycle.id}`);
    assert(Date.parse(`${cycle.effectiveThrough}T00:00:00Z`) >= Date.parse(`${cycle.electionDate}T00:00:00Z`), `Act version ended before election day for ${cycle.id}`);
    const source = councilRuleSources.find((row) => row.election_id === cycle.id);
    assert(source, `missing Council rule source for ${cycle.id}`);
    assert(source.act_version === cycle.actVersion, `Council rule manifest version differs for ${cycle.id}`);
    assert(source.sha256 === cycle.sha256, `Council rule manifest hash differs for ${cycle.id}`);
    assert(Number(source.bytes) === cycle.bytes, `Council rule manifest byte count differs for ${cycle.id}`);
    assert(source.material_rule_set_id === councilRules.materialRuleSetId, `Council rule-set id differs for ${cycle.id}`);
  }
  const allCouncilRegions = [...council2010.regions, ...councilEvidence.regions];
  assert(allCouncilRegions.length === 32, "Council rule reconciliation must cover 32 region-cycle contests");
  for (const region of allCouncilRegions) {
    assert(region.quota === Math.floor(region.formalVotes / (councilRules.vacanciesPerRegion + 1)) + 1, `Council rule quota does not reconcile for ${region.electionId} ${region.regionName}`);
    assert(region.elected.length === councilRules.vacanciesPerRegion, `Council rule vacancy count does not reconcile for ${region.electionId} ${region.regionName}`);
  }

  const historicalConfigs = readJson("model/config/historical-validation-cycles.json");
  const expectedCycleDates = new Map([
    ["vic_la_2010", ["2010-11-27", "2010-11-26"]],
    ["vic_la_2014", ["2014-11-29", "2014-11-28"]],
    ["vic_la_2018", ["2018-11-24", "2018-11-23"]],
    ["vic_la_2022", ["2022-11-26", "2022-11-25"]],
  ]);
  const expectedOutputs = new Set([
    "statewide-five-party-primary-votes",
    "district-five-party-primary-votes",
    "district-final-two-pairs",
    "district-winners-and-probabilities",
    "assembly-seat-count-distribution",
    "council-region-seat-distributions",
  ]);
  assert(historicalConfigs.status === "partial-unrunnable", "historical configurations must remain explicitly partial and unrunnable");
  assert(historicalConfigs.productionCompatible === false, "historical configurations cannot authorise production");
  assert(historicalConfigs.cycles.length === expectedCycleDates.size, "expected four frozen historical configurations");
  assert(new Set(historicalConfigs.cycles.map((cycle) => cycle.id)).size === expectedCycleDates.size, "historical cycle ids must be unique");
  assert(new Set(historicalConfigs.cycles.map((cycle) => cycle.seed)).size === expectedCycleDates.size, "historical seeds must be unique");
  assert(historicalConfigs.requiredOutputs.length === expectedOutputs.size
    && historicalConfigs.requiredOutputs.every((output) => expectedOutputs.has(output)), "historical configurations must target every published model output family");
  assert(historicalConfigs.leakageRules.enforcePublicationDateCutoff === true, "publication-date cutoff must be enforced");
  assert(historicalConfigs.leakageRules.electionOutcomes === "scoring-only", "election outcomes must be scoring-only");
  assert(Object.entries(historicalConfigs.leakageRules)
    .filter(([key]) => key !== "enforcePublicationDateCutoff" && key !== "electionOutcomes")
    .every(([, value]) => value === "forbidden"), "all post-cutoff and later-cycle inputs must be forbidden");
  assert(historicalConfigs.featurePolicy.demographicChallenger.included === false, "rejected demographic challenger cannot enter historical configurations");
  assert(historicalConfigs.featurePolicy.demographicChallenger.centralWeight === 0, "rejected demographic challenger must retain zero weight");
  assert(historicalConfigs.outcomeScoringPolicy.audit === "metadata/historical-assembly-outcome-availability.json", "historical configurations must use the outcome-date audit");
  assert(historicalConfigs.outcomeScoringPolicy.generalElectionScope === "contests-held-on-cycle-election-date", "cycle scores must be limited to election-day contests");
  assert(historicalConfigs.outcomeScoringPolicy.postCycleContests === "separate-scoring-only", "post-cycle contests must be scored separately");
  assert(historicalConfigs.outcomeScoringPolicy.unknownEvidencePublicationDate === "not-pre-cutoff-eligible", "unknown evidence dates cannot enter historical inputs");
  const expectedReplayBlockers = ["pre-election-poll-vintages", "ballot-and-contest-slates", "preference-flows-and-final-pairs"];
  for (const cycle of historicalConfigs.cycles) {
    const expectedDates = expectedCycleDates.get(cycle.id);
    assert(expectedDates, `unexpected historical cycle ${cycle.id}`);
    assert(cycle.electionDate === expectedDates[0], `incorrect election date for ${cycle.id}`);
    assert(cycle.informationCutoff === expectedDates[1], `incorrect information cutoff for ${cycle.id}`);
    assert(Date.parse(`${cycle.informationCutoff}T00:00:00Z`) < Date.parse(`${cycle.electionDate}T00:00:00Z`), `cutoff must precede election day for ${cycle.id}`);
    assert(Number.isSafeInteger(cycle.seed), `seed must be a safe integer for ${cycle.id}`);
    assert(cycle.runnable === false, `${cycle.id} must remain unrunnable until its inputs are complete`);
    assert(JSON.stringify(cycle.blockedBy) === JSON.stringify(expectedReplayBlockers), `${cycle.id} blockers must match the remaining partial evidence`);
    assert(cycle.blockedBy.every((id) => contractById.get(id)?.status === "partial"), `${cycle.id} cannot list completed evidence as a blocker`);
    assert(cycle.inputPolicy.publicationDateAtOrBeforeCutoff === true, `${cycle.id} must enforce its information cutoff`);
    assert(cycle.inputPolicy.outcomesAvailableToModel === false, `${cycle.id} outcomes cannot enter the model`);
    assert(cycle.inputPolicy.outcomesAvailableForScoring === true, `${cycle.id} outcomes must remain available for scoring`);
  }

  const negativeGate = readJson("model/data/processed/historical_structured_residual_validation_gate.json");
  assert(negativeGate.historical_structure_gate_passed === false, "rejected demographic challenger was unexpectedly promoted");
  assert(negativeGate.production_forecast_authorised === false, "negative feature test must not authorise production");
  assert(inventory.summary.completeForecastBacktestReady === false, "partial inventory cannot mark complete backtesting ready");
  assert(inventory.summary.probabilityCalibrationReady === false, "partial inventory cannot mark calibration ready");

  return inventory.summary;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const summary = validateModelValidationEvidence();
  console.log(`Model validation evidence: ${summary.complete} complete, ${summary.partial} partial, ${summary.missing} missing; complete-model gates remain closed.`);
}
