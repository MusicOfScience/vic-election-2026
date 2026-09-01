import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const character = text[i];
    if (character === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (character === '"') quoted = !quoted;
    else if (character === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += character;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function load(path) {
  return readFileSync(new URL(`../${path}`, import.meta.url));
}

function sha256(path) {
  return createHash("sha256").update(load(path)).digest("hex");
}

const candidatePath = "model/data/processed/vec_2010_assembly_candidate_primaries.csv";
const familyPath = "model/data/processed/vec_2010_assembly_family_primaries.csv";
const audit = JSON.parse(load("metadata/vec-2010-assembly-primary-audit.json"));
const crosswalk = JSON.parse(load("model/config/historical-party-family-crosswalk.json"));
const candidates = parseCsv(load(candidatePath).toString("utf8"));
const families = parseCsv(load(familyPath).toString("utf8"));

test("extracts every 2010 Assembly candidate from the fingerprinted VEC report", () => {
  assert.equal(audit.status, "complete-2010-outcome-evidence");
  assert.equal(audit.source.sha256, "be2dbabd5735ff7128fa9ac5ab3e05e99d41c3d7a4502d33959b7c3464da7567");
  assert.equal(audit.source.pages, 1088);
  assert.equal(Object.keys(audit.source.assemblyDistrictTablePages).length, 88);
  assert.equal(candidates.length, 502);
  assert.equal(new Set(candidates.map((row) => row.district_id)).size, 88);
  assert.ok(candidates.every((row) => row.election_id === "vic_la_2010"));
  assert.ok(candidates.every((row) => row.source_sha256 === audit.source.sha256));
  assert.ok(candidates.every((row) => row.candidate_name.split(",").length === 2));
  assert.ok(candidates.every((row) => Number.isSafeInteger(Number(row.first_preference_votes))));
  assert.ok(candidates.every((row) => Number(row.first_preference_votes) >= 0));
  assert.ok(candidates.every((row) => row.district_reconciled === "True"));
  assert.equal(candidates.reduce((sum, row) => sum + Number(row.first_preference_votes), 0), 3_164_729);

  const expectedLabels = new Set([
    "",
    "AUSTRALIAN GREENS",
    "AUSTRALIAN LABOR PARTY",
    "CHRISTIAN PARTY",
    "COUNTRY ALLIANCE",
    "D.L.P. - DEMOCRATIC LABOR PARTY",
    "FAMILY FIRST",
    "LIBERAL",
    "SEX PARTY",
    "SOCIALIST ALLIANCE",
    "THE NATIONALS",
  ]);
  assert.deepEqual(new Set(candidates.map((row) => row.party_raw)), expectedLabels);
  assert.ok(candidates.filter((row) => row.party_raw === "").every((row) => row.independent_status === "True"));
  assert.ok(candidates.filter((row) => row.party_raw !== "").every((row) => row.independent_status === "False"));

  for (const districtId of new Set(candidates.map((row) => row.district_id))) {
    const rows = candidates.filter((row) => row.district_id === districtId);
    assert.deepEqual(rows.map((row) => Number(row.candidate_order)), rows.map((_, index) => index + 1));
    assert.equal(new Set(rows.map((row) => Number(row.formal_votes))).size, 1);
    assert.equal(
      rows.reduce((sum, row) => sum + Number(row.first_preference_votes), 0),
      Number(rows[0].formal_votes),
      `${districtId} candidate votes must reconcile`,
    );
  }
});

test("reconciles all 88 districts to the frozen five-party family crosswalk", () => {
  const expectedFamilies = ["ALP", "Coalition", "Greens", "One Nation", "Other/Independent"];
  assert.equal(families.length, 440);
  assert.equal(new Set(families.map((row) => row.district_id)).size, 88);
  assert.deepEqual(crosswalk.targetFamilies, expectedFamilies);
  assert.equal(crosswalk.status, "frozen-fail-closed");
  assert.equal(crosswalk.schemaVersion, 2);
  assert.equal(crosswalk.sourceAdjudications.length, 1);
  assert.equal(crosswalk.sourceAdjudications[0].sourceSha256, audit.source.sha256);

  for (const districtId of new Set(families.map((row) => row.district_id))) {
    const rows = families.filter((row) => row.district_id === districtId);
    assert.deepEqual(rows.map((row) => row.party_family), expectedFamilies);
    assert.equal(new Set(rows.map((row) => Number(row.formal_votes))).size, 1);
    assert.equal(
      rows.reduce((sum, row) => sum + Number(row.first_preference_votes), 0),
      Number(rows[0].formal_votes),
      `${districtId} family votes must reconcile`,
    );
    assert.ok(rows.filter((row) => row.contest_status === "verified_no_contest")
      .every((row) => Number(row.candidate_count) === 0 && Number(row.first_preference_votes) === 0));
    assert.ok(rows.filter((row) => row.contest_status === "contested")
      .every((row) => Number(row.candidate_count) > 0 && Number(row.first_preference_votes) > 0));
  }

  assert.equal(audit.outputs.find((output) => output.path === candidatePath).sha256, sha256(candidatePath));
  assert.equal(audit.outputs.find((output) => output.path === familyPath).sha256, sha256(familyPath));
  assert.equal(audit.checks.allDistrictCandidateTotalsReconciled, true);
  assert.equal(audit.checks.allDistrictFamilyTotalsReconciled, true);
  assert.equal(audit.use.currentForecast, "excluded");
  assert.equal(audit.use.automaticGateOpening, false);
  assert.equal(audit.use.productionAuthorisation, false);
});
