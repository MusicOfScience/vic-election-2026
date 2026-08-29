import test from "node:test";
import assert from "node:assert/strict";
import { extractDemosAuVictoriaPoll } from "../scripts/discover-demosau-victoria-polls.mjs";

test("DemosAU Victorian poll extracts dates, sample, primaries and TPP", () => {
  const text = "The DemosAU/PremierNational poll of 1,007 Victorians, conducted from 6-11 August, shows Jess Wilson’s Liberal/National Coalition leading with a primary vote of 32% — up 2% compared to the June poll. Under Mr Carroll, Labor is up 2 points to 23%, while One Nation is 22% (-1%), The Greens 13% (-2%) and Others10% (-1%). On a two party preferred basis, the Coalition leads Labor 55% to 45%.";
  const poll = extractDemosAuVictoriaPoll(text, "https://demosau.com/news/example/");
  assert.equal(poll.fieldworkStart, "2026-08-06");
  assert.equal(poll.fieldworkEnd, "2026-08-11");
  assert.equal(poll.sampleSize, 1007);
  assert.deepEqual(poll.primaryVote, { coalition: 32, alp: 23, oneNation: 22, greens: 13, otherParties: 10 });
  assert.deepEqual(poll.twoPartyPreferred, { coalition: 55, alp: 45 });
  assert.equal(poll.geography, "Victoria");
});

test("DemosAU parser refuses incomplete records", () => {
  assert.equal(extractDemosAuVictoriaPoll("Victorian polling mentioned without sample or dates", "https://example.test"), null);
});
