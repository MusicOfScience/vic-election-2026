import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = process.cwd();
const baselinePath = resolve(root, "model/data/validation/historical-replay-2014-assembly-notional-baseline.csv");
const outputPath = resolve(root, "model/data/validation/historical-replay-2014-ballot-mask.csv");
const sourceUrl = "https://www.abc.net.au/news/2014-11-14/2014-victorian-election---summary-of-nominations/9388508";
const sourceSha256 = "13d222c66c96a7013bfbb579b417de6a4cf6c1a5eef03bdea4a33bdf01e67f1c";
const noResidualSeats = new Set(["Hawthorn", "Kew", "Malvern"]);

const [header, ...lines] = readFileSync(baselinePath, "utf8").trim().split("\n");
const baselineColumns = header.split(",");
const index = Object.fromEntries(baselineColumns.map((name, position) => [name, position]));
const rows = lines.map((line) => line.split(","));
if (rows.length !== 88 || new Set(rows.map((row) => row[index.district_id])).size !== 88) throw new Error("2014 ballot mask requires exactly 88 unique districts");

const output = [
  "election_id,district_id,district_name,ballot_active_families,incumbent_party_family,source_url,source_sha256,evidence_publication_date,boundary_basis,availability_basis",
  ...rows.map((row) => {
    const districtName = row[index.district_name];
    const families = ["ALP", "LIB_NAT", "GRN", ...(noResidualSeats.has(districtName) ? [] : ["OTH_IND"])];
    const incumbent = row[index.notional_holder_family];
    if (!families.includes(incumbent)) throw new Error(`notional holder ${incumbent} is not ballot-active in ${districtName}`);
    return [
      row[index.election_id], row[index.district_id], districtName,
      JSON.stringify(families), incumbent, sourceUrl, sourceSha256, "2014-11-13",
      "2013 Victorian redistribution / 2014 ABC election guide",
      "ABC contemporaneous nominations summary: ALP and Greens in all 88; 92 Liberal/National candidates across 88; only Hawthorn, Kew and Malvern have three candidates, so no Other/Independent family",
    ].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",");
  }),
];
writeFileSync(outputPath, `${output.join("\n")}\n`);
console.log(`Wrote ${rows.length} cutoff-safe 2014 ballot-mask rows to ${outputPath}`);
