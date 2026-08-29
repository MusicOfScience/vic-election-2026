import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}
function readJson(path) { return JSON.parse(readFileSync(resolve(path), "utf8")); }
function parseCsv(text) {
  const [header, ...rows] = text.trim().split(/\r?\n/).map((line) => line.split(","));
  return rows.map((row) => Object.fromEntries(header.map((key, index) => [key, row[index]])));
}
function round(value, digits = 1) { return Number(Number(value).toFixed(digits)); }

export function buildAnalystComparison(model, chamberRows, sources, evidence) {
  const sourceById = new Map(sources.sources.map((source) => [source.id, source]));
  const chamber = Object.fromEntries(chamberRows.map((row) => [row.party, row]));
  const records = [];

  for (const item of evidence.records) {
    const source = sourceById.get(item.analystSourceId);
    const base = {
      evidenceId: item.id,
      analyst: source?.displayName ?? item.analystSourceId,
      sourceFamily: source?.sourceFamily ?? item.analystSourceId,
      publishedDate: item.publishedDate,
      sourceUrl: item.sourceUrl,
      evidenceType: item.evidenceType,
      modelUsage: item.modelUsage,
      independenceAssessment: item.independenceAssessment,
      comparisonMode: "context",
    };

    if (item.structuredFindings?.aggregatePrimaryVote) {
      const analyst = item.structuredFindings.aggregatePrimaryVote;
      const mapping = { labor: "ALP", coalition: "LIB_NAT", oneNation: "ONP", greens: "GRN", others: "OTH_IND" };
      const deltas = {};
      for (const [key, party] of Object.entries(mapping)) {
        if (analyst[key] !== undefined) deltas[key] = round(model.polling.mean[party] - analyst[key], 1);
      }
      records.push({ ...base, comparisonMode: "poll-aggregate-comparator", analystPrimaryVote: analyst, modelPrimaryVote: {
        labor: round(model.polling.mean.ALP), coalition: round(model.polling.mean.LIB_NAT), oneNation: round(model.polling.mean.ONP), greens: round(model.polling.mean.GRN), others: round(model.polling.mean.OTH_IND),
      }, modelMinusAnalystPp: deltas });
      continue;
    }

    if (item.structuredFindings?.seatProjectionUsingRauePreferenceFlows) {
      records.push({ ...base, comparisonMode: "scenario-seat-comparator", analystScenarioPrimaryVote: item.structuredFindings.scenarioPrimaryVote, analystSeatProjection: item.structuredFindings.seatProjectionUsingRauePreferenceFlows, currentModelMedianSeats: {
        labor: Number(chamber.ALP.median), coalition: Number(chamber.LIB_NAT.median), oneNation: Number(chamber.ONP.median), greens: Number(chamber.GRN.median),
      }, caution: "Not a like-for-like forecast comparison: the analyst projection uses a specified MRP primary-vote scenario and different preference assumptions." });
      continue;
    }

    if (item.analystSourceId === "antony-green") {
      records.push({ ...base, comparisonMode: "structural-check", analystFindings: item.structuredFindings, currentModel: {
        hungProbability: round(model.assembly.hung_probability * 100, 1),
        medianSeats: { labor: Number(chamber.ALP.median), coalition: Number(chamber.LIB_NAT.median), oneNation: Number(chamber.ONP.median), greens: Number(chamber.GRN.median) },
      }, caution: "Structural evidence is a diagnostic and sensitivity target, not a pseudo-poll or direct forecast weight." });
      continue;
    }

    records.push({ ...base, analystFindings: item.structuredFindings ?? null });
  }

  return {
    schemaVersion: 1,
    modelForecastId: model.forecast_id,
    modelAsOf: model.as_of,
    generatedFromEvidenceReviewedAt: evidence.reviewedAt,
    policy: "comparison-not-averaging",
    summary: {
      evidenceRecords: records.length,
      sourceFamilies: new Set(records.map((record) => record.sourceFamily)).size,
      directModelInputsAdded: 0,
      currentHungProbabilityPct: round(model.assembly.hung_probability * 100, 1),
    },
    interpretationRules: [
      "Analyst outputs are compared with the model; they are not averaged into polling as extra observations.",
      "Poll-derived analyst work retains dependency on its upstream polls.",
      "Scenario projections are not treated as like-for-like forecasts when their assumed primary votes differ from the current model.",
      "Structural findings are candidates for sensitivity tests and backtesting before any model-weight change."
    ],
    records,
  };
}

function main() {
  const model = readJson(arg("--model", "model/data/processed/experimental_forecast_2026.json"));
  const chamber = parseCsv(readFileSync(resolve(arg("--chamber", "model/data/processed/experimental_forecast_2026_chamber.csv")), "utf8"));
  const sources = readJson(arg("--sources", "metadata/psephology-sources.json"));
  const evidence = readJson(arg("--evidence", "metadata/psephology-evidence-2026.json"));
  const report = buildAnalystComparison(model, chamber, sources, evidence);
  const output = arg("--output", "analyst-comparison-report.json");
  writeFileSync(resolve(output), `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Analyst comparison: ${report.summary.evidenceRecords} evidence records across ${report.summary.sourceFamilies} source families; 0 direct model inputs added.`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
