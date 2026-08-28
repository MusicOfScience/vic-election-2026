import test from "node:test";
import assert from "node:assert/strict";
import {
  extractLinks,
  findVecCandidateListUrls,
  extractVecCandidatesFromHtml,
  extractRoyMorganStatePoll,
  extractRoyMorganUpperHouse,
  parseFieldworkRange,
  parseCsv,
} from "../scripts/discover-live-source-records.mjs";

test("VEC discovery follows only candidate-list style links", () => {
  const html = `<a href="/candidate-kit">Candidate kit</a><a href="/voting/2026-candidates">Nominated candidates</a>`;
  assert.equal(extractLinks(html, "https://www.vec.vic.gov.au/").length, 2);
  assert.deepEqual(findVecCandidateListUrls(html, "https://www.vec.vic.gov.au/"), ["https://www.vec.vic.gov.au/voting/2026-candidates"]);
});

test("VEC candidate table becomes structured official evidence", () => {
  const html = `<table><tr><th>District</th><th>Candidate</th><th>Party</th></tr><tr><td>Footscray</td><td>Alex Example</td><td>Independent</td></tr></table>`;
  assert.deepEqual(extractVecCandidatesFromHtml(html, "https://vec.example/candidates"), [{
    kind: "candidate",
    name: "Alex Example",
    contest: "Footscray",
    party: "Independent",
    sourceAuthority: "VEC",
    officialStatus: "nominated",
    sourceUrl: "https://vec.example/candidates",
  }]);
});

test("Roy Morgan statewide poll extracts fieldwork, sample and votes", () => {
  const text = "Victorian State Voting Intention. L-NP Coalition 26% and ALP 26% are level on primary vote ahead of One Nation 23.5%, Greens 12.5%, Other Parties 4% and Independents 8%. This special SMS Roy Morgan Poll was conducted from August 5-7, 2026, with a representative Victoria-wide cross-section of 2,084 electors. On a two-party preferred basis: L-NP 51% cf. ALP 49%.";
  const poll = extractRoyMorganStatePoll(text, "https://example.test/poll");
  assert.equal(poll.fieldworkStart, "2026-08-05");
  assert.equal(poll.fieldworkEnd, "2026-08-07");
  assert.equal(poll.sampleSize, 2084);
  assert.deepEqual(poll.primaryVote, { coalition: 26, alp: 26, oneNation: 23.5, greens: 12.5, otherParties: 4, independents: 8 });
  assert.deepEqual(poll.twoPartyPreferred, { coalition: 51, alp: 49 });
});

test("Roy Morgan upper-house headline becomes a structured projection", () => {
  const text = "The L-NP Coalition is set to win 11 seats in Victoria’s Upper House, just ahead of One Nation (10 seats) and the ALP (nine seats). This special SMS Roy Morgan survey was conducted from August 5-7, 2026, with a representative Victoria-wide cross-section of 2,084 electors.";
  const poll = extractRoyMorganUpperHouse(text, "https://example.test/upper");
  assert.deepEqual(poll.seatProjection, { coalition: 11, oneNation: 10, alp: 9 });
  assert.equal(poll.sampleSize, 2084);
});

test("fieldwork and quoted CSV parsing are deterministic", () => {
  assert.deepEqual(parseFieldworkRange("survey conducted August 5-7, 2026"), { start: "2026-08-05", end: "2026-08-07" });
  assert.deepEqual(parseCsv('a,b\n1,"two, three"\n'), [{ a: "1", b: "two, three" }]);
});
