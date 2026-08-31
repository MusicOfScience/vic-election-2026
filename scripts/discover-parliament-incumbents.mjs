import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function arg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        field += '"';
        index++;
      } else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ',') {
      row.push(field);
      field = "";
    } else if (char === '\n') {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else field += char;
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((item) => item.some((value) => value.trim()));
}

function key(value) {
  return String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function columnIndex(headers, aliases) {
  const normalised = headers.map(key);
  for (const alias of aliases.map(key)) {
    const index = normalised.indexOf(alias);
    if (index >= 0) return index;
  }
  return -1;
}

function canonicalParty(party) {
  const value = party.trim();
  const lower = value.toLowerCase();
  if (lower.includes("labor")) return "Labor";
  if (lower === "lp" || lower.includes("liberal")) return "Liberal";
  if (lower === "np" || lower.includes("national")) return "Nationals";
  if (lower === "ag" || lower.includes("green")) return "Greens";
  if (lower.includes("independent")) return "Independent";
  return value || "Unknown";
}

export function extractAssemblyIncumbents(csv) {
  const rows = parseCsv(csv);
  if (rows.length < 2) throw new Error("Assembly member CSV has no data rows");
  const headers = rows[0];
  const nameIndex = columnIndex(headers, ["Full Name", "Member", "Member Name", "Name"]);
  const electorateIndex = columnIndex(headers, ["Electorate", "District"]);
  const partyIndex = columnIndex(headers, ["Party", "Political Party"]);
  if (nameIndex < 0 || electorateIndex < 0) {
    throw new Error(`Required incumbent columns not found: ${headers.join(" | ")}`);
  }

  return rows.slice(1).flatMap((row) => {
    const name = String(row[nameIndex] ?? "").trim();
    const electorate = String(row[electorateIndex] ?? "").trim();
    const party = partyIndex >= 0 ? String(row[partyIndex] ?? "").trim() : "";
    if (!name || !electorate) return [];
    return [{
      name,
      electorate,
      party,
      canonicalParty: canonicalParty(party),
      house: "Legislative Assembly",
      incumbencyStatus: "current-member",
    }];
  });
}

async function main() {
  const output = resolve(root, arg("--output", "parliament-incumbents-report.json"));
  const source = JSON.parse(readFileSync(resolve(root, "metadata/parliament-incumbent-source-2026.json"), "utf8"));
  const response = await fetch(source.csvUrl, {
    headers: { "user-agent": "vic-election-forecast-incumbency/1.0 (+https://github.com/MusicOfScience/vic-election-2026)" },
    redirect: "follow",
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) throw new Error(`Parliament Assembly CSV HTTP ${response.status}`);
  const csv = await response.text();
  const records = extractAssemblyIncumbents(csv);
  const electorates = new Set(records.map((record) => record.electorate.toLowerCase()));
  const minimum = source.expectedCurrentMembers.minimum;
  const maximum = source.expectedCurrentMembers.maximum;
  if (records.length < minimum || records.length > maximum) {
    throw new Error(`Unexpected Assembly incumbent count ${records.length}; expected ${minimum}-${maximum}`);
  }
  if (electorates.size !== records.length) {
    throw new Error(`Duplicate Assembly electorate records: ${records.length} members across ${electorates.size} electorates`);
  }

  const report = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    sourceId: source.id,
    publisher: source.publisher,
    landingPageUrl: source.landingPageUrl,
    sourceUrl: source.csvUrl,
    sourceSha256: sha256(csv),
    authorityType: source.authorityType,
    policy: source.policy,
    automaticPromotion: false,
    summary: {
      currentMembers: records.length,
      representedDistricts: electorates.size,
      expectedDistricts: source.expectedDistricts,
      vacancies: source.expectedDistricts - electorates.size,
    },
    records,
  };
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Parliament incumbency: ${records.length} current Assembly members across ${electorates.size}/88 districts; ${report.summary.vacancies} vacancies.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
