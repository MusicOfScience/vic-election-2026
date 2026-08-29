import test from "node:test";
import assert from "node:assert/strict";
import { diagnoseDemosPoll, extractDemosAuVictoriaPoll, normaliseDemosText } from "../scripts/discover-demosau-victoria-polls.mjs";

const expectedPrimary = { coalition: 32, alp: 23, oneNation: 22, greens: 13, otherParties: 10 };

test("DemosAU Victorian poll extracts dates, sample, primaries and TPP", () => {
  const text = "The DemosAU/PremierNational poll of 1,007 Victorians, conducted from 6-11 August, shows Jess Wilson’s Liberal/National Coalition leading with a primary vote of 32% — up 2% compared to the June poll. Under Mr Carroll, Labor is up 2 points to 23%, while One Nation is 22% (-1%), The Greens 13% (-2%) and Others10% (-1%). On a two party preferred basis, the Coalition leads Labor 55% to 45%.";
  const poll = extractDemosAuVictoriaPoll(text, "https://demosau.com/news/example/");
  assert.equal(poll.fieldworkStart, "2026-08-06");
  assert.equal(poll.fieldworkEnd, "2026-08-11");
  assert.equal(poll.sampleSize, 1007);
  assert.deepEqual(poll.primaryVote, expectedPrimary);
  assert.deepEqual(poll.twoPartyPreferred, { coalition: 55, alp: 45 });
  assert.equal(poll.geography, "Victoria");
});

test("DemosAU parser tolerates HTML entities and source punctuation", () => {
  const text = "The DemosAU/PremierNational poll of 1,007 Victorians, conducted from 6&#8211;11 August, shows Jess Wilson&#8217;s Liberal/National Coalition leading with a primary vote of 32&percnt; &#8212; up 2&percnt;. Under Mr Carroll, Labor is up 2 points to 23&percnt;, while One Nation is 22&percnt; (-1&percnt;), The Greens 13&percnt; (-2&percnt;) and Others10&percnt;. On a two party preferred basis, the Coalition leads Labor 55&percnt; to 45&percnt;.";
  const poll = extractDemosAuVictoriaPoll(text, "https://demosau.com/news/example/");
  assert.match(normaliseDemosText(text), /6-11 August/);
  assert.deepEqual(poll.primaryVote, expectedPrimary);
  assert.deepEqual(poll.twoPartyPreferred, { coalition: 55, alp: 45 });
  assert.deepEqual(diagnoseDemosPoll(text), {
    fieldwork: true,
    sampleSize: true,
    coalition: true,
    alp: true,
    oneNation: true,
    greens: true,
    otherParties: true,
    twoPartyPreferred: true,
  });
});

test("DemosAU parser refuses incomplete records and reports missing fields", () => {
  const text = "Victorian polling mentioned without sample or dates";
  assert.equal(extractDemosAuVictoriaPoll(text, "https://example.test"), null);
  assert.equal(diagnoseDemosPoll(text).fieldwork, false);
  assert.equal(diagnoseDemosPoll(text).sampleSize, false);
});
