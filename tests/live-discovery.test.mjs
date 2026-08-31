import test from "node:test";
import assert from "node:assert/strict";
import {
  extractLinks,
  findVecCandidateListUrls,
  extractVecCandidatesFromHtml,
  extractGreensCandidates,
  extractOneNationCandidates,
  extractNationalsCandidates,
  extractLaborCandidates,
  extractLiberalCandidates,
  extractVictorianSocialistsCandidates,
  extractFamilyFirstCandidates,
  extractMorningtonPeninsulaCandidates,
  findNextTeamPageUrl,
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

test("VEC candidate table becomes structured nomination evidence", () => {
  const html = `<table><tr><th>District</th><th>Candidate</th><th>Party</th></tr><tr><td>Footscray</td><td>Alex Example</td><td>Independent</td></tr></table>`;
  assert.deepEqual(extractVecCandidatesFromHtml(html, "https://vec.example/candidates"), [{
    kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Independent", candidateStatus: "nominated", sourceAuthority: "VEC", sourceUrl: "https://vec.example/candidates",
  }]);
});

test("Greens party page yields endorsed provisional candidate evidence", () => {
  const html = `<a href="/vic/person/elena">Elena Pereyra Candidate for Footscray and Councillor for Maribyrnong City Council</a><a href="/vic/person/mat">Mat Morgan Lead Candidate for Eastern Victoria Region</a><a href="/vic/person/mp">Ellen Sandell Leader of the Victorian Greens, State Member for Melbourne</a>`;
  assert.deepEqual(extractGreensCandidates(html, "https://greens.org.au/vic/candidates"), [
    { kind: "candidate", name: "Elena Pereyra", contest: "Footscray", party: "Australian Greens Victoria", candidateStatus: "endorsed", sourceAuthority: "Australian Greens Victoria", sourceUrl: "https://greens.org.au/vic/person/elena" },
    { kind: "candidate", name: "Mat Morgan", contest: "Eastern Victoria Region", party: "Australian Greens Victoria", candidateStatus: "endorsed", sourceAuthority: "Australian Greens Victoria", sourceUrl: "https://greens.org.au/vic/person/mat" },
  ]);
});

test("One Nation candidate headings yield endorsed provisional evidence", () => {
  const html = `<h3><a href="/warren-pickering">Warren Pickering for Pakenham</a></h3><p>Bio.</p><h3><a href="/fiona-lopez">Fiona Lopez for Western Metro</a></h3>`;
  assert.deepEqual(extractOneNationCandidates(html, "https://vic.onenation.org.au/candidates"), [
    { kind: "candidate", name: "Warren Pickering", contest: "Pakenham", party: "Pauline Hanson's One Nation", candidateStatus: "endorsed", sourceAuthority: "One Nation Victoria", sourceUrl: "https://vic.onenation.org.au/warren-pickering" },
    { kind: "candidate", name: "Fiona Lopez", contest: "Western Metro", party: "Pauline Hanson's One Nation", candidateStatus: "endorsed", sourceAuthority: "One Nation Victoria", sourceUrl: "https://vic.onenation.org.au/fiona-lopez" },
  ]);
});

test("Nationals team page yields endorsed provisional candidate evidence", () => {
  const html = `<h1>Andrew Lethlean<code><a id="andrew"></a></code></h1><h3><strong>Candidate for Bendigo East</strong></h3><h1>Existing MP</h1><h3>Member for Gippsland South</h3>`;
  assert.deepEqual(extractNationalsCandidates(html, "https://vic.nationals.org.au/our-team/"), [
    { kind: "candidate", name: "Andrew Lethlean", contest: "Bendigo East", party: "The Nationals", candidateStatus: "endorsed", sourceAuthority: "The Nationals Victoria", sourceUrl: "https://vic.nationals.org.au/our-team/" },
  ]);
});

test("Labor roster extracts only explicitly labelled candidates", () => {
  const html = `<div role="listitem" class="member_list-item"><div fs-list-field="member-type">Candidates</div><a href="/members/alex"><h4 fs-list-field="full-name">Alex Example</h4></a><div class="w-embed">Candidate for Footscray</div></div><div role="listitem" class="member_list-item"><div fs-list-field="member-type">State Team</div><h4 fs-list-field="full-name">Existing MP</h4><div class="w-embed">Member for Melbourne</div></div>`;
  assert.deepEqual(extractLaborCandidates(html, "https://www.viclabor.org.au/our-team"), [{
    kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Australian Labor Party - Victorian Branch", candidateStatus: "endorsed", sourceAuthority: "Victorian Labor", sourceUrl: "https://www.viclabor.org.au/members/alex",
  }]);
  assert.equal(findNextTeamPageUrl(`<a class="w-pagination-next" href="?page=2">Next</a>`, "https://www.viclabor.org.au/our-team"), "https://www.viclabor.org.au/our-team?page=2");
});

test("Liberal API keeps only records explicitly marked as candidates", () => {
  const json = JSON.stringify({ Datas: [
    { IsCandidate: true, FirstName: "Alex", LastName: "Example", Electorate: "Footscray", Slug: "alex-example" },
    { IsCandidate: false, FirstName: "Existing", LastName: "MP", Electorate: "Melbourne", Slug: "existing-mp" },
  ] });
  assert.deepEqual(extractLiberalCandidates(json), [{
    kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Liberal Party of Australia (Victorian Division)", candidateStatus: "endorsed", sourceAuthority: "Liberal Victoria", sourceUrl: "https://vic.liberal.org.au/team/alex-example",
  }]);
  assert.throws(() => extractLiberalCandidates(JSON.stringify({ Datas: [] })), /returned no candidates/);
});

test("coverage-gap party sources yield only the configured contests", () => {
  const socialists = `<a href="/candidates/jack-mcmahon">Jack McMahon for Dandenong</a><a href="/candidates/other">Other Person for Footscray</a>`;
  assert.deepEqual(extractVictorianSocialistsCandidates(socialists, "https://www.victoriansocialists.org.au/candidates", ["Dandenong"]), [{
    kind: "candidate", name: "Jack McMahon", contest: "Dandenong", party: "Victorian Socialists", candidateStatus: "endorsed", sourceAuthority: "Victorian Socialists", sourceUrl: "https://www.victoriansocialists.org.au/candidates/jack-mcmahon",
  }]);

  const familyFirst = `<table><tr><td>Lowan - <a href="/elms_2026">Lee Ann Elms</a></td><td>Yan Yean</td></tr></table>`;
  assert.deepEqual(extractFamilyFirstCandidates(familyFirst, "https://www.familyfirstparty.org.au/vic_2026", ["Lowan"]), [{
    kind: "candidate", name: "Lee Ann Elms", contest: "Lowan", party: "Family First Party Australia", candidateStatus: "endorsed", sourceAuthority: "Family First Party Australia", sourceUrl: "https://www.familyfirstparty.org.au/elms_2026",
  }]);
});

test("municipal candidate confirmation remains announced rather than endorsed", () => {
  const html = `<h3>Electorate: Mornington</h3><table><tr><th>Candidate</th><th>Party</th></tr><tr><td>Chris Crewther</td><td>Liberal</td></tr></table><h3>Electorate: Hastings</h3><table><tr><th>Candidate</th><th>Party</th></tr><tr><td>Other Person</td><td>Labor</td></tr></table>`;
  assert.deepEqual(extractMorningtonPeninsulaCandidates(html, "https://www.mornpen.vic.gov.au/The-candidates", ["Mornington"]), [{
    kind: "candidate", name: "Chris Crewther", contest: "Mornington", party: "Liberal Party of Australia (Victorian Division)", candidateStatus: "announced", sourceAuthority: "Mornington Peninsula Shire", sourceUrl: "https://www.mornpen.vic.gov.au/The-candidates",
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
