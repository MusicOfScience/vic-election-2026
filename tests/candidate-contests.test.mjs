import assert from "node:assert/strict";
import test from "node:test";
import { resolve } from "node:path";

import { classifyContest, loadContestUniverse } from "../scripts/candidate-contests.mjs";

const universe = loadContestUniverse(resolve(import.meta.dirname, ".."));

test("canonicalises party shorthand for metropolitan Council regions", () => {
  const aliases = new Map([
    ["North-East Metro Region", "North-Eastern Metropolitan"],
    ["North Eastern Metropolitan Region", "North-Eastern Metropolitan"],
    ["Northern Metro", "Northern Metropolitan"],
    ["South-East Metro", "South-Eastern Metropolitan"],
    ["Southern Metro", "Southern Metropolitan"],
    ["Western Metro", "Western Metropolitan"],
  ]);

  for (const [sourceContest, canonicalContest] of aliases) {
    assert.deepEqual(classifyContest(sourceContest, universe), { chamber: "council", canonicalContest });
  }
});
