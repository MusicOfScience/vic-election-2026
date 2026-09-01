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
  assert(pollPublicAudit.externalContact.status === "deferred", "polling repository contact must remain deferred");

  assert(acquisition.modelImpact.changesCurrentForecast === false, "source acquisition cannot change the current forecast");
  assert(acquisition.modelImpact.automaticPromotion === false, "source responses cannot promote automatically");
  assert(acquisition.modelImpact.automaticGateOpening === false, "source acquisition cannot open gates");
  assert(publicAudit.modelImpact.changesCurrentForecast === false, "public source audit cannot change the current forecast");
  assert(publicAudit.modelImpact.productionAuthorisation === false, "public source audit cannot authorise production");
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
  for (const cycle of historicalConfigs.cycles) {
    const expectedDates = expectedCycleDates.get(cycle.id);
    assert(expectedDates, `unexpected historical cycle ${cycle.id}`);
    assert(cycle.electionDate === expectedDates[0], `incorrect election date for ${cycle.id}`);
    assert(cycle.informationCutoff === expectedDates[1], `incorrect information cutoff for ${cycle.id}`);
    assert(Date.parse(`${cycle.informationCutoff}T00:00:00Z`) < Date.parse(`${cycle.electionDate}T00:00:00Z`), `cutoff must precede election day for ${cycle.id}`);
    assert(Number.isSafeInteger(cycle.seed), `seed must be a safe integer for ${cycle.id}`);
    assert(cycle.runnable === false, `${cycle.id} must remain unrunnable until its inputs are complete`);
    assert(cycle.blockedBy.includes("pre-election-poll-vintages"), `${cycle.id} must disclose the missing polling vintages`);
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
