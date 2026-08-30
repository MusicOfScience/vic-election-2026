import { readFileSync } from "node:fs";
import { resolve } from "node:path";

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

const COUNCIL_CONTEST_ALIASES = new Map([
  ["north-east metro", "north-eastern metropolitan"],
  ["northern metro", "northern metropolitan"],
  ["south-east metro", "south-eastern metropolitan"],
  ["southern metro", "southern metropolitan"],
  ["western metro", "western metropolitan"],
]);

function contestKey(value) {
  const key = String(value ?? "")
    .normalize("NFKC")
    .trim()
    .replace(/\s+region$/i, "")
    .replace(/\s+/g, " ")
    .toLowerCase();
  return COUNCIL_CONTEST_ALIASES.get(key) ?? key;
}

export function loadContestUniverse(root) {
  const assemblyRows = parseCsv(readFileSync(resolve(root, "model/data/processed/experimental_forecast_2026_districts.csv"), "utf8"));
  const councilRows = parseCsv(readFileSync(resolve(root, "model/data/processed/experimental_forecast_2026_council_regions.csv"), "utf8"));
  return {
    assembly: new Map(assemblyRows.map((row) => [contestKey(row.district_name), row.district_name])),
    council: new Map(councilRows.map((row) => [contestKey(row.region_name), row.region_name])),
  };
}

export function classifyContest(contest, universe) {
  const key = contestKey(contest);
  if (universe.assembly.has(key)) return { chamber: "assembly", canonicalContest: universe.assembly.get(key) };
  if (universe.council.has(key)) return { chamber: "council", canonicalContest: universe.council.get(key) };
  return null;
}
