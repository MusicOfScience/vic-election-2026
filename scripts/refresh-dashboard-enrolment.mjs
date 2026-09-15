#!/usr/bin/env node

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const dashboardPath = resolve(process.argv[2] ?? "app/data.generated.ts");
const enrolmentPath = resolve(process.argv[3] ?? "model/data/processed/vec_enrolment_district_2026-09-04.csv");

function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) => Object.fromEntries(line.split(",").map((value, index) => [headers[index], value])));
}

function readExport(text, exportName, nextExportName = null) {
  const marker = `export const ${exportName} = `;
  const start = text.indexOf(marker);
  const boundary = nextExportName ? text.indexOf(`export const ${nextExportName} = `, start) : text.length;
  const end = text.lastIndexOf(" as const;", boundary);
  if (start < 0 || end < start) throw new Error(`Cannot read ${exportName} from dashboard data`);
  return JSON.parse(text.slice(start + marker.length, end));
}

export function refreshDashboardEnrolment(dashboardText, enrolmentText) {
  const districts = readExport(dashboardText, "districts", "validationFolds");
  const validationFolds = readExport(dashboardText, "validationFolds");
  const enrolment = parseCsv(enrolmentText);
  const byName = new Map(enrolment.map((row) => [row.geography_name, row]));
  if (districts.length !== 88 || enrolment.length !== 88) {
    throw new Error(`Expected 88 dashboard districts and 88 enrolment rows; found ${districts.length} and ${enrolment.length}`);
  }
  const missing = districts.filter((district) => !byName.has(district.name)).map((district) => district.name);
  if (missing.length) throw new Error(`Missing enrolment for: ${missing.join(", ")}`);
  const refreshed = districts.map((district) => {
    const row = byName.get(district.name);
    return {
      ...district,
      enrolment: Number(row.enrolled_electors),
      enrolmentVariance: Number(row["Variance to Average (%)"]),
    };
  });
  return `// District enrolment refreshed from the validated VEC 4 September 2026 extract.\n` +
    `// Run: node scripts/refresh-dashboard-enrolment.mjs\n\n` +
    `export const districts = ${JSON.stringify(refreshed, null, 2)} as const;\n\n` +
    `export const validationFolds = ${JSON.stringify(validationFolds, null, 2)} as const;\n`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = refreshDashboardEnrolment(
    readFileSync(dashboardPath, "utf8"),
    readFileSync(enrolmentPath, "utf8"),
  );
  writeFileSync(dashboardPath, output, "utf8");
  console.log("Refreshed dashboard enrolment for 88 districts.");
}
