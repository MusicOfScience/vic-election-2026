import test from "node:test";
import assert from "node:assert/strict";
import { extractLiberalCandidates } from "../scripts/discover-liberal-victoria-candidates.mjs";

test("Liberal team cards yield endorsed candidate evidence and ignore incumbents", () => {
  const html = `
    <div class="card"><a href="/team/simmone-cottom"><span>Simmone Cottom</span></a><div>Candidate for Sunbury</div></div>
    <div class="card"><a href="/team/tommy-le-deux">Tommy Le Deux</a><div>Liberal for Essendon</div></div>
    <div class="card"><a href="/team/jess-wilson">Jess Wilson</a><div>Member for Kew</div><div>Leader of the Liberal Party</div></div>
  `;
  assert.deepEqual(extractLiberalCandidates(html, "https://vic.liberal.org.au/our-team/state/legislative-assembly"), [
    {
      kind: "candidate",
      name: "Simmone Cottom",
      contest: "Sunbury",
      party: "Liberal Party",
      candidateStatus: "endorsed",
      sourceAuthority: "Liberal Victoria",
      sourceUrl: "https://vic.liberal.org.au/team/simmone-cottom",
    },
    {
      kind: "candidate",
      name: "Tommy Le Deux",
      contest: "Essendon",
      party: "Liberal Party",
      candidateStatus: "endorsed",
      sourceAuthority: "Liberal Victoria",
      sourceUrl: "https://vic.liberal.org.au/team/tommy-le-deux",
    },
  ]);
});

test("Liberal candidate extraction canonicalises role suffix clutter and deduplicates cards", () => {
  const html = `
    <a href="/team/bernadette-khoury">Bernadette Khoury</a><span>Candidate for Northern Metropolitan Region</span>
    <a href="/team/bernadette-khoury">Bernadette Khoury Candidate for Northern Metropolitan Region</a><span>Liberal for Northern Metropolitan Region</span>
  `;
  assert.deepEqual(extractLiberalCandidates(html, "https://vic.liberal.org.au/our-team/state/legislative-council"), [
    {
      kind: "candidate",
      name: "Bernadette Khoury",
      contest: "Northern Metropolitan Region",
      party: "Liberal Party",
      candidateStatus: "endorsed",
      sourceAuthority: "Liberal Victoria",
      sourceUrl: "https://vic.liberal.org.au/team/bernadette-khoury",
    },
  ]);
});
