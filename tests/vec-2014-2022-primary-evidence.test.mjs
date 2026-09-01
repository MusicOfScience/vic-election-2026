import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";

function load(path) {
  return readFileSync(new URL(`../${path}`, import.meta.url));
}

function sha256(path) {
  return createHash("sha256").update(load(path)).digest("hex");
}

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let index = 0; index < text.length; index++) {
    const character = text[index];
    if (character === '"' && quoted && text[index + 1] === '"') { cell += '"'; index++; }
    else if (character === '"') quoted = !quoted;
    else if (character === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && text[index + 1] === "\n") index++;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += character;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

const audit = JSON.parse(load("metadata/vec-2014-2022-assembly-primary-audit.json"));
const crosswalk = JSON.parse(load("model/config/historical-party-family-crosswalk.json"));
const expected = {
  2014: { candidates: 545, formal: 3_355_707 },
  2018: { candidates: 507, formal: 3_514_474 },
  2022: { candidates: 742, formal: 3_654_205 },
};

test("fingerprints the complete official VEC source manifest", () => {
  const manifest = parseCsv(load(audit.sourceManifest).toString("utf8"));
  assert.equal(manifest.length, 267);
  assert.equal(manifest.filter((row) => row.district_name === "[summary]").length, 3);
  assert.equal(manifest.filter((row) => row.district_name !== "[summary]").length, 264);
  assert.ok(manifest.every((row) => /^[a-f0-9]{64}$/.test(row.sha256)));
  assert.equal(sha256(audit.sourceManifest), "aa47f31be9c072b4d2a104f167070741dfc8261888048a42ae4373d5f9f10912");
});

for (const [year, counts] of Object.entries(expected)) {
  test(`reconciles every ${year} Assembly district and five-family target`, () => {
    const candidatePath = `model/data/processed/vec_${year}_assembly_candidate_primaries.csv`;
    const familyPath = `model/data/processed/vec_${year}_assembly_family_primaries.csv`;
    const candidates = parseCsv(load(candidatePath).toString("utf8"));
    const families = parseCsv(load(familyPath).toString("utf8"));
    const districts = new Set(candidates.map((row) => row.district_id));

    assert.equal(candidates.length, counts.candidates);
    assert.equal(districts.size, 88);
    assert.equal(families.length, 440);
    assert.equal(new Set(families.map((row) => row.district_id)).size, 88);
    assert.equal(candidates.reduce((sum, row) => sum + Number(row.first_preference_votes), 0), counts.formal);
    assert.equal(families.reduce((sum, row) => sum + Number(row.first_preference_votes), 0), counts.formal);

    for (const districtId of districts) {
      const districtCandidates = candidates.filter((row) => row.district_id === districtId);
      const districtFamilies = families.filter((row) => row.district_id === districtId);
      const formal = Number(districtCandidates[0].formal_votes);
      assert.equal(districtCandidates.reduce((sum, row) => sum + Number(row.first_preference_votes), 0), formal);
      assert.equal(districtFamilies.reduce((sum, row) => sum + Number(row.first_preference_votes), 0), formal);
    }

    assert.equal(audit.outputs.find((output) => output.path === candidatePath).sha256, sha256(candidatePath));
    assert.equal(audit.outputs.find((output) => output.path === familyPath).sha256, sha256(familyPath));
  });
}

test("keeps the four-cycle primary evidence fail-closed and forecast-excluded", () => {
  assert.equal(audit.status, "complete-2014-2022-assembly-primary-evidence");
  assert.deepEqual(audit.checks.existing2022IndicativeOverlap, { rowsChecked: 323, districtsChecked: 39, mismatches: 0 });
  assert.equal(audit.checks.allCandidateTotalsReconciled, true);
  assert.equal(audit.checks.allFamilyTotalsReconciled, true);
  assert.equal(audit.checks.allPartyLabelsAdjudicated, true);
  assert.equal(crosswalk.schemaVersion, 3);
  assert.equal(crosswalk.status, "frozen-fail-closed");
  assert.equal(crosswalk.modelEligibility.historicalPrimaryInputsComplete, true);
  assert.equal(crosswalk.unknownPartyPolicy.automaticOtherMapping, false);
  assert.equal(audit.use.currentForecast, "excluded");
  assert.equal(audit.use.automaticGateOpening, false);
  assert.equal(audit.use.productionAuthorisation, false);
});
