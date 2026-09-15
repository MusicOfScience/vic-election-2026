import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { buildHistoricalPollReconstructionQueue } from "../scripts/build-historical-poll-reconstruction-queue.mjs";

function fixture() {
  const sourceBuffer = Buffer.from([
    "\uFEFFMidDate,Firm,Brand,Comments",
    "2010-11-20,Alpha,,first",
    "2014-11-20,Beta,Publisher,second",
    "2014-11-21,Beta,Publisher,third",
    "",
  ].join("\n"));
  return {
    sourceBuffer,
    audit: {
      scope: "fixture",
      source: {
        repository: "example/source",
        commit: "abc123",
        path: "polls.csv",
        sha256: createHash("sha256").update(sourceBuffer).digest("hex"),
        declaredLicence: null,
      },
      missingRequiredFields: ["publicationDate", "sampleSize"],
      coverage: {
        candidateRows: 3,
        cycles: [
          { id: "cycle-a", windowStart: "2010-01-01", informationCutoff: "2010-12-31", candidateRows: 1 },
          { id: "cycle-b", windowStart: "2014-01-01", informationCutoff: "2014-12-31", candidateRows: 2 },
        ],
      },
    },
  };
}

test("builds an aggregate reconstruction queue without emitting observation rows", () => {
  const report = buildHistoricalPollReconstructionQueue({ ...fixture(), reviewedAt: "2026-09-15" });
  assert.equal(report.coverage.candidateRows, 3);
  assert.equal(report.coverage.sourceFamilies, 2);
  assert.equal(report.coverage.reconstructedRows, 0);
  assert.deepEqual(report.coverage.requiredFieldCoverage, { publicationDate: 0, sampleSize: 0 });
  assert.deepEqual(report.reconstructionQueue.map((family) => [family.id, family.candidateRows]), [
    ["beta-publisher", 2],
    ["alpha", 1],
  ]);
  assert.equal(report.candidateSource.observationVoteRowsWritten, false);
  assert.equal("observations" in report, false);
  assert.equal(report.modelImpact.productionAuthorisation, false);
});

test("fails closed when the supplied lead-list fingerprint differs", () => {
  const input = fixture();
  input.audit.source.sha256 = "0".repeat(64);
  assert.throws(
    () => buildHistoricalPollReconstructionQueue({ ...input, reviewedAt: "2026-09-15" }),
    /fingerprint mismatch/,
  );
});

test("records partial first-party progress without making a lead replay-eligible", () => {
  const input = fixture();
  const report = buildHistoricalPollReconstructionQueue({
    ...input,
    reviewedAt: "2026-09-15",
    reconstructionEvidence: {
      sourceFamilies: [{
        id: "alpha",
        candidateRows: 1,
        matchedObservations: [{ cycleId: "cycle-a", leadMidDate: "2010-11-20" }],
        unresolvedObservations: [],
        coverage: {
          sourceMatchedRows: 1,
          unresolvedRows: 0,
          publicationDatedRows: 1,
          sampleSizeRows: 1,
          explicitMethodRows: 0,
          observationSourceUrlRows: 1,
          declaredReuseLicenceRows: 0,
          fullyReconstructedRows: 0,
          replayEligibleRows: 0,
        },
      }],
    },
  });
  const alpha = report.reconstructionQueue.find((family) => family.id === "alpha");
  assert.equal(report.status, "partial-first-party-reconstruction");
  assert.equal(report.coverage.sourceMatchedRows, 1);
  assert.equal(report.candidateSource.reconstructionMetadataWritten, true);
  assert.equal(report.coverage.requiredFieldCoverage.publicationDate, 1);
  assert.equal(alpha.sourceMatchedRows, 1);
  assert.equal(alpha.reconstructedRows, 0);
  assert.equal(alpha.replayEligibleRows, 0);
  assert.equal(alpha.residualRows, 1);
});
