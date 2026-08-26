#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const sourceRoot = resolve(process.argv[2] ?? "../model");
const outputPath = resolve(process.argv[3] ?? "app/data.generated.ts");

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    const next = text[index + 1];

    if (character === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (character === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && next === "\n") index += 1;
      row.push(field);
      field = "";
      if (row.some((value) => value.length > 0)) rows.push(row);
      row = [];
    } else {
      field += character;
    }
  }

  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }

  const [headers, ...records] = rows;
  return records.map((record) =>
    Object.fromEntries(headers.map((header, index) => [header, record[index] ?? ""])),
  );
}

function readCsv(relativePath) {
  return parseCsv(readFileSync(resolve(sourceRoot, relativePath), "utf8"));
}

const districtConfig = readFileSync(resolve(sourceRoot, "config/current_districts.yml"), "utf8");
const configuredDistricts = [...districtConfig.matchAll(/^- id: (.+)\n  name: (.+)$/gm)].map(
  ([, id, name]) => ({ id, name }),
);

const tppRows = readCsv("data/processed/vec_2022_all_district_tpp.csv");
const enrolmentRows = readCsv("data/processed/vec_enrolment_district_2026-06.csv");
const membershipRows = readCsv("data/processed/district_region_membership_2026.csv");

const byTpp = new Map(tppRows.map((row) => [row.district_id, row]));
const byEnrolment = new Map(enrolmentRows.map((row) => [row.geography_name, row]));
const byMembership = new Map(membershipRows.map((row) => [row.district_name, row]));

const districts = configuredDistricts.map(({ id, name }) => {
  const tpp = byTpp.get(id);
  const enrolment = byEnrolment.get(name);
  const membership = byMembership.get(name);
  const alpTpp = tpp ? Number(tpp.state_alp_tpp_share) * 100 : null;

  return {
    id,
    name,
    region: membership?.region_name ?? "Unassigned",
    enrolment: enrolment ? Number(enrolment.enrolled_electors) : null,
    enrolmentVariance: enrolment ? Number(enrolment["Variance to Average (%)"]) : null,
    alpTpp2022: alpTpp,
    marginFromFifty: alpTpp === null ? null : Math.abs(alpTpp - 50),
    tppMethod: tpp?.vec_tpp_method ?? "Not available",
  };
});

const foldRows = readCsv(
  "data/processed/historical_structured_residual_validation_fold_metrics.csv",
);

const validationFolds = foldRows.map((row) => ({
  cycle: row.cycle_id.replace("vic_la_", ""),
  districts: Number(row.district_rows),
  baselineMae: Number(row.baseline_mae) * 100,
  candidateMae: Number(row.candidate_mae) * 100,
  baselineRmse: Number(row.baseline_rmse) * 100,
  candidateRmse: Number(row.candidate_rmse) * 100,
  baselineWinnerErrors: Number(row.baseline_winner_errors),
  candidateWinnerErrors: Number(row.candidate_winner_errors),
}));

const generated = `// Generated from the sealed 14 August 2026 model checkpoint.\n` +
  `// Run: node scripts/generate-dashboard-data.mjs /path/to/model-checkout\n\n` +
  `export const districts = ${JSON.stringify(districts, null, 2)} as const;\n\n` +
  `export const validationFolds = ${JSON.stringify(validationFolds, null, 2)} as const;\n`;

writeFileSync(outputPath, generated, "utf8");
console.log(`Generated ${districts.length} districts and ${validationFolds.length} validation folds.`);
