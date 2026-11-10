import assert from "node:assert/strict";
import test from "node:test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import roster from "../app/vec-official-candidates-2026.review.json" with { type: "json" };
import audit from "../metadata/vec-nominations-2026-11-10-source-audit.json" with { type: "json" };

const source = resolve(import.meta.dirname, "../metadata/vec-official-candidates-2026-11-10.review.csv");
const raw = readFileSync(source);
const sha256 = createHash("sha256").update(raw).digest("hex");

function parseCsv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (c === '"') quoted = !quoted;
    else if (c === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((v) => v !== "")) rows.push(row);
      row = [];
    } else cell += c;
  }
  if (quoted) throw new Error("Unterminated CSV quote");
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
}

const data = parseCsv(raw.toString("utf8"));
const [columns, ...records] = data;

test("app candidate roster is byte-linked to captured VEC source evidence", () => {
  assert.equal(roster.schemaVersion, 1);
  assert.equal(roster.status, "official-VEC-source-review-only");
  assert.equal(roster.candidateRegistryPromoted, false);
  assert.equal(roster.forecastInputsChanged, false);
  assert.equal(roster.councilGroupVerified, false);
  assert.equal(roster.sourceFileSha256, audit.sourceSha256);
  assert.equal(roster.derivedCsvSha256, sha256);
  assert.deepEqual(roster.columns, ["chamber","contest","rowOrdinal","candidate","registeredParty"]);
  assert.deepEqual(columns, roster.columns);
  assert.equal(audit.contestCounts.totalCandidates, 1037);
});

test("every official candidate exactly matches the privacy-minimised CSV", () => {
  const expected = records.map(([chamber, contest, ordinal, candidate, party]) =>
    [chamber, contest, Number(ordinal), candidate, party || null]);
  assert.deepEqual(roster.rows, expected);
  assert.equal(roster.rows.length, 1037);
  assert.equal(roster.rows.filter((row) => row[0] === "Assembly").length, 734);
  assert.equal(roster.rows.filter((row) => row[0] === "Council").length, 303);
  assert.equal(new Set(roster.rows.filter((row) => row[0] === "Assembly").map((row) => row[1])).size, 88);
  assert.equal(new Set(roster.rows.filter((row) => row[0] === "Council").map((row) => row[1])).size, 8);
  assert.deepEqual(roster.chambers, { Assembly: 734, Council: 303 });
  assert.deepEqual(roster.contests, { Assembly: 88, Council: 8 });
});

test("each of 96 lists has complete ordinals and unique nominated names", () => {
  const groups = new Map();
  for (const [chamber, contest, ordinal, name] of roster.rows) {
    const key = `${chamber}|${contest}`;
    const rows = groups.get(key) ?? [];
    rows.push({ ordinal, name });
    groups.set(key, rows);
  }
  assert.equal(groups.size, 96);
  for (const [key, entries] of groups) {
    assert.deepEqual(entries.map((x) => x.ordinal),
      Array.from({ length: entries.length }, (_, i) => i + 1), key);
    assert.equal(new Set(entries.map((x) => x.name.toLowerCase())).size, entries.length, key);
  }
});

test("the candidate directory has no contact fields or unauthorised model effects", () => {
  const content = JSON.stringify(roster);
  for (const prohibited of ["contactPerson","contactEmail","mobilePhone","emailAddress","@" ]) {
    assert.equal(content.includes(prohibited), false, prohibited);
  }
  assert.equal(roster.rows.filter((row) => row[4] === null).length, 112);
  assert.equal(roster.rows.filter((row) => row[0] === "Assembly" && row[4] === "One Nation Victoria").length, 88);
  const melbourne = roster.rows.filter((row) => row[0] === "Assembly" && row[1] === "Melbourne");
  assert.ok(melbourne.some((row) => row[3] === "COURTIS, Phillip" && row[4] === "One Nation Victoria"));
  assert.ok(!melbourne.some((row) => /Matthew Collins/i.test(row[3])));
  const hawthorn = roster.rows.filter((row) => row[0] === "Assembly" && row[1] === "Hawthorn");
  assert.ok(hawthorn.some((row) => row[3] === "IBUKI, Shima"));
});
