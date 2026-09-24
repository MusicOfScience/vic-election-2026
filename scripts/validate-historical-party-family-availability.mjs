import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);
const readJson = (name) => JSON.parse(readFileSync(resolve(root, name), "utf8"));

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const ch = text[index];
    if (ch === '"' && quoted && text[index + 1] === '"') { cell += '"'; index += 1; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[index + 1] === "\n") index += 1;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((key, index) => [key, values[index] ?? ""])));
}

export function validateHistoricalPartyFamilyAvailability() {
  const contract = readJson("metadata/historical-party-family-availability.json");
  for (const cycle of contract.cycles) {
    const rows = parseCsv(readFileSync(resolve(root, cycle.candidateEvidencePath), "utf8"))
      .filter((row) => !row.contest || row.contest === "general-election");
    const families = [...new Set(rows.map((row) => row.party_family))];
    for (const family of contract.canonicalFamilies) {
      const familyRows = rows.filter((row) => row.party_family === family);
      const districts = new Set(familyRows.map((row) => row.district_id));
      if ((cycle.familyCandidateRows[family] ?? 0) !== familyRows.length || (cycle.districtsWithCandidates[family] ?? 0) !== districts.size) {
        throw new Error(`historical party availability: ${cycle.cycleId} ${family} count mismatch`);
      }
    }
    if (families.length === 0 || !cycle.ballotActiveFamilies.includes("ALP") || !cycle.ballotActiveFamilies.includes("Other/Independent")) {
      throw new Error(`historical party availability: incomplete active-family set for ${cycle.cycleId}`);
    }
    if (cycle.cycleId === "vic_la_2018" && cycle.ballotActiveFamilies.includes("One Nation")) {
      throw new Error("historical party availability: 2018 One Nation must remain inactive");
    }
  }
  return { cycles: contract.cycles.length, verifiedFromCandidateEvidence: true, historicalOnpInactiveThrough2018: true };
}

if (process.argv[1]?.endsWith("validate-historical-party-family-availability.mjs")) {
  console.log(JSON.stringify(validateHistoricalPartyFamilyAvailability()));
}
