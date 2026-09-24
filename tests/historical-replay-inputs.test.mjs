import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { buildHistoricalCouncilInputs } from "../scripts/build-historical-council-inputs.mjs";
import { buildHistoricalLocalInputs } from "../scripts/build-historical-local-inputs.mjs";

test("2018 local-input builder uses only a pre-cutoff baseline and excludes target outcomes", () => {
  const result = buildHistoricalLocalInputs("vic_la_2018");
  assert.equal(result.status, "pass");
  assert.equal(result.inputPath, "model/data/processed/vec_2014_assembly_family_primaries.csv");
  assert.equal(result.sourceOutcomeUse, "pre-cutoff-derived-only");
  assert.match(result.dependencyAudit.scoringOnly[0], /2014_2018_same_boundary/);
});

test("2018 local-input builder rejects the outcome-transition artefact if it appears", () => {
  const root = mkdtempSync(join(tmpdir(), "vic-replay-"));
  mkdirSync(join(root, "model/data/processed"), { recursive: true });
  cpSync("model/data/processed/vec_2014_assembly_family_primaries.csv", join(root, "model/data/processed/vec_2014_assembly_family_primaries.csv"));
  writeFileSync(join(root, "model/data/processed/vec_2014_2018_same_boundary_tpp_swing.csv"), "alp_tpp_share_2018\n");
  assert.throws(() => buildHistoricalLocalInputs("vic_la_2018", root), /forbidden target-outcome-derived local input/i);
});

test("2018 Council builder rejects the modern regional poll as post-cutoff", () => {
  const result = buildHistoricalCouncilInputs("vic_la_2018");
  assert.equal(result.status, "pass-with-broad-fallback");
  assert.equal(result.rejectedModernArtefact, "model/data/processed/upper_house_region_poll_2026-08.csv");
  assert.match(result.reason, /2014 Council regional first-preference structure supplies/i);
  assert.equal(result.outcomeCountSequences, "scoring-only");
  assert.equal(result.regionalPollContribution, 0);
});

test("the uComms case preserves published categories and remains owner-gated", async () => {
  const caseFile = await import("../metadata/historical-poll-reuse-case-2018-ucomms.json", { with: { type: "json" } });
  assert.equal(caseFile.default.fieldwork.sampleSize, 1527);
  assert.deepEqual(caseFile.default.reportedPrimaryCategories, { ALP: 37.6, LIB_NAT: 35.2, GRN: 10.2, INDEPENDENT: 5.7, OTHER_MINOR: 4.6, UNDECIDED: 6.7 });
  assert.equal(caseFile.default.ownerReviewStatus, "awaiting-project-owner-approval");
  assert.equal(caseFile.default.replayEligible, false);
});
