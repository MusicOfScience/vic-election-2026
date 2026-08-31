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

  const candidates = parseCsv(readFileSync(resolve(root, "model/data/processed/vec_2022_indicative_candidate_evidence.csv"), "utf8"));
  assert(candidates.length === 323, "expected 323 audited 2022 candidate-primary rows");
  assert(new Set(candidates.map((row) => row.district_id)).size === 39, "expected 39 districts with audited 2022 primary evidence");

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
