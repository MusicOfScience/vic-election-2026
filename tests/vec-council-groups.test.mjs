import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import roster from "../app/vec-official-candidates-2026.review.json" with { type: "json" };
import review from "../app/vec-council-groups-2026.review.json" with { type: "json" };

const official = roster.rows.filter((row) => row[0] === "Council");

function assignedCandidates(region) {
  const source = review.pages[region];
  const candidates = official.filter((row) => row[1] === region);
  assert.ok(source, region + ": no official Council source page");
  let offset = 0;
  const records = [];
  for (const [letter, groupLabel, count] of source.groups) {
    assert.ok(Number.isInteger(count) && count >= 1);
    for (const row of candidates.slice(offset, offset + count)) {
      records.push({ name: row[3], sourceOrdinal: row[2], letter, groupLabel });
    }
    offset += count;
  }
  assert.equal(offset, candidates.length, region + ": group boundaries do not cover complete VEC list");
  assert.equal(records.length, candidates.length);
  return records;
}

test("Council audit is tied to exact approved VEC workbook and candidate display data", () => {
  const raw = readFileSync(resolve(import.meta.dirname, "../app/vec-official-candidates-2026.review.json"));
  assert.equal(createHash("sha256").update(raw).digest("hex"), review.candidateRosterSha256);
  assert.equal(review.candidateWorkbookSha256, roster.sourceFileSha256);
  assert.equal(review.sourceAuthority, "Victorian Electoral Commission");
  assert.equal(review.status, "source-verified-display-review-only");
  assert.equal(review.privateContactFieldsIncluded, false);
  assert.equal(review.candidateRegistryPromoted, false);
  assert.equal(review.forecastInputsChanged, false);
  assert.equal(review.groupVotingTicketsPresent, false);
});

test("all 303 Council candidates and 8 regions have verifiable contiguous ballot groups", () => {
  assert.equal(official.length, 303);
  assert.equal(review.candidateCount, 303);
  assert.equal(Object.keys(review.pages).length, 8);
  const reviewed = [];
  let lettered = 0;
  let ungrouped = 0;
  for (const [region, page] of Object.entries(review.pages)) {
    assert.match(page.sha256, /^[a-f0-9]{64}$/, region);
    const groups = page.groups;
    assert.ok(groups.length >= 1);
    const letters = groups.filter(([letter]) => letter !== "Ungrouped").map(([letter]) => letter);
    assert.deepEqual(letters, Array.from({ length: letters.length }, (_, i) => String.fromCharCode(65 + i)), region);
    if (groups.some(([letter]) => letter === "Ungrouped")) {
      assert.equal(groups.at(-1)[0], "Ungrouped");
      assert.equal(groups.filter(([letter]) => letter === "Ungrouped").length, 1);
    }
    lettered += letters.length;
    ungrouped += groups.filter(([letter]) => letter === "Ungrouped").reduce((n, group) => n + group[2], 0);
    const rows = assignedCandidates(region);
    assert.deepEqual(rows.map((row) => row.sourceOrdinal), Array.from({ length: rows.length }, (_, i) => i + 1));
    reviewed.push(...rows);
  }
  assert.equal(reviewed.length, 303);
  assert.equal(lettered, 99);
  assert.equal(ungrouped, 5);
  assert.equal(review.letteredGroupCount, 99);
  assert.equal(review.ungroupedCandidateCount, 5);
});

test("named and unnamed groups are not confused with registered parties or group voting tickets", () => {
  const northern = assignedCandidates("Northern Metropolitan");
  assert.equal(northern.find((r) => r.name === "RAZOS, Peter")?.letter, "Ungrouped");
  const northernNoParty = northern.filter((r) => r.letter === "B");
  assert.equal(northernNoParty.length, 2);
  assert.ok(northernNoParty.every((r) => r.groupLabel === "Unnamed-1"));

  const northEastern = assignedCandidates("North-Eastern Metropolitan");
  assert.equal(northEastern.find((r) => r.name === "CHOW, Wai Man Raymond")?.letter, "J");
  assert.equal(northEastern.find((r) => r.name === "ADAMS, Natalie")?.letter, "G");

  const western = assignedCandidates("Western Victoria");
  assert.equal(western.find((r) => r.name === "FISHER, Eve")?.letter, "Ungrouped");
  assert.equal(western.find((r) => r.name === "MCARTHUR, Bev")?.letter, "F");
});

test("sanitised Council source metadata contains no contact-person details", () => {
  const text = JSON.stringify(review);
  assert.ok(!text.includes("@"));
  for (const term of ["telephone", "phoneNumber", "contactEmail", "contactPerson"]) {
    assert.ok(!text.includes(term), term);
  }
});
