import test from "node:test";
import assert from "node:assert/strict";
import { buildManifest, summariseRecord } from "../scripts/build-discovery-review-manifest.mjs";
import { acceptedPollFromDiscovery, candidateFromDiscovery, candidateIdentity } from "../scripts/apply-discovery-decision.mjs";

test("review manifest separates candidates and polls without promoting them", () => {
  const candidate = { id: "c1", kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Example Party", officialStatus: "endorsed", sourceId: "party", sourceUrl: "https://example.test/c" };
  const poll = { id: "p1", kind: "poll", pollster: "Example Poll", fieldworkStart: "2026-08-20", fieldworkEnd: "2026-08-22", sampleSize: 1000, primaryVote: { alp: 30, coalition: 30, oneNation: 20, greens: 10 }, sourceId: "pollster", sourceUrl: "https://example.test/p" };
  const manifest = buildManifest({ checkedAt: "2026-08-29T00:00:00Z", records: [candidate, poll] });
  assert.deepEqual(manifest.summary, { total: 2, candidates: 1, polls: 1 });
  assert.equal(manifest.automaticPromotion, false);
  assert.match(summariseRecord(candidate).proposedAction, /approve into candidate registry/i);
});

test("party evidence cannot confer official nomination status", () => {
  const discovered = { id: "c1", kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Example Party", officialStatus: "nominated", sourceAuthority: "Example Party", sourceUrl: "https://example.test" };
  const accepted = candidateFromDiscovery(discovered, "2026-08-29T00:00:00Z");
  assert.equal(accepted.status, "endorsed");
  assert.equal(candidateIdentity(accepted), "footscray|alex example");
});

test("VEC evidence may carry official nomination status", () => {
  const discovered = { id: "c2", kind: "candidate", name: "Alex Example", contest: "Footscray", party: "Independent", officialStatus: "nominated", sourceAuthority: "VEC", sourceUrl: "https://vec.example" };
  assert.equal(candidateFromDiscovery(discovered, "2026-08-29T00:00:00Z").status, "nominated");
});

test("accepted poll evidence remains model-ineligible by default", () => {
  const accepted = acceptedPollFromDiscovery({ id: "p1", kind: "poll", pollster: "Example", fieldworkStart: "2026-08-20", fieldworkEnd: "2026-08-22", sampleSize: 1000, geography: "Victoria", sourceUrl: "https://example.test", sourceId: "example" }, "2026-08-29T00:00:00Z");
  assert.equal(accepted.verificationStatus, "human-reviewed-source-evidence");
  assert.equal(accepted.modelEligible, false);
});
