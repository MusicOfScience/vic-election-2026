import test from "node:test";
import assert from "node:assert/strict";
import { buildEvidenceFreshness } from "../scripts/build-evidence-freshness-report.mjs";

test("new staged poll does not masquerade as fresh model input", () => {
  const report = buildEvidenceFreshness({
    asOf: "2026-08-29",
    modelPolls: [
      { poll_id: "old", pollster: "Roy Morgan", publication_date: "2026-08-08", model_eligible: "True" },
      { poll_id: "ignored", pollster: "Freshwater", publication_date: "2026-08-20", model_eligible: "False" },
    ],
    acceptedPolls: [],
    stagedPolls: [{
      id: "demos-aug",
      pollster: "DemosAU",
      publicationDate: "2026-08-15",
      status: "quarantined-awaiting-review",
    }],
  });
  assert.equal(report.modelInput.latestPublicationDate, "2026-08-08");
  assert.equal(report.stagedEvidence.latestPublicationDate, "2026-08-15");
  assert.equal(report.newerEvidenceAwaitingReview, true);
  assert.equal(report.modelFreshnessUnchangedByStagedEvidence, true);
});

test("accepted evidence remains distinct from model eligibility", () => {
  const report = buildEvidenceFreshness({
    asOf: "2026-08-29",
    modelPolls: [{ poll_id: "old", pollster: "Roy Morgan", publication_date: "2026-08-08", model_eligible: "True" }],
    acceptedPolls: [{ pollster: "DemosAU", publicationDate: "2026-08-15", modelEligible: false }],
    stagedPolls: [],
  });
  assert.equal(report.acceptedEvidence.latestPublicationDate, "2026-08-15");
  assert.equal(report.modelInput.latestPublicationDate, "2026-08-08");
});

test("explicit hold or defer decisions resolve newer evidence without model admission", () => {
  const report = buildEvidenceFreshness({
    asOf: "2026-08-29",
    modelPolls: [{ poll_id: "old", pollster: "Roy Morgan", publication_date: "2026-08-08", model_eligible: "True" }],
    acceptedPolls: [],
    stagedPolls: [
      { id: "demos-aug", pollster: "DemosAU", publicationDate: "2026-08-15", status: "quarantined-awaiting-review" },
      { id: "resolve-aug", pollster: "Resolve Strategic", publicationDate: "2026-08-21", status: "quarantined-awaiting-review" },
    ],
    reviewDecisions: [
      { evidenceId: "demos-aug", kind: "poll", decision: "defer" },
      { evidenceId: "resolve-aug", kind: "poll", decision: "hold" },
    ],
  });
  assert.equal(report.newerEvidenceAwaitingReview, false);
  assert.equal(report.newerEvidenceExcludedByReview, true);
  assert.deepEqual(report.reviewResolution, {
    stagedRecords: 2,
    resolvedRecords: 2,
    unresolvedRecords: 0,
    latestResolvedEvidence: {
      evidenceId: "resolve-aug",
      pollster: "Resolve Strategic",
      latestPublicationDate: "2026-08-21",
      decision: "hold",
    },
  });
});
